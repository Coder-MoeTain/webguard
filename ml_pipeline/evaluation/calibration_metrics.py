"""
Multiclass calibration and confidence summaries for research reporting.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def multiclass_brier_score(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Mean squared error between one-hot labels and predicted probabilities."""
    y_true = np.asarray(y_true).astype(int)
    y_proba = np.asarray(y_proba, dtype=np.float64)
    n, k = y_proba.shape
    oh = np.zeros((n, k), dtype=np.float64)
    oh[np.arange(n), y_true] = 1.0
    return float(np.mean(np.sum((y_proba - oh) ** 2, axis=1)))


def multiclass_ece(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    n_bins: int = 15,
) -> Tuple[float, List[Dict[str, float]]]:
    """
    Expected calibration error using confidence of the predicted class vs. accuracy in each bin.
    Returns (ece, per-bin diagnostics).
    """
    y_true = np.asarray(y_true).astype(int)
    y_proba = np.asarray(y_proba, dtype=np.float64)
    pred = np.argmax(y_proba, axis=1)
    conf = y_proba.max(axis=1)
    correct = (pred == y_true).astype(np.float64)
    n = len(y_true)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    details: List[Dict[str, float]] = []
    for b in range(n_bins):
        lo, hi = bins[b], bins[b + 1]
        if b == n_bins - 1:
            mask = (conf >= lo) & (conf <= hi)
        else:
            mask = (conf >= lo) & (conf < hi)
        cnt = int(mask.sum())
        if cnt == 0:
            details.append({"bin_lo": float(lo), "bin_hi": float(hi), "n": 0, "acc": 0.0, "conf": 0.0})
            continue
        acc_bin = float(correct[mask].mean())
        conf_bin = float(conf[mask].mean())
        w = cnt / n
        ece += w * abs(acc_bin - conf_bin)
        details.append(
            {
                "bin_lo": float(lo),
                "bin_hi": float(hi),
                "n": cnt,
                "acc": acc_bin,
                "conf": conf_bin,
            }
        )
    return float(ece), details


def margin_summary(y_proba: np.ndarray) -> Dict[str, float]:
    """Top-1 vs top-2 probability gap (useful for abstention / triage studies)."""
    p = np.asarray(y_proba, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] < 2:
        return {"margin_mean": 0.0, "margin_median": 0.0, "margin_p10": 0.0, "margin_p90": 0.0}
    part = np.partition(p, -2, axis=1)
    margin = part[:, -1] - part[:, -2]
    return {
        "margin_mean": float(np.mean(margin)),
        "margin_median": float(np.median(margin)),
        "margin_p10": float(np.percentile(margin, 10)),
        "margin_p90": float(np.percentile(margin, 90)),
    }


def low_margin_rate(y_proba: np.ndarray, threshold: float = 0.2) -> float:
    """Fraction of samples with (p_max - p_second) < threshold."""
    p = np.asarray(y_proba, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] < 2:
        return 0.0
    part = np.partition(p, -2, axis=1)
    margin = part[:, -1] - part[:, -2]
    return float(np.mean(margin < threshold))
