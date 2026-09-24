from __future__ import annotations

# Make script runnable via `python main.py` by fixing sys.path
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import re
import unicodedata

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
    LOT_STATUTS,
    LOT_DATE_MIN_YEAR,
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
    expose_headers=["Content-Disposition"],
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


def _natural_sort_key(value: str | None) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", value or "")]


def _slugify(value: str | None) -> str:
    ascii_value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return slug or "export"


def _build_xlsx_response(
    headers: list[str],
    rows: list[list],
    sheet_title: str,
    filename: str,
    money_columns: set[int] = frozenset(),
    bold_last_row: bool = False,
) -> StreamingResponse:
    """Genere un .xlsx en memoire (lecture seule, aucune ecriture en base) et
    le renvoie en telechargement. Partage par tous les exports xlsx :
    en-tete gras, largeurs de colonnes ajustees, meme media type."""
    from io import BytesIO

    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = re.sub(r"[\[\]:*?/\\]", "", sheet_title or "Export")[:31] or "Export"

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append(row)

    if bold_last_row and ws.max_row > 1:
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)

    for col_idx in money_columns:
        for row_idx in range(2, ws.max_row + 1):
            ws.cell(row=row_idx, column=col_idx).number_format = "#,##0 €"

    for col_idx, header in enumerate(headers, start=1):
        width = len(header)
        for row_idx in range(2, ws.max_row + 1):
            v = ws.cell(row=row_idx, column=col_idx).value
            # Une formule (=SUM(...)) ne compte pas pour la largeur affichee.
            if v is not None and not (isinstance(v, str) and v.startswith("=")):
                width = max(width, len(str(v)))
        ws.column_dimensions[get_column_letter(col_idx)].width = width + 2

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/programmes/{programme_id}/export")
def export_programme_xlsx(programme_id: int, db: Session = Depends(get_db)):
    """Export lecture seule d'un programme au format xlsx (aucune ecriture en base)."""
    from datetime import date

    from openpyxl.utils import get_column_letter

    prog = db.get(Programme, programme_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programme not found")

    rows = (
        db.query(Lot, Batiment.nom, Client)
        .join(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Client, Client.id == Lot.client_id)
        .filter(Batiment.programme_id == programme_id)
        .all()
    )
    rows.sort(key=lambda r: (r[1] or "", _natural_sort_key(r[0].lot)))

    # Memes colonnes que la grille a l'ecran (+ Batiment, + dates).
    headers = [
        "Bâtiment", "N° lot", "Niveau", "Type", "Surface sol", "SHA m²",
        "Orientation", "Annexes", "Jardin", "Terrasse",
        "Prix logement", "Prix stationnement", "Prix total",
        "Prix/m² appart", "Prix/m² stationnement inclus", "Statut",
        "Date option", "Date réservation", "Date acte", "Acquéreur",
    ]
    price_columns = {11, 12, 13, 14, 15}  # Prix logement .. Prix/m² stationnement inclus (1-indexees)

    data_rows = []
    for lot, batiment_nom, client in rows:
        client_name = f"{client.last_name} {client.first_name}".strip() if client else None
        acquereur = client_name or lot.acquereur or ""
        data_rows.append([
            batiment_nom,
            lot.lot,
            lot.niveau,
            lot.type,
            lot.surface_sol,
            lot.sha_m2,
            lot.orientation,
            ", ".join(f"{a.type} {a.numero or ''}".strip() for a in lot.annexes),
            lot.jardin,
            lot.terrasse,
            lot.prix_logement,
            lot.prix_stationnement,
            lot.prix_total,
            lot.prix_m2_appartement,
            lot.prix_m2_appart_parking,
            lot.statut,
            lot.date_option,
            lot.date_reservation,
            lot.date_acte,
            acquereur,
        ])

    # Ligne de totaux en formules Excel (le client retouche ses fichiers).
    # Prix/m^2 = moyennes PONDEREES (somme des prix / somme des SHA), comme a
    # l'ecran : total / SHA totale de cette ligne redonne la moyenne.
    if data_rows:
        first, last = 2, len(data_rows) + 1
        col = lambda name: get_column_letter(headers.index(name) + 1)
        rng = lambda name: f"{col(name)}{first}:{col(name)}{last}"
        sha = f"SUM({rng('SHA m²')})"
        total = [""] * len(headers)
        total[0] = "Total programme"
        total[headers.index("N° lot")] = f"=COUNTA({rng('N° lot')})"
        for name in ("SHA m²", "Prix logement", "Prix stationnement", "Prix total"):
            total[headers.index(name)] = f"=SUM({rng(name)})"
        total[headers.index("Prix/m² appart")] = f"=IF({sha}>0,SUM({rng('Prix logement')})/{sha},\"\")"
        total[headers.index("Prix/m² stationnement inclus")] = f"=IF({sha}>0,SUM({rng('Prix total')})/{sha},\"\")"
        data_rows.append(total)

    filename = f"export_{_slugify(prog.nom)}_{date.today().isoformat()}.xlsx"
    return _build_xlsx_response(
        headers, data_rows, prog.nom or "Programme", filename, price_columns, bold_last_row=bool(data_rows)
    )


def _niveau_order(niveau: str | None) -> int:
    """Meme ordre que la grille a l'ecran : RDC, R+1, R+2..., puis le reste."""
    n = (niveau or "").strip().upper()
    if n == "RDC":
        return 0
    m = re.fullmatch(r"R\+(\d+)", n)
    return int(m.group(1)) if m else 999


def _lot_totals(lots: list[Lot]) -> dict:
    """Totaux d'une grille. Prix/m^2 = moyennes PONDEREES (somme des prix /
    somme des SHA), comme la grille a l'ecran et les formules de l'export Excel."""
    s = lambda f: sum(float(getattr(l, f) or 0) for l in lots)
    sha = s("sha_m2")
    return {
        "count": len(lots),
        "sha": sha,
        "prix_logement": s("prix_logement"),
        "prix_stationnement": s("prix_stationnement"),
        "prix_total": s("prix_total"),
        "m2_appart": s("prix_logement") / sha if sha > 0 else None,
        "m2_stat": s("prix_total") / sha if sha > 0 else None,
    }


@app.get("/programmes/{programme_id}/export-pdf")
def export_programme_pdf(programme_id: int, db: Session = Depends(get_db)):
    """Grille de prix complete d'un programme en PDF A4 paysage (lecture seule) :
    une section par batiment, sous-total par batiment s'il y en a plusieurs,
    ligne "Total programme" a la fin. Toujours la grille complete, sans filtre."""
    from datetime import date
    from io import BytesIO
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    prog = db.get(Programme, programme_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programme not found")

    rows = (
        db.query(Lot, Batiment.nom, Client)
        .join(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Client, Client.id == Lot.client_id)
        .filter(Batiment.programme_id == programme_id)
        .all()
    )
    rows.sort(key=lambda r: (_natural_sort_key(r[1]), _niveau_order(r[0].niveau), _natural_sort_key(r[0].lot)))
    by_bat: dict[str, list] = {}
    for lot, bat_nom, client in rows:
        by_bat.setdefault(bat_nom or "", []).append((lot, client))

    # --- mise en forme ---
    FONT = 7
    st_txt = ParagraphStyle("txt", fontName="Helvetica", fontSize=FONT, leading=FONT + 1.5)
    st_num = ParagraphStyle("num", parent=st_txt, alignment=2)  # a droite
    st_head = ParagraphStyle("head", parent=st_txt, fontName="Helvetica-Bold", fontSize=FONT - 1, leading=FONT)
    st_tot = ParagraphStyle("tot", parent=st_txt, fontName="Helvetica-Bold")
    st_tot_num = ParagraphStyle("totnum", parent=st_tot, alignment=2)

    def fr_num(v, decimals=0):
        if v in (None, ""):
            return "-"
        txt = f"{float(v):,.{decimals}f}".replace(",", " ").replace(".", ",")
        return txt

    def eur(v):
        return "-" if v in (None, "") else f"{fr_num(v)} €"

    def surf(v):
        # 2 decimales fixes : les virgules s'alignent en colonne a l'impression.
        return "-" if v in (None, "", 0) else fr_num(v, 2)

    def fr_date(v):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v or "")
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else "-"

    P = lambda text, style=st_txt: Paragraph(escape(str(text)), style)

    # (en-tete, largeur mm, numerique) : 277 mm = largeur utile A4 paysage.
    # En-tetes avec <br/> : ReportLab ne coupe que sur les espaces.
    columns = [
        ("Lot", 8, False), ("Niveau", 9, False), ("Type", 8, False),
        ("Surf.<br/>sol", 11, True), ("SHA m²", 13, True), ("Orient.", 9, False),
        ("Annexes", 28, False), ("Jardin", 10, True), ("Terrasse", 11, True),
        ("Prix<br/>logement", 18, True), ("Prix<br/>stationnement", 17.5, True), ("Prix total", 18, True),
        ("Prix/m²<br/>appart", 14, True), ("Prix/m²<br/>stationnement<br/>inclus", 17.5, True),
        ("Acquéreur(s)", 32, False), ("Statut", 11, False),
        ("Option", 14, False), ("Réservation", 14, False), ("Acte", 14, False),
    ]
    col_widths = [w * mm for _, w, _ in columns]
    header = [Paragraph(h, st_head) for h, _, _ in columns]
    STATUT_BG = {"Option": colors.HexColor("#dcfce7"), "Réservé": colors.HexColor("#fee2e2"), "Acté": colors.HexColor("#dbeafe")}

    def lot_row(lot, client):
        name = f"{client.last_name} {client.first_name}".strip() if client else (lot.acquereur or "")
        annexes = ", ".join(f"{a.type} {a.numero or ''}".strip() for a in lot.annexes) or "-"
        values = [
            lot.lot or "", lot.niveau or "", lot.type or "", surf(lot.surface_sol), surf(lot.sha_m2),
            lot.orientation or "", annexes, surf(lot.jardin), surf(lot.terrasse),
            eur(lot.prix_logement), eur(lot.prix_stationnement), eur(lot.prix_total),
            eur(lot.prix_m2_appartement), eur(lot.prix_m2_appart_parking),
            name or "-", lot.statut or "", fr_date(lot.date_option), fr_date(lot.date_reservation), fr_date(lot.date_acte),
        ]
        return [P(v, st_num if columns[i][2] else st_txt) for i, v in enumerate(values)]

    def total_row(label, t):
        row = [""] * len(columns)
        row[0] = P(label, st_tot)
        row[4] = P(surf(t["sha"]), st_tot_num)
        row[9] = P(eur(t["prix_logement"]), st_tot_num)
        row[10] = P(eur(t["prix_stationnement"]), st_tot_num)
        row[11] = P(eur(t["prix_total"]), st_tot_num)
        row[12] = P(eur(t["m2_appart"]), st_tot_num)
        row[13] = P(eur(t["m2_stat"]), st_tot_num)
        return row

    all_lots = [lot for lot, _, _ in rows]
    multi = len(by_bat) > 1
    story = []
    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=13, leading=16)
    sub_style = ParagraphStyle("sub", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#4b5563"))
    story.append(Paragraph(escape(f"Grille de prix — {prog.nom}"), title_style))
    infos = " · ".join(x for x in (prog.ville, f"{len(all_lots)} lots", f"édité le {date.today().strftime('%d/%m/%Y')}") if x)
    story.append(Paragraph(escape(infos), sub_style))
    story.append(Spacer(1, 3 * mm))

    bat_names = list(by_bat)
    for i, bat_nom in enumerate(bat_names):
        items = by_bat[bat_nom]
        data = [header] + [lot_row(lot, client) for lot, client in items]
        style = [
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9ca3af")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            # Colonnes texte qui suivent une colonne de nombres alignes a droite :
            # plus d'air pour ne pas lire "69,16 NE" ou "4 222 € KOCH" d'un bloc.
            ("LEFTPADDING", (5, 0), (5, -1), 4), ("LEFTPADDING", (14, 0), (14, -1), 4),
        ]
        for r, (lot, _) in enumerate(items, start=1):
            bg = STATUT_BG.get(lot.statut)
            if bg:
                style.append(("BACKGROUND", (0, r), (-1, r), bg))
        if multi:
            data.append(total_row(f"Total {bat_nom} ({len(items)} lot{'s' if len(items) > 1 else ''})", _lot_totals([l for l, _ in items])))
            style += [("SPAN", (0, len(data) - 1), (3, len(data) - 1)), ("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#f3f4f6"))]
        if i == len(bat_names) - 1:
            data.append(total_row(f"Total programme ({len(all_lots)} lot{'s' if len(all_lots) > 1 else ''})", _lot_totals(all_lots)))
            style += [
                ("SPAN", (0, len(data) - 1), (3, len(data) - 1)),
                ("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#d1d5db")),
                ("LINEABOVE", (0, len(data) - 1), (-1, len(data) - 1), 1, colors.black),
            ]
        story.append(Paragraph(escape(f"{bat_nom} — {len(items)} lot{'s' if len(items) > 1 else ''}"),
                               ParagraphStyle("bat", fontName="Helvetica-Bold", fontSize=9, leading=12, spaceBefore=2 * mm, spaceAfter=1 * mm)))
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle(style))
        story.append(table)

    if not rows:
        story.append(Paragraph("Aucun lot pour ce programme.", sub_style))

    # "page X / Y" : le total de pages n'est connu qu'a la fin.
    class NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self.setFont("Helvetica", 7)
                self.setFillColor(colors.HexColor("#6b7280"))
                self.drawString(10 * mm, 6 * mm, f"{prog.nom} — Grille de prix")
                self.drawRightString(landscape(A4)[0] - 10 * mm, 6 * mm, f"page {self._pageNumber} / {total}")
                super().showPage()
            super().save()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), leftMargin=10 * mm, rightMargin=10 * mm, topMargin=10 * mm, bottomMargin=12 * mm,
        title=f"Grille de prix — {prog.nom}",
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    filename = f"grille_{_slugify(prog.nom)}_{date.today().isoformat()}.pdf"
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


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
def _enrich_lot(lot: Lot, db: Session) -> dict:
    item = {k: v for k, v in lot.__dict__.items() if not k.startswith("_")}

    bat = db.get(Batiment, lot.batiment_id)
    prog = db.get(Programme, bat.programme_id) if bat else None
    item["programme_name"] = prog.nom if prog else None
    item["batiment_name"] = bat.nom if bat else None

    client = db.get(Client, lot.client_id) if lot.client_id else None
    if client:
        item["client_name"] = f"{client.last_name} {client.first_name}".strip()
    else:
        item["client_name"] = lot.acquereur

    item["annexes"] = lot.annexes

    return item
    
