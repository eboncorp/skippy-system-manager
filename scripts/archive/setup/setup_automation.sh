#!/bin/bash

# Skippy Automation Setup - Optimized Installation
# Sets up essential automation and monitoring components

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}        Skippy Automation Setup                    ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo

# Variables
SKIPPY_HOME="/home/ebon/Skippy"
SCRIPTS_DIR="$SKIPPY_HOME/Scripts"
NEXUS_DIR="$SKIPPY_HOME/app-to-deploy/NexusController"
BIN_DIR="/home/ebon/.local/bin"

# Function to print status
status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 1. Setup critical automation scripts
echo -e "${BLUE}Setting up automation scripts...${NC}"

# Create maintenance cron job
cat > "$SCRIPTS_DIR/skippy_maintenance.sh" << 'EOF'
#!/bin/bash
# Daily maintenance tasks for Skippy

LOG_DIR="/var/log/skippy"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/maintenance_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 1. Cleanup old logs
log "Starting maintenance"
find /tmp -name "skippy_*.json" -mtime +7 -delete
find "$LOG_DIR" -name "*.log" -mtime +30 -delete

# 2. Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# 3. Check system health
if command -v python3 >/dev/null; then
    python3 -c "
import psutil
cpu = psutil.cpu_percent(interval=1)
mem = psutil.virtual_memory().percent
if cpu > 80 or mem > 80:
    print(f'WARNING: High resource usage - CPU: {cpu}%, Memory: {mem}%')
" >> "$LOG_FILE" 2>&1
fi

log "Maintenance completed"
EOF

chmod +x "$SCRIPTS_DIR/skippy_maintenance.sh"
status "Created maintenance script"

# 2. Create network scanner wrapper
cat > "$BIN_DIR/network-scan" << 'EOF'
#!/bin/bash
# Network scanner with optimized settings

SKIPPY_HOME="/home/ebon/Skippy"

if [ -f "$SKIPPY_HOME/active_network_scan_v2.py" ]; then
    echo "Starting network scan..."
    python3 "$SKIPPY_HOME/active_network_scan_v2.py" "$@"
elif [ -f "$SKIPPY_HOME/active_network_scan.py" ]; then
    echo "Starting network scan (v1)..."
    python3 "$SKIPPY_HOME/active_network_scan.py" "$@"
else
    echo "Network scanner not found"
    exit 1
fi
EOF

chmod +x "$BIN_DIR/network-scan"
status "Created network scanner wrapper"

# 3. Setup Docker monitoring if Docker is installed
if command -v docker >/dev/null 2>&1; then
    echo -e "${BLUE}Setting up Docker monitoring...${NC}"

    cat > "$SCRIPTS_DIR/docker_monitor.sh" << 'EOF'
#!/bin/bash
# Monitor Docker containers

check_containers() {
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}" 2>/dev/null
}

check_resources() {
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null
}

case "$1" in
    status)
        check_containers
        ;;
    resources)
        check_resources
        ;;
    *)
        echo "Docker Container Status:"
        check_containers
        echo ""
        echo "Resource Usage:"
        check_resources
        ;;
esac
EOF

    chmod +x "$SCRIPTS_DIR/docker_monitor.sh"
    status "Created Docker monitor"
else
    warning "Docker not installed - skipping Docker monitoring"
fi

# 4. Create system health check script
cat > "$SCRIPTS_DIR/health_check.py" << 'EOF'
#!/usr/bin/env python3
"""System health check for Skippy"""

import psutil
import json
import socket
from datetime import datetime

def check_health():
    """Perform comprehensive health check"""

    health = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "status": "healthy",
        "checks": {}
    }

    # CPU check
    cpu_percent = psutil.cpu_percent(interval=1)
    health["checks"]["cpu"] = {
        "value": cpu_percent,
        "status": "ok" if cpu_percent < 80 else "warning"
    }

    # Memory check
    mem = psutil.virtual_memory()
    health["checks"]["memory"] = {
        "percent": mem.percent,
        "available_gb": round(mem.available / (1024**3), 2),
        "status": "ok" if mem.percent < 80 else "warning"
    }

    # Disk check
    disk = psutil.disk_usage('/')
    health["checks"]["disk"] = {
        "percent": disk.percent,
        "free_gb": round(disk.free / (1024**3), 2),
        "status": "ok" if disk.percent < 80 else "warning"
    }

    # Network check
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        health["checks"]["network"] = {"status": "ok", "internet": True}
    except:
        health["checks"]["network"] = {"status": "error", "internet": False}

    # Overall status
    statuses = [c["status"] for c in health["checks"].values()]
    if "error" in statuses:
        health["status"] = "error"
    elif "warning" in statuses:
        health["status"] = "warning"

    return health

