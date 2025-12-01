---

---
---
### Description
Documentation for UIW 3D Program Deadline render farm. Technical docs include:

- **README.md** - Overview and quick reference
- **install.md** - Client installation steps
- **config.md** - SYSTEM drive mounts and license config
- **workflow.md** - Daily operations and render submission
- **troubleshoot.md** - Common issues and fixes
---
# Deadline Client Installation
---
## Network Configuration
Mount repository drive:

```powershell
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d /persistent:yes
```

---
## Installation
1. Copy installer files from T: to D:
	1. `DeadlineClient-10.4.1.6-windows-installer.exe`
	2. `Deadline10RemoteClient.pfx`

2. Run installer as Administrator

3. Installation settings:
	1. **Install Type**: Client
	2. **Connection Type**: Remote Connection Server
	3. **Server**: `10.40.14.25:4433`
	4. **Certificate**: `D:\Deadline10RemoteClient.pfx`
	5. **Certificate Password**: `uiw3d`

4. Launcher configuration:
	1. Enable: Launch Worker When Launcher Starts
	2. Enable: Install Launcher As Service
	3. Account: `.\csadmin[room#]` (400, 405, 406, or 407)
	4. Disable: Auto Upgrade

5. Complete installation

---
## Post-Install Configuration

### Worker Folder Permissions
Grant service account access to worker directory:

```powershell
$account = ".\csadmin[room#]"
icacls "C:\ProgramData\Thinkbox\Deadline10\workers" /grant "${account}:(OI)(CI)F" /T
```

### Restart Service

```powershell
Restart-Service -Name "DeadlineLauncher10"
```

## Verification

Check worker is running:

```powershell
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}
```

Open Deadline Monitor - should connect to `10.40.14.25:4433`.

---

# System Configuration

## Network Drives (SYSTEM Level)
Render services require drives mounted as SYSTEM user.

### Mount Procedure
Using PsExec:
```powershell
# Launch SYSTEM shell
psexec -i -s cmd.exe

# Mount drives
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d /persistent:yes
net use R: \\10.40.14.25\RenderOutputRepo /user:perforce uiw3d /persistent:yes
```

### Verify

```batch
net use
```

Expected: T: and R: mapped to `\\10.40.14.25\...`

## Autodesk License
Set environment variable (System level):

```
Variable: ADSKFLEX_LICENSE_FILE
Value: 27000@jabba.ad.uiwtx.edu
```

PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)
```

Restart Deadline service after setting.

# Automated Installation

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

Tags