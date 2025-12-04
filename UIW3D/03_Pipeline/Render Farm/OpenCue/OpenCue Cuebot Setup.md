---

---
 ---
## Server
- **Host**: 10.40.14.25 (Ubuntu 24.04.3 LTS)
- **Cuebot Version**: 1.13.8
- **Ports**: 8443 (client API), 8444 (RQD communication)
## What We Did
### 1. Downloaded Cuebot JAR

```bash
mkdir -p ~/OpenCue/cuebot-jar
cd ~/OpenCue/cuebot-jar
curl -L -O https://github.com/AcademySoftwareFoundation/OpenCue/releases/download/v1.13.8/cuebot-1.13.8-all.jar
```

### 2. Created Frame Log Directory

```bash
mkdir -p /angd_server_pool/renderRepo/OpenCue/Logs
```
  
Path accessible via Windows: `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs`
  
### 3. Created Systemd Service
File: `/etc/systemd/system/cuebot.service`

```ini
[Unit]
Description=OpenCue Cuebot Server
After=network.target postgresql.service
Requires=postgresql.service
  
[Service]
Type=simple
User=perforce
WorkingDirectory=/home/perforce/OpenCue/cuebot-jar

ExecStart=/usr/bin/java -jar /home/perforce/OpenCue/cuebot-jar/cuebot-1.13.8-all.jar --datasource.cue-data-source.jdbc-url=jdbc:postgresql://localhost/cuebot_local --datasource.cue-data-source.username=cuebot --datasource.cue-data-source.password=uiw3d --log.frame-log-root.default_os=/angd_server_pool/renderRepo/OpenCue/Logs

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

```

### 4. Enabled and Started Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cuebot
sudo systemctl start cuebot
```

## Management Commands

```bash
# Check status
sudo systemctl status cuebot
  
# View logs
sudo journalctl -u cuebot -n 50
  
# Restart
sudo systemctl restart cuebot
  
# Stop
sudo systemctl stop cuebot
```
  
## Architecture Recap

```
Artist Workstation                    Linux Server (10.40.14.25)

┌─────────────────┐                  ┌─────────────────────────┐

│ Maya + Submit   │                  │ Cuebot (:8443/:8444)    │

│ CueGUI          │ ───gRPC───────▶  │     ↓                   │

└─────────────────┘                  │ PostgreSQL (:5432)      │

                                     └─────────────────────────┘

                                               │

                                               ▼

                                     ┌─────────────────┐

                                     │ Lab Machines    │

                                     │ (RQD - next)    │

                                     └─────────────────┘

```

## Shared Storage
- **Frame Logs**: `/angd_server_pool/renderRepo/OpenCue/Logs`
- **Windows UNC**: `\\10.40.14.25\RenderOutputRepo\OpenCue\Logs`
## Status
Cuebot running as system service, starts automatically on boot.
## Next Step
Deploy RQD to Windows lab machines.