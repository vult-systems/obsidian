Download and save as `.ps1`

The script automates:

- Network drive mapping
- File copying
- Silent installation with all your settings
- Permission configuration
- Service restart

Usage:

```powershell
.\Install-DeadlineClient.ps1 -RoomNumber 400
```

You'll still need to manually set the license variable and mount SYSTEM drives (one-time setup), but the main install is fully automated.

```powershell
# Install-DeadlineClient.ps1
# Automates Deadline client installation for UIW render farm

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('400','405','406','407')]
    [string]$RoomNumber
)

#Requires -RunAsAdministrator

$ErrorActionPreference = 'Stop'

# Configuration
$sourceServer = "\\10.40.14.25\RenderSourceRepository"
$installerPath = "$sourceServer\DeadlineClientInstallers\Deadline-10.4.1.6-windows-installer"
$localInstallerPath = "D:\DeadlineInstaller"
$serviceAccount = ".\csadmin$RoomNumber"

Write-Host "Installing Deadline Client for Room $RoomNumber" -ForegroundColor Cyan

# Step 1: Map network drive
Write-Host "Mapping T: drive..." -ForegroundColor Yellow
net use T: $sourceServer /user:perforce uiw3d /persistent:yes | Out-Null

# Step 2: Copy installer files
Write-Host "Copying installer files..." -ForegroundColor Yellow
New-Item -Path $localInstallerPath -ItemType Directory -Force | Out-Null
Copy-Item "$installerPath\DeadlineClient-10.4.1.6-windows-installer.exe" -Destination $localInstallerPath
Copy-Item "$installerPath\Deadline10RemoteClient.pfx" -Destination $localInstallerPath

# Step 3: Silent install
Write-Host "Running installer..." -ForegroundColor Yellow
$installerArgs = @(
    '--mode', 'unattended',
    '--connectiontype', 'Remote',
    '--proxyrootdir', '10.40.14.25:4433',
    '--proxycertificate', "$localInstallerPath\Deadline10RemoteClient.pfx",
    '--proxycertificatepassword', 'uiw3d',
    '--launcherdaemon', 'true',
    '--launcherdaemonuser', $serviceAccount,
    '--slavestartup', 'true',
    '--autoupdateoverride', 'False'
)

$process = Start-Process -FilePath "$localInstallerPath\DeadlineClient-10.4.1.6-windows-installer.exe" `
    -ArgumentList $installerArgs -Wait -PassThru

if ($process.ExitCode -ne 0) {
    throw "Installation failed with exit code $($process.ExitCode)"
}

# Step 4: Set worker permissions
Write-Host "Configuring permissions..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # Wait for service to create directories
icacls "C:\ProgramData\Thinkbox\Deadline10\workers" /grant "${serviceAccount}:(OI)(CI)F" /T | Out-Null

# Step 5: Restart service
Write-Host "Restarting Deadline service..." -ForegroundColor Yellow
Restart-Service -Name "DeadlineLauncher10" -Force

# Verify
Start-Sleep -Seconds 5
$worker = Get-Process deadlineworker -ErrorAction SilentlyContinue
if ($worker) {
    Write-Host "✓ Installation complete - Worker running" -ForegroundColor Green
} else {
    Write-Warning "Worker process not found - check Task Manager"
}
```


---
Status
#Good 

Related
[[../Render Farm/What Is Deadline|What Is Deadline]] [[../../02_Technical/PowerShell/What is PowerShell|What is PowerShell]]

Tags
[[../../05_Utility/Tags/Deadline|Deadline]] [[../../05_Utility/Tags/PowerShell|PowerShell]] 