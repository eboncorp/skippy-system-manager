#!/bin/bash
# NexusController v2.0 - Docker Entrypoint Script
# Handles container initialization and startup

set -euo pipefail

# Configuration
NEXUS_USER="nexus"
VNC_DISPLAY=":99"
VNC_PORT="5901"
VNC_PASSWORD="${VNC_PASSWORD:-nexus123}"

# Logging functions
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >&2
}

# Initialize VNC for GUI access
init_vnc() {
    log_info "Initializing VNC server for GUI access..."
    
    # Start Xvfb virtual display
    Xvfb $VNC_DISPLAY -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
    export DISPLAY=$VNC_DISPLAY
    
    # Wait for X server to start
    sleep 2
    
    # Start window manager
    fluxbox &
    
    # Configure VNC password
    mkdir -p ~/.vnc
    echo "$VNC_PASSWORD" | vncpasswd -f > ~/.vnc/passwd
    chmod 600 ~/.vnc/passwd
    
    # Start VNC server
    x11vnc -display $VNC_DISPLAY -forever -usepw -create -rfbport $VNC_PORT &
    
    log_info "VNC server started on port $VNC_PORT (password: $VNC_PASSWORD)"
}

# Initialize NexusController configuration
init_nexus_config() {
    log_info "Initializing NexusController configuration..."
    
    # Ensure config directory exists with proper permissions
    mkdir -p ~/.nexus/{config,logs,keys,backups}
    chmod -R 700 ~/.nexus
    
    # Create default configuration if it doesn't exist
    if [ ! -f ~/.nexus/config/nexus.json ]; then
        log_info "Creating default configuration..."
        cat > ~/.nexus/config/nexus.json << EOF
{
    "version": "2.0",
    "environment": "${NEXUS_ENV:-production}",
    "created": "$(date -Iseconds)",
    "network": {
        "default_range": "${NEXUS_NETWORK_RANGE:-10.0.0.0/24}",
        "scan_timeout": ${NEXUS_SCAN_TIMEOUT:-120},
        "scan_rate_limit": ${NEXUS_SCAN_RATE_LIMIT:-10}
    },
    "security": {
        "ssh_timeout": ${NEXUS_SSH_TIMEOUT:-30},
        "session_timeout": ${NEXUS_SESSION_TIMEOUT:-3600},
        "max_retries": ${NEXUS_MAX_RETRIES:-3}
    },
    "ui": {
        "theme": "${NEXUS_THEME:-dark}",
        "geometry": "${NEXUS_GEOMETRY:-1200x800}"
    },
    "logging": {
        "level": "${LOG_LEVEL:-INFO}",
        "max_files": 10,
        "max_size": "100MB"
    }
}
EOF
        chmod 600 ~/.nexus/config/nexus.json
        log_info "Default configuration created"
    fi
    
    # Set up logging
    touch ~/.nexus/logs/nexus_$(date +%Y%m%d).log
    chmod 600 ~/.nexus/logs/nexus_$(date +%Y%m%d).log
}

# Wait for dependencies
wait_for_services() {
    log_info "Waiting for dependent services..."
    
    # Wait for Redis if configured
    if [ -n "${REDIS_HOST:-}" ]; then
        log_info "Waiting for Redis at $REDIS_HOST..."
        while ! nc -z "$REDIS_HOST" "${REDIS_PORT:-6379}"; do
            sleep 1
        done
        log_info "Redis is ready"
    fi
    
    # Wait for PostgreSQL if configured
    if [ -n "${POSTGRES_HOST:-}" ]; then
        log_info "Waiting for PostgreSQL at $POSTGRES_HOST..."
        while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
            sleep 1
        done
        log_info "PostgreSQL is ready"
    fi
    
    # Wait for Vault if configured
    if [ -n "${VAULT_ADDR:-}" ]; then
        log_info "Waiting for Vault at $VAULT_ADDR..."
        while ! curl -s "$VAULT_ADDR/v1/sys/health" >/dev/null 2>&1; do
            sleep 1
        done
        log_info "Vault is ready"
    fi
}

