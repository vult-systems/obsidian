---
tags: [Deadline, Installation, Documentation]
status: Good
---

# Deadline Client Installation Guide

Complete installation procedure for Deadline 10.4.2.2 workers in UIW 3D labs.

## Overview

This guide covers:
- Initial setup and prerequisites
- Client installation
- Post-install configuration (critical permissions and settings)
- Verification steps

**Estimated time:** 15-20 minutes per machine

---

## Prerequisites

- Administrator access to the worker machine
- Network access to `10.40.14.25` (Deadline/P4 server)
- Room-specific csadmin account credentials (400, 405, 406, or 407)

---

## Step 1: Prepare Installation Files

### Mount Network Share

Open PowerShell as Administrator:

```powershell
# Temporary mount to access installer (only needed during installation)
net use T: \\10.40.14.25\RenderSourceRepository /user:perforce uiw3d
```

### Copy Files to Local Machine

```powershell
# Copy installer and certificate to D:\
Copy-Item "T:\DeadlineClientInstallers\Deadline-10.4.2.2-windows-installer\DeadlineClient-10.4.2.2-windows-installer.exe" -Destination "D:\"
Copy-Item "T:\DeadlineClientInstallers\Deadline10RemoteClient.pfx" -Destination "D:\"
```

---

## Step 2: Run Installer

1. **Launch installer:** `D:\DeadlineClient-10.4.2.2-windows-installer.exe`

2. **Welcome screen:** Click Next

3. **License Agreement:** Accept

4. **Install Location:** Use default `C:\Program Files\Thinkbox\Deadline10\` (click Next)

5. **Install Type:** Select **Client**

6. **Connection Type:** Select **Remote Connection Server (Recommended)**

7. **Remote Connection Server Settings:**
   - **Host Name:** `10.40.14.25`
   - **Port:** `4433`
   - Click Next

8. **RCS TLS Certificate:**
   - **Certificate Path:** Browse to `D:\Deadline10RemoteClient.pfx`
   - **Certificate Password:** `uiw3d`
   - Click Next

9. **Deadline Launcher Setup:**
   - ✅ **Launch Worker When Launcher Starts** (checked)
   - ✅ **Install Launcher As Service** (checked)
   - **Service Account:** `.\csadmin[room#]` (e.g., `.\csadmin400`)
     - Enter the csadmin password for your room
   - **Remote Control:** Select **Block Remote Control**
   - Click Next

10. **Client Setup:**
    - ❌ **Enable Auto Configuration** (unchecked)
    - ❌ **Allow Auto Upgrade** (unchecked - IMPORTANT)
    - Click Next

11. **Ready to Install:** Click Install

12. Wait for installation to complete (3-5 minutes)

13. **Finish:** Click Finish

---

## Step 3: Post-Install Configuration (CRITICAL)

These steps are **mandatory** for proper operation.

### 3.1 Set "Everyone" Permissions on Deadline Folder

This fixes permission issues when the Worker runs as a service:

```powershell
# Grant Everyone full control to Deadline workers directory
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

# Verify permissions
icacls "C:\ProgramData\Thinkbox\Deadline10\workers"
```

**Why:** The Deadline Worker service needs to write logs, job data, and temp files. Without "Everyone" permissions, it fails silently.

### 3.2 Store Network Credentials

Store credentials for UNC path access (no drive mapping needed):

```powershell
# Store credentials for accessing render repository
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

# Verify credential stored
cmdkey /list | Select-String "10.40.14.25"
```

**Why:** Workers access assets via UNC paths like `\\10.40.14.25\RenderSourceRepository\...`

### 3.3 Set Maya License Environment Variable

Configure system-wide Maya licensing:

```powershell
# Set license server environment variable
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)

# Verify it was set
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
```

**Why:** Maya needs to find the license server when rendering.

### 3.4 Create Local Arnold Cache Directory

Arnold texture cache must be local, not on network:

```powershell
# Create local cache directory
New-Item -Path "D:\ArnoldCache\tx" -ItemType Directory -Force

# Grant full permissions
icacls "D:\ArnoldCache" /grant "Everyone:(OI)(CI)F" /T
```

**Why:** Arnold `.tx` texture caching to network drives causes crashes. Local cache is fast and reliable.

### 3.5 Restart Deadline Service

Apply all configuration changes:

```powershell
# Restart the Deadline Launcher service
Restart-Service -Name "DeadlineLauncher10"

# Wait for worker to start
Start-Sleep -Seconds 10
```

---

## Step 4: Verification

### Check Worker Process

```powershell
# Verify deadlineworker.exe is running
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}
```

**Expected:** Process listed with ID and memory usage.

### Check Network Access

```powershell
# Test UNC path access
Test-Path "\\10.40.14.25\RenderSourceRepository"
Get-ChildItem "\\10.40.14.25\RenderSourceRepository" | Select-Object -First 5
```

**Expected:** Returns `True` and lists directories/files.

### Open Deadline Monitor

1. Search for "Deadline Monitor" in Start menu
2. Launch application
3. Should automatically connect to `10.40.14.25:4433`

**If connection fails:**
- Click OK on error dialog
- Tools → Change Repository
- Enter passphrase: `uiw3d`
- Advanced TLS Options: Use default (first option)
- Click OK

### Verify Worker in Monitor

In Deadline Monitor:
1. Switch to **Workers** panel (bottom tabs)
2. Look for your machine name in the list
3. Status should be **Idle** (green) or **Rendering** (if jobs are queued)

---

## Troubleshooting

### Worker Not Appearing in Monitor

**Check service is running:**
```powershell
Get-Service -Name "DeadlineLauncher10"
```

**If stopped, start it:**
```powershell
Start-Service -Name "DeadlineLauncher10"
```

### Permission Errors in Worker Logs

**View worker logs:**
```powershell
Get-Content "C:\ProgramData\Thinkbox\Deadline10\logs\deadlineworker*.log" -Tail 50
```

**If you see "Access Denied":**
```powershell
# Re-apply Everyone permissions
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T
Restart-Service -Name "DeadlineLauncher10"
```

### Can't Access Network Paths

**Verify credentials:**
```powershell
cmdkey /list | Select-String "10.40.14.25"
```

**If missing, re-add:**
```powershell
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```

### Maya License Errors

**Verify environment variable:**
```powershell
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
```

**Should return:** `27000@jabba.ad.uiwtx.edu`

**If wrong/missing, set it:**
```powershell
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)
Restart-Service -Name "DeadlineLauncher10"
```

---

## Configuration Summary

After successful installation, the worker should have:

- ✅ Deadline Client 10.4.2.2 installed
- ✅ Worker running as `csadmin[room#]` service account
- ✅ "Everyone" permissions on `C:\ProgramData\Thinkbox\Deadline10\`
- ✅ Network credentials stored for `10.40.14.25`
- ✅ Maya license env var: `ADSKFLEX_LICENSE_FILE=27000@jabba.ad.uiwtx.edu`
- ✅ Local Arnold cache: `D:\ArnoldCache\tx`
- ✅ Auto-upgrade disabled
- ✅ Worker appears in Deadline Monitor as Idle

---

## Next Steps

1. **Configure Maya scenes** to use UNC paths:
   - Assets: `\\10.40.14.25\RenderSourceRepository\25_26\...`
   - Output: `\\10.40.14.25\RenderOutputRepo\...`

2. **Set Arnold cache path** in Maya scenes:
   ```mel
   setAttr "defaultArnoldRenderOptions.autotx" 1;
   setAttr -type "string" defaultArnoldRenderOptions.texture_auto_tx_path "D:/ArnoldCache/tx";
   ```

3. **Enable Local Rendering** when submitting Deadline jobs (renders locally, then copies to network)

4. **P4 Sync Workflow:** After submitting scene changes to Perforce, run `T:\Utility\P4Sync.ps1` to sync the server

---

## Related Documentation

- [[What Is Deadline]] - Deadline system overview
- [[Automated Installation]] - Bulk deployment script
- [[Maya Deadline Submission]] - Submitting render jobs from Maya

---

**Last Updated:** 2025-12-02
**Deadline Version:** 10.4.2.2
**Tested On:** Windows 10/11 lab machines (Rooms 400, 405, 406, 407)
