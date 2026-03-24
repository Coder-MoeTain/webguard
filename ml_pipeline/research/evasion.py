"""
Simple payload transforms for robustness / evasion experiments (research baseline battery).
Not a full attacker model — documents sensitivity to common obfuscations.
"""

from __future__ import annotations

import random
import re
import urllib.parse
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ml_pipeline.feature_extraction import FeatureExtractor

TransformFn = Callable[[str, random.Random], str]

_TRANSFORMS: Dict[str, TransformFn] = {}


def register(name: str):
    def deco(fn: TransformFn) -> TransformFn:
        _TRANSFORMS[name] = fn
        return fn

    return deco


@register("identity")
def _identity(payload: str, rng: random.Random) -> str:
    return payload


@register("url_encode_all")
def _url_encode_all(payload: str, rng: random.Random) -> str:
    return urllib.parse.quote(payload, safe="")


@register("insert_space_after_keywords")
def _space_keywords(payload: str, rng: random.Random) -> str:
    p = payload
    for kw in ("SELECT", "UNION", "OR", "AND", "FROM", "WHERE"):
        p = re.sub(rf"(?i)({kw})(?=\s)", r"\1/**/", p)
    return p


@register("random_case")
def _random_case(payload: str, rng: random.Random) -> str:
    return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in payload)


@register("double_url_encode_percent")
def _double_enc(payload: str, rng: random.Random) -> str:
    return payload.replace("%", "%25")


def list_transform_names() -> List[str]:
    return sorted(_TRANSFORMS.keys())


def apply_transform(name: str, payload: str, rng: Optional[random.Random] = None) -> str:
    rng = rng or random.Random(0)
    fn = _TRANSFORMS.get(name)
    if fn is None:
        raise ValueError(f"Unknown transform: {name}. Known: {list_transform_names()}")
    return fn(payload, rng)


def run_evasion_battery(
    raw_df: pd.DataFrame,
    model: Any,
    feature_columns: List[str],
    feature_mode: str,
    transform_names: Optional[List[str]] = None,
    n_samples: int = 400,
    random_state: int = 42,
    label_col: str = "label",
) -> Dict[str, Any]:
    """
    Sample rows from a raw dataset (must include ``payload``), re-extract features after
    each transform, and report accuracy vs. labels mapped the same way as training
    (multiclass string labels on rows).
    """
    if "payload" not in raw_df.columns:
        raise ValueError("raw_df must contain a 'payload' column")
    if label_col not in raw_df.columns:
        raise ValueError(f"raw_df must contain '{label_col}'")

    from ml_pipeline.training.preprocessing import LABEL_MAP_MULTICLASS, LABEL_MAP_BINARY

    df = raw_df.dropna(subset=["payload", label_col]).copy()
    if len(df) == 0:
        return {"error": "no_rows", "per_transform": {}}

    n_samples = min(n_samples, len(df))
    rng = np.random.default_rng(random_state)
    idx = rng.choice(len(df), size=n_samples, replace=False)
    sample = df.iloc[idx].reset_index(drop=True)

    # Infer binary vs multiclass from label values
    lb = sample[label_col].astype(str).str.lower()
    y_series = lb.map(LABEL_MAP_MULTICLASS)
    mode = "multiclass"
    if y_series.isna().any():
        y_series = lb.map(LABEL_MAP_BINARY)
        mode = "binary"
    y = y_series.fillna(0).astype(int).values
    extractor = FeatureExtractor(feature_mode=feature_mode)  # type: ignore[arg-type]
    py_rng = random.Random(random_state)

    names = transform_names or list_transform_names()
    out: Dict[str, float] = {}

    for tname in names:
        xs: List[List[float]] = []
        for _, row in sample.iterrows():
            d = row.to_dict()
            d["payload"] = apply_transform(tname, str(d.get("payload", "")), py_rng)
            feat = extractor.extract_single(d)
            vec = [float(feat.get(c, 0)) for c in feature_columns]
            xs.append(vec)
        X = pd.DataFrame(xs, columns=feature_columns)
        pred = model.predict(X)
        out[tname] = float((pred == y).mean())

    return {"per_transform_accuracy": out, "label_mode": mode, "n_samples": n_samples}
