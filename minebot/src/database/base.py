from logging import Logger
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import declarative_base

from debug import get_logger
from model import DatabaseKeys
from settings import Settings

logger: Logger = get_logger(__name__)

# Create base class for models
Base: Any = declarative_base()

# Initialize engine variable but don't create it yet
engine: AsyncEngine | None = None


def ensure_sqlite_folder_exists(db_url: str) -> None:
    """
    Ensure the folder for a SQLite database exists if the database URL points to a SQLite file.
    """
    if db_url.startswith("sqlite+aiosqlite:///"):
        db_path = db_url.replace("sqlite+aiosqlite:///", "", 1)
        folder = Path(db_path).parent
        if folder and not folder.exists():
            logger.info(f"Creating directory for SQLite database: {folder}")
            folder.mkdir(parents=True, exist_ok=True)


def create_engine() -> AsyncEngine:
    """
    Create and return a SQLAlchemy async engine using settings from configuration.
    """
    global engine

    db_url = Settings.get(DatabaseKeys.URL)

    # Ensure SQLite folder exists if necessary
    ensure_sqlite_folder_exists(db_url)

    logger.info("Creating database engine")
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
    )
    return engine
