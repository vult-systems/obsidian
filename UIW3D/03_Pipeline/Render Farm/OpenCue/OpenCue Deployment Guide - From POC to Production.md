
This guide assumes Cuebot and PostgreSQL are already running on the Linux server (10.40.14.25).

---`

## Part 1: Setting Up a Windows Render Node (Worker)

### Prerequisites
- Windows 10/11
- Admin access
- Network access to 10.40.14.25 (ports 8443, 8444)
- Network access to shared storage: `\\10.40.14.25\RenderOutputRepo`
### Step 1: Install Python 3.9+

Download and install Python from https://www.python.org/downloads/

**IMPORTANT**: Install to a path WITHOUT spaces (e.g., `C:\Python39`) to avoid wrapper script issues.

During installation:
- [x] Add Python to PATH
- [x] Install for all users (requires admin)

### Step 2: Install OpenCue RQD

Open PowerShell as Administrator:

```powershell
pip install opencue-rqd
```

### Step 3: Set Environment Variables

Open System Properties → Environment Variables → User Variables:

| Variable          | Value         |
| ----------------- | ------------- |
| `CUEBOT_HOSTNAME` | `10.40.14.25` |

Or via PowerShell (permanent):
```powershell
[Environment]::SetEnvironmentVariable("CUEBOT_HOSTNAME", "10.40.14.25", "User")
```

### Step 4: Create RQD Config (Optional)

Create `C:\OpenCue\rqd.conf`:

```ini
[Override]
OVERRIDE_CUEBOT=10.40.14.25

[Override]
OVERRIDE_NIMBY=1
```

### Step 5: Test RQD Manually

Open a new PowerShell window:

```powershell
python -m rqd
```

You should see:

```
WARNING:root:CUEBOT_HOSTNAME: 10.40.14.25
WARNING   openrqd-__main__  : RQD Starting Up
WARNING   openrqd-rqcore    : RQD Started
```
  
Check CueGUI on any machine - the host should appear in Monitor Hosts.
  
### Step 6: Install RQD as Windows Service

Create `C:\OpenCue\install-rqd-service.ps1`:

```powershell
# Install RQD as a Windows Service using NSSM
# Requires NSSM (Non-Sucking Service Manager): https://nssm.cc/download

param(
    [string]$PythonPath = "C:\Python39\python.exe",
    [string]$CuebotHost = "10.40.14.25"
)
  
$NssmPath = "C:\OpenCue\nssm.exe"
$ServiceName = "OpenCueRQD"

# Download NSSM if not present
if (-not (Test-Path $NssmPath)) {
    Write-Host "Download NSSM from https://nssm.cc/download and place nssm.exe in C:\OpenCue\"
    exit 1
}

# Remove existing service if present
& $NssmPath stop $ServiceName 2>$null
& $NssmPath remove $ServiceName confirm 2>$null

# Install service
& $NssmPath install $ServiceName $PythonPath "-m" "rqd"
& $NssmPath set $ServiceName AppDirectory "C:\OpenCue"
& $NssmPath set $ServiceName DisplayName "OpenCue RQD"
& $NssmPath set $ServiceName Description "OpenCue Render Queue Daemon"
& $NssmPath set $ServiceName Start SERVICE_AUTO_START
& $NssmPath set $ServiceName AppEnvironmentExtra "CUEBOT_HOSTNAME=$CuebotHost"

# Set up logging
& $NssmPath set $ServiceName AppStdout "C:\OpenCue\logs\rqd-stdout.log"
& $NssmPath set $ServiceName AppStderr "C:\OpenCue\logs\rqd-stderr.log"
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateBytes 1048576
  
# Create logs directory
New-Item -ItemType Directory -Force -Path "C:\OpenCue\logs" 

# Start service
& $NssmPath start $ServiceName