# Run health checks
health_check() {
    log_info "Running container health checks..."
    
    # Check Python dependencies
    if ! python3 -c "import paramiko, psutil, cryptography, tkinter" 2>/dev/null; then
        log_error "Python dependencies check failed"
        return 1
    fi
    
    # Check system tools
    local required_tools=("nmap" "ssh-keyscan" "tar" "openssl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool '$tool' not found"
            return 1
        fi
    done
    
    # Check file permissions
    if [ ! -r ~/.nexus/config/nexus.json ]; then
        log_error "Configuration file not readable"
        return 1
    fi
    
    log_info "Health checks passed"
    return 0
}

# Start NexusController based on mode
start_nexus() {
    local mode="${1:-gui}"
    
    log_info "Starting NexusController in '$mode' mode..."
    
    case "$mode" in
        "gui")
            if [ -z "${DISPLAY:-}" ]; then
                log_error "No DISPLAY set for GUI mode"
                exit 1
            fi
            log_info "Starting GUI mode with VNC access on port $VNC_PORT"
            exec python3 nexus_gui.py
            ;;
        "cli")
            log_info "Starting CLI mode"
            exec python3 nexus_controller_v2.py
            ;;
        "api")
            log_info "Starting API server mode"
            # Future: Start REST API server
            exec python3 nexus_api_server.py
            ;;
        "test")
            log_info "Running test suite"
            exec python3 test_nexus.py
            ;;
        *)
            log_error "Unknown mode: $mode"
            log_info "Available modes: gui, cli, api, test"
            exit 1
            ;;
    esac
}

# Signal handlers
cleanup() {
    log_info "Shutting down NexusController..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    # Clean up temporary files
    rm -rf /tmp/.X*
    
    log_info "Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    local mode="${1:-gui}"
    
    log_info "=== NexusController v2.0 Container Starting ==="
    log_info "Mode: $mode"
    log_info "User: $(whoami)"
    log_info "Working Directory: $(pwd)"
    log_info "Environment: ${NEXUS_ENV:-development}"
    
    # Initialize services
    init_nexus_config
    
    # Wait for dependencies
    wait_for_services
    
    # Initialize VNC for GUI mode
    if [ "$mode" = "gui" ]; then
        init_vnc
    fi
    
    # Run health checks
    if ! health_check; then
        log_error "Health checks failed"
        exit 1
    fi
    
    # Start NexusController
    start_nexus "$mode"
}

# Parse command line arguments
case "${1:-gui}" in
    "gui"|"cli"|"api"|"test")
        main "$1"
        ;;
    "health")
        health_check
        exit $?
        ;;
    "version")
        echo "NexusController v2.0 Container"
        python3 -c "from nexus_controller_v2 import __version__; print(f'Core version: {__version__}')" 2>/dev/null || echo "Core version: unknown"
        exit 0
        ;;
    "help"|"-h"|"--help")
        cat << EOF
NexusController v2.0 Container

Usage: docker run nexuscontroller:v2.0 [COMMAND]

Commands:
    gui         Start GUI mode with VNC access (default)
    cli         Start CLI mode
    api         Start API server mode
    test        Run test suite
    health      Run health checks
    version     Show version information
    help        Show this help message

Environment Variables:
    NEXUS_ENV              Environment (development|production)
    NEXUS_NETWORK_RANGE    Default network range (10.0.0.0/24)
    NEXUS_SCAN_TIMEOUT     Network scan timeout (120)
    NEXUS_SCAN_RATE_LIMIT  Scan rate limit (10)
    VNC_PASSWORD           VNC access password (nexus123)
    LOG_LEVEL              Logging level (INFO)

Ports:
    8080        API server (when enabled)
    5901        VNC server (GUI mode)

Volume Mounts:
    /app/.nexus     Configuration and data directory

EOF
        exit 0
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Run with 'help' for usage information"
        exit 1
        ;;
esac