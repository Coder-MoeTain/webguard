"""
WebGuard RF - Configuration
"""

from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List

# Project root (parent of backend/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "WebGuard RF"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002,http://127.0.0.1:3003,http://127.0.0.1:3004"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "webguard"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "webguard_rf"
    USE_DATABASE: bool = True
    REDIS_URL: str = "redis://localhost:6379/0"
    DATA_DIR: str = "./data"
    MODELS_DIR: str = "./models"
    UPLOAD_MAX_SIZE_MB: int = 500
    BCRYPT_ROUNDS: int = 12
    JWT_EXPIRE_MINUTES: int = 60
    # IDS dashboard polls alerts+stats every ~2s + simulator; 100/min hit 429 with CORS traffic
    RATE_LIMIT_PER_MINUTE: int = 600
    DEFAULT_N_ESTIMATORS: int = 200
    DEFAULT_MAX_DEPTH: int = 30
    DEFAULT_RANDOM_STATE: int = 42
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/webguard.log"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [x.strip() for x in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = str(_PROJECT_ROOT / ".env")
        extra = "ignore"


settings = Settings()
