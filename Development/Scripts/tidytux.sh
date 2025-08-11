#!/bin/bash

# TidyTux - Comprehensive Linux System Cleanup Utility
# Version 1.2.1
# Created: March 2, 2025
# 
# Features:
#  - Low disk space detection and emergency cleanup
#  - File cleanup and organization
#  - System maintenance and updates
#  - Application cache cleanup
#  - Duplicate file detection
#  - Docker cleanup with permission handling
#  - Browser cache cleanup
#  - Performance monitoring
#  - Removable storage handling

VERSION="1.2.1"
PROGRAM_NAME="TidyTux"
PROGRAM_DESCRIPTION="Comprehensive Linux System Cleanup Utility"
GITHUB_REPO="https://github.com/username/tidytux"  # Placeholder

set -e  # Exit on error
set -u  # Exit on undefined variable

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

# Command line arguments
INTERACTIVE=true
SKIP_CONFIRMATION=false
VERBOSE=false
SCHEDULE=false
REPORT_ONLY=false
EMERGENCY_MODE=false

# Storage handling variables
REMOVABLE_DRIVES=()
UNAVAILABLE_PATHS=()

# Performance tracking
START_TIME=$(date +%s)
INITIAL_DISK_USAGE=$(df -h --output=used "$HOME" | tail -1 | tr -d ' ')
SPACE_SAVED=0

# Create a backup directory with timestamp
BACKUP_DIR="$HOME/.tidytux/backups/backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$BACKUP_DIR/tidytux_log.txt"

# Ensure backup directory exists right at the start
mkdir -p "$BACKUP_DIR"
# Function for logging
log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Make sure log directory exists before writing
    if [ ! -d "$(dirname "$LOG_FILE")" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
    fi
    
    if [ "$INTERACTIVE" = true ] || [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[$timestamp]${NC} $1"
    fi
    
    # Always write to log file regardless of interactive mode
    echo "[$timestamp] $1" | sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,3})*)?[mGK]//g" >> "$LOG_FILE" 
}

# Function for confirmation with improved timeout handling
confirm() {
    if [ "$SKIP_CONFIRMATION" = true ]; then
        return 0
    fi
    
    if [ "$EMERGENCY_MODE" = true ] && [[ "$1" == *"Would you like to"* ]]; then
        # In emergency mode, automatically say yes to cleanup questions
        echo -e "${YELLOW}$1 [Y/n] ${GREEN}(Auto-yes due to low disk space)${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}$1 [y/N]${NC}"
    # Longer timeout (120 seconds) with clearer message
    read -r -t 120 response || {
        echo -e "\n${RED}No response within 120 seconds, assuming no.${NC}"
        log "Confirmation timed out after 120 seconds, assuming no: $1"
        return 1
    }
    
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to detect removable storage - IMPROVED VERSION
detect_removable_storage() {
    log "Detecting mounted storage devices..."
    
    # Get list of mounted devices - only truly removable ones (not root filesystem)
    local mounted_devices
    
    # Better filtering for removable devices (USB drives, SD cards, etc.)
    # Looking for devices with removable flag 1 but excluding the root filesystem
    mounted_devices=$(lsblk -o NAME,MOUNTPOINT,RM,TYPE,SIZE | awk '$3 == 1 && $2 != "/" && $4 == "part" {print $2}')
    
    if [ -z "$mounted_devices" ]; then
        log "No removable storage detected"
        return
    fi
    
    # Store removable devices
    while read -r mount_point; do
        if [ -n "$mount_point" ] && [ "$mount_point" != "none" ] && [ "$mount_point" != "/" ]; then
            log "Found removable storage at: ${CYAN}$mount_point${NC}"
            REMOVABLE_DRIVES+=("$mount_point")
        fi
    done <<< "$mounted_devices"
    
    # Warn if files in Downloads point to removable media
    for drive in "${REMOVABLE_DRIVES[@]}"; do
        local symlinks
        symlinks=$(find "$HOME/Downloads" -type l -ls 2>/dev/null | grep "$drive" || echo "")
        
        if [ -n "$symlinks" ]; then
            log "${YELLOW}WARNING: Some files in Downloads link to removable storage at $drive${NC}"
            log "These links may become invalid if the device is disconnected"
        fi
    done
}
# Function to check if a path exists and is accessible
check_path_accessibility() {
    local path="$1"
    
    # If path doesn't exist, add to unavailable paths list
    if [ ! -e "$path" ]; then
        UNAVAILABLE_PATHS+=("$path")
        return 1
    fi
    
    # Check if path is on removable storage
    for drive in "${REMOVABLE_DRIVES[@]}"; do
        if [[ "$path" == "$drive"* ]]; then
            log "${YELLOW}WARNING: $path is on removable storage ($drive)${NC}"
            log "This path may become unavailable if the device is disconnected"
            return 0
        fi
    done
    
    return 0
}

# Function to safely handle file operations
safe_file_operation() {
    local operation="$1"
    local source="$2"
    local destination="${3:-}"  # Use parameter expansion to provide a default empty value    
    # Check if source exists
    if ! check_path_accessibility "$source"; then
        log "${RED}Cannot $operation '$source' - file/directory not found or inaccessible${NC}"
        return 1
    fi
    
    # If destination directory doesn't exist, create it
    if [ -n "$destination" ]; then
        local dest_dir
        dest_dir=$(dirname "$destination")
        if [ ! -d "$dest_dir" ]; then
            mkdir -p "$dest_dir"
        fi
    fi
    
    # Perform operation with proper quoting
    case "$operation" in
        "move")
            log "Moving '$source' to '$destination'..."
            mv "$source" "$destination"
            ;;
        "copy")
            log "Copying '$source' to '$destination'..."
            cp -r "$source" "$destination"
            ;;
        "remove")
            log "Removing '$source'..."
            rm -rf "$source"
            ;;
        "list")
            ls -la "$source" 2>/dev/null || log "${RED}Cannot list '$source'${NC}"
            ;;
        *)
            log "${RED}Unknown operation: $operation${NC}"
            return 1
            ;;
    esac
    
    return $?
}

# Function to show progress spinner with elapsed time
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    local start_time=$(date +%s)
    
    if [ "$INTERACTIVE" = false ]; then
        wait $pid
        return
    fi
    
    echo -n "  "
    while ps -p $pid > /dev/null; do
        local temp=${spinstr#?}
        local elapsed=$(($(date +%s) - start_time))
        local mins=$((elapsed / 60))
        local secs=$((elapsed % 60))
        printf "\b\b%s [%02d:%02d] " "${spinstr}" "$mins" "$secs"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    printf "\r                             \r"
}

# Function to record space saved
record_space_saved() {
    local path="$1"
    local before=$(du -s "$path" 2>/dev/null | cut -f1)
    
    # Run the command (second argument)
    shift
    "$@"
    
    local after=$(du -s "$path" 2>/dev/null | cut -f1)
    local saved=$((before - after))
    
    if [ $saved -gt 0 ]; then
        SPACE_SAVED=$((SPACE_SAVED + saved))
    fi
}
# Parse command-line options
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -q|--quiet)
                INTERACTIVE=false
                SKIP_CONFIRMATION=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -s|--schedule)
                SCHEDULE=true
                shift
                ;;
            -r|--report-only)
                REPORT_ONLY=true
                shift
                ;;
            -e|--emergency)
                EMERGENCY_MODE=true
                SKIP_CONFIRMATION=true
                shift
                ;;
            -c|--check)
                check_for_updates
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                echo -e "${GREEN}$PROGRAM_NAME${NC} version ${CYAN}$VERSION${NC}"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help information
show_help() {
    echo -e "${GREEN}$PROGRAM_NAME v$VERSION${NC} - $PROGRAM_DESCRIPTION"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -y, --yes         Skip all confirmations (assume yes)"
    echo "  -q, --quiet       Run in non-interactive mode (no output except errors)"
    echo "  -v, --verbose     Show verbose output"
    echo "  -e, --emergency   Run in emergency mode for low disk space (most aggressive cleaning)"
    echo "  -s, --schedule    Set up a scheduled cleanup task"
    echo "  -r, --report-only Only report issues, don't make changes"
    echo "  -c, --check       Check for updates"
    echo "  -h, --help        Show this help message"
    echo
    echo "Example: $0 --yes --verbose"
    echo "         $0 --emergency     # Use when disk space is critical"
    echo "         $0 --schedule"
}

# Check for updates
check_for_updates() {
    echo -e "${BLUE}Checking for updates...${NC}"
    echo -e "Current version: ${CYAN}$VERSION${NC}"
    
    # This is a placeholder for an actual update check
    echo -e "${YELLOW}Update check functionality is a placeholder.${NC}"
    echo -e "To check for updates, visit: $GITHUB_REPO"
}

