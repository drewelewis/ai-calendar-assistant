@echo off
REM Get current version from pyproject.toml
for /f %%i in ('python version_manager.py get') do set VERSION=%%i

REM Set your Docker Hub username and image name
set IMAGE_NAME=ai-calendar-assistant
set DOCKERHUB_USER=drewl

echo 🚀 Pushing Docker images for version %VERSION%...
echo.

docker login --username %DOCKERHUB_USER%

echo 🏷️  Tagging images for Docker Hub...
REM Tag both latest and version-specific images for Docker Hub
docker tag %IMAGE_NAME%:latest %DOCKERHUB_USER%/%IMAGE_NAME%:latest
docker tag %IMAGE_NAME%:%VERSION% %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%

echo 📤 Pushing to Docker Hub...
REM Push both tags to Docker Hub
docker push %DOCKERHUB_USER%/%IMAGE_NAME%:latest
docker push %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%

echo.
echo ✅ Push completed!
echo 📦 Pushed images:
echo    - %DOCKERHUB_USER%/%IMAGE_NAME%:latest
echo    - %DOCKERHUB_USER%/%IMAGE_NAME%:%VERSION%