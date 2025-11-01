#!/bin/bash

# Skippy Setup Script - Optimized Installation
# Sets up essential Skippy components without redundancy

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Skippy Optimized Setup for Ebon             ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo

# Variables
SKIPPY_HOME="/home/ebon/Skippy"
BIN_DIR="/home/ebon/.local/bin"
SCRIPTS_DIR="$SKIPPY_HOME/Scripts"

# Function to print status
status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

# 1. Install Python dependencies (optimized - only essentials)
echo -e "${BLUE}Installing essential Python packages...${NC}"
PACKAGES=(
    "psutil"      # System monitoring
    "rich"        # Terminal formatting
    "pyyaml"      # Config management
    "docker"      # Docker integration
    "requests"    # API calls
)

for pkg in "${PACKAGES[@]}"; do
    if pip3 show "$pkg" &>/dev/null; then
        status "$pkg already installed"
    else
        echo "Installing $pkg..."
        pip3 install "$pkg" --user --quiet || warning "Failed to install $pkg"
    fi
done

# 2. Create bin directory if needed
if [ ! -d "$BIN_DIR" ]; then
    mkdir -p "$BIN_DIR"
    status "Created $BIN_DIR"
fi

# 3. Create main skippy command
echo -e "${BLUE}Creating skippy command...${NC}"
cat > "$BIN_DIR/skippy" << 'EOF'
#!/bin/bash
# Skippy - AI Assistant Interface

SKIPPY_HOME="/home/ebon/Skippy"
ACTION="${1:-help}"

case "$ACTION" in
    status)
        echo "Skippy Status:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Location: $SKIPPY_HOME"
        echo "Scripts: $(find $SKIPPY_HOME -name "*.py" -type f | wc -l) Python files"
        echo "Conversations: $(ls $SKIPPY_HOME/conversations/*.md 2>/dev/null | wc -l) logs"
        if pgrep -f "skippy" >/dev/null; then
            echo "Services: Running"
        else
            echo "Services: Not running"
        fi
        ;;

    scan)
        # Network scan
        if [ -f "$SKIPPY_HOME/active_network_scan_v2.py" ]; then
            python3 "$SKIPPY_HOME/active_network_scan_v2.py"
        else
            echo "Network scanner not found"
        fi
        ;;

    maintain)
        # AI maintenance
        if [ -f "$SKIPPY_HOME/ai_maintenance_engine_v2.py" ]; then
            python3 "$SKIPPY_HOME/ai_maintenance_engine_v2.py"
        else
            echo "Maintenance engine not found"
        fi
        ;;

    monitor)
        # System monitoring
        if [ -f "$SKIPPY_HOME/system_monitor.py" ]; then
            python3 "$SKIPPY_HOME/system_monitor.py"
        else
            echo "System monitor not found"
        fi
        ;;

    backup)
        # Run backup
        if [ -f "$SCRIPTS_DIR/full_home_backup.sh" ]; then
            "$SCRIPTS_DIR/full_home_backup.sh"
        else
            echo "Backup script not found"
        fi
        ;;

    help|*)
        echo "Skippy - AI Assistant System"
        echo ""
        echo "Usage: skippy [command]"
        echo ""
        echo "Commands:"
        echo "  status   - Show Skippy status"
        echo "  scan     - Run network scan"
        echo "  maintain - Run AI maintenance"
        echo "  monitor  - Start system monitor"
        echo "  backup   - Run backup"
        echo "  help     - Show this help"
        ;;
esac
EOF

chmod +x "$BIN_DIR/skippy"
status "Created skippy command"

# 4. Create system monitor (lightweight)
echo -e "${BLUE}Creating system monitor...${NC}"
cat > "$SKIPPY_HOME/system_monitor.py" << 'EOF'
#!/usr/bin/env python3
"""Lightweight system monitor for Skippy"""

import psutil
import time
import json
from datetime import datetime