Write-Host "RQD service installed and started"
Get-Service $ServiceName
```

To install:
1. Download NSSM from https://nssm.cc/download
2. Extract `nssm.exe` to `C:\OpenCue\`
3. Run as Administrator:

   ```powershell
   .\install-rqd-service.ps1 -PythonPath "C:\Python39\python.exe" -CuebotHost "10.40.14.25"
   ```

### Step 7: Verify Service

```powershell
Get-Service OpenCueRQD
```

Should show `Running`.

---

## Part 2: Bulk Deployment to Multiple Machines

### Option A: Manual (Small Scale)

Repeat Part 1 on each machine.

### Option B: PowerShell Remoting (Recommended)

Create `C:\OpenCue\deploy-rqd-remote.ps1`:

```powershell

param(
    [Parameter(Mandatory=$true)]
    [string[]]$ComputerNames,
    [string]$CuebotHost = "10.40.14.25"
)
  
$ScriptBlock = {
    param($CuebotHost)
    
    # Install pip packages
    pip install opencue-rqd

    # Set environment variable
    [Environment]::SetEnvironmentVariable("CUEBOT_HOSTNAME", $CuebotHost, "Machine")
  
    # Create directories
    New-Item -ItemType Directory -Force -Path "C:\OpenCue\logs"
    Write-Host "RQD installed on $env:COMPUTERNAME"
}

foreach ($Computer in $ComputerNames) {
    Write-Host "Deploying to $Computer..."
    Invoke-Command -ComputerName $Computer -ScriptBlock $ScriptBlock -ArgumentList $CuebotHost
}
```


Usage:

```powershell
.\deploy-rqd-remote.ps1 -ComputerNames "PC001","PC002","PC003" -CuebotHost "10.40.14.25"
```

**Prerequisites for remoting:**

```powershell
# Run on each target machine (one-time setup)
Enable-PSRemoting -Force
```


---

## Part 3: Setting Up Maya Submission

### Prerequisites
- Maya 2024/2025/2026 installed
- Arnold renderer installed
- Python opencue packages
### Step 1: Install OpenCue Python Libraries

```powershell
pip install opencue-pycue opencue-pyoutline
```

### Step 2: Create OpenCue Config

Create `%APPDATA%\opencue\opencue.yaml`:

```yaml
cuebot.facility_default: local
cuebot.facility:
    local:
        - 10.40.14.25:8443
```

PowerShell command:

```powershell
$ConfigDir = "$env:APPDATA\opencue"
New-Item -ItemType Directory -Force -Path $ConfigDir

@"
cuebot.facility_default: local
cuebot.facility:
    local:
        - 10.40.14.25:8443
"@ | Out-File -FilePath "$ConfigDir\opencue.yaml" -Encoding UTF8
```


### Step 3: Create Maya Submission Script

Save as `C:\OpenCue\maya\submit_maya_job.py`:

```python
"""
OpenCue Maya Job Submission Script
Run from Maya's Script Editor or shelf button
"""
  
import os
import sys
import maya.cmds as cmds

# Ensure OpenCue is available
try:
    import opencue
    import outline
    from outline import Outline, cuerun
    from outline.modules.shell import Shell
except ImportError:
    cmds.error("OpenCue not installed. Run: pip install opencue-pycue opencue-pyoutline")

def get_scene_info():
    """Get current Maya scene information"""
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        cmds.error("Please save your scene first")
        return None

    # Get render settings
    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
  
    # Get render cameras
    cameras = [cam for cam in cmds.ls(type="camera")
             if cmds.getAttr(cam + ".renderable")]

    # Get current renderer
    renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
    return {
        "scene_path": scene_path,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "cameras": cameras,
        "renderer": renderer
    }

def convert_to_unc(local_path):
    """
    Convert local path to UNC path for render farm access
    Modify this based on your storage setup
    """
    # Example: S:\projects\... -> \\server\projects\...
    # Adjust these mappings for your environment 
    path_mappings = {
        "S:": r"\\10.40.14.25\Projects",
        "R:": r"\\10.40.14.25\RenderOutput",
        # Add more drive mappings as needed
    }
    for drive, unc in path_mappings.items():
        if local_path.upper().startswith(drive.upper()):
            return local_path.replace(drive, unc, 1)

    # If already UNC or no mapping found, return as-is
    return local_path
  
