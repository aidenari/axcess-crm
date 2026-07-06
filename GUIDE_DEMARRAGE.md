# 🚀 Guide de Démarrage - Axcess CRM (Mode Portable)

Ce guide explique comment lancer l'application Axcess CRM lorsque vous branchez votre disque dur sur un nouvel ordinateur (Windows 10/11).

## 📋 Pré-requis

Avant de lancer l'application sur un nouvel ordinateur, assurez-vous que :

1. **Python** est installé sur l'ordinateur.
   - Ouvrez un terminal (touche Windows + R, tapez `cmd`, Entrée) et tapez `python --version`.
   - Si vous avez une erreur, téléchargez et installez Python depuis [python.org](https://www.python.org/downloads/).
   - **IMPORTANT** : Lors de l'installation, cochez la case **"Add Python to PATH"**.

2. **Base de Données** (PostgreSQL)
   - Si votre base de données est sur le NAS ou un serveur distant, assurez-vous que le fichier `backend/.env` contient la bonne adresse IP (exemple: `DATABASE_URL=postgresql+psycopg2://user:pass@192.168.1.50:5432/db`).
   - Si la base de données est locale (sur le disque dur externe via une version portable de Postgres) ou installée sur le PC, assurez-vous qu'elle est lancée.

---

## ▶️ Lancement Rapide

1. Ouvrez le dossier `axcess-crm` sur votre disque dur externe.
2. Double-cliquez sur le fichier **`lancer_backend.bat`**.

Une fenêtre noire va s'ouvrir :
- **Si c'est la première fois** sur cet ordinateur (ou si la lettre du disque a changé), le script va automatiquement réinstaller les dépendances (cela peut prendre 1 à 2 minutes).
- Ensuite, le serveur démarrera et affichera des messages de démarrage de "Uvicorn".

✅ **C'est tout !** Votre backend est accessible.

---

## ❓ Problèmes Fréquents

**Q: La fenêtre se ferme tout de suite.**
R: Il y a probablement une erreur. Ouvrez le fichier `lancer_backend.bat`, mais au lieu de double-cliquer, faites "Clic droit > Modifier" et ajoutez `pause` à la toute fin du fichier si ce n'est pas déjà fait. Relancez pour lire le message d'erreur.

**Q: Erreur "ModuleNotFoundError" ou "Python not found"**
R: Vérifiez que Python est bien installé et ajouté au PATH (voir Pré-requis).

**Q: Le script "boucle" ou réinstalle tout à chaque fois.**
R: Supprimez manuellement le dossier `backend/venv` et relancez `lancer_backend.bat`.
