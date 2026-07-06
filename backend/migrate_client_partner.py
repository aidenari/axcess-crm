"""
One-shot migration script for the client "partner" (couple) feature.
Run once: python migrate_client_partner.py

Creates (idempotently):
  - clients.partner_id column (self-referencing FK -> clients.id, ON DELETE SET NULL)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.core.database import engine

migrations = [
    "ALTER TABLE clients ADD COLUMN IF NOT EXISTS partner_id INTEGER NULL REFERENCES clients(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_clients_partner_id ON clients (partner_id)",
]

with engine.connect() as conn:
    for sql in migrations:
        conn.execute(text(sql.strip()))
    conn.commit()
    print("Migration client partner OK")
