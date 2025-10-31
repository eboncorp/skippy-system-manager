#!/bin/bash
# Script to change hostname to "ebon"

echo "🔧 Changing hostname to 'ebon'"
echo "============================="

# Change the system hostname
echo "1. Changing system hostname..."
sudo hostnamectl set-hostname ebon

# Update /etc/hosts
echo "2. Updating /etc/hosts..."
sudo sed -i "s/eboneth/ebon/g" /etc/hosts

# Change the Home Server Master name
echo "3. Updating Home Server Master configuration..."
sed -i 's/server_name: ".*"/server_name: "ebon"/' ~/.home-server/config/server.yaml

# Show the changes
echo
echo "✅ Changes completed!"
echo
echo "Current hostname: $(hostname)"
echo "Home Server name: $(grep server_name ~/.home-server/config/server.yaml)"
echo
echo "4. Restarting Home Server Master..."
systemctl --user restart home-server.service

echo
echo "🎉 Done! Your server is now named 'ebon'"
echo
echo "Note: You may need to reconnect SSH for the hostname change to fully take effect."