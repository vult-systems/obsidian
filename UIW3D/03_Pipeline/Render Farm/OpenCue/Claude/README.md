# OpenCue Maya 2026 Submit Tool

A submission tool for sending Maya 2026 render jobs to OpenCue, designed to work around Python 3.11 incompatibility issues.

## Problem

Maya 2026 uses Python 3.11, but OpenCue's gRPC/protobuf libraries have compatibility issues with Python 3.11. The standard CueSubmit plugin cannot run directly inside Maya 2026.

## Solution

A two-process architecture:
- **UI Process** (Maya/Python 3.11) - Handles the user interface using PySide6
- **Worker Process** (Python 3.9) - Handles OpenCue API communication

## Requirements

- Maya 2026
- Python 3.9 installed at `C:\Program Files\Python39\python.exe`
- OpenCue Python libraries installed in Python 3.9
- Network access to Cuebot server

## Installation

1. Copy the `poc` folder to your desired location or use directly from the repo
2. Ensure Python 3.9 has OpenCue libraries installed:
   ```
   "C:\Program Files\Python39\python.exe" -m pip install opencue
   ```

## Usage

In Maya's Script Editor (Python tab):

```python
import sys
sys.path.insert(0, r"C:\repos\OpenCue\poc")
import maya_submit
maya_submit.main()
```

Or create a shelf button with:
```python
import maya_submit
maya_submit.main()
```

## Configuration

Edit the constants at the top of `maya_submit.py` and `maya_submit_worker.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `PYTHON_PATH` | Path to Python 3.9 | `C:\Program Files\Python39\python.exe` |
| `CUEBOT_HOST` | Cuebot server address | `10.40.14.25:8443` |
| `MAYA_RENDER_EXE` | Maya Render executable | `C:/Program Files/Autodesk/Maya2026/bin/Render.exe` |
| `LOG_ROOT` | UNC path for render logs | `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs` |

## Files

| File | Description |
|------|-------------|
| `maya_submit.py` | Maya UI module (runs in Maya) |
| `maya_submit_worker.py` | OpenCue submission worker (runs in Python 3.9) |
| `CONTEXT.md` | Development context for continuing work |
| `ARCHITECTURE.md` | Technical architecture details |
| `TROUBLESHOOTING.md` | Common issues and solutions |

## Features

- Dark theme UI matching CueSubmit style
- Auto-populates from current Maya scene (filename, frame range, renderer, cameras)
- Direct XML submission (bypasses problematic wrapper scripts)
- Returns job name, ID, and log file path on success

## License

Apache License 2.0 - See OpenCue project license.
