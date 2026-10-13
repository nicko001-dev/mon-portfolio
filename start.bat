@echo off
REM Lance le serveur de developpement du portfolio de Nick.
REM Double-clic sur ce fichier pour demarrer, Ctrl+C dans la fenetre pour arreter.
cd /d "%~dp0"
call "venv\Scripts\activate.bat"
echo.
echo   Portfolio - serveur de developpement
echo   Adresse : http://127.0.0.1:8000/
echo   Arreter : Ctrl+C
echo.
python manage.py runserver
pause
