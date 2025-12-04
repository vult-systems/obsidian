# OpenCue RQD Bulk Deployment Script
# Deploys RQD to multiple Windows machines remotely
#
# Prerequisites:
# - PowerShell Remoting enabled on target machines (Enable-PSRemoting)
# - Admin credentials for target machines
# - machines.txt file with one hostname per line
#
# Usage: .\deploy-bulk.ps1 -CuebotHost "your-linux-server.domain.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$CuebotHost,

    [string]$MachineListFile = "$PSScriptRoot\machines.txt",
    [PSCredential]$Credential,
    [switch]$TestOnly
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OpenCue RQD Bulk Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cuebot Host: $CuebotHost" -ForegroundColor White
Write-Host "Machine List: $MachineListFile" -ForegroundColor White
Write-Host ""

# Check machine list file
if (-not (Test-Path $MachineListFile)) {
    Write-Host "ERROR: Machine list file not found: $MachineListFile" -ForegroundColor Red
    Write-Host "Create a file with one machine hostname per line" -ForegroundColor Yellow
    exit 1
}

$machines = Get-Content $MachineListFile | Where-Object { $_ -and $_ -notmatch '^\s*#' }
Write-Host "Found $($machines.Count) machines to deploy:" -ForegroundColor Yellow
$machines | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
Write-Host ""

# Get credentials if not provided
if (-not $Credential) {
    $Credential = Get-Credential -Message "Enter admin credentials for target machines"
}

# Read the install script
$installScript = Get-Content "$PSScriptRoot\install-rqd.ps1" -Raw
$rqdConfig = Get-Content "$PSScriptRoot\rqd.conf" -Raw

# Results tracking
$results = @{
    Success = @()
    Failed = @()
    Skipped = @()
}

foreach ($machine in $machines) {
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host "Deploying to: $machine" -ForegroundColor Cyan

    # Test connectivity
    if (-not (Test-Connection -ComputerName $machine -Count 1 -Quiet)) {
        Write-Host "  SKIPPED: Machine not reachable" -ForegroundColor Yellow
        $results.Skipped += $machine
        continue
    }

    if ($TestOnly) {
        Write-Host "  TEST MODE: Would deploy to $machine" -ForegroundColor Gray
        continue
    }

    try {
        # Create remote session
        $session = New-PSSession -ComputerName $machine -Credential $Credential -ErrorAction Stop

        # Create directories on remote machine
        Invoke-Command -Session $session -ScriptBlock {
            $dirs = @(
                "C:\OpenCue",
                "C:\OpenCue\logs",
                "C:\tmp\rqd\logs",
                "C:\tmp\rqd\shots",
                "$env:LOCALAPPDATA\OpenCue"
            )
            foreach ($dir in $dirs) {
                if (-not (Test-Path $dir)) {
                    New-Item -ItemType Directory -Path $dir -Force | Out-Null
                }
            }
        }

        # Copy config file
        $remoteConfigPath = "\\$machine\c$\Users\$($Credential.UserName.Split('\')[-1])\AppData\Local\OpenCue\rqd.conf"
        $configContent = $rqdConfig -replace "YOUR_LINUX_SERVER_HOSTNAME", $CuebotHost

        Invoke-Command -Session $session -ScriptBlock {
            param($config, $cuebotHost)
            $configPath = "$env:LOCALAPPDATA\OpenCue\rqd.conf"
            $config | Out-File -FilePath $configPath -Encoding UTF8 -Force
        } -ArgumentList $configContent, $CuebotHost

        # Install RQD
        Invoke-Command -Session $session -ScriptBlock {
            param($cuebotHost)

            # Check Python
            $python = Get-Command python -ErrorAction SilentlyContinue
            if (-not $python) {
                throw "Python not found"
            }

            # Create venv if not exists
            if (-not (Test-Path "C:\OpenCue\venv\Scripts\python.exe")) {
                python -m venv C:\OpenCue\venv
            }

            # Install RQD
            & C:\OpenCue\venv\Scripts\pip.exe install --upgrade pip 2>&1 | Out-Null
            & C:\OpenCue\venv\Scripts\pip.exe install opencue-rqd pynput 2>&1 | Out-Null

            # Download NSSM if not present
            if (-not (Test-Path "C:\OpenCue\nssm.exe")) {
                $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
                Invoke-WebRequest -Uri $nssmUrl -OutFile "$env:TEMP\nssm.zip"
                Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm" -Force
                Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" "C:\OpenCue\nssm.exe"
            }

            # Remove existing service
            $svc = Get-Service -Name "OpenCueRQD" -ErrorAction SilentlyContinue
            if ($svc) {
                & C:\OpenCue\nssm.exe stop OpenCueRQD 2>&1 | Out-Null
                & C:\OpenCue\nssm.exe remove OpenCueRQD confirm 2>&1 | Out-Null
                Start-Sleep -Seconds 2
            }

            # Install service
            & C:\OpenCue\nssm.exe install OpenCueRQD "C:\OpenCue\venv\Scripts\python.exe" "-m rqd.cuerqd"
            & C:\OpenCue\nssm.exe set OpenCueRQD AppDirectory "C:\tmp\rqd"
            & C:\OpenCue\nssm.exe set OpenCueRQD AppEnvironmentExtra "CUEBOT_HOSTNAME=$cuebotHost"
            & C:\OpenCue\nssm.exe set OpenCueRQD Start SERVICE_AUTO_START
            & C:\OpenCue\nssm.exe set OpenCueRQD AppStdout "C:\OpenCue\logs\rqd-stdout.log"
            & C:\OpenCue\nssm.exe set OpenCueRQD AppStderr "C:\OpenCue\logs\rqd-stderr.log"

            # Firewall rule
            $rule = Get-NetFirewallRule -DisplayName "OpenCue RQD" -ErrorAction SilentlyContinue
            if (-not $rule) {
                New-NetFirewallRule -DisplayName "OpenCue RQD" -Direction Inbound -Protocol TCP -LocalPort 8444 -Action Allow | Out-Null
            }

            # Start service
            & C:\OpenCue\nssm.exe start OpenCueRQD 2>&1 | Out-Null
            Start-Sleep -Seconds 3

            # Check status
            $svc = Get-Service -Name "OpenCueRQD"
            return $svc.Status
        } -ArgumentList $CuebotHost

        Remove-PSSession $session
        Write-Host "  SUCCESS: RQD installed and running" -ForegroundColor Green
        $results.Success += $machine

    } catch {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $results.Failed += $machine
        if ($session) { Remove-PSSession $session -ErrorAction SilentlyContinue }
    }
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Successful: $($results.Success.Count)" -ForegroundColor Green
$results.Success | ForEach-Object { Write-Host "  - $_" -ForegroundColor Green }
Write-Host ""
Write-Host "Failed: $($results.Failed.Count)" -ForegroundColor Red
$results.Failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
Write-Host ""
Write-Host "Skipped: $($results.Skipped.Count)" -ForegroundColor Yellow
$results.Skipped | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Verify in CueGUI or run: cueadmin -lh" -ForegroundColor Cyan
