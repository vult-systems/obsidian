# OpenCue Render Node Setup

## Requirements
- Windows 10/11
- Python 3.9+
- Network access to 10.40.14.25

## Setup Steps

### 1. Check Python Installation

```powershell
python --version
where python
```

If Python isn't found or env vars aren't working, find it manually:
```powershell
# Common locations
dir "C:\Python39\python.exe"
dir "C:\Program Files\Python39\python.exe"
dir "C:\Users\*\AppData\Local\Programs\Python\Python39\python.exe"
```

Use the full path if needed (e.g., `C:\Python39\python.exe` instead of `python`).

### 2. Install RQD and Dependencies

```powershell
pip install opencue-rqd
```

**If you get "wmi not found" error:**
```powershell
pip install wmi
pip install opencue-rqd
```

**If pip isn't in PATH:**
```powershell
C:\Python39\python.exe -m pip install wmi opencue-rqd
```

### 3. Set Environment Variable

Open **System Properties → Environment Variables → User Variables**

Add:
- **Name**: `CUEBOT_HOSTNAME`
- **Value**: `10.40.14.25`

**IMPORTANT**: Close and reopen PowerShell after setting. Verify it took:
```powershell
echo $env:CUEBOT_HOSTNAME
```

Should print `10.40.14.25`. If blank, the variable didn't apply - try setting as System variable instead of User, or set in the current session:
```powershell
$env:CUEBOT_HOSTNAME = "10.40.14.25"
```

### 4. Test RQD

```powershell
python -m rqd
```

Or with full path:
```powershell
C:\Python39\python.exe -m rqd
```

Should show:
```
WARNING:root:CUEBOT_HOSTNAME: 10.40.14.25
WARNING   openrqd-rqcore    : RQD Started
```

If it shows `CUEBOT_HOSTNAME: localhost`, the env var isn't set. Set it in the same session before running:
```powershell
$env:CUEBOT_HOSTNAME = "10.40.14.25"
python -m rqd
```

### 5. Verify in CueGUI

On any machine with CueGUI, check **Monitor Hosts** - this machine should appear with status **UP**.

---

## Running as Service (Optional)

For unattended operation, install NSSM from https://nssm.cc:

```powershell
# Download nssm.exe to C:\OpenCue\
nssm install OpenCueRQD "C:\Python39\python.exe" "-m" "rqd"
nssm set OpenCueRQD AppEnvironmentExtra "CUEBOT_HOSTNAME=10.40.14.25"
nssm start OpenCueRQD
```

---

## Troubleshooting

### "python" not recognized
Use full path: `C:\Python39\python.exe -m rqd`

Or add Python to PATH manually:
```powershell
$env:PATH += ";C:\Python39;C:\Python39\Scripts"
```

### "No module named wmi"
```powershell
pip install wmi
```

### RQD won't start / port 8444 error
```powershell
Get-Process python* | Stop-Process -Force
python -m rqd
```

### Host shows DOWN in CueGUI
- Check RQD is running
- Check `CUEBOT_HOSTNAME` is set correctly: `echo $env:CUEBOT_HOSTNAME`
- Test network: `Test-NetConnection 10.40.14.25 -Port 8443`

### Environment variable not applying
Try System variable instead of User variable, or set directly in PowerShell before running RQD:
```powershell
$env:CUEBOT_HOSTNAME = "10.40.14.25"
python -m rqd
```
