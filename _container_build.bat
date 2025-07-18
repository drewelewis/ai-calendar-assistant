@echo off
echo 🔢 Auto-incrementing minor version...
echo.

REM Increment minor version and capture the new version
for /f %%i in ('python version_manager.py increment') do set VERSION=%%i

echo 🐳 Building Docker image with version %VERSION%...
echo.

REM Build with both latest and version tags
docker buildx build --tag ai-calendar-assistant:latest --tag ai-calendar-assistant:%VERSION% --file dockerfile .

echo.
echo ✅ Build completed!
echo 📦 Built images:
echo    - ai-calendar-assistant:latest
echo    - ai-calendar-assistant:%VERSION%
echo.
echo 💡 Next: Run _container_push.bat to push images to registry