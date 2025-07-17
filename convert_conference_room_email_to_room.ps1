# ================================
# Convert Mailbox to Room Mailbox
# ================================

param(
    [Parameter(Mandatory=$false)]
    [string]$RoomMailboxes = "conf_apollo@MngEnvMCAP623732.onmicrosoft.com,conf_gemini@MngEnvMCAP623732.onmicrosoft.com",
    
    [Parameter(Mandatory=$false)]
    [string]$AdminUPN = "admin@MngEnvMCAP623732.onmicrosoft.com"
)

# Function to check if Exchange Online module is available
function Test-ExchangeOnlineModule {
    try {
        # Check if module is installed
        $module = Get-Module -ListAvailable -Name ExchangeOnlineManagement -ErrorAction SilentlyContinue
        if (-not $module) {
            Write-Error "Exchange Online Management module is not installed. Please install it using: Install-Module -Name ExchangeOnlineManagement"
            return $false
        }
        
        # Import the module
        Write-Host "Loading Exchange Online Management module..." -ForegroundColor Yellow
        Import-Module ExchangeOnlineManagement -Force -ErrorAction Stop
        
        # Check module version
        $moduleVersion = (Get-Module ExchangeOnlineManagement).Version
        Write-Host "✅ Exchange Online Management module loaded successfully (Version: $moduleVersion)" -ForegroundColor Green
        
        return $true
    }
    catch {
        Write-Error "Failed to load Exchange Online Management module: $($_.Exception.Message)"
        Write-Host "Try running: Install-Module -Name ExchangeOnlineManagement -Force" -ForegroundColor Yellow
        return $false
    }
}

