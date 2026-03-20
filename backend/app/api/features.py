"""
WebGuard RF - Feature Extraction API
"""

import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path
from ..core.validation import validate_data_path

router = APIRouter()
logger = logging.getLogger("webguard")

# In-memory extraction progress (job_id -> {phase, progress, output_path, error})
_extraction_status: Dict[str, Dict[str, Any]] = {}


class ExtractRequest(BaseModel):
    input_path: str
    output_path: Optional[str] = None
    feature_mode: Literal["payload_only", "response_only", "hybrid", "sqli_37"] = "payload_only"
    format: str = "parquet"


class ExtractResponse(BaseModel):
    job_id: str
    status: str = "started"
    output_path: str


def run_extraction(job_id: str, input_path: str, output_path: str, feature_mode: str, fmt: str):
    import sys
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    try:
        from ml_pipeline.feature_extraction import FeatureExtractor
        ext = FeatureExtractor(feature_mode=feature_mode)
        def progress_cb(written: int, total: int):
            pct = int(100 * written / total) if total else 0
            _extraction_status[job_id] = {
                **_extraction_status.get(job_id, {}),
                "phase": "running",
                "progress": pct,
                "written": written,
                "total": total,
                "output_path": output_path,
            }

        _extraction_status[job_id] = {
            "phase": "running",
            "progress": 0,
            "written": 0,
            "total": 0,
            "output_path": output_path,
        }
        ext.extract_file(input_path, output_path, format=fmt, progress_callback=progress_cb)
        _extraction_status[job_id] = {
            "phase": "completed",
            "progress": 100,
            "written": _extraction_status[job_id].get("written", 0),
            "total": _extraction_status[job_id].get("total", 0),
            "output_path": output_path,
        }
    except Exception as e:
        logger.exception("Feature extraction failed: %s", e)
        _extraction_status[job_id] = {
            "phase": "failed",
            "progress": 0,
            "output_path": output_path,
            "error": str(e),
        }


@router.post("/extract", response_model=ExtractResponse)
def extract_features(req: ExtractRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    resolved_input = validate_data_path(req.input_path)
    if not resolved_input.exists():
        raise HTTPException(400, f"Input file not found: {req.input_path}. Generate or upload a dataset first.")
    output = req.output_path or str(resolve_data_path(settings.DATA_DIR) / f"features_{uuid.uuid4().hex[:12]}.parquet")
    if req.output_path:
        validate_data_path(req.output_path)  # ensure custom output is under DATA_DIR
    job_id = str(uuid.uuid4())[:8]
    _extraction_status[job_id] = {"phase": "queued", "progress": 0, "output_path": output, "written": 0, "total": 0}
    background_tasks.add_task(run_extraction, job_id, str(resolved_input), output, req.feature_mode, req.format)
    return ExtractResponse(job_id=job_id, output_path=output)


@router.get("/extraction/{job_id}/status")
def get_extraction_status(job_id: str, user: dict = Depends(get_current_user)):
    status = _extraction_status.get(job_id)
    if not status:
        return {"job_id": job_id, "phase": "unknown", "progress": 0}
    return {"job_id": job_id, **status}