def submit_job(job_name=None, show="testing", shot="shot01", chunk_size=1):
    """
    Submit current Maya scene to OpenCue
    Args:
        job_name: Name for the job (default: scene name)
        show: OpenCue show name
        shot: Shot name for organization
        chunk_size: Frames per task
    """
    info = get_scene_info()
    if not info:
        return
  
    if job_name is None:
        job_name = os.path.splitext(os.path.basename(info["scene_path"]))[0]

    # Convert scene path to UNC
    scene_unc = convert_to_unc(info["scene_path"])
    # Get Maya and renderer paths
    maya_location = os.environ.get("MAYA_LOCATION", r"C:\Program Files\Autodesk\Maya2024")
    render_exe = os.path.join(maya_location, "bin", "Render.exe")
    # Build render command
    # Using Render.exe directly instead of wrapper scripts
    render_cmd = [
        render_exe,
        "-r", info["renderer"],
        "-s", "#IFRAME#",
        "-e", "#IFRAME#",
        "-cam", info["cameras"][0] if info["cameras"] else "persp",
        scene_unc
    ]

    # Create job
    ol = Outline(name=job_name, show=show, shot=shot)

    # Create render layer
    layer = Shell(
        "render",
        command=render_cmd,
        range=f"{info['start_frame']}-{info['end_frame']}",
        chunk=chunk_size
    )

    layer.set_service("maya")  # or "arnold" if you created that service
    ol.add_layer(layer)

    # Submit with Windows OS specified
    try:
        jobs = cuerun.launch(ol, pause=False, os="Windows")
        cmds.confirmDialog(
            title="Job Submitted",
            message=f"Job '{job_name}' submitted successfully!\n\nFrames: {info['start_frame']}-{info['end_frame']}",
            button=["OK"]
        )
        print(f"Submitted job: {jobs}")
        return jobs
    except Exception as e:
        cmds.error(f"Failed to submit job: {e}")
        return None

def show_submit_dialog():
    """Show a dialog for job submission settings"""
    info = get_scene_info()
    if not info:
        return

    # Create dialog
    result = cmds.promptDialog(
        title="Submit to OpenCue",
        message=f"Scene: {os.path.basename(info['scene_path'])}\nFrames: {info['start_frame']}-{info['end_frame']}\n\nJob Name:",
        text=os.path.splitext(os.path.basename(info['scene_path']))[0],
        button=["Submit", "Cancel"],
        defaultButton="Submit",
        cancelButton="Cancel",
        dismissString="Cancel"
    )

  

    if result == "Submit":

        job_name = cmds.promptDialog(query=True, text=True)

        submit_job(job_name=job_name)

  
  

# Run dialog if executed directly

if __name__ == "__main__":

    show_submit_dialog()

```

  

### Step 4: Add Maya Shelf Button

In Maya:
1. Open Window → Settings/Preferences → Shelf Editor
2. Create a new shelf called "OpenCue"
3. Add a new button with this Python command:

```python
import sys
sys.path.insert(0, r"C:\OpenCue\maya")
import submit_maya_job
submit_maya_job.show_submit_dialog()
```

Or create a shelf file `shelf_OpenCue.mel` in Maya's prefs/shelves folder:

```mel
global proc shelf_OpenCue () {
    shelfButton
        -label "Submit to OpenCue"
        -annotation "Submit current scene to OpenCue render farm"
        -image "render.png"
        -command "import sys; sys.path.insert(0, r'C:\\OpenCue\\maya'); import submit_maya_job; submit_maya_job.show_submit_dialog()"
        -sourceType "python";
}
```
  

---

## Part 4: Creating Required Services
  
Before submitting Maya jobs, create the required services in OpenCue.
  
Run this Python script once:

```python
import os
os.environ["CUEBOT_HOSTS"] = "10.40.14.25"


import opencue


# Create maya service
try:
    opencue.api.createService(opencue.wrappers.service.Service({
        "name": "maya",
        "minCores": 100,      # 1 core minimum
        "maxCores": 800,      # 8 cores maximum
        "minMemory": 4194304, # 4GB minimum
        "minGpus": 0,
        "maxGpus": 0,
        "tags": ["maya", "general"],
        "threadable": True
    }))
    print("Created 'maya' service")
