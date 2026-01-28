"""
Tests for the region push lock service.

Note: These tests require a database connection to run properly.
When run without a database, they test the service logic using mocks.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import User, RegionLockInfo
from app.services.lock_service import (
    acquire_lock,
    release_lock,
    cleanup_expired_locks,
    get_lock_status,
    get_all_lock_statuses,
    DEFAULT_LOCK_TIMEOUT_SECONDS,
)


# Test fixtures
@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        id="user1@example.com",
        email="user1@example.com",
        name="Test User 1",
        role="user",
        groups=[],
        is_admin=False,
        allowed_regions=["cbg", "dub"],
    )


@pytest.fixture
def mock_user2():
    """Create a second mock user for testing."""
    return User(
        id="user2@example.com",
        email="user2@example.com",
        name="Test User 2",
        role="user",
        groups=[],
        is_admin=False,
        allowed_regions=["cbg"],
    )


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


class TestRegionLockInfo:
    """Tests for the RegionLockInfo model."""

    def test_unlocked_region(self):
        """Test creating an unlocked region lock info."""
        lock_info = RegionLockInfo(region="cbg", is_locked=False)
        assert lock_info.region == "cbg"
        assert lock_info.is_locked is False
        assert lock_info.locked_by_email is None
        assert lock_info.locked_by_name is None
        assert lock_info.locked_at is None
        assert lock_info.expires_at is None

    def test_locked_region(self):
        """Test creating a locked region lock info."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=300)

        lock_info = RegionLockInfo(
            region="cbg",
            is_locked=True,
            locked_by_email="user@example.com",
            locked_by_name="Test User",
            locked_at=now,
            expires_at=expires,
        )

        assert lock_info.region == "cbg"
        assert lock_info.is_locked is True
        assert lock_info.locked_by_email == "user@example.com"
        assert lock_info.locked_by_name == "Test User"
        assert lock_info.locked_at == now
        assert lock_info.expires_at == expires


class TestAcquireLock:
    """Tests for the acquire_lock function."""

    @pytest.mark.asyncio
    async def test_acquire_lock_no_existing_lock(self, mock_db, mock_user):
        """Test acquiring a lock when no lock exists."""
        # Setup: No existing lock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        # After insert, return a lock owned by the user
        mock_lock_after_insert = MagicMock()
        mock_lock_after_insert.region = "cbg"
        mock_lock_after_insert.locked_by_email = mock_user.email
        mock_lock_after_insert.locked_by_name = mock_user.name
        mock_lock_after_insert.locked_at = datetime.now(timezone.utc)
        mock_lock_after_insert.expires_at = datetime.now(timezone.utc) + timedelta(seconds=300)

        mock_result_after_insert = MagicMock()
        mock_result_after_insert.scalar_one_or_none.return_value = mock_lock_after_insert

        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),  # cleanup_expired_locks
            mock_result,  # check existing lock
            MagicMock(),  # insert
            mock_result_after_insert,  # verify lock
        ]

        success, lock_info = await acquire_lock(mock_db, "cbg", mock_user)

        assert success is True
        assert lock_info is None

    @pytest.mark.asyncio
    async def test_acquire_lock_own_lock_exists(self, mock_db, mock_user):
        """Test acquiring a lock when user already owns the lock."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=300)

        # Setup: Lock exists owned by the same user
        mock_existing_lock = MagicMock()
        mock_existing_lock.region = "cbg"
        mock_existing_lock.locked_by_email = mock_user.email
        mock_existing_lock.locked_by_name = mock_user.name
        mock_existing_lock.locked_at = now - timedelta(seconds=60)
        mock_existing_lock.expires_at = expires

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_lock

        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),  # cleanup_expired_locks
            mock_result,  # check existing lock
        ]

        success, lock_info = await acquire_lock(mock_db, "cbg", mock_user)

        assert success is True
        assert lock_info is None
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_acquire_lock_blocked_by_another_user(self, mock_db, mock_user, mock_user2):
        """Test acquiring a lock when another user holds it."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=300)

        # Setup: Lock exists owned by another user
        mock_existing_lock = MagicMock()
        mock_existing_lock.region = "cbg"
        mock_existing_lock.locked_by_email = mock_user2.email
        mock_existing_lock.locked_by_name = mock_user2.name
        mock_existing_lock.locked_at = now - timedelta(seconds=60)
        mock_existing_lock.expires_at = expires

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_lock

        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),  # cleanup_expired_locks
            mock_result,  # check existing lock
        ]

        success, lock_info = await acquire_lock(mock_db, "cbg", mock_user)

        assert success is False
        assert lock_info is not None
        assert lock_info.is_locked is True
        assert lock_info.locked_by_email == mock_user2.email

    @pytest.mark.asyncio
    async def test_acquire_lock_expired_lock(self, mock_db, mock_user, mock_user2):
        """Test acquiring a lock when an expired lock exists."""
        now = datetime.now(timezone.utc)
        expired = now - timedelta(seconds=60)

        # Setup: Lock exists but is expired
        mock_existing_lock = MagicMock()
        mock_existing_lock.region = "cbg"
        mock_existing_lock.locked_by_email = mock_user2.email
        mock_existing_lock.locked_by_name = mock_user2.name
        mock_existing_lock.locked_at = expired - timedelta(seconds=240)
        mock_existing_lock.expires_at = expired

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_lock

        mock_db.execute.side_effect = [
            MagicMock(rowcount=0),  # cleanup_expired_locks
            mock_result,  # check existing lock
        ]

        success, lock_info = await acquire_lock(mock_db, "cbg", mock_user)

        assert success is True
        assert lock_info is None
        # Verify the lock was updated with the new user
        assert mock_existing_lock.locked_by_email == mock_user.email


