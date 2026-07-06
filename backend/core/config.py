from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()


class Settings(BaseModel):
    DATABASE_URL: str = Field(...)
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    APP_NAME: str = Field(default="App")
    APP_ENV: str = Field(default="development")
    APP_DEBUG: bool = Field(default=False)
    APP_HOST: str = Field(default="http://localhost:8000")
    APP_PORT: int = Field(default=8000)
    ALLOW_ORIGINS: list[str] = Field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            DATABASE_URL=os.getenv("DATABASE_URL", ""),
            SECRET_KEY=os.getenv("SECRET_KEY", ""),
            ALGORITHM=os.getenv("ALGORITHM", "HS256"),
            ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            APP_NAME=os.getenv("APP_NAME", "App"),
            APP_ENV=os.getenv("APP_ENV", "development"),
            APP_DEBUG=os.getenv("APP_DEBUG", "False").lower() in {"1", "true", "yes", "on"},
            APP_HOST=os.getenv("APP_HOST", "http://localhost:8000"),
            APP_PORT=int(os.getenv("APP_PORT", "8000")),
            ALLOW_ORIGINS=cls._parse_allow_origins(os.getenv("ALLOW_ORIGINS", "")),
        )

    @staticmethod
    def _parse_allow_origins(raw: str) -> list[str]:
        raw = raw.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except ValueError:
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        if isinstance(parsed, list):
            return [str(origin) for origin in parsed]
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()

