#!/bin/bash

# TidyTux Installation Script
# Installs both tailored and GUI versions

set -euo pipefail

readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[0;33m'
readonly RED='\033[0;31m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

readonly INSTALL_DIR="$HOME/.local/bin"
readonly CONFIG_DIR="$HOME/.config/tidytux"
readonly DESKTOP_DIR="$HOME/.local/share/applications"

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for basic tools
    local basic_tools=("curl" "wget" "find" "du" "df")
    for tool in "${basic_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            missing_deps+=("$tool")
        fi
    done
    
    # Check for GUI tools (optional)
    if ! command -v zenity &>/dev/null; then
        warning "zenity not found - GUI features will be limited"
        echo "  Install with: sudo apt install zenity"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing required dependencies: ${missing_deps[*]}"
        echo "Install with: sudo apt install ${missing_deps[*]}"
        exit 1
    fi
    
    success "All dependencies satisfied"
}

# Create necessary directories
create_directories() {
    log "Creating directories..."
    
    local dirs=("$INSTALL_DIR" "$CONFIG_DIR" "$DESKTOP_DIR")
    
    for dir in "${dirs[@]}"; do
        if mkdir -p "$dir"; then
            success "Created $dir"
        else
            error "Failed to create $dir"
            exit 1
        fi
    done
}

# Install scripts
install_scripts() {
    log "Installing TidyTux scripts..."
    
    # Copy the tailored script
    if [ -f "tailored_tidytux.sh" ]; then
        cp "tailored_tidytux.sh" "$INSTALL_DIR/tidytux"
        chmod +x "$INSTALL_DIR/tidytux"
        success "Installed tailored script as 'tidytux'"
    else
        warning "tailored_tidytux.sh not found in current directory"
    fi
    
    # Copy the GUI script
    if [ -f "tidytux_gui.sh" ]; then
        cp "tidytux_gui.sh" "$INSTALL_DIR/tidytux-gui"
        chmod +x "$INSTALL_DIR/tidytux-gui"
        success "Installed GUI script as 'tidytux-gui'"
    else
        warning "tidytux_gui.sh not found in current directory"
    fi
}

# Create desktop entry for GUI
create_desktop_entry() {
    if [ ! -f "$INSTALL_DIR/tidytux-gui" ]; then
        warning "GUI script not installed, skipping desktop entry"
        return
    fi
    
    log "Creating desktop entry..."
    
    cat > "$DESKTOP_DIR/tidytux-gui.desktop" << EOF
[Desktop Entry]
Name=TidyTux GUI
Comment=Graphical system cleanup utility
Exec=$INSTALL_DIR/tidytux-gui
Icon=applications-system
Terminal=false
Type=Application
Categories=System;Utility;
StartupNotify=true
EOF
    
    chmod +x "$DESKTOP_DIR/tidytux-gui.desktop"
    success "Created desktop entry"
}

# Create default configuration
create_config() {
    log "Creating default configuration..."
    
    cat > "$CONFIG_DIR/tidytux.conf" << 'EOF'
# TidyTux Configuration File
# Customized for your system

# Cleanup targets
CLEAN_SYSTEM=true
CLEAN_DEV=true
CLEAN_BROWSERS=true
CLEAN_DOCKER=true
CLEAN_CLOUD=true

# Thresholds
LARGE_FILE_THRESHOLD=100  # MB
OLD_FILE_DAYS=90
EMERGENCY_SPACE_GB=1
WARNING_SPACE_GB=5

# Your specific exclusions (based on your directory structure)
EXCLUDE_PATTERNS=".git:node_modules:venv:virtualenv:.ssh:important:Financial"
PROTECTED_DIRS="$HOME/Documents/Financial:$HOME/Pictures:$HOME/Videos:$HOME/scripts/Ethereum"

# Performance
ENABLE_PARALLEL=true
MAX_PARALLEL_JOBS=4
BACKUP_RETENTION_DAYS=30

# Features
AUTO_INSTALL_TOOLS=false
GENERATE_REPORT=true
SAVE_STATE=true
JSON_OUTPUT=false

# GUI Settings
SHOW_NOTIFICATIONS=true
AUTO_OPEN_REPORT=true
CONFIRM_DANGEROUS_OPERATIONS=true
EOF
    
    success "Created configuration file"
}

# Update PATH
update_path() {
    log "Updating PATH..."
    
    local shell_rc=""
    case "$SHELL" in
        */bash) shell_rc="$HOME/.bashrc" ;;
        */zsh) shell_rc="$HOME/.zshrc" ;;
        */fish) shell_rc="$HOME/.config/fish/config.fish" ;;
        *) warning "Unknown shell: $SHELL" ;;
    esac
    
    if [ -n "$shell_rc" ] && [ -f "$shell_rc" ]; then
        if ! grep -q "$INSTALL_DIR" "$shell_rc"; then
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$shell_rc"
            success "Updated PATH in $shell_rc"
        else
            log "PATH already updated"
        fi
    fi
}

