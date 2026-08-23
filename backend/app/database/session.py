import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("adeip.database")

# Create synchronous SQLAlchemy engine
# pool_pre_ping=True ensures stale/dropped connections are tested and reconnected
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG and settings.APP_ENV == "development",
)

# Factory for creating thread-local database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Ensures the session is cleanly closed even if exceptions occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """
    Executes a lightweight query (SELECT 1) to verify database connectivity.
    Returns status dictionary for health check endpoints.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "connected", "database": "PostgreSQL"}
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return {"status": "disconnected", "database": "PostgreSQL", "error": str(exc) if settings.DEBUG else "Connection failed"}
