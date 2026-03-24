"""
Save F1 score and confusion matrix figures for model evaluation (PNG).
"""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


def _labels_from_per_class(per_class: Optional[Dict[str, Any]], classification_mode: str) -> List[str]:
    if per_class:
        return list(per_class.keys())
    return ["benign", "attack"] if classification_mode == "binary" else ["benign", "sqli", "xss", "csrf"]


def render_f1_score_chart_png(
    split_metrics: Dict[str, Any],
    title: str,
    classification_mode: str = "multiclass",
) -> bytes:
    """
    Bar chart: per-class F1 (when available) and horizontal line for macro-F1.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    per_class = split_metrics.get("per_class_metrics") or {}
    macro_f1 = float(split_metrics.get("f1_macro") or 0.0)

    fig, ax = plt.subplots(figsize=(max(5.0, len(per_class) * 1.2 if per_class else 4), 4.2))

    if per_class and isinstance(per_class, dict):
        names = list(per_class.keys())
        scores = []
        for k in names:
            v = per_class[k]
            if isinstance(v, dict) and "f1" in v:
                scores.append(float(v["f1"]))
            else:
                scores.append(0.0)
        colors = plt.cm.Blues(np.linspace(0.45, 0.85, len(names)))
        ax.bar(names, scores, color=colors, edgecolor="navy", linewidth=0.5)
        ax.axhline(macro_f1, color="crimson", linestyle="--", linewidth=2, label=f"Macro-F1 = {macro_f1:.4f}")
        ax.set_ylabel("F1 score")
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=25, ha="right")

    else:
        ax.bar(["macro-F1"], [macro_f1], color="steelblue", width=0.5)
        ax.set_ylabel("F1 score")

    ax.set_ylim(0, 1.08)
    ax.set_title(title)
    if per_class and isinstance(per_class, dict):
        ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render_confusion_matrix_png(
    confusion_matrix: List[List[Union[int, float]]],
    class_labels: List[str],
    title: str,
    normalize_rows: bool = True,
) -> bytes:
    """Heatmap of confusion matrix (optionally row-normalized for rates)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = np.asarray(confusion_matrix, dtype=float)
    if cm.size == 0:
        raise ValueError("Empty confusion matrix")

    display = cm.copy()
    if normalize_rows:
        row_sums = cm.sum(axis=1, keepdims=True) + 1e-10
        display = cm / row_sums

    n = display.shape[0]
    labels = class_labels[:n] if len(class_labels) >= n else class_labels + [f"c{i}" for i in range(len(class_labels), n)]

    fig, ax = plt.subplots(figsize=(max(4.5, n * 1.1), max(4, n * 0.95)))
    im = ax.imshow(display, cmap="Blues", vmin=0, vmax=1.0 if normalize_rows else None)
    ax.set_title(title)
    tick = np.arange(n)
    ax.set_xticks(tick)
    ax.set_yticks(tick)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticklabels(labels)
    ax.set_ylabel("True label")
    ax.set_xlabel("Predicted label")

    fmt = ".2f" if normalize_rows else "d"
    for i in range(n):
        for j in range(n):
            val = display[i, j]
            txt = f"{val:{fmt}}" if normalize_rows else f"{int(cm[i, j])}"
            ax.text(
                j,
                i,
                txt,
                ha="center",
                va="center",
                color="white" if display[i, j] > 0.5 else "black",
                fontsize=10,
            )

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def save_evaluation_plots_for_metrics(
    metrics: Dict[str, Any],
    output_dir: Union[str, Path],
    model_id: str,
) -> Dict[str, Dict[str, str]]:
    """
    Write PNG files for train/validation/test splits that contain confusion_matrix.
    Returns mapping split -> paths plus base64 for API responses.
    """
    output_dir = Path(output_dir)
    out_root = output_dir / model_id
    out_root.mkdir(parents=True, exist_ok=True)

    config = metrics.get("config") or {}
    classification_mode = config.get("classification_mode", "multiclass")

    saved: Dict[str, Dict[str, str]] = {}
    for split in ("train", "validation", "test"):
        block = metrics.get(split)
        if not isinstance(block, dict):
            continue
        cm = block.get("confusion_matrix")
        if cm is None:
            continue

        per_class = block.get("per_class_metrics")
        labels = _labels_from_per_class(per_class if isinstance(per_class, dict) else None, classification_mode)

        f1_bytes = render_f1_score_chart_png(
            block,
            title=f"{split.capitalize()} — F1 scores ({model_id})",
            classification_mode=classification_mode,
        )
        cm_bytes = render_confusion_matrix_png(
            cm,
            labels,
            title=f"{split.capitalize()} — Confusion matrix ({model_id})",
            normalize_rows=True,
        )

        f1_path = out_root / f"{split}_f1_scores.png"
        cm_path = out_root / f"{split}_confusion_matrix.png"
        f1_path.write_bytes(f1_bytes)
        cm_path.write_bytes(cm_bytes)

        saved[split] = {
            "f1_png": str(f1_path.resolve()),
            "confusion_png": str(cm_path.resolve()),
            "f1_b64": base64.b64encode(f1_bytes).decode("ascii"),
            "confusion_b64": base64.b64encode(cm_bytes).decode("ascii"),
        }

    return saved
