# OpenCue Render Node Setup

## Requirements
- Windows 10/11
- Python 3.9+ (install to `C:\Python39` - avoid paths with spaces)
- Network access to 10.40.14.25
## Setup Steps

### 1. Install RQD
```powershell
pip install opencue-rqd
```

### 2. Set Environment Variable
Open **System Properties → Environment Variables → User Variables**
  
Add:
- **Name**: `CUEBOT_HOSTNAME`
- **Value**: `10.40.14.25`
  
### 3. Test RQD
Open new PowerShell window:

```powershell
python -m rqd
```
  
Should show:

```
WARNING:root:CUEBOT_HOSTNAME: 10.40.14.25
WARNING   openrqd-rqcore    : RQD Started
```


### 4. Verify in CueGUI
On any machine with CueGUI, check **Monitor Hosts** - your machine should appear with status **UP**.
  
## Running as Service (Optional)
For unattended operation, install NSSM from https://nssm.cc and run:

```powershell
nssm install OpenCueRQD "C:\Python39\python.exe" "-m" "rqd"
nssm set OpenCueRQD AppEnvironmentExtra "CUEBOT_HOSTNAME=10.40.14.25"
nssm start OpenCueRQD
```

## Troubleshooting
**RQD won't start / port error**

```powershell
Get-Process python* | Stop-Process -Force
python -m rqd
```

**Host shows DOWN in CueGUI**
- Check RQD is running
- Check firewall allows port 8444
- Run: `Test-NetConnection 10.40.14.25 -Port 8443`