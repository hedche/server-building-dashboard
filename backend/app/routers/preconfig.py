"""
Preconfig management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, PreconfigData, PushPreconfigRequest, PushPreconfigResponse
from app.auth import get_current_user
from app.config import settings
from app.db.models import PreconfigDB
from app.permissions import (
    check_region_access,
    check_depot_access,
    get_region_for_depot,
    get_depot_for_region,
)
from app.routers.config import get_config

logger = logging.getLogger(__name__)

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
    """
    all_preconfigs = [
        PreconfigData(
            dbid="dbid-001",
            depot=1,
            appliance_size="small",
            config={
                "os": "Ubuntu 22.04 LTS",
                "cpu": "2x Intel Xeon Gold 6248R",
                "ram": "128GB DDR4",
                "storage": "4x 1TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 25Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-002",
            depot=1,
            appliance_size="medium",
            config={
                "os": "CentOS 8 Stream",
                "cpu": "2x AMD EPYC 7502",
                "ram": "256GB DDR4",
                "storage": "8x 2TB NVMe SSD",
                "raid": "RAID 6",
                "network": "2x 100Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-003",
            depot=1,
            appliance_size="large",
            config={
                "os": "Rocky Linux 9",
                "cpu": "2x AMD EPYC 7763",
                "ram": "512GB DDR4",
                "storage": "12x 4TB NVMe SSD",
                "raid": "RAID 10",
                "network": "4x 100Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-004",
            depot=2,
            appliance_size="small",
            config={
                "os": "Ubuntu 22.04 LTS",
                "cpu": "2x Intel Xeon Gold 6348",
                "ram": "128GB DDR4",
                "storage": "4x 1TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 25Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-005",
            depot=2,
            appliance_size="medium",
            config={
                "os": "Ubuntu 22.04 LTS",
                "cpu": "2x Intel Xeon Gold 6348",
                "ram": "256GB DDR4",
                "storage": "8x 2TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 100Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-006",
            depot=4,
            appliance_size="small",
            config={
                "os": "Rocky Linux 9",
                "cpu": "2x AMD EPYC 7763",
                "ram": "128GB DDR4",
                "storage": "4x 1TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 25Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            dbid="dbid-007",
            depot=4,
            appliance_size="large",
            config={
                "os": "Rocky Linux 9",
                "cpu": "2x AMD EPYC 7763",
                "ram": "1TB DDR4",
                "storage": "16x 8TB NVMe SSD",
                "raid": "RAID 60",
                "network": "4x 100Gbps",
            },
            created_at=datetime.utcnow(),
        ),
    ]
    return [p for p in all_preconfigs if p.depot == depot]


def generate_mock_pushed_preconfigs() -> List[PreconfigData]:
    """
    Generate mock pushed preconfig data
    Simulates preconfigs that have been pushed to depots
    """
    now = datetime.utcnow()
    return [
        PreconfigData(
            dbid="pushed-001",
            depot=1,
            appliance_size="small",
            config={
                "os": "Ubuntu 20.04 LTS",
                "cpu": "2x Intel Xeon Gold 6248R",
                "ram": "128GB DDR4",
                "storage": "4x 1TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 25Gbps",
            },
            created_at=now,
            pushed_at=now,
        ),
        PreconfigData(
            dbid="pushed-002",
            depot=2,
            appliance_size="medium",
            config={
                "os": "Ubuntu 22.04 LTS",
                "cpu": "2x Intel Xeon Gold 6348",
                "ram": "512GB DDR4",
                "storage": "12x 4TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 100Gbps",
            },
            created_at=now,
            pushed_at=now,
        ),
    ]


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
                pushed_at=p.pushed_at,
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


@router.post(
    "/push-preconfig",
    response_model=PushPreconfigResponse,
    summary="Push preconfig to depot",
    description="Push preconfig to a specific depot (region)",
)
async def push_preconfig(
    request: PushPreconfigRequest, current_user: User = Depends(get_current_user)
) -> PushPreconfigResponse:
    """
    Push preconfig to a specific depot
    Simulates pushing configuration to build system
    """
    try:
        logger.info(
            f"Push preconfig to depot {request.depot} requested by {current_user.email}"
        )

        # Check user has permission for this depot
        if not check_depot_access(current_user.email, request.depot):
            region_name = get_region_for_depot(request.depot) or "Unknown"
            logger.warning(f"Depot access denied for {current_user.email} to depot {request.depot}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not have permission to push to depot {request.depot} ({region_name})"
            )

        depot_to_region = _get_depot_to_region()
        region = depot_to_region.get(request.depot, "Unknown")

        # Simulate preconfig push operation
        # In production, this would:
        # 1. Validate preconfig exists
        # 2. Push to build system
        # 3. Update database status
        # 4. Potentially trigger webhooks/notifications

        logger.info(
            f"Preconfig pushed to depot {request.depot} ({region}) successfully"
        )

        return PushPreconfigResponse(
            status="success",
            message=f"Preconfig pushed to depot {request.depot} ({region}) successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing preconfig: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to push preconfig",
        )


@router.get(
    "/preconfigs/pushed",
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
