@echo off
set PROJECT=%~dp0..

cd /d "%PROJECT%"

git add .
git status

echo.
set /p MSG=Commit message: 

if "%MSG%"=="" (
    echo Commit cancelled: no message entered.
    exit /b 1
)

git commit -m "%MSG%"
git push