# Create quick launcher script
create_launcher() {
    log "Creating quick launcher..."
    
    cat > "$HOME/cleanup" << EOF
#!/bin/bash
# TidyTux Quick Launcher

if [ -n "\${DISPLAY:-}" ] && command -v tidytux-gui &>/dev/null; then
    echo "🖥️  Starting TidyTux GUI..."
    exec tidytux-gui
elif command -v tidytux &>/dev/null; then
    echo "💻 Starting TidyTux CLI..."
    exec tidytux "\$@"
else
    echo "❌ TidyTux not found in PATH"
    echo "Make sure $INSTALL_DIR is in your PATH"
    exit 1
fi
EOF
    
    chmod +x "$HOME/cleanup"
    success "Created quick launcher at ~/cleanup"
}

# Install completion
install_completion() {
    log "Setting up bash completion..."
    
    local completion_dir="$HOME/.local/share/bash-completion/completions"
    mkdir -p "$completion_dir"
    
    cat > "$completion_dir/tidytux" << 'EOF'
# TidyTux bash completion

_tidytux() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    opts="--help --version --dry-run --verbose --yes --emergency --schedule --config --only-system --only-dev --only-browsers"
    
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}

complete -F _tidytux tidytux
EOF
    
    success "Installed bash completion"
}

# Show installation summary
show_summary() {
    echo
    echo -e "${BOLD}🎉 TidyTux Installation Complete! 🎉${NC}"
    echo
    echo "📋 Installed Components:"
    
    if [ -f "$INSTALL_DIR/tidytux" ]; then
        echo -e "  ${GREEN}✅${NC} TidyTux CLI: tidytux"
    fi
    
    if [ -f "$INSTALL_DIR/tidytux-gui" ]; then
        echo -e "  ${GREEN}✅${NC} TidyTux GUI: tidytux-gui"
    fi
    
    if [ -f "$DESKTOP_DIR/tidytux-gui.desktop" ]; then
        echo -e "  ${GREEN}✅${NC} Desktop Entry: Available in applications menu"
    fi
    
    if [ -f "$HOME/cleanup" ]; then
        echo -e "  ${GREEN}✅${NC} Quick Launcher: ~/cleanup"
    fi
    
    echo
    echo "🚀 Getting Started:"
    echo "  • Command line: tidytux --help"
    echo "  • GUI mode: tidytux-gui"
    echo "  • Quick start: ~/cleanup"
    echo "  • Desktop: Search for 'TidyTux GUI' in applications"
    echo
    echo "📁 Configuration: $CONFIG_DIR/tidytux.conf"
    echo "📊 Logs will be saved to: ~/.tidytux/logs/"
    echo "🛡️  Backups will be saved to: ~/.tidytux/backups/"
    echo
    echo "⚠️  Note: Restart your terminal or run 'source ~/.bashrc' to use commands"
    echo
    
    # Offer to run GUI immediately
    if [ -f "$INSTALL_DIR/tidytux-gui" ] && [ -n "${DISPLAY:-}" ]; then
        echo -e "${YELLOW}Would you like to run TidyTux GUI now? [y/N]${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            exec "$INSTALL_DIR/tidytux-gui"
        fi
    fi
}

# Create uninstaller
create_uninstaller() {
    log "Creating uninstaller..."
    
    cat > "$INSTALL_DIR/tidytux-uninstall" << EOF
#!/bin/bash
# TidyTux Uninstaller

echo "🗑️  Uninstalling TidyTux..."

# Remove scripts
rm -f "$INSTALL_DIR/tidytux"
rm -f "$INSTALL_DIR/tidytux-gui"
rm -f "$INSTALL_DIR/tidytux-uninstall"
rm -f "$HOME/cleanup"

# Remove desktop entry
rm -f "$DESKTOP_DIR/tidytux-gui.desktop"

# Remove completion
rm -f "$HOME/.local/share/bash-completion/completions/tidytux"

echo "✅ TidyTux uninstalled"
echo "Configuration and logs preserved in ~/.config/tidytux and ~/.tidytux"
echo "Remove manually if desired:"
echo "  rm -rf ~/.config/tidytux ~/.tidytux"
EOF
    
    chmod +x "$INSTALL_DIR/tidytux-uninstall"
    success "Created uninstaller: tidytux-uninstall"
}

# Main installation process
main() {
    echo -e "${BOLD}🧹 TidyTux Installation Script${NC}"
    echo "Installing tailored system cleanup tools..."
    echo
    
    check_dependencies
    create_directories
    install_scripts
    create_desktop_entry
    create_config
    update_path
    create_launcher
    install_completion
    create_uninstaller
    show_summary
}

# Run installation
main "$@"