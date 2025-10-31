#!/bin/bash

# Install script for Ebonhawk Maintenance Agent

echo "=== Installing Ebonhawk Maintenance Agent ==="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please run this script as a regular user with sudo privileges, not as root"
   exit 1
fi

# Install psutil if not present
echo "Checking dependencies..."
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "Installing psutil..."
    pip3 install --user psutil
fi

# Make agent executable
chmod +x /home/dave/Scripts/ebonhawk_maintenance_agent.py

# Copy systemd service file
echo "Installing systemd service..."
sudo cp /home/dave/Scripts/ebonhawk-maintenance.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
echo "Enabling service..."
sudo systemctl enable ebonhawk-maintenance.service

echo "Starting service..."
sudo systemctl start ebonhawk-maintenance.service

# Check status
sleep 2
sudo systemctl status ebonhawk-maintenance.service --no-pager

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Useful commands:"
echo "  Check status:       sudo systemctl status ebonhawk-maintenance"
echo "  View logs:          sudo journalctl -u ebonhawk-maintenance -f"
echo "  Stop service:       sudo systemctl stop ebonhawk-maintenance"
echo "  Start service:      sudo systemctl start ebonhawk-maintenance"
echo "  Check agent:        python3 /home/dave/Scripts/ebonhawk_maintenance_agent.py --status"
echo "  Manual updates:     /home/dave/Scripts/ebonhawk_update_now.sh"
echo "  Live dashboard:     python3 /home/dave/Scripts/ebonhawk_dashboard.py"
echo ""
echo "Agent data stored in: ~/.ebonhawk-maintenance/"
echo ""
echo "Auto-updates:"
echo "  • Agent updates: Daily check"
echo "  • System updates: Daily at 3:00 AM"
echo "  • Security updates: Installed automatically"
echo "  • Kernel updates: Installed with scheduled reboot"