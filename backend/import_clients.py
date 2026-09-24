"""Import de la base clients Excel de Nicolas (BDD_CLIENT.xlsx) vers Axcess CRM.

Script autonome, lecture seule par defaut (dry-run). N'ecrit en base que si
--commit est passe explicitement.

Usage (depuis le conteneur backend, WORKDIR=/app) :
    python backend/import_clients.py                # dry-run (defaut), affiche le rapport
    python backend/import_clients.py --dry-run       # equivalent explicite
    python backend/import_clients.py --commit        # ecrit reellement en base
    python backend/import_clients.py --file /tmp/autre.xlsx --commit

Regles de mapping et de gestion : voir le rapport genere, qui explique pour
chaque ligne la decision prise. Resume :
  - Programme Excel -> programme CRM par correspondance normalisee, avec 3
    regles explicites (LES GRIOZS - GRIES -> LES GRIOZS, INNOVA - WEITBRUCH
    -> INNOVA, LE PARADISIO - GRIESHEIM-SUR-SOUFFEL -> PARADISIO 1 ou 2
    selon le batiment). Aucun programme non reconnu n'est invente.
  - Batiment / lot matches par comparaison normalisee (accents/casse
    ignores, prefixe BAT/BATIMENT ignore).
  - Un lot dont client_id est deja renseigne n'est JAMAIS modifie.
  - Client dedupliqué par email (Mail 1) sinon par nom+prenom normalises.
    Aucun champ d'un client existant n'est ecrase : on ne fait que le
    rattacher (poser client_id sur le lot). Seuls les nouveaux clients sont
    remplis avec les donnees Excel.
  - Lignes multi-personnes (NOM contenant "et", ",", "&", " - " ou une
    annotation entre parentheses) : pas de parsing fin, le NOM brut devient
    un client unique, et la ligne est loggee pour completion manuelle.
  - Statut Excel normalise via _normalize_lot_status (backend.main) puis
    reconverti vers la convention d'affichage de la base (Libre / Option /
    Réservé / Acté).
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import openpyxl

from backend.core.database import SessionLocal
from backend.main import _normalize_lot_status
from backend.models import Batiment, Client, Lot, Programme

SHEET_NAME = "Feuil1"
DEFAULT_EXCEL_PATH = "/tmp/BDD_CLIENT.xlsx"

COLUMNS = [
    "programme", "civilite", "civilite_complete", "batiment", "n_lot", "nom",
    "mail1", "mail2", "tel1", "tel2", "rue", "code_postal", "ville",
    "statut", "date_resa", "date_acte",
]

STATUT_DISPLAY = {
    "libre": "Libre",
    "option": "Option",
    "reserve": "Réservé",
    "acte": "Acté",
    "transit": "Réservé",  # pas de statut dedie dans l'UI, regroupe avec reserve
}

MULTI_PERSON_RE = re.compile(r"(?:\bET\b|,|&|\s-|-\s|\([^)]*\))", re.IGNORECASE)


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(value) -> str:
    """Normalise pour comparaison : accents et casse ignores, espaces reduits."""
    if value is None:
        return ""
    s = _strip_accents(str(value)).upper()
    return re.sub(r"\s+", " ", s).strip()


def batiment_key(value) -> str:
    s = norm(value)
    return re.sub(r"^(BATIMENT|BAT)\s*", "", s).strip()


# --------------------------------------------------------------------------
# Resolution Programme (regles impératives)
# --------------------------------------------------------------------------

def resolve_programme_key(excel_programme: str, excel_batiment: str) -> str | None:
    p = norm(excel_programme)
    if p == norm("LES GRIOZS - GRIES"):
        return "LES GRIOZS"
    if p == norm("INNOVA - WEITBRUCH"):
        return "INNOVA"
    if p == norm("LE PARADISIO - GRIESHEIM-SUR-SOUFFEL"):
        letter = batiment_key(excel_batiment)
        if letter == "A":
            return "PARADISIO 1"
        if letter == "B":
            return "PARADISIO 2"
        return None
    return None  # programme non reconnu, on n'invente rien


# --------------------------------------------------------------------------
# Parsing du champ NOM
# --------------------------------------------------------------------------

def is_multi_person(nom: str) -> bool:
    return bool(MULTI_PERSON_RE.search(nom))


def split_single_person_name(nom: str) -> tuple[str, str]:
    """'SCHAUINGER  Romuald' -> ('SCHAUINGER', 'Romuald').
    Convention observee dans le fichier : le(s) token(s) en MAJUSCULES en
    tete de chaine forment le nom de famille, le reste le prenom."""
    tokens = nom.split()
    i = 0
    while i < len(tokens) and tokens[i].isupper():
        i += 1
    if i == 0:
        i = 1  # toujours au moins un token pour le nom
    last = " ".join(tokens[:i])
    first = " ".join(tokens[i:])
    return last, first


def excel_date_to_str(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    s = str(value).strip()
    return s or None


def _fit(value: str | None, maxlen: int) -> str | None:
    """Troncature defensive a la limite de colonne (filet de securite ;
    aucune colonne du fichier source ne devrait normalement l'atteindre)."""
    if value is None:
        return None
    value = str(value)
    return value[:maxlen] if len(value) > maxlen else value


def build_address(rue, code_postal, ville) -> str | None:
    parts = []
    if rue:
        parts.append(str(rue).strip())
    if code_postal not in (None, ""):
        parts.append(str(code_postal).strip())
    if ville:
        parts.append(str(ville).strip())
    joined = " ".join(p for p in parts if p)
    return joined or None


# --------------------------------------------------------------------------
# Lecture du fichier Excel
# --------------------------------------------------------------------------

def read_rows(path: str) -> tuple[list[dict], int]:
    """Retourne (lignes utilisables, nb de lignes vides ignorees)."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[SHEET_NAME]
    raw_rows = list(ws.iter_rows(values_only=True))
    rows = []
    blank = 0
    for raw in raw_rows[1:]:
        if all(v is None for v in raw):
            blank += 1
            continue
        row = dict(zip(COLUMNS, raw))
        if row.get("programme") is None:
            blank += 1
            continue
        rows.append(row)
    return rows, blank


# --------------------------------------------------------------------------
# Placeholder pour simuler une creation de client en dry-run
# --------------------------------------------------------------------------

class _PendingClient:
    """Represente un client 'a creer' pas encore en base (dry-run) ou deja
    ajoute a la session mais pas commit (--commit). Permet de faire matcher
    entre elles plusieurs lignes du fichier qui referencent la meme personne
    (idempotence intra-fichier), sans dupliquer le code de resolution."""

    def __init__(self, seq: int, last_name: str, first_name: str, email: str | None):
        self.id = f"NOUVEAU#{seq}"
        self.last_name = last_name
        self.first_name = first_name
        self.email = email


class ClientIndex:
    """Index des clients existants + nouvellement decides pendant l'import,
    pour dedupliquer par email puis par nom+prenom normalises."""

    def __init__(self, db):
        self.by_email: dict[str, object] = {}
        self.by_name: dict[tuple[str, str], object] = {}
        self._seq = 0
        for c in db.query(Client).all():
            self._register(c)

    def _register(self, client) -> None:
        if client.email:
            self.by_email.setdefault(norm(client.email), client)
        self.by_name.setdefault((norm(client.last_name), norm(client.first_name)), client)

    def resolve(self, email: str | None, last_name: str, first_name: str):
        """Retourne (client_existant, critere) si trouve — critere vaut
        "email" ou "nom+prenom" selon ce qui a matche — ou (None, None) si
        aucune correspondance (il faudra creer)."""
        if email:
            existing = self.by_email.get(norm(email))
            if existing is not None:
                return existing, "email"
        existing = self.by_name.get((norm(last_name), norm(first_name)))
        if existing is not None:
            return existing, "nom+prenom"
        return None, None

    def register_new(self, last_name: str, first_name: str, email: str | None):
        self._seq += 1
        placeholder = _PendingClient(self._seq, last_name, first_name, email)
        self._register(placeholder)
        return placeholder

    def register_real(self, client) -> None:
        self._register(client)


# --------------------------------------------------------------------------
# Import principal
# --------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.total_lignes = 0
        self.lignes_vides = 0
        self.programmes_non_resolus: list[dict] = []
        self.lots_non_trouves: dict[str, list[dict]] = {}
        self.lots_matches: dict[str, int] = {}
        self.clients_a_creer: list[dict] = []
        self.clients_a_rattacher: list[dict] = []
        self.conflits_client_deja_rattache: list[dict] = []
        self.multi_personnes: list[dict] = []
        self.maj_statut_dates: list[dict] = []

    def print_report(self, dry_run: bool):
        mode = "DRY-RUN (aucune ecriture)" if dry_run else "COMMIT (ecriture en base)"
        print("=" * 78)
        print(f"IMPORT BDD_CLIENT.xlsx — {mode}")
        print("=" * 78)
        print(f"Lignes lues (hors entete, hors lignes vides) : {self.total_lignes}")
        print(f"Lignes vides ignorees : {self.lignes_vides}")

        print()
        print("--- Programmes non resolus (aucune correspondance CRM) ---")
        if not self.programmes_non_resolus:
            print("  (aucun)")
        for p in self.programmes_non_resolus:
            print(f"  ligne {p['ligne']} : programme={p['programme']!r} batiment={p['batiment']!r} lot={p['n_lot']!r}")

        print()
        print("--- Lots par programme : matches / non trouves ---")
        all_progs = sorted(set(self.lots_matches) | set(self.lots_non_trouves))
        for prog in all_progs:
            ok = self.lots_matches.get(prog, 0)
            ko = self.lots_non_trouves.get(prog, [])
            print(f"  {prog} : {ok} matches, {len(ko)} non trouves")
            for item in ko:
                print(f"      non trouve -> bat={item['batiment']!r} lot={item['n_lot']!r} (ligne {item['ligne']})")

        print()
        print(f"--- Clients a creer ({len(self.clients_a_creer)}) ---")
        for c in self.clients_a_creer:
            print(f"  ligne {c['ligne']} : {c['last_name']} {c['first_name']} "
                  f"(email={c['email'] or '-'}) -> CREERAIT un nouveau client")

        print()
        print(f"--- Clients a rattacher (dedup, {len(self.clients_a_rattacher)}) ---")
        for c in self.clients_a_rattacher:
            print(f"  ligne {c['ligne']} : {c['last_name']} {c['first_name']} "
                  f"(critere={c['critere']}) -> RATTACHERAIT au client id={c['client_id']}")

        print()
        print(f"--- Lots deja rattaches a un client : NON TOUCHES ({len(self.conflits_client_deja_rattache)}) ---")
        for c in self.conflits_client_deja_rattache:
            print(f"  ligne {c['ligne']} : {c['programme']} / {c['batiment']} / lot {c['n_lot']} "
                  f"deja rattache a client id={c['client_id_existant']} ({c['nom_existant']}) "
                  f"— Excel proposait {c['nom_excel']!r}")

        print()
        print(f"--- Lignes multi-personnes a completer manuellement ({len(self.multi_personnes)}) ---")
        for m in self.multi_personnes:
            print(f"  ligne {m['ligne']} : {m['programme']} / {m['batiment']} / lot {m['n_lot']} "
                  f"— NOM brut = {m['nom']!r}")
            print(f"      mail1={m['mail1']!r} mail2={m['mail2']!r} tel1={m['tel1']!r} "
                  f"tel2={m['tel2']!r} rue={m['rue']!r}")

        print()
        print(f"--- Mises a jour statut/dates prevues ({len(self.maj_statut_dates)}) ---")
        for u in self.maj_statut_dates:
            print(f"  ligne {u['ligne']} : {u['programme']} / {u['batiment']} / lot {u['n_lot']} "
                  f"statut {u['statut_avant']!r} -> {u['statut_apres']!r}, "
                  f"resa {u['date_resa_avant']!r} -> {u['date_resa_apres']!r}, "
                  f"acte {u['date_acte_avant']!r} -> {u['date_acte_apres']!r}"
                  f"{'  [+ client ' + str(u['client_action']) + ']' if u['client_action'] else ''}")

        print()
        print("=" * 78)
        print(f"Resume : {sum(self.lots_matches.values())} lots matches, "
              f"{sum(len(v) for v in self.lots_non_trouves.values())} non trouves, "
              f"{len(self.clients_a_creer)} clients a creer, "
              f"{len(self.clients_a_rattacher)} a rattacher, "
              f"{len(self.conflits_client_deja_rattache)} conflits (non touches), "
              f"{len(self.multi_personnes)} lignes a completer manuellement, "
              f"{len(self.maj_statut_dates)} maj statut/dates.")
        print("=" * 78)


def run_import(excel_path: str, dry_run: bool) -> Report:
    report = Report()
    rows, blank = read_rows(excel_path)
    report.total_lignes = len(rows)
    report.lignes_vides = blank

    db = SessionLocal()
    try:
        # Index programmes / batiments / lots existants
        programmes_by_name = {norm(p.nom): p for p in db.query(Programme).all()}
        batiments_by_programme: dict[int, dict[str, Batiment]] = {}
        for b in db.query(Batiment).all():
            batiments_by_programme.setdefault(b.programme_id, {})[batiment_key(b.nom)] = b

        lots_by_batiment: dict[int, dict[str, Lot]] = {}
        for l in db.query(Lot).all():
            lots_by_batiment.setdefault(l.batiment_id, {})[norm(l.lot)] = l

        client_index = ClientIndex(db)

        for i, row in enumerate(rows, start=2):  # ligne Excel reelle (entete = ligne 1)
            programme_key = resolve_programme_key(row["programme"], row["batiment"])
            if programme_key is None:
                report.programmes_non_resolus.append({
                    "ligne": i, "programme": row["programme"],
                    "batiment": row["batiment"], "n_lot": row["n_lot"],
                })
                continue

            prog = programmes_by_name.get(norm(programme_key))
            if prog is None:
                # programme cible connu par nos regles mais absent de la base
                report.programmes_non_resolus.append({
                    "ligne": i, "programme": f"{row['programme']} (-> {programme_key})",
                    "batiment": row["batiment"], "n_lot": row["n_lot"],
                })
                continue

            bat = batiments_by_programme.get(prog.id, {}).get(batiment_key(row["batiment"]))
            lot = None
            if bat is not None:
                lot = lots_by_batiment.get(bat.id, {}).get(norm(row["n_lot"]))

            if lot is None:
                report.lots_non_trouves.setdefault(programme_key, []).append({
                    "ligne": i, "batiment": row["batiment"], "n_lot": row["n_lot"],
                })
                continue

            report.lots_matches[programme_key] = report.lots_matches.get(programme_key, 0) + 1

            # Lot deja rattache a un client : on ne touche a RIEN sur ce lot.
            if lot.client_id is not None:
                existing_client = db.get(Client, lot.client_id)
                nom_existant = (
                    f"{existing_client.last_name} {existing_client.first_name}".strip()
                    if existing_client else "?"
                )
                report.conflits_client_deja_rattache.append({
                    "ligne": i, "programme": programme_key, "batiment": row["batiment"],
                    "n_lot": row["n_lot"], "client_id_existant": lot.client_id,
                    "nom_existant": nom_existant, "nom_excel": row["nom"],
                })
                continue

            nom = (row["nom"] or "").strip()
            client_action = None

            if nom:
                multi = is_multi_person(nom)
                if multi:
                    report.multi_personnes.append({
                        "ligne": i, "programme": programme_key, "batiment": row["batiment"],
                        "n_lot": row["n_lot"], "nom": nom,
                        "mail1": row["mail1"], "mail2": row["mail2"],
                        "tel1": row["tel1"], "tel2": row["tel2"], "rue": row["rue"],
                    })
                    last_name, first_name = nom, ""
                    # Champs contact non fiables sur une ligne multi-personnes
                    # (valeurs multiples dans une seule cellule : depassent les
                    # limites de colonne et/ou ne sont pas un email valide).
                    # On laisse vide, le detail brut est dans le rapport
                    # ci-dessus pour que Nicolas complete a la main.
                    email = email2 = phone = phone2 = address = None
                else:
                    last_name, first_name = split_single_person_name(nom)
                    email = (row["mail1"] or "").strip() or None
                    email2 = (row["mail2"] or None)
                    phone = (row["tel1"] or None)
                    phone2 = (row["tel2"] or None)
                    address = build_address(row["rue"], row["code_postal"], row["ville"])

                last_name = _fit(last_name, 100)
                first_name = _fit(first_name, 100)

                existing, critere = client_index.resolve(email, last_name, first_name)

                if existing is None:
                    report.clients_a_creer.append({
                        "ligne": i, "last_name": last_name, "first_name": first_name,
                        "email": email, "critere": "email" if email else "nom+prenom",
                    })
                    if dry_run:
                        pending = client_index.register_new(last_name, first_name, email)
                        client_action = f"creation ({pending.id})"
                        new_client_id = pending.id
                    else:
                        new_client = Client(
                            civility=_fit(row["civilite"] or None, 20),
                            type="acquereur",
                            last_name=last_name,
                            first_name=first_name,
                            address=_fit(address, 255),
                            phone=_fit(phone, 50),
                            phone2=_fit(phone2, 50),
                            email=_fit(email, 255),
                            email2=_fit(email2, 255),
                        )
                        db.add(new_client)
                        db.flush()  # obtient l'id sans committer la transaction
                        client_index.register_real(new_client)
                        client_action = "creation"
                        new_client_id = new_client.id
                else:
                    report.clients_a_rattacher.append({
                        "ligne": i, "last_name": last_name, "first_name": first_name,
                        "critere": critere, "client_id": existing.id,
                    })
                    client_action = f"rattachement id={existing.id}"
                    new_client_id = existing.id

                if not dry_run:
                    lot.client_id = new_client_id

            # Statut / dates : mis a jour dans tous les cas (avec ou sans NOM),
            # tant que le lot n'a pas deja de client (deja filtre ci-dessus).
            statut_apres = excel_statut_to_display_or_none(row["statut"])
            date_resa_apres = excel_date_to_str(row["date_resa"])
            date_acte_apres = excel_date_to_str(row["date_acte"])
            statut_change = bool(statut_apres) and statut_apres != lot.statut
            resa_change = date_resa_apres != lot.date_reservation
            acte_change = date_acte_apres != lot.date_acte

            if client_action or statut_change or resa_change or acte_change:
                report.maj_statut_dates.append({
                    "ligne": i, "programme": programme_key, "batiment": row["batiment"],
                    "n_lot": row["n_lot"],
                    "statut_avant": lot.statut, "statut_apres": statut_apres or lot.statut,
                    "date_resa_avant": lot.date_reservation, "date_resa_apres": date_resa_apres,
                    "date_acte_avant": lot.date_acte, "date_acte_apres": date_acte_apres,
                    "client_action": client_action,
                })

            if not dry_run:
                if statut_apres:
                    lot.statut = statut_apres
                lot.date_reservation = date_resa_apres
                lot.date_acte = date_acte_apres

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return report


def excel_statut_to_display_or_none(raw) -> str | None:
    if raw is None or str(raw).strip() == "":
        return None
    key = _normalize_lot_status(str(raw))
    return STATUT_DISPLAY.get(key, str(raw).strip().capitalize())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", default=DEFAULT_EXCEL_PATH, help="Chemin du fichier xlsx source")
    parser.add_argument("--dry-run", action="store_true", help="Simulation seule (defaut)")
    parser.add_argument("--commit", action="store_true", help="Ecrit reellement en base")
    args = parser.parse_args()

    dry_run = not args.commit

    report = run_import(args.file, dry_run)
    report.print_report(dry_run)


if __name__ == "__main__":
    main()