# Create backup directory
create_backup_dir() {
    log "Creating backup directory at $BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"  # Secure permissions
    
    # Create version file in backup dir
    echo "$PROGRAM_NAME version $VERSION" > "$BACKUP_DIR/version.txt"
    echo "Backup created on $(date)" >> "$BACKUP_DIR/version.txt"
    echo "User: $(whoami)" >> "$BACKUP_DIR/version.txt"
    echo "Hostname: $(hostname)" >> "$BACKUP_DIR/version.txt"
    echo "System: $(uname -a)" >> "$BACKUP_DIR/version.txt"
}
# Install required tools if missing
install_required_tools() {
    local missing_tools=()
    
    # Check for essential tools
    for tool in ncdu fdupes bc; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        return 0
    fi
    
    log "Some recommended tools are missing: ${missing_tools[*]}"
    
    if confirm "Would you like to install missing tools (${missing_tools[*]})?"; then
        log "Installing missing tools..."
        sudo apt update
        for tool in "${missing_tools[@]}"; do
            log "Installing $tool..."
            sudo apt install -y "$tool"
            if [ $? -eq 0 ]; then
                log "${GREEN}$tool installed successfully${NC}"
            else
                log "${RED}Failed to install $tool${NC}"
            fi
        done
    else
        log "Skipping tool installation. Some features may be limited."
    fi
}

