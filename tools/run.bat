@echo off
setlocal

set PROJECT=%~dp0..
cd /d "%PROJECT%"

call ".venv\Scripts\activate.bat"

pip install -e . >nul
if errorlevel 1 (
    echo Editable install failed.
    exit /b %errorlevel%
)

python -m poster_montage_designer.app