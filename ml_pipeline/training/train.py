"""
WebGuard RF - Random Forest Training Engine
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Literal, Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score,
    f1_score,
)

from .preprocessing import DataPreprocessor, LABEL_MAP_MULTICLASS, LABEL_MAP_BINARY


class RandomForestTrainer:
    """Train and save Random Forest models for web attack detection."""

    def __init__(
        self,
        classification_mode: Literal["binary", "multiclass"] = "multiclass",
        feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"] = "payload_only",
        n_estimators: int = 200,
        max_depth: Optional[int] = 30,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: str = "sqrt",
        bootstrap: bool = True,
        random_state: int = 42,
        n_jobs: int = -1,
        class_weight: Optional[str] = "balanced",
        hyperparameter_tuning: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ):
        self.classification_mode = classification_mode
        self._feature_mode = feature_mode
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.class_weight = class_weight
        self.hyperparameter_tuning = hyperparameter_tuning
        self.progress_callback = progress_callback

        self.model_ = None
        self.preprocessor_ = None
        self.feature_columns_ = None
        self.label_map_ = LABEL_MAP_BINARY if classification_mode == "binary" else LABEL_MAP_MULTICLASS
        if classification_mode == "binary":
            self.inverse_label_map_ = {0: "benign", 1: "attack"}
        else:
            self.inverse_label_map_ = {v: k for k, v in LABEL_MAP_MULTICLASS.items()}

    def _log(self, msg: str, percent: int = 0, details: Optional[Dict[str, Any]] = None):
        if self.progress_callback:
            data = {"phase": msg, "progress": percent}
            if details:
                data.update(details)
            self.progress_callback(data)

    def train(
        self,
        data_path: str,
        output_dir: str = "models",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, Any]:
        """Train model and return metrics."""
        self._log("Loading data...", 5, {"step": "load", "detail": "Reading dataset"})
        if data_path.endswith(".parquet"):
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        total_samples = len(df)

        self._log("Preprocessing...", 10, {"step": "preprocess", "samples_loaded": total_samples})
        preprocessor = DataPreprocessor(
            classification_mode=self.classification_mode,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            random_state=self.random_state,
        )
        X, y = preprocessor.fit_transform(df)
        X_train, y_train, X_val, y_val, X_test, y_test = preprocessor.split(X, y)

        self.preprocessor_ = preprocessor
        self.feature_columns_ = preprocessor.feature_columns_
        train_size, val_size, test_size = len(X_train), len(X_val), len(X_test)

        class_weight = preprocessor.get_class_weights(y_train) if self.class_weight == "balanced" else None

        self._log("Training Random Forest...", 25, {
            "step": "training",
            "samples_loaded": total_samples,
            "train_size": train_size,
            "val_size": val_size,
            "test_size": test_size,
            "feature_count": len(self.feature_columns_),
            "n_estimators": self.n_estimators,
        })
        start = time.time()
        params = {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "min_samples_leaf": self.min_samples_leaf,
            "max_features": self.max_features,
            "bootstrap": self.bootstrap,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
        }
        if class_weight:
            params["class_weight"] = class_weight

        if self.hyperparameter_tuning:
            self._log("Hyperparameter tuning...", 30)
            param_grid = {
                "n_estimators": [100, 200, 300],
                "max_depth": [20, 30, 40, None],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 2],
            }
            search = RandomizedSearchCV(
                RandomForestClassifier(random_state=self.random_state),
                param_grid,
                n_iter=10,
                cv=3,
                n_jobs=self.n_jobs,
                random_state=self.random_state,
            )
            search.fit(X_train, y_train)
            self.model_ = search.best_estimator_
        else:
            self.model_ = RandomForestClassifier(**params)
            self.model_.fit(X_train, y_train)

        train_time = time.time() - start
        self._log("Evaluating...", 80, {"step": "evaluate", "train_time_seconds": round(train_time, 2)})

        metrics = {}
        for split_name, X_s, y_s in [
            ("train", X_train, y_train),
            ("validation", X_val, y_val),
            ("test", X_test, y_test),
        ]:
            pred = self.model_.predict(X_s)
            metrics[split_name] = self._compute_metrics(y_s, pred, X_s)

        metrics["train_time_seconds"] = train_time
        metrics["feature_importance"] = dict(
            zip(self.feature_columns_, self.model_.feature_importances_.tolist())
        )

        self._log("Saving model...", 95)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        model_id = f"rf_{int(time.time())}"
        model_path = Path(output_dir) / f"{model_id}.joblib"
        prep_path = Path(output_dir) / f"{model_id}_preprocessor.joblib"
        joblib.dump(self.model_, model_path)
        joblib.dump(
            {
                "preprocessor": self.preprocessor_,
                "feature_columns": self.feature_columns_,
                "label_map": self.label_map_,
                "classification_mode": self.classification_mode,
                "feature_mode": self._feature_mode,
            },
            prep_path,
        )
        metrics["model_path"] = str(model_path)
        metrics["preprocessor_path"] = str(prep_path)
        metrics["model_id"] = model_id
        metrics["config"] = {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "feature_count": len(self.feature_columns_),
            "feature_mode": self._feature_mode,
            "classification_mode": self.classification_mode,
        }

        self._log("Done", 100, {"step": "complete", "model_id": model_id})
        return metrics

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, X: Optional[pd.DataFrame] = None) -> dict:
        acc = accuracy_score(y_true, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=None)
        prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average="macro", zero_division=0
        )
        f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        cm = confusion_matrix(y_true, y_pred)

        tn, fp, fn, tp = 0, 0, 0, 0
        if cm.size == 4:
            tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

        roc_auc = 0.0
        if self.classification_mode == "binary" and len(np.unique(y_true)) > 1:
            try:
                proba = self.model_.predict_proba(X)[:, 1]
                roc_auc = roc_auc_score(y_true, proba)
            except Exception:
                pass
        elif self.classification_mode == "multiclass" and X is not None:
            try:
                proba = self.model_.predict_proba(X)
                roc_auc = roc_auc_score(y_true, proba, multi_class="ovr", average="macro")
            except Exception:
                pass

        labels = list(self.inverse_label_map_.values())
        per_class = {}
        for i, label in enumerate(labels):
            if i < len(prec):
                per_class[label] = {"precision": float(prec[i]), "recall": float(rec[i]), "f1": float(f1[i])}

        return {
            "accuracy": float(acc),
            "precision_macro": float(prec_macro),
            "recall_macro": float(rec_macro),
            "f1_macro": float(f1_macro),
            "f1_weighted": float(f1_weighted),
            "roc_auc": float(roc_auc),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr),
            "confusion_matrix": cm.tolist(),
            "per_class_metrics": per_class,
        }
