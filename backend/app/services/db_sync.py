"""
WebGuard RF - Sync training results to database
"""

from pathlib import Path

from ..core.config import settings
from ..db import get_db, db_available
from ..db.models import TrainingJob, Model, ModelMetric


def save_model_to_db(job_id: str, metrics: dict) -> None:
    """Save model metadata and metrics to DB after training completes."""
    if not db_available():
        return
    model_id = metrics.get("model_id")
    if not model_id:
        return
    model_path = str(Path(settings.MODELS_DIR) / f"{model_id}.joblib")
    prep_path = str(Path(settings.MODELS_DIR) / f"{model_id}_preprocessor.joblib")
    config = metrics.get("config", {})
    with get_db() as db:
        if not db:
            return
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if not job:
            return
        model = Model(
            model_id=model_id,
            name=model_id,
            training_job_id=job.id,
            file_path=model_path,
            preprocessing_path=prep_path,
            classification_mode=config.get("classification_mode", "multiclass"),
            feature_mode=config.get("feature_mode", "payload_only"),
        )
        db.add(model)
        db.flush()
        for split in ("train", "validation", "test"):
            m = metrics.get(split)
            if m:
                db.add(ModelMetric(
                    model_id=model.id,
                    split_type=split,
                    accuracy=m.get("accuracy"),
                    precision_macro=m.get("precision_macro"),
                    recall_macro=m.get("recall_macro"),
                    f1_macro=m.get("f1_macro"),
                    f1_weighted=m.get("f1_weighted"),
                    roc_auc=m.get("roc_auc"),
                    false_positive_rate=m.get("false_positive_rate"),
                    false_negative_rate=m.get("false_negative_rate"),
                    per_class_metrics=m.get("per_class_metrics"),
                    confusion_matrix=m.get("confusion_matrix"),
                ))
