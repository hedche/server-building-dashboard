"""
Server assignment endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.models import User, AssignRequest, AssignResponse
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/assign",
    response_model=AssignResponse,
    summary="Assign server",
    description="Assign a completed server to a customer",
)
async def assign_server(
    request: AssignRequest, current_user: User = Depends(get_current_user)
) -> AssignResponse:
    """
    Assign a server to a customer
    Updates server status and creates assignment record
    """
    try:
        logger.info(
            f"Server assignment requested by {current_user.email}: "
            f"hostname={request.hostname}, dbid={request.dbid}, sn={request.serial_number}"
        )

        # Validate request data
        if not all([request.serial_number, request.hostname, request.dbid]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Serial number, hostname, and DBID are required",
            )

        # Simulate assignment operation
        # In production, this would:
        # 1. Verify server exists and is available
        # 2. Check server build status is complete
        # 3. Verify user has permission to assign
        # 4. Create assignment record in database
        # 5. Update server status to 'assigned'
        # 6. Potentially trigger provisioning workflows
        # 7. Send notifications

        logger.info(
            f"Server assigned successfully: hostname={request.hostname}, "
            f"dbid={request.dbid} by {current_user.email}"
        )

        return AssignResponse(
            status="success", message=f"Server {request.hostname} assigned successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign server",
        )
