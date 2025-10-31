#!/bin/bash
# Home Server Master Installer
# Automatically sets up and configures the complete home server system

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Installation paths
INSTALL_DIR="$HOME/.home-server"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.home-server/config"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# Print functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   Home Server Master Installer v1.0${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! python3 -m pip --version &> /dev/null; then
        print_warning "pip not found, attempting to install..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        else
            print_error "Could not install pip. Please install manually."
            exit 1
        fi
    fi
    
    # Check for systemd (optional)
    if command -v systemctl &> /dev/null; then
        SYSTEMD_AVAILABLE=true
        print_status "systemd detected - service management available"
    else
        SYSTEMD_AVAILABLE=false
        print_warning "systemd not detected - automatic startup not available"
    fi
    
    print_success "Requirements check passed"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    
    # Activate venv and install packages
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Core dependencies
    pip install --upgrade pip
    pip install pyyaml psutil click
    
    # Optional dependencies with fallback
    pip install requests || print_warning "requests not installed - some features may be limited"
    pip install paramiko || print_warning "paramiko not installed - SSH features disabled"
    pip install flask || print_warning "flask not installed - web UI disabled"
    pip install pystray pillow || print_warning "pystray not installed - system tray disabled"
    
    deactivate
    print_success "Dependencies installed"
}

# Setup directory structure
setup_directories() {
    print_status "Creating directory structure..."
    
    mkdir -p "$INSTALL_DIR"/{logs,data,config,components,plugins,backups}
    mkdir -p "$BIN_DIR"
    mkdir -p "$CONFIG_DIR"
    
    # Set proper permissions
    chmod 700 "$INSTALL_DIR"
    chmod 755 "$BIN_DIR"
    
    print_success "Directories created"
}

# Copy files to installation directory
copy_files() {
    print_status "Copying files..."
    
    # Get the directory where the installer is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Copy main program
    cp "$SCRIPT_DIR/home_server_master.py" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/home_server_master.py"
    
    # Copy component files if they exist
    components=(
        "advanced_system_manager.py"
        "web_system_manager.py"
        "multi_server_manager.py"
        "ai_maintenance_engine.py"
        "cloud_monitoring_integration.py"
        "unified-system-manager.sh"
        "gdrive_manager.sh"
        "complete-tidytux.sh"
    )
    
    for component in "${components[@]}"; do
        if [ -f "$SCRIPT_DIR/$component" ]; then
            cp "$SCRIPT_DIR/$component" "$INSTALL_DIR/components/"
            print_status "Copied $component"
        else
            print_warning "$component not found - feature may be unavailable"
        fi
    done
    
    # Copy Ethereum node scripts
    if [ -d "$SCRIPT_DIR/Downloads" ]; then
        mkdir -p "$INSTALL_DIR/Downloads"
        find "$SCRIPT_DIR/Downloads" -name "*.sh" -exec cp {} "$INSTALL_DIR/Downloads/" \;
    fi
    
    print_success "Files copied"
}

# Create wrapper script
create_wrapper() {
    print_status "Creating wrapper script..."
    
    cat > "$BIN_DIR/home-server" << 'EOF'
#!/bin/bash
# Home Server Master wrapper script

INSTALL_DIR="$HOME/.home-server"
VENV_PYTHON="$INSTALL_DIR/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found. Please run the installer again."
    exit 1
fi

# Run the home server master with virtual environment
exec "$VENV_PYTHON" "$INSTALL_DIR/home_server_master.py" "$@"
EOF
    
    chmod +x "$BIN_DIR/home-server"
    
    # Add to PATH if not already there
    if ! echo "$PATH" | grep -q "$BIN_DIR"; then
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
        print_warning "Added $BIN_DIR to PATH. Please run: source ~/.bashrc"
    fi
    
    print_success "Wrapper script created"
}

# Create default configuration
create_default_config() {
    print_status "Creating default configuration..."
    
    cat > "$CONFIG_DIR/server.yaml" << EOF
# Home Server Master Configuration
server_name: "HomeServer"
server_port: 8080
enable_web_ui: true
enable_api: true

# Component settings
enable_system_manager: true
enable_ethereum_node: false
enable_cloud_sync: true
enable_monitoring: true
enable_ai_maintenance: false

# Paths
data_dir: "$INSTALL_DIR/data"
log_dir: "$INSTALL_DIR/logs"
config_dir: "$CONFIG_DIR"

# Performance
max_workers: 4
check_interval: 60
EOF
    
    print_success "Default configuration created"
}

# Setup systemd service
setup_systemd_service() {
    if [ "$SYSTEMD_AVAILABLE" != "true" ]; then
        return
    fi
    
    print_status "Setting up systemd service..."
    
    mkdir -p "$SYSTEMD_USER_DIR"
    
    cat > "$SYSTEMD_USER_DIR/home-server.service" << EOF
[Unit]
Description=Home Server Master
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$BIN_DIR/home-server start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=default.target
EOF
    
    # Reload systemd
    systemctl --user daemon-reload
    
    print_success "Systemd service created"
    print_status "To enable automatic startup, run:"
    echo "  systemctl --user enable home-server.service"
    echo "  systemctl --user start home-server.service"
}

# Post-installation setup
post_install() {
    print_header
    print_success "Installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Source your bashrc to update PATH:"
    echo "   source ~/.bashrc"
    echo
    echo "2. Start the server:"
    echo "   home-server start"
    echo
    echo "3. Check status:"
    echo "   home-server status"
    echo
    echo "4. Configure settings:"
    echo "   home-server configure --help"
    echo
    if [ "$SYSTEMD_AVAILABLE" = "true" ]; then
        echo "5. Enable automatic startup (optional):"
        echo "   systemctl --user enable home-server.service"
        echo "   systemctl --user start home-server.service"
        echo
    fi
    echo "Configuration file: $CONFIG_DIR/server.yaml"
    echo "Logs directory: $INSTALL_DIR/logs"
    echo
    print_status "Web UI will be available at: http://localhost:8080"
}

# Main installation process
main() {
    print_header
    
    # Check if already installed
    if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/home_server_master.py" ]; then
        print_warning "Home Server appears to be already installed at $INSTALL_DIR"
        read -p "Do you want to reinstall? This will preserve your config. (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installation cancelled"
            exit 0
        fi
        # Backup config
        if [ -f "$CONFIG_DIR/server.yaml" ]; then
            cp "$CONFIG_DIR/server.yaml" "$CONFIG_DIR/server.yaml.bak"
            print_status "Backed up existing configuration"
        fi
    fi
    
    # Run installation steps
    check_requirements
    setup_directories
    install_dependencies
    copy_files
    create_wrapper
    
    # Restore config if it was backed up
    if [ -f "$CONFIG_DIR/server.yaml.bak" ]; then
        mv "$CONFIG_DIR/server.yaml.bak" "$CONFIG_DIR/server.yaml"
        print_status "Restored existing configuration"
    else
        create_default_config
    fi
    
    setup_systemd_service
    post_install
}

# Run main installation
main "$@"