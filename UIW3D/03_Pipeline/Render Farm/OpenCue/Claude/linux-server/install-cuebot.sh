#!/bin/bash
#
# OpenCue Cuebot + PostgreSQL Installation Script
# For Ubuntu/Debian Linux Server
#
# Usage: sudo ./install-cuebot.sh
#

set -e

echo "=========================================="
echo "OpenCue Cuebot Installation"
echo "=========================================="

# Configuration - EDIT THESE
POSTGRES_PASSWORD="cuebot_secure_password_change_me"
CUEBOT_VERSION="latest"  # or specific version like "0.25.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo ""
echo "Step 1: Installing system dependencies..."
apt-get update
apt-get install -y \
    openjdk-17-jdk \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl

echo ""
echo "Step 2: Configuring PostgreSQL..."

# Start PostgreSQL
systemctl enable postgresql
systemctl start postgresql

# Create OpenCue database and user
sudo -u postgres psql -c "CREATE USER cuebot WITH PASSWORD '${POSTGRES_PASSWORD}';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "CREATE DATABASE cuebot OWNER cuebot;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cuebot TO cuebot;"

# Allow password authentication for cuebot user
PG_HBA=$(sudo -u postgres psql -t -c "SHOW hba_file;" | tr -d ' ')
if ! grep -q "cuebot" "$PG_HBA"; then
    echo "host    cuebot          cuebot          0.0.0.0/0               md5" >> "$PG_HBA"
    systemctl reload postgresql
fi

# Allow external connections
PG_CONF=$(sudo -u postgres psql -t -c "SHOW config_file;" | tr -d ' ')
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
systemctl reload postgresql

echo ""
echo "Step 3: Creating OpenCue directories..."
mkdir -p /opt/opencue
mkdir -p /opt/opencue/logs
mkdir -p /opt/opencue/conf
mkdir -p /var/log/opencue

echo ""
echo "Step 4: Downloading Cuebot..."

# Download latest Cuebot JAR
cd /opt/opencue
if [ "$CUEBOT_VERSION" == "latest" ]; then
    # Get latest release
    DOWNLOAD_URL=$(curl -s https://api.github.com/repos/AcademySoftwareFoundation/OpenCue/releases/latest | grep "browser_download_url.*cuebot.*jar" | cut -d '"' -f 4 | head -1)
    if [ -z "$DOWNLOAD_URL" ]; then
        echo "Could not find Cuebot JAR in latest release. Downloading from Docker image..."
        # Alternative: extract from Docker image
        docker pull opencue/cuebot
        docker create --name temp-cuebot opencue/cuebot
        docker cp temp-cuebot:/opt/opencue/cuebot-latest.jar /opt/opencue/
        docker rm temp-cuebot
    else
        wget -O cuebot-latest.jar "$DOWNLOAD_URL"
    fi
else
    wget -O cuebot-latest.jar "https://github.com/AcademySoftwareFoundation/OpenCue/releases/download/v${CUEBOT_VERSION}/cuebot-${CUEBOT_VERSION}-all.jar"
fi

echo ""
echo "Step 5: Running database migrations (Flyway)..."

# Download Flyway
FLYWAY_VERSION="9.11.0"
cd /tmp
wget -q https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/${FLYWAY_VERSION}/flyway-commandline-${FLYWAY_VERSION}.tar.gz
tar -xzf flyway-commandline-${FLYWAY_VERSION}.tar.gz

# Clone OpenCue repo for migrations (if not exists)
if [ ! -d "/opt/opencue/repo" ]; then
    git clone --depth 1 https://github.com/AcademySoftwareFoundation/OpenCue.git /opt/opencue/repo
fi

# Run migrations
cd /tmp/flyway-${FLYWAY_VERSION}
./flyway -url="jdbc:postgresql://localhost/cuebot" \
         -user=cuebot \
         -password="${POSTGRES_PASSWORD}" \
         -locations="filesystem:/opt/opencue/repo/cuebot/src/main/resources/conf/ddl/postgres/migrations" \
         migrate

# Run seed data
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h localhost -U cuebot -d cuebot -f /opt/opencue/repo/cuebot/src/main/resources/conf/ddl/postgres/seed_data.sql

echo ""
echo "Step 6: Creating Cuebot configuration..."

cat > /opt/opencue/conf/opencue.properties << EOF
# OpenCue Cuebot Configuration

# Database connection
datasource.cue-data-source.driver-class-name=org.postgresql.Driver
datasource.cue-data-source.jdbc-url=jdbc:postgresql://localhost/cuebot
datasource.cue-data-source.username=cuebot
datasource.cue-data-source.password=${POSTGRES_PASSWORD}

# gRPC ports
grpc.cue_port=8443
grpc.rqd_port=8444

# Logging
logging.level.com.imageworks.spcue=INFO
logging.file.name=/var/log/opencue/cuebot.log

# Frame log directory (where RQD writes logs - must be accessible)
CUE_FRAME_LOG_DIR=/mnt/renders/logs
EOF

echo ""
echo "Step 7: Creating systemd service..."

cat > /etc/systemd/system/cuebot.service << EOF
[Unit]
Description=OpenCue Cuebot Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/java -jar /opt/opencue/cuebot-latest.jar --spring.config.location=/opt/opencue/conf/opencue.properties
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cuebot

echo ""
echo "Step 8: Configuring firewall..."
ufw allow 8443/tcp comment "OpenCue Cuebot gRPC (clients)"
ufw allow 8444/tcp comment "OpenCue Cuebot gRPC (RQD)"
ufw allow 5432/tcp comment "PostgreSQL (if needed externally)"

echo ""
echo "Step 9: Starting Cuebot..."
systemctl start cuebot

# Wait for startup
sleep 5

# Check status
if systemctl is-active --quiet cuebot; then
    echo -e "${GREEN}=========================================="
    echo "Cuebot is running!"
    echo "==========================================${NC}"
else
    echo -e "${RED}Cuebot failed to start. Check logs:${NC}"
    journalctl -u cuebot -n 50
    exit 1
fi

echo ""
echo "Step 10: Installing Python tools (pycue, cuegui, cueadmin)..."
pip3 install opencue-pycue opencue-cuegui opencue-cueadmin opencue-cuesubmit

# Create default config for Python tools
mkdir -p /root/.config/opencue
cat > /root/.config/opencue/opencue.yaml << EOF
cuebot.facility_default: local
cuebot.facility:
    local:
        - localhost:8443
EOF

echo ""
echo -e "${GREEN}=========================================="
echo "Installation Complete!"
echo "==========================================${NC}"
echo ""
echo "Cuebot is running on ports 8443 (clients) and 8444 (RQD)"
echo ""
echo "Next steps:"
echo "1. Edit /opt/opencue/conf/opencue.properties if needed"
echo "2. Set CUE_FRAME_LOG_DIR to your shared storage path"
echo "3. Run: cueadmin -lh   (to list hosts once RQD connects)"
echo "4. Run: cuegui         (to launch the GUI)"
echo ""
echo "To check status: systemctl status cuebot"
echo "To view logs: journalctl -u cuebot -f"
