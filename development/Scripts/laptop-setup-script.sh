#!/bin/bash
# Ethereum Light Node Setup Script for Ubuntu Desktop
set -euo pipefail

# Set variables
USERNAME="dave"
GETH_DATA_DIR="/home/$USERNAME/.ethereum"
PRYSM_DATA_DIR="/home/$USERNAME/.prysm"
LOG_FILE="/tmp/ethereum_light_node_setup.log"

# Function to log messages
log_message() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

# Function to check command success
check_command() {
    if [ $? -ne 0 ]; then
        log_message "Error: $1"
        exit 1
    fi
}

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
   log_message "This script must be run as root" 
   exit 1
fi

# Main script starts here
log_message "Starting Ethereum light node setup script"

# Update and upgrade the system
log_message "Updating and upgrading the system..."
apt update && apt upgrade -y
check_command "System update failed"

# Install necessary packages
log_message "Installing necessary packages..."
apt install -y software-properties-common curl wget git

# Install Geth
log_message "Installing Geth..."
add-apt-repository -y ppa:ethereum/ethereum
apt update
apt install -y ethereum
check_command "Geth installation failed"

# Install Prysm
log_message "Installing Prysm..."
mkdir -p /usr/local/bin
curl https://raw.githubusercontent.com/prysmaticlabs/prysm/master/prysm.sh --output /usr/local/bin/prysm.sh
chmod +x /usr/local/bin/prysm.sh
check_command "Prysm installation failed"

# Create Geth systemd service
log_message "Creating Geth systemd service..."
cat > /etc/systemd/system/geth-light.service <<EOL
[Unit]
Description=Ethereum Go Client (Light Mode)
After=network.target

[Service]
User=$USERNAME
ExecStart=/usr/bin/geth --datadir $GETH_DATA_DIR --syncmode light --cache 1024
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOL

# Create Prysm beacon chain systemd service
log_message "Creating Prysm beacon chain systemd service..."
cat > /etc/systemd/system/prysm-beacon-chain-light.service <<EOL
[Unit]
Description=Prysm Ethereum 2.0 Beacon Chain (Light Mode)
Wants=network-online.target
After=network-online.target

[Service]
User=$USERNAME
ExecStart=/usr/local/bin/prysm.sh beacon-chain --datadir=$PRYSM_DATA_DIR --http-web3provider=http://localhost:8545 --minimal-config
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

# Set up Ethereum data directories
log_message "Setting up Ethereum data directories..."
mkdir -p $GETH_DATA_DIR $PRYSM_DATA_DIR
chown -R $USERNAME:$USERNAME $GETH_DATA_DIR $PRYSM_DATA_DIR

# Enable and start services
log_message "Enabling and starting services..."
systemctl enable geth-light prysm-beacon-chain-light
systemctl start geth-light prysm-beacon-chain-light

log_message "Ethereum light node setup completed successfully."
echo "============================================================"
echo "Ethereum Light Node Setup Complete"
echo "============================================================"
echo "Your Ethereum light node has been set up successfully."
echo "Geth and Prysm are running in light client mode."
echo "You can check the status of the services using:"
echo "systemctl status geth-light"
echo "systemctl status prysm-beacon-chain-light"
echo "============================================================"
echo "Next steps:"
echo "1. Monitor your node's sync status"
echo "2. Consider setting up a lightweight monitoring solution"
echo "3. Regularly check for updates to Geth and Prysm"
echo "============================================================"
