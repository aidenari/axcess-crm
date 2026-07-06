"""
One-shot migration script for the "dossier acquereur" feature.
Run once: python migrate_dossiers.py

Creates (idempotently):
  - dossier_acquereur table
  - annexes table
  - clients.dossier_id column (FK -> dossier_acquereur.id, ON DELETE SET NULL)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.core.database import engine

migrations = [
    """
    CREATE TABLE IF NOT EXISTS dossier_acquereur (
        id SERIAL PRIMARY KEY,
        type VARCHAR(10) NOT NULL DEFAULT 'solo',
        lot_id INTEGER NULL REFERENCES lots(id) ON DELETE SET NULL,
        programme_id INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
        created_at TIMESTAMP NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_dossier_acquereur_lot_id ON dossier_acquereur (lot_id)",
    "CREATE INDEX IF NOT EXISTS ix_dossier_acquereur_programme_id ON dossier_acquereur (programme_id)",
    """
    CREATE TABLE IF NOT EXISTS annexes (
        id SERIAL PRIMARY KEY,
        lot_id INTEGER NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        numero VARCHAR(50) NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_annexes_lot_id ON annexes (lot_id)",
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS dossier_id INTEGER NULL REFERENCES dossier_acquereur(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_clients_dossier_id ON clients (dossier_id)",
]

with engine.connect() as conn:
    for sql in migrations:
        conn.execute(text(sql.strip()))
    conn.commit()
    print("Migration dossiers OK")
