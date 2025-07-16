@echo off
echo Installing OpenTelemetry dependencies for AI Calendar Assistant...
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo ✅ Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found, using system Python
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not available or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

echo Installing requirements...
pip install -r requirements.txt --verbose

if %errorlevel% neq 0 (
    echo ❌ Failed to install requirements
    echo Please check your internet connection and try again
    echo Error code: %errorlevel%
    pause
    exit /b 1
)

echo ✅ All packages installed successfully
echo.

echo Testing telemetry configuration...
python test_telemetry.py

echo.
echo 🎉 Installation complete!
echo.
echo Next steps:
echo 1. Run: _setup_application_insights.bat (to create Azure resources)
echo 2. Update your .env file with the Application Insights connection string
echo 3. Test your application to see telemetry in Azure Portal
echo.
pause
