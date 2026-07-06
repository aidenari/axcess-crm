@echo off
echo Arret des processus Axcess CRM...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Axcess Backend*" >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo Controles :
echo Si python.exe ou node.exe tournent encore pour d'autres applis, ceci a peut-etre coupe trop large.
echo Dans un contexte dedié (NAS), cela devrait aller.
pause
