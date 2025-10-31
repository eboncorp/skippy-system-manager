# 1. deploy_ethereum_node.sh

#!/bin/bash
set -euo pipefail

VERSION="1.1.0"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source configuration and utilities
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/utils.sh"
source "${SCRIPT_DIR}/functions/deployment_functions.sh"

# Print version
print_version() {
    echo "Ethereum Node Deployment Script v${VERSION}"
}

# Main deployment function
deploy_ethereum_node() {
    log "Starting Ethereum node deployment v${VERSION}"
    
    validate_config
    check_requirements
    create_backup
    setup_system
    setup_docker
    setup_ethereum_node
    setup_monitoring
    setup_web_server
    setup_automated_backup
    install_grafana
    setup_status_dashboard
    setup_log_rotation
    
    log "Deployment completed successfully"
}

# Dry run function
dry_run() {
    log "Performing dry run..."
    # Add dry run logic here
    log "Dry run completed"
}

# Update function
update_node() {
    log "Updating Ethereum node..."
    "${SCRIPT_DIR}/scripts/update.sh"
    log "Update completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --update)
            UPDATE=true
            shift
            ;;
        --version|-v)
            print_version
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
if [[ ${DRY_RUN:-false} == true ]]; then
    dry_run
elif [[ ${UPDATE:-false} == true ]]; then
    update_node
else
    if ! deploy_ethereum_node; then
        log "ERROR: Deployment failed. Check the log for details."
        cleanup
        exit 1
    fi
fi

log "Script execution completed"

# 2. config.sh

#!/bin/bash

# Server configuration
SERVER_IP="10.0.0.21"
USERNAME="ebon"
SSH_PORT=22
EMAIL="eboncorp@gmail.com"
DOMAIN="eboneth.xyz"
SSH_KEY="$HOME/.ssh/id_rsa"

# Directories
GETH_DATA_DIR="/var/lib/goethereum"
PRYSM_DATA_DIR="/var/lib/prysm"
BACKUP_DIR="/var/backups/ethereum_node"

# Software versions
DOCKER_COMPOSE_VERSION="1.29.2"
GETH_VERSION="1.13.5"
PRYSM_VERSION="v4.1.1"

# Resource requirements
MIN_DISK_SPACE=2000 # GB
MIN_MEMORY=16 # GB
MIN_CPU_CORES=4

# Firewall ports
FIREWALL_PORTS=(
    "22/tcp"
    "80/tcp"
    "443/tcp"
    "30303/tcp"
    "30303/udp"
    "13000/tcp"
    "12000/udp"
)

# 3. utils.sh

#!/bin/bash

LOG_FILE="/var/log/ethereum_node_deployment.log"

log() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

run_remote() {
    ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$USERNAME@$SERVER_IP" "$1" || {
        log "ERROR: Failed to execute command on remote server: $1"
        return 1
    }
}

copy_to_remote() {
    scp -i "$SSH_KEY" -P "$SSH_PORT" -o StrictHostKeyChecking=no -o PasswordAuthentication=no "$1" "$USERNAME@$SERVER_IP:$2" || {
        log "ERROR: Failed to copy file to remote server: $1 -> $2"
        return 1
    }
}

check_remote_command() {
    run_remote "command -v $1 &> /dev/null" && return 0 || return 1
}

cleanup() {
    log "Performing cleanup..."
    # Add cleanup tasks here
}

check_requirements() {
    log "Checking system requirements..."
    local disk_space=$(run_remote "df -BG / | awk 'NR==2 {print \$4}' | sed 's/G//'")
    local memory=$(run_remote "free -g | awk '/^Mem:/{print \$2}'")
    local cpu_cores=$(run_remote "nproc")

    [[ $disk_space -lt $MIN_DISK_SPACE ]] && { log "ERROR: Insufficient disk space. Required: ${MIN_DISK_SPACE}GB, Available: ${disk_space}GB"; return 1; }
    [[ $memory -lt $MIN_MEMORY ]] && { log "ERROR: Insufficient memory. Required: ${MIN_MEMORY}GB, Available: ${memory}GB"; return 1; }
    [[ $cpu_cores -lt $MIN_CPU_CORES ]] && { log "ERROR: Insufficient CPU cores. Required: ${MIN_CPU_CORES}, Available: ${cpu_cores}"; return 1; }
}

