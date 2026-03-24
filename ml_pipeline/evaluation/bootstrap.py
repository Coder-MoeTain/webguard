"""
Bootstrap confidence intervals for scalar metrics (research reporting).
"""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np


def bootstrap_statistic(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    statistic_fn: Callable[[np.ndarray, np.ndarray], float],
    n_resamples: int = 1000,
    random_state: Optional[int] = None,
    confidence: Tuple[float, float] = (2.5, 97.5),
) -> Dict[str, float]:
    """
    Nonparametric bootstrap over samples (stratify not preserved — use for large n).

    Returns keys: point, ci_low, ci_high, mean_boot, std_boot
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    if n == 0:
        return {"point": 0.0, "ci_low": 0.0, "ci_high": 0.0, "mean_boot": 0.0, "std_boot": 0.0}

    rng = np.random.default_rng(random_state)
    point = float(statistic_fn(y_true, y_pred))
    stats: List[float] = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        stats.append(float(statistic_fn(y_true[idx], y_pred[idx])))

    arr = np.asarray(stats, dtype=np.float64)
    lo, hi = confidence
    return {
        "point": point,
        "ci_low": float(np.percentile(arr, lo)),
        "ci_high": float(np.percentile(arr, hi)),
        "mean_boot": float(arr.mean()),
        "std_boot": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
    }
