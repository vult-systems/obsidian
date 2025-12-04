# Troubleshooting

## Common Issues

### 1. XML Invalid Character (Unicode: 0x8)

**Error:**
```
Failed to parse job spec XML, org.jdom.input.JDOMParseException:
Error on line 1: An invalid XML character (Unicode: 0x8) was found
```

**Cause:**
Backslashes in Windows paths are interpreted as escape sequences:
- `\b` = backspace (0x08)
- `\t` = tab (0x09)
- `\n` = newline (0x0A)

**Solution:**
Use forward slashes in all paths:
```python
# Bad
path = "C:\\Program Files\\Autodesk\\Maya2026\\bin\\Render.exe"

# Good
path = "C:/Program Files/Autodesk/Maya2026/bin/Render.exe"
```

---

### 2. 'C:\Program' is not recognized

**Error:**
```
'C:\Program' is not recognized as an internal or external command,
operable program or batch file.
```

**Cause:**
PyOutline wrapper scripts (`opencue_wrap_frame`, `pycuerun`) don't properly quote paths with spaces on Windows.

**Solution:**
Bypass PyOutline entirely. Use direct XML submission via `opencue.api.launchSpecAndWait()` instead of `outline.cuerun.launch()`.

---

### 3. Module Not Found: opencue

**Error:**
```
ModuleNotFoundError: No module named 'opencue'
```

**Cause:**
OpenCue libraries not installed in Python 3.9.

**Solution:**
```cmd
"C:\Program Files\Python39\python.exe" -m pip install opencue opencue-outline
```

---

### 4. Connection Refused to Cuebot

**Error:**
```
grpc._channel._InactiveRpcError: failed to connect to all addresses
```

**Cause:**
- Cuebot server not running
- Wrong host/port
- Firewall blocking connection

**Solution:**
1. Verify Cuebot is running
2. Check `CUEBOT_HOST` setting (default: `10.40.14.25:8443`)
3. Test connectivity: `telnet 10.40.14.25 8443`

---

### 5. Maya Scene Not Saved

**Error:**
```
Validation Error: Maya file is required (save your scene first)
```

**Cause:**
Attempting to submit an unsaved scene.

**Solution:**
Save your Maya scene before submitting.

---

### 6. UI Not Updating After Code Changes

**Problem:**
Changes to `maya_submit.py` not reflected in Maya.

**Solution:**
Reload the module:
```python
import importlib
import maya_submit
importlib.reload(maya_submit)
maya_submit.main()
```

---

### 7. PySide Import Error

**Error:**
```
ImportError: No module named 'PySide6'
```

**Cause:**
Running in an older Maya version without PySide6.

**Solution:**
The code has a fallback to PySide2:
```python
try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
```

If this still fails, you may be running outside Maya or in a very old version.

---

### 8. Cannot Launch Jobs as Root

**Error:**
```
Failed to launch and add job: Cannot launch jobs as root.
```

**Cause:**
The XML spec has `<uid>0</uid>`, and UID 0 is root. OpenCue blocks root submissions for security.

**Solution:**
Use a non-root UID (1000+):
```xml
<uid>1000</uid>
```

---

### 9. Show Does Not Exist

**Error:**
```
CueException: Show 'testing' does not exist
```

**Cause:**
The show specified doesn't exist in OpenCue.

**Solution:**
1. Create the show in CueGUI or via API
2. Or change the show name to an existing show

---

### 9. Service Not Found

**Error:**
```
Service 'maya' is not a valid service
```

**Cause:**
The service tag doesn't exist in OpenCue.

**Solution:**
1. Create the service in OpenCue admin
2. Or use an existing service name

---

### 10. Log Path Not Accessible

**Problem:**
Can't access the log files at the returned path.

**Cause:**
- Network share not mounted
- Permissions issue
- Path format issue (mixed slashes)

**Solution:**
1. Verify the network share is accessible: `dir \\10.40.14.25\RenderOutputRepo`
2. Check permissions on the share
3. Log path uses backslashes for Windows compatibility

---

## Debugging Tips

### View Generated XML Spec
Add this to `maya_submit_worker.py` before submission:
```python
spec = buildJobSpec(jobData)
print("Generated spec:")
print(spec)
```

### View Job Data JSON
The temp JSON file is deleted after submission. To preserve it:
```python
# In maya_submit.py, comment out the cleanup:
# os.unlink(jobDataFile)
print("Job data saved to:", jobDataFile)
```

### Test Worker Script Directly
```cmd
"C:\Program Files\Python39\python.exe" maya_submit_worker.py job_data.json 10.40.14.25:8443
```

### Check Cuebot Connection
```python
import sys
sys.path.insert(0, r"C:\Program Files\Python39\Lib\site-packages")
from opencue.cuebot import Cuebot
Cuebot.setHosts(["10.40.14.25:8443"])
import opencue
print(opencue.api.getShows())
```

---

## Getting Help

- OpenCue GitHub Issues: https://github.com/AcademySoftwareFoundation/OpenCue/issues
- OpenCue Documentation: https://www.opencue.io/docs/
