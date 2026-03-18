"""
WebGuard RF - Path resolution utilities
"""

from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/core -> project root


def resolve_data_path(path: str) -> Path:
    """Resolve a data path (relative or absolute) to an absolute Path."""
    p = Path(path)
    if not p.is_absolute():
        p = _PROJECT_ROOT / path
    return p.resolve()


def normalize_path_for_api(path: Path, base: Path | None = None) -> str:
    """Return path as forward-slash string. If base given, return path relative to base."""
    if base:
        try:
            rel = path.resolve().relative_to(base.resolve())
            return rel.as_posix()
        except ValueError:
            pass
    return path.as_posix()
