# OpenCue Proof of Concept Test Plan

## Overview
This document outlines the test plan for validating OpenCue as a replacement for AWS Thinkbox Deadline in your render farm environment.

## Environment
- **Cuebot Server**: 1 Linux server (Ubuntu/Debian)
- **Render Nodes**: 5 Windows lab machines (pilot)
- **Submitter**: Artist workstation with Maya 2026
- **Storage**: P4 workspace accessed via UNC paths

---

## Pre-Deployment Checklist

### Linux Server
- [ ] Ubuntu/Debian server accessible via SSH
- [ ] Server hostname/IP documented: `_______________`
- [ ] Ports 8443, 8444, 5432 available
- [ ] Java 17+ available or can be installed
- [ ] PostgreSQL available or can be installed
- [ ] Git installed for cloning migrations

### Windows Machines (5 pilot)
- [ ] Machine hostnames documented in `machines.txt`
- [ ] Python 3.7+ installed on all machines
- [ ] PowerShell Remoting enabled (for bulk deployment)
- [ ] Admin credentials available
- [ ] Maya 2026 installed
- [ ] Arnold installed

### Network
- [ ] Windows machines can reach Linux server on ports 8443, 8444
- [ ] UNC path to P4 workspace accessible from all machines
- [ ] UNC path documented: `_______________`

---

## Phase 1: Linux Server Setup

### Steps
1. SSH into Linux server
2. Copy `poc/linux-server/install-cuebot.sh` to server
3. Edit script to set `POSTGRES_PASSWORD`
4. Run: `sudo ./install-cuebot.sh`
5. Verify Cuebot is running: `systemctl status cuebot`

### Validation
```bash
# Check Cuebot logs
journalctl -u cuebot -n 50

# Test gRPC port
nc -zv localhost 8443

# Test from Windows (PowerShell)
Test-NetConnection -ComputerName YOUR_SERVER -Port 8443
```

### Expected Result
- Cuebot service is running
- PostgreSQL has `cuebot` database
- Ports 8443 and 8444 are listening

---

## Phase 2: Create Services

### Steps
1. On Linux server or any machine with Python:
```bash
pip install opencue-pycue
python poc/services/setup_services.py --cuebot YOUR_SERVER:8443
```

### Validation
```bash
# List services
python -c "import os; os.environ['CUEBOT_HOSTS']='YOUR_SERVER:8443'; import opencue; print([s.name() for s in opencue.api.getDefaultServices()])"
```

### Expected Result
- Services created: `shell`, `maya2026`, `arnold`
- Show created: `maya_renders`

---

## Phase 3: Deploy RQD to Pilot Machines

### Option A: Manual Install (1 machine at a time)
1. Copy `poc/windows-rqd/` folder to each machine
2. Edit `rqd.conf` - set `OVERRIDE_CUEBOT`
3. Run as Administrator:
```powershell
.\install-rqd.ps1 -CuebotHost "YOUR_SERVER"
```

### Option B: Bulk Deploy (all 5 at once)
1. Edit `poc/windows-rqd/machines.txt` with 5 hostnames
2. Run from admin workstation:
```powershell
.\deploy-bulk.ps1 -CuebotHost "YOUR_SERVER"
```

### Validation
```powershell
# On each machine
Get-Service OpenCueRQD

# From Cuebot server
cueadmin -lh

# From any machine with pycue
python -c "import os; os.environ['CUEBOT_HOSTS']='YOUR_SERVER:8443'; import opencue; print([h.name() for h in opencue.api.getHosts()])"
```

### Expected Result
- 5 machines appear in CueGUI Hosts view
- All show "UP" state
- NIMBY may be "LOCKED" if user is active

---

## Phase 4: Install Maya Tools

### Steps
1. On submitter workstation, install OpenCue Python:
```powershell
pip install opencue-pycue opencue-pyoutline
```

2. Create OpenCue config:
```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\opencue"
@"
cuebot.facility_default: local
cuebot.facility:
    local:
        - YOUR_SERVER:8443
"@ | Out-File -FilePath "$env:APPDATA\opencue\opencue.yaml" -Encoding UTF8
```

