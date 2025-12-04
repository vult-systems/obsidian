---
tags: [Deadline, PowerShell, Automation, Documentation]
status: Good
---

# Automated Deadline Client Installation

PowerShell script for automated Deadline 10.4.2.2 deployment to UIW 3D lab machines.

## Quick Install

Run as Administrator on the target worker machine:

```powershell
.\Install-DeadlineClient.ps1 -RoomNumber 400
```

Replace `400` with your room number (400, 405, 406, or 407).

---

## What It Does

The automation script performs all critical installation and configuration steps:

1. ✅ Mounts network share (temporary, for installer access)
2. ✅ Copies installer and certificate files to D:\
3. ✅ Runs silent installation with correct settings
4. ✅ Configures "Everyone" permissions on Deadline folders
5. ✅ Stores network credentials for UNC path access
6. ✅ Sets Maya license environment variable
7. ✅ Creates local Arnold cache directory
8. ✅ Restarts Deadline service
9. ✅ Verifies worker is running

**Result:** Fully configured worker ready for rendering.

---

## Complete Working Configuration

The automated installation applies this configuration:

### 1. Deadline Client Installation
- Version: 10.4.2.2
- Install path: `C:\Program Files\Thinkbox\Deadline10\`
- Connection type: Remote Connection Server (RCS)
- Server: `10.40.14.25:4433` (HTTPS/TLS)
- Certificate: `Deadline10RemoteClient.pfx`
- Service account: `.\csadmin[room#]`

### 2. Critical Permissions
```powershell
# Everyone full control on Deadline folder (CRITICAL)
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T
```
**Why:** Worker service needs write access for logs, job data, and temp files.

### 3. Network Credentials (UNC Paths)
```powershell
# Store credentials for SMB access
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```
**Why:** Workers access `\\10.40.14.25\RenderSourceRepository\...` directly (no drive mapping).

### 4. Maya License
```powershell
# System-wide environment variable
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)
```
**Why:** Maya finds license server automatically when rendering.

### 5. Local Arnold Cache
```powershell
# Create local cache directory
New-Item -Path "D:\ArnoldCache\tx" -ItemType Directory -Force
icacls "D:\ArnoldCache" /grant "Everyone:(OI)(CI)F" /T
```
**Why:** Arnold texture caching to network drives causes crashes. Must be local.

### 6. Service Configuration
- Auto-upgrade: **Disabled** (manual upgrades only)
- Auto-configuration: **Disabled** (manual worker configs)
- Remote control: **Blocked** (security measure)
- Worker launch: **Enabled** (starts when service starts)

---

## Bulk Deployment

Deploy to multiple machines using PowerShell remoting:

```powershell
# Define target machines
$machines = @(
    "ROOM400-PC01",
    "ROOM400-PC02",
    "ROOM400-PC03",
    "ROOM405-PC01",
    "ROOM405-PC02"
)

$roomNumber = "400"  # Adjust per room

# Deploy to all machines
foreach ($machine in $machines) {
    Write-Host "Installing Deadline on $machine..." -ForegroundColor Cyan

    Invoke-Command -ComputerName $machine -FilePath .\Install-DeadlineClient.ps1 `
        -ArgumentList $roomNumber

    Write-Host "Completed: $machine" -ForegroundColor Green
}

Write-Host "`nDeployment complete! Verify workers in Deadline Monitor." -ForegroundColor Yellow
```

### Room-Specific Deployment

```powershell
# Room 400 deployment
$room400Machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03")
foreach ($machine in $room400Machines) {
    Invoke-Command -ComputerName $machine -FilePath .\Install-DeadlineClient.ps1 `
        -ArgumentList "400"
}

# Room 405 deployment
$room405Machines = @("ROOM405-PC01", "ROOM405-PC02", "ROOM405-PC03")
foreach ($machine in $room405Machines) {
    Invoke-Command -ComputerName $machine -FilePath .\Install-DeadlineClient.ps1 `
        -ArgumentList "405"
}
```

---

## Prerequisites

**Network access:**
- Connectivity to `10.40.14.25` (Deadline/P4 server)
- SMB port 445 open
- HTTPS port 4433 open

**Credentials:**
- Administrator access to worker machines
- Service account passwords (csadmin400, csadmin405, csadmin406, csadmin407)

**Files on network share (`\\10.40.14.25\RenderSourceRepository\`):**
- `DeadlineClientInstallers\Deadline-10.4.2.2-windows-installer\DeadlineClient-10.4.2.2-windows-installer.exe`
- `DeadlineClientInstallers\Deadline10RemoteClient.pfx`

**PowerShell:**
- Run as Administrator
- ExecutionPolicy: RemoteSigned or Bypass

---

## Verification

After installation, verify the worker:

### Check Worker Service

```powershell
# Service status
Get-Service -Name "DeadlineLauncher10"

