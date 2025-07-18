@echo off
REM Production Azure Maps Test Runner
REM Comprehensive test suite for production-ready Azure Maps operations

echo.
echo ===============================================================
echo Production Azure Maps Test Suite
echo ===============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Display current environment configuration
echo Environment Configuration:
echo -------------------------
if defined AZURE_MAPS_CLIENT_ID (
    echo ✓ AZURE_MAPS_CLIENT_ID is configured
) else (
    echo ? AZURE_MAPS_CLIENT_ID is not set
)

if defined AZURE_MAPS_SUBSCRIPTION_KEY (
    echo ✓ AZURE_MAPS_SUBSCRIPTION_KEY is configured  
) else (
    echo ? AZURE_MAPS_SUBSCRIPTION_KEY is not set
)

if defined DEBUG_AZURE_MAPS (
    echo ✓ DEBUG_AZURE_MAPS = %DEBUG_AZURE_MAPS%
) else (
    echo ? DEBUG_AZURE_MAPS is not set (default: disabled)
)

if defined DISABLE_TELEMETRY (
    echo ✓ DISABLE_TELEMETRY = %DISABLE_TELEMETRY%
) else (
    echo ? DISABLE_TELEMETRY is not set (default: enabled)
)

echo.

REM Check for required credentials
if not defined AZURE_MAPS_CLIENT_ID if not defined AZURE_MAPS_SUBSCRIPTION_KEY (
    echo ===============================================================
    echo CREDENTIAL CONFIGURATION REQUIRED
    echo ===============================================================
    echo.
    echo No Azure Maps credentials found. Please set one of:
    echo.
    echo Option 1 - Subscription Key Authentication:
    echo   set AZURE_MAPS_SUBSCRIPTION_KEY=your_subscription_key_here
    echo.
    echo Option 2 - Managed Identity Authentication:
    echo   set AZURE_MAPS_CLIENT_ID=your_client_id_here
    echo.
    echo Optional debugging and telemetry settings:
    echo   set DEBUG_AZURE_MAPS=true          ^(enable detailed logging^)
    echo   set DISABLE_TELEMETRY=true         ^(disable telemetry system^)
    echo.
    echo ===============================================================
    pause
    exit /b 1
)

echo Running production test suite...
echo.

REM Set test start time
set START_TIME=%time%

REM Run the production test with comprehensive output
python "%~dp0test_azure_maps_production.py"
set TEST_RESULT=%errorlevel%

REM Calculate test duration
set END_TIME=%time%

echo.
echo ===============================================================
echo Test Summary
echo ===============================================================
echo Start Time: %START_TIME%
echo End Time:   %END_TIME%

if %TEST_RESULT% equ 0 (
    echo Status:     SUCCESS ✓
    echo.
    echo Production Azure Maps operations are ready for deployment!
    echo.
    echo Recommendations:
    echo - Deploy to production environment
    echo - Set up monitoring and alerting
    echo - Configure Application Insights
    echo - Test with real production workloads
) else if %TEST_RESULT% equ 130 (
    echo Status:     INTERRUPTED (user cancelled)
) else (
    echo Status:     FAILED ✗
    echo.
    echo Troubleshooting recommendations:
    echo - Check Azure Maps credentials and permissions
    echo - Verify network connectivity to Azure services
    echo - Review error messages above for specific issues
    echo - Enable DEBUG_AZURE_MAPS=true for detailed logging
    echo - Check Azure service status for outages
)

echo ===============================================================
echo.
echo Press any key to exit...
pause >nul

exit /b %TEST_RESULT%