3. Copy Maya scripts:
   - Copy `poc/maya/opencue_submit.py` to Maya scripts folder
   - Copy `poc/maya/userSetup.py` to Maya scripts folder
   - Edit `userSetup.py` - set `CUEBOT_HOSTNAME`
   - Edit `opencue_submit.py` - set `UNC_PATH_PREFIX` and `LOCAL_PATH_PREFIX`

4. Copy shelf (optional):
   - Copy `poc/maya/shelf_OpenCue.mel` to Maya prefs/shelves folder

### Validation
1. Launch Maya
2. Check Script Editor for "[OpenCue] Connected!" message
3. Run: `import opencue_submit; opencue_submit.show()`

### Expected Result
- Maya loads without errors
- OpenCue menu appears in menu bar
- Submit dialog opens and shows scene info

---

## Phase 5: End-to-End Render Test

### Test Scenario
Submit a simple Maya/Arnold render and verify it completes on the farm.

### Steps
1. Open a Maya scene with Arnold render settings
2. Save scene to P4 workspace (S:\ drive)
3. Sync scene to Linux server (P4Sync.ps1)
4. Open OpenCue Submit dialog (OpenCue menu or shelf)
5. Verify settings:
   - Job name
   - Frame range
   - Camera
   - Renderer: arnold
6. Click "Submit to OpenCue"
7. Open CueGUI to monitor

### Validation
```bash
# List jobs
python -c "import os; os.environ['CUEBOT_HOSTS']='YOUR_SERVER:8443'; import opencue; jobs=opencue.api.getJobs(); print([j.name() for j in jobs])"
```

### Expected Result
- Job appears in CueGUI
- Frames dispatch to available hosts
- Frames complete successfully (green)
- Output images appear in render location

---

## Phase 6: NIMBY Test

### Test Scenario
Verify idle detection works correctly on lab machines.

### Steps
1. Ensure a render job is running/pending
2. On a pilot machine, move mouse/type - verify machine locks
3. Stop input for 5+ minutes - verify machine unlocks and accepts frames
4. While frame is running, move mouse - verify frame is killed and host locks

### Validation
- Check host state in CueGUI
- Check RQD logs: `C:\OpenCue\logs\rqd-stderr.log`

### Expected Result
- NIMBY locks host immediately on user input
- NIMBY unlocks after configured idle time (default 5 min)
- Running frames are terminated when host locks

---

## Troubleshooting

### RQD won't start
```powershell
# Check logs
Get-Content C:\OpenCue\logs\rqd-stderr.log -Tail 50

# Test connection manually
$env:CUEBOT_HOSTNAME = "YOUR_SERVER"
C:\OpenCue\venv\Scripts\python.exe -m rqd.cuerqd
```

### Host not appearing in CueGUI
- Check firewall: port 8444 inbound must be open
- Check config: `OVERRIDE_CUEBOT` must be correct
- Check network: `Test-NetConnection -ComputerName SERVER -Port 8443`

### Maya submission fails
- Check OpenCue config: `%APPDATA%\opencue\opencue.yaml`
- Test connection: `import opencue; opencue.api.getHosts()`
- Check UNC path is accessible from render nodes

### Frames fail immediately
- Check frame log in CueGUI
- Verify Maya is in PATH on render nodes
- Verify scene file is accessible via UNC path

---

## Success Criteria

| Test | Pass Criteria |
|------|---------------|
| Cuebot running | Service active, responding on 8443 |
| Services created | maya2026, arnold, shell exist |
| RQD connected | 5 hosts visible in CueGUI |
| Maya submission | Job appears in CueGUI |
| Frame rendering | At least 1 frame completes |
| NIMBY lock | Host locks on user input |
| NIMBY unlock | Host unlocks after idle |
| End-to-end | Full sequence renders successfully |

---

## Notes

### Path Configuration
Your environment uses:
- Local work: `S:\` (subst drive mapped to P4 workspace)
- Render access: UNC path to Linux server's P4 workspace

Update `opencue_submit.py`:
```python
UNC_PATH_PREFIX = r"\\YOUR_LINUX_SERVER\p4workspace"
LOCAL_PATH_PREFIX = "S:"
```

### Next Steps After POC
1. Deploy to remaining 80 lab machines
2. Configure CueNIMBY for time-based scheduling
3. Integrate with other DCCs (if needed)
4. Create production job templates
5. Train artists on CueGUI usage
