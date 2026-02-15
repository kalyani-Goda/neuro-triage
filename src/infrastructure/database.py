"""Database connection and ORM setup."""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

from src.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy base class for models
Base = declarative_base()

# Create database engine
engine: Engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,  # Prevent connection pooling issues in async context
)


def get_session():
    """Get a new database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
