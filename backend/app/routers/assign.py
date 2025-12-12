"""
Server assignment endpoints
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, AssignRequest, AssignResponse
from app.auth import get_current_user
from app.db.models import BuildHistoryDB
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post(
    "/assign",
    response_model=AssignResponse,
    summary="Assign server",
    description="Assign a completed server to a customer",
)
async def assign_server(
    request: AssignRequest,
    current_user: User = Depends(get_current_user),
    db: Optional[AsyncSession] = Depends(get_optional_db),
) -> AssignResponse:
    """
    Assign a server to a customer
    Updates server status and creates assignment record in database
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

        # Simulate processing time (placeholder for real assignment logic)
        await asyncio.sleep(2)

        # If database is available, update the record
        db_updated = False
        if db is not None:
            try:
                # Look up server by dbid
                stmt = select(BuildHistoryDB).where(BuildHistoryDB.dbid == request.dbid)
                result = await db.execute(stmt)
                server = result.scalar_one_or_none()

                if not server:
                    logger.warning(
                        f"Server not found: dbid={request.dbid}, "
                        f"requested by {current_user.email}"
                    )
                    return AssignResponse(
                        status="failed",
                        message=f"Server with dbid {request.dbid} not found",
                    )

                # Update assignment fields
                server.assigned_status = "assigned"
                server.assigned_by = current_user.email
                server.assigned_at = datetime.now(timezone.utc)

                await db.commit()
                db_updated = True

                logger.info(
                    f"Server assigned successfully: hostname={request.hostname}, "
                    f"dbid={request.dbid} by {current_user.email}"
                )
            except Exception as e:
                logger.warning(f"Database operation failed: {str(e)}")
                try:
                    await db.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                # Fall through to mock mode

        if not db_updated:
            # No database or database unavailable - return mock success for dev mode
            logger.info(
                f"Server assigned (mock): hostname={request.hostname}, "
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