@app.get("/lots", response_model=list[LotRead])
def list_lots(
    programme_id: int | None = None,
    batiment_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(Lot, Programme.nom, Batiment.nom, Client)
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
    for lot, p_nom, b_nom, client in rows:
        # Convert ORM object to dict safe for Pydantic
        item = {k: v for k, v in lot.__dict__.items() if not k.startswith("_")}
        item["programme_name"] = p_nom
        item["batiment_name"] = b_nom
        
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
    return _enrich_lot(l, db)
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
    return _enrich_lot(l, db)


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
        "réservé": "reserve",
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
    counts = {"disponible": 0, "option": 0, "reserve": 0, "acte": 0}
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
        "date_option", "date_reservation", "date_acte",
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


# Import CSV (tableur client) : alias tolérés -> statut canonique. Clés en minuscules.
_CSV_STATUT_ALIASES = {
    "libre": "Libre",
    "disponible": "Libre",
    "option": "Option",
    "réservé": "Réservé",
    "réservation": "Réservé",
    "reserve": "Réservé",
    "reservation": "Réservé",
    "reservé": "Réservé",
    "reserv": "Réservé",
    "acté": "Acté",
    "acte": "Acté",
}


_CSV_DATE_FIELDS = ("date_option", "date_reservation", "date_acte")

# Import CSV : une cellule vide ne modifie jamais la valeur existante. Pour
# effacer volontairement un champ facultatif, le client ecrit ce marqueur.
_CSV_CLEAR = "#EFFACER"


def _is_csv_clear(value: str | None) -> bool:
    return (value or "").strip().upper() == _CSV_CLEAR


def _parse_csv_date(raw: str) -> str:
    """Date du tableur -> YYYY-MM-DD (format stocke). Accepte YYYY-MM-DD et
    JJ/MM/AAAA (format d'un export Excel francais), annee >= 1900 comme
    l'API. ValueError sinon."""
    from datetime import datetime

    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
        if parsed.year < LOT_DATE_MIN_YEAR:
            raise ValueError(raw)
        return parsed.isoformat()
    raise ValueError(raw)


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
        if _is_csv_clear(lot_num):
            errors.append({"ligne": line_num, "raison": f"{_CSV_CLEAR} interdit sur 'lot' (champ obligatoire)"})
            continue

        raw_statut = (row.get("statut") or "").strip()
        statut = None
        if _is_csv_clear(raw_statut):
            errors.append({"ligne": line_num, "raison": f"{_CSV_CLEAR} interdit sur 'statut' (champ obligatoire)"})
            continue
        if raw_statut:
            statut = _CSV_STATUT_ALIASES.get(unicodedata.normalize("NFC", raw_statut).lower())
            if statut is None:
                errors.append({"ligne": line_num, "raison": f"statut inconnu {raw_statut!r} (attendu : {', '.join(LOT_STATUTS)})"})
                continue

        # Dates : une cellule vide ne touche pas la date existante (un
        # re-import de grille sans dates ne doit rien effacer).
        dates = {}
        bad_date = None
        for k in _CSV_DATE_FIELDS:
            raw_date = (row.get(k) or "").strip()
            if _is_csv_clear(raw_date):
                dates[k] = None
            elif raw_date:
                try:
                    dates[k] = _parse_csv_date(raw_date)
                except ValueError:
                    bad_date = f"date invalide pour '{k}': {raw_date!r} (attendu : AAAA-MM-JJ ou JJ/MM/AAAA, à partir de {LOT_DATE_MIN_YEAR})"
                    break
        if bad_date:
            errors.append({"ligne": line_num, "raison": bad_date})
            continue

        if bat_nom not in by_name:
            new_bat = Batiment(nom=bat_nom, programme_id=programme_id)
            db.add(new_bat)
            db.flush()
            by_name[bat_nom] = new_bat
            print(f"[IMPORT] bâtiment créé: {bat_nom!r} (id={new_bat.id})")

        bat = by_name[bat_nom]

        payload = {}
        # Cellule absente ou vide : on ne touche pas la valeur existante
        # (avant, une cellule vide effacait la valeur, et un statut vide
        # faisait echouer tout l'import). #EFFACER : on vide le champ.
        for k in ("lot", "niveau", "type", "orientation", "acquereur"):
            if _is_csv_clear(row.get(k)):
                payload[k] = None
            elif (row.get(k) or "").strip():
                payload[k] = row[k]
        if statut:
            payload["statut"] = statut
        payload.update(dates)

        for k in ("surface_sol", "sha_m2", "jardin", "terrasse", "prix_logement", "prix_stationnement", "prix_total", "prix_m2_appartement", "prix_m2_appart_parking"):
            if _is_csv_clear(row.get(k)):
                payload[k] = None
            elif row.get(k) not in (None, ""):
                try:
                    payload[k] = float(row[k])
                except ValueError:
                    errors.append({"ligne": line_num, "raison": f"valeur numérique invalide pour '{k}': {row[k]!r}"})

        # Cases a cocher : cellule vide = on ne touche pas ; pour decocher, "Non".
        for k in ("garage", "parking1", "parking2", "cave"):
            v = (row.get(k) or "").strip().lower()
            if v:
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


def _format_prog_lot(items: list[tuple[str | None, str | None]]) -> tuple[str | None, str | None]:
    """Combine a client's (programme_name, lot_label) pairs into the two
    display fields of ClientRead. Single programme -> unchanged shape
    (programme_name + comma-joined lot labels). Several programmes -> fold
    everything into lot_label as "Programme / Lot" pairs."""
    if not items:
        return None, None
    programmes = {p for p, _ in items if p}
    if len(programmes) <= 1:
        programme_name = next(iter(programmes), None)
        lot_label = ", ".join(l for _, l in items if l) or None
        return programme_name, lot_label
    return None, ", ".join(f"{p} / {l}" for p, l in items if l)


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
            Programme.nom.label("programme_name"),
            Lot.id.label("lot_id"),
            Lot.lot.label("lot_label"),
        )
        .select_from(Client)
        .outerjoin(Lot, Lot.client_id == Client.id)
        .outerjoin(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Programme, Programme.id == Batiment.programme_id)
        .order_by(Client.id.desc())
        .all()
    )

    # Un client peut avoir plusieurs lots : on les agrege par client_id
    # (une ligne par client, pas une ligne par lot).
    base_by_client = {}
    lots_by_client: dict[int, list[tuple[str | None, str | None]]] = {}
    seen_lot_keys = set()
    for r in rows:
        base_by_client.setdefault(r.id, r)
        if r.lot_id and (r.id, r.lot_id) not in seen_lot_keys:
            seen_lot_keys.add((r.id, r.lot_id))
            lots_by_client.setdefault(r.id, []).append((r.programme_name, r.lot_label))

    # Rattachement additionnel par texte libre (lots.acquereur) quand le lot
    # n'a pas de client_id : ajoute au client trouve par nom/email plutot
    # que de creer une ligne supplementaire pour ce meme client.
    unmatched_lots = (
        db.query(Lot, Programme)
        .select_from(Lot)
        .outerjoin(Batiment, Batiment.id == Lot.batiment_id)
        .outerjoin(Programme, Programme.id == Batiment.programme_id)
        .filter(Lot.client_id.is_(None))
        .filter(Lot.acquereur.isnot(None))
        .all()
    )
    all_clients = list(base_by_client.values())
    for lot, prog in unmatched_lots:
        aq = (lot.acquereur or "").strip().lower()
        if not aq:
            continue
        for c in all_clients:
            name1 = f"{(c.last_name or '').strip()} {(c.first_name or '').strip()}".strip().lower()
            name2 = f"{(c.first_name or '').strip()} {(c.last_name or '').strip()}".strip().lower()
            email = (c.email or "").strip().lower()
            if (name1 and name1 in aq) or (name2 and name2 in aq) or (email and email == aq):
                if (c.id, lot.id) not in seen_lot_keys:
                    seen_lot_keys.add((c.id, lot.id))
                    lots_by_client.setdefault(c.id, []).append((getattr(prog, "nom", None), lot.lot))
                break

    # Lookup partner info (nom/prenom/email/tel) a embarquer sur la ligne du client.
    partner_ids = {r.partner_id for r in base_by_client.values() if r.partner_id}
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
                "address": p.address,
                "address2": p.address2,
                "partner_id": p.partner_id,
            }

    result = []
    for cid, r in sorted(base_by_client.items(), key=lambda kv: -kv[0]):
        # Un couple = 2 clients distincts, lies reciproquement : on n'affiche
        # qu'une seule ligne (celle du plus petit id) pour eviter d'afficher
        # deux lignes "A + B" / "B + A" pour le meme couple.
        if r.partner_id and r.partner_id in base_by_client and r.partner_id < cid:
            continue

        combined_lots = list(lots_by_client.get(cid, []))
        if r.partner_id:
            combined_lots += lots_by_client.get(r.partner_id, [])
        programme_name, lot_label = _format_prog_lot(combined_lots)

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
            "programme_id": None,
            "programme_name": programme_name,
            "lot_id": None,
            "lot_label": lot_label,
        })
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


