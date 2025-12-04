# OpenCue POC - Current Status (Dec 3, 2025)

## What's Working

### Linux Server (10.40.14.25)
- **PostgreSQL**: Running, database `cuebot_local` with user `cuebot` (password: `uiw3d`)
- **Cuebot**: Running as systemd service, auto-starts on boot
- **Ports**: 8443 (client API), 8444 (RQD), 5432 (PostgreSQL)

Service file: `/etc/systemd/system/cuebot.service`
```ini
[Unit]
Description=OpenCue Cuebot Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=perforce
WorkingDirectory=/home/perforce/OpenCue/cuebot-jar
ExecStart=/usr/bin/java -jar /home/perforce/OpenCue/cuebot-jar/cuebot-1.13.8-all.jar --datasource.cue-data-source.jdbc-url=jdbc:postgresql://localhost/cuebot_local --datasource.cue-data-source.username=cuebot --datasource.cue-data-source.password=uiw3d --log.frame-log-root.default_os=/angd_server_pool/renderRepo/OpenCue/Logs --log.frame-log-root.Windows=//10.40.14.25/RenderOutputRepo/OpenCue/Logs
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Windows Client (10.40.14.38)
- **RQD**: Works when started manually with `python -m rqd`
- **CueGUI**: Works, connects to Cuebot, shows hosts and jobs
- **Host registration**: Shows UP and OPEN in CueGUI

### Environment Variables (Windows - set as User variables)
| Variable | Value |
|----------|-------|
| `CUEBOT_HOSTNAME` | `10.40.14.25` |
| `CUEBOT_HOSTS` | `10.40.14.25` |
| `CUE_FRAME_LOG_DIR` | `C:\OpenCue\Logs` |

### Log Paths
- **Linux jobs**: `/angd_server_pool/renderRepo/OpenCue/Logs`
- **Windows jobs**: `//10.40.14.25/RenderOutputRepo/OpenCue/Logs` (UNC path)
- Windows UNC accessible at: `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs`

---

## What's NOT Working

### Job Execution
Test jobs submit but fail with `exit_status: 1`. Two issues identified:

1. **Path quoting issue**: Commands with spaces in paths fail
   ```
   'C:\Program' is not recognized as an internal or external command
   ```
   The OpenCue wrapper scripts don't properly quote paths with spaces.

2. **OS must be specified at submission**: Jobs must include `os="Windows"` parameter to use Windows log paths.

---

## How to Start Services

### Linux Server
```bash
# Cuebot starts automatically, but to manage:
sudo systemctl status cuebot
sudo systemctl restart cuebot
sudo journalctl -u cuebot -f  # Watch logs
```

### Windows Client
```powershell
# Start RQD (must run in foreground for now)
python -m rqd

# Start CueGUI (separate terminal)
cuegui
```

---

## Job Submission (Python)

```python
import os
os.environ["CUEBOT_HOSTS"] = "10.40.14.25"

import outline
from outline import Outline, cuerun
from outline.modules.shell import Shell

ol = Outline(name="my_job", show="testing", shot="shot01")
layer = Shell("my_layer", command=["hostname"])
layer.set_service("shell")
ol.add_layer(layer)

# IMPORTANT: os="Windows" required for Windows log paths
jobs = cuerun.launch(ol, pause=False, os="Windows")
```

---

## Next Steps

1. **Maya Integration**: Set up Maya submission (bypasses wrapper issues)
2. **RQD as Service**: Install RQD as Windows service for unattended operation
3. **Fix path quoting**: Either:
   - Install Python/OpenCue in path without spaces
   - Or modify wrapper scripts to handle spaces
4. **Test with real render**: Submit actual Maya/Arnold job

---

## Useful Commands

### CueGUI
- Monitor Hosts: See registered render nodes
- Monitor Jobs: See submitted jobs
- Right-click frame → View Log (if log path accessible)

### Linux Server
```bash
# Check Cuebot status
sudo systemctl status cuebot

# View recent logs
sudo journalctl -u cuebot -n 100

# Restart Cuebot
sudo systemctl restart cuebot
```

### Windows
```powershell
# Check if RQD is running
Get-Process python* | Where-Object { $_.CommandLine -like "*rqd*" }

# Kill stuck RQD
Get-Process python* | Stop-Process -Force

# Test connection to Cuebot
Test-NetConnection -ComputerName 10.40.14.25 -Port 8443
```

---

## Architecture Diagram

```
Artist Workstation                    Linux Server (10.40.14.25)
┌─────────────────┐                  ┌─────────────────────────┐
│ Maya + Submit   │                  │ Cuebot (:8443/:8444)    │
│ CueGUI          │ ───gRPC───────►  │     ↓                   │
└─────────────────┘                  │ PostgreSQL (:5432)      │
                                     └─────────────────────────┘
                                               │
                                               ▼
                                     ┌─────────────────┐
                                     │ Windows Render  │
                                     │ Nodes (RQD)     │
                                     │ 10.40.14.38     │
                                     └─────────────────┘

Shared Storage:
- Linux: /angd_server_pool/renderRepo/OpenCue/Logs
- Windows: \\10.40.14.25\RenderOutputRepo\OpenCue\Logs
```

---

## Show Created
- `testing` - test show for POC

---

## Known Issues

1. **PySide2 warnings in CueGUI** - Harmless, can ignore:
   ```
   QObject: Cannot create children for a parent that is in a different thread
   ```

2. **VERSION.in not found** - Cosmetic warning, harmless

3. **RQD port conflict** - If RQD fails to start with port 8444 error, kill existing Python processes

4. **Backslash in job names** - Windows domain usernames create paths with backslashes that may cause issues
