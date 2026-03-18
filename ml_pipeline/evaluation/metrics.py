"""
WebGuard RF - Evaluation Metrics
"""

from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score,
    f1_score,
)


class EvaluationMetrics:
    """Compute and format evaluation metrics."""

    @staticmethod
    def compute(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray = None,
        labels: list = None,
    ) -> Dict[str, Any]:
        labels = labels or ["benign", "sqli", "xss", "csrf"]
        acc = accuracy_score(y_true, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=None, labels=range(len(labels)), zero_division=0)
        prec_macro = np.mean(prec) if len(prec) else 0
        rec_macro = np.mean(rec) if len(rec) else 0
        f1_macro = np.mean(f1) if len(f1) else 0
        f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        roc_auc = 0.0
        if y_proba is not None and len(np.unique(y_true)) > 1:
            try:
                roc_auc = roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro")
            except Exception:
                pass
        return {
            "accuracy": float(acc),
            "precision_macro": float(prec_macro),
            "recall_macro": float(rec_macro),
            "f1_macro": float(f1_macro),
            "f1_weighted": float(f1_weighted),
            "roc_auc": float(roc_auc),
            "confusion_matrix": cm.tolist(),
        }
