"""
Build history endpoints
Returns build records for specific regions and dates
"""

import logging
from datetime import date as date_type, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, BuildStatus, Server, BuildHistoryRecord, BuildHistoryResponse
from app.auth import get_current_user
from app.db.models import BuildHistoryDB
from app.routers.config import get_build_servers_for_region, get_config
from app.config import settings
from app.permissions import check_region_access

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_valid_regions() -> set:
    """Get valid regions from config"""
    config = get_config()
    return set(config.get("regions", {}).keys())


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


def _generate_mock_build_status() -> dict:
    """
    Generate mock build status data
    Simulates current active builds across regions
    """
    return {
        "cbg": [
            Server(
                rackID="1-E",
                hostname="cbg-srv-001",
                dbid="100001",
                serial_number="SN-CBG-001",
                percent_built=55,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing",
            ),
            Server(
                rackID="2-A",
                hostname="cbg-srv-002",
                dbid="100002",
                serial_number="SN-CBG-002",
                percent_built=75,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing",
            ),
            Server(
                rackID="3-C",
                hostname="cbg-srv-003",
                dbid="100003",
                serial_number="SN-CBG-003",
                percent_built=100,
                assigned_status="assigned",
                machine_type="Server",
                status="complete",
            ),
        ],
        "dub": [
            Server(
                rackID="1-B",
                hostname="dub-srv-001",
                dbid="200001",
                serial_number="SN-DUB-001",
                percent_built=45,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing",
            ),
            Server(
                rackID="2-D",
                hostname="dub-srv-002",
                dbid="200002",
                serial_number="SN-DUB-002",
                percent_built=90,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing",
            ),
        ],
        "dal": [
            Server(
                rackID="1-F",
                hostname="dal-srv-001",
                dbid="300001",
                serial_number="SN-DAL-001",
                percent_built=30,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing",
            ),
            Server(
                rackID="3-E",
                hostname="dal-srv-002",
                dbid="300002",
                serial_number="SN-DAL-002",
                percent_built=15,
                assigned_status="not assigned",
                machine_type="Server",
                status="failed",
            ),
        ],
    }


@router.get(
    "/build-status",
    response_model=BuildStatus,
    summary="Get current build status",
    description="Get current build status across all regions",
)
async def get_build_status(
    current_user: User = Depends(get_current_user),
) -> BuildStatus:
    """
    Get current build status for all regions
    Returns active server builds with progress
    Filtered by user's allowed regions (admins see all)
    """
    try:
        logger.info(f"Build status requested by {current_user.email}")

        # Simulate database query (TODO: implement real query)
        data = _generate_mock_build_status()

        # Filter by user's allowed regions (admins see all)
        if not current_user.is_admin:
            data = {
                region: servers
                for region, servers in data.items()
                if region in current_user.allowed_regions
            }

        return BuildStatus(**data)

    except Exception as e:
        logger.error(f"Error fetching build status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build status",
        )


async def _fetch_build_history(
    db: Optional[AsyncSession], region: str, date_str: str, user: User
) -> BuildHistoryResponse:
    """
    Fetch build history for a specific region and date from the database.

    Args:
        db: Database session (may be None if database not configured)
        region: Region code (cbg, dub, dal)
        date_str: Date in YYYY-MM-DD format
        user: Current user making the request

    Returns:
        BuildHistoryResponse with servers list
    """
    # Get build servers for this region
    build_servers = get_build_servers_for_region(region)

    if not build_servers:
        # Region has no build servers configured
        logger.warning(f"No build servers configured for region: {region}")
        return BuildHistoryResponse(region=region, date=date_str, servers=[])

    # If no database session, return empty result
    if db is None:
        logger.warning("No database connection available")
        return BuildHistoryResponse(region=region, date=date_str, servers=[])

    try:
        # Query filtered by build_server IN list AND date
        stmt = select(BuildHistoryDB).where(
            BuildHistoryDB.build_server.in_(build_servers),
            func.date(BuildHistoryDB.build_start) == date_str
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
    except Exception as e:
        # Database connection or query error - return empty result
        logger.warning(f"Database query failed for {region}/{date_str}: {str(e)}")
        return BuildHistoryResponse(region=region, date=date_str, servers=[])

    # Convert to response models
    servers: List[BuildHistoryRecord] = []
    for record in records:
        try:
            servers.append(BuildHistoryRecord.model_validate(record))
        except Exception as e:
            logger.warning(
                f"Failed to validate record {record.id}: {str(e)}"
            )

    logger.info(
        f"Build history for {region}/{date_str} requested by {user.email}: "
        f"found {len(servers)} servers"
    )

    return BuildHistoryResponse(region=region, date=date_str, servers=servers)


@router.get(
    "/build-history/{region}",
    response_model=BuildHistoryResponse,
    summary="Get build history for today",
    description="Get build history for a specific region for today's date",
)
async def get_build_history_today(
    region: str,
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_optional_db),
) -> BuildHistoryResponse:
    """
    Get build history for a specific region for today's date.

    Args:
        region: Region code (cbg, dub, dal)

    Returns:
        Build history records for the specified region
    """
    try:
        valid_regions = _get_valid_regions()
        if region not in valid_regions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid region. Must be one of: {', '.join(sorted(valid_regions))}",
            )

        # Check user has permission for this region
        if not check_region_access(current_user.email, region):
            logger.warning(f"Region access denied for {current_user.email} to {region}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not have permission to access region {region}"
            )

        today = date_type.today().isoformat()
        return await _fetch_build_history(db, region, today, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching build history for {region}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build history",
        )


@router.get(
    "/build-history/{region}/{date}",
    response_model=BuildHistoryResponse,
    summary="Get build history for date",
    description="Get build history for a specific region and date (YYYY-MM-DD format)",
)
async def get_build_history(
    region: str,
    date: str,
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_optional_db),
) -> BuildHistoryResponse:
    """
    Get build history for a specific region and date.

    Args:
        region: Region code (cbg, dub, dal)
        date: Date in YYYY-MM-DD format

    Returns:
        Build history records for the specified region and date
    """
    try:
        valid_regions = _get_valid_regions()
        if region not in valid_regions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid region. Must be one of: {', '.join(sorted(valid_regions))}",
            )

        # Check user has permission for this region
        if not check_region_access(current_user.email, region):
            logger.warning(f"Region access denied for {current_user.email} to {region}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: You do not have permission to access region {region}"
            )

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

        return await _fetch_build_history(db, region, date, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching build history for {region}/{date}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build history",
        )