def _link_partner(db: Session, c: Client, partner_payload: "ClientCreate") -> None:
    partner_data = partner_payload.model_dump(exclude_none=True, exclude={"partner"})
    raw_partner_type = (partner_data.get("type") or "prospect").strip().lower()
    if raw_partner_type not in ("prospect", "acquereur"):
        raw_partner_type = "prospect"
    partner_data["type"] = raw_partner_type

    # Si un conjoint est deja rattache, on le met a jour lui precisement
    # plutot que de relancer une recherche floue (find_or_create_client ne
    # retrouve pas un conjoint sans email ni telephone -> creerait un
    # doublon a chaque re-enregistrement, meme sans rien changer au formulaire).
    partner = db.get(Client, c.partner_id) if c.partner_id else None
    if partner is not None:
        for key, value in partner_data.items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            setattr(partner, key, value)
    else:
        partner = find_or_create_client(db, partner_data)

    c.partner_id = partner.id
    partner.partner_id = c.id


def _partner_read_dict(partner_obj: Client) -> dict:
    return {
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
        _link_partner(db, c, partner_payload)

    db.commit()
    db.refresh(c)
    result = _client_to_dict(c)
    if c.partner_id:
        partner_obj = db.get(Client, c.partner_id)
        if partner_obj:
            result["partner"] = _partner_read_dict(partner_obj)
    return result


@app.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(status_code=404, detail="Client not found")
    partner_payload = payload.partner
    data = payload.model_dump(exclude_none=True, exclude={"partner"})
    if "type" in data:
        raw_type = (data.get("type") or "prospect").strip().lower()
        data["type"] = raw_type if raw_type in ("prospect", "acquereur") else "prospect"
    for k, v in data.items():
        setattr(c, k, v)

    if partner_payload is not None:
        _link_partner(db, c, partner_payload)

    db.add(c)
    db.commit()
    db.refresh(c)
    result = _client_to_dict(c)
    if c.partner_id:
        partner_obj = db.get(Client, c.partner_id)
        if partner_obj:
            result["partner"] = _partner_read_dict(partner_obj)
    return result


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


@app.get("/clients/export")
def export_clients_xlsx(db: Session = Depends(get_db)):
    """Export lecture seule de la base clients au format xlsx (aucune ecriture en base).
    Un client par ligne (contrairement a GET /clients, qui joint les lots et
    duplique une ligne par lot rattache)."""
    from datetime import date

    clients = db.query(Client).order_by(Client.last_name.asc(), Client.first_name.asc()).all()
    by_id = {c.id: c for c in clients}

    headers = [
        "Civilité", "Nom", "Prénom", "Email 1", "Email 2", "Tél 1", "Tél 2",
        "Adresse", "Code postal", "Ville", "Type", "Conjoint",
    ]

    data_rows = []
    for c in clients:
        partner = by_id.get(c.partner_id) if c.partner_id else None
        conjoint = f"{partner.last_name} {partner.first_name}".strip() if partner else ""
        data_rows.append([
            c.civility,
            c.last_name,
            c.first_name,
            c.email,
            c.email2,
            c.phone,
            c.phone2,
            c.address,
            None,  # pas de colonne code postal separee en base
            None,  # pas de colonne ville separee en base
            c.type,
            conjoint,
        ])

    filename = f"export_clients_{date.today().isoformat()}.xlsx"
    return _build_xlsx_response(headers, data_rows, "Clients", filename)


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