def get_system_stats():
    """Get current system statistics"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
        },
        "disk": {
            "percent": psutil.disk_usage('/').percent,
            "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
        },
        "network": len(psutil.net_connections()),
        "processes": len(psutil.pids())
    }
    return stats

def monitor_loop():
    """Main monitoring loop"""
    print("Skippy System Monitor")
    print("=" * 50)

    while True:
        try:
            stats = get_system_stats()
            print(f"\r[{stats['timestamp'].split('T')[1][:8]}] "
                  f"CPU: {stats['cpu_percent']:5.1f}% | "
                  f"RAM: {stats['memory']['percent']:5.1f}% | "
                  f"Disk: {stats['disk']['percent']:5.1f}% | "
                  f"Procs: {stats['processes']:4d}", end='', flush=True)

            # Save to log every minute
            if int(time.time()) % 60 == 0:
                log_file = f"/tmp/skippy_monitor_{datetime.now().strftime('%Y%m%d')}.json"
                with open(log_file, 'a') as f:
                    json.dump(stats, f)
                    f.write('\n')

            time.sleep(5)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()
EOF

chmod +x "$SKIPPY_HOME/system_monitor.py"
status "Created system monitor"

# 5. Setup conversation logger
echo -e "${BLUE}Setting up conversation logger...${NC}"
mkdir -p "$SKIPPY_HOME/conversations"
cat > "$SKIPPY_HOME/log_conversation.sh" << 'EOF'
#!/bin/bash
# Log conversations with Claude

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H%M%S)
LOG_FILE="$HOME/Skippy/conversations/claude_${DATE}_${TIME}.md"

echo "# Claude Conversation - $DATE $TIME" > "$LOG_FILE"
echo "" >> "$LOG_FILE"
echo "Starting conversation log..."
echo "Log file: $LOG_FILE"
EOF

chmod +x "$SKIPPY_HOME/log_conversation.sh"
status "Created conversation logger"

# 6. Create quick launcher for common tasks
echo -e "${BLUE}Creating quick launcher...${NC}"
cat > "$BIN_DIR/skip" << 'EOF'
#!/bin/bash
# Quick launcher for Skippy tasks

case "$1" in
    auth) sudo /home/ebon/authorize_claude ;;
    revoke) sudo /home/ebon/revoke_claude ;;
    scan) skippy scan ;;
    monitor) skippy monitor ;;
    status) skippy status ;;
    *) skippy help ;;
esac
EOF

chmod +x "$BIN_DIR/skip"
status "Created quick launcher 'skip'"

# 7. Setup systemd service (optional)
echo -e "${BLUE}Creating systemd service file...${NC}"
cat > "/tmp/skippy-monitor.service" << EOF
[Unit]
Description=Skippy System Monitor
After=network.target

[Service]
Type=simple
User=ebon
WorkingDirectory=/home/ebon/Skippy
ExecStart=/usr/bin/python3 /home/ebon/Skippy/system_monitor.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

status "Service file created at /tmp/skippy-monitor.service"
echo -e "${YELLOW}To install as service, run: sudo cp /tmp/skippy-monitor.service /etc/systemd/system/ && sudo systemctl daemon-reload${NC}"

# 8. Add to PATH if needed
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "" >> ~/.bashrc
    echo "# Skippy PATH" >> ~/.bashrc
    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> ~/.bashrc
    status "Added $BIN_DIR to PATH (reload shell or run: source ~/.bashrc)"
fi

# 9. Create config file
echo -e "${BLUE}Creating configuration...${NC}"
cat > "$SKIPPY_HOME/config.yaml" << EOF
# Skippy Configuration
skippy:
  version: "2.0"
  home: "/home/ebon/Skippy"
  user: "ebon"

monitoring:
  interval: 5
  log_dir: "/tmp"

network:
  scan_range: "10.0.0.0/24"

maintenance:
  auto_update: false
  check_interval: 3600
EOF

status "Created config.yaml"

# Final summary
echo
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       Skippy Setup Complete!                      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo
echo "Available commands:"
echo "  skippy       - Main command"
echo "  skip         - Quick launcher"
echo "  skip auth    - Authorize Claude (4 hours)"
echo "  skip revoke  - Revoke Claude authorization"
echo ""
echo "Run 'source ~/.bashrc' to update PATH or start a new shell"
echo "Run 'skippy help' for more information"