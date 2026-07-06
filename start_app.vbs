Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory

' Commande pour lancer le Backend en arriere-plan
' On utilise cmd /c pour executer, et 0 pour cacher la fenetre
WshShell.Run "cmd /c cd /d """ & strPath & """ && backend\venv\Scripts\python.exe backend\main.py", 0, False

' Commande pour lancer le Frontend (Dev) en arriere-plan
WshShell.Run "cmd /c cd /d """ & strPath & "\frontend"" && npm run dev -- --port 5173", 0, False

' Attendre que les serveurs demarrent (5 secondes)
WScript.Sleep 5000

' Ouvrir le navigateur
WshShell.Run "http://localhost:5173"
