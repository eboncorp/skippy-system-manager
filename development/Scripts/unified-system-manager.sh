#!/bin/bash

# Unified System Manager - Combines TidyTux, Google Drive Manager, and GUI
# Version 1.0.0
# A comprehensive system management tool for Linux

VERSION="1.0.0"
PROGRAM_NAME="Unified System Manager"
PROGRAM_DESCRIPTION="Complete system management: cleanup, backup, and cloud storage"

# Set strict error handling
set -e
set -u

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "This script should NOT be run as root" >&2
    exit 1
fi

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration paths
CONFIG_DIR="$HOME/.unified-system-manager"
CONFIG_FILE="$CONFIG_DIR/config.conf"
LOG_DIR="$CONFIG_DIR/logs"
BACKUP_DIR="$CONFIG_DIR/backups"
CACHE_DIR="$CONFIG_DIR/cache"

# Component paths
TIDYTUX_SCRIPT="$CONFIG_DIR/components/tidytux.sh"
GDRIVE_SCRIPT="$CONFIG_DIR/components/gdrive-manager.sh"
GUI_SCRIPT="$CONFIG_DIR/components/unified-gui.py"

# Ensure directories exist
mkdir -p "$CONFIG_DIR" "$LOG_DIR" "$BACKUP_DIR" "$CACHE_DIR" "$CONFIG_DIR/components"

# Default configuration
DEFAULT_CONFIG="# Unified System Manager Configuration
# TidyTux Settings
ENABLE_TIDYTUX=true
AUTO_CLEANUP=false
CLEANUP_SCHEDULE=weekly

# Google Drive Settings
ENABLE_GDRIVE=true
GDRIVE_LOCAL_PATH=$HOME/GoogleDrive
RCLONE_REMOTE_NAME=googledrive
AUTO_BACKUP=false
BACKUP_SCHEDULE=daily

# GUI Settings
ENABLE_GUI=true
GUI_THEME=modern
START_MINIMIZED=false

# General Settings
NOTIFY_ENABLED=true
LOG_LEVEL=info
MAX_LOG_SIZE=100M"

# Function to print colored output
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

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   $PROGRAM_NAME v$VERSION${NC}"
    echo -e "${BLUE}   $PROGRAM_DESCRIPTION${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

# Initialize configuration
init_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "$DEFAULT_CONFIG" > "$CONFIG_FILE"
        print_status "Created default configuration at $CONFIG_FILE"
    fi
    
    # Source configuration
    source "$CONFIG_FILE"
}

# Check and install dependencies
check_dependencies() {
    local missing_deps=()
    
    # Core dependencies
    local core_deps=(
        "python3"
        "rclone"
        "ncdu"
        "fdupes"
        "bc"
        "curl"
        "git"
    )
    
    # Python dependencies
    local python_deps=(
        "tkinter"
        "subprocess"
        "threading"
        "queue"
    )
    
    print_status "Checking system dependencies..."
    
    # Check core dependencies
    for dep in "${core_deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    # Check Python and tkinter
    if command -v python3 &> /dev/null; then
        if ! python3 -c "import tkinter" &> /dev/null 2>&1; then
            missing_deps+=("python3-tk")
        fi
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        print_success "All dependencies are installed"
        return 0
    fi
    
    print_warning "Missing dependencies: ${missing_deps[*]}"
    
    read -p "Would you like to install missing dependencies? (y/n): " install_deps
    if [[ $install_deps =~ ^[Yy]$ ]]; then
        print_status "Installing dependencies..."
        
        # Update package list
        sudo apt update
        
        # Install missing dependencies
        for dep in "${missing_deps[@]}"; do
            case "$dep" in
                "rclone")
                    print_status "Installing rclone..."
                    curl -f https://rclone.org/install.sh | sudo bash
                    ;;
                "python3-tk")
                    sudo apt install -y python3-tk
                    ;;
                *)
                    sudo apt install -y "$dep"
                    ;;
            esac
        done
        
        print_success "Dependencies installed successfully"
    else
        print_error "Cannot proceed without required dependencies"
        exit 1
    fi
}