# Worker process
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}
```

**Expected:** Service running, worker process active.

### Check Configuration

```powershell
# Everyone permissions
icacls "C:\ProgramData\Thinkbox\Deadline10" | Select-String "Everyone"

# Network credentials
cmdkey /list | Select-String "10.40.14.25"

# Maya license
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')

# Arnold cache
Test-Path "D:\ArnoldCache\tx"
```

**Expected:** All checks pass.

### Test Network Access

```powershell
# UNC path access
Test-Path "\\10.40.14.25\RenderSourceRepository"
Test-Path "\\10.40.14.25\RenderOutputRepo"

# Write test
New-Item -Path "\\10.40.14.25\RenderOutputRepo\test-$env:COMPUTERNAME.txt" `
    -ItemType File -Value "Test from $env:COMPUTERNAME"
```

**Expected:** All paths accessible, write succeeds.

### Check Deadline Monitor

1. Open Deadline Monitor on the worker
2. Should connect to `10.40.14.25:4433` automatically
3. Switch to Workers panel
4. Find the worker in the list
5. Status should be **Idle** (green)

---

## Troubleshooting

### Worker Not Starting

**Diagnose:**
```powershell
# View service status
Get-Service -Name "DeadlineLauncher10"

# View recent logs
Get-Content "C:\ProgramData\Thinkbox\Deadline10\logs\deadlinelauncher*.log" -Tail 50
```

**Fix:**
```powershell
# Re-apply permissions
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

# Restart service
Restart-Service -Name "DeadlineLauncher10"
```

### Permission Errors in Logs

**Symptom:** Worker logs show "Access Denied" errors

**Fix:**
```powershell
# Grant Everyone permissions recursively
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

# Restart service
Restart-Service -Name "DeadlineLauncher10"
```

### Can't Access Network Paths

**Diagnose:**
```powershell
# Check credentials
cmdkey /list | Select-String "10.40.14.25"

# Test connectivity
ping 10.40.14.25
Test-NetConnection -ComputerName 10.40.14.25 -Port 445
```

**Fix:**
```powershell
# Re-add credentials
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

# Test access
Test-Path "\\10.40.14.25\RenderSourceRepository"
```

### Maya License Errors

**Diagnose:**
```powershell
# Check env var
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
```

**Fix:**
```powershell
# Set license server
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)

# Restart service (required for env var changes)
Restart-Service -Name "DeadlineLauncher10"
```

### Installation Fails

**Diagnose:**
```powershell
# Check installer exists
Test-Path "D:\DeadlineClient-10.4.2.2-windows-installer.exe"
Test-Path "D:\Deadline10RemoteClient.pfx"

# Check network access to installer source
Test-Path "\\10.40.14.25\RenderSourceRepository\DeadlineClientInstallers"
```

**Fix:**
```powershell
# Manually copy installer files
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d
Copy-Item "T:\DeadlineClientInstallers\Deadline-10.4.2.2-windows-installer\*" -Destination "D:\" -Recurse
net use T: /delete
```

---

## Manual Installation Steps

If the automated script fails, follow the manual installation guide:

See: [[Install Deadline Client]]

---

## Post-Deployment Checklist

After deploying to all machines:

### Worker Verification

```powershell
# Check all workers are online
$machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03")

foreach ($machine in $machines) {
    $status = Invoke-Command -ComputerName $machine -ScriptBlock {
        $service = Get-Service -Name "DeadlineLauncher10"
        $process = Get-Process -Name "deadlineworker" -ErrorAction SilentlyContinue

        [PSCustomObject]@{
            Machine = $env:COMPUTERNAME
            Service = $service.Status
            WorkerRunning = ($null -ne $process)
        }
    }

    $status | Format-Table -AutoSize
}
```

