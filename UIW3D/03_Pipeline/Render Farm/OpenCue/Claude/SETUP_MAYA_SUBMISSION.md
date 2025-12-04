# Maya Submission Setup

## Requirements
- Maya 2024 or 2025 (Maya 2026 uses Python 3.11 which is NOT compatible with OpenCue)
- Python 3.9 or 3.10 on system
- Scene saved to shared storage accessible from render nodes

## Known Issues

**Maya 2026**: Uses Python 3.11 internally. OpenCue packages don't support Python 3.11 on Windows. Use Maya 2024/2025 or submit via external script (see Troubleshooting).

---

## Setup Steps

### 1. Install OpenCue Python Libraries (System Python)
```powershell
pip install opencue-pycue opencue-pyoutline
```

### 2. Create OpenCue Config

**IMPORTANT**: YAML must be ASCII encoded with no BOM, spaces not tabs.

Run in PowerShell:
```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\opencue"

@"
cuebot.facility_default: local
cuebot.facility:
  local:
    - 10.40.14.25:8443
"@ | Out-File -FilePath "$env:APPDATA\opencue\opencue.yaml" -Encoding ASCII -NoNewline
```

**Verify the file is valid:**
```powershell
python -c "import yaml; print(yaml.safe_load(open(r'$env:APPDATA\opencue\opencue.yaml')))"
```

Should print:
```
{'cuebot.facility_default': 'local', 'cuebot.facility': {'local': ['10.40.14.25:8443']}}
```

If you get YAML errors, delete the file and recreate it, or check for invisible characters/BOM.

### 3. Set Environment Variable (Recommended)

Most reliable method - set `CUEBOT_HOSTS`:

**System Properties → Environment Variables → User Variables**
- **Name**: `CUEBOT_HOSTS`
- **Value**: `10.40.14.25`

Or via PowerShell (permanent):
```powershell
[Environment]::SetEnvironmentVariable("CUEBOT_HOSTS", "10.40.14.25", "User")
```

**Close and reopen PowerShell/Maya after setting.**

### 4. Test Connection (System Python)

```powershell
python -c "import opencue; print([h.name() for h in opencue.api.getHosts()])"
```

Should list your render nodes.

If you get `localhost:8443` errors, force the host:
```python
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])
import opencue
print([h.name() for h in opencue.api.getHosts()])
```

---

## Submitting from Maya 2024/2025

In Maya's Script Editor (Python tab):

```python
import os
import maya.cmds as cmds

# Force correct Cuebot host FIRST
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])

import opencue
from outline import Outline, cuerun
from outline.modules.shell import Shell

# Get scene info
scene = cmds.file(q=True, sceneName=True)
start = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
end = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
job_name = os.path.splitext(os.path.basename(scene))[0]

# IMPORTANT: Convert scene path to UNC if using mapped drives
# Example: scene = scene.replace("S:", r"\\10.40.14.25\Projects")

# Build render command - UPDATE PATH FOR YOUR MAYA VERSION
render_cmd = [
    r"C:\Program Files\Autodesk\Maya2024\bin\Render.exe",
    "-r", renderer,
    "-s", "#IFRAME#",
    "-e", "#IFRAME#",
    scene
]

# Create and submit job
ol = Outline(name=job_name, show="testing", shot="shot01")
layer = Shell("render", command=render_cmd, range=f"{start}-{end}", chunk=1)
layer.set_service("maya")
ol.add_layer(layer)

jobs = cuerun.launch(ol, pause=False, os="Windows")
print(f"Submitted: {job_name}")
```

---

## Submitting from Maya 2026 (Workaround)

Maya 2026 uses Python 3.11 which doesn't support OpenCue. Use subprocess to call system Python:

### Step 1: Create submission script