# Check disk space (now with detailed reporting and emergency cleanup)
check_disk_space() {
    log "${BOLD}====== DISK SPACE CHECK ======${NC}"
    log "Checking disk space..."
    
    # Get disk information
    DISK_INFO=$(df -h "$HOME")
    DISK_DEVICE=$(echo "$DISK_INFO" | grep -v "Filesystem" | awk '{print $1}')
    DISK_SIZE=$(echo "$DISK_INFO" | grep -v "Filesystem" | awk '{print $2}')
    DISK_USED=$(echo "$DISK_INFO" | grep -v "Filesystem" | awk '{print $3}')
    DISK_AVAIL=$(echo "$DISK_INFO" | grep -v "Filesystem" | awk '{print $4}')
    DISK_PERCENT=$(echo "$DISK_INFO" | grep -v "Filesystem" | awk '{print $5}')
    
    log "Disk summary for $HOME:"
    log "  Device:     ${CYAN}$DISK_DEVICE${NC}"
    log "  Total size: ${CYAN}$DISK_SIZE${NC}"
    log "  Used:       ${CYAN}$DISK_USED${NC} ($DISK_PERCENT)"
    log "  Available:  ${CYAN}$DISK_AVAIL${NC}"
    
    echo "$DISK_INFO" | grep -v "Filesystem" | tee -a "$LOG_FILE"
    
    # Check if disk space is critically low (under threshold)
    AVAILABLE_KB=$(df -k --output=avail "$HOME" | tail -1)
    
    # Set thresholds: critical is 1GB, warning is 5GB
    CRITICAL_THRESHOLD=$((1024 * 1024))  # 1GB in KB
    WARNING_THRESHOLD=$((5 * 1024 * 1024))  # 5GB in KB
    
    if [ "$AVAILABLE_KB" -lt "$CRITICAL_THRESHOLD" ]; then
        log "${RED}CRITICAL: Very low disk space (less than 1GB available)${NC}"
        log "Enabling emergency mode for aggressive cleanup"
        EMERGENCY_MODE=true
        
        if confirm "Would you like to run emergency cleanup immediately to free up space?"; then
            log "Running emergency cleanup..."
            
            # Clear package cache
            sudo apt clean
            
            # Clean journals
            if command -v journalctl &> /dev/null; then
                sudo journalctl --vacuum-time=1d
            fi
            
            # Clear thumbnail cache
            rm -rf ~/.cache/thumbnails/* 2>/dev/null || true
            
            # Clear browser caches
            if [ -d "$HOME/.cache/google-chrome" ]; then
                rm -rf "$HOME/.cache/google-chrome"/* 2>/dev/null || true
            fi
            if [ -d "$HOME/.cache/mozilla" ]; then
                rm -rf "$HOME/.cache/mozilla"/* 2>/dev/null || true
            fi
            
            # Clean /tmp
            find /tmp -type f -atime +1 -delete 2>/dev/null || true
            
            log "${GREEN}Emergency cleanup completed${NC}"
            
            # Check space again
            NEW_AVAILABLE_KB=$(df -k --output=avail "$HOME" | tail -1)
            FREED_KB=$((NEW_AVAILABLE_KB - AVAILABLE_KB))
            FREED_MB=$((FREED_KB / 1024))
            
            log "Freed approximately ${CYAN}${FREED_MB}MB${NC} of disk space"
            
            if [ "$NEW_AVAILABLE_KB" -lt "$CRITICAL_THRESHOLD" ]; then
                log "${YELLOW}Disk space is still critically low. Continuing with full cleanup...${NC}"
            else
                log "${GREEN}Disk space increased to $(df -h --output=avail "$HOME" | tail -1 | tr -d ' ')${NC}"
            fi
        fi
    elif [ "$AVAILABLE_KB" -lt "$WARNING_THRESHOLD" ]; then
        log "${YELLOW}WARNING: Low disk space (less than 5GB available)${NC}"
        log "Some cleanup operations may need to be more aggressive"
        
        if confirm "Would you like to enable emergency mode for more aggressive cleaning?"; then
            EMERGENCY_MODE=true
            log "Emergency mode enabled"
        fi
    fi
    
    # Install ncdu if not already installed
    if ! command -v ncdu &> /dev/null; then
        if confirm "ncdu (disk usage analyzer) is not installed. Would you like to install it?"; then
            log "Installing ncdu..."
            sudo apt update && sudo apt install -y ncdu
        fi
    fi
}
# System updates function
update_system() {
    log "${BOLD}====== SYSTEM UPDATES ======${NC}"
    
    # Check for available updates
    log "Checking for available system updates..."
    sudo apt update
    
    # Count number of upgradable packages
    UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -c upgradable || echo "0")
    
    if [ "$UPGRADABLE" -eq "0" ]; then
        log "${GREEN}System is up to date. No packages need upgrading.${NC}"
        return
    fi
    
    log "Found ${CYAN}$UPGRADABLE${NC} packages that can be upgraded"
    
    if [ "$EMERGENCY_MODE" = true ]; then
        log "${YELLOW}Skipping system upgrades in emergency mode to save space${NC}"
        return
    fi
    
    if confirm "Would you like to upgrade these packages?"; then
        log "Upgrading packages... (this may take a while)"
        sudo apt upgrade -y
        log "${GREEN}System packages upgraded successfully${NC}"
        
        if confirm "Would you like to remove unnecessary packages (autoremove)?"; then
            log "Removing unnecessary packages..."
            sudo apt autoremove -y
            log "${GREEN}Unnecessary packages removed${NC}"
        fi
    else
        log "Skipping system upgrades"
    fi
}

# Clean installation packages
clean_deb_files() {
    log "${BOLD}====== INSTALLATION PACKAGES ======${NC}"
    log "Looking for .deb installation packages..."
    
    # Find .deb files in home directory and Downloads
    DEB_FILES=$(find "$HOME" -maxdepth 3 -name "*.deb" -type f 2>/dev/null || echo "")
    
    if [ -z "$DEB_FILES" ]; then
        log "No .deb files found in home directory"
        return
    fi
    
    # Calculate total size safely
    local total_size_kb=0
    local file_count=0
    
    while IFS= read -r file; do
        # Skip empty lines
        [ -z "$file" ] && continue
        
        # Check accessibility
        if check_path_accessibility "$file"; then
            size_kb=$(du -k "$file" | cut -f1)
            total_size_kb=$((total_size_kb + size_kb))
            file_count=$((file_count + 1))
        fi
    done <<< "$DEB_FILES"
    
    # Convert KB to MB for display
    local total_size_mb=$((total_size_kb / 1024))
    
    log "Found $file_count .deb files taking up ${CYAN}${total_size_mb}MB${NC} of space:"
    echo "$DEB_FILES" | tee -a "$LOG_FILE"
    
    if confirm "Would you like to move these .deb files to the backup directory?"; then
        mkdir -p "$BACKUP_DIR/deb_files"
        local moved_count=0
        local moved_size=0
        
        while IFS= read -r file; do
            # Skip empty lines
            [ -z "$file" ] && continue
            
            # Get just the filename for the destination
            local file_name
            file_name=$(basename "$file")
            local backup_dest="$BACKUP_DIR/deb_files/$file_name"
            
            # Move the file safely
            if safe_file_operation "move" "$file" "$backup_dest"; then
                size_kb=$(du -k "$backup_dest" | cut -f1)
                moved_size=$((moved_size + size_kb))
                moved_count=$((moved_count + 1))
            fi
        done <<< "$DEB_FILES"
        
        # Convert KB to MB for display
        local moved_size_mb=$((moved_size / 1024))
        log "${GREEN}Moved $moved_count .deb files (${moved_size_mb}MB) to $BACKUP_DIR/deb_files/${NC}"
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + moved_size))
    fi
}
# Organize Downloads folder with improved error handling
organize_downloads() {
    log "${BOLD}====== DOWNLOADS FOLDER ======${NC}"
    DOWNLOADS="$HOME/Downloads"
    
    if [ ! -d "$DOWNLOADS" ]; then
        log "${YELLOW}Downloads directory not found${NC}"
        return
    fi
    
    # Check size before organizing
    if check_path_accessibility "$DOWNLOADS"; then
        DOWNLOADS_SIZE=$(du -sh "$DOWNLOADS" | cut -f1)
        log "Downloads folder size: ${CYAN}$DOWNLOADS_SIZE${NC}"
    else
        log "${RED}Cannot access Downloads folder${NC}"
        return
    fi
    
    # Count files by type safely
    PDF_COUNT=$(find "$DOWNLOADS" -maxdepth 2 -name "*.pdf" 2>/dev/null | wc -l)
    DOC_COUNT=$(find "$DOWNLOADS" -maxdepth 2 -name "*.doc*" 2>/dev/null | wc -l)
    ZIP_COUNT=$(find "$DOWNLOADS" -maxdepth 2 -name "*.zip" 2>/dev/null | wc -l)
    TAR_COUNT=$(find "$DOWNLOADS" -maxdepth 2 -name "*.tar*" 2>/dev/null | wc -l)
    DEB_COUNT=$(find "$DOWNLOADS" -maxdepth 2 -name "*.deb" 2>/dev/null | wc -l)
    IMG_COUNT=$(find "$DOWNLOADS" -maxdepth 2 \( -name "*.jp*g" -o -name "*.png" \) 2>/dev/null | wc -l)
    
    log "Downloads content summary:"
    log "  PDF files:      ${CYAN}$PDF_COUNT${NC}"
    log "  Document files: ${CYAN}$DOC_COUNT${NC}"
    log "  Archives:       ${CYAN}$((ZIP_COUNT + TAR_COUNT))${NC}"
    log "  Packages:       ${CYAN}$DEB_COUNT${NC}"
    log "  Images:         ${CYAN}$IMG_COUNT${NC}"
    
    log "Organizing Downloads folder..."
    
    # Create category directories
    mkdir -p "$DOWNLOADS/documents" 2>/dev/null || true
    mkdir -p "$DOWNLOADS/archives" 2>/dev/null || true
    mkdir -p "$DOWNLOADS/software" 2>/dev/null || true
    mkdir -p "$DOWNLOADS/images" 2>/dev/null || true
    mkdir -p "$DOWNLOADS/scripts" 2>/dev/null || true
    mkdir -p "$DOWNLOADS/other" 2>/dev/null || true
    
    # Move files by extension
    if confirm "Would you like to organize your Downloads folder by file type?"; then
        # Documents
        DOCS_MOVED=0
        DOCS_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f \( -name "*.pdf" -o -name "*.doc" -o -name "*.docx" -o -name "*.txt" -o -name "*.odt" -o -name "*.rtf" -o -name "*.qbo" -o -name "*.csv" \) 2>/dev/null || echo "")
        if [ -n "$DOCS_FOUND" ]; then
            while IFS= read -r doc; do
                [ -z "$doc" ] && continue
                if safe_file_operation "move" "$doc" "$DOWNLOADS/documents/$(basename "$doc")"; then
                    DOCS_MOVED=$((DOCS_MOVED + 1))
                fi
            done <<< "$DOCS_FOUND"
            log "Moved ${CYAN}$DOCS_MOVED${NC} document files to documents folder"
        fi
        
        # Archives
        ARCHIVES_MOVED=0
        ARCHIVES_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f \( -name "*.zip" -o -name "*.tar.gz" -o -name "*.tar" -o -name "*.gz" -o -name "*.bz2" -o -name "*.xz" -o -name "*.rar" \) 2>/dev/null || echo "")
        if [ -n "$ARCHIVES_FOUND" ]; then
            while IFS= read -r archive; do
                [ -z "$archive" ] && continue
                if safe_file_operation "move" "$archive" "$DOWNLOADS/archives/$(basename "$archive")"; then
                    ARCHIVES_MOVED=$((ARCHIVES_MOVED + 1))
                fi
            done <<< "$ARCHIVES_FOUND"
            log "Moved ${CYAN}$ARCHIVES_MOVED${NC} archive files to archives folder"
        fi
        
        # Software
        SOFTWARE_MOVED=0
        SOFTWARE_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" -o -name "*.exe" -o -name "*.msi" -o -name "*.dmg" \) 2>/dev/null || echo "")
        if [ -n "$SOFTWARE_FOUND" ]; then
            while IFS= read -r software; do
                [ -z "$software" ] && continue
                if safe_file_operation "move" "$software" "$DOWNLOADS/software/$(basename "$software")"; then
                    SOFTWARE_MOVED=$((SOFTWARE_MOVED + 1))
                fi
            done <<< "$SOFTWARE_FOUND"
            log "Moved ${CYAN}$SOFTWARE_MOVED${NC} software files to software folder"
        fi
# Images
        IMAGES_MOVED=0
        IMAGES_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.svg" -o -name "*.bmp" \) 2>/dev/null || echo "")
        if [ -n "$IMAGES_FOUND" ]; then
            while IFS= read -r image; do
                [ -z "$image" ] && continue
                if safe_file_operation "move" "$image" "$DOWNLOADS/images/$(basename "$image")"; then
                    IMAGES_MOVED=$((IMAGES_MOVED + 1))
                fi
            done <<< "$IMAGES_FOUND"
            log "Moved ${CYAN}$IMAGES_MOVED${NC} image files to images folder"
        fi
        
        # Scripts
        SCRIPTS_MOVED=0
        SCRIPTS_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.py" -o -name "*.pl" -o -name "*.rb" -o -name "*.js" -o -name "*.md" \) 2>/dev/null || echo "")
        if [ -n "$SCRIPTS_FOUND" ]; then
            while IFS= read -r script; do
                [ -z "$script" ] && continue
                if safe_file_operation "move" "$script" "$DOWNLOADS/scripts/$(basename "$script")"; then
                    SCRIPTS_MOVED=$((SCRIPTS_MOVED + 1))
                fi
            done <<< "$SCRIPTS_FOUND"
            log "Moved ${CYAN}$SCRIPTS_MOVED${NC} script files to scripts folder"
        fi
        
        # Move everything else to other
        OTHER_MOVED=0
        OTHER_FOUND=$(find "$DOWNLOADS" -maxdepth 1 -type f -not -path "*/\.*" 2>/dev/null || echo "")
        if [ -n "$OTHER_FOUND" ]; then
            while IFS= read -r other; do
                [ -z "$other" ] && continue
                if safe_file_operation "move" "$other" "$DOWNLOADS/other/$(basename "$other")"; then
                    OTHER_MOVED=$((OTHER_MOVED + 1))
                fi
            done <<< "$OTHER_FOUND"
            log "Moved ${CYAN}$OTHER_MOVED${NC} other files to other folder"
        fi
        
        TOTAL_MOVED=$((DOCS_MOVED + ARCHIVES_MOVED + SOFTWARE_MOVED + IMAGES_MOVED + SCRIPTS_MOVED + OTHER_MOVED))
        log "${GREEN}Downloads folder organized with $TOTAL_MOVED files sorted${NC}"
    fi
    
    # Special handling for financial documents
    if confirm "Would you like to move financial documents to your Documents folder?"; then
        FINANCE_DIR="$HOME/Documents/Financial"
        mkdir -p "$FINANCE_DIR"
        
        # Look for likely financial documents
        FINANCE_DOCS=$(find "$DOWNLOADS/documents" "$DOWNLOADS/other" -type f 2>/dev/null | grep -E '(statement|tax|W2|1099|1120|8949|Schedule|Form|transaction|qbo|budget)' || echo "")
        
        if [ -n "$FINANCE_DOCS" ]; then
            FINANCE_COUNT=0
            while IFS= read -r doc; do
                [ -z "$doc" ] && continue
                if safe_file_operation "move" "$doc" "$FINANCE_DIR/$(basename "$doc")"; then
                    FINANCE_COUNT=$((FINANCE_COUNT + 1))
                fi
            done <<< "$FINANCE_DOCS"
            log "${GREEN}$FINANCE_COUNT financial documents moved to $FINANCE_DIR${NC}"
        else
            log "No obvious financial documents found"
        fi
    fi
}
# Handle duplicate scripts with better handling for spaces in filenames
clean_duplicate_scripts() {
    log "${BOLD}====== DUPLICATE SCRIPTS ======${NC}"
    log "Looking for duplicate scripts..."
    
    # Handle duplicate Ethereum node setup scripts
    handle_duplicate_scripts "production-ready-ethereum-node-setup-script*.sh" "ethereum node setup"
    
    # Handle duplicate server setup scripts
    handle_duplicate_scripts "server-setup-script*.sh" "server setup"
}

# Function to handle duplicate scripts of a specific pattern
handle_duplicate_scripts() {
    local pattern="$1"
    local script_type="$2"
    
    # Find scripts matching pattern
    local SCRIPTS
    SCRIPTS=$(find "$HOME" -name "$pattern" 2>/dev/null || echo "")
    
    if [ -z "$SCRIPTS" ]; then
        log "No $script_type scripts found"
        return
    fi
    
    # Count lines properly with wc -l
    local SCRIPT_COUNT
    SCRIPT_COUNT=$(echo "$SCRIPTS" | wc -l)
    log "Found $SCRIPT_COUNT $script_type scripts:"
    echo "$SCRIPTS" | tee -a "$LOG_FILE"
    
    if confirm "Would you like to keep only the latest version?"; then
        mkdir -p "$BACKUP_DIR/scripts"
        
        # Find the most recently modified script
        local latest_timestamp=0
        local latest_script=""
        
        while IFS= read -r script_path; do
            # Skip empty lines
            [ -z "$script_path" ] && continue
            
            # Check if file exists and is accessible
            if ! check_path_accessibility "$script_path"; then
                log "${YELLOW}Skipping inaccessible script: $script_path${NC}"
                continue
            fi
            
            # Get timestamp
            local timestamp
            timestamp=$(stat -c %Y "$script_path" 2>/dev/null || echo "0")
            
            # Update latest if needed
            if (( timestamp > latest_timestamp )); then
                latest_timestamp=$timestamp
                latest_script="$script_path"
            fi
        done <<< "$SCRIPTS"
        
        if [ -n "$latest_script" ]; then
            log "Latest script: $latest_script"
            
            local MOVED_COUNT=0
            while IFS= read -r script_path; do
                # Skip empty lines
                [ -z "$script_path" ] && continue
                
                # Skip latest script
                if [ "$script_path" = "$latest_script" ]; then
                    continue
                fi
                
                # Get just the filename for the destination
                local script_name
                script_name=$(basename "$script_path")
                local backup_dest="$BACKUP_DIR/scripts/$script_name"
                
                # Move the file safely
                if safe_file_operation "move" "$script_path" "$backup_dest"; then
                    MOVED_COUNT=$((MOVED_COUNT + 1))
                fi
            done <<< "$SCRIPTS"
            
            log "${GREEN}Kept latest script: $latest_script${NC}"
            log "${GREEN}Moved $MOVED_COUNT duplicate scripts to backup${NC}"
        else
            log "${YELLOW}Could not determine latest script, no files moved${NC}"
        fi
    fi
}
# Clean snap packages
clean_snap_packages() {
    log "${BOLD}====== SNAP PACKAGES ======${NC}"
    
    if ! command -v snap &> /dev/null; then
        log "${YELLOW}snap not installed, skipping snap cleanup${NC}"
        return
    fi
    
    log "Checking for old snap revisions..."
    
    # Get snap disk usage before cleanup
    SNAP_USAGE_BEFORE=$(df -h /var/lib/snapd/snaps 2>/dev/null | grep -v "Filesystem" | awk '{print $3}' || echo "Unknown")
    log "Current snap storage usage: ${CYAN}$SNAP_USAGE_BEFORE${NC}"
    
    # List all disabled snap packages
    DISABLED_SNAPS=$(snap list --all 2>/dev/null | grep disabled || echo "")
    
    if [ -z "$DISABLED_SNAPS" ]; then
        log "No disabled snap revisions found"
        return
    fi
    
    DISABLED_COUNT=$(echo "$DISABLED_SNAPS" | wc -l)
    log "Found ${CYAN}$DISABLED_COUNT${NC} disabled snap revisions:"
    echo "$DISABLED_SNAPS" | tee -a "$LOG_FILE"
    
    if confirm "Would you like to remove old snap revisions?"; then
        log "Setting snap retention policy to 2 revisions..."
        sudo snap set system refresh.retain=2
        
        log "Removing old snap revisions..."
        REMOVED_COUNT=0
        
        # Extract and process revisions more reliably
        while IFS= read -r line; do
            if [[ "$line" == *"disabled"* ]]; then
                SNAPNAME=$(echo "$line" | awk '{print $1}')
                REVISION=$(echo "$line" | awk '{print $3}')
                
                if [ -n "$SNAPNAME" ] && [ -n "$REVISION" ]; then
                    log "Removing $SNAPNAME revision $REVISION..."
                    sudo snap remove "$SNAPNAME" --revision="$REVISION" && REMOVED_COUNT=$((REMOVED_COUNT + 1)) || log "${RED}Failed to remove $SNAPNAME revision $REVISION${NC}"
                fi
            fi
        done <<< "$DISABLED_SNAPS"
        
        # Get snap disk usage after cleanup
        SNAP_USAGE_AFTER=$(df -h /var/lib/snapd/snaps 2>/dev/null | grep -v "Filesystem" | awk '{print $3}' || echo "Unknown")
        
        log "${GREEN}$REMOVED_COUNT old snap revisions removed${NC}"
        log "Snap storage usage reduced from ${CYAN}$SNAP_USAGE_BEFORE${NC} to ${CYAN}$SNAP_USAGE_AFTER${NC}"
    fi
}

# Clean browser caches - PATCHED VERSION WITH FIREFOX FIX
clean_browser_caches() {
    log "${BOLD}====== BROWSER CACHES ======${NC}"
    log "Checking browser caches..."
    
    # Initialize cache variables
    CHROME_CACHE="$HOME/.cache/google-chrome"
    CHROMIUM_CACHE="$HOME/.cache/chromium"
    BRAVE_CACHE="$HOME/.config/BraveSoftware/Brave-Browser/Default/Cache"
    FIREFOX_CACHE="$HOME/.mozilla/firefox"
    FIREFOX_PROFILE=""
    FIREFOX_CACHE_DIR=""  # Initialize this to empty
    
    # Calculate total cache size
    CACHE_SIZE=0
    
    if [ -d "$CHROME_CACHE" ]; then
        CHROME_SIZE=$(du -sh "$CHROME_CACHE" 2>/dev/null | cut -f1 || echo "0")
        log "Chrome cache: ${CYAN}$CHROME_SIZE${NC}"
        CHROME_KB=$(du -sk "$CHROME_CACHE" 2>/dev/null | cut -f1 || echo "0")
        CACHE_SIZE=$((CACHE_SIZE + CHROME_KB))
    fi
if [ -d "$CHROMIUM_CACHE" ]; then
        CHROMIUM_SIZE=$(du -sh "$CHROMIUM_CACHE" 2>/dev/null | cut -f1 || echo "0")
        log "Chromium cache: ${CYAN}$CHROMIUM_SIZE${NC}"
        CHROMIUM_KB=$(du -sk "$CHROMIUM_CACHE" 2>/dev/null | cut -f1 || echo "0")
        CACHE_SIZE=$((CACHE_SIZE + CHROMIUM_KB))
    fi
    
    if [ -d "$BRAVE_CACHE" ]; then
        BRAVE_SIZE=$(du -sh "$BRAVE_CACHE" 2>/dev/null | cut -f1 || echo "0")
        log "Brave cache: ${CYAN}$BRAVE_SIZE${NC}"
        BRAVE_KB=$(du -sk "$BRAVE_CACHE" 2>/dev/null | cut -f1 || echo "0")
        CACHE_SIZE=$((CACHE_SIZE + BRAVE_KB))
    fi
    
    # Fixed Firefox cache handling
    if [ -d "$FIREFOX_CACHE" ]; then
        FIREFOX_PROFILE=$(find "$FIREFOX_CACHE" -name "*.default*" -type d 2>/dev/null | head -1 || echo "")
        if [ -n "$FIREFOX_PROFILE" ]; then
            FIREFOX_CACHE_DIR="$FIREFOX_PROFILE/Cache"
            if [ -d "$FIREFOX_CACHE_DIR" ]; then
                FIREFOX_SIZE=$(du -sh "$FIREFOX_CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
                log "Firefox cache: ${CYAN}$FIREFOX_SIZE${NC}"
                FIREFOX_KB=$(du -sk "$FIREFOX_CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
                CACHE_SIZE=$((CACHE_SIZE + FIREFOX_KB))
            fi
        fi
    fi
    
    CACHE_SIZE_MB=$((CACHE_SIZE / 1024))
    log "Total browser cache size: ${CYAN}${CACHE_SIZE_MB}MB${NC}"
    
    if [ "$CACHE_SIZE" -eq 0 ]; then
        log "No browser caches found"
        return
    fi
    
    if confirm "Would you like to clean browser caches?"; then
        # Close browsers first
        log "Checking for running browsers..."
        BROWSERS_RUNNING=false
        
        for browser in chrome chromium brave firefox; do
            if pgrep -x "$browser" > /dev/null; then
                log "${YELLOW}$browser is running and should be closed before cleaning cache${NC}"
                BROWSERS_RUNNING=true
            fi
        done
        
        if [ "$BROWSERS_RUNNING" = true ]; then
            if ! confirm "Browsers are still running. Continue anyway?"; then
                log "Skipping browser cache cleanup"
                return
            fi
        fi
        
        # Clean Chrome cache
        if [ -d "$CHROME_CACHE" ] && check_path_accessibility "$CHROME_CACHE"; then
            log "Cleaning Chrome cache..."
            rm -rf "$CHROME_CACHE"/* 2>/dev/null || log "${RED}Failed to clean Chrome cache${NC}"
        fi
        
        # Clean Chromium cache
        if [ -d "$CHROMIUM_CACHE" ] && check_path_accessibility "$CHROMIUM_CACHE"; then
            log "Cleaning Chromium cache..."
            rm -rf "$CHROMIUM_CACHE"/* 2>/dev/null || log "${RED}Failed to clean Chromium cache${NC}"
        fi
        
        # Clean Brave cache
        if [ -d "$BRAVE_CACHE" ] && check_path_accessibility "$BRAVE_CACHE"; then
            log "Cleaning Brave cache..."
            rm -rf "$BRAVE_CACHE"/* 2>/dev/null || log "${RED}Failed to clean Brave cache${NC}"
        fi
        
        # Clean Firefox cache - fixed to check if directory exists
        if [ -n "$FIREFOX_CACHE_DIR" ] && [ -d "$FIREFOX_CACHE_DIR" ] && check_path_accessibility "$FIREFOX_CACHE_DIR"; then
            log "Cleaning Firefox cache..."
            rm -rf "$FIREFOX_CACHE_DIR"/* 2>/dev/null || log "${RED}Failed to clean Firefox cache${NC}"
        fi
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + CACHE_SIZE))
        
        log "${GREEN}Browser caches cleaned (${CACHE_SIZE_MB}MB)${NC}"
    fi
}
# Additional features and improvements

# Add function to clean snap application caches
clean_snap_app_caches() {
    log "${BOLD}====== SNAP APPLICATION CACHES ======${NC}"
    
    if ! command -v snap &> /dev/null; then
        log "${YELLOW}snap not installed, skipping snap application cache cleanup${NC}"
        return
    fi
    
    log "Checking for snap application caches..."
    
    # Look for snap-specific cache directories
    SNAP_CACHE_DIRS=$(find "$HOME/snap" -path "*/*/cache" -type d 2>/dev/null || echo "")
    
    if [ -z "$SNAP_CACHE_DIRS" ]; then
        log "No snap application cache directories found"
        return
    fi
    
    # Calculate total size
    TOTAL_SIZE_KB=0
    CACHE_DIR_COUNT=0
    
    while IFS= read -r cache_dir; do
        # Skip empty lines
        [ -z "$cache_dir" ] && continue
        
        # Check accessibility
        if check_path_accessibility "$cache_dir"; then
            CACHE_SIZE_KB=$(du -sk "$cache_dir" 2>/dev/null | cut -f1 || echo "0")
            TOTAL_SIZE_KB=$((TOTAL_SIZE_KB + CACHE_SIZE_KB))
            CACHE_DIR_COUNT=$((CACHE_DIR_COUNT + 1))
        fi
    done <<< "$SNAP_CACHE_DIRS"
    
    TOTAL_SIZE_MB=$((TOTAL_SIZE_KB / 1024))
    
    log "Found ${CYAN}$CACHE_DIR_COUNT${NC} snap application cache directories using ${CYAN}${TOTAL_SIZE_MB}MB${NC}"
    
    if [ "$TOTAL_SIZE_KB" -eq 0 ]; then
        return
    fi
    
    if confirm "Would you like to clean snap application caches?"; then
        CLEARED_COUNT=0
        
        while IFS= read -r cache_dir; do
            # Skip empty lines
            [ -z "$cache_dir" ] && continue
            
            # Get app name from path
            APP_NAME=$(echo "$cache_dir" | grep -oP 'snap/\K[^/]+' || echo "unknown")
            
            log "Cleaning cache for $APP_NAME..."
            if check_path_accessibility "$cache_dir"; then
                # Clean cache but preserve directory structure
                find "$cache_dir" -type f -delete 2>/dev/null
                CLEARED_COUNT=$((CLEARED_COUNT + 1))
            fi
        done <<< "$SNAP_CACHE_DIRS"
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + TOTAL_SIZE_KB))
        
        log "${GREEN}Cleaned $CLEARED_COUNT snap application caches (${TOTAL_SIZE_MB}MB)${NC}"
    fi
}

