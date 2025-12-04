---
tags: [Deadline, Documentation, Overview]
status: Good
---

# Deadline Render Farm - UIW 3D Program

AWS Thinkbox Deadline 10.4.2.2 render farm documentation for the UIW 3D program.

## What Is Deadline?

Deadline is a render farm management system that distributes rendering tasks across multiple computers. Our setup consists of:

- **Server:** `10.40.14.25` (Ubuntu Server running MongoDB + Deadline Repository)
- **Workers:** Computer lab machines in rooms 400, 405, 406, and 407
- **Submitters:** Artist workstations running Maya, Blender, etc.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│  Deadline Server (10.40.14.25)                      │
│  ├─ MongoDB Database (job queue, worker status)     │
│  ├─ Repository (plugins, scripts, logs)             │
│  └─ Remote Connection Server (HTTPS on port 4433)   │
└─────────────────────────────────────────────────────┘
                         ▲
                         │ HTTPS
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
   │ Worker 1 │    │ Worker 2 │    │ Worker N │
   │ (Room400)│    │ (Room405)│    │ (RoomXXX)│
   └──────────┘    └──────────┘    └──────────┘
```

## How It Works

1. **Artist submits job** from Maya/Blender → Job enters queue in MongoDB
2. **Idle workers pull jobs** from queue → Each worker grabs available tasks
3. **Workers render frames** → Output written to network share
4. **Job completes** → Artist reviews rendered frames

## Network Architecture

All workers access shared storage via **UNC paths** (no drive mapping needed):

- **Source Repository:** `\\10.40.14.25\RenderSourceRepository`
  - Maya projects, scene files, textures, assets
  - Synced from Perforce via P4Sync listener service

- **Output Repository:** `\\10.40.14.25\RenderOutputRepo`
  - Rendered frames, logs, output files

**Key Point:** Workers use UNC paths directly. No T: or R: drive letters required.

---

## Quick Reference

### Installation
See: [[Install Deadline Client]]

**Summary:**
1. Install Deadline Client 10.4.2.2 as Windows service
2. Set "Everyone" permissions on `C:\ProgramData\Thinkbox\Deadline10\`
3. Store network credentials: `cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d`
4. Set Maya license: `ADSKFLEX_LICENSE_FILE=27000@jabba.ad.uiwtx.edu`
5. Create local Arnold cache: `D:\ArnoldCache\tx`

### Submitting Jobs

**From Maya:**
1. Set project to use UNC paths:
   - Project: `\\10.40.14.25\RenderSourceRepository\25_26\NLG\prod\...`
   - Images: `\\10.40.14.25\RenderOutputRepo\ProjectName\images`

2. Configure Arnold cache (in Maya scene):
   ```mel
   setAttr "defaultArnoldRenderOptions.autotx" 1;
   setAttr -type "string" defaultArnoldRenderOptions.texture_auto_tx_path "D:/ArnoldCache/tx";
   ```

3. Submit via Deadline Monitor or integrated submitter
   - ✅ Enable "Local Rendering" (renders locally, copies to network)
   - MayaBatch plugin: Optional (works either way)

4. After submitting scene changes to P4, sync the server:
   ```powershell
   T:\Utility\P4Sync.ps1
   ```

### Monitoring Jobs

**Deadline Monitor Application:**
- View job queue and status
- Monitor worker availability
- View render logs and errors
- Pause/resume/delete jobs

**Worker States:**
- **Idle** (green) - Available for work
- **Rendering** (blue) - Currently processing a task
- **Offline** (red) - Not connected to server
- **Stalled** (yellow) - Stuck on a task

---

## Components

### Server Components (10.40.14.25)

**MongoDB Database**
- Stores job queue, task status, worker configurations
- Port: 27100 (internal)

**Deadline Repository**
- File storage: `/opt/perforce/deadlineRepository/`
- Contains: plugins, scripts, job logs, auxiliary files
- Accessed via UNC: `\\10.40.14.25\RenderSourceRepository\deadline\`

**Remote Connection Server (RCS)**
- HTTPS endpoint: `10.40.14.25:4433`
- TLS certificate: `Deadline10RemoteClient.pfx`
- All workers connect via this (more secure than direct DB access)

**P4 Sync Listener**
- HTTP endpoint: `http://10.40.14.25:5005/sync`
- Triggered by `T:\Utility\P4Sync.ps1`
- Syncs Perforce workspace to `/opt/perforce/deadlineRenderSource/`

### Worker Components (Lab Machines)

**Deadline Launcher Service**
- Windows service: `DeadlineLauncher10`
- Runs as: `.\csadmin[room#]` account
- Starts/stops the Worker process

