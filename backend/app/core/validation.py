"""
WebGuard RF - Path and input validation
"""

from pathlib import Path

from fastapi import HTTPException

from .config import settings
from .paths import resolve_data_path


def validate_data_path(path_str: str) -> Path:
    """Ensure path is under DATA_DIR to prevent path traversal."""
    resolved = resolve_data_path(path_str)
    data_dir = resolve_data_path(settings.DATA_DIR)
    try:
        resolved.relative_to(data_dir)
    except ValueError:
        raise HTTPException(400, "Path must be under data directory")
    return resolved


def validate_models_path(path_str: str) -> Path:
    """Ensure path is under MODELS_DIR."""
    path = Path(path_str).resolve()
    models_dir = Path(settings.MODELS_DIR).resolve()
    if not str(path).startswith(str(models_dir)):
        raise HTTPException(400, "Path must be under models directory")
    return path
