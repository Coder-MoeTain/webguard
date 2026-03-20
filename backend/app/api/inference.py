"""
WebGuard RF - Live Inference API
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..core.config import settings
from ..core.deps import get_current_user

router = APIRouter()

# Cache loaded model
_model_cache = {}


class InferenceRequest(BaseModel):
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    query_params: Optional[str] = None
    request_method: str = "GET"
    response_status: Optional[int] = 200
    response_length: Optional[int] = 1000
    response_time: Optional[float] = 100.0
    model_id: Optional[str] = None


class InferenceResponse(BaseModel):
    prediction: str
    confidence: float
    top_features: list
    risk_explanation: str


def _build_record(req: InferenceRequest) -> dict:
    payload = req.body or req.query_params or req.url or ""
    return {
        "payload": payload,
        "request_method": req.request_method,
        "url": req.url or "https://example.com/",
        "cookies_present": bool(req.headers and "Cookie" in str(req.headers)),
        "token_present": bool(req.headers and any("csrf" in k.lower() or "token" in k.lower() for k in (req.headers or {}))),
        "referrer_present": bool(req.headers and "Referer" in str(req.headers)),
        "response_status": req.response_status or 200,
        "response_length": req.response_length or 1000,
        "response_time": req.response_time or 100.0,
        "error_flag": (req.response_status or 200) >= 400,
        "redirection_flag": req.response_status in (301, 302, 303) if req.response_status else False,
    }


@router.post("/predict", response_model=InferenceResponse)
def predict(req: InferenceRequest, user: dict = Depends(get_current_user)):
    import sys
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from ml_pipeline.feature_extraction import FeatureExtractor  # noqa: E402

    model_id = req.model_id
    models_dir = Path(settings.MODELS_DIR)
    if not model_id:
        joblibs = list(models_dir.glob("rf_*.joblib"))
        joblibs = [f for f in joblibs if "_preprocessor" not in f.name]
        if not joblibs:
            raise HTTPException(400, "No trained model found. Train a model first.")
        model_id = joblibs[-1].stem

    import joblib
    model_path = models_dir / f"{model_id}.joblib"
    prep_path = models_dir / f"{model_id}_preprocessor.joblib"
    if not model_path.exists():
        raise HTTPException(400, f"Model {model_id} not found. Train a model first.")

    if model_id not in _model_cache:
        model = joblib.load(model_path)
        # XGBoost GPU models: use CPU for inference (allows inference on CPU-only servers)
        if hasattr(model, "set_params"):
            try:
                model.set_params(device="cpu")
            except Exception:
                pass
        _model_cache[model_id] = (model, joblib.load(prep_path))

    model, prep_data = _model_cache[model_id]
    preprocessor = prep_data["preprocessor"]
    feature_columns = prep_data["feature_columns"]
    label_map_inv = {v: k for k, v in prep_data["label_map"].items()}
    if prep_data.get("classification_mode") == "binary":
        label_map_inv = {0: "benign", 1: "attack"}

    feature_mode = prep_data.get("feature_mode", "payload_only")
    ext = FeatureExtractor(feature_mode=feature_mode)
    record = _build_record(req)
    feat = ext.extract_single(record)
    import pandas as pd
    row = {k: feat.get(k, 0) for k in feature_columns}
    df = pd.DataFrame([row])
    for c in feature_columns:
        if c not in df.columns:
            df[c] = 0
    df = df[feature_columns].fillna(0)

    pred_raw = model.predict(df)
    pred = int(pred_raw[0]) if hasattr(pred_raw, "__getitem__") else int(pred_raw)
    proba = model.predict_proba(df)[0]
    conf = float(max(proba))
    pred_label = label_map_inv.get(int(pred), "unknown")

    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        imp = imp.tolist() if hasattr(imp, "tolist") else list(imp)
    elif hasattr(model, "coef_"):
        import numpy as np
        coef = np.asarray(model.coef_)
        imp = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
        imp = (imp / (imp.sum() + 1e-10)).tolist()
    else:
        imp = [1.0 / len(feature_columns)] * len(feature_columns)
    importances = dict(zip(feature_columns, imp))
    top = sorted(importances.items(), key=lambda x: -x[1])[:5]
    top_features = [{"name": k, "importance": float(v)} for k, v in top]

    risk_msg = f"Classified as {pred_label} with {conf:.1%} confidence."
    if pred_label != "benign":
        risk_msg += f" Top indicators: {', '.join(t[0] for t in top[:3])}."

    return InferenceResponse(
        prediction=pred_label,
        confidence=conf,
        top_features=top_features,
        risk_explanation=risk_msg,
    )
