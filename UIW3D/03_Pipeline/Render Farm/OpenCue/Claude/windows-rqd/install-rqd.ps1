# OpenCue RQD Installation Script for Windows
# Run as Administrator
#
# Usage: .\install-rqd.ps1 -CuebotHost "your-linux-server.domain.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$CuebotHost,

    [string]$PythonPath = "python",
    [string]$InstallDir = "C:\OpenCue",
    [switch]$SkipNSSM
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OpenCue RQD Installation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Verify Python
Write-Host "Step 1: Verifying Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found at '$PythonPath'" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and add to PATH" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host ""
Write-Host "Step 2: Creating directories..." -ForegroundColor Yellow
$directories = @(
    $InstallDir,
    "$InstallDir\venv",
    "$InstallDir\logs",
    "C:\tmp\rqd\logs",
    "C:\tmp\rqd\shots"
)
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

# Create virtual environment
Write-Host ""
Write-Host "Step 3: Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "$InstallDir\venv\Scripts\python.exe")) {
    & $PythonPath -m venv "$InstallDir\venv"
    Write-Host "  Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  Virtual environment already exists" -ForegroundColor Gray
}

# Install RQD
Write-Host ""
Write-Host "Step 4: Installing OpenCue RQD..." -ForegroundColor Yellow
& "$InstallDir\venv\Scripts\pip.exe" install --upgrade pip
& "$InstallDir\venv\Scripts\pip.exe" install opencue-rqd pynput

# Create config directory and file
Write-Host ""
Write-Host "Step 5: Creating configuration..." -ForegroundColor Yellow
$configDir = "$env:LOCALAPPDATA\OpenCue"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Read template config and update Cuebot hostname
$configContent = Get-Content "$PSScriptRoot\rqd.conf" -Raw
$configContent = $configContent -replace "YOUR_LINUX_SERVER_HOSTNAME", $CuebotHost
$configContent | Out-File -FilePath "$configDir\rqd.conf" -Encoding UTF8

Write-Host "  Config written to: $configDir\rqd.conf" -ForegroundColor Green

# Configure Windows Firewall
Write-Host ""
Write-Host "Step 6: Configuring Windows Firewall..." -ForegroundColor Yellow
$ruleName = "OpenCue RQD"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if (-not $existingRule) {
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8444 `
        -Action Allow `
        -Description "Allow OpenCue Cuebot to connect to RQD" | Out-Null
    Write-Host "  Firewall rule created" -ForegroundColor Green
} else {
    Write-Host "  Firewall rule already exists" -ForegroundColor Gray
}

# Install NSSM and create service
if (-not $SkipNSSM) {
    Write-Host ""
    Write-Host "Step 7: Installing RQD as Windows Service..." -ForegroundColor Yellow

    # Check for NSSM
    $nssmPath = "$InstallDir\nssm.exe"
    if (-not (Test-Path $nssmPath)) {
        Write-Host "  Downloading NSSM..." -ForegroundColor Gray
        $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
        $nssmZip = "$env:TEMP\nssm.zip"
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm" -Force
        Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" $nssmPath
        Remove-Item $nssmZip -Force
        Remove-Item "$env:TEMP\nssm" -Recurse -Force
    }

    # Remove existing service if present
    $existingService = Get-Service -Name "OpenCueRQD" -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "  Removing existing service..." -ForegroundColor Gray
        & $nssmPath stop OpenCueRQD 2>$null
        & $nssmPath remove OpenCueRQD confirm 2>$null
        Start-Sleep -Seconds 2
    }

    # Install service
    Write-Host "  Creating service..." -ForegroundColor Gray
    & $nssmPath install OpenCueRQD "$InstallDir\venv\Scripts\python.exe" "-m rqd.cuerqd"
    & $nssmPath set OpenCueRQD AppDirectory "C:\tmp\rqd"
    & $nssmPath set OpenCueRQD AppEnvironmentExtra "CUEBOT_HOSTNAME=$CuebotHost"
    & $nssmPath set OpenCueRQD Start SERVICE_AUTO_START
    & $nssmPath set OpenCueRQD AppStdout "$InstallDir\logs\rqd-stdout.log"
    & $nssmPath set OpenCueRQD AppStderr "$InstallDir\logs\rqd-stderr.log"
    & $nssmPath set OpenCueRQD AppRotateFiles 1
    & $nssmPath set OpenCueRQD AppRotateBytes 10485760

    # Start service
    Write-Host "  Starting service..." -ForegroundColor Gray
    & $nssmPath start OpenCueRQD
    Start-Sleep -Seconds 3

    $service = Get-Service -Name "OpenCueRQD" -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        Write-Host "  Service is running!" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Service may not have started. Check logs." -ForegroundColor Yellow
    }
}

# Create test script
Write-Host ""
Write-Host "Step 8: Creating test script..." -ForegroundColor Yellow
$testScript = @"
# Test RQD connection to Cuebot
`$env:CUEBOT_HOSTNAME = "$CuebotHost"

# Activate virtual environment
& "$InstallDir\venv\Scripts\Activate.ps1"

# Test connection
python -c "import opencue; hosts = opencue.api.getHosts(); print('Connected! Hosts:', [h.name() for h in hosts])"
"@
$testScript | Out-File -FilePath "$InstallDir\test-connection.ps1" -Encoding UTF8
Write-Host "  Created: $InstallDir\test-connection.ps1" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "RQD is configured to connect to: $CuebotHost" -ForegroundColor White
Write-Host ""
Write-Host "Configuration file: $configDir\rqd.conf" -ForegroundColor Gray
Write-Host "Service logs: $InstallDir\logs\" -ForegroundColor Gray
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  Check service:  Get-Service OpenCueRQD" -ForegroundColor Gray
Write-Host "  Stop service:   Stop-Service OpenCueRQD" -ForegroundColor Gray
Write-Host "  Start service:  Start-Service OpenCueRQD" -ForegroundColor Gray
Write-Host "  View logs:      Get-Content $InstallDir\logs\rqd-stderr.log -Tail 50" -ForegroundColor Gray
Write-Host ""
Write-Host "The machine should appear in CueGUI within 30 seconds." -ForegroundColor Green
