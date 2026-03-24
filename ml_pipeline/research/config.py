"""Load YAML experiment definitions for reproducible research runs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise ImportError("Install PyYAML to use research configs: pip install pyyaml") from e


DEFAULT_RESEARCH_CONFIG: Dict[str, Any] = {
    "featured_data_path": "data/sample_features.parquet",
    "raw_data_path": "data/sample_dataset.parquet",
    "feature_extraction": {
        "enabled": False,
        "raw_path": "data/sample_dataset.parquet",
        "output_path": "data/research_features.parquet",
        "feature_mode": "payload_only",
    },
    "training": {
        "classification_mode": "multiclass",
        "feature_mode": "payload_only",
        "algorithms": ["random_forest"],
        "seeds": [42, 43, 44],
        "n_estimators": 100,
        "max_depth": 20,
        "output_dir": "models/research",
        "bootstrap_resamples": 500,
        "extended_research_metrics": True,
        "extended_research_on_last_seed_only": True,
    },
    "evasion": {
        "enabled": True,
        "n_samples": 300,
        "transforms": None,
    },
    "report_dir": "data/research_reports",
}


def load_research_config(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}
    cfg = deepcopy(DEFAULT_RESEARCH_CONFIG)
    _deep_merge(cfg, user)
    return cfg


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
