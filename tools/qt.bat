@echo off

set PROJECT=%~dp0..

"%PROJECT%\.venv\Scripts\pyside6-designer.exe" ^
    "%PROJECT%\src\poster_montage_designer\ui\main_window.ui"