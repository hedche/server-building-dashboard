"""
Build logs endpoints
"""
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
import logging

from app.models import User
from app.auth import get_current_user
from app.config import settings
from app.logger import buildlogs_logger

# Use dedicated buildlogs logger for detailed debugging
logger = buildlogs_logger
router = APIRouter()

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB limit


def sanitize_hostname(hostname: str) -> str:
    """Validate hostname to prevent path traversal attacks"""
    logger.debug(f"[BUILDLOG] Validating hostname: '{hostname}'")
    logger.debug(f"[BUILDLOG] Hostname length: {len(hostname)} characters")

    if not hostname or len(hostname) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname length"
        )

    logger.debug(f"[BUILDLOG] ✓ Length check passed ({len(hostname)} chars)")

    # Compile pattern from config
    hostname_pattern = re.compile(settings.HOSTNAME_PATTERN)
    logger.debug(f"[BUILDLOG] Using pattern: {settings.HOSTNAME_PATTERN}")

    if not hostname_pattern.match(hostname):
        logger.warning(f"Invalid hostname format attempted: {hostname}")
        logger.debug(f"[BUILDLOG] ✗ Hostname validation failed - invalid characters")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid hostname format. Only alphanumeric, dots, hyphens, and underscores allowed."
        )

    logger.debug(f"[BUILDLOG] ✓ Hostname format valid")
    return hostname


def get_log_file_path(hostname: str) -> tuple[Path, str]:
    """
    Get and validate log file path in nested directory structure.

    Searches for: BUILD_LOGS/{build_server}/{hostname}/{hostname}-Installer.log

    Args:
        hostname: Server hostname to search for

    Returns:
        Tuple of (log_file_path, build_server_name)

    Raises:
        HTTPException: If logs dir not configured, hostname invalid, or log not found
    """
    logger.debug("[BUILDLOG] Starting file discovery...")
    logger.debug(f"[BUILDLOG] Searching in: {settings.BUILD_LOGS_DIR}")

    if not settings.BUILD_LOGS_DIR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Build logs directory not configured"
        )

    sanitized = sanitize_hostname(hostname)
    base_dir = Path(settings.BUILD_LOGS_DIR).resolve()

    # Check base directory exists and is accessible
    if not base_dir.exists():
        logger.warning(f"Build logs directory does not exist: {base_dir}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build log not found for hostname: {hostname}"
        )

    # Get all build_server subdirectories
    try:
        build_server_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    except PermissionError:
        logger.error(f"Permission denied reading build logs directory: {base_dir}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission denied reading build logs directory"
        )

    # Sort for deterministic first-match behavior
    build_server_dirs.sort()
    build_servers = [d.name for d in build_server_dirs]

    logger.debug(f"[BUILDLOG] Found {len(build_servers)} build server(s): {build_servers}")
    logger.debug("[BUILDLOG] Searching for log file...")
    logger.debug("-" * 80)

    # Search for hostname in each build_server directory
    for build_server_dir in build_server_dirs:
        build_server_name = build_server_dir.name

        logger.debug(f"[BUILDLOG] Checking build server: {build_server_name}")

        # Construct expected path: {build_server}/{hostname}/{hostname}-Installer.log
        candidate_path = build_server_dir / sanitized / f"{sanitized}-Installer.log"
        logger.debug(f"[BUILDLOG]   Candidate path: {candidate_path}")

        # Resolve path and security check
        try:
            resolved_path = candidate_path.resolve()
            logger.debug(f"[BUILDLOG]   Resolved path: {resolved_path}")

            # Security: Ensure resolved path is within BUILD_LOGS_DIR
            resolved_path.relative_to(base_dir)
            logger.debug(f"[BUILDLOG]   ✓ Path is within BUILD_LOGS_DIR")
        except (ValueError, RuntimeError):
            # Path traversal attempt or resolution error - skip this candidate
            logger.warning(f"Path resolution failed for {candidate_path}")
            logger.debug(f"[BUILDLOG]   ✗ Path resolution failed (security violation)")
            continue

        # Check if file exists and is a regular file
        if resolved_path.exists() and resolved_path.is_file():
            logger.info(f"Found log for {hostname} in build_server: {build_server_name}")
            logger.debug(f"[BUILDLOG] ✓ Log file found in build server: {build_server_name}")
            logger.debug(f"[BUILDLOG]   File path: {resolved_path}")
            logger.debug("-" * 80)
            return (resolved_path, build_server_name)

    # No match found in any build_server directory
    logger.info(f"Build log not found for hostname: {hostname}")
    logger.debug(f"[BUILDLOG] ⊘ No log file found after checking {len(build_servers)} build server(s)")
    logger.debug("-" * 80)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Build log not found for hostname: {hostname}"
    )


