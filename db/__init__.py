"""Database initialization and setup."""

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import declarative_base

# Base class for all models
Base = declarative_base()


def create_engine_from_url(database_url: str):
    """Create SQLAlchemy engine from database URL.

    Args:
        database_url: Database connection string

    Returns:
        SQLAlchemy Engine instance
    """
    # SQLite doesn't support pooling parameters
    if database_url.startswith("sqlite"):
        return sa_create_engine(
            database_url,
            echo=False,
        )

    # PostgreSQL/MySQL with connection pooling
    return sa_create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Max connections beyond pool_size
        echo=False,  # Don't log SQL queries (set True for debugging)
    )

