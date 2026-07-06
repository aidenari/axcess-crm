@echo off
SETLOCAL EnableDelayedExpansion

echo ===================================================
echo   INSTALLATION DE L'ENVIRONNEMENT AXCESS CRM
echo ===================================================
echo.

REM 1. Verifier Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas detecte !
    echo Veuillez installer Python 3.11 ou superieur et cocher "Add Python to PATH"
    echo Telechargement : https://www.python.org/downloads/
    pause
    exit /b
)

REM 2. Aller dans le dossier backend
cd /d "%~dp0backend"

REM 3. Nettoyer l'ancien venv si existe (pour garantir la portabilite)
IF EXIST "venv" (
    echo [INFO] Suppression de l'ancien environnement virtuel (pour eviter les conflits de chemins)...
    rmdir /s /q venv
)

REM 4. Creation du venv
echo [INFO] Creation du nouvel environnement virtuel...
python -m venv venv
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Impossible de creer le venv.
    pause
    exit /b
)

REM 5. Installation des dependances
echo [INFO] Activation et installation des dependances...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] L'installation des dependances a echoue.
    pause
    exit /b
)

echo.
echo ===================================================
echo   INSTALLATION TERMINEE AVEC SUCCES !
echo ===================================================
echo Vous pouvez maintenant lancer l'application avec start_app.vbs
echo.
pause

