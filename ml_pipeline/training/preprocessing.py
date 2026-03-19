"""
WebGuard RF - Data Preprocessing
Handles missing values, encoding, stratified splits.
"""

from typing import Optional, Tuple, Literal

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler


LABEL_MAP_MULTICLASS = {"benign": 0, "sqli": 1, "xss": 2, "csrf": 3}
LABEL_MAP_BINARY = {"benign": 0, "sqli": 1, "xss": 1, "csrf": 1}


class DataPreprocessor:
    """Preprocess dataset for Random Forest training."""

    def __init__(
        self,
        classification_mode: Literal["binary", "multiclass"] = "multiclass",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42,
        use_class_weight: bool = True,
    ):
        self.classification_mode = classification_mode
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_state = random_state
        self.use_class_weight = use_class_weight
        self.label_encoder_ = LabelEncoder()
        self.scaler_ = StandardScaler()
        self.feature_columns_ = None

    def _get_label_map(self):
        return LABEL_MAP_BINARY if self.classification_mode == "binary" else LABEL_MAP_MULTICLASS

    def _encode_labels(self, y: pd.Series) -> np.ndarray:
        label_map = self._get_label_map()
        return y.map(label_map).values

    # Columns to always exclude (identifiers, raw text - not usable as numeric features)
    EXCLUDE_COLUMNS = frozenset({"id", "payload", "url", "headers", "content_type", "request_method", "endpoint_type"})

    def fit_transform(self, df: pd.DataFrame, label_col: str = "label") -> Tuple[pd.DataFrame, np.ndarray]:
        """Preprocess and return X, y. Only numeric columns are used as features."""
        exclude = self.EXCLUDE_COLUMNS | {label_col}
        candidates = [c for c in df.columns if c not in exclude]

        # Keep only numeric columns (int, float, bool) - required for sklearn
        numeric_cols = []
        for c in candidates:
            dtype = df[c].dtype
            if np.issubdtype(dtype, np.number) or dtype == bool:
                numeric_cols.append(c)
            elif dtype == object:
                # Skip object columns (strings like UUID, URLs) - they cannot be used as features
                continue
            else:
                try:
                    pd.to_numeric(df[c], errors="raise")
                    numeric_cols.append(c)
                except (ValueError, TypeError):
                    pass

        self.feature_columns_ = numeric_cols
        if not self.feature_columns_:
            raise ValueError(
                "No numeric feature columns found. Use a feature-extracted dataset (with has_select, has_union, etc.) "
                "or run Feature Extraction on your raw dataset first."
            )
        X = df[self.feature_columns_].copy()
        y = df[label_col]

        X = X.fillna(0)
        X = X.replace([np.inf, -np.inf], 0)
        # Ensure all columns are numeric (convert bool to int)
        X = X.astype(np.float64)
        y_encoded = self._encode_labels(y)
        return X, y_encoded

    def split(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
    ) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
        """Stratified train/val/test split."""
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=(1 - self.train_ratio), stratify=y, random_state=self.random_state
        )
        val_ratio_adj = self.val_ratio / (self.val_ratio + self.test_ratio)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=(1 - val_ratio_adj), stratify=y_temp, random_state=self.random_state
        )
        return X_train, y_train, X_val, y_val, X_test, y_test

    def get_class_weights(self, y: np.ndarray) -> dict:
        """Compute class weights for imbalanced data."""
        from sklearn.utils.class_weight import compute_class_weight
        classes = np.unique(y)
        weights = compute_class_weight(
            "balanced", classes=classes, y=y
        )
        return dict(zip(classes, weights))
