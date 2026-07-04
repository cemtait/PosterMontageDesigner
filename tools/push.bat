@echo off
set PROJECT=%~dp0..

cd /d "%PROJECT%"
git add .
git status
echo.
set /p MSG=Commit message: 
git commit -m "%MSG%"
git push