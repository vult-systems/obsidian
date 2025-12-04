---
tags: [Deadline, Testing, Documentation]
status: Good
---

# UNC Path Method - SUCCESSFUL ✅

Testing UNC path access instead of mapped drives for Deadline Workers. **This method has been validated and is now the recommended approach.**

---

## Test Results

**Status:** ✅ **SUCCESS - Working in Production**

**Date Tested:** 2025-12-02

**Configuration:**
- UNC Paths: `\\10.40.14.25\RenderSourceRepository\...`
- "Everyone" permissions on `C:\ProgramData\Thinkbox\Deadline10\`
- Local Arnold cache: `D:\ArnoldCache\tx`
- Local Rendering: Enabled
- Maya license env var: `ADSKFLEX_LICENSE_FILE=27000@jabba.ad.uiwtx.edu`

**Outcome:**
- ✅ Workers access UNC paths without drive mapping
- ✅ Maya renders successfully with Arnold
- ✅ Frames write to network output directory
- ✅ No permission errors
- ✅ No "path not found" errors
- ✅ Works with and without MayaBatch plugin

---

## Why UNC Paths?

**Problems with mapped drives:**
- Require scheduled tasks to mount at startup
- Can fail after Windows updates
- Complex credential management for SYSTEM account
- Troubleshooting is difficult

**UNC path benefits:**
- No mounting or scheduled tasks needed
- More reliable for Windows services
- One-time credential setup via `cmdkey`
- Simpler troubleshooting
- Works universally across all service accounts

**Zero server changes required** - just worker-side configuration.

---

## Complete Working Configuration

### Step 1: Store Credentials

Run as Administrator on worker machine:

```powershell
# Store credentials for UNC path access
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

# Verify credential stored
cmdkey /list | Select-String "10.40.14.25"
```

**Expected output:** `Target: 10.40.14.25 Type: Domain Password User: perforce`

### Step 2: Set Everyone Permissions

Critical for Worker service to write logs and temp files:

```powershell
# Grant Everyone full control on Deadline folder
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

# Verify permissions
icacls "C:\ProgramData\Thinkbox\Deadline10\workers" | Select-String "Everyone"
```

**Expected output:** `Everyone:(OI)(CI)F`

### Step 3: Create Local Arnold Cache

Arnold texture cache must be local (not network):

```powershell
# Create cache directory
New-Item -Path "D:\ArnoldCache\tx" -ItemType Directory -Force

# Grant permissions
icacls "D:\ArnoldCache" /grant "Everyone:(OI)(CI)F" /T
```

### Step 4: Set Maya License Environment Variable

System-wide environment variable:

```powershell
# Set license server
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)

# Verify
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
```

**Expected output:** `27000@jabba.ad.uiwtx.edu`

### Step 5: Configure Maya Scene

In Maya scene file, set Arnold cache to local directory:

```mel
# Set Arnold texture cache to local drive
setAttr "defaultArnoldRenderOptions.autotx" 1;
setAttr -type "string" defaultArnoldRenderOptions.texture_auto_tx_path "D:/ArnoldCache/tx";
```

**Set project paths to UNC:**
- Project root: `\\10.40.14.25\RenderSourceRepository\25_26\NLG\prod\lyt\act01`
- Output images: `\\10.40.14.25\RenderOutputRepo\NLG\act01\images`

### Step 6: Restart Deadline Worker

Apply all configuration changes:

```powershell
# Restart Deadline service
Restart-Service -Name "DeadlineLauncher10"

# Wait for worker to start
Start-Sleep -Seconds 10

# Verify worker is running
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}
```

### Step 7: Submit Job with Local Rendering

In Deadline job submission dialog:
- ✅ **Enable Local Rendering** (checkbox)
- Output directory: `\\10.40.14.25\RenderOutputRepo\NLG\act01\images`
- MayaBatch plugin: Optional (works either way)

### Step 8: Sync P4 Workspace (If Using Perforce)

After making scene changes and submitting to P4:

```powershell
# Trigger server sync
T:\Utility\P4Sync.ps1

# Wait for sync to complete
Start-Sleep -Seconds 5
```

---

## Verification Checklist

### Network Access Test

```powershell
# Test UNC path connectivity
Test-Path "\\10.40.14.25\RenderSourceRepository"
Test-Path "\\10.40.14.25\RenderOutputRepo"

# List contents
Get-ChildItem "\\10.40.14.25\RenderSourceRepository\25_26" | Select-Object -First 5

# Test write access
New-Item -Path "\\10.40.14.25\RenderOutputRepo\test-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt" `
    -ItemType File -Value "Write test from $env:COMPUTERNAME"
```

**Expected:** All commands succeed without errors.

### Permission Verification

```powershell
# Check Everyone permissions
icacls "C:\ProgramData\Thinkbox\Deadline10" | Select-String "Everyone"

# Check Arnold cache exists
Test-Path "D:\ArnoldCache\tx"

# Check credentials stored
cmdkey /list | Select-String "10.40.14.25"

# Check Maya license env var
[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')
```

### Worker Status Check

```powershell
# Check worker service
Get-Service -Name "DeadlineLauncher10"

# Check worker process
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}

# View recent logs
Get-Content "C:\ProgramData\Thinkbox\Deadline10\logs\deadlineworker*.log" -Tail 50
```

### Render Test

1. Open simple Maya scene
2. Set project to UNC path: `\\10.40.14.25\RenderSourceRepository\TestProject`
3. Set images output to: `\\10.40.14.25\RenderOutputRepo\TestProject\images`
4. Set Arnold cache to: `D:/ArnoldCache/tx`
5. Submit to Deadline with Local Rendering enabled
6. Monitor job in Deadline Monitor

