@echo off

set PROJECT=%~dp0..

call "%PROJECT%\.venv\Scripts\activate.bat"

python -m poster_montage_designer.app