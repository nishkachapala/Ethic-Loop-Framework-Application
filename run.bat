@echo off
title ETHIC-Loop Framework Server
echo ========================================================
echo Starting ETHIC-Loop Framework on http://127.0.0.1:5000
echo ========================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    start http://127.0.0.1:5000
    ".venv\Scripts\python.exe" app.py
) else (
    echo [ERROR] Virtual environment not found in .venv.
    echo Running with system python...
    start http://127.0.0.1:5000
    python app.py
)

pause
