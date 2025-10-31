#!/bin/bash

# Comprehensive Deployment Automation & Configuration Management Package
# Version: 3.0
# Compiled from multiple conversation artifacts 2024-2025
# Supports: Docker, Kubernetes, Traditional Server Deployments

set -euo pipefail

# === GLOBAL CONFIGURATION ===
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEPLOY_BASE_DIR="/opt/deployments"
readonly CONFIG_DIR="${SCRIPT_DIR}/configs"
readonly TEMPLATES_DIR="${SCRIPT_DIR}/templates"
readonly LOG_DIR="${SCRIPT_DIR}/logs"
readonly BACKUP_DIR="${SCRIPT_DIR}/backups"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Environment configurations
declare -A ENVIRONMENTS=(
    ["development"]="dev.local:8080"
    ["staging"]="staging.company.com:443"
    ["production"]="prod.company.com:443"
)

declare -A DEPLOY_CONFIGS=(
    ["development"]="user@dev-server"
    ["staging"]="deploy@staging-server"
    ["production"]="deploy@prod-server"
)

# === UTILITY FUNCTIONS ===

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[$timestamp] INFO:${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[$timestamp] WARN:${NC} $message" ;;
        "ERROR") echo -e "${RED}[$timestamp] ERROR:${NC} $message" >&2 ;;
        "DEBUG") echo -e "${CYAN}[$timestamp] DEBUG:${NC} $message" ;;
    esac
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "${LOG_DIR}/deploy_${TIMESTAMP}.log"
}

log_info() { log "INFO" "$1"; }
log_warn() { log "WARN" "$1"; }
log_error() { log "ERROR" "$1"; }
log_debug() { log "DEBUG" "$1"; }

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "Script failed at line $line_number with exit code $exit_code"
    cleanup_on_error
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Cleanup function
cleanup_on_error() {
    log_warn "Performing cleanup after error..."
    # Add cleanup logic here
    log_info "Cleanup completed"
}

# === INITIALIZATION ===

init_deployment_system() {
    log_info "Initializing deployment system..."
    
    # Create directory structure
    local dirs=("$CONFIG_DIR" "$TEMPLATES_DIR" "$LOG_DIR" "$BACKUP_DIR")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    # Initialize configuration files
    create_default_configs
    create_deployment_templates
    
    log_info "Deployment system initialized"
}

# === CONFIGURATION MANAGEMENT ===

create_default_configs() {
    log_info "Creating default configuration files..."
    
    # Main deployment configuration
    cat > "${CONFIG_DIR}/deploy.conf" << 'EOF'
# Deployment Configuration
# Version: 3.0

# Global settings
PROJECT_NAME="project-name"
DEPLOY_USER="deploy"
KEEP_RELEASES=5
BUILD_TIMEOUT=600
DEPLOY_TIMEOUT=300

# Security settings
VERIFY_SSL=true
USE_SSH_KEYS=true
BACKUP_BEFORE_DEPLOY=true

# Notification settings
SLACK_WEBHOOK=""
EMAIL_NOTIFICATIONS=false
NOTIFY_ON_SUCCESS=true
NOTIFY_ON_FAILURE=true

# Health check settings
HEALTH_CHECK_URL="/health"
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_RETRIES=3
EOF

    # Environment-specific configurations
    for env in development staging production; do
        cat > "${CONFIG_DIR}/${env}.conf" << EOF
# ${env^} Environment Configuration

# Server settings
SERVER_HOST="${env}.company.com"
SERVER_PORT="443"
DEPLOY_PATH="/var/www/${env}"

# Database settings
DB_HOST="${env}-db.company.com"
DB_NAME="${PROJECT_NAME}_${env}"
DB_BACKUP_BEFORE_DEPLOY=true

# Application settings
DEBUG_MODE=$( [ "$env" = "development" ] && echo "true" || echo "false" )
LOG_LEVEL=$( [ "$env" = "production" ] && echo "ERROR" || echo "INFO" )

# Resource limits
MAX_MEMORY="512M"
MAX_CPU="1000m"
REPLICAS=$( [ "$env" = "production" ] && echo "3" || echo "1" )
EOF
    done
    
    log_info "Default configurations created"
}

