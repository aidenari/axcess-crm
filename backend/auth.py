from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.models import User
from backend.schemas import LoginPayload, Token, UserRegister, UserRead


router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
settings = get_settings()

ROLE_SUPER = "super_utilisateur"
ROLE_ADMIN = "admin"
ROLE_COMMERCIAL = "commercial"
ROLE_READONLY = "lecture_seule"


def normalize_role(value: str | None) -> str:
    if not value:
        return ROLE_COMMERCIAL
    raw = value.strip().lower()
    mapping = {
        "super utilisateur": ROLE_SUPER,
        "super_utilisateur": ROLE_SUPER,
        "super-user": ROLE_SUPER,
        "admin": ROLE_ADMIN,
        "administrateur": ROLE_ADMIN,
        "commercial": ROLE_COMMERCIAL,
        "lecture seule": ROLE_READONLY,
        "lecture_seule": ROLE_READONLY,
        "read_only": ROLE_READONLY,
        "readonly": ROLE_READONLY,
    }
    return mapping.get(raw, raw)


def ensure_user_columns(db: Session) -> None:
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "postgresql":
        db.execute(text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='username'
                ) THEN
                    ALTER TABLE users ADD COLUMN username VARCHAR(255);
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='password_hash'
                ) THEN
                    ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role'
                ) THEN
                    ALTER TABLE users ADD COLUMN role VARCHAR(50);
                END IF;
            END$$;
            """
        ))
    else:
        try:
            rows = db.execute(text("PRAGMA table_info(users)")).fetchall()
            cols = {r[1] for r in rows}
            if "username" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
                db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
            if "password_hash" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            if "role" not in cols:
                db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50)"))
        except Exception:
            return
    db.execute(text("UPDATE users SET role = :role WHERE role IS NULL"), {"role": ROLE_COMMERCIAL})
    db.commit()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    ensure_user_columns(db)
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if normalize_role(current_user.role) != ROLE_SUPER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.post("/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    ensure_user_columns(db)
    username = (payload.email.split("@")[0]).lower()
    existing = db.query(User).filter((User.email == payload.email) | (User.username == username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = User(
        email=str(payload.email),
        username=username,
        full_name=payload.full_name,
        role=ROLE_COMMERCIAL,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    ensure_user_columns(db)
    user = db.query(User).filter(User.username == payload.username.lower()).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username}, expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