**Success criteria:**
- ✅ Job starts rendering
- ✅ Worker accesses scene assets via UNC paths
- ✅ Frames render successfully
- ✅ Frames write to network output directory
- ✅ No "path not found" errors
- ✅ No "access denied" errors
- ✅ No Arnold crashes

---

## What Fixed the Initial Problems

### Problem 1: Network Path Access
**Solution:** UNC paths with stored credentials (`cmdkey`)
- No scheduled tasks required
- No drive mapping complexity
- Direct SMB access

### Problem 2: Worker Permission Errors
**Solution:** "Everyone" permissions on `C:\ProgramData\Thinkbox\Deadline10\`
- Worker service can write logs
- Worker can cache job data
- Worker can create temp files

### Problem 3: Arnold Crashes
**Solution:** Local Arnold cache (`D:\ArnoldCache\tx`)
- Network caching caused crashes (exit code -1073741819)
- Local cache is fast and reliable
- Set via Arnold render settings in Maya

### Problem 4: Local Rendering Stability
**Solution:** Enable "Local Rendering" in Deadline submission
- Renders to local temp first
- Copies completed frame to network
- Reduces network I/O during rendering
- More stable than direct network writes

### Problem 5: Maya License Errors
**Solution:** System-wide env var `ADSKFLEX_LICENSE_FILE`
- Maya finds license server automatically
- Persists across service restarts
- Set at Machine level (not user level)

### Problem 6: Outdated Scene Files
**Solution:** P4 Sync workflow
- Run `T:\Utility\P4Sync.ps1` after submitting changes
- Triggers listener service on server
- Ensures workers have latest files

---

## Rollout Status

**Current deployment:**
- ✅ UNC paths validated on test worker
- ✅ Production rendering successful
- ✅ No issues with multiple concurrent jobs

**Next steps:**
- Deploy configuration to all lab machines
- Update team documentation
- Remove references to mapped drives (T:, R:)

---

## Deployment to All Machines

Use PowerShell remoting to deploy configuration:

```powershell
$machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03", "ROOM405-PC01")

$setupScript = {
    # Store credentials
    cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

    # Set Everyone permissions
    icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

    # Create Arnold cache
    New-Item -Path "D:\ArnoldCache\tx" -ItemType Directory -Force
    icacls "D:\ArnoldCache" /grant "Everyone:(OI)(CI)F" /T

    # Set Maya license
    [System.Environment]::SetEnvironmentVariable(
        'ADSKFLEX_LICENSE_FILE',
        '27000@jabba.ad.uiwtx.edu',
        'Machine'
    )

    # Restart Deadline service
    Restart-Service -Name "DeadlineLauncher10"
}

foreach ($machine in $machines) {
    Write-Host "Configuring $machine..."
    Invoke-Command -ComputerName $machine -ScriptBlock $setupScript
}

Write-Host "Deployment complete!"
```

---

## Comparison: UNC vs Mapped Drives

| Feature | UNC Paths ✅ | Mapped Drives ❌ |
|---------|-------------|-----------------|
| **Setup Complexity** | Simple (cmdkey) | Complex (scheduled task) |
| **Reliability** | High | Medium (can fail after updates) |
| **Service Account Support** | Native | Requires workarounds |
| **Maintenance** | Minimal | Regular troubleshooting |
| **Windows Updates** | Unaffected | Can break mounts |
| **Troubleshooting** | Easy | Difficult |
| **Performance** | Same | Same |

**Verdict:** UNC paths are simpler, more reliable, and require less maintenance.

---

## Troubleshooting

### Can't Access UNC Path

```powershell
# Check network connectivity
ping 10.40.14.25
Test-NetConnection -ComputerName 10.40.14.25 -Port 445

# Check credentials
cmdkey /list | Select-String "10.40.14.25"

# Re-add credentials if missing
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```

### Worker Can't Write to Output Directory

```powershell
# Test write access
New-Item -Path "\\10.40.14.25\RenderOutputRepo\test.txt" -ItemType File -Value "test"

# If fails, check SMB share permissions on server (Linux):
# sudo chmod 775 /path/to/RenderOutputRepo
# sudo chown -R perforce:perforce /path/to/RenderOutputRepo
```

### Arnold Still Crashing

```powershell
# Verify Arnold cache is local
# In Maya scene, check:
getAttr "defaultArnoldRenderOptions.texture_auto_tx_path"
# Should return: D:/ArnoldCache/tx

# Verify Local Rendering is enabled in Deadline submission
# Check job properties in Monitor
```

### Worker Logs Show Permission Errors

```powershell
# Re-apply Everyone permissions
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T

# Restart service
Restart-Service -Name "DeadlineLauncher10"
```

---

## Notes

- **Both methods access same files:** `T:\file.txt` and `\\10.40.14.25\RenderSourceRepository\file.txt` are identical
- **Other machines unaffected:** Machines can use different methods simultaneously
- **No server changes:** All configuration is worker-side only
- **Credentials persist:** Stored in Windows Credential Manager, survive reboots
- **Service account agnostic:** Works for SYSTEM, csadmin, or any service account

---

## Related Documentation

- [[Install Deadline Client]] - Complete installation guide
- [[What Is Deadline]] - System overview with UNC path configuration
- [[Automated Installation]] - Bulk deployment script
- [[Network Drive Mounting Troubleshooting]] - Legacy mapped drive troubleshooting (archived)
- [[__UPDATE__Deploying Deadline as a Service]] - Scheduled task method (archived)

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-12-02
**Tested By:** Technical Director
**Validated:** Maya + Arnold rendering on Deadline workers
