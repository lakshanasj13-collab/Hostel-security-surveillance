@echo off
cd /d "%~dp0"
title Hostel Security System - Setup & Launcher

echo =========================================================
echo       HOSTEL SECURITY MONITORING - ENVIRONMENT SETUP
echo =========================================================
echo.

:: 1. Check if virtual environment exists, create if not
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python not found or failed to create venv.
        echo Please ensure Python 3.10-3.12 is installed and added to PATH.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment (.venv) already exists.
)

:: 2. Install / Verify dependencies
echo.
echo [2/3] Installing and verifying required packages...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Pip failed, attempting fallback installer...
    uv pip install --python .venv\Scripts\python.exe -r requirements.txt
)

:: 3. Launch application
echo.
echo [3/3] Setup complete! Starting Hostel Security Monitoring...
echo =========================================================
echo  * Look into the camera to register or verify identity.
echo  * Click on the video window and press 'q' to quit.
echo =========================================================
echo.

.venv\Scripts\python.exe security_monitor.py

pause
