# Mode d'emploi - Installation Docker (Windows)

Ce guide explique comment installer et lancer le projet **axcess-crm** sur un environnement Windows via Docker Desktop.

## Prérequis
1.  **Docker Desktop** : Télécharger et installer depuis [docker.com](https://www.docker.com/products/docker-desktop/).
2.  **WSL 2** : Docker Desktop vous proposera de l'activer lors de l'installation. C'est recommandé.
3.  **Redémarrage** : Redémarrez votre PC après l'installation.

## Installation
1.  Copiez le dossier du projet (ex: `C:\axcess-crm`) sur votre machine.
    > **IMPORTANT** : Évitez les espaces et accents dans le chemin du dossier (ex: pas de `C:\Projets Récents\Mon App`). Docker et certains outils peuvent mal interpréter ces caractères, causant des erreurs de build ou de volumes.
2.  Ouvrez un terminal (PowerShell ou CMD) et naviguez dans ce dossier :
    ```powershell
    cd C:\axcess-crm
    ```

## Lancement (Build & Run)
Pour construire les images et lancer l'application en arrière-plan :
```powershell
docker compose up --build -d
```
Attendez quelques minutes lors du premier lancement (téléchargement des images et installation des dépendances).

## Accès à l'application
- **Frontend** : [http://localhost:3000](http://localhost:3000)
- **Backend API** : [http://localhost:8000/docs](http://localhost:8000/docs) (Documentation Swagger)

## Gestion courante
- **Voir les logs** (pour vérifier que tout tourne bien) :
  ```powershell
  docker compose logs -f
  ```
  (Ctrl+C pour quitter les logs, cela ne coupe pas l'application)

- **Arrêter l'application** :
  ```powershell
  docker compose down
  ```

- **Arrêter et supprimer les données (Reset DB)** :
  ```powershell
  docker compose down -v
  ```

- **Sauvegarder la base de données** :
  ```powershell
  docker exec axcess-db pg_dump -U axcess_user axcess_crm > backup.sql
  ```

## Dépannage (Check-list)
1.  **Docker non démarré** : Vérifiez que l'icône de la baleine Docker est bien visible près de l'horloge.
2.  **Ports occupés** : Vérifiez que rien n'utilise déjà les ports 3000 (React), 8000 (Python) ou 5432 (Postgres).
3.  **WSL 2** : Si Docker ne démarre pas, vérifiez que la virtualisation est activée dans le BIOS.
4.  **Firewall / Antivirus** : Il peut bloquer le partage de fichiers ou le réseau. Autorisez Docker.
5.  **VPN / Proxy** : En entreprise, coupez le VPN pour le premier build (npm/pip install échouent souvent derrière un proxy).
6.  **"db host not found"** : Le backend attend que la DB soit prête. Il va réessayer automatiquement, patientez quelques secondes.
7.  **Accès Localhost** : Si `localhost` ne marche pas, essayez `127.0.0.1`.
8.  **Chemins fichiers** : Vérifiez encore qu'il n'y a pas d'espace dans le chemin du dossier projet (`C:\Program Files` -> Problème possible).
