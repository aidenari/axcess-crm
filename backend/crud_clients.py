from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import Client


def find_or_create_client(db: Session, data: dict) -> Client:
    """Find an existing client matching `data` and update it, or create a new one.

    Dedup strategy (fixes duplicate-client bug from the old codebase, where
    _make_client / create_client always inserted a new row):
      1. If an email is provided, look up an existing client by email
         (case-insensitive). If found, update only the non-empty/non-None
         fields from `data` (never overwrite an existing value with blank/None).
      2. If no email is provided, fall back to matching on
         (last_name, first_name, phone) when a phone is provided.
      3. Otherwise (no email, no phone) there is no reliable identifier —
         always create a new client.
    """
    email = (data.get("email") or "").strip()
    existing: Client | None = None

    if email:
        existing = (
            db.query(Client)
            .filter(func.lower(Client.email) == email.lower())
            .first()
        )
    else:
        last_name = (data.get("last_name") or "").strip()
        first_name = (data.get("first_name") or "").strip()
        phone = (data.get("phone") or "").strip()
        if phone and last_name and first_name:
            existing = (
                db.query(Client)
                .filter(
                    func.lower(Client.last_name) == last_name.lower(),
                    func.lower(Client.first_name) == first_name.lower(),
                    Client.phone == phone,
                )
                .first()
            )

    if existing is not None:
        # Only apply non-empty/non-None payload fields, so we never
        # overwrite an existing value with a blank one.
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            setattr(existing, key, value)
        db.flush()
        return existing

    new_client = Client(**data)
    db.add(new_client)
    db.flush()
    return new_client
