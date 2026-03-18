#!/usr/bin/env python3
"""Run WebGuard RF backend server."""
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
