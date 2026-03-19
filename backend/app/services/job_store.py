"""
WebGuard RF - Persistent job status store (file + optional DB)
"""

import json
from pathlib import Path
from typing import Any

from ..core.config import settings
from ..core.paths import resolve_data_path

JOBS_FILE = Path(settings.DATA_DIR) / "jobs.json"


def _ensure_file():
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    if not JOBS_FILE.exists():
        JOBS_FILE.write_text("{}")


def _file_get(job_id: str) -> dict | None:
    _ensure_file()
    data = json.loads(JOBS_FILE.read_text())
    return data.get(job_id)


def _file_set(job_id: str, status: dict[str, Any]) -> None:
    _ensure_file()
    data = json.loads(JOBS_FILE.read_text())
    existing = data.get(job_id, {})
    data[job_id] = {**existing, **status}
    JOBS_FILE.write_text(json.dumps(data, indent=2))


def _file_list(limit: int) -> list[dict]:
    _ensure_file()
    data = json.loads(JOBS_FILE.read_text())
    jobs = [{"job_id": k, **v} for k, v in reversed(list(data.items()))]
    return jobs[:limit]


def _phase_to_status(phase: str) -> str:
    m = {"starting": "running", "queued": "pending", "completed": "completed", "failed": "failed"}
    return m.get(phase, "running")


def get_job(job_id: str) -> dict | None:
    from ..db import get_db, db_available
    from ..db.models import TrainingJob
    if db_available():
        with get_db() as db:
            if db:
                row = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
                if row:
                    config = {
                        "classification_mode": row.classification_mode,
                        "feature_mode": row.feature_mode,
                        "train_ratio": row.train_ratio,
                        "val_ratio": row.val_ratio,
                        "test_ratio": row.test_ratio,
                        "n_estimators": row.n_estimators,
                        "max_depth": row.max_depth,
                        "hyperparameter_tuning": row.hyperparameter_tuning,
                    }
                    return {
                        "job_id": row.job_id,
                        "phase": row.current_phase or row.status,
                        "progress": row.progress_percent,
                        "step": row.current_phase,
                        "metrics": row.metrics_json,
                        "error": row.error_message,
                        "config": config,
                        **{k: v for k, v in (row.metrics_json or {}).items() if k in ("samples_loaded", "train_size", "val_size", "test_size", "feature_count")},
                    }
    return _file_get(job_id)


def set_job(job_id: str, status: dict[str, Any], config: dict | None = None) -> None:
    from ..db import get_db, db_available
    from ..db.models import TrainingJob
    from datetime import datetime
    to_store = {**status}
    if config is not None:
        to_store["config"] = config
    _file_set(job_id, to_store)
    if db_available():
        with get_db() as db:
            if db:
                row = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
                if row:
                    row.progress_percent = status.get("progress", row.progress_percent)
                    row.current_phase = status.get("phase", row.current_phase)
                    row.error_message = status.get("error")
                    row.metrics_json = status.get("metrics", row.metrics_json)
                    if status.get("phase") in ("completed", "failed"):
                        row.completed_at = datetime.utcnow()
                        row.status = _phase_to_status(status["phase"])
                elif config:
                    db.add(TrainingJob(
                        job_id=job_id,
                        status=status.get("phase", "pending"),
                        progress_percent=status.get("progress", 0),
                        current_phase=status.get("phase"),
                        error_message=status.get("error"),
                        metrics_json=status.get("metrics"),
                        classification_mode=config.get("classification_mode", "multiclass"),
                        feature_mode=config.get("feature_mode", "payload_only"),
                        train_ratio=config.get("train_ratio", 0.7),
                        val_ratio=config.get("val_ratio", 0.15),
                        test_ratio=config.get("test_ratio", 0.15),
                        n_estimators=config.get("n_estimators", 200),
                        max_depth=config.get("max_depth"),
                        hyperparameter_tuning=config.get("hyperparameter_tuning", False),
                    ))


def list_jobs(limit: int = 50) -> list[dict]:
    from ..db import get_db, db_available
    from ..db.models import TrainingJob
    if db_available():
        with get_db() as db:
            if db:
                rows = db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(limit).all()
                return [
                    {
                        "job_id": r.job_id,
                        "phase": r.status,
                        "progress": r.progress_percent,
                        "metrics": r.metrics_json,
                    }
                    for r in rows
                ]
    return _file_list(limit)
