"""
Preconfig management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, date, timezone

import httpx
from sqlalchemy import select, and_, func
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    PreconfigData,
    PushPreconfigResponse,
    BuildServerPushResult,
    RegionLockInfo,
    RegionLockResponse,
    LockConflictDetail,
)
from app.auth import get_current_user
from app.config import settings
from app.db.models import PreconfigDB
from app.permissions import (
    check_region_access,
    check_depot_access,
    get_region_for_depot,
    get_depot_for_region,
)
from app.routers.config import get_config, get_appliance_sizes, get_build_server_config
from app.services.lock_service import (
    acquire_lock,
    release_lock,
    get_lock_status,
    get_all_lock_statuses,
)
from app.logger import preconfig_logger

# Use dedicated preconfig logger for detailed debugging
logger = preconfig_logger

router = APIRouter()


def _get_valid_regions() -> set:
    """Get valid regions from config"""
    config = get_config()
    return set(config.get("regions", {}).keys())


def _get_region_to_depot() -> dict:
    """Get region to depot mapping from config"""
    config = get_config()
    regions = config.get("regions", {})
    return {r: cfg.get("depot_id") for r, cfg in regions.items() if cfg.get("depot_id")}


def _get_depot_to_region() -> dict:
    """Get depot to region mapping from config"""
    config = get_config()
    regions = config.get("regions", {})
    return {cfg.get("depot_id"): r.upper() for r, cfg in regions.items() if cfg.get("depot_id")}


async def get_optional_db() -> Optional[AsyncSession]:
    """
    Optional database dependency - returns None if database not configured.
    This allows endpoints to gracefully handle missing database.
    """
    if not settings.DATABASE_URL:
        return None

    try:
        from app.db.database import get_db
        async for session in get_db():
            return session
    except Exception as e:
        logger.warning(f"Database connection failed: {str(e)}")
        return None


def generate_mock_preconfigs(depot: int) -> List[PreconfigData]:
    """
    Generate mock preconfig data for a specific depot
    Used when external API or database is not available
    Appliance sizes are read from config.json
    """
    appliance_sizes = get_appliance_sizes()

    # Sample configs that scale with appliance size
    sample_configs = [
        {
            "os": "Ubuntu 22.04 LTS",
            "cpu": "2x Intel Xeon Gold 6248R",
            "ram": "128GB DDR4",
            "storage": "4x 1TB NVMe SSD",
            "raid": "RAID 10",
            "network": "2x 25Gbps",
        },
        {
            "os": "CentOS 8 Stream",
            "cpu": "2x AMD EPYC 7502",
            "ram": "256GB DDR4",
            "storage": "8x 2TB NVMe SSD",
            "raid": "RAID 6",
            "network": "2x 100Gbps",
        },
        {
            "os": "Rocky Linux 9",
            "cpu": "2x AMD EPYC 7763",
            "ram": "512GB DDR4",
            "storage": "12x 4TB NVMe SSD",
            "raid": "RAID 10",
            "network": "4x 100Gbps",
        },
    ]

    preconfigs = []
    for i, size in enumerate(appliance_sizes):
        config = sample_configs[i % len(sample_configs)]
        preconfigs.append(
            PreconfigData(
                dbid=f"dbid-{depot:03d}-{i + 1:03d}",
                depot=depot,
                appliance_size=size,
                config=config,
                created_at=datetime.utcnow(),
            )
        )

    return preconfigs


def generate_mock_pushed_preconfigs() -> List[PreconfigData]:
    """
    Generate mock pushed preconfig data
    Simulates preconfigs that have been pushed to depots
    Appliance sizes are read from config.json
    """
    appliance_sizes = get_appliance_sizes()
    now = datetime.utcnow()

    # Return a couple of pushed preconfigs using sizes from config
    preconfigs = []
    if len(appliance_sizes) >= 1:
        preconfigs.append(
            PreconfigData(
                dbid="pushed-001",
                depot=1,
                appliance_size=appliance_sizes[0],
                config={
                    "os": "Ubuntu 20.04 LTS",
                    "cpu": "2x Intel Xeon Gold 6248R",
                    "ram": "128GB DDR4",
                    "storage": "4x 1TB NVMe SSD",
                    "raid": "RAID 10",
                    "network": "2x 25Gbps",
                },
                created_at=now,
                last_pushed_at=now,
                pushed_to=["cbg-build-01"],
            )
        )
    if len(appliance_sizes) >= 2:
        preconfigs.append(
            PreconfigData(
                dbid="pushed-002",
                depot=2,
                appliance_size=appliance_sizes[1],
                config={
                    "os": "Ubuntu 22.04 LTS",
                    "cpu": "2x Intel Xeon Gold 6348",
                    "ram": "512GB DDR4",
                    "storage": "12x 4TB NVMe SSD",
                    "raid": "RAID 10",
                    "network": "2x 100Gbps",
                },
                created_at=now,
                last_pushed_at=now,
                pushed_to=["dub-build-01"],
            )
        )

    return preconfigs


async def fetch_preconfigs_from_api() -> dict:
    """
    Fetch preconfigs from external API using PSK authentication
    Returns the raw JSON response as a dict, or empty dict if API unavailable
    """
    if not settings.PRECONFIG_API_ENDPOINT or not settings.PRECONFIG_API_PSK:
        logger.warning("Preconfig API not configured, using mock data")
        return {}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                settings.PRECONFIG_API_ENDPOINT,
                headers={"orange-psk": settings.PRECONFIG_API_PSK}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch preconfigs from API: {e}")
        # Return empty dict to allow fallback to mock data
        return {}


async def upsert_preconfigs_to_db(db, preconfigs_data: dict) -> None:
    """
    Upsert preconfigs to database
    If preconfig with dbid exists, update it; otherwise insert new record
    """
    for key, preconfig_obj in preconfigs_data.items():
        # Extract dbid from key (format: "dbid-{dbid}")
        dbid = key.replace("dbid-", "") if key.startswith("dbid-") else key

        # Get values from preconfig object
        depot_id = preconfig_obj.get("depot_id")
        appliance_size = preconfig_obj.get("appliance_size")
        config = preconfig_obj  # Store the entire object as config

        if depot_id is None:
            logger.warning(f"Skipping preconfig {dbid}: missing depot_id")
            continue

        # MySQL upsert using INSERT ... ON DUPLICATE KEY UPDATE
        stmt = insert(PreconfigDB).values(
            dbid=dbid,
            depot=depot_id,
            appliance_size=appliance_size,
            config=config,
            created_at=datetime.utcnow(),
        )
        stmt = stmt.on_duplicate_key_update(
            depot=stmt.inserted.depot,
            appliance_size=stmt.inserted.appliance_size,
            config=stmt.inserted.config,
            updated_at=datetime.utcnow(),
        )

        await db.execute(stmt)

    await db.commit()


@router.get(
    "/preconfig/pushed",
    response_model=List[PreconfigData],
    summary="Get pushed preconfigs",
    description="Get preconfigurations that have been pushed to depots",
)
async def get_pushed_preconfigs(
    current_user: User = Depends(get_current_user),
) -> List[PreconfigData]:
    """
    Get pushed preconfigurations
    Returns list of preconfig records that have been pushed
    Filtered by user's allowed regions (admins see all)
    """
    try:
        logger.info(f"Pushed preconfigs requested by {current_user.email}")

        # Simulate database query
        preconfigs = generate_mock_pushed_preconfigs()

        # Filter by user's allowed regions (admins see all)
        if not current_user.is_admin:
            region_to_depot = _get_region_to_depot()
            allowed_depots = [region_to_depot.get(r) for r in current_user.allowed_regions if region_to_depot.get(r)]
            preconfigs = [p for p in preconfigs if p.depot in allowed_depots]

        return preconfigs

    except Exception as e:
        logger.error(f"Error fetching pushed preconfigs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pushed preconfigs",
        )


@router.get(
    "/preconfig/{region}",
    response_model=List[PreconfigData],
    summary="Get preconfigs by region",
    description="Get preconfigurations for a specific region. Fetches from external API and stores in database.",
)
async def get_preconfigs_by_region(
    region: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_optional_db),
) -> List[PreconfigData]:
    """
    Get preconfigurations for a specific region
    1. Validates region
    2. Checks user has permission for the region
    3. Fetches from external API (if configured)
    4. Upserts to database
    5. Returns preconfigs filtered by region/depot
    """
    # Validate region
    valid_regions = _get_valid_regions()
    region_lower = region.lower()
    if region_lower not in valid_regions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region: {region}. Must be one of: {', '.join(valid_regions)}"
        )

    # Check user has permission for this region
    if not check_region_access(current_user.email, region_lower):
        logger.warning(f"Region access denied for {current_user.email} to {region_lower}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You do not have permission to access region {region}"
        )

    region_to_depot = _get_region_to_depot()
    depot = region_to_depot.get(region_lower)
    logger.info(f"Preconfigs for region {region} (depot {depot}) requested by {current_user.email}")

    # If no database or API configured, return mock data
    if db is None or not settings.PRECONFIG_API_ENDPOINT:
        logger.info("Using mock preconfig data (no DB or API configured)")
        return generate_mock_preconfigs(depot)

    try:
        # Fetch from external API
        preconfigs_data = await fetch_preconfigs_from_api()

        if preconfigs_data:
            # Upsert to database
            await upsert_preconfigs_to_db(db, preconfigs_data)

        # Query database for preconfigs matching depot
        stmt = select(PreconfigDB).where(PreconfigDB.depot == depot)
        result = await db.execute(stmt)
        db_preconfigs = result.scalars().all()

        # If no preconfigs found in database, return mock data
        if not db_preconfigs:
            logger.info("No preconfigs in database, using mock data")
            return generate_mock_preconfigs(depot)

        # Convert to Pydantic models
        preconfigs = [
            PreconfigData(
                dbid=p.dbid,
                depot=p.depot,
                appliance_size=p.appliance_size,
                config=p.config,
                created_at=p.created_at,
                last_pushed_at=p.last_pushed_at,
                pushed_to=p.pushed_to or [],
            )
            for p in db_preconfigs
        ]

        return preconfigs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preconfigs: {str(e)}")
        # Fall back to mock data on error
        logger.info("Falling back to mock preconfig data due to error")
        return generate_mock_preconfigs(depot)


@router.get(
    "/preconfig/locks",
    response_model=RegionLockResponse,
    summary="Get all region lock statuses",
    description="Get the current lock status for all regions",
)
async def get_all_region_locks(
    current_user: User = Depends(get_current_user),
    db=Depends(get_optional_db),
) -> RegionLockResponse:
    """
    Get lock status for all regions.

    Returns a dictionary mapping region codes to their lock status.
    Useful for displaying lock indicators across all regions.
    """
    try:
        if db is None:
            # No database - return empty locks (graceful degradation)
            logger.debug("No database configured, returning empty lock status")
            return RegionLockResponse(locks={})

        locks = await get_all_lock_statuses(db)
        return RegionLockResponse(locks=locks)

    except Exception as e:
        logger.error(f"Error getting all lock statuses: {str(e)}")
        # Graceful degradation - return empty locks instead of error
        return RegionLockResponse(locks={})


@router.get(
    "/preconfig/{region}/lock",
    response_model=RegionLockInfo,
    summary="Get region lock status",
    description="Get the current lock status for a specific region",
)
async def get_region_lock(
    region: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_optional_db),
) -> RegionLockInfo:
    """
    Get the lock status for a specific region.

    Returns information about who holds the lock (if any) and when it expires.
    """
    # Validate region
    valid_regions = _get_valid_regions()
    region_lower = region.lower()
    if region_lower not in valid_regions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region: {region}. Must be one of: {', '.join(valid_regions)}"
        )

    try:
        if db is None:
            # No database - return unlocked status (graceful degradation)
            logger.debug(f"No database configured, returning unlocked status for {region_lower}")
            return RegionLockInfo(region=region_lower, is_locked=False)

        return await get_lock_status(db, region_lower)

    except Exception as e:
        logger.error(f"Error getting lock status for {region_lower}: {str(e)}")
        # Graceful degradation - return unlocked instead of error
        return RegionLockInfo(region=region_lower, is_locked=False)


@router.post(
    "/preconfig/{region}/push",
    response_model=PushPreconfigResponse,
    summary="Push preconfigs to build servers",
    description="Push today's preconfigs to all build servers in the specified region",
    responses={
        409: {
            "description": "Region is locked by another user",
            "model": LockConflictDetail,
        }
    },
)
async def push_preconfig(
    region: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_optional_db),
) -> PushPreconfigResponse:
    """
    Push preconfigs to build servers in the region.

    1. Validates region and permissions
    2. Acquires region lock (returns 409 if locked by another user)
    3. Gets build servers for region from config
    4. Queries preconfigs created today for the region
    5. For each build server, filters preconfigs by appliance_size matching server's preconfigs[]
    6. Sends PUT request to each build server
    7. Updates last_pushed_at and pushed_to for successful pushes
    8. Releases region lock
    9. Returns per-server status
    """
    # Validate region using config.json
    valid_regions = _get_valid_regions()
    region_lower = region.lower()
    if region_lower not in valid_regions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region: {region}. Must be one of: {', '.join(valid_regions)}"
        )

    # Check user has permission for this region
    if not check_region_access(current_user.email, region_lower):
        logger.warning(f"Region access denied for {current_user.email} to {region_lower}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You do not have permission to push to region {region}"
        )

    region_to_depot = _get_region_to_depot()
    depot = region_to_depot.get(region_lower)

    # Get build server configuration for this region
    build_server_config = get_build_server_config(region_lower)
    if not build_server_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No build servers configured for region {region}"
        )

    logger.info(
        f"Push preconfig to region {region_lower} (depot {depot}) requested by {current_user.email}"
    )
    logger.info(f"Build servers: {list(build_server_config.keys())}")

    # DEBUG: Log detailed request information
    logger.debug("=" * 80)
    logger.debug(f"PRECONFIG PUSH REQUEST - Region: {region_lower.upper()}")
    logger.debug("=" * 80)
    logger.debug(f"User: {current_user.email} (Role: {current_user.role})")
    logger.debug(f"Region: {region_lower} -> Depot: {depot}")
    logger.debug(f"Build servers configured: {len(build_server_config)}")
    for bs_name, bs_config in build_server_config.items():
        logger.debug(f"  - {bs_name}: handles appliance sizes {bs_config.get('preconfigs', [])}")
    logger.debug("-" * 80)

    # If no database, return mock success (no locking available)
    if db is None:
        logger.debug("No database configured, proceeding without locking")
        mock_results = [
            BuildServerPushResult(
                build_server=bs,
                status="success",
                preconfig_count=len(get_appliance_sizes())
            )
            for bs in build_server_config.keys()
        ]
        return PushPreconfigResponse(
            status="success",
            message=f"Mock push successfully sent preconfigs to {len(build_server_config)} build server(s) in {region_lower.upper()}",
            results=mock_results,
            pushed_preconfigs=generate_mock_preconfigs(depot),
        )

    # Try to acquire lock for this region
    logger.debug(f"Attempting to acquire lock for region {region_lower}...")
    try:
        lock_acquired, existing_lock = await acquire_lock(db, region_lower, current_user)
        if lock_acquired:
            logger.debug(f"✓ Lock acquired successfully for region {region_lower}")
        else:
            logger.debug(f"✗ Lock acquisition failed - region {region_lower} is locked by another user")
    except Exception as e:
        # If locking fails, proceed without lock (graceful degradation)
        logger.warning(f"Lock acquisition failed, proceeding without lock: {e}")
        logger.debug(f"⚠ Lock service error, continuing without lock protection")
        lock_acquired = True
        existing_lock = None

    if not lock_acquired and existing_lock:
        # Region is locked by another user - return 409 Conflict
        logger.info(
            f"Push blocked for {current_user.email} - region {region_lower} locked by {existing_lock.locked_by_email}"
        )
        logger.debug(
            f"Lock held by: {existing_lock.locked_by_email} ({existing_lock.locked_by_name}) "
            f"since {existing_lock.locked_at}, expires at {existing_lock.expires_at}"
        )
        conflict_detail = LockConflictDetail(
            error="region_locked",
            message=f"Region {region_lower.upper()} is currently locked by another user",
            lock_info=existing_lock,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=conflict_detail.model_dump(mode="json"),
        )

    try:
        # Query preconfigs for this depot created today (UTC)
        today_utc = date.today()
        logger.debug(f"Querying database for preconfigs: depot={depot}, date={today_utc}")

        stmt = select(PreconfigDB).where(
            and_(
                PreconfigDB.depot == depot,
                func.date(PreconfigDB.created_at) == today_utc
            )
        )
        result = await db.execute(stmt)
        preconfigs_to_push = result.scalars().all()

        logger.debug(f"Found {len(preconfigs_to_push)} preconfigs to push for depot {depot} today")

        if not preconfigs_to_push:
            logger.debug("No preconfigs found for today - returning early")
            # Return results for all build servers indicating no preconfigs
            results = [
                BuildServerPushResult(
                    build_server=bs,
                    status="skipped",
                    error="No preconfigs to push today",
                    preconfig_count=0
                )
                for bs in build_server_config.keys()
            ]
            return PushPreconfigResponse(
                status="success",
                message=f"No preconfigs to push for {region_lower.upper()} today",
                results=results,
                pushed_preconfigs=[],
            )

        # DEBUG: Log detailed preconfig information
        logger.debug("-" * 80)
        logger.debug("PRECONFIGS TO PUSH:")
        appliance_size_counts = {}
        for p in preconfigs_to_push:
            size = p.appliance_size
            appliance_size_counts[size] = appliance_size_counts.get(size, 0) + 1
            logger.debug(f"  DBID: {p.dbid:<20} | Depot: {p.depot} | Size: {size:<10} | Created: {p.created_at}")

        logger.debug("-" * 80)
        logger.debug("PRECONFIGS BY APPLIANCE SIZE:")
        for size, count in sorted(appliance_size_counts.items()):
            logger.debug(f"  {size}: {count} preconfig(s)")
        logger.debug("-" * 80)

        # Push to each build server
        push_results: List[BuildServerPushResult] = []
        # Track which preconfigs were successfully pushed to which servers
        preconfig_push_map: Dict[str, List[str]] = {p.dbid: [] for p in preconfigs_to_push}

        logger.debug(f"Starting push to {len(build_server_config)} build server(s)...")
        logger.debug("=" * 80)

        async with httpx.AsyncClient(timeout=settings.BUILD_SERVER_TIMEOUT) as client:
            for build_server, server_config in build_server_config.items():
                logger.debug(f"Processing build server: {build_server}")

                # Get the appliance sizes this build server handles
                server_preconfig_sizes = server_config.get("preconfigs", [])
                logger.debug(f"  Server handles appliance sizes: {server_preconfig_sizes}")

                # Filter preconfigs to only those matching this server's sizes
                matching_preconfigs = [
                    p for p in preconfigs_to_push
                    if p.appliance_size in server_preconfig_sizes
                ]

                logger.debug(f"  Matched {len(matching_preconfigs)} preconfigs for this server")

                if not matching_preconfigs:
                    logger.debug(f"  ⊘ SKIPPING {build_server}: No matching preconfigs")
                    push_results.append(BuildServerPushResult(
                        build_server=build_server,
                        status="skipped",
                        error="No matching preconfigs for this server's sizes",
                        preconfig_count=0
                    ))
                    logger.debug("-" * 80)
                    continue

                # DEBUG: Log preconfigs being sent to this server
                logger.debug(f"  Preconfigs to push to {build_server}:")
                for p in matching_preconfigs:
                    logger.debug(f"    - DBID: {p.dbid} | Size: {p.appliance_size}")

                # Prepare payload
                payload = [
                    {
                        "dbid": p.dbid,
                        "depot": p.depot,
                        "appliance_size": p.appliance_size,
                        "config": p.config,
                    }
                    for p in matching_preconfigs
                ]

                url = f"https://{build_server}{settings.BUILD_SERVER_DOMAIN}/preconfig"
                logger.debug(f"  PUT {url}")
                logger.debug(f"  Payload size: {len(payload)} preconfig(s)")
                logger.debug(f"  Timeout: {settings.BUILD_SERVER_TIMEOUT}s")

                try:
                    response = await client.put(url, json=payload)
                    response.raise_for_status()

                    logger.debug(f"  ✓ SUCCESS: {build_server} - Status: {response.status_code}")
                    logger.info(f"Successfully pushed {len(matching_preconfigs)} preconfigs to {build_server}")

                    push_results.append(BuildServerPushResult(
                        build_server=build_server,
                        status="success",
                        preconfig_count=len(matching_preconfigs)
                    ))
                    # Track successful push for each preconfig
                    for p in matching_preconfigs:
                        preconfig_push_map[p.dbid].append(build_server)
                        logger.debug(f"    Tracked: DBID {p.dbid} pushed to {build_server}")

                except httpx.TimeoutException as e:
                    logger.error(f"  ✗ TIMEOUT: {build_server} - Request timed out after {settings.BUILD_SERVER_TIMEOUT}s")
                    logger.debug(f"  Timeout details: {str(e)}")
                    push_results.append(BuildServerPushResult(
                        build_server=build_server,
                        status="failed",
                        error="Connection timeout",
                        preconfig_count=0
                    ))
                except httpx.HTTPStatusError as e:
                    logger.error(f"  ✗ HTTP ERROR: {build_server} - Status: {e.response.status_code}")
                    logger.debug(f"  Response body: {e.response.text[:200]}")
                    push_results.append(BuildServerPushResult(
                        build_server=build_server,
                        status="failed",
                        error=f"HTTP {e.response.status_code}",
                        preconfig_count=0
                    ))
                except Exception as e:
                    logger.error(f"  ✗ ERROR: {build_server} - {str(e)[:100]}")
                    logger.debug(f"  Full error: {str(e)}", exc_info=True)
                    push_results.append(BuildServerPushResult(
                        build_server=build_server,
                        status="failed",
                        error=str(e)[:100],  # Truncate long errors
                        preconfig_count=0
                    ))

                logger.debug("-" * 80)

        # Update database for preconfigs that were successfully pushed
        logger.debug("=" * 80)
        logger.debug("UPDATING DATABASE WITH PUSH RESULTS")
        logger.debug("-" * 80)

        now = datetime.now(timezone.utc)
        pushed_preconfigs_data: List[PreconfigData] = []

        for preconfig in preconfigs_to_push:
            successful_servers = preconfig_push_map.get(preconfig.dbid, [])
            if successful_servers:
                # Merge existing pushed_to with new successful servers
                existing_pushed_to = preconfig.pushed_to or []
                updated_pushed_to = list(set(existing_pushed_to + successful_servers))

                logger.debug(f"DBID {preconfig.dbid}:")
                logger.debug(f"  Previously pushed to: {existing_pushed_to if existing_pushed_to else 'None'}")
                logger.debug(f"  New successful pushes: {successful_servers}")
                logger.debug(f"  Updated pushed_to list: {updated_pushed_to}")
                logger.debug(f"  Last pushed at: {now}")

                preconfig.last_pushed_at = now
                preconfig.pushed_to = updated_pushed_to

                pushed_preconfigs_data.append(PreconfigData(
                    dbid=preconfig.dbid,
                    depot=preconfig.depot,
                    appliance_size=preconfig.appliance_size,
                    config=preconfig.config,
                    created_at=preconfig.created_at,
                    last_pushed_at=now,
                    pushed_to=updated_pushed_to,
                ))
            else:
                logger.debug(f"DBID {preconfig.dbid}: No successful pushes (not updating)")

        logger.debug("-" * 80)
        logger.debug(f"Committing {len(pushed_preconfigs_data)} preconfig updates to database...")

        if pushed_preconfigs_data:
            await db.commit()
            logger.debug(f"✓ Database commit successful")

        # Determine overall status
        success_count = sum(1 for r in push_results if r.status == "success")
        failed_count = sum(1 for r in push_results if r.status == "failed")
        skipped_count = sum(1 for r in push_results if r.status == "skipped")
        total_count = len(push_results)

        logger.debug("=" * 80)
        logger.debug("PUSH OPERATION SUMMARY")
        logger.debug("-" * 80)
        logger.debug(f"Total build servers: {total_count}")
        logger.debug(f"  ✓ Successful: {success_count}")
        logger.debug(f"  ✗ Failed: {failed_count}")
        logger.debug(f"  ⊘ Skipped: {skipped_count}")
        logger.debug(f"Total preconfigs processed: {len(preconfigs_to_push)}")
        logger.debug(f"Total preconfigs pushed successfully: {len(pushed_preconfigs_data)}")
        logger.debug("-" * 80)

        if failed_count == 0 and success_count > 0:
            overall_status = "success"
            message = f"Successfully pushed preconfigs to {success_count} build server(s)"
        elif success_count > 0:
            overall_status = "partial"
            message = f"Pushed to {success_count}/{total_count - skipped_count} build servers"
        elif skipped_count == total_count:
            overall_status = "success"
            message = "No preconfigs matched any build server configurations"
        else:
            overall_status = "failed"
            message = "Failed to push to any build servers"

        logger.debug(f"Overall status: {overall_status}")
        logger.debug(f"Response message: {message}")
        logger.debug("=" * 80)

        return PushPreconfigResponse(
            status=overall_status,
            message=message,
            results=push_results,
            pushed_preconfigs=pushed_preconfigs_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing preconfig: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to push preconfig",
        )
    finally:
        # Always release the lock when done
        if db is not None:
            try:
                logger.debug(f"Releasing lock for region {region_lower}...")
                await release_lock(db, region_lower, current_user)
                logger.debug(f"✓ Lock released successfully for region {region_lower}")
            except Exception as e:
                logger.error(f"✗ Error releasing lock for {region_lower}: {e}")
                logger.debug(f"Lock release error details: {str(e)}", exc_info=True)
