#!/bin/bash
# NexusController v2.0 Launcher Script
# Secure launcher with dependency checking and environment setup

set -euo pipefail  # Exit on any error, undefined variable, or pipe failure

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEXUS_DIR="$HOME/.nexus"
LOG_DIR="$NEXUS_DIR/logs"
VENV_DIR="$NEXUS_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_DIR/launcher.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_DIR/launcher.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_DIR/launcher.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_DIR/launcher.log"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up NexusController directories..."
    
    mkdir -p "$NEXUS_DIR"/{config,logs,keys,backups}
    
    # Set secure permissions
    chmod 700 "$NEXUS_DIR"
    chmod 700 "$NEXUS_DIR/keys"
    chmod 700 "$NEXUS_DIR/config"
    
    log_success "Directories created successfully"
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    local missing_commands=()
    local required_commands=("python3" "pip3" "nmap" "ssh-keyscan" "tar" "openssl")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_info "Install missing commands with:"
        log_info "  sudo apt update"
        log_info "  sudo apt install ${missing_commands[*]}"
        return 1
    fi
    
    # Check Python version
    local python_version
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    local min_version="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python 3.8+ required, found $python_version"
        return 1
    fi
    
    log_success "System requirements satisfied"
    return 0
}

# Create Python virtual environment
setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip &> /dev/null
    
    log_success "Virtual environment activated"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Create requirements.txt if it doesn't exist
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_warning "Requirements file not found, creating default..."
        cat > "$REQUIREMENTS_FILE" << EOF
# NexusController v2.0 Requirements
paramiko>=3.3.1
psutil>=5.9.5
cryptography>=41.0.4
requests>=2.31.0
tkinter-tooltip>=2.0.0
EOF
    fi
    
    # Install requirements
    if ! pip install -r "$REQUIREMENTS_FILE" &> /dev/null; then
        log_error "Failed to install Python dependencies"
        log_info "Try installing manually:"
        log_info "  pip3 install paramiko psutil cryptography requests"
        return 1
    fi
    
    log_success "Python dependencies installed"
}

# Check network connectivity
check_network() {
    log_info "Checking network connectivity..."
    
    # Check if we can reach the internet
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_warning "No internet connectivity detected"
        log_info "Some features may not work without internet access"
    else
        log_success "Network connectivity verified"
    fi
}

# Validate configuration files
validate_configuration() {
    log_info "Validating configuration..."
    
    local config_file="$NEXUS_DIR/config/nexus.json"
    
    # Create default configuration if it doesn't exist
    if [ ! -f "$config_file" ]; then
        log_info "Creating default configuration..."
        cat > "$config_file" << EOF
{
    "version": "2.0",
    "created": "$(date -Iseconds)",
    "network": {
        "default_range": "10.0.0.0/24",
        "scan_timeout": 120,
        "scan_rate_limit": 10
    },
    "security": {
        "ssh_timeout": 30,
        "session_timeout": 3600,
        "max_retries": 3
    },
    "ui": {
        "theme": "dark",
        "geometry": "1200x800"
    }
}
EOF
        chmod 600 "$config_file"
        log_success "Default configuration created"
    fi
    
    # Validate JSON syntax
    if ! python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
        log_error "Invalid configuration file syntax"
        return 1
    fi
    
    log_success "Configuration validated"
}

# Check for existing processes
check_running_processes() {
    log_info "Checking for running NexusController processes..."
    
    local pids
    pids=$(pgrep -f "nexus_controller_v2.py" || true)
    
    if [ -n "$pids" ]; then
        log_warning "Found running NexusController processes: $pids"
        read -p "Kill existing processes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # shellcheck disable=SC2086
            kill $pids
            sleep 2
            log_success "Existing processes terminated"
        else
            log_info "Continuing with existing processes running"
        fi
    fi
}

# Launch NexusController
launch_nexus() {
    log_info "Launching NexusController v2.0..."
    
    # Ensure we're in the script directory
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment if it exists
    if [ -f "$VENV_DIR/bin/activate" ]; then
        # shellcheck source=/dev/null
        source "$VENV_DIR/bin/activate"
    fi
    
    # Set Python path
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # Launch with GUI
    if [ "${1:-gui}" = "gui" ]; then
        log_info "Starting GUI mode..."
        
        # Check if X11 is available
        if [ -z "${DISPLAY:-}" ]; then
            log_error "No X11 display available for GUI mode"
            log_info "Try: export DISPLAY=:0"
            return 1
        fi
        
        python3 nexus_gui.py 2>&1 | tee -a "$LOG_DIR/nexus_$(date +%Y%m%d).log"
    else
        # CLI mode
        log_info "Starting CLI mode..."
        python3 nexus_controller_v2.py 2>&1 | tee -a "$LOG_DIR/nexus_$(date +%Y%m%d).log"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    # Deactivate virtual environment if active
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        deactivate
    fi
    
    log_success "Cleanup completed"
}

# Signal handlers
trap cleanup EXIT
trap 'log_error "Interrupted by user"; exit 130' INT
trap 'log_error "Terminated"; exit 143' TERM

# Main execution
main() {
    echo "================================================================"
    echo "              NexusController v2.0 Launcher"
    echo "         Enterprise Infrastructure Management"
    echo "================================================================"
    echo
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    log_info "Starting NexusController launcher at $(date)"
    
    # Run setup steps
    setup_directories || exit 1
    check_system_requirements || exit 1
    setup_virtual_environment || exit 1
    install_dependencies || exit 1
    check_network
    validate_configuration || exit 1
    check_running_processes
    
    echo
    log_success "All checks passed! Launching NexusController..."
    echo
    
    # Launch the application
    launch_nexus "${1:-gui}"
}

# Help function
show_help() {
    cat << EOF
NexusController v2.0 Launcher

Usage: $0 [OPTION]

Options:
    gui         Launch with graphical interface (default)
    cli         Launch in command-line mode
    help        Show this help message
    check       Run system checks only
    install     Install/update dependencies only

Examples:
    $0              # Launch GUI mode
    $0 gui          # Launch GUI mode
    $0 cli          # Launch CLI mode
    $0 check        # Check system requirements
    $0 install      # Install dependencies

EOF
}

# Parse command line arguments
case "${1:-gui}" in
    "gui")
        main "gui"
        ;;
    "cli")
        main "cli"
        ;;
    "check")
        setup_directories
        check_system_requirements
        check_network
        validate_configuration
        log_success "System check completed"
        ;;
    "install")
        setup_directories
        check_system_requirements
        setup_virtual_environment
        install_dependencies
        log_success "Installation completed"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac