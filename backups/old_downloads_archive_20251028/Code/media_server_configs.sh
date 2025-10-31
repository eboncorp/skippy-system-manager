# Media Server Configuration Files & Setup Scripts
# Complete package for Docker media server automation

# ===== .env file =====
cat > .env << 'EOF'
# Media Server Environment Configuration
# Version: 2.0

# === GENERAL SETTINGS ===
TIMEZONE=America/New_York
DOMAIN=yourdomain.com
SERVER_IP=192.168.1.100

# === USER SETTINGS ===
PUID=1000
PGID=1000

# === PATHS ===
MEDIA_PATH=/tank/media
DOWNLOADS_PATH=/tank/downloads
PERSONAL_PATH=/tank/personal
BACKUP_SOURCE_PATH=/tank
BACKUP_DEST_PATH=/tank/backups

# === PLEX SETTINGS ===
PLEX_CLAIM_TOKEN=claim-xxxxxxxxxxxxxxxxxx

# === CLOUDFLARE SETTINGS (for SSL) ===
CLOUDFLARE_EMAIL=your-email@domain.com
CLOUDFLARE_API_KEY=your-cloudflare-api-key
ACME_EMAIL=your-email@domain.com

# === DATABASE SETTINGS ===
POSTGRES_PASSWORD=your-secure-password-here

# === NEXTCLOUD SETTINGS ===
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=your-secure-password-here

# === MONITORING SETTINGS ===
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-password-here

# === NOTIFICATION SETTINGS ===
SLACK_WEBHOOK=https://hooks.slack.com/services/your/webhook/url
EOF

# ===== setup.sh - Initial Setup Script =====
cat > setup.sh << 'EOF'
#!/bin/bash

# Media Server Setup Script
# Version: 2.0

set -euo pipefail

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check available disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 100 ]; then
        log_warn "Less than 100GB available. Recommended: 500GB+"
    fi
    
    log "Requirements check passed"
}

create_directories() {
    log "Creating directory structure..."
    
    # Media directories
    mkdir -p /tank/media/{movies,tv,music}
    mkdir -p /tank/downloads/{complete,incomplete,watch}
    mkdir -p /tank/personal
    mkdir -p /tank/backups
    
    # Config directories
    mkdir -p ./config/{plex,sonarr,radarr,prowlarr,bazarr,lidarr}
    mkdir -p ./config/{qbittorrent,jellyfin,duplicati,prometheus,grafana}
    mkdir -p ./config/{homeassistant,mosquitto,nextcloud,traefik}
    mkdir -p ./data/{prometheus,grafana,portainer,mosquitto}
    mkdir -p ./logs/mosquitto
    mkdir -p ./cache/jellyfin
    mkdir -p ./traefik/{dynamic,certs}
    
    # Set permissions
    sudo chown -R $USER:$USER /tank
    sudo chown -R $USER:$USER ./config ./data ./logs ./cache ./traefik
    
    log "Directory structure created"
}

setup_traefik() {
    log "Setting up Traefik configuration..."
    
    cat > ./traefik/traefik.yml << 'TRAEFIK_EOF'
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  cloudflare:
    acme:
      email: ${ACME_EMAIL}
      storage: /etc/certs/acme.json
      dnsChallenge:
        provider: cloudflare
TRAEFIK_EOF

    # Create dynamic config
    cat > ./traefik/dynamic/middlewares.yml << 'MIDDLEWARE_EOF'
http:
  middlewares:
    secure-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
        customFrameOptionsValue: "SAMEORIGIN"
        customResponseHeaders:
          X-Robots-Tag: "none,noarchive,nosnippet,notranslate,noimageindex"
          server: ""
    
    auth:
      basicAuth:
        users:
          - "admin:$2y$10$..."  # Generate with htpasswd
MIDDLEWARE_EOF

    # Set permissions for certificates
    touch ./traefik/certs/acme.json
    chmod 600 ./traefik/certs/acme.json
    
    log "Traefik configuration complete"
}

setup_prometheus() {
    log "Setting up Prometheus configuration..."
    
    cat > ./config/prometheus/prometheus.yml << 'PROMETHEUS_EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'plex'
    static_configs:
      - targets: ['plex:32400']
    scrape_interval: 30s
    metrics_path: '/metrics'
PROMETHEUS_EOF

    log "Prometheus configuration complete"
}

setup_media_structure() {
    log "Setting up media organization structure..."
    
    # Create media organization script
    cat > organize_media.py << 'ORGANIZE_EOF'
#!/usr/bin/env python3
"""
Media Organization Script
Automatically organizes downloaded media files
"""

import os
import shutil
import re
from pathlib import Path
import argparse

def organize_movies(source_dir, dest_dir):
    """Organize movie files"""
    movie_pattern = r"(.+?)\s*\((\d{4})\).*\.(mkv|mp4|avi)$"
    
    for file_path in Path(source_dir).glob("*"):
        if file_path.is_file():
            match = re.match(movie_pattern, file_path.name, re.IGNORECASE)
            if match:
                title, year, ext = match.groups()
                title = re.sub(r'[^\w\s-]', '', title).strip()
                
                # Create movie directory
                movie_dir = Path(dest_dir) / f"{title} ({year})"
                movie_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = movie_dir / f"{title} ({year}).{ext}"
                shutil.move(str(file_path), str(new_path))
                print(f"Moved: {file_path.name} -> {new_path}")

def organize_tv_shows(source_dir, dest_dir):
    """Organize TV show files"""
    tv_pattern = r"(.+?)[\.\s][Ss](\d{2})[Ee](\d{2}).*\.(mkv|mp4|avi)$"
    
    for file_path in Path(source_dir).glob("*"):
        if file_path.is_file():
            match = re.match(tv_pattern, file_path.name, re.IGNORECASE)
            if match:
                show, season, episode, ext = match.groups()
                show = re.sub(r'[^\w\s-]', '', show).strip()
                
                # Create show/season directory
                show_dir = Path(dest_dir) / show / f"Season {int(season):02d}"
                show_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                new_name = f"{show} - S{season}E{episode}.{ext}"
                new_path = show_dir / new_name
                shutil.move(str(file_path), str(new_path))
                print(f"Moved: {file_path.name} -> {new_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize media files")
    parser.add_argument("--source", required=True, help="Source directory")
    parser.add_argument("--movies", help="Movies destination directory")
    parser.add_argument("--tv", help="TV shows destination directory")
    
    args = parser.parse_args()
    
    if args.movies:
        organize_movies(args.source, args.movies)
    
    if args.tv:
        organize_tv_shows(args.source, args.tv)
ORGANIZE_EOF

    chmod +x organize_media.py
    log "Media organization script created"
}

