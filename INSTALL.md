# Guide d'Installation et de Démarrage (Axcess CRM)

Ce document explique comment lancer l'application en arrière-plan sans laisser de terminaux ouverts.

## 1. Préparation (À faire une seule fois)

1.  Ouvrez un terminal dans `e:\axcess-crm\frontend`.
2.  Lancez la commande : `npm run build`
    *Cela va créer une version optimisée du site.*

## 2. Démarrage

Utilisez le fichier **`start_app.vbs`** situé à la racine du dossier `axcess-crm`.

1.  Double-cliquez sur **`start_app.vbs`**.
2.  L'application se lance en arrière-plan (aucun écran noir ne reste ouvert).
3.  Le navigateur s'ouvre automatiquement sur `http://localhost:5173`.

## 3. Arrêt

Utilisez le fichier **`stop_app.bat`** pour tout arrêter.

1.  Double-cliquez sur **`stop_app.bat`**.
