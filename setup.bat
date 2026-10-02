@echo off
echo ============================================================
echo   PocketSmart AI — Setup Script
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements.
    pause
    exit /b 1
)

echo [4/4] Checking .env file...
if not exist .env (
    echo WARNING: .env file not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo ACTION REQUIRED: Open .env and set your GEMINI_API_KEY
    echo.
) else (
    echo .env file found.
)

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   To start the server, run:
echo     venv\Scripts\activate.bat
echo     python run.py
echo.
echo   Then open: http://localhost:8000
echo ============================================================
pause
