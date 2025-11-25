"""
Preconfig management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from datetime import datetime

from app.models import User, PreconfigData, PushPreconfigRequest, PushPreconfigResponse
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_mock_preconfigs() -> List[PreconfigData]:
    """
    Generate mock preconfig data
    Simulates preconfig records from database
    """
    return [
        PreconfigData(
            id="pre-001",
            depot=1,
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
            id="pre-002",
            depot=1,
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
            id="pre-003",
            depot=2,
            config={
                "os": "Ubuntu 22.04 LTS",
                "cpu": "2x Intel Xeon Gold 6348",
                "ram": "512GB DDR4",
                "storage": "12x 4TB NVMe SSD",
                "raid": "RAID 10",
                "network": "2x 100Gbps",
            },
            created_at=datetime.utcnow(),
        ),
        PreconfigData(
            id="pre-004",
            depot=4,
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


def generate_mock_pushed_preconfigs() -> List[PreconfigData]:
    """
    Generate mock pushed preconfig data
    Simulates preconfigs that have been pushed to depots
    """
    now = datetime.utcnow()
    return [
        PreconfigData(
            id="pushed-001",
            depot=1,
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
            id="pushed-002",
            depot=2,
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


@router.get(
    "/preconfigs",
    response_model=List[PreconfigData],
    summary="Get all preconfigs",
    description="Get all preconfigurations across all depots",
)
async def get_preconfigs(
    current_user: User = Depends(get_current_user),
) -> List[PreconfigData]:
    """
    Get all preconfigurations
    Returns list of preconfig records
    """
    try:
        logger.info(f"Preconfigs requested by {current_user.email}")

        # Simulate database query
        preconfigs = generate_mock_preconfigs()

        return preconfigs

    except Exception as e:
        logger.error(f"Error fetching preconfigs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preconfigs",
        )


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

        # Map depot to region for logging
        depot_map = {1: "CBG", 2: "DUB", 4: "DAL"}
        region = depot_map.get(request.depot, "Unknown")

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
    """
    try:
        logger.info(f"Pushed preconfigs requested by {current_user.email}")

        # Simulate database query
        preconfigs = generate_mock_pushed_preconfigs()

        return preconfigs

    except Exception as e:
        logger.error(f"Error fetching pushed preconfigs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pushed preconfigs",
        )