# Add function to clean old log files
clean_log_files() {
    log "${BOLD}====== LOG FILES CLEANUP ======${NC}"
    log "Checking for old log files..."
    
    # Define log file patterns to search for
    LOG_PATHS=(
        "$HOME/.xsession-errors*"
        "$HOME/.local/share/xorg/Xorg.*.log*"
        "$HOME/*.log"
        "$HOME/.cache/upstart/*.log"
    )
    
    # Find log files older than 7 days (or 2 days in emergency mode)
    LOG_DAYS=7
    if [ "$EMERGENCY_MODE" = true ]; then
        LOG_DAYS=2
    fi
# Build find command for all log paths
    LOG_FILES=""
    for path in "${LOG_PATHS[@]}"; do
        if [ -n "$LOG_FILES" ]; then
            LOG_FILES="$LOG_FILES"$'\n'
        fi
        LOG_FILES="$LOG_FILES$(find $path -type f -mtime +$LOG_DAYS 2>/dev/null || echo "")"
    done
    
    if [ -z "$LOG_FILES" ]; then
        log "No old log files found"
        return
    fi
    
    # Calculate total size
    TOTAL_SIZE_KB=0
    FILE_COUNT=0
    
    while IFS= read -r log_file; do
        # Skip empty lines
        [ -z "$log_file" ] && continue
        
        # Check accessibility
        if check_path_accessibility "$log_file"; then
            SIZE_KB=$(du -k "$log_file" 2>/dev/null | cut -f1 || echo "0")
            TOTAL_SIZE_KB=$((TOTAL_SIZE_KB + SIZE_KB))
            FILE_COUNT=$((FILE_COUNT + 1))
        fi
    done <<< "$LOG_FILES"
    
    TOTAL_SIZE_MB=$((TOTAL_SIZE_KB / 1024))
    
    log "Found ${CYAN}$FILE_COUNT${NC} old log files using ${CYAN}${TOTAL_SIZE_MB}MB${NC}"
    
    if confirm "Would you like to remove old log files?"; then
        REMOVED_COUNT=0
        
        while IFS= read -r log_file; do
            # Skip empty lines
            [ -z "$log_file" ] && continue
            
            if safe_file_operation "remove" "$log_file"; then
                REMOVED_COUNT=$((REMOVED_COUNT + 1))
            fi
        done <<< "$LOG_FILES"
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + TOTAL_SIZE_KB))
        
        log "${GREEN}Removed $REMOVED_COUNT old log files (${TOTAL_SIZE_MB}MB)${NC}"
    fi
}

# Add function to clean old crash reports and core dumps
clean_crash_reports() {
    log "${BOLD}====== CRASH REPORTS ======${NC}"
    log "Checking for crash reports and core dumps..."
    
    # Check for apport crash reports
    CRASH_DIRS=(
        "/var/crash"
        "$HOME/.cache/abrt"
        "$HOME/.local/share/apport"
        "/var/lib/systemd/coredump"
    )
    
    CRASH_FILES=""
    for dir in "${CRASH_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            if [ -n "$CRASH_FILES" ]; then
                CRASH_FILES="$CRASH_FILES"$'\n'
            fi
            CRASH_FILES="$CRASH_FILES$(find "$dir" -type f 2>/dev/null || echo "")"
        fi
    done
    
    # Also find core dump files
    CORE_DUMPS=$(find "$HOME" -name "core" -o -name "core.*" -type f 2>/dev/null || echo "")
    if [ -n "$CORE_DUMPS" ]; then
        if [ -n "$CRASH_FILES" ]; then
            CRASH_FILES="$CRASH_FILES"$'\n'
        fi
        CRASH_FILES="$CRASH_FILES$CORE_DUMPS"
    fi
    
    if [ -z "$CRASH_FILES" ]; then
        log "No crash reports or core dumps found"
        return
    fi
# Calculate total size more safely
TOTAL_SIZE_KB=0
FILE_COUNT=0

# Create a temporary file to store sizes
TEMP_SIZE_FILE="$BACKUP_DIR/crash_sizes.txt"
touch "$TEMP_SIZE_FILE"

while IFS= read -r crash_file; do
    # Skip empty lines
    [ -z "$crash_file" ] && continue
    
    # Check if file exists and is readable
    if [ -r "$crash_file" ]; then
        # Append size to temp file instead of adding directly
        du -k "$crash_file" 2>/dev/null >> "$TEMP_SIZE_FILE"
        FILE_COUNT=$((FILE_COUNT + 1))
    fi
done <<< "$CRASH_FILES"

# Sum up all sizes from the temp file
if [ -s "$TEMP_SIZE_FILE" ]; then
    TOTAL_SIZE_KB=$(awk '{sum += $1} END {print sum}' "$TEMP_SIZE_FILE")
fi
rm -f "$TEMP_SIZE_FILE"
    TOTAL_SIZE_MB=$((TOTAL_SIZE_KB / 1024))
    
    log "Found ${CYAN}$FILE_COUNT${NC} crash reports and core dumps using ${CYAN}${TOTAL_SIZE_MB}MB${NC}"
    
    if confirm "Would you like to remove crash reports and core dumps?"; then
        REMOVED_COUNT=0
        
        while IFS= read -r crash_file; do
            # Skip empty lines
            [ -z "$crash_file" ] && continue
            
            # Remove file if accessible (may need sudo for system files)
            if [[ "$crash_file" == "/var/"* ]]; then
                sudo rm -f "$crash_file" 2>/dev/null && REMOVED_COUNT=$((REMOVED_COUNT + 1)) || log "${RED}Failed to remove $crash_file${NC}"
            else
                safe_file_operation "remove" "$crash_file" && REMOVED_COUNT=$((REMOVED_COUNT + 1))
            fi
        done <<< "$CRASH_FILES"
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + TOTAL_SIZE_KB))
        
        log "${GREEN}Removed $REMOVED_COUNT crash reports and core dumps (${TOTAL_SIZE_MB}MB)${NC}"
    fi
}

