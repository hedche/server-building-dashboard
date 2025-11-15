"""
Build status endpoints
Returns mock data simulating database responses
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from datetime import datetime, timedelta

from app.models import User, BuildStatus, BuildHistory, Server
from app.auth import get_current_user
from app.logger import api_logger, log_error

router = APIRouter()


def generate_mock_build_status() -> Dict[str, List[Server]]:
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
                status="installing"
            ),
            Server(
                rackID="2-A",
                hostname="cbg-srv-002",
                dbid="100002",
                serial_number="SN-CBG-002",
                percent_built=75,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing"
            ),
            Server(
                rackID="3-C",
                hostname="cbg-srv-003",
                dbid="100003",
                serial_number="SN-CBG-003",
                percent_built=100,
                assigned_status="assigned",
                machine_type="Server",
                status="complete"
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
                status="installing"
            ),
            Server(
                rackID="2-D",
                hostname="dub-srv-002",
                dbid="200002",
                serial_number="SN-DUB-002",
                percent_built=90,
                assigned_status="not assigned",
                machine_type="Server",
                status="installing"
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
                status="installing"
            ),
            Server(
                rackID="3-E",
                hostname="dal-srv-002",
                dbid="300002",
                serial_number="SN-DAL-002",
                percent_built=15,
                assigned_status="not assigned",
                machine_type="Server",
                status="failed"
            ),
        ]
    }


def generate_mock_build_history(date: str) -> Dict[str, List[Server]]:
    """
    Generate mock build history data for a specific date
    Simulates completed builds
    """
    return {
        "cbg": [
            Server(
                rackID="1-A",
                hostname=f"cbg-hist-{date}-001",
                dbid="400001",
                serial_number="SN-CBG-H001",
                percent_built=100,
                assigned_status="assigned",
                machine_type="Server",
                status="complete"
            ),
            Server(
                rackID="2-B",
                hostname=f"cbg-hist-{date}-002",
                dbid="400002",
                serial_number="SN-CBG-H002",
                percent_built=100,
                assigned_status="not assigned",
                machine_type="Server",
                status="complete"
            ),
        ],
        "dub": [
            Server(
                rackID="1-C",
                hostname=f"dub-hist-{date}-001",
                dbid="500001",
                serial_number="SN-DUB-H001",
                percent_built=100,
                assigned_status="assigned",
                machine_type="Server",
                status="complete"
            ),
        ],
        "dal": [
            Server(
                rackID="1-D",
                hostname=f"dal-hist-{date}-001",
                dbid="600001",
                serial_number="SN-DAL-H001",
                percent_built=100,
                assigned_status="not assigned",
                machine_type="Server",
                status="complete"
            ),
        ]
    }


@router.get(
    "/build-status",
    response_model=BuildStatus,
    summary="Get current build status",
    description="Get current build status across all regions"
)
async def get_build_status(
    current_user: User = Depends(get_current_user)
) -> BuildStatus:
    """
    Get current build status for all regions
    Returns active server builds with progress
    """
    try:
        api_logger.info(f"Build status requested by {current_user.email}")

        # Simulate database query
        data = generate_mock_build_status()

        return BuildStatus(**data)

    except Exception as e:
        log_error(e, context="Fetching build status", extra={"user": current_user.email})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build status"
        )


@router.get(
    "/build-history/{date}",
    response_model=BuildHistory,
    summary="Get build history",
    description="Get build history for a specific date (YYYY-MM-DD format)"
)
async def get_build_history(
    date: str,
    current_user: User = Depends(get_current_user)
) -> BuildHistory:
    """
    Get build history for a specific date
    Returns completed builds from that date
    """
    try:
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        api_logger.info(f"Build history for {date} requested by {current_user.email}")

        # Simulate database query
        data = generate_mock_build_history(date)

        return BuildHistory(**data)

    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context=f"Fetching build history for {date}", extra={"user": current_user.email})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build history"
        )