# ================================
# Test Exchange Online Connection
# ================================

Write-Host "=== Exchange Online Connection Test ===" -ForegroundColor Cyan

# Step 1: Test PowerShell Version
Write-Host "`n1. Testing PowerShell Version..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Host "PowerShell Version: $psVersion" -ForegroundColor White
if ($psVersion.Major -lt 5) {
    Write-Host "⚠️  PowerShell 5.0 or higher recommended" -ForegroundColor Yellow
} else {
    Write-Host "✅ PowerShell version is compatible" -ForegroundColor Green
}

# Step 2: Test Module Installation
Write-Host "`n2. Testing Exchange Online Module..." -ForegroundColor Yellow
try {
    $module = Get-Module -ListAvailable -Name ExchangeOnlineManagement -ErrorAction SilentlyContinue
    if ($module) {
        Write-Host "✅ Exchange Online Management module found" -ForegroundColor Green
        Write-Host "   Version: $($module.Version)" -ForegroundColor White
        Write-Host "   Path: $($module.ModuleBase)" -ForegroundColor White
    } else {
        Write-Host "❌ Exchange Online Management module not found" -ForegroundColor Red
        Write-Host "   Please install with: Install-Module -Name ExchangeOnlineManagement" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error checking module: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Test Module Import
Write-Host "`n3. Testing Module Import..." -ForegroundColor Yellow
try {
    Import-Module ExchangeOnlineManagement -Force -ErrorAction Stop
    Write-Host "✅ Module imported successfully" -ForegroundColor Green
    
    # Check available commands
    $commands = Get-Command -Module ExchangeOnlineManagement | Select-Object -First 5
    Write-Host "   Available commands (first 5):" -ForegroundColor White
    $commands | ForEach-Object { Write-Host "     - $($_.Name)" -ForegroundColor Gray }
} catch {
    Write-Host "❌ Error importing module: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Test Connection Function
Write-Host "`n4. Testing Connection Function..." -ForegroundColor Yellow
try {
    $connectionInfo = Get-Command Connect-ExchangeOnline -ErrorAction Stop
    Write-Host "✅ Connect-ExchangeOnline command is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Connect-ExchangeOnline command not found" -ForegroundColor Red
    exit 1
}

# Step 5: Check Current Connection
Write-Host "`n5. Checking Current Connection..." -ForegroundColor Yellow
try {
    $currentConnection = Get-ConnectionInformation -ErrorAction SilentlyContinue
    if ($currentConnection) {
        Write-Host "✅ Already connected to Exchange Online" -ForegroundColor Green
        Write-Host "   User: $($currentConnection.UserPrincipalName)" -ForegroundColor White
        Write-Host "   Organization: $($currentConnection.Organization)" -ForegroundColor White
        Write-Host "   Connection ID: $($currentConnection.ConnectionId)" -ForegroundColor White
        
        # Test Exchange cmdlets
        Write-Host "`n6. Testing Exchange Cmdlets..." -ForegroundColor Yellow
        try {
            $testMailbox = Get-Mailbox -ResultSize 1 -ErrorAction Stop
            Write-Host "✅ Get-Mailbox command works" -ForegroundColor Green
            Write-Host "   Sample mailbox: $($testMailbox.DisplayName)" -ForegroundColor White
        } catch {
            Write-Host "❌ Get-Mailbox failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "ℹ️  No active connection found" -ForegroundColor Yellow
        Write-Host "   You'll need to connect manually or let the script connect" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error checking connection: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 6: Test User Permissions
Write-Host "`n7. Testing User Context..." -ForegroundColor Yellow
try {
    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    Write-Host "Current Windows User: $($currentUser.Name)" -ForegroundColor White
    
    if ($currentConnection) {
        Write-Host "Exchange User: $($currentConnection.UserPrincipalName)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Error getting user context: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "If all tests passed, the main script should work." -ForegroundColor Green
Write-Host "If any tests failed, please address those issues first." -ForegroundColor Yellow
