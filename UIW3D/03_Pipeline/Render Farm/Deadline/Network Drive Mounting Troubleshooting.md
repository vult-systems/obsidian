---

---
### Description
Troubleshooting guide for network drive mounting issues on Deadline Worker machines. Common problems and solutions when render services can't access network storage.

---
## Quick Diagnosis

### Check Current Mounts

```powershell
# View all mapped drives
net use

# Check scheduled task status
Get-ScheduledTask -TaskName "MountRenderDrives" | Select-Object TaskName, State, LastRunTime, LastTaskResult

# View mount log
Get-Content C:\Scripts\mount-log.txt -Tail 10
```

### Test Network Connectivity

```powershell
# Ping server
ping 10.40.14.25

# Test SMB port
Test-NetConnection -ComputerName 10.40.14.25 -Port 445

# List available shares
net view \\10.40.14.25
```

---
## Common Issues

### Issue 1: "Network Admin Denied Access"

**Symptom:**
- Drives mount for logged-in users
- Services can't access mapped drives
- Deadline Worker shows "path not found" errors

**Cause:**
Network credentials stored in user session, not available to SYSTEM account.

**Solution:**
Use scheduled task method to mount drives as SYSTEM with `cmdkey` for credential storage.

See [[__UPDATE__Deploying Deadline as a Service]] for complete solution.

### Issue 2: Drives Disappear After Reboot

**Symptom:**
- Drives work after manual mounting
- Lost after reboot or Windows updates
- Have to manually remount frequently

**Cause:**
Using PsExec or user-session mounting instead of persistent scheduled task.

**Solution:**
Create scheduled task that runs at startup:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Scripts\MountDrives.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "MountRenderDrives" -Action $Action -Trigger $Trigger -Principal $Principal -Force
```

### Issue 3: "Multiple Connections to Server Not Allowed"

**Symptom:**
```
Multiple connections to a server or shared resource by the same user, using more than one user name, are not allowed.
```

**Cause:**
Existing connection to the server with different credentials.

**Solution:**

```powershell
# View current connections
net use

# Disconnect existing connections to the server
net use \\10.40.14.25\IPC$ /delete
net use * /delete /y

# Remount with correct credentials
Start-ScheduledTask -TaskName "MountRenderDrives"
```

### Issue 4: Scheduled Task Fails to Run

**Symptom:**
- Task exists but drives aren't mounted
- LastTaskResult shows error code
- No entries in mount log

**Diagnosis:**

```powershell
# Check task history
Get-ScheduledTask -TaskName "MountRenderDrives" | Get-ScheduledTaskInfo

# View task event log
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'} -MaxEvents 50 |
    Where-Object {$_.Message -like "*MountRenderDrives*"}
```

**Common fixes:**

```powershell
# Ensure script exists
Test-Path C:\Scripts\MountDrives.ps1

# Fix permissions on script
icacls "C:\Scripts\MountDrives.ps1" /grant "SYSTEM:(RX)"

# Recreate task with correct settings
Unregister-ScheduledTask -TaskName "MountRenderDrives" -Confirm:$false
# Then run creation commands again
```

### Issue 5: "Access Denied" When Writing to Network Drive

**Symptom:**
- Drives mount successfully
- Can read files but can't write
- Render output fails to save

**Cause:**
SMB share permissions don't allow write access for the perforce user.

**Check permissions on the server:**

```bash
# On Ubuntu server (10.40.14.25)
ls -la /path/to/RenderOutputRepo
```

**Fix on server:**

```bash
# Grant write permissions
sudo chmod 775 /path/to/RenderOutputRepo
sudo chown -R perforce:perforce /path/to/RenderOutputRepo
```

**Verify from Windows:**

```powershell
# Test write access
New-Item -Path "T:\test.txt" -ItemType File -Value "test"
Remove-Item "T:\test.txt"
```

### Issue 6: Deadline Worker Can't See Mounted Drives

**Symptom:**
- `net use` shows drives mounted
- Deadline Worker still reports "path not found"
- Drives visible in File Explorer when logged in

**Cause:**
Deadline Worker service started before scheduled task ran.

**Solution:**

```powershell
# Restart Deadline service AFTER drives are mounted
Start-ScheduledTask -TaskName "MountRenderDrives"
Start-Sleep -Seconds 5
Restart-Service -Name "DeadlineLauncher10"

