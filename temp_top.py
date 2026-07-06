from __future__ import annotations

# Make script runnable via `python main.py` by fixing sys.path
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.config import get_settings
from backend.core.database import Base, engine, get_db
from backend.models import User, Programme, Batiment, Lot
from backend.schemas import (
    UserRead,
    ProgrammeCreate,
    ProgrammeRead,
    BatimentCreate,
    BatimentRead,
    LotCreate,
    LotUpdate,
    LotRead,
    LotsStatistics,
)
from backend.auth import router as auth_router


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Always ensure tables exist so the app works out of the box
    Base.metadata.create_all(bind=engine)
    # Best-effort dev convenience without Alembic: add missing auth columns if DB is Postgres
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='users' AND column_name='username'
                    ) THEN
                        ALTER TABLE users ADD COLUMN username VARCHAR(255);
                        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
                    END IF;
                END$$;
                """
            )
            conn.exec_driver_sql(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='users' AND column_name='password_hash'
                    ) THEN
                        ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
                    END IF;
                END$$;
                """
            )
    except Exception:
        # Ignore if the dialect doesn't support these blocks or table doesn't exist yet
        pass


@app.get("/", include_in_schema=False)
def index():
    return {
        "message": f"{settings.APP_NAME} backend is running",
    }