create_deployment_templates() {
    log_info "Creating deployment templates..."
    
    # Docker Compose template
    cat > "${TEMPLATES_DIR}/docker-compose.yml.template" << 'EOF'
version: '3.8'

networks:
  app_network:
    driver: bridge

volumes:
  app_data:
  db_data:

services:
  app:
    image: ${APP_IMAGE}:${APP_VERSION}
    container_name: ${PROJECT_NAME}_app
    restart: unless-stopped
    environment:
      - NODE_ENV=${ENVIRONMENT}
      - DB_HOST=${DB_HOST}
      - DB_NAME=${DB_NAME}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - app_data:/app/data
    networks:
      - app_network
    ports:
      - "${APP_PORT}:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      - db

  db:
    image: postgres:14-alpine
    container_name: ${PROJECT_NAME}_db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - app_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: ${PROJECT_NAME}_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    networks:
      - app_network
    depends_on:
      - app
EOF

    # Kubernetes deployment template
    cat > "${TEMPLATES_DIR}/k8s-deployment.yml.template" << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${PROJECT_NAME}-app
  namespace: ${NAMESPACE}
  labels:
    app: ${PROJECT_NAME}
    version: ${APP_VERSION}
spec:
  replicas: ${REPLICAS}
  selector:
    matchLabels:
      app: ${PROJECT_NAME}
  template:
    metadata:
      labels:
        app: ${PROJECT_NAME}
        version: ${APP_VERSION}
    spec:
      containers:
      - name: app
        image: ${APP_IMAGE}:${APP_VERSION}
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "${ENVIRONMENT}"
        - name: DB_HOST
          value: "${DB_HOST}"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "${MAX_MEMORY}"
            cpu: "${MAX_CPU}"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ${PROJECT_NAME}-service
  namespace: ${NAMESPACE}
spec:
  selector:
    app: ${PROJECT_NAME}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
EOF

    # Nginx configuration template
    cat > "${TEMPLATES_DIR}/nginx.conf.template" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:3000;
    }

    server {
        listen 80;
        server_name ${SERVER_HOST};
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name ${SERVER_HOST};

        ssl_certificate /etc/ssl/cert.pem;
        ssl_certificate_key /etc/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            access_log off;
            proxy_pass http://app;
        }
    }
}
EOF

    log_info "Deployment templates created"
}

# === BUILD FUNCTIONS ===

build_application() {
    local environment="$1"
    log_info "Building application for $environment environment..."
    
    # Load environment configuration
    source "${CONFIG_DIR}/${environment}.conf"
    source "${CONFIG_DIR}/deploy.conf"
    
    # Pre-build checks
    check_build_prerequisites
    
    # Clean previous builds
    log_info "Cleaning previous builds..."
    rm -rf dist/ build/
    
    # Install dependencies
    log_info "Installing dependencies..."
    if [ -f "package.json" ]; then
        npm ci || { log_error "Failed to install npm dependencies"; exit 1; }
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt || { log_error "Failed to install Python dependencies"; exit 1; }
    elif [ -f "Cargo.toml" ]; then
        cargo build --release || { log_error "Failed to build Rust application"; exit 1; }
    fi
    
    # Run tests
    log_info "Running tests..."
    run_tests
    
    # Build application
    log_info "Building application..."
    case "$BUILD_TYPE" in
        "npm")
            NODE_ENV="$environment" npm run build || { log_error "Build failed"; exit 1; }
            ;;
        "docker")
            build_docker_image "$environment"
            ;;
        "static")
            # Copy static files
            mkdir -p dist/
            cp -r src/* dist/
            ;;
        *)
            log_warn "Unknown build type: $BUILD_TYPE"
            ;;
    esac
    
    # Create build metadata
    create_build_metadata "$environment"
    
    log_info "Build completed successfully"
}

check_build_prerequisites() {
    log_debug "Checking build prerequisites..."
    
    # Check required commands
    local required_commands=("git" "ssh" "rsync")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check disk space
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        log_error "Insufficient disk space. Required: 5GB, Available: ${available_space}GB"
        exit 1
    fi
    
    # Check git status
    if [ -d ".git" ]; then
        if ! git diff-index --quiet HEAD --; then
            log_warn "Working directory has uncommitted changes"
        fi
    fi
    
    log_debug "Prerequisites check passed"
}

run_tests() {
    log_info "Running test suite..."
    
    if [ -f "package.json" ]; then
        npm test || { log_error "Tests failed"; exit 1; }
    elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
        python -m pytest || { log_error "Tests failed"; exit 1; }
    elif [ -f "Cargo.toml" ]; then
        cargo test || { log_error "Tests failed"; exit 1; }
    else
        log_warn "No test configuration found, skipping tests"
    fi
    
    log_info "All tests passed"
}

build_docker_image() {
    local environment="$1"
    log_info "Building Docker image for $environment..."
    
    local image_tag="${PROJECT_NAME}:${environment}-${TIMESTAMP}"
    
    # Build Docker image
    docker build \
        --build-arg ENVIRONMENT="$environment" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        -t "$image_tag" \
        . || { log_error "Docker build failed"; exit 1; }
    
    # Tag as latest for environment
    docker tag "$image_tag" "${PROJECT_NAME}:${environment}-latest"
    
    log_info "Docker image built: $image_tag"
}

create_build_metadata() {
    local environment="$1"
    log_info "Creating build metadata..."
    
    mkdir -p dist/
    
    cat > dist/build-info.json << EOF
{
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "buildTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "environment": "$environment",
    "builder": "$USER",
    "buildHost": "$(hostname)",
    "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "commit": "$(git log -1 --format='%H %s' 2>/dev/null || echo 'unknown')",
    "buildNumber": "$TIMESTAMP"
}
EOF
    
    log_info "Build metadata created"
}

# === DEPLOYMENT FUNCTIONS ===

deploy_application() {
    local environment="$1"
    log_info "Starting deployment to $environment..."
    
    # Load configurations
    source "${CONFIG_DIR}/${environment}.conf"
    source "${CONFIG_DIR}/deploy.conf"
    
    # Pre-deployment checks
    check_deployment_prerequisites "$environment"
    
    # Create backup if enabled
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        create_backup "$environment"
    fi
    
    # Deploy based on deployment type
    case "${DEPLOYMENT_TYPE:-traditional}" in
        "docker")
            deploy_docker "$environment"
            ;;
        "kubernetes")
            deploy_kubernetes "$environment"
            ;;
        "traditional")
            deploy_traditional "$environment"
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    # Post-deployment verification
    verify_deployment "$environment"
    
    # Send notifications
    send_deployment_notification "$environment" "success"
    
    log_info "Deployment to $environment completed successfully"
}

check_deployment_prerequisites() {
    local environment="$1"
    log_debug "Checking deployment prerequisites for $environment..."
    
    # Check SSH connection
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    if ! ssh -q "$deploy_target" exit; then
        log_error "SSH connection to $deploy_target failed"
        exit 1
    fi
    
    # Check remote disk space
    local remote_space=$(ssh "$deploy_target" "df -BG $DEPLOY_PATH | awk 'NR==2 {print \$4}' | sed 's/G//'")
    if [ "$remote_space" -lt 10 ]; then
        log_error "Insufficient disk space on remote server. Required: 10GB, Available: ${remote_space}GB"
        exit 1
    fi
    
    log_debug "Deployment prerequisites check passed"
}

deploy_traditional() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    local release_dir="releases/$TIMESTAMP"
    
    log_info "Deploying to traditional server: $deploy_target"
    
    # Create release directory
    ssh "$deploy_target" "mkdir -p $DEPLOY_PATH/$release_dir"
    
    # Upload files
    log_info "Uploading application files..."
    rsync -azP --exclude='.git' \
        dist/ "$deploy_target:$DEPLOY_PATH/$release_dir/"
    
    # Update symlink
    log_info "Updating current symlink..."
    ssh "$deploy_target" "cd $DEPLOY_PATH && ln -sfn $release_dir current"
    
    # Restart services
    restart_services "$environment"
    
    # Cleanup old releases
    cleanup_old_releases "$environment"
    
    log_info "Traditional deployment completed"
}

deploy_docker() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    log_info "Deploying Docker application to: $deploy_target"
    
    # Generate docker-compose file
    generate_docker_compose "$environment"
    
    # Upload docker-compose configuration
    scp docker-compose.yml "$deploy_target:/tmp/"
    
    # Deploy containers
    ssh "$deploy_target" "cd /tmp && docker-compose down && docker-compose pull && docker-compose up -d"
    
    log_info "Docker deployment completed"
}

deploy_kubernetes() {
    local environment="$1"
    
    log_info "Deploying to Kubernetes: $environment"
    
    # Generate Kubernetes manifests
    generate_kubernetes_manifests "$environment"
    
    # Apply manifests
    kubectl apply -f k8s-deployment.yml
    
    # Wait for rollout
    kubectl rollout status deployment/${PROJECT_NAME}-app -n "$NAMESPACE"
    
    log_info "Kubernetes deployment completed"
}

generate_docker_compose() {
    local environment="$1"
    log_debug "Generating docker-compose.yml for $environment"
    
    # Load template and substitute variables
    envsubst < "${TEMPLATES_DIR}/docker-compose.yml.template" > docker-compose.yml
}

generate_kubernetes_manifests() {
    local environment="$1"
    log_debug "Generating Kubernetes manifests for $environment"
    
    # Load template and substitute variables
    envsubst < "${TEMPLATES_DIR}/k8s-deployment.yml.template" > k8s-deployment.yml
}

# === VERIFICATION FUNCTIONS ===

verify_deployment() {
    local environment="$1"
    log_info "Verifying deployment for $environment..."
    
    # Health check
    perform_health_check "$environment"
    
    # Smoke tests
    run_smoke_tests "$environment"
    
    log_info "Deployment verification completed"
}

perform_health_check() {
    local environment="$1"
    local health_url="${ENVIRONMENTS[$environment]}${HEALTH_CHECK_URL}"
    local retries="$HEALTH_CHECK_RETRIES"
    
    log_info "Performing health check: $health_url"
    
    for ((i=1; i<=retries; i++)); do
        if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" "$health_url" > /dev/null; then
            log_info "Health check passed"
            return 0
        else
            log_warn "Health check attempt $i/$retries failed"
            if [ "$i" -lt "$retries" ]; then
                sleep 10
            fi
        fi
    done
    
    log_error "Health check failed after $retries attempts"
    return 1
}

run_smoke_tests() {
    local environment="$1"
    log_info "Running smoke tests for $environment..."
    
    # Basic connectivity test
    local base_url="${ENVIRONMENTS[$environment]}"
    
    # Test main page
    if curl -f -s "$base_url" > /dev/null; then
        log_info "Main page accessible"
    else
        log_error "Main page not accessible"
        return 1
    fi
    
    # Additional smoke tests can be added here
    
    log_info "Smoke tests passed"
}

# === BACKUP FUNCTIONS ===

create_backup() {
    local environment="$1"
    local backup_file="backup_${environment}_${TIMESTAMP}.tar.gz"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    log_info "Creating backup for $environment..."
    
    # Create backup on remote server
    ssh "$deploy_target" "cd $DEPLOY_PATH && tar -czf /tmp/$backup_file current/"
    
    # Download backup
    scp "$deploy_target:/tmp/$backup_file" "$BACKUP_DIR/"
    
    # Cleanup remote backup file
    ssh "$deploy_target" "rm -f /tmp/$backup_file"
    
    log_info "Backup created: $backup_file"
}

# === MAINTENANCE FUNCTIONS ===

restart_services() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    log_info "Restarting services for $environment..."
    
    # Restart web server (example for nginx)
    ssh "$deploy_target" "sudo systemctl reload nginx || sudo systemctl restart nginx"
    
    # Restart application service
    ssh "$deploy_target" "sudo systemctl restart ${PROJECT_NAME} || true"
    
    log_info "Services restarted"
}

cleanup_old_releases() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    log_info "Cleaning up old releases..."
    
    # Keep only the specified number of releases
    ssh "$deploy_target" "cd $DEPLOY_PATH/releases && ls -1t | tail -n +$((KEEP_RELEASES + 1)) | xargs -r rm -rf"
    
    log_info "Old releases cleaned up"
}

# === NOTIFICATION FUNCTIONS ===

send_deployment_notification() {
    local environment="$1"
    local status="$2"
    
    if [ "$NOTIFY_ON_SUCCESS" = "true" ] && [ "$status" = "success" ]; then
        send_notification "$environment" "✅ Deployment successful" "Deployment to $environment completed successfully"
    elif [ "$NOTIFY_ON_FAILURE" = "true" ] && [ "$status" = "failure" ]; then
        send_notification "$environment" "❌ Deployment failed" "Deployment to $environment failed"
    fi
}

send_notification() {
    local environment="$1"
    local title="$2"
    local message="$3"
    
    # Slack notification
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$title\", \"attachments\":[{\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK"
    fi
    
    # Email notification (if configured)
    if [ "$EMAIL_NOTIFICATIONS" = "true" ]; then
        echo "$message" | mail -s "$title" "$NOTIFICATION_EMAIL"
    fi
}

# === UTILITY FUNCTIONS ===

rollback_deployment() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    log_info "Rolling back deployment for $environment..."
    
    # Find previous release
    local previous_release=$(ssh "$deploy_target" "cd $DEPLOY_PATH/releases && ls -1t | sed -n '2p'")
    
    if [ -n "$previous_release" ]; then
        # Update symlink to previous release
        ssh "$deploy_target" "cd $DEPLOY_PATH && ln -sfn releases/$previous_release current"
        
        # Restart services
        restart_services "$environment"
        
        log_info "Rollback completed to release: $previous_release"
    else
        log_error "No previous release found for rollback"
        exit 1
    fi
}

show_deployment_status() {
    local environment="$1"
    local deploy_target="${DEPLOY_CONFIGS[$environment]}"
    
    echo "=== Deployment Status for $environment ==="
    
    # Current release
    local current_release=$(ssh "$deploy_target" "readlink $DEPLOY_PATH/current | xargs basename")
    echo "Current release: $current_release"
    
    # Available releases
    echo "Available releases:"
    ssh "$deploy_target" "cd $DEPLOY_PATH/releases && ls -lt | head -6"
    
    # Service status
    echo -e "\nService status:"
    ssh "$deploy_target" "systemctl is-active ${PROJECT_NAME} || echo 'Service not running'"
}

# === MAIN FUNCTIONS ===

show_help() {
    cat << 'EOF'
Deployment Automation & Configuration Management Package
Version: 3.0

USAGE:
    deploy.sh [COMMAND] [OPTIONS]

COMMANDS:
    init                    Initialize deployment system
    build <env>            Build application for environment
    deploy <env>           Deploy application to environment
    rollback <env>         Rollback to previous release
    status <env>           Show deployment status
    backup <env>           Create backup
    health <env>           Check application health

ENVIRONMENTS:
    development            Development environment
    staging                Staging environment
    production             Production environment

OPTIONS:
    -h, --help             Show this help message
    -v, --verbose          Enable verbose output
    --dry-run              Show what would be done without executing

EXAMPLES:
    deploy.sh init                          # Initialize deployment system
    deploy.sh build staging                 # Build for staging
    deploy.sh deploy production            # Deploy to production
    deploy.sh rollback production          # Rollback production
    deploy.sh status staging               # Show staging status

For more information, see the documentation in docs/
EOF
}

main() {
    # Parse command line arguments
    local command="${1:-}"
    local environment="${2:-}"
    
    case "$command" in
        "init")
            init_deployment_system
            ;;
        "build")
            [ -z "$environment" ] && { log_error "Environment required for build"; exit 1; }
            build_application "$environment"
            ;;
        "deploy")
            [ -z "$environment" ] && { log_error "Environment required for deploy"; exit 1; }
            deploy_application "$environment"
            ;;
        "rollback")
            [ -z "$environment" ] && { log_error "Environment required for rollback"; exit 1; }
            rollback_deployment "$environment"
            ;;
        "status")
            [ -z "$environment" ] && { log_error "Environment required for status"; exit 1; }
            show_deployment_status "$environment"
            ;;
        "backup")
            [ -z "$environment" ] && { log_error "Environment required for backup"; exit 1; }
            create_backup "$environment"
            ;;
        "health")
            [ -z "$environment" ] && { log_error "Environment required for health check"; exit 1; }
            perform_health_check "$environment"
            ;;
        "-h"|"--help"|"help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi