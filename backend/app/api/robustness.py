"""
WebGuard RF - Robustness Analysis API
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path
from ..core.validation import validate_data_path

router = APIRouter()


class RobustnessRequest(BaseModel):
    model_id: Optional[str] = None
    data_path: str
    test_type: Literal["zero_out", "ablation"] = "zero_out"
    top_n: int = 10


@router.post("/analyze")
def analyze_robustness(req: RobustnessRequest, user: dict = Depends(get_current_user)):
    """Run robustness analysis: zero-out sensitivity or feature ablation."""
    import sys
    import joblib
    import pandas as pd
    import numpy as np

    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from ml_pipeline.evaluation.robustness import RobustnessTester
    from ml_pipeline.feature_extraction.features import ablation_groups_for_mode

    models_dir = resolve_data_path(settings.MODELS_DIR)
    model_id = req.model_id
    if not model_id:
        joblibs = [f for f in models_dir.glob("rf_*.joblib") if "_preprocessor" not in f.name]
        if not joblibs:
            raise HTTPException(404, "No trained model found")
        model_id = sorted(joblibs, key=lambda f: f.stat().st_mtime)[-1].stem

    if "/" in model_id or "\\" in model_id or ".." in model_id:
        raise HTTPException(400, "Invalid model_id")
    model_path = models_dir / f"{model_id}.joblib"
    prep_path = models_dir / f"{model_id}_preprocessor.joblib"
    if not model_path.exists() or not prep_path.exists():
        raise HTTPException(404, f"Model {model_id} not found")

    data_path = validate_data_path(req.data_path)
    if not data_path.exists():
        raise HTTPException(404, f"Data file not found: {req.data_path}")

    model = joblib.load(model_path)
    prep_data = joblib.load(prep_path)
    feature_columns = prep_data.get("feature_columns", [])
    preprocessor = prep_data.get("preprocessor")

    if data_path.suffix == ".parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)

    if "label" not in df.columns:
        raise HTTPException(400, "Dataset must have a 'label' column")

    X = df[[c for c in feature_columns if c in df.columns]].copy().fillna(0)
    label_map = prep_data.get("label_map", {"benign": 0, "sqli": 1, "xss": 1, "csrf": 1})
    y = df["label"].map(label_map).fillna(0).astype(int).values

    tester = RobustnessTester(model, preprocessor, list(X.columns))

    if req.test_type == "zero_out":
        results = tester.zero_out_sensitivity(X, y, top_n=min(req.top_n, len(X.columns)))
        return {
            "model_id": model_id,
            "test_type": "zero_out",
            "baseline_accuracy": float((model.predict(X) == y).mean()),
            "accuracy_drops": {k: round(v, 6) for k, v in results.items()},
            "sorted_by_sensitivity": [
                {"feature": k, "accuracy_drop": round(v, 6)} for k, v in
                sorted(results.items(), key=lambda x: -x[1])
            ],
        }
    else:
        fm = prep_data.get("feature_mode", "payload_only")
        groups = ablation_groups_for_mode(fm, list(X.columns))
        if not groups:
            raise HTTPException(400, "No feature groups for this model")
        results = tester.feature_ablation(X, y, groups)
        return {
            "model_id": model_id,
            "test_type": "ablation",
            "baseline_accuracy": results.get("baseline", 0),
            "group_accuracies": {k: round(v, 6) for k, v in results.items() if k != "baseline"},
            "accuracy_drops": {
                k: round(results["baseline"] - v, 6)
                for k, v in results.items() if k != "baseline"
            },
        }