Save as `C:\OpenCue\maya\submit_job.py`:
```python
"""
External submission script - called from Maya via subprocess
Usage: python submit_job.py <scene_path> <start_frame> <end_frame> [renderer]
"""
import sys
import os

# Force Cuebot host
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])

from outline import Outline, cuerun
from outline.modules.shell import Shell

def submit(scene_path, start_frame, end_frame, renderer="arnold"):
    job_name = os.path.splitext(os.path.basename(scene_path))[0]

    render_cmd = [
        r"C:\Program Files\Autodesk\Maya2026\bin\Render.exe",
        "-r", renderer,
        "-s", "#IFRAME#",
        "-e", "#IFRAME#",
        scene_path
    ]

    ol = Outline(name=job_name, show="testing", shot="shot01")
    layer = Shell("render", command=render_cmd, range=f"{start_frame}-{end_frame}", chunk=1)
    layer.set_service("maya")
    ol.add_layer(layer)

    jobs = cuerun.launch(ol, pause=False, os="Windows")
    print(f"Submitted: {job_name}")
    return jobs

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python submit_job.py <scene> <start> <end> [renderer]")
        sys.exit(1)

    scene = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    renderer = sys.argv[4] if len(sys.argv) > 4 else "arnold"

    submit(scene, start, end, renderer)
```

### Step 2: Call from Maya 2026

In Maya's Script Editor (Python tab):
```python
import subprocess
import maya.cmds as cmds

scene = cmds.file(q=True, sceneName=True)
start = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
end = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")

# Call system Python 3.9 with submission script
result = subprocess.run([
    r"C:\Python39\python.exe",
    r"C:\OpenCue\maya\submit_job.py",
    scene,
    str(start),
    str(end),
    renderer
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
```

---

## Quick Shelf Button

Add to Maya shelf (Python command):

**Maya 2024/2025:**
```python
exec(open(r"C:\OpenCue\maya\submit_maya.py").read())
```

**Maya 2026:**
```python
import subprocess
import maya.cmds as cmds
scene = cmds.file(q=True, sceneName=True)
start = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
end = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
result = subprocess.run([r"C:\Python39\python.exe", r"C:\OpenCue\maya\submit_job.py", scene, str(start), str(end), renderer], capture_output=True, text=True)
print(result.stdout)
if result.stderr: print("Errors:", result.stderr)
```

---

## Monitoring Jobs

Run `cuegui` and go to **Monitor Jobs** to watch your renders.

---

## Troubleshooting

### "localhost:8443" connection errors

OpenCue ignoring your config. Fix by forcing host in code:
```python
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])
```

Or set `CUEBOT_HOSTS=10.40.14.25` environment variable and restart Maya.

### YAML parsing errors / BOM issues

Delete and recreate the config file:
```powershell
Remove-Item "$env:APPDATA\opencue\opencue.yaml"
@"
cuebot.facility_default: local
cuebot.facility:
  local:
    - 10.40.14.25:8443
"@ | Out-File -FilePath "$env:APPDATA\opencue\opencue.yaml" -Encoding ASCII -NoNewline
```

Check for invisible characters:
```powershell
Format-Hex "$env:APPDATA\opencue\opencue.yaml" | Select-Object -First 5
```
First bytes should NOT be `EF BB BF` (that's BOM).

### "No module named opencue" in Maya 2026

Maya 2026 uses Python 3.11 which doesn't support OpenCue. Use the subprocess workaround above.

### "Service not found" error

Create the maya service (run once):
```python
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])

import opencue
opencue.api.createService(opencue.wrappers.service.Service({
    "name": "maya",
    "minCores": 100,
    "maxCores": 800,
    "minMemory": 4194304,
    "minGpus": 0,
    "maxGpus": 0,
    "tags": ["maya", "general"],
    "threadable": True
}))
```

### Frames fail - can't find scene

Use UNC paths (`\\server\share\...`) not mapped drives (`S:\...`).

### Frames fail - can't find Maya

Update `Render.exe` path in submit script to match your Maya version.