# Clean application caches
clean_app_caches() {
    log "${BOLD}====== APPLICATION CACHES ======${NC}"
    log "Checking application caches..."
    
    # List of common cache directories to clean
    declare -a CACHE_DIRS=(
        "$HOME/.cache/thumbnails"
        "$HOME/.thumbnails"
        "$HOME/.cache/mozilla"
        "$HOME/.cache/spotify"
        "$HOME/.cache/Mesa_Shader_Cache"
        "$HOME/.cache/fontconfig"
    )
    
    TOTAL_CACHE_SIZE=0
    
    # Check size of each cache directory
    for dir in "${CACHE_DIRS[@]}"; do
        if [ -d "$dir" ] && check_path_accessibility "$dir"; then
            DIR_SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "0")
            DIR_SIZE_KB=$(du -sk "$dir" 2>/dev/null | cut -f1 || echo "0")
            TOTAL_CACHE_SIZE=$((TOTAL_CACHE_SIZE + DIR_SIZE_KB))
            log "Found cache: $dir (${CYAN}$DIR_SIZE${NC})"
        fi
    done
    
    TOTAL_CACHE_SIZE_MB=$((TOTAL_CACHE_SIZE / 1024))
    log "Total application cache size: ${CYAN}${TOTAL_CACHE_SIZE_MB}MB${NC}"
    
    if [ "$TOTAL_CACHE_SIZE" -eq 0 ]; then
        log "No application caches found"
        return
    fi
