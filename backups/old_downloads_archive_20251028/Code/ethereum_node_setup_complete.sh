#!/bin/bash

# Ethereum Node Setup Script
# Version: 2.4.0
# Description: Automated deployment script for Ethereum full node with Geth + Lighthouse
# Author: Compiled from conversations
# Date: 2024-2025

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/node_config.env"
LOG_FILE="${SCRIPT_DIR}/ethereum_setup.log"
REMOTE_SCRIPT="/tmp/ethereum_remote_setup.sh"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Check if configuration file exists
check_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file $CONFIG_FILE not found!"
        echo "Creating sample configuration file..."
        create_sample_config
        log "Please edit $CONFIG_FILE with your server details and run again."
        exit 1
    fi
}

# Create sample configuration file
create_sample_config() {
    cat > "$CONFIG_FILE" << 'EOF'
# Ethereum Node Configuration
# Version: 2.4.0

# Server connection details
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="YOUR_USERNAME"
SSH_KEY_PATH="~/.ssh/id_rsa"

# Ethereum configuration
ETHEREUM_USER="ethereum"
ETHEREUM_HOME="/home/ethereum"
DATA_DIR="/home/ethereum/ethereum-data"

# Network configuration (mainnet/goerli/sepolia)
NETWORK="mainnet"

# Geth configuration
GETH_VERSION="latest"
GETH_HTTP_PORT="8545"
GETH_WS_PORT="8546"
GETH_P2P_PORT="30303"

# Lighthouse configuration
LIGHTHOUSE_VERSION="latest"
LIGHTHOUSE_HTTP_PORT="5052"
LIGHTHOUSE_P2P_PORT="9000"

# System configuration
SWAP_SIZE="4G"
MAX_PEERS="50"
CACHE_SIZE="2048"

# Security settings
ENABLE_FIREWALL="true"
ALLOWED_IPS="YOUR_IP_ADDRESS"
EOF
}

# Load configuration
load_config() {
    log "Loading configuration from $CONFIG_FILE"
    source "$CONFIG_FILE"
    
    # Validate required variables
    local required_vars=("SERVER_IP" "SERVER_USER" "SSH_KEY_PATH")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required variable $var is not set in $CONFIG_FILE"
            exit 1
        fi
    done
}

# Enhanced sudo command execution with retries
run_sudo_command() {
    local command="$1"
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        if sudo -n true 2>/dev/null; then
            eval "$command"
            return 0
        else
            ((retry_count++))
            if [[ $retry_count -lt $max_retries ]]; then
                echo "Sudo authentication required (attempt $retry_count/$max_retries)"
                sudo -v
            else
                log_error "Failed to authenticate sudo after $max_retries attempts"
                return 1
            fi
        fi
    done
}

