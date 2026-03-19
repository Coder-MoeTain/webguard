"""
WebGuard RF - FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.rate_limit import check_rate_limit
from .api import auth, datasets, features, training, models, inference, experiments, reports, ids, robustness, system

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger("webguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WebGuard RF starting")
    logger.info("CORS allowed origins: %s", [x.strip() for x in settings.ALLOWED_ORIGINS.split(",")])
    try:
        from .db import init_db
        if init_db():
            logger.info("Database connected")
        else:
            logger.info("Database not available, using file-based storage")
    except Exception as e:
        logger.warning("Database init skipped: %s", e)
    yield
    logger.info("WebGuard RF shutting down")


app = FastAPI(
    lifespan=lifespan,
    title="WebGuard RF API",
    description="Machine Learning Driven Web Attack Detection - SQLi, XSS, CSRF",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    if not check_rate_limit(client, limit=settings.RATE_LIMIT_PER_MINUTE):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.DEBUG else str(exc)},
    )

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(features.router, prefix="/api/features", tags=["features"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(inference.router, prefix="/api/inference", tags=["inference"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(ids.router, prefix="/api/ids", tags=["ids"])
app.include_router(robustness.router, prefix="/api/robustness", tags=["robustness"])
app.include_router(system.router, prefix="/api/system", tags=["system"])


@app.get("/")
def root():
    return {"message": "WebGuard RF API", "version": "1.0.0"}


@app.get("/health")
def health():
    from .db import db_available
    return {"status": "ok", "database": db_available()}
