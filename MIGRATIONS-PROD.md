# Migrations à rejouer en production

Le projet n'utilise pas d'outil de migration (Alembic ou autre). Ce fichier liste, dans l'ordre, les opérations SQL à exécuter à la main sur la base de production le jour du déploiement.

Connexion : `docker compose exec db psql -U axcess_user -d axcess_crm`

Pour chaque opération : l'exécuter dans une transaction, vérifier que le résultat obtenu correspond au résultat attendu avant `COMMIT`, sinon `ROLLBACK`.

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