# Create remote setup script
create_remote_script() {
    log "Creating remote setup script"
    
    cat > "${REMOTE_SCRIPT}" << 'REMOTE_SCRIPT_EOF'
#!/bin/bash

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Update system
log "Updating system packages"
sudo apt update && sudo apt upgrade -y

# Install dependencies
log "Installing dependencies"
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    htop \
    tmux \
    jq

# Create ethereum user
log "Creating ethereum user"
if ! id "$ETHEREUM_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash "$ETHEREUM_USER"
    sudo usermod -aG sudo "$ETHEREUM_USER"
    log "Created user: $ETHEREUM_USER"
else
    log "User $ETHEREUM_USER already exists"
fi

# Create data directory
log "Creating data directory: $DATA_DIR"
sudo mkdir -p "$DATA_DIR"
sudo chown -R "$ETHEREUM_USER:$ETHEREUM_USER" "$DATA_DIR"
sudo chmod 755 "$DATA_DIR"

# Install Geth
log "Installing Geth (Go Ethereum)"
cd /tmp
wget -q https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.13.8-7516b617.tar.gz
tar -xzf geth-linux-amd64-*.tar.gz
sudo cp geth-linux-amd64-*/geth /usr/local/bin/
sudo chmod +x /usr/local/bin/geth
rm -rf geth-linux-amd64-*

# Install Lighthouse
log "Installing Lighthouse (Consensus Client)"
cd /tmp
LIGHTHOUSE_VERSION=$(curl -s https://api.github.com/repos/sigp/lighthouse/releases/latest | jq -r '.tag_name')
wget -q "https://github.com/sigp/lighthouse/releases/download/${LIGHTHOUSE_VERSION}/lighthouse-${LIGHTHOUSE_VERSION}-x86_64-unknown-linux-gnu.tar.gz"
tar -xzf lighthouse-*.tar.gz
sudo cp lighthouse /usr/local/bin/
sudo chmod +x /usr/local/bin/lighthouse
rm -rf lighthouse-*

# Create Geth service
log "Creating Geth systemd service"
sudo tee /etc/systemd/system/geth.service > /dev/null << EOF
[Unit]
Description=Ethereum Geth Client
After=network.target
Wants=network.target

[Service]
User=$ETHEREUM_USER
Group=$ETHEREUM_USER
Type=simple
Restart=always
RestartSec=5
TimeoutStopSec=600
ExecStart=/usr/local/bin/geth \\
    --datadir $DATA_DIR/geth \\
    --http \\
    --http.addr 0.0.0.0 \\
    --http.port $GETH_HTTP_PORT \\
    --http.api eth,net,web3,personal \\
    --ws \\
    --ws.addr 0.0.0.0 \\
    --ws.port $GETH_WS_PORT \\
    --ws.api eth,net,web3 \\
    --port $GETH_P2P_PORT \\
    --maxpeers $MAX_PEERS \\
    --cache $CACHE_SIZE \\
    --authrpc.addr localhost \\
    --authrpc.port 8551 \\
    --authrpc.vhosts localhost \\
    --authrpc.jwtsecret $DATA_DIR/jwt.hex

[Install]
WantedBy=multi-user.target
EOF

# Generate JWT secret for Geth-Lighthouse communication
log "Generating JWT secret"
sudo -u "$ETHEREUM_USER" openssl rand -hex 32 > "$DATA_DIR/jwt.hex"
sudo chown "$ETHEREUM_USER:$ETHEREUM_USER" "$DATA_DIR/jwt.hex"
sudo chmod 600 "$DATA_DIR/jwt.hex"

# Create Lighthouse beacon service
log "Creating Lighthouse Beacon systemd service"
sudo tee /etc/systemd/system/lighthouse-beacon.service > /dev/null << EOF
[Unit]
Description=Lighthouse Ethereum Beacon Node
Wants=network-online.target
After=network-online.target
Documentation=https://lighthouse-book.sigmaprime.io/

[Service]
Type=simple
User=$ETHEREUM_USER
Group=$ETHEREUM_USER
Restart=always
RestartSec=5
TimeoutStopSec=600
ExecStart=/usr/local/bin/lighthouse bn \\
    --network $NETWORK \\
    --datadir $DATA_DIR/lighthouse \\
    --http \\
    --http-address 0.0.0.0 \\
    --http-port $LIGHTHOUSE_HTTP_PORT \\
    --execution-endpoint http://localhost:8551 \\
    --execution-jwt $DATA_DIR/jwt.hex \\
    --checkpoint-sync-url https://mainnet.checkpoint.sigp.io

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
if [[ "$ENABLE_FIREWALL" == "true" ]]; then
    log "Configuring firewall"
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow 22/tcp
    
    # Allow Ethereum P2P ports
    sudo ufw allow $GETH_P2P_PORT/tcp
    sudo ufw allow $GETH_P2P_PORT/udp
    sudo ufw allow $LIGHTHOUSE_P2P_PORT/tcp
    sudo ufw allow $LIGHTHOUSE_P2P_PORT/udp
    
    # Allow RPC access from specific IPs if configured
    if [[ -n "$ALLOWED_IPS" && "$ALLOWED_IPS" != "YOUR_IP_ADDRESS" ]]; then
        sudo ufw allow from "$ALLOWED_IPS" to any port $GETH_HTTP_PORT
        sudo ufw allow from "$ALLOWED_IPS" to any port $GETH_WS_PORT
        sudo ufw allow from "$ALLOWED_IPS" to any port $LIGHTHOUSE_HTTP_PORT
    fi
    
    # Enable UFW
    sudo ufw --force enable
    
    # Show status
    sudo ufw status verbose
fi

# Configure swap if needed
log "Configuring swap space"
if [[ ! -f /swapfile ]]; then
    sudo fallocate -l "$SWAP_SIZE" /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    log "Swap file created: $SWAP_SIZE"
else
    log "Swap file already exists"
fi

# Reload systemd and start services
log "Starting Ethereum services"
sudo systemctl daemon-reload

# Start Geth first
sudo systemctl enable geth
sudo systemctl start geth

# Wait for Geth to start
log "Waiting for Geth to initialize..."
sleep 30

# Start Lighthouse
sudo systemctl enable lighthouse-beacon
sudo systemctl start lighthouse-beacon

# Show service status
log "Service Status:"
sudo systemctl status geth --no-pager -l
sudo systemctl status lighthouse-beacon --no-pager -l

log "Ethereum node setup completed successfully!"
log "Monitor services with: sudo journalctl -f -u geth -u lighthouse-beacon"
log "Geth HTTP RPC: http://localhost:$GETH_HTTP_PORT"
log "Lighthouse API: http://localhost:$LIGHTHOUSE_HTTP_PORT"

REMOTE_SCRIPT_EOF

    # Replace variables in the remote script
    sed -i "s/\$ETHEREUM_USER/$ETHEREUM_USER/g" "$REMOTE_SCRIPT"
    sed -i "s/\$DATA_DIR/$DATA_DIR/g" "$REMOTE_SCRIPT"
    sed -i "s/\$NETWORK/$NETWORK/g" "$REMOTE_SCRIPT"
    sed -i "s/\$GETH_HTTP_PORT/$GETH_HTTP_PORT/g" "$REMOTE_SCRIPT"
    sed -i "s/\$GETH_WS_PORT/$GETH_WS_PORT/g" "$REMOTE_SCRIPT"
    sed -i "s/\$GETH_P2P_PORT/$GETH_P2P_PORT/g" "$REMOTE_SCRIPT"
    sed -i "s/\$LIGHTHOUSE_HTTP_PORT/$LIGHTHOUSE_HTTP_PORT/g" "$REMOTE_SCRIPT"
    sed -i "s/\$LIGHTHOUSE_P2P_PORT/$LIGHTHOUSE_P2P_PORT/g" "$REMOTE_SCRIPT"
    sed -i "s/\$MAX_PEERS/$MAX_PEERS/g" "$REMOTE_SCRIPT"
    sed -i "s/\$CACHE_SIZE/$CACHE_SIZE/g" "$REMOTE_SCRIPT"
    sed -i "s/\$SWAP_SIZE/$SWAP_SIZE/g" "$REMOTE_SCRIPT"
    sed -i "s/\$ENABLE_FIREWALL/$ENABLE_FIREWALL/g" "$REMOTE_SCRIPT"
    sed -i "s/\$ALLOWED_IPS/$ALLOWED_IPS/g" "$REMOTE_SCRIPT"
}

# Deploy and execute remote script
deploy_and_execute() {
    log "Deploying setup script to remote server"
    
    # Copy script to remote server
    scp -i "$SSH_KEY_PATH" "$REMOTE_SCRIPT" "$SERVER_USER@$SERVER_IP:/tmp/"
    
    # Make script executable and run it
    ssh -t -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_IP" "chmod +x /tmp/ethereum_remote_setup.sh && /tmp/ethereum_remote_setup.sh"
    
    # Clean up
    ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_IP" "rm -f /tmp/ethereum_remote_setup.sh"
    rm -f "$REMOTE_SCRIPT"
}

# Test connection to remote server
test_connection() {
    log "Testing connection to $SERVER_USER@$SERVER_IP"
    
    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'"; then
        log "Connection test passed"
    else
        log_error "Failed to connect to remote server"
        exit 1
    fi
}

# Main execution
main() {
    log "Starting Ethereum Node Setup v2.4.0"
    
    check_config
    load_config
    test_connection
    create_remote_script
    deploy_and_execute
    
    log "Ethereum node deployment completed!"
    log "You can monitor the services by SSHing to your server and running:"
    log "  sudo journalctl -f -u geth -u lighthouse-beacon"
    log "Access Geth RPC at: http://$SERVER_IP:$GETH_HTTP_PORT"
    log "Access Lighthouse API at: http://$SERVER_IP:$LIGHTHOUSE_HTTP_PORT"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi