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
    local destination="$3"
    
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