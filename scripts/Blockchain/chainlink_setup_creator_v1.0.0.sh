#!/bin/bash

# Chainlink Node Setup Creator Script
# Version: 1.0.0

set -euo pipefail

# Create main directory
mkdir -p chainlink_node_setup
cd chainlink_node_setup

# Create modules directory
mkdir -p modules

# Create main setup script
cat > chainlink_node_setup.sh << 'EOL'
#!/bin/bash

# Chainlink Node Setup Script (Modular Version)
# Version: 1.0.0

set -euo pipefail

# Load configuration
source config.env

# Load modules
source modules/utils.sh
source modules/system_setup.sh
source modules/docker_setup.sh
source modules/chainlink_setup.sh
source modules/monitoring_setup.sh
source modules/backup_setup.sh
source modules/security_setup.sh

# Main setup function
setup_chainlink_node() {
    log_info "Starting Chainlink node setup..."

    check_prerequisites
    setup_system
    setup_docker
    setup_chainlink
    setup_monitoring
    setup_backups
    enhance_security

    log_info "Chainlink node setup completed successfully!"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if config.env exists
    if [[ ! -f "config.env" ]]; then
        log_error "config.env file not found. Please create it with the necessary configurations."
        exit 1
    fi

    # Check if all required variables are set
    local required_vars=(
        "DO_API_TOKEN" "ETH_NODE_URL" "CHAINLINK_VERSION" "POSTGRES_PASSWORD"
        "API_EMAIL" "API_PASSWORD" "WALLET_PASSWORD" "CHAINLINK_DATA_DIR"
    )
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "$var is not set in config.env"
            exit 1
        fi
    done
}

# Run the setup
setup_chainlink_node
EOL

chmod +x chainlink_node_setup.sh

# Create config.env template
cat > config.env << 'EOL'
# DigitalOcean API Token
DO_API_TOKEN="your_digitalocean_api_token"

# Ethereum Node URL
ETH_NODE_URL="http://your_eth_node_ip:8545"

# Chainlink Version
CHAINLINK_VERSION="1.11.0"

# PostgreSQL Password
POSTGRES_PASSWORD="your_secure_postgres_password"

# Chainlink Node API Credentials
API_EMAIL="your_chainlink_api_email"
API_PASSWORD="your_chainlink_api_password"

# Chainlink Node Wallet Password
WALLET_PASSWORD="your_chainlink_wallet_password"

# Chainlink Data Directory
CHAINLINK_DATA_DIR="/chainlink"
EOL

# Create module files
cd modules

# utils.sh
cat > utils.sh << 'EOL'
#!/bin/bash

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}
EOL

# system_setup.sh
cat > system_setup.sh << 'EOL'
#!/bin/bash

setup_system() {
    log_info "Setting up system..."
    apt-get update && apt-get upgrade -y
    apt-get install -y curl jq
}
EOL

# docker_setup.sh
cat > docker_setup.sh << 'EOL'
#!/bin/bash

setup_docker() {
    log_info "Setting up Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
}
EOL

# chainlink_setup.sh
cat > chainlink_setup.sh << 'EOL'
#!/bin/bash

setup_chainlink() {
    log_info "Setting up Chainlink node..."
    mkdir -p $CHAINLINK_DATA_DIR
    
    cat > ../docker-compose.yml <<EOF
version: '3'
services:
  chainlink:
    image: smartcontract/chainlink:${CHAINLINK_VERSION}
    restart: always
    volumes:
      - ${CHAINLINK_DATA_DIR}:/chainlink
    env_file:
      - chainlink-env
    command: node start --password /chainlink/.password --api /chainlink/.api
    ports:
      - "6688:6688"
  postgres:
    image: postgres:13
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
EOF

    cat > ../chainlink-env <<EOF
ROOT=/chainlink
LOG_LEVEL=debug
ETH_CHAIN_ID=1
CHAINLINK_TLS_PORT=0
SECURE_COOKIES=false
ALLOW_ORIGINS=*
ETH_URL=${ETH_NODE_URL}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/chainlink?sslmode=disable
EOF

    echo "${API_EMAIL}" > ${CHAINLINK_DATA_DIR}/.api
    echo "${API_PASSWORD}" >> ${CHAINLINK_DATA_DIR}/.api
    echo "${WALLET_PASSWORD}" > ${CHAINLINK_DATA_DIR}/.password

    docker-compose up -d
}
EOL

# monitoring_setup.sh
cat > monitoring_setup.sh << 'EOL'
#!/bin/bash

setup_monitoring() {
    log_info "Setting up monitoring..."
    # Add Prometheus and Grafana setup here
    # This is a placeholder and should be expanded based on your specific monitoring needs
}
EOL

# backup_setup.sh
cat > backup_setup.sh << 'EOL'
#!/bin/bash

setup_backups() {
    log_info "Setting up backups..."
    # Add backup script and cron job here
    # This is a placeholder and should be expanded based on your specific backup strategy
}
EOL

# security_setup.sh
cat > security_setup.sh << 'EOL'
#!/bin/bash

enhance_security() {
    log_info "Enhancing security..."
    # Set up firewall
    ufw allow 22/tcp
    ufw allow 6688/tcp
    ufw --force enable

    # Set up fail2ban
    apt-get install -y fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
}
EOL

cd ..

echo "Chainlink node setup directory and files have been created successfully!"
echo "Please edit the config.env file with your specific configuration before running the setup script."