if confirm "Would you like to clean application caches?"; then
        for dir in "${CACHE_DIRS[@]}"; do
            if [ -d "$dir" ] && check_path_accessibility "$dir"; then
                log "Cleaning $dir..."
                rm -rf "$dir"/* 2>/dev/null || log "${RED}Failed to clean $dir${NC}"
            fi
        done
        
        # Record space saved
        SPACE_SAVED=$((SPACE_SAVED + TOTAL_CACHE_SIZE))
        
        log "${GREEN}Application caches cleaned (${TOTAL_CACHE_SIZE_MB}MB)${NC}"
    fi
}

# Clean system journals
clean_system_journals() {
    log "${BOLD}====== SYSTEM JOURNALS ======${NC}"
    
    if ! command -v journalctl &> /dev/null; then
        log "${YELLOW}journalctl not available, skipping journal cleanup${NC}"
        return
    fi
    
    log "Checking system journal size..."
    
    JOURNAL_SIZE=$(journalctl --disk-usage 2>/dev/null | cut -d " " -f7-8 || echo "Unknown")
    log "Current journal size: ${CYAN}$JOURNAL_SIZE${NC}"
    
    # If in emergency mode or prompted
    if [ "$EMERGENCY_MODE" = true ] || confirm "Would you like to clean up system journals?"; then
        # In emergency mode, use more aggressive cleaning (3 days instead of 7)
        if [ "$EMERGENCY_MODE" = true ]; then
            log "Cleaning system journals older than 3 days (emergency mode)..."
            sudo journalctl --vacuum-time=3d
        else
            log "Cleaning system journals older than 7 days..."
            sudo journalctl --vacuum-time=7d
        fi
        
        NEW_JOURNAL_SIZE=$(journalctl --disk-usage 2>/dev/null | cut -d " " -f7-8 || echo "Unknown")
        log "${GREEN}Journal cleanup completed${NC}"
        log "New journal size: ${CYAN}$NEW_JOURNAL_SIZE${NC}"
    fi
}

# Find and handle duplicate files - improved version
find_duplicate_files() {
    log "${BOLD}====== DUPLICATE FILES ======${NC}"
    log "Checking for duplicate files..."
    
    # Install fdupes if not already installed
    if ! command -v fdupes &> /dev/null; then
        if confirm "fdupes (duplicate file finder) is not installed. Would you like to install it?"; then
            log "Installing fdupes..."
            sudo apt update && sudo apt install -y fdupes
        else
            log "Skipping duplicate file detection (fdupes not installed)"
            return
        fi
    fi
    
    # Create duplicate files report
    DUPES_REPORT="$BACKUP_DIR/duplicate_files.txt"
    log "Scanning for duplicate files (this may take a while)..."
# Exclude certain directories to make scan faster and avoid system files
    EXCLUDE_DIRS=(
        "$HOME/.cache"
        "$HOME/.local/share/Trash"
        "$HOME/.npm"
        "$HOME/.gradle"
        "$HOME/.m2"
        "$HOME/node_modules"
        "$HOME/.git"
    )
    
    # Build exclude arguments
    EXCLUDE_ARGS=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$dir"
        fi
    done
    
    # Show progress indicator - improved with exclude directories
    (fdupes -r $EXCLUDE_ARGS "$HOME" > "$DUPES_REPORT") &
    PID=$!
    spinner $PID
    
    # Count number of duplicate file sets
    DUPE_SETS=$(grep -c "^$" "$DUPES_REPORT" || echo "0")
    
    if [ "$DUPE_SETS" -eq 0 ]; then
        log "No duplicate files found"
        return
    fi
    
    TOTAL_DUPES=$(grep -v "^$" "$DUPES_REPORT" | wc -l)
    
    # Better calculation of wasted space
    TEMP_SIZE_FILE="$BACKUP_DIR/dupes_size.txt"
    grep -v "^$" "$DUPES_REPORT" | xargs -I{} du -ch "{}" 2>/dev/null > "$TEMP_SIZE_FILE"
    
    # Calculate total wasted space 
    WASTED_SPACE=$(awk '/total$/ {sum+=$1} END {print sum}' "$TEMP_SIZE_FILE")
    
    log "Found ${CYAN}$DUPE_SETS${NC} sets of duplicate files with ${CYAN}$TOTAL_DUPES${NC} total files"
    log "Potential space savings: ${CYAN}$WASTED_SPACE${NC}"
    
    if [ "$REPORT_ONLY" = true ]; then
        log "Duplicate file report saved to $DUPES_REPORT"
        return
    fi
    
    # In emergency mode, offer to auto-remove duplicates
    if [ "$EMERGENCY_MODE" = true ]; then
        if confirm "Would you like to automatically clean up duplicate files (keeping the first copy)?"; then
            log "Automatically removing duplicate files (keeping first copy)..."
            fdupes -rdN "$HOME"
            log "${GREEN}Duplicate file cleanup completed${NC}"
            return
        fi
    fi
    
    if confirm "Would you like to review and clean up duplicate files?"; then
        # Make a backup copy of the report
        cp "$DUPES_REPORT" "$DUPES_REPORT.bak"
        
        # Open the report in a text editor if interactive
        if [ "$INTERACTIVE" = true ]; then
            if command -v nano &> /dev/null; then
                log "Opening duplicate file report in nano..."
                nano "$DUPES_REPORT"
            else
                log "Opening duplicate file report in less..."
                less "$DUPES_REPORT"
            fi
        fi
if confirm "Would you like to interactively remove duplicate files?"; then
            log "Starting interactive duplicate file removal..."
            fdupes -rd "$HOME"
            log "${GREEN}Duplicate file cleanup completed${NC}"
        fi
    fi
}

# Clean Docker resources if installed (with improved error handling)
clean_docker() {
    log "${BOLD}====== DOCKER CLEANUP ======${NC}"
    
    if ! command -v docker &> /dev/null; then
        log "${YELLOW}Docker not installed, skipping Docker cleanup${NC}"
        return
    fi
    
    log "Checking Docker resources..."
    
    # Check if user is in docker group
    if ! groups | grep -q docker; then
        log "${YELLOW}WARNING: You are not in the docker group. Docker operations may fail.${NC}"
        
        if confirm "Would you like to add yourself to the docker group? (requires logout/login to take effect)"; then
            log "Adding user to docker group..."
            sudo usermod -aG docker $USER
            log "${GREEN}Added to docker group. Please log out and log back in for changes to take effect.${NC}"
            log "${YELLOW}Skipping Docker cleanup for now.${NC}"
            return
        fi
    fi
    
    # Check if Docker service is running
    if ! systemctl is-active --quiet docker; then
        log "${YELLOW}Docker service is not running. Attempting to start...${NC}"
        
        if confirm "Would you like to start the Docker service?"; then
            sudo systemctl start docker
            
            if ! systemctl is-active --quiet docker; then
                log "${RED}Failed to start Docker service. Skipping Docker cleanup.${NC}"
                return
            else
                log "${GREEN}Docker service started successfully.${NC}"
            fi
        else
            log "Skipping Docker cleanup"
            return
        fi
    fi
    
    # Get Docker disk usage
    DOCKER_USAGE=$(docker system df 2>/dev/null || echo "Docker not responding")
    
    if [[ "$DOCKER_USAGE" == *"permission denied"* ]] || [[ "$DOCKER_USAGE" == *"not responding"* ]]; then
        log "${RED}Cannot access Docker. You might need to run 'newgrp docker' or restart your session.${NC}"
        
        if confirm "Would you like to try running Docker commands with sudo?"; then
            log "Getting Docker disk usage with sudo..."
            DOCKER_USAGE=$(sudo docker system df 2>/dev/null || echo "Docker not responding")
            
            if [[ "$DOCKER_USAGE" == *"not responding"* ]]; then
                log "${RED}Still cannot access Docker. Skipping Docker cleanup.${NC}"
                return
            fi
log "Current Docker disk usage:"
            echo "$DOCKER_USAGE" | tee -a "$LOG_FILE"
            
            if confirm "Would you like to clean up unused Docker resources (with sudo)?"; then
                log "Removing unused Docker containers..."
                sudo docker container prune -f
                
                log "Removing unused Docker images..."
                sudo docker image prune -f
                
                log "Removing unused Docker volumes..."
                sudo docker volume prune -f
                
                log "Removing unused Docker networks..."
                sudo docker network prune -f
                
                # Get new Docker disk usage
                NEW_DOCKER_USAGE=$(sudo docker system df)
                log "${GREEN}Docker cleanup completed${NC}"
                log "New Docker disk usage:"
                echo "$NEW_DOCKER_USAGE" | tee -a "$LOG_FILE"
            fi
        else
            log "Skipping Docker cleanup"
        fi
        
        return
    fi
    
    log "Current Docker disk usage:"
    echo "$DOCKER_USAGE" | tee -a "$LOG_FILE"
    
    if confirm "Would you like to clean up unused Docker resources?"; then
        log "Removing unused Docker containers..."
        docker container prune -f
        
        log "Removing unused Docker images..."
        docker image prune -f
        
        log "Removing unused Docker volumes..."
        docker volume prune -f
        
        log "Removing unused Docker networks..."
        docker network prune -f
        
        # Get new Docker disk usage
        NEW_DOCKER_USAGE=$(docker system df)
        log "${GREEN}Docker cleanup completed${NC}"
        log "New Docker disk usage:"
        echo "$NEW_DOCKER_USAGE" | tee -a "$LOG_FILE"
    fi
}

# Run system maintenance tasks
system_maintenance() {
    log "${BOLD}====== SYSTEM MAINTENANCE ======${NC}"
    
    if confirm "Would you like to run system maintenance tasks (apt clean, autoremove)?"; then
        log "Running apt clean..."
        sudo apt clean
        
        log "Running apt autoremove..."
        sudo apt autoremove -y
        
        log "Cleaning package lists..."
        sudo rm -rf /var/lib/apt/lists/*
        
        log "Cleaning thumbnails cache..."
        rm -rf ~/.cache/thumbnails/* 2>/dev/null || true
        
        log "${GREEN}System maintenance tasks completed${NC}"
    fi
if [ "$EMERGENCY_MODE" = false ] && confirm "Would you like to check for and remove old kernel packages (BE CAREFUL)?"; then
        CURRENT_KERNEL=$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")
        log "Current kernel: $CURRENT_KERNEL"
        
        OLD_KERNELS=$(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$CURRENT_KERNEL"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/;/[0-9]/!d')
        
        if [ -z "$OLD_KERNELS" ]; then
            log "No old kernel packages found"
        else
            OLD_KERNEL_COUNT=$(echo "$OLD_KERNELS" | wc -l)
            log "Found $OLD_KERNEL_COUNT old kernel packages:"
            echo "$OLD_KERNELS" | tee -a "$LOG_FILE"
            
            if confirm "${RED}WARNING: This will remove old kernel packages. Make sure your system is stable. Continue?${NC}"; then
                log "Removing old kernel packages..."
                sudo apt purge $OLD_KERNELS -y
                log "${GREEN}Old kernel packages removed${NC}"
            fi
        fi
    fi
}

# Add new feature: Final cleanup steps and system health check
final_cleanup() {
    log "${BOLD}====== FINAL CLEANUP ======${NC}"
    
    # Clean package lists for apt
    if command -v apt &> /dev/null; then
        if confirm "Would you like to clean package lists to save disk space?"; then
            log "Cleaning package lists..."
            sudo apt clean
            log "${GREEN}Package lists cleaned${NC}"
        fi
    fi
    
    # System health check
    log "${BOLD}====== SYSTEM HEALTH CHECK ======${NC}"
    log "Performing system health check..."
    
    # Check disk health
    if command -v smartctl &> /dev/null; then
        log "Checking disk health status..."
        DISK_DEVICE_SHORT=$(echo "$DISK_DEVICE" | sed 's/[0-9]*$//')
        if [[ "$DISK_DEVICE_SHORT" == "/dev/"* ]]; then
            SMART_STATUS=$(sudo smartctl -H "$DISK_DEVICE_SHORT" 2>/dev/null || echo "Not supported")
            if [[ "$SMART_STATUS" == *"PASSED"* ]]; then
                log "${GREEN}Disk health status: PASSED${NC}"
            elif [[ "$SMART_STATUS" == *"FAILED"* ]]; then
                log "${RED}WARNING: Disk health status: FAILED - Consider backing up your data!${NC}"
            else
                log "${YELLOW}Disk health check not supported or requires special permissions${NC}"
            fi
        fi
    else
        log "${YELLOW}smartctl not installed, skipping disk health check${NC}"
    fi
    
    # Check filesystem status
    log "Checking filesystem status..."
    FILESYSTEM_STATUS=$(sudo tune2fs -l "$DISK_DEVICE" 2>/dev/null | grep "Filesystem state" || echo "Unknown")
    if [[ "$FILESYSTEM_STATUS" == *"clean"* ]]; then
        log "${GREEN}Filesystem status: CLEAN${NC}"
    elif [[ "$FILESYSTEM_STATUS" != "Unknown" ]]; then
        log "${YELLOW}Filesystem status: $FILESYSTEM_STATUS${NC}"
        log "Consider running 'sudo fsck $DISK_DEVICE' at next reboot"
    fi
# Check for system updates needing restart
    if [ -f /var/run/reboot-required ]; then
        log "${YELLOW}System indicates a reboot is required for updates to take effect${NC}"
    fi
    
    # Check if swap is enabled and used
    SWAP_USAGE=$(free -h | grep Swap)
    if [[ "$SWAP_USAGE" == *"0B"* ]]; then
        log "${YELLOW}Swap space is not enabled or used. Consider enabling swap for better performance.${NC}"
    else
        log "${GREEN}Swap space is properly configured${NC}"
    fi
}

# Set up scheduled cleaning
setup_scheduled_cleaning() {
    log "${BOLD}====== SCHEDULED CLEANING ======${NC}"
    
    if command -v crontab &> /dev/null; then
        log "Setting up scheduled cleaning..."
        
        # Get current script path
        SCRIPT_PATH=$(readlink -f "$0")
        
        # Create a temp file for crontab
        TEMP_CRON=$(mktemp)
        crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# $PROGRAM_NAME scheduled tasks" > "$TEMP_CRON"
        
        # Remove any existing TidyTux cron jobs to avoid duplicates
        grep -v "$PROGRAM_NAME" "$TEMP_CRON" > "${TEMP_CRON}.new"
        mv "${TEMP_CRON}.new" "$TEMP_CRON"
        
        # Choose schedule
        echo -e "${CYAN}Select schedule for automated cleanup:${NC}"
        echo "1) Weekly (Sunday at 2am)"
        echo "2) Monthly (1st of month at 3am)"
        echo "3) Daily (every day at 4am)"
        echo "4) Low disk space monitoring (runs in emergency mode when disk space is low)"
        read -r -p "Choose schedule [1-4]: " schedule_choice
        
        case "$schedule_choice" in
            1)
                echo "# $PROGRAM_NAME v$VERSION weekly cleanup" >> "$TEMP_CRON"
                echo "0 2 * * 0 $SCRIPT_PATH --yes --quiet" >> "$TEMP_CRON"
                SCHEDULE_MSG="weekly (Sunday at 2am)"
                ;;
            2)
                echo "# $PROGRAM_NAME v$VERSION monthly cleanup" >> "$TEMP_CRON"
                echo "0 3 1 * * $SCRIPT_PATH --yes --quiet" >> "$TEMP_CRON"
                SCHEDULE_MSG="monthly (1st of month at 3am)"
                ;;
            3)
                echo "# $PROGRAM_NAME v$VERSION daily cleanup" >> "$TEMP_CRON"
                echo "0 4 * * * $SCRIPT_PATH --yes --quiet" >> "$TEMP_CRON"
                SCHEDULE_MSG="daily (every day at 4am)"
                ;;
            4)
                echo "# $PROGRAM_NAME v$VERSION low disk space monitoring" >> "$TEMP_CRON"
                # Check disk space every 3 hours and run in emergency mode if less than 5GB free
                echo "0 */3 * * * if [ \$(df -k --output=avail $HOME | tail -1) -lt $((5 * 1024 * 1024)) ]; then $SCRIPT_PATH --emergency --quiet; fi" >> "$TEMP_CRON"
                SCHEDULE_MSG="low disk space monitoring (checked every 3 hours)"
                ;;
            *)
                log "${YELLOW}Invalid choice, using weekly schedule${NC}"
                echo "# $PROGRAM_NAME v$VERSION weekly cleanup" >> "$TEMP_CRON"
                echo "0 2 * * 0 $SCRIPT_PATH --yes --quiet" >> "$TEMP_CRON"
                SCHEDULE_MSG="weekly (Sunday at 2am)"
                ;;
        esac
