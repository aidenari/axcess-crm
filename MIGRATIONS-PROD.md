# Migrations à rejouer en production

Le projet n'utilise pas d'outil de migration (Alembic ou autre). Ce fichier liste, dans l'ordre, les opérations SQL à exécuter à la main sur la base de production le jour du déploiement.

Connexion : `docker compose exec db psql -U axcess_user -d axcess_crm`

Pour chaque opération : l'exécuter dans une transaction, vérifier que le résultat obtenu correspond au résultat attendu avant `COMMIT`, sinon `ROLLBACK`.

---

## Contraintes de déploiement hors SQL

Étapes à faire le jour J en plus des migrations SQL ci-dessous.

### D1 — Reconstruire l'image backend (nouvelle dépendance ReportLab)

- **Date** : 2026-09-24
- **Raison** : l'export PDF des grilles de prix (`GET /programmes/{id}/export-pdf`) utilise **ReportLab**, ajouté à `backend/requirements.txt` (`reportlab==5.0.1`, qui installe aussi `pillow` et `charset-normalizer`). L'image backend actuelle ne la contient pas : sans reconstruction, l'export PDF renvoie une erreur 500 (`ModuleNotFoundError: reportlab`). Le reste de l'application n'est pas affecté.
- **Commande** (depuis la racine du projet sur le serveur) :
  ```
  docker compose build backend
  docker compose up -d backend
  ```
  `up -d` sans `--build` réutiliserait l'ancienne image : bien lancer le `build` d'abord.
- **Contrôle** : `docker compose exec backend python -c "import reportlab; print(reportlab.Version)"` doit afficher `5.0.1`, puis télécharger un PDF depuis une grille de prix.
- **Réseau** : le build télécharge les paquets depuis PyPI ; le serveur doit avoir un accès sortant ce jour-là.

---

## 001 — Statut du lot A22 (INNOVA) : `DISPONIBLE` → `Libre`

- **Date** : 2026-09-24
- **Branche** : `corrections-septembre-2026`
- **Raison** : le lot A22 du programme INNOVA (id 111) est le seul des 109 lots dont le statut n'est pas canonique (`DISPONIBLE` en majuscules, probablement issu d'un import CSV). Les endpoints `POST /lots` et `PUT /lots/{id}` n'acceptent désormais que `Libre`, `Option`, `Réservé` ou `Acté`. Sans cette correction, toute modification de ce lot depuis la fenêtre d'édition échouerait (erreur 422), car le formulaire renvoie le statut existant.

**Vérification préalable** (attendu : 1 ligne, `A22 | DISPONIBLE`) :
```sql
SELECT id, lot, statut FROM lots WHERE id = 111;
```

**Requête** :
```sql
BEGIN;
UPDATE lots SET statut = 'Libre' WHERE id = 111 AND statut = 'DISPONIBLE';
COMMIT;
```

**Résultat attendu** : `UPDATE 1`

**Contrôle après coup** (attendu : aucune ligne) :
```sql
SELECT id, lot, statut FROM lots WHERE statut NOT IN ('Libre', 'Option', 'Réservé', 'Acté') OR statut IS NULL;
```

---

## 002 — Nouvelle colonne `lots.date_option`

- **Date** : 2026-09-24
- **Branche** : `corrections-septembre-2026`
- **Raison** : le client veut saisir une date de mise en option, comme pour la réservation et l'acte. Même type que `date_reservation` et `date_acte` : `VARCHAR(20)`, nullable, format `YYYY-MM-DD`.
- **⚠️ Ordre impératif** : exécuter cette migration **AVANT** de déployer le nouveau code backend. Le modèle SQLAlchemy lit `lots.date_option` : si le code est déployé sans la colonne, tous les endpoints qui lisent des lots (grilles, liste des lots, dashboard, clients, exports) renvoient une erreur 500. L'inverse est sans danger : l'ancien code ignore la colonne.
- **Idempotente** : `IF NOT EXISTS`, la rejouer ne fait rien (PostgreSQL affiche un `NOTICE ... already exists, skipping`).

**Requête** :
```sql
BEGIN;
ALTER TABLE lots ADD COLUMN IF NOT EXISTS date_option VARCHAR(20);
COMMIT;
```

**Résultat attendu** : `ALTER TABLE` (au premier passage comme aux suivants).

**Contrôle après coup** (attendu : 1 ligne, `date_option | character varying | 20 | YES`) :
```sql
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'lots' AND column_name = 'date_option';
```