if __name__ == "__main__":
    result = check_health()
    print(json.dumps(result, indent=2))

    # Return exit code based on status
    if result["status"] == "error":
        exit(2)
    elif result["status"] == "warning":
        exit(1)
    else:
        exit(0)
EOF

chmod +x "$SCRIPTS_DIR/health_check.py"
status "Created health check script"

# 5. Create backup wrapper
cat > "$SCRIPTS_DIR/skippy_backup.sh" << 'EOF'
#!/bin/bash
# Skippy backup wrapper

BACKUP_DIR="/home/ebon/backups"
SKIPPY_HOME="/home/ebon/Skippy"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup important Skippy files
echo "Backing up Skippy configuration..."
tar -czf "$BACKUP_DIR/skippy_config_$DATE.tar.gz" \
    "$SKIPPY_HOME/config.yaml" \
    "$SKIPPY_HOME/conversations/" \
    "$SKIPPY_HOME/.env" \
    2>/dev/null

# Cleanup old backups (keep last 7)
ls -t "$BACKUP_DIR"/skippy_config_*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null

echo "Backup completed: $BACKUP_DIR/skippy_config_$DATE.tar.gz"
EOF

chmod +x "$SCRIPTS_DIR/skippy_backup.sh"
status "Created backup script"

# 6. Setup cron jobs
echo -e "${BLUE}Setting up scheduled tasks...${NC}"

CRON_FILE="/tmp/skippy_cron"
cat > "$CRON_FILE" << EOF
# Skippy Automated Tasks
# Daily maintenance at 2 AM
0 2 * * * $SCRIPTS_DIR/skippy_maintenance.sh

# Health check every hour
0 * * * * $SCRIPTS_DIR/health_check.py > /tmp/skippy_health.json

# Weekly backup on Sunday at 3 AM
0 3 * * 0 $SCRIPTS_DIR/skippy_backup.sh
EOF

echo -e "${YELLOW}To install cron jobs, run: crontab $CRON_FILE${NC}"

# 7. Create monitoring dashboard script
cat > "$BIN_DIR/skippy-dash" << 'EOF'
#!/bin/bash
# Skippy Dashboard - System Overview

clear
echo "╔════════════════════════════════════════════════╗"
echo "║           SKIPPY SYSTEM DASHBOARD              ║"
echo "╚════════════════════════════════════════════════╝"
echo

# System info
echo "📊 System Information:"
echo "───────────────────────"
hostname -I | awk '{print "IP: " $1}'
uptime -p
echo

# Resource usage
echo "💻 Resource Usage:"
echo "───────────────────────"
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent(interval=1)}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage('/').percent}%')
"

echo
echo "🔧 Services:"
echo "───────────────────────"
if pgrep -f "skippy" >/dev/null; then
    echo "✅ Skippy: Running"
else
    echo "❌ Skippy: Stopped"
fi

if systemctl is-active docker >/dev/null 2>&1; then
    echo "✅ Docker: Running"
    docker ps -q | wc -l | xargs echo "   Containers:"
fi

echo
echo "📁 Recent Logs:"
echo "───────────────────────"
ls -t /home/ebon/Skippy/conversations/*.md 2>/dev/null | head -3 | xargs -I {} basename {}

echo
echo "Commands: skippy | skip auth | network-scan | skippy-dash"
EOF

chmod +x "$BIN_DIR/skippy-dash"
status "Created dashboard script"

# 8. Install systemd timer for health checks (better than cron)
cat > "/tmp/skippy-health.service" << EOF
[Unit]
Description=Skippy Health Check
After=network.target

[Service]
Type=oneshot
User=ebon
ExecStart=$SCRIPTS_DIR/health_check.py
StandardOutput=journal
EOF

cat > "/tmp/skippy-health.timer" << EOF
[Unit]
Description=Run Skippy Health Check every hour
Requires=skippy-health.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

status "Created systemd timer files"
echo -e "${YELLOW}To install timers: sudo cp /tmp/skippy-health.* /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable skippy-health.timer${NC}"

# Final summary
echo
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       Automation Setup Complete!                   ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo
echo "New commands available:"
echo "  network-scan    - Run network scanner"
echo "  skippy-dash     - System dashboard"
echo ""
echo "Automation scripts in: $SCRIPTS_DIR"
echo "  - skippy_maintenance.sh  (daily cleanup)"
echo "  - health_check.py        (system health)"
echo "  - docker_monitor.sh      (container monitoring)"
echo "  - skippy_backup.sh       (config backup)"
echo ""
echo "Run 'skippy-dash' to see system overview"