# OpenCue Maya 2026 Submit Tool - Development Context

> **For Claude CLI**: Read this file first when resuming work on this project.

## Quick Start for New Session
```
Read C:\repos\OpenCue\poc\CONTEXT.md and continue where we left off
```

## Overview
Building a Maya 2026 submission tool for OpenCue that works around Python 3.11 incompatibility with OpenCue's gRPC/protobuf libraries.

## Architecture
Maya 2026 uses Python 3.11, but OpenCue libraries require Python 3.9. Solution:
1. **maya_submit.py** - Runs inside Maya (Python 3.11, PySide6 UI)
2. **maya_submit_worker.py** - Runs externally (Python 3.9, OpenCue libraries)
3. Communication via JSON temp file passed as argument

## Project Files

```
C:\repos\OpenCue\poc\
├── maya_submit.py          # Maya UI module (Python 3.11/PySide6)
├── maya_submit_worker.py   # OpenCue worker (Python 3.9)
├── README.md               # User documentation
├── ARCHITECTURE.md         # Technical architecture details
├── TROUBLESHOOTING.md      # Common issues and solutions
└── CONTEXT.md              # This file - development context
```

## Configuration
```python
PYTHON_PATH = r"C:\Program Files\Python39\python.exe"
CUEBOT_HOST = "10.40.14.25:8443"
MAYA_VERSION = "2026"
MAYA_RENDER_EXE = r"C:/Program Files/Autodesk/Maya2026/bin/Render.exe"
LOG_ROOT = r"\\10.40.14.25\RenderOutputRepo\OpenCue\Logs"
```

## Usage in Maya
```python
import sys
sys.path.insert(0, r"C:\repos\OpenCue\poc")
import maya_submit
maya_submit.main()

# To reload after changes:
import importlib
importlib.reload(maya_submit)
maya_submit.main()
```

## Issues Resolved

### 1. XML Invalid Character (0x8)
- **Problem**: Backslashes in paths like `\bin\` were interpreted as escape sequences (`\b` = backspace = 0x8)
- **Solution**: Use forward slashes in all paths within the XML spec

### 2. PyOutline Wrapper Path Quoting
- **Problem**: `opencue_wrap_frame` and `pycuerun` paths with spaces weren't quoted
- **Error**: `'C:\Program' is not recognized as an internal or external command`
- **Solution**: Bypass PyOutline entirely, submit XML spec directly via `opencue.api.launchSpecAndWait()`

### 3. Cannot Launch Jobs as Root
- **Problem**: Using `<uid>0</uid>` in XML spec caused rejection
- **Error**: `Cannot launch jobs as root`
- **Solution**: Changed to `<uid>1000</uid>` (non-root user ID)

## Current Status
- [x] UI working with CueSubmit dark theme styling
- [x] Direct XML submission implemented (no wrapper scripts)
- [x] Maya Render.exe path properly quoted
- [x] Log path returned on successful submission
- [x] Documentation complete
- [x] UID fixed (was 0/root, now 1000)
- [x] **Job submission working** - jobs now submit successfully

## Next Steps
1. Test job submission and verify render executes on render farm
2. Verify log path is correct and accessible
3. Consider adding more features from CueSubmit:
   - Multiple layers
   - Layer dependencies
   - Facility selection
   - Limits
   - Core override

## Key Implementation Details

### Why Direct XML Instead of PyOutline?
PyOutline uses wrapper scripts that have Windows path quoting bugs. Direct XML submission via `opencue.api.launchSpecAndWait()` bypasses all wrapper scripts.

### Frame Tokens
- `#FRAME_START#` - First frame of chunk
- `#FRAME_END#` - Last frame of chunk
- `#IFRAME#` - Current frame number

### Log Path Format
```
\\10.40.14.25\RenderOutputRepo\OpenCue\Logs\<show>\<shot>\logs\<job_name>\
```

## Reference Files (Original CueSubmit)
- Maya Plugin: `C:\repos\OpenCue\cuesubmit\plugins\maya\CueMayaSubmit.py`
- UI Widget: `C:\repos\OpenCue\cuesubmit\cuesubmit\ui\Submit.py`
- Styling: `C:\repos\OpenCue\cuesubmit\cuesubmit\ui\Style.py`
- Submission: `C:\repos\OpenCue\cuesubmit\cuesubmit\Submission.py`
- Settings Widgets: `C:\repos\OpenCue\cuesubmit\cuesubmit\ui\SettingsWidgets.py`

## Session History Summary
1. Started with simple inline script submission - hit XML escape issues
2. Tried escaping backslashes - still had issues with nested escapes
3. Switched to forward slashes - fixed XML parsing
4. Hit PyOutline wrapper quoting issue on Windows
5. Switched to direct XML submission - bypasses all wrappers
6. Added CueSubmit dark theme styling to UI
7. Added log path output
8. Created comprehensive documentation
9. Fixed UID 0 (root) rejection - changed to UID 1000
10. **Job submission confirmed working**
