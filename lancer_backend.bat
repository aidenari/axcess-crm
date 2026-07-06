@echo off
SETLOCAL EnableDelayedExpansion

cd /d "%~dp0"

echo ===================================================
echo   DEMARRAGE AUTO - AXCESS CRM BACKEND
echo ===================================================

REM 1. Verifier si Python est installe
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas detecte !
    echo Veuillez installer Python 3.11 ou superieur et cocher "Add Python to PATH"
    echo Telechargement : https://www.python.org/downloads/
    pause
    exit /b
)

REM 2. Aller dans le dossier backend
cd backend

REM 3. Detection de changement de lettre de lecteur ou de chemin (corruption du venv)
REM Une solution simple est de tester si le python du venv fonctionne.
venv\Scripts\python.exe --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ATTENTION] L'environnement virtuel semble invalide (changement de PC ?).
    echo Re-creating venv...
    if exist venv rmdir /s /q venv
)

REM 4. Creation/Mise a jour du VENV
IF NOT EXIST "venv" (
    echo [INFO] Installation de l'environnement virtuel...
    python -m venv venv
    echo [INFO] Installation des bibliotheques...
    venv\Scripts\pip install -r requirements.txt
)

REM 5. Lancer le serveur
echo [INFO] Lancement du serveur Axcess CRM...
echo L'application sera accessible a l'adresse : http://localhost:8001
echo Laissez cette fenetre ouverte.
echo.
venv\Scripts\python.exe main.py

pause
