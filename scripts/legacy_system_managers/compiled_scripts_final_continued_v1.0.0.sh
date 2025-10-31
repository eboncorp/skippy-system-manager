app = Flask(__name__)
    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

    @app.route('/api/status')
    def get_status():
        return jsonify({
            'geth': 'Running' if w3.isConnected() else 'Not Connected',
            'prysm': 'Running',  # You might want to implement a real check for Prysm
            'lastBlock': w3.eth.block_number,
            'peers': len(w3.geth.admin.peers())
        })

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
    "
    
    echo "$api_content" | run_remote "cat > /home/$USERNAME/node_api.py"
    
    # Set up systemd service for the API
    local service_content="
    [Unit]
    Description=Ethereum Node Status API
    After=network.target

    [Service]
    User=$USERNAME
    WorkingDirectory=/home/$USERNAME
    ExecStart=/usr/bin/python3 /home/$USERNAME/node_api.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    "
    
    echo "$service_content" | run_remote "sudo tee /etc/systemd/system/node-api.service > /dev/null"
    run_remote "sudo systemctl daemon-reload"
    run_remote "sudo systemctl enable node-api"
    run_remote "sudo systemctl start node-api"
    
    # Update Nginx configuration to serve dashboard and proxy API requests
    local nginx_config="
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name $DOMAIN;

        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

        root /var/www/html;
        index dashboard.html;

        location / {
            try_files $uri $uri/ =404;
        }

        location /api/ {
            proxy_pass http://localhost:5000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }
    }
    "
    
    echo "$nginx_config" | run_remote "sudo tee /etc/nginx/sites-available/ethereum > /dev/null"
    run_remote "sudo nginx -t && sudo systemctl reload nginx"
    
    log "Status dashboard setup completed"
}

setup_log_rotation() {
    log "Setting up log rotation..."
    
    local logrotate_config="
/var/log/ethereum_node_deployment.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
"
    
    echo "$logrotate_config" | run_remote "sudo tee /etc/logrotate.d/ethereum_node > /dev/null"
    
    log "Log rotation setup completed"
}

# 5. scripts/backup.sh

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils.sh"

BACKUP_FILENAME="ethereum_node_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

log "Starting backup process..."

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Stop Ethereum services
log "Stopping Ethereum services..."
docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" down

# Create backup
log "Creating backup..."
sudo tar -czf "${BACKUP_DIR}/${BACKUP_FILENAME}" -C / \
    "${GETH_DATA_DIR#/}" \
    "${PRYSM_DATA_DIR#/}" \
    "${SCRIPT_DIR%/*}"

# Start Ethereum services
log "Starting Ethereum services..."
docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" up -d

# Optional: Copy to remote location (uncomment and configure as needed)
# rsync -avz "${BACKUP_DIR}/${BACKUP_FILENAME}" user@remote:/path/to/backups/

log "Backup completed successfully: ${BACKUP_DIR}/${BACKUP_FILENAME}"

# 6. scripts/update.sh

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils.sh"

log "Starting update process..."

# Function to compare versions
version_gt() { test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"; }

# Update Geth
update_geth() {
    local latest_version=$(curl -s https://api.github.com/repos/ethereum/go-ethereum/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    if version_gt "${latest_version}" "${GETH_VERSION}"; then
        log "Updating Geth from ${GETH_VERSION} to ${latest_version}"
        sed -i "s/GETH_VERSION=.*/GETH_VERSION=${latest_version}/" "${SCRIPT_DIR}/../config.sh"
    else
        log "Geth is already up to date (${GETH_VERSION})"
    fi
}

# Update Prysm
update_prysm() {
    local latest_version=$(curl -s https://api.github.com/repos/prysmaticlabs/prysm/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    if version_gt "${latest_version}" "${PRYSM_VERSION}"; then
        log "Updating Prysm from ${PRYSM_VERSION} to ${latest_version}"
        sed -i "s/PRYSM_VERSION=.*/PRYSM_VERSION=${latest_version}/" "${SCRIPT_DIR}/../config.sh"
    else
        log "Prysm is already up to date (${PRYSM_VERSION})"
    fi
}

# Perform updates
update_geth
update_prysm

# Restart services with new versions
log "Restarting Ethereum services with updated versions..."
docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" down
docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" pull
docker-compose -f "${SCRIPT_DIR}/../docker-compose.yml" up -d

log "Update completed successfully"

# 7. scripts/check_ethereum_updates.sh

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils.sh"

check_geth_updates() {
    local latest_version=$(curl -s https://api.github.com/repos/ethereum/go-ethereum/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    if [ "$latest_version" != "$GETH_VERSION" ]; then
        log "New Geth version available: $latest_version (current: $GETH_VERSION)"
    else
        log "Geth is up to date"
    fi
}

check_prysm_updates() {
    local latest_version=$(curl -s https://api.github.com/repos/prysmaticlabs/prysm/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
    if [ "$latest_version" != "$PRYSM_VERSION" ]; then
        log "New Prysm version available: $latest_version (current: $PRYSM_VERSION)"
    else
        log "Prysm is up to date"
    fi
}

check_geth_updates
check_prysm_updates

# 8. tests/test_deployment.sh

#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../config.sh"
source "${SCRIPT_DIR}/../utils.sh"

test_system_requirements() {
    log "Testing system requirements..."
    check_requirements
}

test_docker_installation() {
    log "Testing Docker installation..."
    if ! check_remote_command "docker"; then
        log "ERROR: Docker is not installed"
        return 1
    fi
    if ! check_remote_command "docker-compose"; then
        log "ERROR: Docker Compose is not installed"
        return 1
    fi
}

test_ethereum_node() {
    log "Testing Ethereum node..."
    if ! run_remote "docker ps | grep -q geth"; then
        log "ERROR: Geth container is not running"
        return 1
    fi
    if ! run_remote "docker ps | grep -q beacon"; then
        log "ERROR: Prysm beacon chain is not running"
        return 1
    fi
}

test_nginx() {
    log "Testing Nginx configuration..."
    if ! run_remote "sudo nginx -t"; then
        log "ERROR: Nginx configuration test failed"
        return 1
    fi
}

run_tests() {
    test_system_requirements
    test_docker_installation
    test_ethereum_node
    test_nginx
    log "All tests passed successfully"
}

run_tests

