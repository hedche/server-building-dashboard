"""
Build logs endpoints
"""
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
import logging

from app.models import User
from app.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Security: Hostname validation pattern
HOSTNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB limit


def sanitize_hostname(hostname: str) -> str:
    """Validate hostname to prevent path traversal attacks"""
    if not hostname or len(hostname) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname length"
        )

    if not HOSTNAME_PATTERN.match(hostname):
        logger.warning(f"Invalid hostname format attempted: {hostname}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname format. Only alphanumeric, dots, hyphens, and underscores allowed."
        )

    return hostname


def get_log_file_path(hostname: str) -> Path:
    """Get and validate log file path"""
    if not settings.BUILD_LOGS_DIR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Build logs directory not configured"
        )

    sanitized = sanitize_hostname(hostname)
    base_dir = Path(settings.BUILD_LOGS_DIR).resolve()
    log_file = (base_dir / f"{sanitized}.log").resolve()

    # Security: Ensure the resolved path is within BUILD_LOGS_DIR
    try:
        log_file.relative_to(base_dir)
    except ValueError:
        logger.error(f"Path traversal attempt detected: {hostname}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname"
        )

    return log_file


@router.get(
    "/build-logs/{hostname}",
    response_class=PlainTextResponse,
    summary="Get build log for hostname",
    description="Returns the build log file content for the specified hostname"
)
async def get_build_log(
    hostname: str,
    current_user: User = Depends(get_current_user),
) -> str:
    """Get build log content for a specific hostname"""
    try:
        logger.info(f"Build log requested for {hostname} by {current_user.email}")

        log_file = get_log_file_path(hostname)

        # Check if file exists
        if not log_file.exists():
            logger.info(f"Build log not found: {hostname}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Build log not found for hostname: {hostname}"
            )

        # Check file size
        file_size = log_file.stat().st_size
        if file_size > MAX_LOG_SIZE:
            logger.warning(f"Build log too large: {hostname} ({file_size} bytes)")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Build log file too large to display"
            )

        # Read file content
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            logger.error(f"Build log encoding error: {hostname}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Build log file is not valid UTF-8"
            )
        except PermissionError:
            logger.error(f"Permission denied reading build log: {hostname}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission denied reading build log"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching build log for {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build log"
        )
