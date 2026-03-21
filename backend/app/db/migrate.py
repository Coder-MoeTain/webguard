"""
Run Alembic migrations programmatically (used on API startup).
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("webguard")


def run_alembic_upgrade(database_url: str) -> bool:
    """
    Apply all pending migrations (``alembic upgrade head``).

    Returns True if upgrade completed without exception.
    """
    try:
        from alembic import command
        from alembic.config import Config
    except ImportError:
        logger.warning("Alembic not installed; skipping migrations")
        return False

    # backend/app/db/migrate.py -> parents[3] = project root (contains alembic.ini)
    root = Path(__file__).resolve().parents[3]
    ini_path = root / "alembic.ini"
    if not ini_path.is_file():
        logger.warning("alembic.ini not found at %s; skipping migrations", ini_path)
        return False

    versions_dir = root / "alembic" / "versions"
    if not versions_dir.is_dir():
        logger.warning("alembic/versions missing; skipping migrations")
        return False

    try:
        cfg = Config(str(ini_path))
        cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(cfg, "head")
        logger.info("Database migrations applied (alembic upgrade head)")
        return True
    except Exception as e:
        logger.warning("Alembic upgrade failed: %s", e)
        return False