# Verify worker can see drives
Get-Process deadlineworker | Select-Object Id, Name
```

---
## Advanced Troubleshooting

### Verify SYSTEM Account Can Access Drives

Run PowerShell as SYSTEM to test:

```powershell
# Download PsExec (for testing only)
Invoke-WebRequest -Uri "https://live.sysinternals.com/PsExec64.exe" -OutFile "C:\Temp\PsExec64.exe"

# Launch PowerShell as SYSTEM
C:\Temp\PsExec64.exe -i -s powershell.exe

# In the SYSTEM PowerShell window:
net use
Get-ChildItem T:\
Get-ChildItem R:\
```

### Check Stored Credentials

```powershell
# View stored credentials (won't show passwords)
cmdkey /list

# Look for entry: Target: 10.40.14.25
```

### Monitor Task Execution

```powershell
# Enable detailed logging in mount script
$LogScript = @'
Start-Transcript -Path "C:\Scripts\mount-debug.log" -Append
Write-Host "$(Get-Date): Starting mount process"

cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
Write-Host "Credentials stored"

net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
Write-Host "T: drive result: $LASTEXITCODE"

net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes
Write-Host "R: drive result: $LASTEXITCODE"

net use
Stop-Transcript
'@

Set-Content -Path "C:\Scripts\MountDrives.ps1" -Value $LogScript

# Run task and check log
Start-ScheduledTask -TaskName "MountRenderDrives"
Start-Sleep -Seconds 3
Get-Content "C:\Scripts\mount-debug.log"
```

---
## Alternative Solutions

### Use UNC Paths Instead

Eliminate drive mapping entirely by configuring Deadline and Maya to use UNC paths:

**Advantages:**
- More reliable for services
- No scheduled task needed
- Automatic credential handling

**Setup:**

```powershell
# Store credentials once
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```

**Configure Deadline:**
- Asset Directories: `\\10.40.14.25\RenderSourceRepository\Assets`
- Output Directories: `\\10.40.14.25\RenderOutputRepo\Frames`

**Configure Maya Projects:**
- sourceimages: `\\10.40.14.25\RenderSourceRepository\Projects\ProjectName\sourceimages`
- images: `\\10.40.14.25\RenderOutputRepo\ProjectName\images`

### Manual Mount for Testing

For quick testing without rebooting:

```powershell
# Store credentials
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

# Mount drives
net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes

# Verify
net use
```

---
## Preventive Maintenance

### Regular Checks

Add to monthly maintenance routine:

```powershell
# Verify scheduled task is enabled
Get-ScheduledTask -TaskName "MountRenderDrives" |
    Where-Object {$_.State -ne "Ready"} |
    ForEach-Object {
        Write-Warning "Task not ready on $env:COMPUTERNAME"
    }

# Verify drives are mounted
$drives = @("T:", "R:")
foreach ($drive in $drives) {
    if (-not (Test-Path $drive)) {
        Write-Warning "$drive not mounted on $env:COMPUTERNAME"
    }
}
```

### After Windows Updates

Check mounts still work after major updates:

```powershell
# Verify and remount if needed
if (-not (Test-Path T:\)) {
    Start-ScheduledTask -TaskName "MountRenderDrives"
}
```

---
Status
#Good

Related
[[What Is Deadline]] [[__UPDATE__Deploying Deadline as a Service]] [[../../../02_Technical/PowerShell/What is PowerShell|What is PowerShell]]

Tags
[[../../../05_Utility/Tags/Deadline|Deadline]] [[../../../05_Utility/Tags/PowerShell|PowerShell]] [[../../../05_Utility/Tags/Documentation|Documentation]]
