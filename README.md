# Axcess CRM

Application de gestion de programmes immobiliers (CRM) conçue pour suivre la commercialisation de lots (appartements, maisons), la gestion des acquéreurs et l'édition de grilles de prix.

## Fonctionnalités Principales

*   **Gestion des Programmes et Bâtiments** : Création et suivi des projets immobiliers.
*   **Grille de Prix Interactive** : Visualisation des lots, modification des statuts (Libre, Option, Réservé, Acté) et des prix.
*   **Gestion des Clients** : Base de données acquéreurs/prospects.
*   **Statistiques** : Tableaux de bord en temps réel (CA, écoulement des stocks).
*   **Import/Export** : Imports CSV pour initialiser les grilles et exports pour le reporting.

## Prérequis

*   **Python** (3.10 ou supérieur) pour le Backend.
*   **Node.js** (LTS) pour le Frontend.
*   Accès réseau (si hébergé sur NAS).

## Installation

### 1. Backend (API)

```bash
cd backend
python -m venv venv
# Windows :
.\venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Frontend (Interface)

```bash
cd frontend
npm install
npm run build
```

## Démarrage Rapide (Windows / NAS)

Pour un usage quotidien sans terminal :

1.  **Démarrer** : Double-cliquez sur le script `start_app.vbs` à la racine du dossier.
    *   L'application se lance en arrière-plan.
    *   Le navigateur s'ouvre automatiquement sur `http://localhost:5173`.
2.  **Arrêter** : Double-cliquez sur `stop_app.bat`.

## Démarrage Manuel (Développement)

**Terminal 1 (Backend)** :
```bash
cd backend
.\venv\Scripts\activate
python main.py
# Le serveur écoute sur http://127.0.0.1:8001
```

**Terminal 2 (Frontend)** :
```bash
cd frontend
npm run dev
# Le site est accessible sur http://localhost:5173
```

## Structure du Projet

*   `/backend` : API FastAPI, base de données SQLite/Postgres.
*   `/frontend` : Interface React + Tailwind CSS.
*   `start_app.vbs` : Launcher Windows silencieux.
*   `stop_app.bat` : Script d'arrêt.

## Auteur

Axcess Promotion
