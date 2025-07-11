@echo off
echo ===================================
echo Azure Container Registry Deployment
echo ===================================

set registry_name=drewelewis-grd9fpeebzejgwd7
set registry_location=drewelewis-grd9fpeebzejgwd7.azurecr.io
set image_name=ai-calendar-assistant
set image_tag=latest
set full_image_name=%registry_location%/%image_name%:%image_tag%

echo Debug: Full image name will be: %full_image_name%

echo Registry: %registry_location%
echo Image: %image_name%:%image_tag%
echo ===================================

echo.
echo Step 1: Building Docker image...
docker build -t %image_name%:%image_tag% -f dockerfile .
if errorlevel 1 (
    echo ERROR: Failed to build Docker image.
    pause
    exit /b 1
)
echo ✓ Docker image built successfully.

echo.
echo Step 2: Logging into Azure Container Registry...
az acr login --name %registry_name%
if errorlevel 1 (
    echo ERROR: Failed to login to Azure Container Registry.
    echo Make sure you are logged into Azure with 'az login' first.
    pause
    exit /b 1
)
echo ✓ Successfully logged into ACR.

echo.
echo Step 3: Tagging image for Azure Container Registry...
echo About to run: docker tag %image_name%:%image_tag% %full_image_name%
docker tag %image_name%:%image_tag% %full_image_name%
if errorlevel 1 (
    echo ERROR: Failed to tag image.
    echo Checking if local image exists...
    docker images %image_name%:%image_tag%
    pause
    exit /b 1
)
echo ✓ Image tagged successfully.

echo.
echo Step 4: Pushing image to Azure Container Registry...
echo About to run: docker push %full_image_name%
docker push %full_image_name%
if errorlevel 1 (
    echo ERROR: Failed to push image to ACR.
    echo Checking tagged images...
    docker images | findstr %registry_location%
    pause
    exit /b 1
)

echo.
echo ===================================
echo ✓ SUCCESS! Image pushed to ACR
echo ===================================
echo Image: %full_image_name%
echo ===================================

pause
