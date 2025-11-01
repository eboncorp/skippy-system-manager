#!/bin/bash

# Setup No-IP configuration
cat > /usr/local/etc/no-ip2.conf << EOF
UPDATE_INTERVAL=5
HOST=eboneth.ddns.net
USERNAME=eboncorp
PASSWORD=REDACTED_SERVER_PASSWORD
INTERFACE=eno1
EOF

# Create systemd service for No-IP
sudo tee /etc/systemd/system/noip2.service > /dev/null << 'EOF'
[Unit]
Description=No-IP Dynamic DNS Update Client
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/noip2
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable noip2
sudo systemctl start noip2

echo "No-IP Dynamic DNS configured for eboneth.ddns.net"
echo "Checking status..."
sudo systemctl status noip2