"""
WebGuard RF - Dataset API
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path, normalize_path_for_api
from ..core.validation import validate_data_path

router = APIRouter()
_DATA_DIR = resolve_data_path(settings.DATA_DIR)
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# In-memory generation progress (job_id -> {phase, progress, written, total, output_path})
_generation_status: dict[str, dict] = {}


class GenerateRequest(BaseModel):
    total_samples: int = 5_000_000
    attack_ratio: float = 0.8
    output_format: str = "parquet"
    random_seed: Optional[int] = 42
    label_noise_ratio: float = 0.04


class GenerateResponse(BaseModel):
    job_id: str
    status: str = "started"
    message: str


def run_generation(job_id: str, total: int, attack_ratio: float, fmt: str, seed: int, label_noise: float = 0.04):
    import sys
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from ml_pipeline.dataset_generator import DatasetGenerator
    output = _DATA_DIR / f"{job_id}.{fmt}"
    _generation_status[job_id] = {"phase": "running", "progress": 0, "written": 0, "total": total, "output_path": str(output)}

    def progress_cb(written: int, total_samples: int):
        pct = int(100 * written / total_samples) if total_samples else 0
        _generation_status[job_id] = {"phase": "running", "progress": pct, "written": written, "total": total_samples, "output_path": str(output)}

    try:
        gen = DatasetGenerator(
            total_samples=total,
            attack_ratio=attack_ratio,
            benign_ratio=1 - attack_ratio,
            random_seed=seed,
            label_noise_ratio=label_noise,
        )
        gen.generate(output_path=str(output), format=fmt, progress_callback=progress_cb)
        _generation_status[job_id] = {"phase": "completed", "progress": 100, "written": total, "total": total, "output_path": str(output)}
    except Exception as e:
        _generation_status[job_id] = {"phase": "failed", "progress": 0, "error": str(e), "output_path": str(output)}


@router.get("/generation/{job_id}/status")
def get_generation_status(job_id: str, user: dict = Depends(get_current_user)):
    """Get dataset generation progress."""
    status = _generation_status.get(job_id)
    if not status:
        return {"job_id": job_id, "phase": "unknown", "progress": 0}
    return {"job_id": job_id, **status}


@router.post("/generate", response_model=GenerateResponse)
def generate_dataset(req: GenerateRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    job_id = str(uuid.uuid4())[:8]
    _generation_status[job_id] = {"phase": "starting", "progress": 0, "written": 0, "total": req.total_samples, "output_path": ""}
    background_tasks.add_task(
        run_generation,
        job_id,
        req.total_samples,
        req.attack_ratio,
        req.output_format,
        req.random_seed or 42,
        req.label_noise_ratio,
    )
    return GenerateResponse(job_id=job_id, message=f"Generation started. Output: {settings.DATA_DIR}/{job_id}.{req.output_format}")


@router.get("/preview")
def preview_dataset(path: str, limit: int = 100, user: dict = Depends(get_current_user)):
    """Return first N rows of a dataset for preview. Path relative to project root."""
    resolved = validate_data_path(path)
    if not resolved.exists():
        raise HTTPException(404, f"Dataset not found: {path}")
    import pandas as pd
    try:
        file_size = resolved.stat().st_size
        label_counts = {}
        if resolved.suffix == ".parquet":
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(resolved)
            total_rows = pf.metadata.num_rows
            if "label" in pf.schema.names:
                label_table = pq.read_table(resolved, columns=["label"])
                from collections import Counter
                col = label_table.column("label")
                raw = Counter(str(col[i]) if col[i] is not None else "" for i in range(total_rows))
                label_counts = {k: v for k, v in raw.items() if k}
            df = pd.read_parquet(resolved).head(limit)
        else:
            df = pd.read_csv(resolved, nrows=limit)
            total_rows = None
            if "label" in df.columns:
                label_counts = df["label"].value_counts().to_dict()
                label_counts = {str(k): int(v) for k, v in label_counts.items()}
        df = df.fillna("").astype(str)
        # Put label and payload first so they're visible (feature datasets have many 0/1 columns)
        cols = list(df.columns)
        priority = [c for c in ("label", "payload") if c in cols]
        rest = [c for c in cols if c not in priority]
        ordered_cols = priority + rest
        df = df[ordered_cols]
        return {
            "path": path,
            "columns": ordered_cols,
            "rows": df.to_dict(orient="records"),
            "total_rows": total_rows,
            "preview_rows": len(df),
            "file_size_bytes": file_size,
            "label_counts": label_counts,
        }
    except Exception as e:
        raise HTTPException(400, f"Could not read dataset: {e}")


@router.get("/")
def list_datasets(user: dict = Depends(get_current_user)):
    """List available datasets in DATA_DIR."""
    if not _DATA_DIR.exists():
        return {"datasets": []}
    datasets = []
    for f in sorted(_DATA_DIR.glob("*.parquet")):
        datasets.append({"path": normalize_path_for_api(f, _DATA_DIR.parent), "name": f.name, "format": "parquet"})
    for f in sorted(_DATA_DIR.glob("*.csv")):
        datasets.append({"path": normalize_path_for_api(f, _DATA_DIR.parent), "name": f.name, "format": "csv"})
    return {"datasets": sorted(datasets, key=lambda x: x["name"])}


@router.post("/reset")
def reset_datasets(user: dict = Depends(get_current_user)):
    """Delete all dataset files (*.parquet, *.csv) in DATA_DIR. Keeps reports and jobs."""
    deleted = []
    for pattern in ("*.parquet", "*.csv"):
        for f in _DATA_DIR.glob(pattern):
            try:
                f.unlink()
                deleted.append(f.name)
            except OSError as e:
                raise HTTPException(500, f"Failed to delete {f.name}: {e}")
    return {"deleted": deleted, "count": len(deleted)}


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not file.filename or not (file.filename.endswith(".csv") or file.filename.endswith(".parquet")):
        raise HTTPException(400, "Only CSV or Parquet allowed")
    path = _DATA_DIR / f"upload_{uuid.uuid4().hex[:12]}_{file.filename}"
    with open(path, "wb") as f:
        content = await file.read()
        if len(content) > settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"File too large. Max {settings.UPLOAD_MAX_SIZE_MB}MB")
        f.write(content)
    return {"path": str(path), "filename": file.filename}
