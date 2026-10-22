@echo off
setlocal
cd /d "%~dp0"
title Parcel Detective
echo Starting Parcel Detective...
echo Keep this window open while using the dashboard.
echo Open http://127.0.0.1:8080 in your browser.
echo.

python --version >nul 2>&1
if not errorlevel 1 (
    python app.py
    goto finished
)

py --version >nul 2>&1
if not errorlevel 1 (
    py app.py
    goto finished
)

echo Python was not found. Install Python 3.10 or newer, then try again.
echo If Python is already installed, reopen your terminal after installation.

:finished
echo.
pause
endlocal
