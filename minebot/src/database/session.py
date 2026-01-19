import contextlib
from logging import Logger
from typing import AsyncGenerator, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database import Base, create_engine, engine
from debug import get_logger

logger: Logger = get_logger(__name__)

# Session factory will be initialized later
AsyncSessionLocal = None

T = TypeVar("T")


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Creates a new SQLAlchemy AsyncSession that automatically handles
    commit/rollback and closes the session when the context exists.

    Yields:
        AsyncSession: The SQLAlchemy async session

    Example:
        async with get_db_session() as session:
            result = await session.execute(...)
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")

    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Unexpected error during database operation: {e}")
        raise
    finally:
        await session.close()


async def initialize_database() -> None:
    """
    Initialize the database by creating all tables.

    This should be called during application startup to ensure
    all tables defined in models are created in the database.
    """
    from database.models import (  # noqa: F401
        PunishmentLog,
        TemporaryAction,
        TicketChannel,
        TicketInfo,
        User,
    )

    try:
        # Create engine and session factory
        global AsyncSessionLocal, engine
        if engine is None:
            engine = create_engine()
            if engine is None:
                raise RuntimeError("Failed to create database engine")

        AsyncSessionLocal = async_sessionmaker(
            engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
            class_=AsyncSession,
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.critical(f"Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close database connections and dispose of the engine.
    """
    from database.base import engine

    try:
        if engine is not None:
            logger.info("Closing database engine and releasing connections...")
            await engine.dispose()
            logger.info("Database connections successfully closed")
    except Exception as e:
        logger.error(f"Error while closing database connections: {e}")
