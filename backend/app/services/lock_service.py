"""
Lock service for managing region push locks.

Provides atomic lock acquisition using MySQL INSERT ... ON DUPLICATE KEY UPDATE
to prevent race conditions when multiple users try to push to the same region.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
import logging

from sqlalchemy import select, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RegionPushLockDB
from app.models import User, RegionLockInfo
from app.logger import preconfig_logger

# Use dedicated preconfig logger for detailed debugging
logger = preconfig_logger

# Default lock timeout in seconds (5 minutes)
DEFAULT_LOCK_TIMEOUT_SECONDS = 300


async def acquire_lock(
    db: AsyncSession,
    region: str,
    user: User,
    timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> Tuple[bool, Optional[RegionLockInfo]]:
    """
    Attempt to acquire a lock for a region.

    Uses INSERT ... ON DUPLICATE KEY UPDATE with conditional update
    to ensure atomic lock acquisition.

    Args:
        db: Database session
        region: Region code (e.g., 'cbg', 'dub', 'dal')
        user: User attempting to acquire the lock
        timeout_seconds: Lock expiration time in seconds

    Returns:
        Tuple of (success, existing_lock_info):
        - If lock acquired: (True, None)
        - If lock exists and is held by another user: (False, RegionLockInfo)
        - If lock exists but is expired (and we claimed it): (True, None)
    """
    region_lower = region.lower()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=timeout_seconds)

    logger.debug(f"[LOCK] Acquire lock request: region={region_lower}, user={user.email}, timeout={timeout_seconds}s")

    try:
        # First, clean up any expired locks for this region
        logger.debug(f"[LOCK] Cleaning up expired locks for region {region_lower}...")
        cleanup_count = await cleanup_expired_locks(db, region_lower)
        if cleanup_count > 0:
            logger.debug(f"[LOCK] Cleaned up {cleanup_count} expired lock(s)")

        # Check for existing lock
        logger.debug(f"[LOCK] Checking for existing lock on region {region_lower}...")
        stmt = select(RegionPushLockDB).where(RegionPushLockDB.region == region_lower)
        result = await db.execute(stmt)
        existing_lock = result.scalar_one_or_none()

        if existing_lock:
            logger.debug(
                f"[LOCK] Existing lock found: locked_by={existing_lock.locked_by_email}, "
                f"locked_at={existing_lock.locked_at}, expires_at={existing_lock.expires_at}"
            )

            # Lock exists - check if it's ours or if it's expired
            if existing_lock.locked_by_email == user.email:
                # It's our lock - refresh it
                logger.debug(f"[LOCK] Lock belongs to current user - refreshing...")
                existing_lock.locked_at = now
                existing_lock.expires_at = expires_at
                await db.commit()
                logger.info(f"Lock refreshed for region {region_lower} by {user.email}")
                logger.debug(f"[LOCK] ✓ Lock refresh successful, new expiry: {expires_at}")
                return (True, None)

            if existing_lock.expires_at > now:
                # Lock is still valid and held by someone else
                time_remaining = (existing_lock.expires_at - now).total_seconds()
                logger.debug(
                    f"[LOCK] Lock is held by another user ({existing_lock.locked_by_email}), "
                    f"expires in {time_remaining:.0f}s"
                )
                lock_info = RegionLockInfo(
                    region=existing_lock.region,
                    is_locked=True,
                    locked_by_email=existing_lock.locked_by_email,
                    locked_by_name=existing_lock.locked_by_name,
                    locked_at=existing_lock.locked_at,
                    expires_at=existing_lock.expires_at,
                )
                logger.info(
                    f"Lock acquisition failed for region {region_lower} by {user.email} - "
                    f"locked by {existing_lock.locked_by_email}"
                )
                logger.debug(f"[LOCK] ✗ Lock acquisition denied")
                return (False, lock_info)

            # Lock is expired - claim it
            logger.debug(f"[LOCK] Existing lock is expired - claiming it...")
            existing_lock.locked_by_email = user.email
            existing_lock.locked_by_name = user.name
            existing_lock.locked_at = now
            existing_lock.expires_at = expires_at
            await db.commit()
            logger.info(f"Expired lock claimed for region {region_lower} by {user.email}")
            logger.debug(f"[LOCK] ✓ Expired lock claimed successfully")
            return (True, None)

        # No lock exists - create one using INSERT ... ON DUPLICATE KEY UPDATE
        # This handles the race condition where two users try to create at the same time
        logger.debug(f"[LOCK] No existing lock found - creating new lock...")
        stmt = insert(RegionPushLockDB).values(
            region=region_lower,
            locked_by_email=user.email,
            locked_by_name=user.name,
            locked_at=now,
            expires_at=expires_at,
        )

        # Only update if the existing lock is expired
        stmt = stmt.on_duplicate_key_update(
            locked_by_email=stmt.inserted.locked_by_email,
            locked_by_name=stmt.inserted.locked_by_name,
            locked_at=stmt.inserted.locked_at,
            expires_at=stmt.inserted.expires_at,
        )

        logger.debug(f"[LOCK] Executing INSERT with ON DUPLICATE KEY UPDATE...")
        await db.execute(stmt)
        await db.commit()
        logger.debug(f"[LOCK] Insert/update committed to database")

        # Verify we got the lock by reading it back
        logger.debug(f"[LOCK] Verifying lock ownership...")
        result = await db.execute(
            select(RegionPushLockDB).where(RegionPushLockDB.region == region_lower)
        )
        lock = result.scalar_one_or_none()

        if lock and lock.locked_by_email == user.email:
            logger.info(f"Lock acquired for region {region_lower} by {user.email}")
            logger.debug(f"[LOCK] ✓ Lock creation successful, expires at {lock.expires_at}")
            return (True, None)
        else:
            # Another user won the race
            logger.debug(
                f"[LOCK] Race condition detected - another user acquired the lock: "
                f"{lock.locked_by_email if lock else 'unknown'}"
            )
            lock_info = RegionLockInfo(
                region=lock.region if lock else region_lower,
                is_locked=True,
                locked_by_email=lock.locked_by_email if lock else "unknown",
                locked_by_name=lock.locked_by_name if lock else None,
                locked_at=lock.locked_at if lock else now,
                expires_at=lock.expires_at if lock else now,
            )
            logger.info(
                f"Lock acquisition failed (race) for region {region_lower} by {user.email}"
            )
            logger.debug(f"[LOCK] ✗ Lost race condition")
            return (False, lock_info)

    except Exception as e:
        logger.error(f"Error acquiring lock for region {region_lower}: {e}")
        logger.debug(f"[LOCK] Exception during lock acquisition: {str(e)}", exc_info=True)
        await db.rollback()
        raise


async def release_lock(
    db: AsyncSession,
    region: str,
    user: User,
) -> bool:
    """
    Release a lock for a region.

    Only the user who holds the lock can release it.

    Args:
        db: Database session
        region: Region code
        user: User attempting to release the lock

    Returns:
        True if lock was released, False if user didn't hold the lock
    """
    region_lower = region.lower()

    logger.debug(f"[LOCK] Release lock request: region={region_lower}, user={user.email}")

    try:
        logger.debug(f"[LOCK] Checking for existing lock on region {region_lower}...")
        stmt = select(RegionPushLockDB).where(RegionPushLockDB.region == region_lower)
        result = await db.execute(stmt)
        lock = result.scalar_one_or_none()

        if not lock:
            # No lock to release
            logger.debug(f"[LOCK] No lock found to release for region {region_lower}")
            return True

        logger.debug(
            f"[LOCK] Lock found: locked_by={lock.locked_by_email}, "
            f"locked_at={lock.locked_at}, expires_at={lock.expires_at}"
        )

        if lock.locked_by_email != user.email:
            # User doesn't own the lock
            logger.warning(
                f"User {user.email} attempted to release lock held by {lock.locked_by_email} "
                f"for region {region_lower}"
            )
            logger.debug(f"[LOCK] ✗ Lock release denied - not owned by requesting user")
            return False

        # Delete the lock
        logger.debug(f"[LOCK] Deleting lock for region {region_lower}...")
        await db.execute(
            delete(RegionPushLockDB).where(RegionPushLockDB.region == region_lower)
        )
        await db.commit()

        logger.info(f"Lock released for region {region_lower} by {user.email}")
        logger.debug(f"[LOCK] ✓ Lock deleted successfully")
        return True

    except Exception as e:
        logger.error(f"Error releasing lock for region {region_lower}: {e}")
        logger.debug(f"[LOCK] Exception during lock release: {str(e)}", exc_info=True)
        await db.rollback()
        raise


async def cleanup_expired_locks(
    db: AsyncSession,
    region: Optional[str] = None,
) -> int:
    """
    Remove expired locks from the database.

    Args:
        db: Database session
        region: Optional region to clean up. If None, cleans up all expired locks.

    Returns:
        Number of locks cleaned up
    """
    now = datetime.now(timezone.utc)

    if region:
        logger.debug(f"[LOCK] Cleanup expired locks for region: {region.lower()}")
    else:
        logger.debug(f"[LOCK] Cleanup all expired locks")

    try:
        if region:
            stmt = delete(RegionPushLockDB).where(
                RegionPushLockDB.region == region.lower(),
                RegionPushLockDB.expires_at < now,
            )
        else:
            stmt = delete(RegionPushLockDB).where(RegionPushLockDB.expires_at < now)

        result = await db.execute(stmt)
        count = result.rowcount
        await db.commit()

        if count > 0:
            logger.info(f"Cleaned up {count} expired lock(s)")
            logger.debug(f"[LOCK] ✓ Deleted {count} expired lock(s)")
        else:
            logger.debug(f"[LOCK] No expired locks to clean up")

        return count

    except Exception as e:
        logger.error(f"Error cleaning up expired locks: {e}")
        logger.debug(f"[LOCK] Exception during cleanup: {str(e)}", exc_info=True)
        await db.rollback()
        raise


async def get_lock_status(
    db: AsyncSession,
    region: str,
) -> RegionLockInfo:
    """
    Get the lock status for a specific region.

    Args:
        db: Database session
        region: Region code

    Returns:
        RegionLockInfo with current lock status
    """
    region_lower = region.lower()
    now = datetime.now(timezone.utc)

    try:
        stmt = select(RegionPushLockDB).where(RegionPushLockDB.region == region_lower)
        result = await db.execute(stmt)
        lock = result.scalar_one_or_none()

        if lock and lock.expires_at > now:
            return RegionLockInfo(
                region=lock.region,
                is_locked=True,
                locked_by_email=lock.locked_by_email,
                locked_by_name=lock.locked_by_name,
                locked_at=lock.locked_at,
                expires_at=lock.expires_at,
            )

        return RegionLockInfo(
            region=region_lower,
            is_locked=False,
        )

    except Exception as e:
        logger.error(f"Error getting lock status for region {region_lower}: {e}")
        raise


async def get_all_lock_statuses(
    db: AsyncSession,
) -> dict[str, RegionLockInfo]:
    """
    Get lock status for all regions.

    Args:
        db: Database session

    Returns:
        Dictionary mapping region code to RegionLockInfo
    """
    now = datetime.now(timezone.utc)

    try:
        stmt = select(RegionPushLockDB).where(RegionPushLockDB.expires_at > now)
        result = await db.execute(stmt)
        locks = result.scalars().all()

        lock_statuses = {}
        for lock in locks:
            lock_statuses[lock.region] = RegionLockInfo(
                region=lock.region,
                is_locked=True,
                locked_by_email=lock.locked_by_email,
                locked_by_name=lock.locked_by_name,
                locked_at=lock.locked_at,
                expires_at=lock.expires_at,
            )

        return lock_statuses

    except Exception as e:
        logger.error(f"Error getting all lock statuses: {e}")
        raise
