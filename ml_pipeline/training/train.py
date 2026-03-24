"""
WebGuard RF - Multi-Algorithm Training Engine
Supports: XGBoost (GPU), Random Forest, Logistic Regression, SVM, LightGBM, CatBoost.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, Literal, Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score,
    f1_score,
)

from .preprocessing import DataPreprocessor, LABEL_MAP_MULTICLASS, LABEL_MAP_BINARY

ALGORITHMS = ["xgboost", "random_forest", "logistic_regression", "svm", "lightgbm", "catboost"]
ALGORITHM_LABELS = {
    "xgboost": "XGBoost",
    "random_forest": "Random Forest (sklearn)",
    "logistic_regression": "Logistic Regression",
    "svm": "SVM",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
}


def _get_feature_importances(model, feature_columns: list) -> Dict[str, float]:
    """Get feature importances for any model type."""
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        if hasattr(imp, "tolist"):
            imp = imp.tolist()
        else:
            imp = list(imp)
        return dict(zip(feature_columns, imp))
    if hasattr(model, "coef_"):
        coef = np.asarray(model.coef_)
        if coef.ndim == 1:
            imp = np.abs(coef)
        else:
            imp = np.abs(coef).mean(axis=0)
        imp = imp / (imp.sum() + 1e-10)
        return dict(zip(feature_columns, imp.tolist()))
    # Fallback: uniform
    n = len(feature_columns)
    return {f: 1.0 / n for f in feature_columns}


def _is_lightgbm_cuda_build_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "cuda tree learner was not enabled" in msg
        or "recompile with cmake option -duse_cuda=1" in msg
        or "gpu tree learner was not enabled" in msg
    )


def _is_catboost_cuda_error(exc: Exception) -> bool:
    """Best-effort detection of CatBoost GPU/CUDA failures."""
    msg = str(exc).lower()
    return (
        "cuda" in msg
        or "tCUDAException" in msg
        or "invalid configuration argument" in msg
        or "task_type" in msg and "gpu" in msg
    )


def _get_model(
    algorithm: str,
    classification_mode: str,
    n_estimators: int,
    max_depth: Optional[int],
    min_child_weight: int,
    colsample_bytree: float,
    random_state: int,
    scale_pos_weight: Optional[float],
    n_features: int,
) -> Any:
    """Create model for given algorithm."""
    if algorithm == "xgboost":
        import xgboost as xgb
        objective = "binary:logistic" if classification_mode == "binary" else "multi:softprob"
        num_class = None if classification_mode == "binary" else 4
        params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth or 6,
            "min_child_weight": min_child_weight,
            "colsample_bytree": colsample_bytree,
            "random_state": random_state,
            "tree_method": "hist",
            "device": "cuda",
            "objective": objective,
            "eval_metric": "mlogloss" if classification_mode == "multiclass" else "logloss",
        }
        if num_class:
            params["num_class"] = num_class
        if scale_pos_weight is not None:
            params["scale_pos_weight"] = scale_pos_weight
        return xgb.XGBClassifier(**params)

    if algorithm == "random_forest":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_child_weight,
            max_features="sqrt" if n_features > 1 else "auto",
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced" if scale_pos_weight else None,
        )

    if algorithm == "logistic_regression":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(
            max_iter=5000,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        )

    if algorithm == "svm":
        from sklearn.svm import SVC
        return SVC(
            kernel="rbf",
            C=1.0,
            gamma="scale",
            probability=True,
            random_state=random_state,
            class_weight="balanced",
        )

    if algorithm == "lightgbm":
        import lightgbm as lgb
        objective = "binary" if classification_mode == "binary" else "multiclass"
        num_class = None if classification_mode == "binary" else 4
        params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth or 6,
            "min_child_samples": min_child_weight,
            "feature_fraction": colsample_bytree,
            "random_state": random_state,
            "device": "cuda",
            "objective": objective,
            "verbose": -1,
        }
        if num_class:
            params["num_class"] = num_class
        if scale_pos_weight is not None:
            params["scale_pos_weight"] = scale_pos_weight
        return lgb.LGBMClassifier(**params)

    if algorithm == "catboost":
        import catboost as cb
        # CatBoost hard limit: depth <= 16.
        cat_depth = max_depth or 6
        cat_depth = max(1, min(int(cat_depth), 16))
        # Use CPU by default for stability across Windows/CUDA driver combinations.
        # Native CatBoost CUDA errors can terminate the process before Python catches them.
        return cb.CatBoostClassifier(
            iterations=n_estimators,
            depth=cat_depth,
            random_state=random_state,
            verbose=0,
            task_type="CPU",
        )

    raise ValueError(f"Unknown algorithm: {algorithm}")


class RandomForestTrainer:
    """Train classification models for web attack detection. Supports multiple algorithms."""

    def __init__(
        self,
        algorithm: Literal["xgboost", "random_forest", "logistic_regression", "svm", "lightgbm", "catboost"] = "xgboost",
        classification_mode: Literal["binary", "multiclass"] = "multiclass",
        feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"] = "payload_only",
        n_estimators: int = 200,
        max_depth: Optional[int] = 30,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: str = "sqrt",
        bootstrap: bool = True,
        random_state: int = 42,
        n_jobs: int = 1,
        class_weight: Optional[str] = "balanced",
        hyperparameter_tuning: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ):
        self.algorithm = algorithm
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

    def _check_gpu_if_needed(self):
        """Verify GPU for algorithms that require it."""
        gpu_algorithms = ["xgboost", "lightgbm"]
        if self.algorithm not in gpu_algorithms:
            return
        try:
            import subprocess
            r = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
            if r.returncode != 0:
                raise RuntimeError("NVIDIA GPU not detected. XGBoost/LightGBM/CatBoost use GPU.")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"NVIDIA GPU not detected. {ALGORITHM_LABELS.get(self.algorithm, self.algorithm)} uses GPU. "
                f"Install CUDA and ensure nvidia-smi works. Error: {e}"
            ) from e

    def train(
        self,
        data_path: str,
        output_dir: str = "models",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        extended_research_metrics: bool = False,
        bootstrap_resamples: int = 500,
    ) -> Dict[str, Any]:
        """Train model and return metrics."""
        # CatBoost runs on CPU in this project; only tree libs using CUDA need a GPU check.
        if self.algorithm in ("xgboost", "lightgbm"):
            self._check_gpu_if_needed()

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

        n_features = len(self.feature_columns_)
        colsample = 1.0 / (n_features ** 0.5) if self.max_features == "sqrt" and n_features > 1 else 1.0
        min_child = max(1, self.min_samples_leaf)
        scale_pos_weight = None
        if self.class_weight == "balanced" and self.classification_mode == "binary":
            n_pos = (y_train == 1).sum()
            n_neg = (y_train == 0).sum()
            if n_pos > 0:
                scale_pos_weight = float(n_neg / n_pos)

        algo_label = ALGORITHM_LABELS.get(self.algorithm, self.algorithm)
        self._log(f"Training ({algo_label})...", 25, {
            "step": "training",
            "samples_loaded": total_samples,
            "train_size": train_size,
            "val_size": val_size,
            "test_size": test_size,
            "feature_count": n_features,
            "n_estimators": self.n_estimators,
        })
        start = time.time()

        if self.hyperparameter_tuning and self.algorithm in ("xgboost", "random_forest"):
            self._log("Hyperparameter tuning...", 30)
            from sklearn.model_selection import RandomizedSearchCV
            base = _get_model(
                self.algorithm, self.classification_mode, 100, 20,
                min_child, colsample, self.random_state, scale_pos_weight, n_features,
            )
            if self.algorithm == "random_forest":
                param_grid = {"n_estimators": [100, 200, 300], "max_depth": [20, 30, 40], "min_samples_leaf": [1, 2, 5], "max_features": ["sqrt", "log2"]}
            else:
                param_grid = {"n_estimators": [100, 200, 300], "max_depth": [20, 30, 40], "min_child_weight": [1, 2, 5], "colsample_bytree": [0.6, 0.8, 1.0]}
            search = RandomizedSearchCV(base, param_grid, n_iter=10, cv=3, random_state=self.random_state)
            search.fit(X_train, y_train)
            self.model_ = search.best_estimator_
        else:
            self.model_ = _get_model(
                self.algorithm, self.classification_mode, self.n_estimators, self.max_depth,
                min_child, colsample, self.random_state, scale_pos_weight, n_features,
            )
            try:
                self.model_.fit(X_train, y_train)
            except Exception as e:
                # Some LightGBM wheels include package support but are built without CUDA.
                # Fall back to CPU automatically so training can still proceed.
                if self.algorithm == "lightgbm" and _is_lightgbm_cuda_build_error(e):
                    self._log("LightGBM CUDA not enabled in this build; falling back to CPU...", 28)
                    import lightgbm as lgb

                    cpu_params = dict(self.model_.get_params())
                    cpu_params["device"] = "cpu"
                    self.model_ = lgb.LGBMClassifier(**cpu_params)
                    self.model_.fit(X_train, y_train)
                elif self.algorithm == "catboost" and _is_catboost_cuda_error(e):
                    self._log("CatBoost CUDA failed; falling back to CPU...", 28)
                    import catboost as cb

                    cat_depth = self.max_depth or 6
                    cat_depth = max(1, min(int(cat_depth), 16))
                    self.model_ = cb.CatBoostClassifier(
                        iterations=self.n_estimators,
                        depth=cat_depth,
                        random_state=self.random_state,
                        verbose=0,
                        task_type="CPU",
                    )
                    self.model_.fit(X_train, y_train)
                else:
                    raise

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

        if extended_research_metrics:
            from ml_pipeline.evaluation.calibration_metrics import (
                low_margin_rate,
                margin_summary,
                multiclass_brier_score,
                multiclass_ece,
            )
            from ml_pipeline.evaluation.bootstrap import bootstrap_statistic
            from ml_pipeline.evaluation.robustness import RobustnessTester
            from ml_pipeline.feature_extraction.features import ablation_groups_for_mode

            proba_te = self.model_.predict_proba(X_test)
            pred_te = self.model_.predict(X_test)
            ece_val, _ece_bins = multiclass_ece(y_test, proba_te)
            boot = bootstrap_statistic(
                y_test,
                pred_te,
                lambda yt, yp: float(f1_score(yt, yp, average="macro", zero_division=0)),
                n_resamples=bootstrap_resamples,
                random_state=self.random_state,
            )
            groups = ablation_groups_for_mode(self._feature_mode, self.feature_columns_)
            abla: Dict[str, Any] = {}
            if groups:
                tester = RobustnessTester(self.model_, self.preprocessor_, self.feature_columns_)
                abla = tester.feature_ablation(X_test, y_test, groups)
            metrics["research"] = {
                "test_ece": ece_val,
                "test_brier": float(multiclass_brier_score(y_test, proba_te)),
                "margin": margin_summary(proba_te),
                "low_margin_rate_lt_0.2": float(low_margin_rate(proba_te, 0.2)),
                "bootstrap_f1_macro": boot,
                "feature_ablation_accuracy": abla,
            }

        metrics["train_time_seconds"] = train_time
        metrics["feature_importance"] = _get_feature_importances(self.model_, self.feature_columns_)

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
                "algorithm": self.algorithm,
                "algorithm_label": ALGORITHM_LABELS.get(self.algorithm, self.algorithm),
            },
            prep_path,
        )
        metrics["model_path"] = str(model_path)
        metrics["preprocessor_path"] = str(prep_path)
        metrics["model_id"] = model_id
        metrics["algorithm"] = self.algorithm
        metrics["algorithm_label"] = ALGORITHM_LABELS.get(self.algorithm, self.algorithm)
        metrics["config"] = {
            "algorithm": self.algorithm,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "feature_count": len(self.feature_columns_),
            "feature_mode": self._feature_mode,
            "classification_mode": self.classification_mode,
        }

        self._log("Done", 100, {"step": "complete", "model_id": model_id})
        return metrics

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, X: Optional[pd.DataFrame] = None) -> dict:
        y_pred = np.asarray(y_pred).astype(int)
        acc = accuracy_score(y_true, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
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
        if self.classification_mode == "binary" and len(np.unique(y_true)) > 1 and X is not None:
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
