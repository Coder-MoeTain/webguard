"""
WebGuard RF - Experiments API
"""

from fastapi import APIRouter, Depends

from ..core.deps import get_current_user

router = APIRouter()


@router.get("/")
def list_experiments(user: dict = Depends(get_current_user)):
    return {"experiments": []}


@router.get("/{exp_id}")
def get_experiment(exp_id: str, user: dict = Depends(get_current_user)):
    return {"id": exp_id, "metrics": {}}
