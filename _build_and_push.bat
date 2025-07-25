@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo 🚀 AI Calendar Assistant - Build and Push Pipeline
echo ================================================
echo.

echo 🔢 Step 1: Auto-incrementing minor version...
for /f %%i in ('python version_manager.py increment') do set VERSION=%%i
echo ✅ Version updated to: %VERSION%
echo.

echo 🐳 Step 2: Building Docker images...
docker buildx build --tag ai-calendar-assistant:latest --tag ai-calendar-assistant:%VERSION% --file dockerfile .
if %errorlevel% neq 0 (
    echo ❌ Docker build failed!
    exit /b 1
)
echo ✅ Docker images built successfully
echo.

echo 🏷️  Step 3: Tagging for Docker Hub...
set IMAGE_NAME=ai-calendar-assistant
set DOCKERHUB_USER=sxavramidis

docker tag %IMAGE_NAME%:latest %DOCKERHUB_USER%/%IMAGE_NAME%:latest
docker tag %IMAGE_NAME%:%VERSION% %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%
echo ✅ Images tagged for registry
echo.

echo 🔐 Step 4: Docker Hub login...
docker login --username %DOCKERHUB_USER%
if %errorlevel% neq 0 (
    echo ❌ Docker login failed!
    exit /b 1
)
echo.

echo 📤 Step 5: Pushing to Docker Hub...
docker push %DOCKERHUB_USER%/%IMAGE_NAME%:latest
docker push %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%
if %errorlevel% neq 0 (
    echo ❌ Docker push failed!
    exit /b 1
)

echo.
echo 🎉 Pipeline completed successfully!
echo ================================================
echo 📦 Published images:
echo    - %DOCKERHUB_USER%/%IMAGE_NAME%:latest
echo    - %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%
echo.
echo 📋 Next steps:
echo    - Update deployment configs to use version %VERSION%
echo    - Test the new container version
echo    - Create release notes for version %VERSION%
