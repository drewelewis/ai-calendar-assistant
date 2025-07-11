@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Azure Container Registry Deployment
echo ===================================

set registry_name=drewelewis-grd9fpeebzejgwd7
set registry_location=drewelewis-grd9fpeebzejgwd7.azurecr.io
set image_name=ai-calendar-assistant
set image_tag=latest
set full_image_name=%registry_location%/%image_name%:%image_tag%

echo Registry: %registry_location%
echo Image: %image_name%:%image_tag%
echo Full image name: %full_image_name%
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
echo Step 1.5: Verifying local image exists...
docker images %image_name%:%image_tag% --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}"
if errorlevel 1 (
    echo WARNING: Could not verify image exists locally
)

echo.
echo Step 2: Logging into Azure Container Registry...
echo Running: az acr login --name %registry_name%
az acr login --name %registry_name%
set login_result=%errorlevel%
echo Login command completed with exit code: %login_result%

if %login_result% neq 0 (
    echo ERROR: Failed to login to Azure Container Registry.
    echo Make sure you are logged into Azure with 'az login' first.
    echo Also verify you have access to the registry: %registry_name%
    pause
    exit /b 1
)
echo ✓ Successfully logged into ACR.

echo.
echo Step 3: Tagging image for Azure Container Registry...
echo Running: docker tag %image_name%:%image_tag% %full_image_name%
docker tag %image_name%:%image_tag% %full_image_name%
set tag_result=%errorlevel%
echo Tag command completed with exit code: %tag_result%

if %tag_result% neq 0 (
    echo ERROR: Failed to tag image.
    echo Checking available local images:
    docker images
    pause
    exit /b 1
)
echo ✓ Image tagged successfully.

echo.
echo Step 3.5: Verifying tagged image exists...
docker images %full_image_name% --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}"

echo.
echo Step 4: Pushing image to Azure Container Registry...
echo Running: docker push %full_image_name%
docker push %full_image_name%
set push_result=%errorlevel%
echo Push command completed with exit code: %push_result%

if %push_result% neq 0 (
    echo ERROR: Failed to push image to ACR.
    echo Checking registry connection and tagged images...
    docker images | findstr %registry_location%
    pause
    exit /b 1
)

echo.
echo ===================================
echo ✓ SUCCESS! Image pushed to ACR
echo ===================================
echo Image: %full_image_name%
echo.
echo You can now use this image in Azure deployments such as:
echo - Azure Container Instances
echo - Azure Container Apps
echo - Azure Kubernetes Service
echo - Azure App Service
echo ===================================

pause
