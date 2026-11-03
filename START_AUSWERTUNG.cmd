@echo off
setlocal
cd /d "%~dp0"
set "SMARTOCHROME_PY=python"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "SMARTOCHROME_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
"%SMARTOCHROME_PY%" -c "import numpy; from PIL import Image" >nul 2>&1
if errorlevel 1 (
 echo Fuer die lokale Auswertung fehlen NumPy oder Pillow.
 echo Einmal ausfuehren: python -m pip install -r requirements-lab.txt
 pause
 exit /b 1
)
"%SMARTOCHROME_PY%" tools\local_lab.py
pause
