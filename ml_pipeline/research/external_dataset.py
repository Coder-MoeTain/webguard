"""
Validate external raw datasets for the same labeling convention as the training pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import FrozenSet

import pandas as pd

REQUIRED_COLUMNS: FrozenSet[str] = frozenset({"payload", "label"})


def validate_raw_research_dataset(df: pd.DataFrame) -> None:
    """Raise ValueError if the frame cannot be used for feature extraction + supervised training."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")
    if df["payload"].isna().all():
        raise ValueError("Column 'payload' is all null")
    if df["label"].isna().all():
        raise ValueError("Column 'label' is all null")


def load_raw_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)
