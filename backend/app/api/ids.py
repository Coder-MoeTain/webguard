"""
WebGuard RF - Real-time IDS API
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, Literal

import joblib
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import time

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.http_context import resolve_request_context
from ..services.ids_engine import add_alert, get_alerts, get_stats, clear_alerts

router = APIRouter()
_model_cache = {}


def _load_model(model_id: Optional[str] = None):
    """Load or get cached model. model_id=None uses latest."""
    global _model_cache
    models_dir = Path(settings.MODELS_DIR)
    if model_id:
        cache_key = model_id
    else:
        joblibs = list(models_dir.glob("rf_*.joblib"))
        joblibs = [f for f in joblibs if "_preprocessor" not in f.name]
        if not joblibs:
            return None
        model_id = joblibs[-1].stem
        cache_key = model_id

    if cache_key in _model_cache:
        return _model_cache[cache_key]

    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from ml_pipeline.feature_extraction import FeatureExtractor

    model_path = models_dir / f"{model_id}.joblib"
    prep_path = models_dir / f"{model_id}_preprocessor.joblib"
    if not model_path.exists() or not prep_path.exists():
        return None

    model = joblib.load(model_path)
    prep_data = joblib.load(prep_path)
    ext = FeatureExtractor(feature_mode=prep_data.get("feature_mode", "payload_only"))

    _model_cache[cache_key] = (model, prep_data, ext)
    return _model_cache[cache_key]


class AnalyzeRequest(BaseModel):
    method: str = "GET"
    url: str = "/"
    body: Optional[str] = None
    query_params: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    model_id: Optional[str] = None
    # default: browser-like defaults when headers omitted; csrf_attack: session cookie, no CSRF token, no referer
    request_context_profile: Optional[Literal["default", "csrf_attack"]] = None


@router.post("/analyze")
def analyze_request(req: AnalyzeRequest, request: Request, user: dict = Depends(get_current_user)):
    """Analyze a single request - IDS core detection."""
    loaded = _load_model(req.model_id)
    if not loaded:
        raise HTTPException(503, "No trained model. Train a model first.")

    model, prep_data, ext = loaded
    feature_columns = prep_data["feature_columns"]
    label_map_inv = {v: k for k, v in prep_data["label_map"].items()}
    if prep_data.get("classification_mode") == "binary":
        label_map_inv = {0: "benign", 1: "attack"}

    payload = req.body or (str(req.query_params) if req.query_params else "") or ""
    ctx = resolve_request_context(
        req.headers,
        "csrf_attack" if req.request_context_profile == "csrf_attack" else None,
    )
    record = {
        "payload": payload,
        "request_method": req.method or "GET",
        "url": req.url or "/",
        "cookies_present": ctx["cookies_present"],
        "token_present": ctx["token_present"],
        "referrer_present": ctx["referrer_present"],
        "response_status": 200,
        "response_length": 1000,
        "response_time": 100.0,
        "error_flag": False,
        "redirection_flag": False,
    }

    feat = ext.extract_single(record)
    import pandas as pd
    row = {k: feat.get(k, 0) for k in feature_columns}
    df = pd.DataFrame([row])
    for c in feature_columns:
        if c not in df.columns:
            df[c] = 0
    df = df[feature_columns].fillna(0)

    import numpy as np

    proba_arr = np.asarray(model.predict_proba(df)[0], dtype=float).ravel()
    if hasattr(model, "classes_") and len(model.classes_) == len(proba_arr):
        cls_list = [int(x) for x in model.classes_]
    else:
        cls_list = sorted(label_map_inv.keys())
        if len(cls_list) != len(proba_arr):
            cls_list = list(range(len(proba_arr)))

    pairs: list[tuple[str, float]] = []
    for idx, p in enumerate(proba_arr):
        cid = cls_list[idx] if idx < len(cls_list) else idx
        pairs.append((label_map_inv.get(int(cid), str(cid)), float(p)))
    pairs.sort(key=lambda x: -x[1])

    pred_label = pairs[0][0]
    conf = pairs[0][1]
    second_best = pairs[1][0] if len(pairs) > 1 else None
    second_confidence = float(pairs[1][1]) if len(pairs) > 1 else None
    margin = conf - (second_confidence or 0.0)
    uncertain = bool(conf < 0.55 or margin < 0.12)

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
    top_indicators = [k for k, _ in top]

    client_ip = request.client.host if request.client else "unknown"
    alert = add_alert(
        prediction=pred_label,
        confidence=conf,
        method=req.method,
        url=req.url,
        payload_preview=payload[:200] if payload else "(empty)",
        source_ip=client_ip,
        top_indicators=top_indicators,
        second_best=second_best,
        second_confidence=second_confidence,
        confidence_margin=margin,
        uncertain=uncertain,
    )

    return {
        "prediction": pred_label,
        "confidence": conf,
        "second_best": second_best,
        "second_confidence": second_confidence,
        "confidence_margin": margin,
        "uncertain": uncertain,
        "is_attack": pred_label != "benign",
        "alert_raised": alert is not None,
        "alert_id": alert.id if alert else None,
        "top_indicators": top_indicators,
        "request_context_profile": req.request_context_profile or "default",
    }


@router.get("/alerts")
def list_alerts(limit: int = 50, since: Optional[float] = None, user: dict = Depends(get_current_user)):
    """Get recent IDS alerts."""
    return {"alerts": get_alerts(limit=limit, since=since)}


@router.get("/stats")
def ids_stats(user: dict = Depends(get_current_user)):
    """Get IDS statistics."""
    return get_stats()


@router.get("/stream")
def stream_alerts(user: dict = Depends(get_current_user)):
    """Server-Sent Events stream of real-time alerts and stats."""
    def event_generator():
        last_count = 0
        while True:
            alerts = get_alerts(limit=100)
            new_count = len(alerts) - last_count
            if new_count > 0:
                for a in alerts[:new_count]:
                    yield f"data: {json.dumps({'type': 'alert', **a})}\n\n"
                last_count = len(alerts)
            yield f"data: {json.dumps({'type': 'heartbeat', 'stats': get_stats()})}\n\n"
            time.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/clear")
def clear_ids_alerts(user: dict = Depends(get_current_user)):
    """Clear alert history (admin)."""
    clear_alerts()
    return {"status": "cleared"}
