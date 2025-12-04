How we finally got Deadline Worker running as a proper Windows service with persistent network drive access.

## The Problem

Our initial documentation recommended using PsExec to mount network drives as SYSTEM:

```powershell
psexec -i -s cmd.exe
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d /persistent:yes
```

**This approach failed** with "Network Admin Denied Access" errors because:

1. **Windows SMB security policies** prevent SYSTEM from using credentials stored via `net use`
2. **Mapped drives don't persist** across reboots or Windows updates reliably
3. **Service accounts can't access** user-session credential vaults
4. The Deadline Worker service (running as SYSTEM or csadmin) couldn't access the mapped drives

**Symptoms:**
- Drives mounted successfully when users were logged in
- Deadline Worker couldn't access T: or R: drives
- Render jobs failed with "path not found" errors
- Maya couldn't load assets from network storage

## The Solution

**Use Windows Scheduled Tasks** to mount drives at system startup with embedded credentials.

### Implementation

Create a PowerShell script that mounts drives:

```powershell
# C:\Scripts\MountDrives.ps1
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes
Add-Content -Path "C:\Scripts\mount-log.txt" -Value "$(Get-Date): Drives mounted"
```

Create scheduled task to run at startup as SYSTEM:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\Scripts\MountDrives.ps1"

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
    -LogonType ServiceAccount -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask -TaskName "MountRenderDrives" `
    -Action $Action -Trigger $Trigger -Principal $Principal `
    -Settings $Settings -Force
```

### Why This Works

1. **cmdkey stores credentials** in SYSTEM's credential vault (not user's)
2. **Scheduled task runs before user login**, ensuring drives are available system-wide
3. **SYSTEM account persists** - credentials survive reboots and updates
4. **Automatic retry** - scheduled task settings handle failures gracefully

## Configuration

### One-Time Setup Per Machine

Run as Administrator on each worker machine:

```powershell
# Create scripts directory
New-Item -Path "C:\Scripts" -ItemType Directory -Force

# Create mount script
Set-Content -Path "C:\Scripts\MountDrives.ps1" -Value @'
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes
Add-Content -Path "C:\Scripts\mount-log.txt" -Value "$(Get-Date): Drives mounted"
'@

# Create scheduled task
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Scripts\MountDrives.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "MountRenderDrives" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

# Test immediately
Start-ScheduledTask -TaskName "MountRenderDrives"
Start-Sleep -Seconds 3
net use
```

### Verification

Check drives are mounted:
```powershell
net use
```

Expected output:
```
Status       Local     Remote                    Network
-------------------------------------------------------------------------------
OK           T:        \\10.40.14.25\RenderSourceRepository  Microsoft Windows Network
OK           R:        \\10.40.14.25\RenderOutputRepo        Microsoft Windows Network
```

Check scheduled task:
```powershell
Get-ScheduledTask -TaskName "MountRenderDrives" | Select-Object TaskName, State
```

View mount log:
```powershell
Get-Content C:\Scripts\mount-log.txt -Tail 5
```

## Lessons Learned

### What Worked
1. **Scheduled tasks are more reliable** than PsExec or registry hacks
2. **cmdkey stores credentials persistently** for SYSTEM account
3. **Logging helps debugging** - always log mount success/failure
4. **Test immediately** with `Start-ScheduledTask` before rebooting

### What Didn't Work
- **PsExec + net use** - Fails on modern Windows due to SMB security
- **Registry manipulation** - Too fragile, breaks on Windows updates
- **Group Policy mappings** - Requires domain controller access
- **Service-specific user mappings** - Lost during service restarts

### Better Alternative: UNC Paths

For future projects, **skip drive mapping entirely**:

- Configure Deadline and Maya to use `\\10.40.14.25\RenderSourceRepository` directly
- Store credentials once: `cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d`
- More reliable, no startup dependencies, works for all services automatically

### Bulk Deployment

Deploy to multiple machines via PSRemoting:

```powershell
$machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03")

$setupScript = {
    New-Item -Path "C:\Scripts" -ItemType Directory -Force
    Set-Content -Path "C:\Scripts\MountDrives.ps1" -Value @'
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes
Add-Content -Path "C:\Scripts\mount-log.txt" -Value "$(Get-Date): Drives mounted"
'@

    $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Scripts\MountDrives.ps1"
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName "MountRenderDrives" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

    Start-ScheduledTask -TaskName "MountRenderDrives"
}

foreach ($machine in $machines) {
    Invoke-Command -ComputerName $machine -ScriptBlock $setupScript
}
```

[[../../../05_Utility/Tags/Deadline|Deadline]]
[[What Is Deadline]]
