#!/bin/bash

echo "=== Installing Ebon Media Server Maintenance Agent ==="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "Please run this script as a regular user with sudo privileges, not as root"
   exit 1
fi

# Install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-psutil curl

# Copy agent files to ebon server
echo "Copying agent files to ebon server..."
scp /home/dave/Scripts/ebon_maintenance_agent.py ebon@10.0.0.29:~/

# Create service file
cat > /tmp/ebon-maintenance.service << 'EOF'
[Unit]
Description=Ebon Media Server Maintenance Agent
After=network.target docker.service

[Service]
Type=simple
User=ebon
Group=ebon
WorkingDirectory=/home/ebon
ExecStart=/usr/bin/python3 /home/ebon/ebon_maintenance_agent.py --daemon
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to ebon
echo "Deploying service configuration..."
scp /tmp/ebon-maintenance.service ebon@10.0.0.29:/tmp/

# Install and start the service on ebon
echo "Installing service on ebon server..."
ssh ebon@10.0.0.29 << 'REMOTE_COMMANDS'
# First, kill any runaway noip2 processes
echo "Killing runaway noip2 processes..."
sudo pkill -9 noip2

# Install psutil if not present
pip3 install --user psutil

# Create necessary directories
sudo mkdir -p /var/log/ebon-maintenance
sudo mkdir -p /var/lib/ebon-maintenance
sudo chown ebon:ebon /var/log/ebon-maintenance
sudo chown ebon:ebon /var/lib/ebon-maintenance

# Make agent executable
chmod +x ~/ebon_maintenance_agent.py

# Install service
sudo cp /tmp/ebon-maintenance.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ebon-maintenance.service
sudo systemctl start ebon-maintenance.service

# Check status
sleep 3
sudo systemctl status ebon-maintenance.service
REMOTE_COMMANDS

echo ""
echo "=== Installation Complete ==="
echo ""
echo "The agent is now running on ebon server."
echo ""
echo "Useful commands (run on ebon server):"
echo "  Check status:       sudo systemctl status ebon-maintenance"
echo "  View logs:          sudo journalctl -u ebon-maintenance -f"
echo "  Stop service:       sudo systemctl stop ebon-maintenance"
echo "  Start service:      sudo systemctl start ebon-maintenance"
echo "  Check agent:        python3 ~/ebon_maintenance_agent.py --status"
echo "  Kill noip2:         python3 ~/ebon_maintenance_agent.py --kill-noip2"
echo "  Emergency cleanup:  python3 ~/ebon_maintenance_agent.py --cleanup"
echo ""
echo "The agent will:"
echo "  • Kill runaway noip2 processes automatically"
echo "  • Clean disk space when root partition > 85% full"
echo "  • Monitor and restart Docker containers"
echo "  • Perform daily cleanups"
echo "  • Monitor system load and resources"