### Configuration Verification

```powershell
# Verify configuration on all workers
$machines = @("ROOM400-PC01", "ROOM400-PC02")

foreach ($machine in $machines) {
    Write-Host "`nChecking $machine..." -ForegroundColor Cyan

    Invoke-Command -ComputerName $machine -ScriptBlock {
        Write-Host "  Permissions: " -NoNewline
        $perms = icacls "C:\ProgramData\Thinkbox\Deadline10" | Select-String "Everyone"
        if ($perms) { Write-Host "OK" -ForegroundColor Green } else { Write-Host "FAIL" -ForegroundColor Red }

        Write-Host "  Credentials: " -NoNewline
        $creds = cmdkey /list | Select-String "10.40.14.25"
        if ($creds) { Write-Host "OK" -ForegroundColor Green } else { Write-Host "FAIL" -ForegroundColor Red }

        Write-Host "  License: " -NoNewline
        $license = [System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
        if ($license -eq "27000@jabba.ad.uiwtx.edu") {
            Write-Host "OK" -ForegroundColor Green
        } else {
            Write-Host "FAIL" -ForegroundColor Red
        }

        Write-Host "  Arnold Cache: " -NoNewline
        if (Test-Path "D:\ArnoldCache\tx") {
            Write-Host "OK" -ForegroundColor Green
        } else {
            Write-Host "FAIL" -ForegroundColor Red
        }
    }
}
```

### Test Render

Submit a simple test job to verify the farm:

1. Open Deadline Monitor
2. Submit a test job (CommandLine plugin):
   - Executable: `cmd.exe`
   - Arguments: `/c echo Test render from %COMPUTERNAME% && ping 10.40.14.25 -n 2`
   - Frames: 1-5
3. Monitor job completion
4. Verify all workers picked up tasks

---

## Configuration Summary

After successful installation, each worker has:

- ✅ Deadline Client 10.4.2.2 installed
- ✅ Connected to `10.40.14.25:4433` via HTTPS/TLS
- ✅ Worker running as `csadmin[room#]` service
- ✅ "Everyone" permissions on `C:\ProgramData\Thinkbox\Deadline10\`
- ✅ UNC path credentials stored (no drive mapping needed)
- ✅ Maya license env var: `ADSKFLEX_LICENSE_FILE=27000@jabba.ad.uiwtx.edu`
- ✅ Local Arnold cache: `D:\ArnoldCache\tx`
- ✅ Auto-upgrade disabled
- ✅ Worker appears in Deadline Monitor as Idle

---

## Usage Tips

### Scene Configuration

Artists must configure Maya scenes for the render farm:

**Set UNC paths in Maya projects:**
- Project: `\\10.40.14.25\RenderSourceRepository\25_26\NLG\prod\...`
- Images: `\\10.40.14.25\RenderOutputRepo\ProjectName\images`

**Set Arnold cache (MEL):**
```mel
setAttr "defaultArnoldRenderOptions.autotx" 1;
setAttr -type "string" defaultArnoldRenderOptions.texture_auto_tx_path "D:/ArnoldCache/tx";
```

### Job Submission

When submitting Deadline jobs:
- ✅ Enable "Local Rendering" (more stable, faster)
- ✅ Set output to UNC path: `\\10.40.14.25\RenderOutputRepo\...`
- MayaBatch plugin: Optional (works either way)

### P4 Sync Workflow

After submitting scene changes to Perforce:
```powershell
# Sync server with latest P4 changes
T:\Utility\P4Sync.ps1

# Wait for sync to complete
Start-Sleep -Seconds 5

# Then submit Deadline job
```

---

## Related Documentation

- [[Install Deadline Client]] - Detailed manual installation guide
- [[What Is Deadline]] - System overview and architecture
- [[Testing UNC Path Method]] - UNC path validation and troubleshooting
- [[Network Drive Mounting Troubleshooting]] - Legacy troubleshooting (archived)
- [[__UPDATE__Deploying Deadline as a Service]] - Alternative deployment methods (archived)

---

**Last Updated:** 2025-12-02
**Deadline Version:** 10.4.2.2
**PowerShell Version:** 5.1+
**Tested On:** Windows 10/11 lab machines (Rooms 400, 405, 406, 407)
