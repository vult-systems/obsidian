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

```powershell
psexec -i -s cmd.exe
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /user:perforce uiw3d /persistent:yes
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
- PsExec downloaded for SYSTEM drive mounting

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
