"""
Async Database Connection and Session Management
Uses SQLAlchemy 2.0 async patterns with aiomysql
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from settings with validation"""
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL not configured in environment")

    # Ensure async driver
    url = settings.DATABASE_URL
    if url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+aiomysql://", 1)
    elif url.startswith("mysql+pymysql://"):
        url = url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)

    return url


def create_engine() -> AsyncEngine:
    """Create async database engine with connection pooling"""
    database_url = get_database_url()

    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,  # SQL logging in debug mode
        pool_pre_ping=True,  # Test connections before using
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        # For testing, use NullPool to avoid connection issues
        poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    )

    logger.info(f"Database engine created: {database_url.split('@')[1] if '@' in database_url else 'configured'}")
    return engine


def get_engine() -> AsyncEngine:
    """Get or create the global engine"""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the global session factory"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session
    Usage: async def my_route(db: AsyncSession = Depends(get_db))
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables (dev only, use Alembic for production)"""
    engine = get_engine()
    async with engine.begin() as conn:
        # In development, we can auto-create tables for convenience
        # In production, ALWAYS use Alembic migrations
        if settings.ENVIRONMENT == "dev":
            logger.info("Creating database tables (dev mode)...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        else:
            logger.info("Production mode - use Alembic for schema management")


async def close_db():
    """Close database connections - call during app shutdown"""
    global _engine, _async_session_factory

    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")
        _engine = None
        _async_session_factory = None


@asynccontextmanager
async def get_db_context():
    """Context manager for manual database sessions (non-FastAPI contexts)"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