# Function to connect to Exchange Online
function Connect-ToExchangeOnline {
    param([string]$AdminUPN)
    
    try {
        Write-Host "Connecting to Exchange Online..." -ForegroundColor Yellow
        Write-Host "Note: Authentication window may appear in your browser." -ForegroundColor Cyan
        
        # Check if already connected and cmdlets are available
        try {
            $existingConnection = Get-ConnectionInformation -ErrorAction SilentlyContinue
            if ($existingConnection) {
                Write-Host "Found existing connection to: $($existingConnection.UserPrincipalName)" -ForegroundColor Green
                
                # Test if Exchange cmdlets are working
                $testMailbox = Get-Mailbox -ResultSize 1 -ErrorAction SilentlyContinue
                if ($testMailbox) {
                    Write-Host "✅ Exchange Online cmdlets are working properly." -ForegroundColor Green
                    return $true
                }
            }
        }
        catch {
            Write-Host "Previous connection not functional, reconnecting..." -ForegroundColor Yellow
        }
        
        # Try different connection methods
        $connectionSuccess = $false
        
        # Method 1: Try with device code authentication (better for environments with browser issues)
        Write-Host "Trying device code authentication..." -ForegroundColor Yellow
        try {
            Connect-ExchangeOnline -Device -ShowProgress $true -ErrorAction Stop
            $connectionSuccess = $true
            Write-Host "✅ Connected using device code authentication." -ForegroundColor Green
        }
        catch {
            Write-Host "Device code authentication failed, trying interactive..." -ForegroundColor Yellow
        }
        
        # Method 2: Try interactive authentication if device code failed
        if (-not $connectionSuccess) {
            Write-Host "Trying interactive authentication..." -ForegroundColor Yellow
            try {
                # Set a timeout for the connection attempt
                $job = Start-Job -ScriptBlock {
                    Import-Module ExchangeOnlineManagement
                    Connect-ExchangeOnline -ShowProgress $true
                }
                
                # Wait for connection with timeout
                $timeout = 60 # 60 seconds timeout
                $completed = Wait-Job -Job $job -Timeout $timeout
                
                if ($completed) {
                    Receive-Job -Job $job
                    Remove-Job -Job $job
                    $connectionSuccess = $true
                    Write-Host "✅ Connected using interactive authentication." -ForegroundColor Green
                } else {
                    Write-Host "⚠️ Connection timed out after $timeout seconds." -ForegroundColor Yellow
                    Stop-Job -Job $job
                    Remove-Job -Job $job -Force
                }
            }
            catch {
                Write-Host "Interactive authentication failed." -ForegroundColor Red
            }
        }
        
        # Method 3: Try with certificate-based authentication if available
        if (-not $connectionSuccess) {
            Write-Host "Trying certificate-based authentication..." -ForegroundColor Yellow
            try {
                Connect-ExchangeOnline -CertificateThumbprint "AutoDetect" -ShowProgress $true -ErrorAction Stop
                $connectionSuccess = $true
                Write-Host "✅ Connected using certificate authentication." -ForegroundColor Green
            }
            catch {
                Write-Host "Certificate authentication failed or not configured." -ForegroundColor Yellow
            }
        }
        
        if (-not $connectionSuccess) {
            throw "All connection methods failed"
        }
        
        # Wait a moment for connection to fully initialize
        Start-Sleep -Seconds 3
        
        # Verify connection and cmdlet availability
        $currentUser = Get-ConnectionInformation -ErrorAction Stop
        Write-Host "✅ Connected to Exchange Online successfully." -ForegroundColor Green
        Write-Host "Connected as: $($currentUser.UserPrincipalName)" -ForegroundColor Green
        Write-Host "Organization: $($currentUser.Organization)" -ForegroundColor Green
        
        # Test Exchange cmdlets
        Write-Host "Testing Exchange cmdlets..." -ForegroundColor Yellow
        $testMailbox = Get-Mailbox -ResultSize 1 -ErrorAction Stop
        Write-Host "✅ Exchange Online cmdlets are working properly." -ForegroundColor Green
        
        return $true
    }
    catch {
        Write-Error "Failed to connect to Exchange Online: $($_.Exception.Message)"
        Write-Host "`nTroubleshooting tips:" -ForegroundColor Yellow
        Write-Host "1. Try running this command manually: Connect-ExchangeOnline -Device" -ForegroundColor Yellow
        Write-Host "2. Ensure you have Exchange Online admin permissions" -ForegroundColor Yellow
        Write-Host "3. Check if your browser is blocking popups" -ForegroundColor Yellow
        Write-Host "4. Try running PowerShell as Administrator" -ForegroundColor Yellow
        Write-Host "5. Clear browser cache and cookies for Microsoft login" -ForegroundColor Yellow
        Write-Host "6. Try connecting from a different network" -ForegroundColor Yellow
        Write-Host "7. Update the Exchange Online module: Update-Module ExchangeOnlineManagement" -ForegroundColor Yellow
        return $false
    }
}

