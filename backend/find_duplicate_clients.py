"""
Read-only report: find groups of clients sharing the same (non-empty) email.
Does not write anything to the database.

Run: python find_duplicate_clients.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict

from backend.core.database import SessionLocal
from backend.models import Client


def main() -> None:
    db = SessionLocal()
    try:
        clients = (
            db.query(Client)
            .filter(Client.email.isnot(None))
            .filter(Client.email != "")
            .order_by(Client.email.asc(), Client.id.asc())
            .all()
        )

        groups: dict[str, list[Client]] = defaultdict(list)
        for c in clients:
            key = c.email.strip().lower()
            if key:
                groups[key].append(c)

        duplicate_groups = {email: rows for email, rows in groups.items() if len(rows) > 1}

        if not duplicate_groups:
            print("Aucun doublon de client trouve (par email).")
            return

        print(f"{len(duplicate_groups)} groupe(s) de doublons trouve(s):\n")
        for email, rows in duplicate_groups.items():
            print(f"Email: {email}  ({len(rows)} clients)")
            for c in rows:
                print(f"  - id={c.id} last_name={c.last_name!r} first_name={c.first_name!r} dossier_id={c.dossier_id}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main()
