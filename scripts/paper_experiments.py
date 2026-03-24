#!/usr/bin/env python3
"""
Generate synthetic + curated corpora, extract features, train multiple algorithms,
and write JSON results + figures for docs/International_Research_Paper.md.

Run from repo root: python scripts/paper_experiments.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _align_X(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in columns:
        if c in df.columns:
            out[c] = df[c]
        else:
            out[c] = 0.0
    return out.astype(np.float64).fillna(0)


def _metrics_block(
    model: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    class_names: List[str],
) -> Dict[str, Any]:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
        roc_auc_score,
    )

    pred = model.predict(X)
    proba = None
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)
        except Exception:
            proba = None
    prec_mac, rec_mac, f1_mac, _ = precision_recall_fscore_support(
        y, pred, average="macro", zero_division=0
    )
    f1_w = f1_score(y, pred, average="weighted", zero_division=0)
    per_class: Dict[str, Dict[str, float]] = {}
    prec, rec, f1, _ = precision_recall_fscore_support(
        y, pred, average=None, labels=range(len(class_names)), zero_division=0
    )
    for i, name in enumerate(class_names):
        per_class[name] = {
            "precision": float(prec[i]) if i < len(prec) else 0.0,
            "recall": float(rec[i]) if i < len(rec) else 0.0,
            "f1": float(f1[i]) if i < len(f1) else 0.0,
        }
    roc = 0.0
    if proba is not None and len(np.unique(y)) > 1:
        try:
            roc = float(roc_auc_score(y, proba, multi_class="ovr", average="macro"))
        except Exception:
            roc = 0.0
    ece = brier = None
    if proba is not None:
        from ml_pipeline.evaluation.calibration_metrics import multiclass_brier_score, multiclass_ece

        ece = float(multiclass_ece(y, proba)[0])
        brier = float(multiclass_brier_score(y, proba))
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "f1_macro": float(f1_mac),
        "f1_weighted": float(f1_w),
        "precision_macro": float(prec_mac),
        "recall_macro": float(rec_mac),
        "roc_auc_macro_ovr": roc,
        "ece": ece,
        "brier": brier,
        "confusion_matrix": confusion_matrix(y, pred, labels=range(len(class_names))).tolist(),
        "per_class": per_class,
        "y_pred": pred.tolist(),
        "y_true": y.tolist(),
    }


def _plot_confusion(
    cm: List[List[int]],
    class_names: List[str],
    title: str,
    path: Path,
    normalize: bool = True,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm_arr = np.asarray(cm, dtype=float)
    if normalize:
        row_sums = cm_arr.sum(axis=1, keepdims=True) + 1e-10
        cm_arr = cm_arr / row_sums
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_arr, cmap="Blues", vmin=0, vmax=1 if normalize else None)
    ax.set_title(title)
    tick = np.arange(len(class_names))
    ax.set_xticks(tick)
    ax.set_yticks(tick)
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_ylabel("True")
    ax.set_xlabel("Predicted")
    for i in range(cm_arr.shape[0]):
        for j in range(cm_arr.shape[1]):
            val = cm_arr[i, j]
            ax.text(j, i, f"{val:.2f}" if normalize else f"{int(cm[i][j])}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_bar_comparison(rows: List[Dict[str, Any]], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    algos = [r["algorithm"] for r in rows]
    x = np.arange(len(algos))
    w = 0.35
    syn = [r["synthetic_test"]["f1_macro"] for r in rows]
    cur = [r["curated_test"]["f1_macro"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, syn, w, label="Synthetic held-out test")
    ax.bar(x + w / 2, cur, w, label="Curated pattern corpus (external-style)")
    ax.set_ylabel("Macro-F1")
    ax.set_xticks(x)
    ax.set_xticklabels(algos, rotation=15, ha="right")
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.set_title("Model comparison: same features, two evaluation corpora")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    from ml_pipeline.dataset_generator import DatasetGenerator
    from ml_pipeline.datasets.curated_corpus import CURATED_CORPUS_DESCRIPTION, build_curated_labeled_dataframe
    from ml_pipeline.feature_extraction import FeatureExtractor
    from ml_pipeline.training.preprocessing import LABEL_MAP_MULTICLASS, DataPreprocessor
    from ml_pipeline.training.train import _get_model

    data_dir = ROOT / "data"
    img_dir = ROOT / "docs" / "images" / "paper"
    data_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    syn_raw = data_dir / "paper_synthetic_raw.parquet"
    cur_raw = data_dir / "paper_curated_raw.parquet"
    syn_feat = data_dir / "paper_synthetic_features.parquet"
    cur_feat = data_dir / "paper_curated_features.parquet"
    out_json = data_dir / "paper_experiment_results.json"

    class_names = ["benign", "sqli", "xss", "csrf"]

    print("Generating synthetic corpus (20k rows)...")
    gen = DatasetGenerator(
        total_samples=20_000,
        attack_ratio=0.8,
        benign_ratio=0.2,
        random_seed=42,
        label_noise_ratio=0.02,
    )
    gen.generate(str(syn_raw), format="parquet", chunk_size=10_000)

    print("Building curated pattern corpus...")
    build_curated_labeled_dataframe(n_per_class=400, random_state=7).to_parquet(cur_raw, index=False)

    print("Feature extraction (payload_only)...")
    ext = FeatureExtractor(feature_mode="payload_only")
    ext.extract_file(str(syn_raw), str(syn_feat), format="parquet")
    ext.extract_file(str(cur_raw), str(cur_feat), format="parquet")

    df_syn = pd.read_parquet(syn_feat)
    prep = DataPreprocessor(
        classification_mode="multiclass",
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42,
    )
    X, y = prep.fit_transform(df_syn)
    X_train, y_train, X_val, y_val, X_test, y_test = prep.split(X, y)
    feature_columns = prep.feature_columns_
    n_features = len(feature_columns)

    df_cur = pd.read_parquet(cur_feat)
    y_cur = df_cur["label"].astype(str).str.lower().map(LABEL_MAP_MULTICLASS).fillna(0).astype(int).values
    X_cur = _align_X(df_cur, feature_columns)

    algorithms: List[str] = ["random_forest", "logistic_regression", "catboost"]
    colsample = 1.0 / (n_features ** 0.5) if n_features > 1 else 1.0
    min_child = 1
    n_estimators = 200
    max_depth = 24

    run_rows: List[Dict[str, Any]] = []
    trained_models: Dict[str, Any] = {}

    for algo in algorithms:
        print(f"Training: {algo}")
        model = _get_model(
            algo,
            "multiclass",
            n_estimators,
            max_depth,
            min_child,
            colsample,
            42,
            None,
            n_features,
        )
        model.fit(X_train, y_train)
        trained_models[algo] = model
        syn_block = _metrics_block(model, X_test, y_test, class_names)
        cur_block = _metrics_block(model, X_cur, y_cur, class_names)
        # drop huge arrays from stored json
        syn_store = {k: v for k, v in syn_block.items() if k not in ("y_pred", "y_true")}
        cur_store = {k: v for k, v in cur_block.items() if k not in ("y_pred", "y_true")}
        run_rows.append(
            {
                "algorithm": algo,
                "synthetic_test": syn_store,
                "curated_test": cur_store,
            }
        )

    best = max(run_rows, key=lambda r: r["synthetic_test"]["f1_macro"])
    best_algo = best["algorithm"]
    best_model = trained_models[best_algo]
    best_syn = _metrics_block(best_model, X_test, y_test, class_names)
    best_cur = _metrics_block(best_model, X_cur, y_cur, class_names)

    _plot_confusion(
        best_syn["confusion_matrix"],
        class_names,
        f"Confusion (normalized rows) — {best_algo} — synthetic test",
        img_dir / "fig_cm_synthetic_test.png",
        normalize=True,
    )
    _plot_confusion(
        best_cur["confusion_matrix"],
        class_names,
        f"Confusion (normalized rows) — {best_algo} — curated corpus",
        img_dir / "fig_cm_curated_corpus.png",
        normalize=True,
    )
    _plot_bar_comparison(run_rows, img_dir / "fig_macro_f1_comparison.png")

    payload: Dict[str, Any] = {
        "description": {
            "synthetic": "Procedural generator (20k rows, 80% attack / 20% benign, 2% label noise, seed=42).",
            "curated": CURATED_CORPUS_DESCRIPTION + " 400 samples per class (1,600 rows), shuffled, seed=7.",
            "split": "Stratified 70/15/15 on synthetic features only; curated set is never used for training.",
            "features": "payload_only mode; same column order for both corpora.",
        },
        "class_names": class_names,
        "best_algorithm_by_synthetic_macro_f1": best_algo,
        "comparison": run_rows,
        "train_size": int(len(X_train)),
        "synthetic_test_size": int(len(X_test)),
        "curated_test_size": int(len(X_cur)),
        "feature_dimension": n_features,
        "figures": {
            "comparison_bars": "docs/images/paper/fig_macro_f1_comparison.png",
            "confusion_synthetic": "docs/images/paper/fig_cm_synthetic_test.png",
            "confusion_curated": "docs/images/paper/fig_cm_curated_corpus.png",
        },
    }

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote figures under {img_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