# Function to process a single room mailbox
function Convert-SingleRoomMailbox {
    param(
        [string]$RoomMailbox,
        [int]$Index,
        [int]$Total
    )
    
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "Processing Room Mailbox [$Index/$Total]: $RoomMailbox" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    try {
        # Get mailbox information
        Write-Host "Getting mailbox information..." -ForegroundColor Yellow
        $mailbox = Get-Mailbox -Identity $RoomMailbox -ErrorAction Stop
        
        Write-Host "Current mailbox type: $($mailbox.RecipientTypeDetails)" -ForegroundColor White
        
        # Convert to Room mailbox if needed
        if ($mailbox.RecipientTypeDetails -ne "RoomMailbox") {
            Write-Host "Converting $RoomMailbox to Room mailbox..." -ForegroundColor Yellow
            Set-Mailbox -Identity $RoomMailbox -Type Room -ErrorAction Stop
            Write-Host "✅ Successfully converted to Room mailbox." -ForegroundColor Green
            
            # Refresh mailbox info after conversion
            $mailbox = Get-Mailbox -Identity $RoomMailbox -ErrorAction Stop
        } else {
            Write-Host "✅ $RoomMailbox is already a Room mailbox." -ForegroundColor Green
        }
        
        # Ensure it's visible in the GAL
        Write-Host "Checking Global Address List visibility..." -ForegroundColor Yellow
        if ($mailbox.HiddenFromAddressListsEnabled) {
            Write-Host "Unhiding $RoomMailbox from address lists..." -ForegroundColor Yellow
            Set-Mailbox -Identity $RoomMailbox -HiddenFromAddressListsEnabled $false -ErrorAction Stop
            Write-Host "✅ Room mailbox is now visible in address lists." -ForegroundColor Green
        } else {
            Write-Host "✅ $RoomMailbox is already visible in address lists." -ForegroundColor Green
        }
        
        # Configure room mailbox settings for better functionality
        Write-Host "Configuring room mailbox settings..." -ForegroundColor Yellow
        Set-CalendarProcessing -Identity $RoomMailbox -AutomateProcessing AutoAccept -ErrorAction Stop
        Write-Host "✅ Room mailbox configured to auto-accept meeting requests." -ForegroundColor Green
        
        Write-Host "✅ Room mailbox conversion completed successfully!" -ForegroundColor Green
        Write-Host "Room mailbox: $RoomMailbox" -ForegroundColor White
        Write-Host "Type: $($mailbox.RecipientTypeDetails)" -ForegroundColor White
        Write-Host "Visible in GAL: $(-not $mailbox.HiddenFromAddressListsEnabled)" -ForegroundColor White
        
        return @{
            Success = $true
            Mailbox = $RoomMailbox
            Message = "Successfully processed"
        }
    }
    catch {
        Write-Error "Failed to process $RoomMailbox : $($_.Exception.Message)"
        Write-Host "Please check the mailbox identity and your permissions." -ForegroundColor Red
        
        return @{
            Success = $false
            Mailbox = $RoomMailbox
            Message = $_.Exception.Message
        }
    }
}

# Main script execution
Write-Host "Starting Room Mailbox Conversion Process..." -ForegroundColor Cyan

# Parse comma-separated room mailboxes
$roomMailboxList = $RoomMailboxes -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
$totalMailboxes = $roomMailboxList.Count

Write-Host "Target Mailboxes ($totalMailboxes):" -ForegroundColor Cyan
$roomMailboxList | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }

# Check if Exchange Online module is available
if (-not (Test-ExchangeOnlineModule)) {
    exit 1
}

# Connect to Exchange Online
if (-not (Connect-ToExchangeOnline -AdminUPN $AdminUPN)) {
    exit 1
}

try {
    # Process each room mailbox
    $results = @()
    for ($i = 0; $i -lt $roomMailboxList.Count; $i++) {
        $result = Convert-SingleRoomMailbox -RoomMailbox $roomMailboxList[$i] -Index ($i + 1) -Total $totalMailboxes
        $results += $result
    }

    # Summary report
    Write-Host "`n" + "="*60 -ForegroundColor Magenta
    Write-Host "SUMMARY REPORT" -ForegroundColor Magenta
    Write-Host "="*60 -ForegroundColor Magenta

    $successCount = ($results | Where-Object { $_.Success }).Count
    $failureCount = ($results | Where-Object { -not $_.Success }).Count

    Write-Host "Total mailboxes processed: $totalMailboxes" -ForegroundColor White
    Write-Host "Successful conversions: $successCount" -ForegroundColor Green
    Write-Host "Failed conversions: $failureCount" -ForegroundColor Red

    if ($successCount -gt 0) {
        Write-Host "`nSuccessful conversions:" -ForegroundColor Green
        $results | Where-Object { $_.Success } | ForEach-Object {
            Write-Host "  ✅ $($_.Mailbox)" -ForegroundColor Green
        }
    }

    if ($failureCount -gt 0) {
        Write-Host "`nFailed conversions:" -ForegroundColor Red
        $results | Where-Object { -not $_.Success } | ForEach-Object {
            Write-Host "  ❌ $($_.Mailbox) - $($_.Message)" -ForegroundColor Red
        }
    }
}
catch {
    Write-Error "An unexpected error occurred: $($_.Exception.Message)"
    exit 1
}
finally {
    # Disconnect from Exchange Online
    Write-Host "`nDisconnecting from Exchange Online..." -ForegroundColor Yellow
    Disconnect-ExchangeOnline -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "✅ Disconnected from Exchange Online." -ForegroundColor Green
}