create_backup() {
    log "Creating backup..."
    run_remote "sudo mkdir -p $BACKUP_DIR && sudo tar -czf $BACKUP_DIR/ethereum_node_backup_$(date +%Y%m%d_%H%M%S).tar.gz $GETH_DATA_DIR $PRYSM_DATA_DIR /etc/nginx/sites-available/ethereum"
}

# 4. functions/deployment_functions.sh

#!/bin/bash

# Source the config and utils files
source "$(dirname "$0")/../config.sh"
source "$(dirname "$0")/../utils.sh"

setup_system() {
    log "Setting up system..."
    update_system
    install_dependencies
    configure_firewall
    setup_ssh_hardening
}

update_system() {
    log "Updating system..."
    run_remote "sudo apt update && sudo apt upgrade -y"
}

install_dependencies() {
    log "Installing dependencies..."
    run_remote "sudo apt install -y software-properties-common curl wget git ufw unattended-upgrades apt-listchanges fail2ban"
}

configure_firewall() {
    log "Configuring firewall..."
    for port in "${FIREWALL_PORTS[@]}"; do
        run_remote "sudo ufw allow $port"
    done
    run_remote "sudo ufw --force enable"
}

setup_ssh_hardening() {
    log "Hardening SSH configuration..."
    run_remote "sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config"
    run_remote "sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config"
    run_remote "sudo systemctl restart sshd"
}

setup_docker() {
    log "Setting up Docker..."
    install_docker
    install_docker_compose
}

install_docker() {
    if ! check_remote_command "docker"; then
        log "Installing Docker..."
        run_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
        run_remote "sudo usermod -aG docker $USERNAME"
    else
        log "Docker is already installed."
    fi
}

install_docker_compose() {
    if ! check_remote_command "docker-compose"; then
        log "Installing Docker Compose..."
        run_remote "sudo curl -L \"https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
        run_remote "sudo chmod +x /usr/local/bin/docker-compose"
    else
        log "Docker Compose is already installed."
    fi
}

setup_ethereum_node() {
    log "Setting up Ethereum node..."
    create_data_directories
    copy_docker_compose_file
    start_ethereum_services
}

create_data_directories() {
    run_remote "sudo mkdir -p $GETH_DATA_DIR $PRYSM_DATA_DIR"
    run_remote "sudo chown -R $USERNAME:$USERNAME $GETH_DATA_DIR $PRYSM_DATA_DIR"
}

copy_docker_compose_file() {
    copy_to_remote "docker-compose.yml" "~/docker-compose.yml"
}

start_ethereum_services() {
    run_remote "docker-compose up -d"
}

setup_monitoring() {
    log "Setting up monitoring..."
    install_prometheus
    install_node_exporter
    configure_prometheus
}

install_prometheus() {
    run_remote "sudo apt install -y prometheus"
}

install_node_exporter() {
    run_remote "sudo apt install -y prometheus-node-exporter"
}

configure_prometheus() {
    # Add Prometheus configuration here
    log "Prometheus configuration not implemented yet."
}

setup_web_server() {
    log "Setting up web server..."
    install_nginx
    setup_ssl
    configure_nginx
}

install_nginx() {
    run_remote "sudo apt install -y nginx"
}

setup_ssl() {
    log "Setting up SSL..."
    run_remote "sudo apt install -y certbot python3-certbot-nginx"
    run_remote "sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m $EMAIL"
}

