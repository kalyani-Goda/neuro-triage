@echo off
REM NEURO-TRIAGE SETUP WIZARD FOR WINDOWS
REM Quick setup script for getting started

setlocal enabledelayedexpansion

echo ==========================================
echo   NEURO-TRIAGE SETUP WIZARD (Windows)
echo ==========================================
echo.

REM Check Python
echo [1/5] Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+ from python.org
    exit /b 1
)
echo ✓ Python found

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker not found. Please install Docker Desktop.
    echo    https://www.docker.com/products/docker-desktop
)
echo ✓ Docker desktop available

REM Setup environment
echo.
echo [2/5] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo ✓ Created .env file
    echo ⚠️  Please edit .env and add your OPENAI_API_KEY
    echo    Then run this script again.
    exit /b 0
) else (
    echo ✓ .env file exists
)

REM Install dependencies
echo.
echo [3/5] Installing dependencies...
pip install -q -r requirements.txt
echo ✓ Dependencies installed

REM Start Docker services
echo.
echo [4/5] Starting Docker services...
docker-compose up -d
echo ✓ Docker services started
echo    Waiting for services to be healthy (30 seconds^)...
timeout /t 30 /nobreak

REM Initialize system
echo.
echo [5/5] Initializing system...
python scripts/init_system.py
echo ✓ System initialized

echo.
echo ==========================================
echo   ✨ SETUP COMPLETE! ✨
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Start the backend API (in PowerShell^):
echo    python -m src.api.main
echo.
echo 2. In another PowerShell window, start the UI:
echo    streamlit run src/ui/app.py
echo.
echo 3. Open your browser:
echo    http://localhost:8501
echo.
echo For more information, see:
echo    - README.md ^(full documentation^)
echo    - QUICKSTART.md ^(quick reference^)
echo.
pause
