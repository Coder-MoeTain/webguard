"""
WebGuard RF - Feature Extraction API
"""

import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.paths import resolve_data_path
from ..core.validation import validate_data_path

router = APIRouter()
logger = logging.getLogger("webguard")


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
        ext.extract_file(input_path, output_path, format=fmt)
    except Exception as e:
        logger.exception("Feature extraction failed: %s", e)


@router.post("/extract", response_model=ExtractResponse)
def extract_features(req: ExtractRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    resolved_input = validate_data_path(req.input_path)
    if not resolved_input.exists():
        raise HTTPException(400, f"Input file not found: {req.input_path}. Generate or upload a dataset first.")
    output = req.output_path or str(resolve_data_path(settings.DATA_DIR) / f"features_{uuid.uuid4().hex[:12]}.parquet")
    if req.output_path:
        validate_data_path(req.output_path)  # ensure custom output is under DATA_DIR
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_extraction, job_id, str(resolved_input), output, req.feature_mode, req.format)
    return ExtractResponse(job_id=job_id, output_path=output)