configure_nginx() {
    # Nginx configuration (similar to the original script)
    local config_content="server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }

    server {
        listen 443 ssl;
        server_name $DOMAIN;

        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        location / {
            proxy_pass http://localhost:8545;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_cache_bypass \$http_upgrade;
        }

        location /beacon/ {
            proxy_pass http://localhost:3500/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_cache_bypass \$http_upgrade;
        }
    }"

    run_remote "echo '$config_content' | sudo tee /etc/nginx/sites-available/ethereum"
    run_remote "sudo ln -sf /etc/nginx/sites-available/ethereum /etc/nginx/sites-enabled/"
    run_remote "sudo nginx -t && sudo systemctl restart nginx"
}

setup_automated_backup() {
    log "Setting up automated backup..."
    run_remote "echo '0 2 * * * ${HOME}/scripts/backup.sh' | crontab -"
}

install_grafana() {
    log "Installing Grafana..."
    run_remote "sudo apt-get install -y software-properties-common"
    run_remote "sudo add-apt-repository 'deb https://packages.grafana.com/oss/deb stable main'"
    run_remote "wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -"
    run_remote "sudo apt-get update"
    run_remote "sudo apt-get install -y grafana"
    run_remote "sudo systemctl enable grafana-server"
    run_remote "sudo systemctl start grafana-server"
}

validate_config() {
    log "Validating configuration..."
    local error=0

    # Check if required variables are set
    for var in SERVER_IP USERNAME SSH_PORT EMAIL DOMAIN SSH_KEY GETH_DATA_DIR PRYSM_DATA_DIR BACKUP_DIR; do
        if [ -z "${!var}" ]; then
            log "ERROR: $var is not set in config.sh"
            error=1
        fi
    done

    # Validate IP address format
    if ! [[ $SERVER_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log "ERROR: Invalid SERVER_IP format"
        error=1
    fi

    # Validate SSH port
    if ! [[ $SSH_PORT =~ ^[0-9]+$ ]] || [ $SSH_PORT -lt 1 ] || [ $SSH_PORT -gt 65535 ]; then
        log "ERROR: Invalid SSH_PORT"
        error=1
    fi

    # Validate email format
    if ! [[ $EMAIL =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log "ERROR: Invalid EMAIL format"
        error=1
    fi

    # Check if SSH key file exists
    if [ ! -f "$SSH_KEY" ]; then
        log "ERROR: SSH key file not found: $SSH_KEY"
        error=1
    fi

    if [ $error -eq 0 ]; then
        log "Configuration validation passed"
    else
        log "Configuration validation failed"
        exit 1
    fi
}

setup_status_dashboard() {
    log "Setting up status dashboard..."
    
    # Create a simple HTML file
    local dashboard_content="
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Ethereum Node Status</title>
        <script src='https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js'></script>
    </head>
    <body>
        <h1>Ethereum Node Status</h1>
        <div id='status'></div>
        <script>
        function updateStatus() {
            axios.get('/api/status')
                .then(function (response) {
                    document.getElementById('status').innerHTML = \`
                        <p>Geth Status: \${response.data.geth}</p>
                        <p>Prysm Status: \${response.data.prysm}</p>
                        <p>Last Block: \${response.data.lastBlock}</p>
                        <p>Peers: \${response.data.peers}</p>
                    \`;
                })
                .catch(function (error) {
                    console.log(error);
                });
        }
        setInterval(updateStatus, 5000);
        updateStatus();
        </script>
    </body>
    </html>
    "
    
    # Copy dashboard to server
    echo "$dashboard_content" | run_remote "cat > /var/www/html/dashboard.html"
    
    # Set up a simple API endpoint using Python and Flask
    run_remote "sudo apt install -y python3-pip"
    run_remote "pip3 install flask web3"
    
    local api_content="
    from flask import Flask, jsonify
    from web3 import Web3

    app = Flask(__name__)
    w3 = Web3(Web3.HTTPProvider('http