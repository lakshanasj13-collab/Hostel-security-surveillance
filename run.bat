@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run environment setup first.
    pause
    exit /b 1
)
echo Starting Hostel Security Monitoring...
echo Press 'q' inside the video window to quit.
.venv\Scripts\python.exe security_monitor.py
pause