class TestReleaseLock:
    """Tests for the release_lock function."""

    @pytest.mark.asyncio
    async def test_release_own_lock(self, mock_db, mock_user):
        """Test releasing a lock the user owns."""
        now = datetime.now(timezone.utc)

        # Setup: Lock exists owned by the user
        mock_existing_lock = MagicMock()
        mock_existing_lock.region = "cbg"
        mock_existing_lock.locked_by_email = mock_user.email
        mock_existing_lock.locked_by_name = mock_user.name
        mock_existing_lock.locked_at = now - timedelta(seconds=60)
        mock_existing_lock.expires_at = now + timedelta(seconds=240)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_lock

        mock_db.execute.side_effect = [
            mock_result,  # select
            MagicMock(),  # delete
        ]

        success = await release_lock(mock_db, "cbg", mock_user)

        assert success is True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_release_lock_not_owned(self, mock_db, mock_user, mock_user2):
        """Test releasing a lock the user doesn't own."""
        now = datetime.now(timezone.utc)

        # Setup: Lock exists owned by another user
        mock_existing_lock = MagicMock()
        mock_existing_lock.region = "cbg"
        mock_existing_lock.locked_by_email = mock_user2.email
        mock_existing_lock.locked_by_name = mock_user2.name
        mock_existing_lock.locked_at = now - timedelta(seconds=60)
        mock_existing_lock.expires_at = now + timedelta(seconds=240)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_lock

        mock_db.execute.return_value = mock_result

        success = await release_lock(mock_db, "cbg", mock_user)

        assert success is False

    @pytest.mark.asyncio
    async def test_release_nonexistent_lock(self, mock_db, mock_user):
        """Test releasing a lock that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        success = await release_lock(mock_db, "cbg", mock_user)

        # Should return True since there's nothing to release
        assert success is True


class TestGetLockStatus:
    """Tests for the get_lock_status function."""

    @pytest.mark.asyncio
    async def test_get_lock_status_locked(self, mock_db):
        """Test getting status of a locked region."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=300)

        mock_lock = MagicMock()
        mock_lock.region = "cbg"
        mock_lock.locked_by_email = "user@example.com"
        mock_lock.locked_by_name = "Test User"
        mock_lock.locked_at = now - timedelta(seconds=60)
        mock_lock.expires_at = expires

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lock

        mock_db.execute.return_value = mock_result

        lock_info = await get_lock_status(mock_db, "cbg")

        assert lock_info.region == "cbg"
        assert lock_info.is_locked is True
        assert lock_info.locked_by_email == "user@example.com"
        assert lock_info.locked_by_name == "Test User"

    @pytest.mark.asyncio
    async def test_get_lock_status_unlocked(self, mock_db):
        """Test getting status of an unlocked region."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        lock_info = await get_lock_status(mock_db, "cbg")

        assert lock_info.region == "cbg"
        assert lock_info.is_locked is False
        assert lock_info.locked_by_email is None

    @pytest.mark.asyncio
    async def test_get_lock_status_expired(self, mock_db):
        """Test getting status of an expired lock (should show as unlocked)."""
        now = datetime.now(timezone.utc)
        expired = now - timedelta(seconds=60)

        mock_lock = MagicMock()
        mock_lock.region = "cbg"
        mock_lock.locked_by_email = "user@example.com"
        mock_lock.locked_by_name = "Test User"
        mock_lock.locked_at = expired - timedelta(seconds=240)
        mock_lock.expires_at = expired

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lock

        mock_db.execute.return_value = mock_result

        lock_info = await get_lock_status(mock_db, "cbg")

        # Expired lock should show as unlocked
        assert lock_info.region == "cbg"
        assert lock_info.is_locked is False


class TestGetAllLockStatuses:
    """Tests for the get_all_lock_statuses function."""

    @pytest.mark.asyncio
    async def test_get_all_lock_statuses_multiple_locks(self, mock_db):
        """Test getting all lock statuses with multiple active locks."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=300)

        mock_lock1 = MagicMock()
        mock_lock1.region = "cbg"
        mock_lock1.locked_by_email = "user1@example.com"
        mock_lock1.locked_by_name = "User 1"
        mock_lock1.locked_at = now - timedelta(seconds=60)
        mock_lock1.expires_at = expires

        mock_lock2 = MagicMock()
        mock_lock2.region = "dub"
        mock_lock2.locked_by_email = "user2@example.com"
        mock_lock2.locked_by_name = "User 2"
        mock_lock2.locked_at = now - timedelta(seconds=30)
        mock_lock2.expires_at = expires

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lock1, mock_lock2]

        mock_db.execute.return_value = mock_result

        lock_statuses = await get_all_lock_statuses(mock_db)

        assert len(lock_statuses) == 2
        assert "cbg" in lock_statuses
        assert "dub" in lock_statuses
        assert lock_statuses["cbg"].locked_by_email == "user1@example.com"
        assert lock_statuses["dub"].locked_by_email == "user2@example.com"

    @pytest.mark.asyncio
    async def test_get_all_lock_statuses_no_locks(self, mock_db):
        """Test getting all lock statuses when no locks exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db.execute.return_value = mock_result

        lock_statuses = await get_all_lock_statuses(mock_db)

        assert len(lock_statuses) == 0


class TestCleanupExpiredLocks:
    """Tests for the cleanup_expired_locks function."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_removes_expired(self, mock_db):
        """Test that cleanup removes expired locks."""
        mock_result = MagicMock()
        mock_result.rowcount = 2

        mock_db.execute.return_value = mock_result

        count = await cleanup_expired_locks(mock_db)

        assert count == 2
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_region_specific(self, mock_db):
        """Test cleanup for a specific region."""
        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_db.execute.return_value = mock_result

        count = await cleanup_expired_locks(mock_db, region="cbg")

        assert count == 1
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_locks_none_to_clean(self, mock_db):
        """Test cleanup when no expired locks exist."""
        mock_result = MagicMock()
        mock_result.rowcount = 0

        mock_db.execute.return_value = mock_result

        count = await cleanup_expired_locks(mock_db)

        assert count == 0
        mock_db.commit.assert_called()


class TestDefaultLockTimeout:
    """Tests for lock timeout configuration."""

    def test_default_timeout_is_5_minutes(self):
        """Verify default lock timeout is 5 minutes (300 seconds)."""
        assert DEFAULT_LOCK_TIMEOUT_SECONDS == 300