**Retour arrière** (uniquement si le code qui l'utilise est retiré, supprime les dates saisies) :
```sql
ALTER TABLE lots DROP COLUMN IF EXISTS date_option;
```

---

## 003 — Date de réservation invalide du lot A01 (PARADISIO 1)

- **Date** : 2026-09-24 — validée ; exécutée en local le 2026-09-24 (`UPDATE 1`, contrôle après coup vide).
- **⚠️ Ordre** : à rejouer **avant** ou en même temps que le déploiement du code. Le backend refuse désormais les dates antérieures à 1900 : tant que A01 garde `0001-01-01`, toute modification de ce lot depuis la fenêtre d'édition échoue (erreur 422), car le formulaire renvoie la date existante.
- **Branche** : `corrections-septembre-2026`
- **Raison** : le lot A01 de PARADISIO 1 (id 115, statut `Libre`) a `date_reservation = '0001-01-01'`, affichée « 01/01/0001 » dans la grille. C'est la seule date de ce type dans la base, et aucun code ne l'écrit : elle provient très probablement d'une saisie de zéros dans le champ date du navigateur, en voulant « remettre à zéro » la date. Le client souhaite que cette date soit vide.

**Vérification préalable** (attendu : 1 ligne, `A01 | Libre | 0001-01-01`) :
```sql
SELECT l.id, l.lot, l.statut, l.date_reservation
FROM lots l JOIN batiments b ON b.id = l.batiment_id JOIN programmes p ON p.id = b.programme_id
WHERE l.id = 115 AND p.nom = 'PARADISIO 1';
```

**Requête** :
```sql
BEGIN;
UPDATE lots SET date_reservation = NULL WHERE id = 115 AND date_reservation = '0001-01-01';
COMMIT;
```

**Résultat attendu** : `UPDATE 1`

**Contrôle après coup** (attendu : aucune ligne — aucune date antérieure à 1900 dans les trois colonnes) :
```sql
SELECT id, lot, date_option, date_reservation, date_acte FROM lots
WHERE date_option < '1900' OR date_reservation < '1900' OR date_acte < '1900';
```

---

## 004 — Adresse des conjoints : copie de l'adresse du titulaire

- **Date** : 2026-09-24 — exécutée en local le 2026-09-24 (`UPDATE 9`).
- **Branche** : `corrections-septembre-2026`
- **Raison** : le formulaire client n'avait pas de champ adresse pour le conjoint. Dans un couple, seul le titulaire (la fiche affichée dans la liste des clients, identifiant le plus petit) avait donc une adresse : 9 conjoints n'en avaient pas. Le formulaire propose désormais « Même adresse que le titulaire » ; cette opération complète les conjoints existants.
- **Gardes** : ne modifie que le conjoint d'un couple lié dans les deux sens, **uniquement si son adresse est NULL, vide ou faite d'espaces**, et seulement si le titulaire en a une. `address2` n'est copiée que si celle du conjoint est vide. Un conjoint qui a déjà une adresse n'est jamais touché. Rejouer la requête ne fait rien (`UPDATE 0`).
- **Ordre** : indépendante du déploiement du code, peut être rejouée avant ou après.

**Vérification préalable** (liste des conjoints qui seront complétés ; en local : 9 lignes, conjoints 91, 93, 95, 100 à 105) :
```sql
SELECT c.id AS conjoint_id, c.last_name AS conjoint, t.id AS titulaire_id, t.last_name AS titulaire, t.address, t.address2
FROM clients c JOIN clients t ON t.id = c.partner_id AND t.partner_id = c.id
WHERE c.id > c.partner_id
  AND NULLIF(TRIM(c.address), '') IS NULL
  AND NULLIF(TRIM(t.address), '') IS NOT NULL
ORDER BY c.id;
```

**Requête** :
```sql
BEGIN;
UPDATE clients c
SET address  = t.address,
    address2 = CASE WHEN NULLIF(TRIM(c.address2), '') IS NULL THEN t.address2 ELSE c.address2 END
FROM clients t
WHERE t.id = c.partner_id
  AND t.partner_id = c.id
  AND c.id > c.partner_id
  AND NULLIF(TRIM(c.address), '') IS NULL
  AND NULLIF(TRIM(t.address), '') IS NOT NULL;
COMMIT;
```

**Résultat attendu** : `UPDATE n`, où n est le nombre de lignes de la vérification préalable (9 sur la copie locale du 24/09 ; si le client a entre-temps saisi des adresses de conjoints, n sera plus petit — c'est normal). Si n diffère de la vérification préalable, `ROLLBACK` au lieu de `COMMIT`.

**Contrôle après coup** (attendu : aucune ligne) :
```sql
SELECT c.id, c.last_name FROM clients c JOIN clients t ON t.id = c.partner_id AND t.partner_id = c.id
WHERE c.id > c.partner_id AND NULLIF(TRIM(c.address), '') IS NULL AND NULLIF(TRIM(t.address), '') IS NOT NULL;
```
