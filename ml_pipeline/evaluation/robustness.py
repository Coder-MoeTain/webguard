"""
WebGuard RF - Robustness Testing
Feature ablation, zero-out sensitivity, attack/benign suite testing.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


class RobustnessTester:
    """Test model robustness via feature ablation and test suites."""

    def __init__(self, model, preprocessor, feature_columns: List[str]):
        self.model = model
        self.preprocessor = preprocessor
        self.feature_columns = feature_columns

    def zero_out_sensitivity(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        top_n: int = 10,
    ) -> Dict[str, float]:
        """Zero out each of top-N important features and measure accuracy drop."""
        base_acc = (self.model.predict(X) == y).mean()
        importances = dict(zip(self.feature_columns, self.model.feature_importances_))
        sorted_features = sorted(importances.keys(), key=lambda f: importances[f], reverse=True)[:top_n]
        results = {}
        for feat in sorted_features:
            X_zeroed = X.copy()
            X_zeroed[feat] = 0
            acc = (self.model.predict(X_zeroed) == y).mean()
            results[feat] = float(base_acc - acc)
        return results

    def feature_ablation(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        feature_groups: Dict[str, List[str]],
    ) -> Dict[str, float]:
        """Remove entire feature groups (zero them out) and measure accuracy."""
        base_acc = (self.model.predict(X) == y).mean()
        results = {"baseline": float(base_acc)}
        for group_name, feats in feature_groups.items():
            zero_feats = [f for f in feats if f in X.columns]
            if not zero_feats:
                continue
            X_ablated = X.copy()
            X_ablated[zero_feats] = 0
            acc = (self.model.predict(X_ablated) == y).mean()
            results[group_name] = float(acc)
        return results
