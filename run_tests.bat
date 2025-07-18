@echo off
REM Multi-Agent System Test Suite Runner
REM This script runs comprehensive tests for the multi-agent orchestrator

echo ========================================
echo Multi-Agent System Test Suite
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
    echo WARNING: .env file not found. Some tests may fail without proper configuration.
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
echo Running Multi-Agent Test Suite...
echo.

REM Run the test suite
python test_multi_agent.py

REM Capture exit code
set TEST_EXIT_CODE=%errorlevel%

REM Deactivate virtual environment if it was activated
if exist venv\Scripts\activate.bat (
    deactivate
)

echo.
if %TEST_EXIT_CODE% equ 0 (
    echo Test suite completed successfully!
) else (
    echo Test suite completed with errors. Exit code: %TEST_EXIT_CODE%
)

pause