**Deadline Worker**
- Executable: `deadlineworker.exe`
- Connects to: `10.40.14.25:4433` (RCS via HTTPS)
- Renders jobs, reports status, writes logs

**Local Data Storage**
- Worker files: `C:\ProgramData\Thinkbox\Deadline10\workers\[WORKERNAME]\`
- Logs: `C:\ProgramData\Thinkbox\Deadline10\logs\`
- Arnold cache: `D:\ArnoldCache\tx\` (local, not network)

---

## Configuration Details

### Critical Settings

**1. Everyone Permissions**
```powershell
icacls "C:\ProgramData\Thinkbox\Deadline10" /grant "Everyone:(OI)(CI)F" /T
```
**Why:** Worker service needs write access to its own directories for logs and temp files.

**2. Network Credentials**
```powershell
cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d
```
**Why:** Workers access `\\10.40.14.25\...` UNC paths. Credentials must be stored for the service account.

**3. Maya License**
```powershell
[System.Environment]::SetEnvironmentVariable(
    'ADSKFLEX_LICENSE_FILE',
    '27000@jabba.ad.uiwtx.edu',
    'Machine'
)
```
**Why:** Maya needs to find the license server when rendering.

**4. Local Arnold Cache**
- Path: `D:\ArnoldCache\tx`
- Set in Maya scenes via Arnold render settings

**Why:** Arnold texture caching to network drives causes crashes. Must be local.

**5. Local Rendering**
- Enable in Deadline job submission
- Renders frames to local temp directory
- Copies completed frames to network output directory

**Why:** Improves render stability and speed. Network writes only happen when frame is complete.

### Optional Settings

**Auto Configuration:** Disabled
- Workers don't auto-configure from server settings
- Manual control over worker configs

**Auto Upgrade:** Disabled
- Prevents workers from auto-updating when repository version changes
- Manual upgrades only (controlled rollout)

**Remote Control:** Blocked
- Can't remotely control workers via Monitor
- Security measure for lab environments

---

## Workflow

### Daily Operations

**Starting a Render:**
1. Prepare Maya scene with UNC paths
2. Configure Arnold cache to D:\ArnoldCache\tx
3. Submit to P4 (if applicable)
4. Run `T:\Utility\P4Sync.ps1` to sync server
5. Submit job via Deadline Monitor
6. Enable "Local Rendering" in submission dialog
7. Monitor progress in Deadline Monitor

**Checking Worker Status:**
```powershell
# Check if worker is running
Get-Process | Where-Object {$_.Name -eq "deadlineworker"}

# Check service status
Get-Service -Name "DeadlineLauncher10"

# View recent worker logs
Get-Content "C:\ProgramData\Thinkbox\Deadline10\logs\deadlineworker*.log" -Tail 50
```

**Restarting a Worker:**
```powershell
Restart-Service -Name "DeadlineLauncher10"
```

### Troubleshooting

**Worker offline in Monitor:**
- Check network connectivity: `ping 10.40.14.25`
- Check service: `Get-Service -Name "DeadlineLauncher10"`
- Restart service: `Restart-Service -Name "DeadlineLauncher10"`

**Job fails with "path not found":**
- Verify UNC path access: `Test-Path "\\10.40.14.25\RenderSourceRepository"`
- Check credentials: `cmdkey /list | Select-String "10.40.14.25"`
- Re-add if missing: `cmdkey /add:10.40.14.25 /user:perforce /pass:uiw3d`

**Maya license errors:**
- Check env var: `[System.Environment]::GetEnvironmentVariable('ADSKFLEX_LICENSE_FILE', 'Machine')`
- Should be: `27000@jabba.ad.uiwtx.edu`
- Restart service after changing env vars

**Arnold crashes/errors:**
- Check cache path: Should be `D:\ArnoldCache\tx` (local, not network)
- Verify Local Rendering is enabled in job submission
- Check worker logs for "Access Violation" errors

**Scene files not up to date:**
- Run P4 sync: `T:\Utility\P4Sync.ps1`
- Wait 5-10 seconds for sync to complete
- Resubmit job

---

## Technical Architecture

### Job Lifecycle

1. **Submission**
   - Job info file (.job) created with metadata
   - Plugin info file (.plugin) created with render settings
   - Files uploaded to Repository
   - Job enters MongoDB queue

2. **Task Assignment**
   - Idle worker queries database for available tasks
   - Scheduling algorithm determines task assignment:
     - Pool/Group membership
     - Job priority (0-100)
     - Machine limits
     - Worker capabilities (GPU, licenses, etc.)

3. **Rendering**
   - Worker downloads job files from Repository
   - Executes plugin (Maya, Blender, etc.)
   - Streams STDOUT/STDERR to worker log
   - Reports progress to database

4. **Completion**
   - If Local Rendering enabled:
     - Frame rendered to local temp directory
     - Copied to network output directory
     - Temp file deleted
   - Task marked complete in database
   - Worker picks next available task

### Network Communication

**Workers → RCS (HTTPS on 4433):**
- TLS encrypted
- Certificate: `Deadline10RemoteClient.pfx` (passphrase: `uiw3d`)
- Endpoints:
  - Get job info
  - Report task status
  - Upload logs
  - Query worker settings

**RCS → MongoDB (TCP on 27100):**
- Internal communication
- Job queue queries
- Worker status updates

**Workers → SMB Shares (Port 445):**
- `\\10.40.14.25\RenderSourceRepository` - Read scene files, textures
- `\\10.40.14.25\RenderOutputRepo` - Write rendered frames
- Credentials: `perforce/uiw3d` (stored via cmdkey)

---

## File Locations

### Worker Machine (Windows)

```
C:\Program Files\Thinkbox\Deadline10\
├── bin\                          # Executables (deadlineworker.exe, etc.)
├── lib\                          # DLLs and libraries
└── ...

C:\ProgramData\Thinkbox\Deadline10\
├── workers\
│   └── [WORKERNAME]\
│       ├── config\               # Worker configuration files
│       ├── jobsData\             # Cached job data
│       └── plugins\              # Local plugin cache
├── logs\
│   ├── deadlineworker*.log       # Worker logs
│   └── deadlinelauncher*.log     # Launcher logs
└── temp\                         # Temporary files

D:\ArnoldCache\
└── tx\                           # Arnold texture cache (local)
```

### Server (Linux)

```
/opt/perforce/deadlineRepository/
├── plugins\                      # Deadline plugins (Maya, Blender, etc.)
├── scripts\                      # Python scripts
├── events\                       # Event plugins
├── jobs\                         # Active job files
├── jobsArchived\                 # Archived job files
└── reports\                      # Render reports and logs

/opt/perforce/deadlineRenderSource/
└── 25_26\                        # P4 workspace - synced scene files
    └── NLG\
        └── prod\
            └── lyt\
                └── act01\
                    └── act01_shot01.ma
```

---

## Best Practices

### Scene Preparation

1. **Use UNC paths consistently**
   - Don't mix UNC and mapped drives
   - Example: `\\10.40.14.25\RenderSourceRepository\25_26\...`

2. **Set relative paths in Maya projects**
   - sourceimages, cache, etc. relative to project root
   - Makes projects portable across machines

3. **Configure Arnold cache**
   - Always set to local: `D:/ArnoldCache/tx`
   - Never point to network drive

4. **Test locally first**
   - Verify scene renders on your workstation before farm submission
   - Isolates scene errors from farm errors

### Job Submission

1. **Enable Local Rendering**
   - Improves stability
   - Reduces network load during rendering
   - Only writes completed frames to network

2. **Set appropriate priority**
   - 0-100 scale (50 is default)
   - Higher priority jobs render first
   - Don't set everything to 100

3. **Use frame chunks for long renders**
   - Frames per task: 1 for heavy scenes, 5-10 for light scenes
   - Allows better parallelization

4. **Sync P4 after scene changes**
   - Run `T:\Utility\P4Sync.ps1`
   - Ensures workers have latest files

### Maintenance

1. **Monitor worker health**
   - Check Deadline Monitor daily
   - Look for offline or stalled workers

2. **Clear old jobs periodically**
   - Archive or delete completed jobs
   - Keeps database lean

3. **Update workers during breaks**
   - Don't auto-upgrade during production
   - Schedule upgrades between semesters

4. **Check disk space**
   - Worker temp directories: `C:\ProgramData\Thinkbox\Deadline10\temp\`
   - Arnold cache: `D:\ArnoldCache\`
   - Server output: `\\10.40.14.25\RenderOutputRepo\`

---

## Related Documentation

- [[Install Deadline Client]] - Step-by-step installation guide
- [[Automated Installation]] - Bulk deployment script
- [[Testing UNC Path Method]] - UNC path validation procedure
- [[Network Drive Mounting Troubleshooting]] - Legacy drive mapping (archived)
- [[__UPDATE__Deploying Deadline as a Service]] - Alternative service deployment (archived)

### External Resources

- [Official Deadline Documentation](C:\repos\obsidian\UIW3D\03_Pipeline\Resources\Deadline-10.4.2.2-User-Manual)
- AWS Thinkbox Support: support@awsthinkbox.zendesk.com

---

**Last Updated:** 2025-12-02
**Deadline Version:** 10.4.2.2
**Server:** 10.40.14.25 (Ubuntu Server)
**Client OS:** Windows 10/11
