"""
WebGuard RF - System Metrics API (CPU, Memory, GPU)
"""

import subprocess
from fastapi import APIRouter, Depends

from ..core.deps import get_current_user

router = APIRouter()


def _get_cpu_memory():
    """Get CPU and memory stats using psutil if available."""
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": round(psutil.virtual_memory().used / (1024 * 1024), 1),
            "memory_total_mb": round(psutil.virtual_memory().total / (1024 * 1024), 1),
            "memory_available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 1),
        }
    except ImportError:
        return {
            "cpu_percent": 0,
            "cpu_count": 0,
            "memory_percent": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 0,
            "memory_available_mb": 0,
            "note": "Install psutil for system metrics",
        }


def _get_gpu_info():
    """Get GPU info via nvidia-smi if available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append({
                        "name": parts[0],
                        "memory_used_mb": int(parts[1].replace(" MiB", "").strip()) if "MiB" in parts[1] else int(parts[1]) if parts[1].isdigit() else 0,
                        "memory_total_mb": int(parts[2].replace(" MiB", "").strip()) if "MiB" in parts[2] else int(parts[2]) if parts[2].isdigit() else 0,
                        "utilization_percent": int(parts[3].replace("%", "").strip()) if "%" in parts[3] else int(parts[3]) if parts[3].isdigit() else 0,
                    })
            return {"available": True, "gpus": gpus}
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return {"available": False, "gpus": [], "note": "NVIDIA GPU not detected (Random Forest uses CPU)"}


@router.get("/metrics")
def get_system_metrics(user: dict = Depends(get_current_user)):
    """Get CPU, memory, and GPU metrics for training monitor."""
    cpu_mem = _get_cpu_memory()
    gpu = _get_gpu_info()
    return {
        "cpu": cpu_mem,
        "gpu": gpu,
    }
