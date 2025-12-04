
## Requirements
- Maya 2024/2025/2026
- Python 3.9+
- Scene saved to shared storage accessible from render nodes

---
## Setup Steps
### 1. Install OpenCue Python Libraries

```powershell
pip install opencue-pycue opencue-pyoutline
```

### 2. Create OpenCue Config
Run in PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\opencue"
@"
cuebot.facility_default: local
cuebot.facility:
    local:
        - 10.40.14.25:8443
"@ | Out-File -FilePath "$env:APPDATA\opencue\opencue.yaml" -Encoding UTF8
```

### 3. Test Connection
```powershell
python -c "import opencue; print(opencue.api.getHosts())"
```

Should list your render nodes.
  
## Submitting from Maya
In Maya's Script Editor (Python tab), run:
  
```python
"""Submit Maya render job to OpenCue."""

import os

import maya.cmds as cmds
from outline import Outline, cuerun
from outline.modules.shell import Shell

# Render executable path
MAYA_RENDER_EXE = r"C:\Program Files\Autodesk\Maya2024\bin\Render.exe"

# OpenCue job settings
SHOW = "testing"
SHOT = "shot01"
SERVICE = "maya"
CHUNK_SIZE = 1


def get_scene_info():
    """Get current scene information from Maya."""
    scene_path = cmds.file(q=True, sceneName=True)
    start_frame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
    renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
    job_name = os.path.splitext(os.path.basename(scene_path))[0]

    return {
        "scene_path": scene_path,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "renderer": renderer,
        "job_name": job_name,
    }


def convert_to_unc(path, drive_letter="S:", unc_root=r"\\10.40.14.25\Projects"):
    """Convert mapped drive path to UNC path if needed."""
    if path.startswith(drive_letter):
        return path.replace(drive_letter, unc_root)
    return path


def build_render_command(scene_path, renderer):
    """Build the Maya render command."""
    return [
        MAYA_RENDER_EXE,
        "-r", renderer,
        "-s", "#IFRAME#",
        "-e", "#IFRAME#",
        scene_path,
    ]


def submit_job(job_name, render_cmd, frame_range):
    """Create and submit the OpenCue job."""
    outline = Outline(name=job_name, show=SHOW, shot=SHOT)

    layer = Shell("render", command=render_cmd, range=frame_range, chunk=CHUNK_SIZE)
    layer.set_service(SERVICE)
    outline.add_layer(layer)

    jobs = cuerun.launch(outline, pause=False, os="Windows")
    return jobs


def main():
    """Main entry point for job submission."""
    info = get_scene_info()

    # Convert to UNC path if using mapped drives
    scene_path = convert_to_unc(info["scene_path"])

    render_cmd = build_render_command(scene_path, info["renderer"])
    frame_range = f"{info['start_frame']}-{info['end_frame']}"

    submit_job(info["job_name"], render_cmd, frame_range)
    print(f"Submitted: {info['job_name']}")


if __name__ == "__main__":
    main()
```

---
## Quick Shelf Button
Add this to a Maya shelf button (Python command):
```python
exec(open(r"C:\OpenCue\maya\submit.py").read())
```
Then create `C:\OpenCue\maya\submit.py` with the submission code above.

## Monitoring Jobs
Run `cuegui` and go to **Monitor Jobs** to watch your renders.

---
## Troubleshooting
**"Service not found" error**
Run once to create the maya service:
```python
"""Create Maya service for OpenCue."""

import opencue
from opencue.wrappers.service import Service

SERVICE_CONFIG = {
    "name": "maya",
    "minCores": 100,
    "maxCores": 800,
    "minMemory": 4194304,
    "minGpus": 0,
    "maxGpus": 0,
    "tags": ["maya", "general"],
    "threadable": True,
}


def create_maya_service():
    """Register the Maya service with OpenCue."""
    service = Service(SERVICE_CONFIG)
    opencue.api.createService(service)


if __name__ == "__main__":
    create_maya_service()
```

**Frames fail - can't find scene**
Scene path must be accessible from render nodes. Use UNC paths (`\\server\share\...`) not mapped drives (`S:\...`).

**Frames fail - can't find Maya**
Update the `Render.exe` path in the submit script to match your Maya version.