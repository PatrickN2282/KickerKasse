from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from app.core.config import settings, resolve_timezone_name

logger = logging.getLogger(__name__)

# Connection Pool
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "connect")
def _set_connection_timezone(dbapi_connection, _connection_record):
    timezone_name = resolve_timezone_name(settings.APP_TIMEZONE)
    cursor = dbapi_connection.cursor()
    try:
        try:
            cursor.execute("SET TIME ZONE %s", (timezone_name,))
        except Exception:
            logger.warning("Failed to set DB timezone '%s'; fallback to Europe/Berlin", timezone_name)
            cursor.execute("SET TIME ZONE %s", ("Europe/Berlin",))
    finally:
        cursor.close()


def get_db() -> Session:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