except Exception as e:
    print(f"maya service may already exist: {e}")
  
# Create arnold service
try:
    opencue.api.createService(opencue.wrappers.service.Service({
        "name": "arnold",
        "minCores": 100,
        "maxCores": 800,
        "minMemory": 8388608, # 8GB minimum
        "minGpus": 0,
        "maxGpus": 100,       # Can use GPU
        "tags": ["arnold", "maya", "general"],
        "threadable": True
    }))
    print("Created 'arnold' service")
except Exception as e:
    print(f"arnold service may already exist: {e}")
  
# Create shell service (for test jobs)
try:
    opencue.api.createService(opencue.wrappers.service.Service({
        "name": "shell",
        "minCores": 100,
        "maxCores": 100,
        "minMemory": 1048576, # 1GB minimum
        "minGpus": 0,
        "maxGpus": 0,
        "tags": ["shell", "general"],
        "threadable": False
    }))
    print("Created 'shell' service")
except Exception as e:
    print(f"shell service may already exist: {e}")
print("\nServices configured!")

```


---
## Part 5: Daily Workflow

### For Artists

1. **Open Maya**, work on scene
2. **Save scene** to shared storage (must be accessible via UNC path from render nodes)
3. **Click "Submit to OpenCue"** shelf button
4. **Monitor in CueGUI**:
   - Open CueGUI (or run `cuegui` from command line)
   - Go to Monitor Jobs → select your show
   - Watch frames turn green

### For TDs/Admins
  
**Check farm status:**

```powershell
cuegui
```

- Monitor Hosts: See all render nodes, their status
- Monitor Jobs: See all jobs, kill/pause/retry as needed

**Common operations in CueGUI:**
- Right-click job → Kill (stop job)
- Right-click job → Pause (stop dispatching)
- Right-click frame → Retry (re-run failed frame)
- Right-click frame → View Log (see render output)
- Right-click host → Lock (prevent new frames)  

**Check RQD service on a node:**

```powershell
Get-Service OpenCueRQD
Restart-Service OpenCueRQD
```

**View RQD logs:**

```powershell
Get-Content C:\OpenCue\logs\rqd-stderr.log -Tail 50
```
  
---
## Part 6: Troubleshooting

### Host shows DOWN in CueGUI
- Check if RQD is running: `Get-Service OpenCueRQD`
- Check RQD logs: `C:\OpenCue\logs\rqd-stderr.log`
- Check network: `Test-NetConnection 10.40.14.25 -Port 8443`

### Job stays pending (doesn't dispatch)
- Check host is UP and OPEN (not NIMBY locked)
- Check job's service matches host's tags
- Check host has enough memory/cores for job requirements
  
### Frame fails immediately
- View frame log in CueGUI
- Check scene path is accessible via UNC from render node
- Check Maya/Arnold is installed on render node
- Check render node can access all textures and references

### "Service not found" error
- Run the service creation script from Part 4
- Verify with:
  ```python
  import opencue
  for s in opencue.api.getDefaultServices():
      print(s.name())
  ```
### Log path errors

- Verify `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs` is accessible from render nodes
- Check Windows share permissions

---

## Quick Reference

### Paths
| Item | Path |
|------|------|
| Cuebot Server | 10.40.14.25:8443 |
| Frame Logs (UNC) | `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs` |
| RQD Logs | `C:\OpenCue\logs\` |
| Maya Submit Script | `C:\OpenCue\maya\submit_maya_job.py` |
| OpenCue Config | `%APPDATA%\opencue\opencue.yaml` |

  
### Commands

```powershell
# Start CueGUI
cuegui
  
# Check RQD service
Get-Service OpenCueRQD

# Restart RQD
Restart-Service OpenCueRQD
  
# Test Cuebot connection
python -c "import os; os.environ['CUEBOT_HOSTS']='10.40.14.25'; import opencue; print(opencue.api.getHosts())"
```

### Environment Variables (Windows)

| Variable | Value |
|----------|-------|
| `CUEBOT_HOSTNAME` | `10.40.14.25` |
| `CUEBOT_HOSTS` | `10.40.14.25` |
