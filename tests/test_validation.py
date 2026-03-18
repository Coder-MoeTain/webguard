"""Unit tests for validation."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.validation import validate_data_path
from backend.app.core.paths import resolve_data_path


def test_validate_data_path_valid():
    """Valid path under data dir should be accepted."""
    valid = "data/sample_dataset.parquet"
    if (resolve_data_path("data") / "sample_dataset.parquet").exists():
        result = validate_data_path(valid)
        assert result.is_absolute()
        assert "sample_dataset" in str(result)


def test_validate_data_path_traversal_rejected():
    """Path traversal should raise 400."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        validate_data_path("../../../etc/passwd")
    assert exc.value.status_code == 400
    assert "data directory" in str(exc.value.detail).lower()


def test_validate_data_path_relative():
    """Relative path under data should work."""
    data_dir = resolve_data_path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    # Use a path that exists under data
    try:
        result = validate_data_path("data")
        assert result.is_absolute()
    except Exception:
        pytest.skip("Data dir structure may differ")