@router.get(
    "/build-logs/{hostname}",
    response_class=Response,
    summary="Get build log for hostname",
    description="""Returns the build log file content for the specified hostname.
    The build server name is returned in the X-Build-Server response header.

    Log file structure: BUILD_LOGS/{build_server}/{hostname}/{hostname}-Installer.log"""
)
async def get_build_log(
    hostname: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Get build log content for a specific hostname"""
    try:
        logger.info(f"Build log requested for {hostname} by {current_user.email}")

        # DEBUG: Log detailed request information
        logger.debug("=" * 80)
        logger.debug(f"BUILD LOG REQUEST - Hostname: {hostname}")
        logger.debug("=" * 80)
        logger.debug(f"User: {current_user.email} (Role: {current_user.role})")
        logger.debug(f"BUILD_LOGS_DIR: {settings.BUILD_LOGS_DIR}")
        logger.debug(f"HOSTNAME_PATTERN: {settings.HOSTNAME_PATTERN}")
        logger.debug("-" * 80)

        # Get log file path and build server name
        log_file, build_server = get_log_file_path(hostname)

        # Check file size
        file_size = log_file.stat().st_size
        logger.debug(f"[BUILDLOG] File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        logger.debug(f"[BUILDLOG] Size limit: {MAX_LOG_SIZE:,} bytes ({MAX_LOG_SIZE / 1024 / 1024:.0f} MB)")

        if file_size > MAX_LOG_SIZE:
            logger.warning(
                f"Build log too large: {hostname} in {build_server} ({file_size} bytes)"
            )
            logger.debug(f"[BUILDLOG] ✗ File exceeds size limit")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Build log file too large to display"
            )

        logger.debug(f"[BUILDLOG] ✓ File size within limits")

        # Read file content
        try:
            logger.debug(f"[BUILDLOG] Reading file with UTF-8 encoding...")
            logger.debug(f"[BUILDLOG] File: {log_file}")

            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.debug(f"[BUILDLOG] ✓ File read successful")
            logger.debug(f"[BUILDLOG] Content length: {len(content):,} characters")
            # Use repr to escape newlines in preview
            content_preview = repr(content[:100])
            logger.debug(f"[BUILDLOG] Content preview (first 100 chars): {content_preview}")

            # Return response with custom header
            logger.info(
                f"Returning log for {hostname} from build_server: {build_server} "
                f"({file_size} bytes)"
            )

            logger.debug("=" * 80)
            logger.debug("BUILD LOG RESPONSE SUMMARY")
            logger.debug("-" * 80)
            logger.debug(f"Status: 200 OK")
            logger.debug(f"Build Server: {build_server}")
            logger.debug(f"File Path: {log_file}")
            logger.debug(f"File Size: {file_size:,} bytes")
            logger.debug(f"Content Type: text/plain; charset=utf-8")
            logger.debug(f"X-Build-Server Header: {build_server}")
            logger.debug("=" * 80)
            return Response(
                content=content,
                media_type="text/plain; charset=utf-8",
                headers={"X-Build-Server": build_server}
            )

        except UnicodeDecodeError:
            logger.error(f"Build log encoding error: {hostname} in {build_server}")
            logger.debug(f"[BUILDLOG] ✗ UTF-8 decoding failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Build log file is not valid UTF-8"
            )
        except PermissionError:
            logger.error(f"Permission denied reading build log: {hostname} in {build_server}")
            logger.debug(f"[BUILDLOG] ✗ Permission denied reading file")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission denied reading build log"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching build log for {hostname}: {str(e)}")
        logger.debug(f"[BUILDLOG] ✗ Unexpected error occurred", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch build log"
        )