# Install new crontab
        crontab "$TEMP_CRON"
        rm "$TEMP_CRON"
        
        log "${GREEN}Scheduled cleanup set up for $SCHEDULE_MSG${NC}"
        log "Use 'crontab -l' to view and 'crontab -e' to modify schedule"
    else
        log "${YELLOW}crontab not available, skipping scheduled cleanup${NC}"
    fi
}

# Show disk usage summary with improved visualization
disk_usage_summary() {
    log "${BOLD}====== FINAL SUMMARY ======${NC}"
    
    # Calculate space saved
    FINAL_DISK_USAGE=$(df -h --output=used "$HOME" | tail -1 | tr -d ' ')
    
    # Calculate new available space
    FINAL_AVAIL=$(df -h --output=avail "$HOME" | tail -1 | tr -d ' ')
    
    log "${GREEN}===== Disk Usage Summary =====${NC}"
    log "Space used before cleanup: ${CYAN}$INITIAL_DISK_USAGE${NC}"
    log "Space used after cleanup:  ${CYAN}$FINAL_DISK_USAGE${NC}"
    log "Space available now:       ${CYAN}$FINAL_AVAIL${NC}"
    
    # Calculate the MB value of space saved
    SPACE_SAVED_MB=$((SPACE_SAVED / 1024))
    # Convert to GB if > 1024 MB
    if [ $SPACE_SAVED_MB -gt 1024 ]; then
        SPACE_SAVED_GB=$(echo "scale=2; $SPACE_SAVED_MB/1024" | bc)
        log "Approximate space freed:   ${CYAN}${SPACE_SAVED_GB} GB${NC}"
    else
        log "Approximate space freed:   ${CYAN}${SPACE_SAVED_MB} MB${NC}"
    fi
    
    # Get time elapsed
    END_TIME=$(date +%s)
    RUNTIME=$((END_TIME - START_TIME))
    MINUTES=$((RUNTIME / 60))
    SECONDS=$((RUNTIME % 60))
    
    log "Script runtime: ${CYAN}${MINUTES}m ${SECONDS}s${NC}"
    
    # Summary of unavailable paths
    if [ ${#UNAVAILABLE_PATHS[@]} -gt 0 ]; then
        log "${YELLOW}WARNING: The following paths were unavailable during cleanup:${NC}"
        for path in "${UNAVAILABLE_PATHS[@]}"; do
            log "  - $path"
        done
        log "These may be on a disconnected drive or have been moved/deleted."
    fi
    
    if command -v ncdu &> /dev/null && confirm "Would you like to see detailed disk usage with ncdu?"; then
        log "Running ncdu on home directory..."
        ncdu "$HOME"
    else
        log "Top 10 largest directories/files:"
        du -sh "$HOME"/* 2>/dev/null | sort -hr | head -10 | tee -a "$LOG_FILE"
    fi
# Check if still low on space
    AVAILABLE_KB=$(df -k --output=avail "$HOME" | tail -1)
    if [ "$AVAILABLE_KB" -lt $((5 * 1024 * 1024)) ]; then  # Less than 5GB
        log "${YELLOW}WARNING: You are still low on disk space (less than 5GB available)${NC}"
        log "Consider running the script with --emergency option for more aggressive cleaning"
        
        if [ ! "$EMERGENCY_MODE" = true ] && confirm "Would you like to run in emergency mode now for more aggressive cleaning?"; then
            EMERGENCY_MODE=true
            log "Rerunning cleaning tasks in emergency mode..."
            
            # Rerun the most effective space saving tasks
            clean_browser_caches
            clean_app_caches
            clean_system_journals
            
            # Check for Docker images that can be cleaned
            if command -v docker &> /dev/null; then
                if confirm "Would you like to remove ALL Docker images (not just unused ones)?"; then
                    log "Removing all Docker images..."
                    sudo docker rmi $(sudo docker images -q) -f
                    log "${GREEN}All Docker images removed${NC}"
                fi
            fi
        fi
    else
        log "${GREEN}Disk space is now at a healthy level${NC}"
    fi
}

# Main execution
main() {
    # Process command line arguments
    parse_arguments "$@"
    
    # Create backup directory structure right away
    mkdir -p "$BACKUP_DIR"
    
    # Detect removable storage early
    detect_removable_storage
    
    if [ "$INTERACTIVE" = true ]; then
        clear
        echo -e "${GREEN}========== $PROGRAM_NAME v$VERSION ==========${NC}"
        echo -e "${CYAN}$PROGRAM_DESCRIPTION${NC}"
        
        if [ "$EMERGENCY_MODE" = true ]; then
            echo -e "${RED}RUNNING IN EMERGENCY MODE - AGGRESSIVE CLEANING ENABLED${NC}"
        fi
        
        echo -e "${YELLOW}This utility will clean up your system by:${NC}"
        echo "  - Moving .deb installation files to backup"
        echo "  - Organizing your Downloads folder"
        echo "  - Managing duplicate scripts"
        echo "  - Cleaning up old snap revisions"
        echo "  - Cleaning browser caches" 
        echo "  - Cleaning Docker resources (if installed)"
        echo "  - Cleaning snap app caches"
        echo "  - Cleaning old log files and crash reports"
        echo "  - Finding and removing duplicate files"
        echo "  - Running system maintenance tasks"
        echo "  - Showing disk usage information"
        echo
        echo -e "${RED}IMPORTANT: This script will move files around your system.${NC}"
        echo -e "${RED}A backup will be created at $BACKUP_DIR${NC}"
        echo
        
        if ! confirm "Do you want to proceed?"; then
            echo "Cleanup canceled. Exiting..."
            exit 0
        fi
    fi
    
    # Create backup directory
    create_backup_dir
    
    # Check for required tools
    install_required_tools
    
    # Start the cleanup process - check disk space first
    check_disk_space
    
    # If report only mode, just gather information
    if [ "$REPORT_ONLY" = true ]; then
        log "Running in report-only mode (no changes will be made)"
        find_duplicate_files
        clean_deb_files
        disk_usage_summary
        log "$PROGRAM_NAME completed in report-only mode"
        exit 0
    fi
    
    # Run system updates if requested and not in emergency mode
    if [ "$EMERGENCY_MODE" = false ] && confirm "Would you like to check for system updates?"; then
        update_system
    fi
    
    # Run all cleanup tasks
    # Use subshells for parallelization where possible for non-critical tasks
    (clean_deb_files) &
    (organize_downloads) &
    wait  # Wait for parallel tasks to complete
    
    clean_duplicate_scripts
    clean_snap_packages
    clean_browser_caches
    clean_app_caches
    clean_snap_app_caches # Added new function
    clean_log_files # Added new function
    clean_crash_reports # Added new function
    clean_system_journals
    find_duplicate_files
    clean_docker
    system_maintenance
    final_cleanup # Added new function
    
    # Show final summary
    disk_usage_summary
    
    echo
    log "${GREEN}========== $PROGRAM_NAME Completed ==========${NC}"
    log "Backup created at: $BACKUP_DIR"
    log "Log file: $LOG_FILE"
    echo
    
    # Set up scheduled cleaning if requested
    if [ "$SCHEDULE" = true ]; then
        setup_scheduled_cleaning
    elif [ "$INTERACTIVE" = true ] && [ "$EMERGENCY_MODE" = false ]; then
        if confirm "Would you like to set up scheduled automatic cleaning?"; then
            setup_scheduled_cleaning
        fi
    fi
    
    if [ "$INTERACTIVE" = true ] && confirm "Would you like to see a summary of actions taken?"; then
        if command -v less &> /dev/null; then
            less "$LOG_FILE"
        else
            cat "$LOG_FILE"
        fi
    fi
    
    log "$PROGRAM_NAME v$VERSION completed successfully"
}

# Run the main function with all arguments
main "$@"
