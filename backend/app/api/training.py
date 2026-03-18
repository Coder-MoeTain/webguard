"""
WebGuard RF - Training API
"""

import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional, Literal

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path
from ..core.validation import validate_data_path
from ..services.job_store import get_job, set_job, list_jobs
from ..services.db_sync import save_model_to_db

router = APIRouter()
logger = logging.getLogger("webguard")
Path(settings.MODELS_DIR).mkdir(parents=True, exist_ok=True)


class TrainingConfig(BaseModel):
    data_path: str
    classification_mode: Literal["binary", "multiclass"] = "multiclass"
    feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"] = "payload_only"
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    n_estimators: int = 200
    max_depth: Optional[int] = 30
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    max_features: str = "sqrt"
    random_state: int = 42
    hyperparameter_tuning: bool = False

    @model_validator(mode="after")
    def check_ratios(self):
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"train_ratio + val_ratio + test_ratio must equal 1.0, got {total:.2f}")
        return self


class TrainingResponse(BaseModel):
    job_id: str
    status: str = "started"
    message: str


def run_training(job_id: str, config: dict):
    def progress_cb(data):
        if isinstance(data, dict):
            set_job(job_id, data)
        else:
            set_job(job_id, {"phase": str(data), "progress": 0})

    import sys
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from ml_pipeline.training import RandomForestTrainer

    data_path = str(resolve_data_path(config["data_path"]))
    config = {**config, "data_path": data_path}

    set_job(job_id, {"phase": "starting", "progress": 0, "step": "init"}, config=config)
    trainer = RandomForestTrainer(
        classification_mode=config["classification_mode"],
        feature_mode=config.get("feature_mode", "payload_only"),
        n_estimators=config["n_estimators"],
        max_depth=config["max_depth"],
        min_samples_split=config["min_samples_split"],
        min_samples_leaf=config["min_samples_leaf"],
        max_features=config["max_features"],
        random_state=config["random_state"],
        hyperparameter_tuning=config["hyperparameter_tuning"],
        progress_callback=progress_cb,
    )
    try:
        metrics = trainer.train(
            data_path=config["data_path"],
            output_dir=settings.MODELS_DIR,
            train_ratio=config["train_ratio"],
            val_ratio=config["val_ratio"],
            test_ratio=config["test_ratio"],
        )
        set_job(job_id, {"phase": "completed", "progress": 100, "metrics": metrics, "step": "complete"})
        save_model_to_db(job_id, metrics)
    except Exception as e:
        set_job(job_id, {"phase": "failed", "progress": 0, "error": str(e), "step": "failed"})


@router.get("/")
def list_training_jobs(limit: int = 20, user: dict = Depends(get_current_user)):
    return {"jobs": list_jobs(limit=limit)}


@router.post("/start", response_model=TrainingResponse)
def start_training(config: TrainingConfig, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    resolved = validate_data_path(config.data_path)
    if not resolved.exists():
        raise HTTPException(400, f"Data file not found: {config.data_path}. Generate or upload a dataset first.")
    job_id = str(uuid.uuid4())[:12]
    cfg = config.model_dump()
    set_job(job_id, {"phase": "queued", "progress": 0}, config=cfg)
    background_tasks.add_task(run_training, job_id, cfg)
    return TrainingResponse(job_id=job_id, message="Training started")


@router.get("/{job_id}/status")
def get_training_status(job_id: str, user: dict = Depends(get_current_user)):
    status_data = get_job(job_id)
    if not status_data:
        raise HTTPException(404, "Job not found")
    return status_data
