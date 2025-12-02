---

---
---
### Description
Using PowerShell we can automated the process of setting up Deadline in our labs. 

---
## Quick Install

Run as Administrator:

```powershell
.\Install-DeadlineClient.ps1 -RoomNumber 400
```

Replace 400 with your room number (400, 405, 406, or 407).

## What It Does

1. Maps T: drive to `\\10.40.14.25\RenderSourceRepository`
2. Copies installer and certificate to D:\
3. Runs silent installation with correct settings
4. Configures worker folder permissions
5. Restarts Deadline service
6. Verifies worker is running

## Manual Configuration Still Needed

After automated install, you still need to:

### Set License Variable (one-time per machine)

```powershell
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)
```

### Mount Drives as SYSTEM (one-time per machine)

**Use Scheduled Task method** (PsExec method is unreliable):

```powershell
# Create mount script
New-Item -Path "C:\Scripts" -ItemType Directory -Force
Set-Content -Path "C:\Scripts\MountDrives.ps1" -Value @'
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
net use T: \\10.40.14.25\RenderSourceRepository /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /persistent:yes
Add-Content -Path "C:\Scripts\mount-log.txt" -Value "$(Get-Date): Drives mounted"
'@

# Create scheduled task (runs at startup as SYSTEM)
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\Scripts\MountDrives.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "MountRenderDrives" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force

# Test immediately
Start-ScheduledTask -TaskName "MountRenderDrives"
Start-Sleep -Seconds 2
net use
```

## Bulk Deployment

Install on multiple machines via PSRemoting:

```powershell
$machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03")
$roomNumber = "400"

foreach ($machine in $machines) {
    Invoke-Command -ComputerName $machine -FilePath .\Install-DeadlineClient.ps1 `
        -ArgumentList $roomNumber
}
```

## Prerequisites

- Administrator access
- Network access to `10.40.14.25`
- Service account password set (contact TD if needed)

## Troubleshooting

If worker doesn't start, manually set permissions:

```powershell
icacls "C:\ProgramData\Thinkbox\Deadline10\workers" /grant ".\csadmin[room#]:(OI)(CI)F" /T
Restart-Service -Name "DeadlineLauncher10"
```


---
Status
#Good

Related
[[What Is Deadline]] [[../../02_Technical/PowerShell/What is PowerShell|What is PowerShell]]

Tags
[[../../05_Utility/Tags/Deadline|Deadline]] [[../../05_Utility/Tags/PowerShell|PowerShell]] [[../../05_Utility/Tags/Documentation|Documentation]]
