"""
WebGuard RF - Database session
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..core.config import settings
from .models import Base

_db_available = None
engine = None
SessionLocal = None


def _check_db():
    global _db_available, engine, SessionLocal
    if _db_available is not None:
        return _db_available
    if not getattr(settings, "USE_DATABASE", True):
        _db_available = False
        return False
    try:
        url = settings.DATABASE_URL
        engine = create_engine(url, pool_pre_ping=True, pool_recycle=300)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _db_available = True
    except Exception:
        _db_available = False
        engine = None
        SessionLocal = None
    return _db_available


def db_available() -> bool:
    return _check_db()


def init_db():
    """Initialize database and create tables."""
    return _check_db()


@contextmanager
def get_db():
    """Yield a database session. Use as context manager."""
    if not _check_db() or SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """Return a session for dependency injection. Use with Depends()."""
    if not _check_db() or SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