# Extract embedded components
extract_components() {
    print_status "Extracting system components..."
    
    # Check if components already exist
    if [ -f "$TIDYTUX_SCRIPT" ] && [ -f "$GDRIVE_SCRIPT" ] && [ -f "$GUI_SCRIPT" ]; then
        print_status "Components already extracted"
        return 0
    fi
    
    # Copy components from Skippy folder if they exist
    if [ -f "$HOME/Skippy/complete-tidytux.sh" ]; then
        cp "$HOME/Skippy/complete-tidytux.sh" "$TIDYTUX_SCRIPT"
        chmod +x "$TIDYTUX_SCRIPT"
        print_success "Extracted TidyTux component"
    fi
    
    if [ -f "$HOME/Skippy/gdrive_manager.sh" ]; then
        cp "$HOME/Skippy/gdrive_manager.sh" "$GDRIVE_SCRIPT"
        chmod +x "$GDRIVE_SCRIPT"
        print_success "Extracted Google Drive Manager component"
    fi
    
    if [ -f "$HOME/Skippy/gdrive_gui.py" ]; then
        cp "$HOME/Skippy/gdrive_gui.py" "$GUI_SCRIPT"
        chmod +x "$GUI_SCRIPT"
        print_success "Extracted GUI component"
    fi
}

# Create desktop entry
create_desktop_entry() {
    local desktop_dir="$HOME/.local/share/applications"
    local desktop_file="$desktop_dir/unified-system-manager.desktop"
    
    mkdir -p "$desktop_dir"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Unified System Manager
Comment=Complete system management tool
Exec=$0 --gui
Icon=system-software-install
Terminal=false
Categories=System;Utility;
StartupNotify=true
EOF
    
    chmod +x "$desktop_file"
    
    # Update desktop database if available
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$desktop_dir"
    fi
    
    print_success "Desktop entry created"
}

# Quick setup wizard
quick_setup() {
    print_header
    print_status "Welcome to the Unified System Manager setup wizard!"
    echo
    
    # Step 1: Check dependencies
    print_status "Step 1/4: Checking dependencies..."
    check_dependencies
    echo
    
    # Step 2: Extract components
    print_status "Step 2/4: Setting up components..."
    extract_components
    echo
    
    # Step 3: Configure
    print_status "Step 3/4: Configuration..."
    
    # TidyTux configuration
    if [ "$ENABLE_TIDYTUX" = true ]; then
        read -p "Enable automatic system cleanup? (y/n): " auto_cleanup
        if [[ $auto_cleanup =~ ^[Yy]$ ]]; then
            sed -i 's/AUTO_CLEANUP=false/AUTO_CLEANUP=true/' "$CONFIG_FILE"
        fi
    fi
    
    # Google Drive configuration
    if [ "$ENABLE_GDRIVE" = true ]; then
        read -p "Configure Google Drive backup now? (y/n): " config_gdrive
        if [[ $config_gdrive =~ ^[Yy]$ ]]; then
            "$GDRIVE_SCRIPT" config
        fi
    fi
    echo
    
    # Step 4: Create shortcuts
    print_status "Step 4/4: Creating shortcuts..."
    create_desktop_entry
    
    # Create command alias
    read -p "Add 'usm' command alias to your shell? (y/n): " add_alias
    if [[ $add_alias =~ ^[Yy]$ ]]; then
        echo "alias usm='$0'" >> "$HOME/.bashrc"
        print_success "Added 'usm' command alias (restart shell to use)"
    fi
    
    print_success "Setup completed successfully!"
    echo
    print_status "You can now use the Unified System Manager:"
    echo "  - From terminal: $0"
    echo "  - From GUI: $0 --gui"
    echo "  - From applications menu: Unified System Manager"
    if [[ $add_alias =~ ^[Yy]$ ]]; then
        echo "  - Using alias: usm (after restarting shell)"
    fi
}

# Show main menu
show_menu() {
    print_header
    echo "${GREEN}MAIN MENU${NC}"
    echo
    echo " ${CYAN}System Cleanup (TidyTux):${NC}"
    echo "  1. Run System Cleanup"
    echo "  2. Emergency Cleanup (Low Disk Space)"
    echo "  3. Schedule Automatic Cleanup"
    echo
    echo " ${CYAN}Cloud Backup (Google Drive):${NC}"
    echo "  4. Mount/Unmount Google Drive"
    echo "  5. Smart Backup Wizard"
    echo "  6. Sync Files"
    echo "  7. Configure Google Drive"
    echo
    echo " ${CYAN}System Management:${NC}"
    echo "  8. System Information & Status"
    echo "  9. Update System"
    echo " 10. Manage Applications"
    echo
    echo " ${CYAN}Advanced Options:${NC}"
    echo " 11. Launch GUI Interface"
    echo " 12. Configuration Settings"
    echo " 13. View Logs"
    echo " 14. About & Help"
    echo
    echo " ${RED}0. Exit${NC}"
    echo
}

