---

---
### Description
Testing UNC path access instead of mapped drives for Deadline Workers. Single machine test before rollout.

---
## Why UNC Paths?

**Problems with mapped drives:**
- Require scheduled tasks to mount at startup
- Can fail after Windows updates
- Complex troubleshooting

**UNC path benefits:**
- No mounting needed
- More reliable for services
- One-time credential setup

**Zero server changes required** - just worker-side configuration.

---
## Test Procedure

### Step 1: Store Credentials

Run as Administrator on one worker machine:

```powershell
# Store credentials for SYSTEM account
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d

# Verify credential stored
cmdkey /list | Select-String "10.40.14.25"
```

### Step 2: Test Access

```powershell
# Test connectivity
Test-Path "\\10.40.14.25\RenderSourceRepository"
Test-Path "\\10.40.14.25\RenderOutputRepo"

# List contents
Get-ChildItem "\\10.40.14.25\RenderSourceRepository" | Select-Object -First 5
Get-ChildItem "\\10.40.14.25\RenderOutputRepo" | Select-Object -First 5

# Test write access
New-Item -Path "\\10.40.14.25\RenderOutputRepo\test-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt" -ItemType File -Value "Write test from $env:COMPUTERNAME"
```

**Expected:** All commands succeed without errors.

### Step 3: Configure Maya Project

In your Maya project, update paths to use UNC:

**Example project structure:**
```
Project: \\10.40.14.25\RenderSourceRepository\Projects\TestProject
sourceimages: \\10.40.14.25\RenderSourceRepository\Projects\TestProject\sourceimages
scenes: \\10.40.14.25\RenderSourceRepository\Projects\TestProject\scenes
images: \\10.40.14.25\RenderOutputRepo\TestProject\images
```

**Set in Maya:**
- File → Set Project → Browse to `\\10.40.14.25\RenderSourceRepository\Projects\TestProject`
- Or manually edit `workspace.mel` to use UNC paths

### Step 4: Restart Deadline Worker

```powershell
# Restart to ensure service picks up credentials
Restart-Service -Name "DeadlineLauncher10"

# Verify worker is running
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}

# Check in Deadline Monitor
# Worker should appear online and idle
```

### Step 5: Submit Test Render

1. Open simple Maya scene with basic geometry
2. Set render output path: `\\10.40.14.25\RenderOutputRepo\TestProject\images`
3. Submit to Deadline using UNC paths
4. Monitor job in Deadline Monitor

**Success criteria:**
- Job starts rendering
- Worker can access scene assets from `\\10.40.14.25\RenderSourceRepository`
- Frames write successfully to `\\10.40.14.25\RenderOutputRepo`
- No "path not found" errors

---
## Verification Checklist

After test render completes:

```powershell
# Check output frames exist
Get-ChildItem "\\10.40.14.25\RenderOutputRepo\TestProject\images"

# Check Deadline worker log for errors
Get-Content "C:\ProgramData\Thinkbox\Deadline10\logs\deadlineworker*.log" -Tail 50
```

**Green flags:**
- ✓ Frames rendered successfully
- ✓ No permission errors in logs
- ✓ Asset loading worked correctly
- ✓ Write operations completed

**Red flags:**
- ✗ "Access denied" errors
- ✗ "Path not found" errors
- ✗ Assets failed to load
- ✗ Can't write output frames

---
## If Test Succeeds

### Option 1: Keep This Machine on UNC
- Remove any scheduled mount tasks (no longer needed)
- Document which machines use UNC vs mapped drives
- Gradually migrate other machines

### Option 2: Rollout to All Machines

Deploy credentials to all workers:

```powershell
$machines = @("ROOM400-PC01", "ROOM400-PC02", "ROOM400-PC03")

foreach ($machine in $machines) {
    Invoke-Command -ComputerName $machine -ScriptBlock {
        cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
        Restart-Service -Name "DeadlineLauncher10"
    }
}
```

Update team documentation:
- Users must use UNC paths in Maya projects
- Remove references to T: and R: drive letters

---
## If Test Fails

### Troubleshoot

```powershell
# Check if credentials stored correctly
cmdkey /list

# Test from SYSTEM account (download PsExec first)
psexec -i -s powershell.exe
# In SYSTEM shell:
Test-Path "\\10.40.14.25\RenderSourceRepository"
Get-ChildItem "\\10.40.14.25\RenderSourceRepository"
```

### Common Issues

**Can't access UNC path:**
- Check network connectivity: `ping 10.40.14.25`
- Check SMB port: `Test-NetConnection -ComputerName 10.40.14.25 -Port 445`
- Verify credentials: `cmdkey /list`

**Deadline can't write output:**
- Check SMB share permissions on server
- Verify write test succeeded in Step 2

### Fallback to Mapped Drives

If UNC doesn't work, use scheduled task method from [[__UPDATE__Deploying Deadline as a Service]].

---
## Notes

- **Both methods access the same files** - `T:\file.txt` and `\\10.40.14.25\RenderSourceRepository\file.txt` are identical
- **Other machines unaffected** - they can keep using mapped drives during testing
- **No server changes** - all configuration is worker-side only
- **Credentials persist** - stored in Windows Credential Manager, survive reboots

---
Status
#InProgress

Related
[[What Is Deadline]] [[__UPDATE__Deploying Deadline as a Service]] [[Network Drive Mounting Troubleshooting]]

Tags
[[../../05_Utility/Tags/Deadline|Deadline]] [[../../05_Utility/Tags/Documentation|Documentation]]
