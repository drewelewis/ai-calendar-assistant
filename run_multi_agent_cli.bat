@echo off
REM Multi-Agent AI Calendar Assistant CLI Launcher
REM This script launches the interactive multi-agent system

echo ========================================
echo Multi-Agent AI Calendar Assistant CLI
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found. Please ensure environment variables are configured.
    echo.
    echo Required variables:
    echo   - AZURE_OPENAI_API_KEY
    echo   - AZURE_OPENAI_ENDPOINT  
    echo   - AZURE_OPENAI_API_VERSION
    echo   - AZURE_CLIENT_ID
    echo   - AZURE_CLIENT_SECRET
    echo   - AZURE_TENANT_ID
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using global Python installation.
)

REM Install requirements if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

echo.
echo Starting Multi-Agent CLI...
echo.

REM Launch the CLI
python multi_agent_cli.py

REM Deactivate virtual environment if it was activated
if exist venv\Scripts\activate.bat (
    deactivate
)

echo.
echo CLI session ended.
pause
