---
tags:
  - Installation
  - QuickStart
status: Good
---
# Deadline Worker - Quick Install Guide
## Step 1: Copy Installer Files
 
Open PowerShell as Administrator:
 
```powershell
# Mount network share
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d

# Make Deadline Directory Folder
mkdir D:\Deadline 

# Future me...I need to make sure the above "mkdir D:\Deadline" first checks if it has that folder made and conent needed, and if not, make it then do the below.

# Copy files to D:\
Copy-Item "T:\Utility\DeadlineClientInstallers\Deadline-10.4.1.6-windows-installer\DeadlineClient-10.4.1.6-windows-installer.exe" -Destination "D:\Deadline\"
Copy-Item "T:\Utility\DeadlineClientInstallers\Deadline10RemoteClient.pfx" -Destination "D:\Deadline\"
 
# Unmount
net use T: /delete
```
 
---
## Step 2: Run Installer
 
1. Launch `D:\DeadlineClient-10.4.2.2-windows-installer.exe`
2. Next → Accept → Next → **Client** → Next
3. **Remote Connection Server** → Next
4. Host: `10.40.14.25` | Port: `4433` → Next
5. Certificate: `D:\Deadline10RemoteClient.pfx` | Password: `uiw3d` → Next
6. Configure:
   -  Launch Worker When Launcher Starts
   -  Install Launcher As Service
   - Account: `.\csadmin[room#]`(.\csadmin400) (enter password: Adam12-angd)
	   - Future me needs to automate this or create a prompt to select the room you're in as all the passwords are the same.
   - **Block Remote Control**
   - Next
1. Uncheck **all** auto options (Auto Configuration, Auto Upgrade) → Next
2. Install → Wait → Finish
 
---
## Step 3: Configure Permissions
 
```powershell
# Grant Everyone permissions (CRITICAL)
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T
```
 
---
## Step 4: Store Network Credentials
 
```powershell
# Store UNC path credentials
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```
 
---
## Step 5: Set Maya License
 
```powershell
# Set environment variable
[System.Environment]::SetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', '27000@jabba.ad.uiwtx.edu', 'Machine')
```
 
---
## Step 6: Create Arnold Cache
 
```powershell
# Create local cache directory
New-Item -Path "D:\ArnoldCache\tx" -ItemType Directory -Force
icacls "D:\ArnoldCache" /grant "Everyone:(OI)(CI)F" /T
```
 
---
## Step 7: Restart Service
 
```powershell
# Restart Deadline
Restart-Service -Name "Deadline 10 Launcher Service"

# Wait for worker to start
Start-Sleep -Seconds 10
```
 
---
## Verification
 
```powershell
# Check worker is running
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}
 
# Check network access
Test-Path "\\10.40.14.25\RenderSourceRepository"
 
# Check credentials
cmdkey /list | Select-String "10.40.14.25"
 
# Check license
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
 
# Check Arnold cache
Test-Path "D:\ArnoldCache\tx"
```
 
**All checks should pass.** Open Deadline Monitor → Worker should appear as **Idle** (green).
 
---
## Troubleshooting
 
**Worker not running:**

```powershell
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T
Restart-Service -Name "DeadlineLauncher10"
```
 
**Can't access network:**

```powershell
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```
 
**License errors:**

```powershell
[System.Environment]::SetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', '27000@jabba.ad.uiwtx.edu', 'Machine')

Restart-Service -Name "DeadlineLauncher10"
```
 
---
## Done
Worker is configured. For detailed documentation see [[What Is Deadline]].

 