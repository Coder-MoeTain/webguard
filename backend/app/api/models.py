"""
WebGuard RF - Models API
"""

import joblib
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import normalize_path_for_api, resolve_data_path
from ..services.job_store import list_jobs

router = APIRouter()
_MODELS_DIR = resolve_data_path(settings.MODELS_DIR)
_EVAL_PLOTS_DIR = resolve_data_path("data/evaluation_plots")

_ALLOWED_PLOT_SUFFIXES = ("_f1_scores.png", "_confusion_matrix.png")


def _get_model_metrics_map():
    """Build model_id -> metrics from completed training jobs."""
    model_metrics = {}
    for job in list_jobs(limit=500):
        if job.get("phase") == "completed" and job.get("metrics"):
            mid = job["metrics"].get("model_id")
            if mid:
                model_metrics[mid] = job["metrics"]
    return model_metrics


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


@router.delete("/{model_id}")
def delete_model(model_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific model and its preprocessor."""
    model_path = _MODELS_DIR / f"{model_id}.joblib"
    prep_path = _MODELS_DIR / f"{model_id}_preprocessor.joblib"

    deleted: list[str] = []
    for p in (model_path, prep_path):
        if p.exists():
            try:
                p.unlink()
                deleted.append(p.name)
            except OSError as e:
                raise HTTPException(500, f"Failed to delete {p.name}: {e}")

    if not deleted:
        raise HTTPException(404, "Model not found")
    return {"deleted": deleted, "count": len(deleted)}


@router.get("/")
def list_models(
    include_metrics: bool = Query(False, description="Include test/train/val metrics per model"),
    user: dict = Depends(get_current_user),
):
    models_dir = _MODELS_DIR
    if not models_dir.exists():
        return {"models": []}
    models = []
    for f in models_dir.glob("*.joblib"):
        if "_preprocessor" not in f.name:
            model_id = f.stem
            algorithm = None
            algorithm_label = None
            prep_path = models_dir / f"{model_id}_preprocessor.joblib"
            if prep_path.exists():
                try:
                    prep_data = joblib.load(prep_path)
                    algorithm = prep_data.get("algorithm")
                    algorithm_label = prep_data.get("algorithm_label") or algorithm
                except Exception:
                    algorithm = None
                    algorithm_label = None
            display_name = algorithm_label or algorithm or f.name
            models.append(
                {
                    "id": model_id,
                    "path": str(f),
                    "name": display_name,
                    "algorithm": algorithm,
                    "algorithm_label": algorithm_label,
                }
            )

    if include_metrics:
        metrics_map = _get_model_metrics_map()
        for m in models:
            metrics = metrics_map.get(m["id"])
            if metrics:
                m["metrics"] = metrics
                m["algorithm"] = metrics.get("algorithm")
                m["algorithm_label"] = metrics.get("algorithm_label") or m.get("algorithm") or "Unknown"
                test = metrics.get("test") or {}
                m["test_accuracy"] = test.get("accuracy")
                m["test_f1_macro"] = test.get("f1_macro")
                m["test_precision_macro"] = test.get("precision_macro")
                m["test_recall_macro"] = test.get("recall_macro")
                m["train_time_seconds"] = metrics.get("train_time_seconds")
            else:
                m["metrics"] = None
                algo, algo_label = _get_algorithm_from_prep(m["id"])
                m["algorithm"] = algo
                m["algorithm_label"] = algo_label or algo or "Unknown"
                m["test_accuracy"] = None
                m["test_f1_macro"] = None
                m["test_precision_macro"] = None
                m["test_recall_macro"] = None
                m["train_time_seconds"] = None
            if not m.get("algorithm_label"):
                m["algorithm_label"] = m.get("algorithm") or "Unknown"

    return {"models": models}


@router.post("/{model_id}/evaluation-plots")
def create_evaluation_plots(model_id: str, user: dict = Depends(get_current_user)):
    """
    Generate and save F1 score and confusion matrix PNGs (train/val/test when available)
    under data/evaluation_plots/{model_id}/. Returns base64 for inline display in the UI.
    """
    if "/" in model_id or "\\" in model_id or ".." in model_id:
        raise HTTPException(400, "Invalid model_id")

    model_path = _MODELS_DIR / f"{model_id}.joblib"
    if not model_path.exists():
        raise HTTPException(404, "Model not found")

    metrics_map = _get_model_metrics_map()
    metrics = metrics_map.get(model_id)
    if not metrics:
        raise HTTPException(
            404,
            "No stored training metrics for this model. Train from the dashboard or run training so the job record includes metrics.",
        )

    try:
        from ml_pipeline.evaluation.plot_metrics import save_evaluation_plots_for_metrics
    except ImportError as e:
        raise HTTPException(500, f"Plotting dependencies missing: {e}") from e

    saved = save_evaluation_plots_for_metrics(metrics, _EVAL_PLOTS_DIR, model_id)
    if not saved:
        raise HTTPException(400, "Metrics contain no confusion matrices; cannot build plots.")

    rel_root = normalize_path_for_api(_EVAL_PLOTS_DIR.resolve())
    out = {
        "model_id": model_id,
        "directory": f"{rel_root}/{model_id}",
        "splits": {},
    }
    for split, data in saved.items():
        out["splits"][split] = {
            "f1_image_base64": data["f1_b64"],
            "confusion_image_base64": data["confusion_b64"],
            "f1_filename": Path(data["f1_png"]).name,
            "confusion_filename": Path(data["confusion_png"]).name,
        }
    return out


@router.get("/{model_id}/evaluation-plots/{filename}")
def get_evaluation_plot_file(model_id: str, filename: str, user: dict = Depends(get_current_user)):
    """Serve a previously generated evaluation PNG (auth required)."""
    if "/" in model_id or "\\" in model_id or ".." in model_id:
        raise HTTPException(400, "Invalid model_id")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")
    if not any(filename.endswith(s) for s in _ALLOWED_PLOT_SUFFIXES):
        raise HTTPException(400, "Unknown plot file type")

    path = _EVAL_PLOTS_DIR / model_id / filename
    if not path.is_file():
        raise HTTPException(404, "Plot file not found; generate plots first.")
    return FileResponse(path, media_type="image/png", filename=filename)


def _get_feature_importances(model, feature_columns: list) -> dict:
    """Get feature importances for any model type."""
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        imp = imp.tolist() if hasattr(imp, "tolist") else list(imp)
        return dict(zip(feature_columns, imp))
    if hasattr(model, "coef_"):
        import numpy as np
        coef = np.asarray(model.coef_)
        imp = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
        imp = imp / (imp.sum() + 1e-10)
        return dict(zip(feature_columns, imp.tolist()))
    n = len(feature_columns)
    return {f: 1.0 / n for f in feature_columns}


def _get_algorithm_from_prep(model_id: str) -> tuple[Optional[str], Optional[str]]:
    """Load preprocessor to get algorithm (for models without job metrics). Returns (algorithm, algorithm_label)."""
    prep_path = _MODELS_DIR / f"{model_id}_preprocessor.joblib"
    if not prep_path.exists():
        return None, None
    try:
        prep_data = joblib.load(prep_path)
        return prep_data.get("algorithm"), prep_data.get("algorithm_label")
    except Exception:
        return None, None


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
    importances = _get_feature_importances(model, feature_columns)
    top_features = sorted(importances.items(), key=lambda x: -x[1])
    return {
        "id": model_id,
        "classification_mode": prep_data.get("classification_mode", "multiclass"),
        "feature_mode": prep_data.get("feature_mode", "payload_only"),
        "algorithm": prep_data.get("algorithm"),
        "algorithm_label": prep_data.get("algorithm_label"),
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
