from __future__ import annotations

# Make script runnable via `python main.py` by fixing sys.path
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.config import get_settings
from backend.core.database import Base, engine, get_db
from backend.models import User, Programme, Batiment, Lot, Client, Annexe
from backend.crud_clients import find_or_create_client
from backend.schemas import (
    UserRead,
    UserCreate,
    UserUpdate,
    ProgrammeCreate,
    ProgrammeRead,
    BatimentCreate,
    BatimentRead,
    LotCreate,
    LotUpdate,
    LotRead,
    LotsStatistics,
    AnnexeCreate,
    AnnexeRead,
)
from backend.auth import (
    ROLE_SUPER,
    ensure_user_columns,
    hash_password,
    normalize_role,
    require_superuser,
    router as auth_router,
)


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG)

_DEFAULT_ALLOW_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS or _DEFAULT_ALLOW_ORIGINS,
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
                        WHERE table_name='programmes' AND column_name='ca_bilan'
                    ) THEN
                        ALTER TABLE programmes ADD COLUMN ca_bilan DOUBLE PRECISION NULL;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='programmes' AND column_name='gfa_objectif'
                    ) THEN
                        ALTER TABLE programmes ADD COLUMN gfa_objectif DOUBLE PRECISION NULL;
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
                        WHERE table_name='clients' AND column_name='origin'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN origin VARCHAR(100) NULL;
                        ALTER TABLE clients ADD COLUMN address2 VARCHAR(255) NULL;
                        ALTER TABLE clients ADD COLUMN phone2 VARCHAR(50) NULL;
                        ALTER TABLE clients ADD COLUMN email2 VARCHAR(255) NULL;
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
            conn.exec_driver_sql(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='lots' AND column_name='client_id'
                    ) THEN
                        ALTER TABLE lots ADD COLUMN client_id INTEGER NULL;
                    END IF;
                    -- Add FK if missing
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name='lots' AND tc.constraint_type='FOREIGN KEY' AND kcu.column_name='client_id'
                    ) THEN
                        BEGIN
                            ALTER TABLE lots
                              ADD CONSTRAINT fk_lots_client
                              FOREIGN KEY (client_id)
                              REFERENCES clients(id)
                              ON DELETE SET NULL;
                        EXCEPTION WHEN others THEN
                            NULL;
                        END;
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
                        WHERE table_name='clients' AND column_name='type'
                    ) THEN
                        ALTER TABLE clients ADD COLUMN type VARCHAR(20) DEFAULT 'prospect';
                    END IF;
                    UPDATE clients SET type='prospect' WHERE type IS NULL;
                END$$;
                """
            )
    except Exception:
        # Ignore if the dialect doesn't support these blocks or table doesn't exist yet
        pass
    try:
        if engine.dialect.name == "sqlite":
            with engine.begin() as conn:
                cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(programmes)").fetchall()}
                if "ca_bilan" not in cols:
                    conn.exec_driver_sql("ALTER TABLE programmes ADD COLUMN ca_bilan REAL")
                if "gfa_objectif" not in cols:
                    conn.exec_driver_sql("ALTER TABLE programmes ADD COLUMN gfa_objectif REAL")
                client_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(clients)").fetchall()}
                if "type" not in client_cols:
                    conn.exec_driver_sql("ALTER TABLE clients ADD COLUMN type TEXT DEFAULT 'prospect'")
                conn.exec_driver_sql("UPDATE clients SET type='prospect' WHERE type IS NULL")
    except Exception:
        pass
    try:
        with Session(bind=engine) as db:
            ensure_user_columns(db)
            email = "nicolas.hirlimann@axcess.com"
            username = email.split("@")[0].lower()
            user = db.query(User).filter(User.email == email).first()
            if user:
                if user.role != ROLE_SUPER:
                    user.role = ROLE_SUPER
                    if not user.username:
                        user.username = username
                    db.add(user)
                    db.commit()
            else:
                user = User(
                    email=email,
                    username=username,
                    role=ROLE_SUPER,
                    password_hash=hash_password("ChangeMe123!"),
                )
                db.add(user)
                db.commit()
    except Exception:
        pass


@app.get("/", include_in_schema=False)
def index():
    return {
        "message": f"{settings.APP_NAME} backend is running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    # DB ping for a real connectivity check
    db.execute(text("SELECT 1"))
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


# --- Users minimal CRUD ---
@app.get("/users", response_model=list[UserRead], dependencies=[Depends(require_superuser)])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.desc()).all()


@app.get("/users/id/{user_id}", response_model=UserRead, dependencies=[Depends(require_superuser)])
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users", response_model=UserRead, status_code=201, dependencies=[Depends(require_superuser)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    ensure_user_columns(db)
    if not payload.username and not payload.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email required")
    username = (payload.username or (payload.email.split("@")[0] if payload.email else "")).lower() or None
    role = normalize_role(payload.role)
    filters = []
    if payload.email:
        filters.append(User.email == str(payload.email))
    if username:
        filters.append(User.username == username)
    existing = db.query(User).filter(or_(*filters)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = User(
        email=str(payload.email) if payload.email else None,
        username=username,
        full_name=payload.full_name,
        role=role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_superuser)])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.username is not None:
        user.username = payload.username.lower() if payload.username else None
    if payload.email is not None:
        user.email = str(payload.email) if payload.email else None
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = normalize_role(payload.role)
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=204, dependencies=[Depends(require_superuser)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return Response(status_code=204)


app.include_router(auth_router)


# ----------------- Programmes -----------------

@app.get("/programmes", response_model=list[ProgrammeRead])
def list_programmes(db: Session = Depends(get_db)):
    programmes = db.query(Programme).order_by(Programme.id.desc()).all()
    lots = (
        db.query(Lot, Batiment)
        .join(Batiment, Batiment.id == Lot.batiment_id)
        .all()
    )
    stats_by_programme: dict[int, dict[str, float]] = {}
    for lot, bat in lots:
        pid = bat.programme_id
        bucket = stats_by_programme.setdefault(pid, {"count": 0, "total": 0.0, "realise": 0.0})
        bucket["count"] += 1
        price = float(getattr(lot, "prix_total", 0) or 0)
        bucket["total"] += price
        if _normalize_lot_status(getattr(lot, "statut", None)) == "acte":
            bucket["realise"] += price
    # Renvoyer explicitement les champs cles attendus par le front
    return [
        {
            "id": p.id,
            "nom": p.nom,
            "ville": p.ville,
            "adresse": p.adresse,
            "ca_bilan": float(p.ca_bilan or 0.0),
            "gfa_objectif": p.gfa_objectif,
            "lots_count": stats_by_programme.get(p.id, {}).get("count", 0),
            "ca_total": round(stats_by_programme.get(p.id, {}).get("total", 0.0), 2),
            "ca_realise": round(stats_by_programme.get(p.id, {}).get("realise", 0.0), 2),
            "ca_restant": round(
                stats_by_programme.get(p.id, {}).get("total", 0.0)
                - stats_by_programme.get(p.id, {}).get("realise", 0.0),
                2,
            ),
            # Les autres champs du schema resteront a leur valeur par defaut/None
        }
        for p in programmes
    ]


@app.post("/programmes", response_model=ProgrammeRead, status_code=201)
def create_programme(payload: ProgrammeCreate, db: Session = Depends(get_db)):
    # Keep original create logic and return ORM object for backward compatibility
    p = Programme(**payload.model_dump(exclude_none=True))
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@app.get("/programmes/{programme_id}", response_model=ProgrammeRead)
def get_programme(programme_id: int, db: Session = Depends(get_db)):
    p = db.get(Programme, programme_id)
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")
    return p


@app.put("/programmes/{programme_id}", response_model=ProgrammeRead)
def update_programme(programme_id: int, patch: dict, db: Session = Depends(get_db)):
    p = db.get(Programme, programme_id)
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")
    data = dict(patch or {})
    allowed = {c.name for c in Programme.__table__.columns}
    for k, v in data.items():
        if k in allowed and k != "id":
            setattr(p, k, v)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@app.delete("/programmes/{programme_id}")
def delete_programme(programme_id: int, db: Session = Depends(get_db)):
    p = db.get(Programme, programme_id)
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")
    db.delete(p)
    db.commit()
    return {"message": "Programme supprimé"}


@app.get("/programmes/{programme_id}/statistics", response_model=LotsStatistics)
def programme_statistics(programme_id: int, db: Session = Depends(get_db)):
    # gather lots for programme via batiments
    bat_ids = [b.id for b in db.query(Batiment).filter(Batiment.programme_id == programme_id).all()]
    lots = []
    if bat_ids:
        lots = db.query(Lot).filter(Lot.batiment_id.in_(bat_ids)).all()
    return _compute_stats(lots)


# ----------------- BÃ¢timents -----------------

@app.get("/batiments", response_model=list[BatimentRead])
def list_batiments(programme_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Batiment).where(Batiment.programme_id == programme_id).order_by(Batiment.nom.asc()).all()


@app.post("/batiments", response_model=BatimentRead, status_code=201)
def create_batiment(payload: BatimentCreate, db: Session = Depends(get_db)):
    if not db.get(Programme, payload.programme_id):
        raise HTTPException(status_code=404, detail="Programme not found")
    b = Batiment(**payload.model_dump(exclude_none=True))
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@app.put("/batiments/{batiment_id}", response_model=BatimentRead)
def update_batiment(batiment_id: int, payload: BatimentCreate, db: Session = Depends(get_db)):
    b = db.get(Batiment, batiment_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bâtiment not found")
    # We only update fields that are meaningful. Usually just matching the payload.
    # Note: payload includes programme_id, but usually we don't move buildings between programmes.
    # We'll just update the name/nom if present.
    # Actually payload is BatimentCreate, let's just update attributes.
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(b, k, v)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@app.delete("/batiments/{batiment_id}", status_code=204)
def delete_batiment(batiment_id: int, db: Session = Depends(get_db)):
    b = db.get(Batiment, batiment_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bâtiment not found")
    # Cascade delete lots? 
    # SQLAlchemy relationship might handle it if defined with cascade="all, delete", 
    # OR DB foreign key "ON DELETE CASCADE". 
    # But explicitly:
    db.query(Lot).filter(Lot.batiment_id == batiment_id).delete()
    db.delete(b)
    db.commit()
    return Response(status_code=204)


# ----------------- Lots -----------------

@app.get("/lots", response_model=list[LotRead])
def list_lots(
    programme_id: int | None = None,
    batiment_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(Lot, Programme.nom, Client)
        .join(Batiment, Batiment.id == Lot.batiment_id)
        .join(Programme, Programme.id == Batiment.programme_id)
        .outerjoin(Client, Client.id == Lot.client_id)
    )
    if batiment_id:
        q = q.where(Lot.batiment_id == batiment_id)
    elif programme_id:
        # Optimization: since we joined Programme, we can filter on it or via Batiment
        q = q.where(Batiment.programme_id == programme_id)

    rows = q.order_by(Lot.id.desc()).all()
    
    results = []
    for lot, p_nom, client in rows:
        # Convert ORM object to dict safe for Pydantic
        item = {k: v for k, v in lot.__dict__.items() if not k.startswith("_")}
        item["programme_name"] = p_nom
        
        # Resolve client name
        if client:
            item["client_name"] = f"{client.last_name} {client.first_name}".strip()
        else:
            item["client_name"] = lot.acquereur
        
        results.append(item)
    return results


@app.post("/lots", response_model=LotRead, status_code=201)
def create_lot(payload: LotCreate, db: Session = Depends(get_db)):
    b = db.get(Batiment, payload.batiment_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bǽtiment not found")
    l = Lot(**payload.model_dump(exclude_none=True))
    db.add(l)
    db.commit()
    db.refresh(l)
    return l
@app.put("/lots/{lot_id}", response_model=LotRead)
def update_lot(lot_id: int, patch: LotUpdate, db: Session = Depends(get_db)):
    l = db.get(Lot, lot_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lot not found")
    # Apply patch updates to the object (but don't commit yet)
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(l, k, v)

    # Recalculate logic
    # We need to ensure consistency:
    # Prix logement = Prix total - Prix stationnement
    # Prix m2 ... 
    
    # helper: get value from attribute, fallback to 0.0 if None
    def val(field):
        return float(getattr(l, field, 0.0) or 0.0)

    # 1. Update prix_logement based on total & parking
    # (The user said "Prix logement TTC non éditable, calcul automatique : Prix logement TTC = Prix total TTC – Prix stationnement TTC")
    p_total = val("prix_total")
    p_parking = val("prix_stationnement")
    new_p_logement = p_total - p_parking
    l.prix_logement = new_p_logement

    # 2. Recalculate m2 prices
    # "Conserver “Prix au m² stationnement inclus” comme référence principale" -> implied logic?
    # Usually p_m2 = price / surface. 
    # Let's assume sha_m2 is the reference surface.
    surface = val("sha_m2")
    if surface > 0:
        l.prix_m2_appartement = new_p_logement / surface
        l.prix_m2_appart_parking = p_total / surface
    else:
        l.prix_m2_appartement = 0.0
        l.prix_m2_appart_parking = 0.0

    db.add(l)
    db.commit()
    db.refresh(l)
    return l


@app.delete("/lots/{lot_id}", status_code=204)
def delete_lot(lot_id: int, db: Session = Depends(get_db)):
    l = db.get(Lot, lot_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lot not found")
    db.delete(l)
    db.commit()
    return Response(status_code=204)


@app.get("/lots/statistics", response_model=LotsStatistics)
def lots_statistics(programme_id: int | None = None, db: Session = Depends(get_db)):
    # If programme_id provided, compute stats for that programme; otherwise global stats
    if programme_id is not None:
        bat_ids = [b.id for b in db.query(Batiment).filter(Batiment.programme_id == programme_id).all()]
        lots = db.query(Lot).filter(Lot.batiment_id.in_(bat_ids)).all() if bat_ids else []
    else:
        lots = db.query(Lot).all()
    return _compute_stats(lots)


def _normalize_lot_status(value: str | None) -> str:
    if not value:
        return "libre"
    raw = value.strip().lower()
    mapping = {
        "libre": "libre",
        "disponible": "libre",
        "option": "option",
        "reserve": "reserve",
        "reservé": "reserve",
        "reserver": "reserve",
        "reservation": "reserve",
        "réservation": "reserve",
        "transit": "transit",
        "acte": "acte",
        "acté": "acte",
    }
    return mapping.get(raw, raw)


@app.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(Lot, Batiment, Programme)
        .select_from(Lot)
        .join(Batiment, Batiment.id == Lot.batiment_id)
        .join(Programme, Programme.id == Batiment.programme_id)
        .order_by(Lot.id.desc())
        .all()
    )
    counts = {"disponible": 0, "option": 0, "reserve": 0, "acte": 0, "transit": 0}
    ca_total = 0.0
    ca_encaisse = 0.0
    lots_disponibles = []
    for lot, bat, prog in rows:
        statut = _normalize_lot_status(getattr(lot, "statut", None))
        price = float(getattr(lot, "prix_total", 0) or 0)
        ca_total += price
        if statut == "acte":
            counts["acte"] += 1
            ca_encaisse += price
        elif statut == "option":
            counts["option"] += 1
        elif statut == "reserve":
            counts["reserve"] += 1
        elif statut == "transit":
            counts["transit"] += 1
        else:
            counts["disponible"] += 1
        if statut != "acte":
            lots_disponibles.append({
                "id": lot.id,
                "lot": lot.lot,
                "statut": statut,
                "prix_total": price,
                "type": lot.type,
                "batiment_id": bat.id,
                "programme_id": prog.id,
                "programme_name": prog.nom,
            })
    return {
        "counts": counts,
        "ca": {
            "total": round(ca_total, 2),
            "encaisse": round(ca_encaisse, 2),
            "restant": round(ca_total - ca_encaisse, 2),
        },
        "lots_disponibles": lots_disponibles,
    }


@app.get("/lots/export")
def export_lots_csv(programme_id: int = Query(...), db: Session = Depends(get_db)):
    import csv
    from io import StringIO

    batiments = db.query(Batiment).filter(Batiment.programme_id == programme_id).all()
    bat_by_id = {b.id: b for b in batiments}
    bat_ids = list(bat_by_id.keys())
    lots = db.query(Lot).filter(Lot.batiment_id.in_(bat_ids)).order_by(Lot.id.asc()).all() if bat_ids else []

    headers = [
        "batiment_nom",
        "lot",
        "niveau",
        "type",
        "surface_sol",
        "sha_m2",
        "orientation",
        "garage",
        "parking1",
        "parking2",
        "cave",
        "jardin",
        "terrasse",
        "prix_logement",
        "prix_stationnement",
        "prix_total",
        "prix_m2_appartement",
        "prix_m2_appart_parking",
        "acquereur",
        "statut",
    ]
    bool_fields = {"garage", "parking1", "parking2", "cave"}
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for l in lots:
        row = {}
        for h in headers:
            if h == "batiment_nom":
                row[h] = bat_by_id[l.batiment_id].nom if l.batiment_id in bat_by_id else ""
            elif h in bool_fields:
                row[h] = "Oui" if getattr(l, h) else "Non"
            else:
                row[h] = getattr(l, h)
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=lots_programme_{programme_id}.csv"})


from fastapi import UploadFile, File


@app.get("/lots/csv-template")
def download_csv_template():
    from io import StringIO
    import csv

    headers = [
        "batiment_nom", "lot", "niveau", "type", "surface_sol", "sha_m2",
        "orientation", "garage", "parking1", "parking2", "cave", "jardin",
        "terrasse", "prix_logement", "prix_stationnement", "prix_total",
        "prix_m2_appartement", "prix_m2_appart_parking", "acquereur", "statut",
    ]
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=modele_grille_prix.csv"})


@app.post("/lots/import", status_code=201)
async def import_lots_csv(programme_id: int = Query(...), db: Session = Depends(get_db), file: UploadFile = File(...)):
    content = await file.read()
    return await _import_lots_impl(programme_id, db, file=content)


async def _import_lots_impl(programme_id: int, db: Session, file: bytes | None):
    from io import StringIO
    import csv

    print(f"[IMPORT] programme_id={programme_id}, file={'None' if file is None else f'{len(file)} bytes'}")

    if file is None:
        return {"created": 0, "updated": 0, "errors": []}

    bats = db.query(Batiment).filter(Batiment.programme_id == programme_id).all()
    by_name = {b.nom: b for b in bats}
    print(f"[IMPORT] bâtiments existants: {list(by_name.keys())}")

    raw = file.decode("utf-8")
    buf = StringIO(raw)
    reader = csv.DictReader(buf)
    print(f"[IMPORT] colonnes CSV détectées: {reader.fieldnames}")

    created = 0
    updated = 0
    errors = []

    for line_num, row in enumerate(reader, start=2):
        bat_nom = (row.get("batiment_nom") or "").strip()
        lot_num = (row.get("lot") or "").strip()
        print(f"[IMPORT] ligne {line_num}: batiment_nom={bat_nom!r}, lot={lot_num!r}")

        if not bat_nom:
            errors.append({"ligne": line_num, "raison": "batiment_nom manquant"})
            continue
        if not lot_num:
            errors.append({"ligne": line_num, "raison": "numéro de lot manquant"})
            continue

        if bat_nom not in by_name:
            new_bat = Batiment(nom=bat_nom, programme_id=programme_id)
            db.add(new_bat)
            db.flush()
            by_name[bat_nom] = new_bat
            print(f"[IMPORT] bâtiment créé: {bat_nom!r} (id={new_bat.id})")

        bat = by_name[bat_nom]

        payload = {}
        for k in ("lot", "niveau", "type", "orientation", "acquereur", "statut"):
            if k in row:
                payload[k] = row[k] or None

        for k in ("surface_sol", "sha_m2", "jardin", "terrasse", "prix_logement", "prix_stationnement", "prix_total", "prix_m2_appartement", "prix_m2_appart_parking"):
            if row.get(k) not in (None, ""):
                try:
                    payload[k] = float(row[k])
                except ValueError:
                    errors.append({"ligne": line_num, "raison": f"valeur numérique invalide pour '{k}': {row[k]!r}"})

        for k in ("garage", "parking1", "parking2", "cave"):
            v = (row.get(k) or "").strip().lower()
            payload[k] = v in ("1", "true", "oui", "yes", "y")

        existing = db.query(Lot).filter(Lot.batiment_id == bat.id, Lot.lot == lot_num).first()
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            updated += 1
            print(f"[IMPORT] lot mis à jour: {lot_num!r} dans {bat_nom!r}")
        else:
            db.add(Lot(batiment_id=bat.id, **payload))
            created += 1
            print(f"[IMPORT] lot créé: {lot_num!r} dans {bat_nom!r}")

    db.commit()
    print(f"[IMPORT] terminé: created={created}, updated={updated}, errors={len(errors)}")
    return {"created": created, "updated": updated, "errors": errors}

def _compute_stats(lots: list[Lot]) -> LotsStatistics:
    def norm_status(s: str | None) -> str:
        if not s:
            return "Libre"
        s = s.strip().lower()
        mapping = {
            "libre": "Libre",
            "disponible": "Libre",
            "option": "Option",
            "reservé": "Réservation",
            "reserve": "Réservation",
            "réservé": "Réservation",
            "reservation": "Réservation",
            "réservation": "Réservation",
            "transit": "Réservation",
            "acté": "Acté",
            "acte": "Acté",
        }
        return mapping.get(s, s.capitalize())

    total = len(lots)
    actes = 0
    reservations = 0
    options = 0
    libres = 0
    ca_total = 0.0
    ca_actes = 0.0
    ca_res = 0.0
    for l in lots:
        st = norm_status(getattr(l, "statut", None))
        price = float(getattr(l, "prix_total", 0) or 0)
        ca_total += price
        if st == "Acté":
            actes += 1
            ca_actes += price
        elif st in ("Réservation", "Reservé", "Reserve"):
            reservations += 1
            ca_res += price
        elif st == "Option":
            options += 1
        else:
            libres += 1
    return LotsStatistics(
        lots_total=total,
        actes=actes,
        reservations=reservations,
        options=options,
        libres=libres,
        ca_total=round(ca_total, 2),
        ca_actes=round(ca_actes, 2),
        ca_reservations=round(ca_res, 2),
    )


# ----------------- Clients -----------------

from backend.schemas import ClientCreate, ClientRead, ClientBasic, ClientUpdate


@app.get("/clients", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Client.id,
            Client.civility,
            Client.type,
            Client.last_name,
            Client.first_name,
            Client.address,
            Client.address2,
            Client.phone,
            Client.phone2,
            Client.email,
            Client.email2,
            Client.origin,
            Client.partner_id,
            Programme.id.label("programme_id"),
            Programme.nom.label("programme_name"),
            Lot.id.label("lot_id"),
            Lot.lot.label("lot_label"),
        )
        .select_from(Client)
        .outerjoin(Lot, Lot.client_id == Client.id)
        .outerjoin(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Programme, Programme.id == Batiment.programme_id)
        .order_by(Client.id.desc(), Lot.id.desc())
        .all()
    )
    # Build a lookup of basic partner info (nom/prenom/email/tel) to embed
    # in each row without adding extra lines for the linked client. We keep
    # every Client row in the response (no filtering out of "partner" rows):
    # a couple is stored as two independent Client rows, but the frontend
    # only needs a single line per couple with the partner's info attached,
    # so we let the caller decide how to group/display it.
    partner_ids = {r.partner_id for r in rows if r.partner_id}
    partners_by_id = {}
    if partner_ids:
        for p in db.query(Client).filter(Client.id.in_(partner_ids)).all():
            partners_by_id[p.id] = {
                "id": p.id,
                "civility": p.civility,
                "type": p.type,
                "last_name": p.last_name,
                "first_name": p.first_name,
                "email": p.email,
                "phone": p.phone,
                "partner_id": p.partner_id,
            }
    result = []
    seen = set()
    for r in rows:
        key = (r.id, r.lot_id)
        seen.add(key)
        result.append({
            "id": r.id,
            "civility": r.civility,
            "type": r.type,
            "last_name": r.last_name,
            "first_name": r.first_name,
            "address": r.address,
            "address2": r.address2,
            "phone": r.phone,
            "phone2": r.phone2,
            "email": r.email,
            "email2": r.email2,
            "origin": r.origin,
            "partner_id": r.partner_id,
            "partner": partners_by_id.get(r.partner_id) if r.partner_id else None,
            "programme_id": r.programme_id,
            "programme_name": r.programme_name,
            "lot_id": r.lot_id,
            "lot_label": r.lot_label,
        })
    # Also associate by text match on lots.acquereur when client_id is NULL
    unmatched_lots = (
        db.query(Lot, Batiment, Programme)
        .select_from(Lot)
        .outerjoin(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Programme, Programme.id == Batiment.programme_id)
        .filter(Lot.client_id.is_(None))
        .filter(Lot.acquereur.isnot(None))
        .all()
    )
    clients = db.query(Client).all()
    for lot, bat, prog in unmatched_lots:
        aq = (lot.acquereur or "").strip().lower()
        if not aq:
            continue
        for c in clients:
            name1 = f"{(c.last_name or '').strip()} {(c.first_name or '').strip()}".strip().lower()
            name2 = f"{(c.first_name or '').strip()} {(c.last_name or '').strip()}".strip().lower()
            email = (c.email or "").strip().lower()
            if (name1 and name1 in aq) or (name2 and name2 in aq) or (email and email == aq):
                key = (c.id, lot.id)
                if key in seen:
                    continue
                seen.add(key)
                result.append({
                    "id": c.id,
                    "civility": c.civility,
                    "type": c.type,
                    "last_name": c.last_name,
                    "first_name": c.first_name,
                    "address": c.address,
                    "address2": c.address2,
                    "phone": c.phone,
                    "phone2": c.phone2,
                    "email": c.email,
                    "email2": c.email2,
                    "origin": c.origin,
                    "programme_id": getattr(prog, 'id', None),
                    "programme_name": getattr(prog, 'nom', None),
                    "lot_id": lot.id,
                    "lot_label": lot.lot,
                })
                break
    return result


def _client_to_dict(c: Client) -> dict:
    return {
        "id": c.id,
        "civility": c.civility,
        "type": c.type,
        "last_name": c.last_name,
        "first_name": c.first_name,
        "address": c.address,
        "address2": c.address2,
        "phone": c.phone,
        "phone2": c.phone2,
        "email": c.email,
        "email2": c.email2,
        "origin": c.origin,
        "partner_id": c.partner_id,
        "programme_id": None,
        "programme_name": None,
        "lot_id": None,
        "lot_label": None,
    }


@app.post("/clients", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    partner_payload = payload.partner
    data = payload.model_dump(exclude_none=True, exclude={"partner"})
    raw_type = (data.get("type") or "prospect").strip().lower()
    if raw_type not in ("prospect", "acquereur"):
        raw_type = "prospect"
    data["type"] = raw_type
    c = find_or_create_client(db, data)

    if partner_payload is not None:
        partner_data = partner_payload.model_dump(exclude_none=True, exclude={"partner"})
        raw_partner_type = (partner_data.get("type") or "prospect").strip().lower()
        if raw_partner_type not in ("prospect", "acquereur"):
            raw_partner_type = "prospect"
        partner_data["type"] = raw_partner_type
        partner = find_or_create_client(db, partner_data)
        c.partner_id = partner.id
        partner.partner_id = c.id

    db.commit()
    db.refresh(c)
    result = _client_to_dict(c)
    if c.partner_id:
        partner_obj = db.get(Client, c.partner_id)
        if partner_obj:
            result["partner"] = {
                "id": partner_obj.id,
                "civility": partner_obj.civility,
                "type": partner_obj.type,
                "last_name": partner_obj.last_name,
                "first_name": partner_obj.first_name,
                "address": partner_obj.address,
                "address2": partner_obj.address2,
                "phone": partner_obj.phone,
                "phone2": partner_obj.phone2,
                "email": partner_obj.email,
                "email2": partner_obj.email2,
                "origin": partner_obj.origin,
                "partner_id": partner_obj.partner_id,
            }
    return result


@app.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    data = payload.model_dump(exclude_none=True)
    if "type" in data:
        raw_type = (data.get("type") or "prospect").strip().lower()
        data["type"] = raw_type if raw_type in ("prospect", "acquereur") else "prospect"
    for k, v in data.items():
        setattr(c, k, v)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _client_to_dict(c)


@app.get("/clients/all", response_model=list[ClientBasic])
def list_clients_basic(db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.last_name.asc(), Client.first_name.asc()).all()
    out: list[ClientBasic] = []
    for c in clients:
        out.append(ClientBasic(
            id=c.id,
            civility=c.civility,
            type=c.type,
            last_name=c.last_name,
            first_name=c.first_name,
            email=c.email,
        ))
    return out


@app.delete("/clients/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.query(Lot).filter(Lot.client_id == client_id).update({"client_id": None}, synchronize_session=False)
    db.delete(client)
    db.commit()
    return Response(status_code=204)


## mapping helpers removed


# ----------------- Annexes -----------------

@app.post("/lots/{lot_id}/annexes", response_model=AnnexeRead, status_code=201)
def create_annexe(lot_id: int, payload: AnnexeCreate, db: Session = Depends(get_db)):
    if not db.get(Lot, lot_id):
        raise HTTPException(status_code=404, detail="Lot introuvable")
    a = Annexe(lot_id=lot_id, type=payload.type, numero=payload.numero or None)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@app.delete("/annexes/{annexe_id}", status_code=204)
def delete_annexe(annexe_id: int, db: Session = Depends(get_db)):
    a = db.get(Annexe, annexe_id)
    if not a:
        raise HTTPException(status_code=404, detail="Annexe introuvable")
    db.delete(a)
    db.commit()
    return Response(status_code=204)




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=settings.APP_PORT)