# System cleanup menu
system_cleanup_menu() {
    while true; do
        clear
        print_header
        echo "${GREEN}SYSTEM CLEANUP MENU${NC}"
        echo
        echo "  1. Full System Cleanup"
        echo "  2. Clean Package Cache"
        echo "  3. Clean User Cache"
        echo "  4. Clean Browser Data"
        echo "  5. Remove Old Kernels"
        echo "  6. Find Duplicate Files"
        echo "  7. Organize Downloads"
        echo "  8. Docker Cleanup"
        echo "  9. Emergency Cleanup (Critical Space)"
        echo
        echo "  0. Back to Main Menu"
        echo
        
        read -p "Select option (0-9): " choice
        
        case $choice in
            1)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    "$TIDYTUX_SCRIPT"
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            2)
                print_status "Cleaning package cache..."
                sudo apt clean
                sudo apt autoclean
                print_success "Package cache cleaned"
                ;;
            3)
                print_status "Cleaning user cache..."
                rm -rf ~/.cache/thumbnails/*
                rm -rf ~/.cache/pip/*
                print_success "User cache cleaned"
                ;;
            4)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    # Call specific function from TidyTux
                    bash -c "source $TIDYTUX_SCRIPT && clean_browser_caches"
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            5)
                print_status "Removing old kernels..."
                sudo apt autoremove --purge
                print_success "Old kernels removed"
                ;;
            6)
                if command -v fdupes &> /dev/null; then
                    print_status "Finding duplicate files..."
                    fdupes -r "$HOME" | less
                else
                    print_error "fdupes not installed"
                fi
                ;;
            7)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    bash -c "source $TIDYTUX_SCRIPT && organize_downloads"
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            8)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    bash -c "source $TIDYTUX_SCRIPT && clean_docker"
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            9)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    "$TIDYTUX_SCRIPT" --emergency
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            0)
                return
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Google Drive menu
google_drive_menu() {
    while true; do
        clear
        print_header
        echo "${GREEN}GOOGLE DRIVE MENU${NC}"
        echo
        echo "  1. Mount/Unmount Google Drive"
        echo "  2. Smart Backup Wizard"
        echo "  3. Upload Files/Folders"
        echo "  4. Download Files/Folders"
        echo "  5. Sync Local to Drive"
        echo "  6. Sync Drive to Local"
        echo "  7. List Drive Contents"
        echo "  8. Configure Google Drive"
        echo "  9. Schedule Automatic Backup"
        echo
        echo "  0. Back to Main Menu"
        echo
        
        read -p "Select option (0-9): " choice
        
        case $choice in
            1)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    # Check mount status
                    if mountpoint -q "$GDRIVE_LOCAL_PATH" 2>/dev/null; then
                        "$GDRIVE_SCRIPT" unmount
                    else
                        "$GDRIVE_SCRIPT" mount
                    fi
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            2)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" smart-backup
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            3)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" upload
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            4)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" download
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            5)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" sync-to
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            6)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" sync-from
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            7)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" list
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            8)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" config
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            9)
                print_status "Setting up automatic backup..."
                # Add cron job for automatic backup
                cron_line="0 2 * * * $GDRIVE_SCRIPT auto-backup >> $LOG_DIR/gdrive-auto.log 2>&1"
                (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
                print_success "Automatic backup scheduled for 2:00 AM daily"
                ;;
            0)
                return
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# System information
show_system_info() {
    clear
    print_header
    echo "${GREEN}SYSTEM INFORMATION${NC}"
    echo
    
    # System info
    echo "${CYAN}System:${NC}"
    echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
    echo "  Kernel: $(uname -r)"
    echo "  Architecture: $(uname -m)"
    echo "  Hostname: $(hostname)"
    echo "  User: $(whoami)"
    echo
    
    # Disk usage
    echo "${CYAN}Disk Usage:${NC}"
    df -h | grep -E "^/dev/|Filesystem"
    echo
    
    # Memory usage
    echo "${CYAN}Memory Usage:${NC}"
    free -h
    echo
    
    # Component status
    echo "${CYAN}Component Status:${NC}"
    
    # TidyTux status
    if [ -f "$TIDYTUX_SCRIPT" ]; then
        echo "  TidyTux: ${GREEN}Installed${NC}"
    else
        echo "  TidyTux: ${RED}Not installed${NC}"
    fi
    
    # Google Drive status
    if [ -f "$GDRIVE_SCRIPT" ]; then
        echo "  Google Drive Manager: ${GREEN}Installed${NC}"
        if command -v rclone &> /dev/null; then
            if rclone listremotes | grep -q "^${RCLONE_REMOTE_NAME}:$"; then
                echo "  Google Drive: ${GREEN}Configured${NC}"
                if mountpoint -q "$GDRIVE_LOCAL_PATH" 2>/dev/null; then
                    echo "  Mount Status: ${GREEN}Mounted at $GDRIVE_LOCAL_PATH${NC}"
                else
                    echo "  Mount Status: ${YELLOW}Not mounted${NC}"
                fi
            else
                echo "  Google Drive: ${YELLOW}Not configured${NC}"
            fi
        fi
    else
        echo "  Google Drive Manager: ${RED}Not installed${NC}"
    fi
    
    # GUI status
    if [ -f "$GUI_SCRIPT" ]; then
        echo "  GUI Component: ${GREEN}Installed${NC}"
    else
        echo "  GUI Component: ${RED}Not installed${NC}"
    fi
    
    echo
    read -p "Press Enter to continue..."
}

# Launch GUI
launch_gui() {
    if [ ! -f "$GUI_SCRIPT" ]; then
        print_error "GUI component not found"
        read -p "Would you like to extract the GUI component? (y/n): " extract_gui
        if [[ $extract_gui =~ ^[Yy]$ ]]; then
            extract_components
        else
            return 1
        fi
    fi
    
    # Create a unified GUI launcher that integrates all components
    # For now, launch the Google Drive GUI
    print_status "Launching GUI interface..."
    python3 "$GUI_SCRIPT" &
}

# View logs
view_logs() {
    clear
    print_header
    echo "${GREEN}LOG VIEWER${NC}"
    echo
    echo "  1. View System Cleanup Logs"
    echo "  2. View Google Drive Logs"
    echo "  3. View All Logs"
    echo "  4. Clear Logs"
    echo
    echo "  0. Back to Main Menu"
    echo
    
    read -p "Select option (0-4): " choice
    
    case $choice in
        1)
            if [ -f "$LOG_DIR/tidytux_log.txt" ]; then
                less "$LOG_DIR/tidytux_log.txt"
            else
                print_warning "No cleanup logs found"
            fi
            ;;
        2)
            if [ -f "$LOG_DIR/gdrive-manager.log" ]; then
                less "$LOG_DIR/gdrive-manager.log"
            else
                print_warning "No Google Drive logs found"
            fi
            ;;
        3)
            if [ -d "$LOG_DIR" ]; then
                ls -la "$LOG_DIR"
                echo
                read -p "Enter log file name to view: " logfile
                if [ -f "$LOG_DIR/$logfile" ]; then
                    less "$LOG_DIR/$logfile"
                else
                    print_error "Log file not found"
                fi
            else
                print_warning "No log directory found"
            fi
            ;;
        4)
            read -p "Are you sure you want to clear all logs? (y/n): " clear_logs
            if [[ $clear_logs =~ ^[Yy]$ ]]; then
                rm -f "$LOG_DIR"/*
                print_success "Logs cleared"
            fi
            ;;
        0)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
}

# Show help
show_help() {
    clear
    print_header
    echo "${GREEN}HELP & DOCUMENTATION${NC}"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --setup       Run initial setup wizard"
    echo "  --gui         Launch GUI interface"
    echo "  --cleanup     Run system cleanup"
    echo "  --backup      Run Google Drive backup"
    echo "  --emergency   Run emergency cleanup (low disk space)"
    echo "  --status      Show system status"
    echo "  --help        Show this help message"
    echo "  --version     Show version information"
    echo
    echo "Features:"
    echo "  - System Cleanup: Remove unnecessary files, organize downloads, clean caches"
    echo "  - Google Drive Integration: Backup, sync, and manage cloud storage"
    echo "  - GUI Interface: User-friendly graphical interface"
    echo "  - Automation: Schedule regular cleanups and backups"
    echo "  - Emergency Mode: Quick cleanup when disk space is critical"
    echo
    echo "Components:"
    echo "  - TidyTux: Comprehensive system cleanup utility"
    echo "  - Google Drive Manager: rclone-based cloud storage management"
    echo "  - Unified GUI: Integrated graphical interface"
    echo
    echo "For more information, visit the documentation or use --help with specific commands"
    echo
    read -p "Press Enter to continue..."
}

# Main function
main() {
    # Initialize
    init_config
    
    # Parse command line arguments
    case "${1:-}" in
        --setup)
            quick_setup
            exit 0
            ;;
        --gui)
            launch_gui
            exit 0
            ;;
        --cleanup)
            if [ -f "$TIDYTUX_SCRIPT" ]; then
                "$TIDYTUX_SCRIPT" "${@:2}"
            else
                print_error "TidyTux component not found. Run --setup first."
                exit 1
            fi
            exit 0
            ;;
        --backup)
            if [ -f "$GDRIVE_SCRIPT" ]; then
                "$GDRIVE_SCRIPT" smart-backup
            else
                print_error "Google Drive Manager component not found. Run --setup first."
                exit 1
            fi
            exit 0
            ;;
        --emergency)
            if [ -f "$TIDYTUX_SCRIPT" ]; then
                "$TIDYTUX_SCRIPT" --emergency
            else
                print_error "TidyTux component not found. Run --setup first."
                exit 1
            fi
            exit 0
            ;;
        --status)
            show_system_info
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        --version)
            echo "$PROGRAM_NAME v$VERSION"
            exit 0
            ;;
    esac
    
    # Check if components are installed
    if [ ! -f "$TIDYTUX_SCRIPT" ] || [ ! -f "$GDRIVE_SCRIPT" ]; then
        print_warning "Some components are not installed."
        read -p "Would you like to run the setup wizard? (y/n): " run_setup
        if [[ $run_setup =~ ^[Yy]$ ]]; then
            quick_setup
            echo
        else
            print_error "Cannot proceed without required components"
            exit 1
        fi
    fi
    
    # Interactive menu loop
    while true; do
        clear
        show_menu
        read -p "Select option (0-14): " choice
        
        case $choice in
            1)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    "$TIDYTUX_SCRIPT"
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            2)
                if [ -f "$TIDYTUX_SCRIPT" ]; then
                    "$TIDYTUX_SCRIPT" --emergency
                else
                    print_error "TidyTux component not found"
                fi
                ;;
            3)
                print_status "Setting up automatic cleanup schedule..."
                # Add cron job
                cron_line="0 3 * * 0 $TIDYTUX_SCRIPT --quiet >> $LOG_DIR/tidytux-auto.log 2>&1"
                (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
                print_success "Weekly cleanup scheduled for Sunday 3:00 AM"
                ;;
            4)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    # Toggle mount
                    if mountpoint -q "$GDRIVE_LOCAL_PATH" 2>/dev/null; then
                        "$GDRIVE_SCRIPT" unmount
                    else
                        "$GDRIVE_SCRIPT" mount
                    fi
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            5)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" smart-backup
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            6)
                google_drive_menu
                ;;
            7)
                if [ -f "$GDRIVE_SCRIPT" ]; then
                    "$GDRIVE_SCRIPT" config
                else
                    print_error "Google Drive Manager component not found"
                fi
                ;;
            8)
                show_system_info
                ;;
            9)
                print_status "Updating system packages..."
                sudo apt update && sudo apt upgrade -y
                print_success "System updated"
                read -p "Press Enter to continue..."
                ;;
            10)
                system_cleanup_menu
                ;;
            11)
                launch_gui
                ;;
            12)
                ${EDITOR:-nano} "$CONFIG_FILE"
                init_config  # Reload configuration
                ;;
            13)
                view_logs
                ;;
            14)
                show_help
                ;;
            0)
                print_status "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please select 0-14."
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# Run main function
main "$@"