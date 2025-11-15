"""
Server details endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
from datetime import datetime, timedelta

from app.models import User, ServerDetails
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_mock_server_details(hostname: str) -> ServerDetails:
    """
    Generate mock server details
    Simulates detailed server information from database
    """
    return ServerDetails(
        rackID="1-E",
        hostname=hostname,
        dbid="100001",
        serial_number="SN-SERVER-001",
        percent_built=65,
        assigned_status="not assigned",
        machine_type="Server",
        status="installing",
        ip_address="192.168.1.100",
        mac_address="00:1A:2B:3C:4D:5E",
        cpu_model="Intel Xeon Gold 6248R",
        ram_gb=128,
        storage_gb=4000,
        install_start_time=datetime.utcnow() - timedelta(hours=2),
        estimated_completion=datetime.utcnow() + timedelta(hours=1),
        last_heartbeat=datetime.utcnow() - timedelta(minutes=5),
    )


@router.get(
    "/server-details",
    response_model=ServerDetails,
    summary="Get server details",
    description="Get detailed information about a specific server by hostname",
)
async def get_server_details(
    hostname: str = Query(..., description="Server hostname"),
    current_user: User = Depends(get_current_user),
) -> ServerDetails:
    """
    Get detailed information about a specific server
    Returns comprehensive server data including hardware specs and timing
    """
    try:
        if not hostname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Hostname is required"
            )

        logger.info(f"Server details for {hostname} requested by {current_user.email}")

        # Simulate database query
        server_details = generate_mock_server_details(hostname)

        return server_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching server details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch server details",
        )
