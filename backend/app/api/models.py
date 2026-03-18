"""
WebGuard RF - Models API
"""

import joblib
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path

router = APIRouter()
_MODELS_DIR = resolve_data_path(settings.MODELS_DIR)


@router.post("/reset")
def reset_models(user: dict = Depends(get_current_user)):
    """Delete all model files (*.joblib) in MODELS_DIR."""
    deleted = []
    for f in _MODELS_DIR.glob("*.joblib"):
        try:
            f.unlink()
            deleted.append(f.name)
        except OSError as e:
            raise HTTPException(500, f"Failed to delete {f.name}: {e}")
    return {"deleted": deleted, "count": len(deleted)}


@router.get("/")
def list_models(user: dict = Depends(get_current_user)):
    models_dir = _MODELS_DIR
    if not models_dir.exists():
        return {"models": []}
    models = []
    for f in models_dir.glob("*.joblib"):
        if "_preprocessor" not in f.name:
            models.append({"id": f.stem, "path": str(f), "name": f.name})
    return {"models": models}


@router.get("/{model_id}")
def get_model_detail(model_id: str, user: dict = Depends(get_current_user)):
    """Return model config, feature importance, and metadata."""
    models_dir = _MODELS_DIR
    model_path = models_dir / f"{model_id}.joblib"
    prep_path = models_dir / f"{model_id}_preprocessor.joblib"
    if not model_path.exists() or not prep_path.exists():
        raise HTTPException(404, "Model not found")
    prep_data = joblib.load(prep_path)
    model = joblib.load(model_path)
    feature_columns = prep_data.get("feature_columns", [])
    importances = dict(zip(feature_columns, model.feature_importances_.tolist()))
    top_features = sorted(importances.items(), key=lambda x: -x[1])
    return {
        "id": model_id,
        "classification_mode": prep_data.get("classification_mode", "multiclass"),
        "feature_mode": prep_data.get("feature_mode", "payload_only"),
        "feature_count": len(feature_columns),
        "feature_importance": importances,
        "top_features": [{"name": k, "importance": round(v, 6)} for k, v in top_features],
        "label_map": prep_data.get("label_map", {}),
        "n_estimators": getattr(model, "n_estimators", None),
        "max_depth": getattr(model, "max_depth", None),
    }


@router.get("/{model_id}/download")
def download_model(model_id: str, user: dict = Depends(get_current_user)):
    path = _MODELS_DIR / f"{model_id}.joblib"
    if not path.exists():
        raise HTTPException(404, "Model not found")
    return FileResponse(path, filename=f"{model_id}.joblib")