setup_backup_script() {
    log "Setting up backup automation..."
    
    cat > backup_media.sh << 'BACKUP_EOF'
#!/bin/bash

# Media Backup Script
# Automated backup with Duplicati integration

set -euo pipefail

BACKUP_SOURCE="/tank"
BACKUP_DEST="/tank/backups"
LOG_FILE="/var/log/media_backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create incremental backup
create_backup() {
    log "Starting backup process..."
    
    # Create timestamped backup directory
    BACKUP_DIR="$BACKUP_DEST/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration files
    log "Backing up configurations..."
    tar -czf "$BACKUP_DIR/configs.tar.gz" ./config/ ./data/
    
    # Backup important media metadata
    log "Backing up media metadata..."
    find /tank/media -name "*.nfo" -o -name "*.jpg" -o -name "*.png" | \
        tar -czf "$BACKUP_DIR/metadata.tar.gz" -T -
    
    # Sync to cloud storage (if configured)
    if command -v rclone &> /dev/null; then
        log "Syncing to cloud storage..."
        rclone sync "$BACKUP_DIR" "remote:backups/$(basename "$BACKUP_DIR")"
    fi
    
    log "Backup completed successfully"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    find "$BACKUP_DEST" -name "backup_*" -type d -mtime +30 -exec rm -rf {} \;
    log "Old backup cleanup completed"
}

create_backup
cleanup_old_backups
BACKUP_EOF

    chmod +x backup_media.sh
    log "Backup script created"
}

setup_monitoring_dashboard() {
    log "Setting up Grafana dashboard..."
    
    mkdir -p ./config/grafana/provisioning/{dashboards,datasources}
    
    # Datasource configuration
    cat > ./config/grafana/provisioning/datasources/prometheus.yml << 'DATASOURCE_EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
DATASOURCE_EOF

    # Dashboard provisioning
    cat > ./config/grafana/provisioning/dashboards/dashboard.yml << 'DASHBOARD_EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
DASHBOARD_EOF

    log "Monitoring dashboard configuration complete"
}

main() {
    log "Starting Media Server setup..."
    
    check_requirements
    create_directories
    setup_traefik
    setup_prometheus
    setup_media_structure
    setup_backup_script
    setup_monitoring_dashboard
    
    log "Setup complete! Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Get Plex claim token: https://plex.tv/claim"
    echo "3. Configure Cloudflare API for SSL certificates"
    echo "4. Run: docker-compose up -d"
    echo "5. Configure your applications through their web interfaces"
}

main "$@"
EOF

chmod +x setup.sh

# ===== docker-management.sh - Container Management =====
cat > docker-management.sh << 'EOF'
#!/bin/bash

# Docker Media Server Management Script

set -euo pipefail

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

show_status() {
    log "Media Server Status:"
    docker-compose ps
}

start_services() {
    log "Starting all services..."
    docker-compose up -d
    log "Services started"
}

stop_services() {
    log "Stopping all services..."
    docker-compose down
    log "Services stopped"
}

restart_services() {
    log "Restarting all services..."
    docker-compose restart
    log "Services restarted"
}

update_services() {
    log "Updating all services..."
    docker-compose pull
    docker-compose up -d
    docker system prune -f
    log "Services updated"
}

backup_configs() {
    log "Backing up configurations..."
    tar -czf "backup_configs_$(date +%Y%m%d_%H%M%S).tar.gz" ./config ./data
    log "Configuration backup created"
}

show_logs() {
    local service=${1:-}
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

show_usage() {
    echo "Usage: $0 {start|stop|restart|status|update|backup|logs [service]}"
    echo "  start   - Start all services"
    echo "  stop    - Stop all services"
    echo "  restart - Restart all services"
    echo "  status  - Show service status"
    echo "  update  - Update and restart all services"
    echo "  backup  - Backup configuration files"
    echo "  logs    - Show logs (optionally for specific service)"
}

case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    update)
        update_services
        ;;
    backup)
        backup_configs
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
EOF

chmod +x docker-management.sh

echo "=== Media Server Configuration Package Created ==="
echo "Files created:"
echo "  - .env (environment configuration)"
echo "  - setup.sh (initial setup script)"
echo "  - docker-management.sh (container management)"
echo "  - organize_media.py (media organization)"
echo "  - backup_media.sh (backup automation)"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Run: ./setup.sh"
echo "3. Run: docker-compose up -d"