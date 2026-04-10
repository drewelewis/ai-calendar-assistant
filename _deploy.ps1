#Requires -Version 5.1
<#
.SYNOPSIS
    Full deploy pipeline: version increment → Docker build → push → ACA update → smoke test.
.PARAMETER SkipTest
    Skip the quick_test.py smoke test after deployment.
.PARAMETER SkipVersion
    Skip version increment (re-deploy current version).
.EXAMPLE
    .\_deploy.ps1
    .\_deploy.ps1 -SkipTest
    .\_deploy.ps1 -SkipVersion
#>
param(
    [switch]$SkipTest,
    [switch]$SkipVersion
)

$ErrorActionPreference = "Stop"
# Force UTF-8 so emoji output doesn't crash
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# Always use the venv Python
$PYTHON = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$IMAGE_NAME    = "ai-calendar-assistant"
$DOCKERHUB_USER = "drewl"
$ACA_NAME      = "aiwrapper-private"
$RESOURCE_GROUP = "devops-ai-rg"

function Write-Step($msg) { Write-Host "`n$msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  ❌ $msg" -ForegroundColor Red ; exit 1 }

Write-Host "`n🚀 AI Calendar Assistant - Full Deploy Pipeline" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Yellow

# ── Step 1: Version ──────────────────────────────────────────────────────────
Write-Step "Step 1: Version"
if ($SkipVersion) {
    $VERSION = (& $PYTHON version_manager.py get | Select-Object -Last 1).Trim()
    Write-OK "Keeping current version: $VERSION"
} else {
    $VERSION = (& $PYTHON version_manager.py increment | Select-Object -Last 1).Trim()
    if ($LASTEXITCODE -ne 0) { Write-Fail "version_manager.py increment failed" }
    Write-OK "Version incremented to: $VERSION"
}

# ── Step 2: Docker build ──────────────────────────────────────────────────────
Write-Step "Step 2: Docker build"
# docker buildx writes progress to stderr, which triggers $ErrorActionPreference="Stop".
# Temporarily set to Continue so docker build output doesn't kill the script.
$ErrorActionPreference = "Continue"
docker buildx build `
    --tag "${IMAGE_NAME}:latest" `
    --tag "${IMAGE_NAME}:${VERSION}" `
    --file dockerfile .
$ErrorActionPreference = "Stop"
# Verify the image was actually built (LASTEXITCODE from buildx is unreliable)
$null = docker image inspect "${IMAGE_NAME}:${VERSION}" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Fail "Docker build failed - image '${IMAGE_NAME}:${VERSION}' not found after build" }
Write-OK "Built ${IMAGE_NAME}:${VERSION} and :latest"

# ── Step 3: Tag ───────────────────────────────────────────────────────────────
Write-Step "Step 3: Tag for Docker Hub"
docker tag "${IMAGE_NAME}:${VERSION}" "${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION}"
docker tag "${IMAGE_NAME}:latest"     "${DOCKERHUB_USER}/${IMAGE_NAME}:latest"
Write-OK "Tagged as ${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION} and :latest"

# ── Step 4: Push ──────────────────────────────────────────────────────────────
Write-Step "Step 4: Push to Docker Hub"
docker push "${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION}"
if ($LASTEXITCODE -ne 0) { Write-Fail "Push of :${VERSION} failed" }
docker push "${DOCKERHUB_USER}/${IMAGE_NAME}:latest"
if ($LASTEXITCODE -ne 0) { Write-Fail "Push of :latest failed" }
Write-OK "Pushed both tags to Docker Hub"

# ── Step 5: ACA update ───────────────────────────────────────────────────────
Write-Step "Step 5: Update Azure Container App"
$result = az containerapp update `
    --name $ACA_NAME `
    --resource-group $RESOURCE_GROUP `
    --image "${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION}" `
    --set-env-vars "APP_VERSION=${VERSION}" `
    --query "{revision:properties.latestRevisionName, state:properties.provisioningState, image:properties.template.containers[0].image}" `
    -o json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) { Write-Fail "ACA update failed" }
Write-OK "Revision : $($result.revision)"
Write-OK "State    : $($result.state)"
Write-OK "Image    : $($result.image)"

# ── Step 6: Smoke test ────────────────────────────────────────────────────────
if (-not $SkipTest) {
    Write-Step "Step 6: Smoke test (quick_test.py)"
    $env:PYTHONUTF8 = "1"
    & $PYTHON quick_test.py
    if ($LASTEXITCODE -ne 0) { Write-Fail "Smoke test failed - check ACA logs" }
    Write-OK "Smoke test passed"
} else {
    Write-Host "`nStep 6: Smoke test skipped (-SkipTest)" -ForegroundColor DarkGray
}

Write-Host "`n================================================" -ForegroundColor Yellow
Write-Host "🎉 Deploy complete: ${DOCKERHUB_USER}/${IMAGE_NAME}:${VERSION}" -ForegroundColor Yellow
Write-Host "   ACA revision: $($result.revision)" -ForegroundColor Yellow
