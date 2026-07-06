"""
One-shot migration script.
Run once: python migrate.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.core.database import engine

migrations = [
    # Evolution 1 — dates lot
    "ALTER TABLE lots ADD COLUMN IF NOT EXISTS date_reservation VARCHAR(20)",
    "ALTER TABLE lots ADD COLUMN IF NOT EXISTS date_acte        VARCHAR(20)",
    # Evolution 2 — multi-acquéreurs
    """
    CREATE TABLE IF NOT EXISTS lot_clients (
        lot_id    INTEGER NOT NULL REFERENCES lots(id)    ON DELETE CASCADE,
        client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        PRIMARY KEY (lot_id, client_id)
    )
    """,
]

with engine.connect() as conn:
    for sql in migrations:
        conn.execute(text(sql.strip()))
    conn.commit()
    print("Migration OK")
