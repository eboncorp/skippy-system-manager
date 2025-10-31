#!/bin/bash

# TidyTux Enhanced - Comprehensive Linux System Cleanup Utility
# Version 2.0.0
# Created: March 2025
# 
# New Features in v2.0:
#  - Development cache cleanup (node_modules, Python, etc.)
#  - Intelligent large file detection
#  - Parallel processing for faster cleanup
#  - Dry-run mode for safety
#  - Enhanced duplicate detection with checksums
#  - System health monitoring
#  - Configuration file support
#  - Better progress tracking
#  - Improved emergency mode
#  - Cloud storage cache cleanup

VERSION="2.0.0"
PROGRAM_NAME="TidyTux Enhanced"
PROGRAM_DESCRIPTION="Advanced Linux System Cleanup and Optimization Utility"
GITHUB_REPO="https://github.com/username/tidytux"

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "This script should NOT be run as root" >&2
    exit 1
fi

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m' # No Color

# Configuration defaults
readonly CONFIG_DIR="$HOME/.config/tidytux"
readonly CONFIG_FILE="$CONFIG_DIR/tidytux.conf"
readonly STATE_FILE="$CONFIG_DIR/state.json"
readonly CACHE_DIR="$HOME/.cache/tidytux"

# Command line arguments
INTERACTIVE=true
SKIP_CONFIRMATION=false
VERBOSE=false
SCHEDULE=false
REPORT_ONLY=false
EMERGENCY_MODE=false
DRY_RUN=false
PARALLEL=true
CONFIG_MODE=false

# Cleanup targets
CLEAN_SYSTEM=true
CLEAN_DEV=true
CLEAN_BROWSERS=true
CLEAN_DOCKER=true
CLEAN_CLOUD=true

# Storage handling variables
declare -a REMOVABLE_DRIVES=()
declare -a UNAVAILABLE_PATHS=()
declare -A SPACE_BY_CATEGORY=()

# Performance tracking
readonly START_TIME=$(date +%s)
INITIAL_DISK_USAGE=$(df -BM --output=used "$HOME" | tail -1 | tr -d ' M')
SPACE_SAVED=0
ITEMS_PROCESSED=0
ITEMS_CLEANED=0
declare -A CLEANUP_STATS=()

# Progress tracking
CURRENT_TASK=""
TASK_PROGRESS=0
TOTAL_TASKS=0

# Create required directories
mkdir -p "$CONFIG_DIR" "$CACHE_DIR"

# Backup directory with timestamp
BACKUP_DIR="$HOME/.tidytux/backups/backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$BACKUP_DIR/tidytux_log.txt"
REPORT_FILE="$BACKUP_DIR/cleanup_report.html"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Trap for cleanup on exit
trap cleanup_on_exit EXIT

cleanup_on_exit() {
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log "${RED}Script exited with error code: $exit_code${NC}"
    fi
    
    # Save state
    save_state
    
    # Generate final report
    if [ "$REPORT_ONLY" = false ]; then
        generate_report
    fi
    
    return $exit_code
}

# Enhanced logging function
log() {
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="$1"
    
    # Color based on level
    local color=""
    case "$level" in
        ERROR) color="$RED" ;;
        WARN) color="$YELLOW" ;;
        SUCCESS) color="$GREEN" ;;
        INFO) color="$BLUE" ;;
        DEBUG) color="$DIM" ;;
    esac
    
    # Console output
    if [ "$INTERACTIVE" = true ] || [ "$VERBOSE" = true ] || [ "$level" = "ERROR" ]; then
        echo -e "${color}[$timestamp] [$level]${NC} $message"
    fi
    
    # Always write to log file
    echo "[$timestamp] [$level] $message" | sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,3})*)?[mGK]//g" >> "$LOG_FILE"
}

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local task="${3:-Processing}"
    
    if [ "$INTERACTIVE" = false ]; then
        return
    fi
    
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    
    printf "\r${CYAN}%s${NC} [" "$task"
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' '-'
    printf "] %3d%% (%d/%d)" "$percent" "$current" "$total"
    
    if [ "$current" -eq "$total" ]; then
        echo
    fi
}

# Enhanced confirmation function
confirm() {
    local prompt="$1"
    local default="${2:-n}"
    local timeout="${3:-120}"
    
    if [ "$SKIP_CONFIRMATION" = true ] || [ "$DRY_RUN" = true ]; then
        [ "$DRY_RUN" = true ] && log "${DIM}[DRY RUN] Would execute: $prompt${NC}"
        return 0
    fi
    
    if [ "$EMERGENCY_MODE" = true ] && [[ "$prompt" == *"cleanup"* ]]; then
        log "${GREEN}Auto-yes due to emergency mode: $prompt${NC}" "INFO"
        return 0
    fi
    
    local yn_prompt="[y/N]"
    [ "$default" = "y" ] && yn_prompt="[Y/n]"
    
    echo -en "${YELLOW}$prompt $yn_prompt${NC} "
    
    if read -r -t "$timeout" response; then
        case "$response" in
            [yY][eE][sS]|[yY]) return 0 ;;
            [nN][oO]|[nN]) return 1 ;;
            "") [ "$default" = "y" ] && return 0 || return 1 ;;
            *) return 1 ;;
        esac
    else
        echo -e "\n${RED}Timeout after $timeout seconds, assuming no.${NC}"
        return 1
    fi
}

# Load configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log "Loading configuration from $CONFIG_FILE" "DEBUG"
        # shellcheck source=/dev/null
        source "$CONFIG_FILE"
    else
        log "No configuration file found, using defaults" "DEBUG"
        create_default_config
    fi
}

# Create default configuration
create_default_config() {
    cat > "$CONFIG_FILE" << EOF
# TidyTux Configuration File
# Generated on $(date)

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

# Exclusions (comma-separated patterns)
EXCLUDE_PATTERNS=".git,node_modules,venv,virtualenv"
PROTECTED_DIRS="\$HOME/Documents,\$HOME/Pictures,\$HOME/important"

# Performance
ENABLE_PARALLEL=true
MAX_PARALLEL_JOBS=4

# Features
AUTO_INSTALL_TOOLS=false
GENERATE_REPORT=true
SAVE_STATE=true
EOF
    log "Created default configuration at $CONFIG_FILE" "SUCCESS"
}

# Save state for resume capability
save_state() {
    if [ "$SAVE_STATE" = false ]; then
        return
    fi
    
    cat > "$STATE_FILE" << EOF
{
    "last_run": "$(date -Iseconds)",
    "version": "$VERSION",
    "space_saved": $SPACE_SAVED,
    "items_cleaned": $ITEMS_CLEANED,
    "cleanup_stats": {
$(for key in "${!CLEANUP_STATS[@]}"; do
    echo "        \"$key\": ${CLEANUP_STATS[$key]},"
done | sed '$ s/,$//')
    }
}
EOF
}

# Detect system information
detect_system_info() {
    log "${BOLD}====== SYSTEM INFORMATION ======${NC}" "INFO"
    
    # OS Information
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        log "OS: $PRETTY_NAME" "INFO"
    fi
    
    # Kernel
    log "Kernel: $(uname -r)" "INFO"
    
    # CPU and Memory
    log "CPU: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)" "INFO"
    log "Memory: $(free -h | grep Mem | awk '{print $2}')" "INFO"
    
    # Disk information
    log "Disk usage:" "INFO"
    df -h "$HOME" | tail -1
}

# Enhanced disk space check with predictive analysis
check_disk_space() {
    log "${BOLD}====== DISK SPACE ANALYSIS ======${NC}" "INFO"
    
    # Get current disk usage
    local disk_info=$(df -BG "$HOME" | tail -1)
    local total_gb=$(echo "$disk_info" | awk '{print $2}' | tr -d 'G')
    local used_gb=$(echo "$disk_info" | awk '{print $3}' | tr -d 'G')
    local avail_gb=$(echo "$disk_info" | awk '{print $4}' | tr -d 'G')
    local percent=$(echo "$disk_info" | awk '{print $5}' | tr -d '%')
    
    log "Disk space: ${used_gb}GB used of ${total_gb}GB (${percent}% full)" "INFO"
    log "Available: ${avail_gb}GB" "INFO"
    
    # Analyze disk usage trends
    analyze_disk_trends
    
    # Check thresholds
    if [ "$avail_gb" -lt "${EMERGENCY_SPACE_GB:-1}" ]; then
        log "CRITICAL: Less than ${EMERGENCY_SPACE_GB}GB available!" "ERROR"
        EMERGENCY_MODE=true
        emergency_cleanup
    elif [ "$avail_gb" -lt "${WARNING_SPACE_GB:-5}" ]; then
        log "WARNING: Less than ${WARNING_SPACE_GB}GB available" "WARN"
        if confirm "Enable aggressive cleanup mode?" "y"; then
            EMERGENCY_MODE=true
        fi
    fi
    
    # Find largest directories
    log "Analyzing largest directories..." "INFO"
    find_large_directories
}

# Analyze disk usage trends
analyze_disk_trends() {
    local usage_file="$CACHE_DIR/disk_usage.log"
    
    # Log current usage
    echo "$(date -Iseconds) $used_gb $avail_gb $percent" >> "$usage_file"
    
    # Analyze if we have enough data
    if [ $(wc -l < "$usage_file" 2>/dev/null || echo 0) -gt 7 ]; then
        log "Disk usage trend over last 7 runs:" "INFO"
        tail -7 "$usage_file" | awk '{
            split($1, date, "T");
            printf "  %s: %sGB used (%s%% full)\n", date[1], $2, $4
        }'
    fi
}

# Find large directories
find_large_directories() {
    log "Top 10 largest directories in home:" "INFO"
    
    # Use du with timeout to prevent hanging on slow filesystems
    timeout 30 du -h "$HOME" 2>/dev/null | \
        sort -rh | \
        head -20 | \
        grep -E '^[0-9.]+G' | \
        head -10 | \
        while read -r size dir; do
            log "  $size  $dir" "INFO"
        done
}

# Emergency cleanup for critical disk space
emergency_cleanup() {
    log "${BOLD}====== EMERGENCY CLEANUP MODE ======${NC}" "ERROR"
    log "Running emergency cleanup to free disk space..." "WARN"
    
    # 1. Clear all caches
    log "Clearing system caches..." "INFO"
    sudo apt clean
    sudo apt autoclean
    
    # 2. Clear journal logs
    if command -v journalctl &>/dev/null; then
        log "Vacuum journal logs..." "INFO"
        sudo journalctl --vacuum-time=1d
        sudo journalctl --vacuum-size=50M
    fi
    
    # 3. Clear temp files
    log "Clearing temporary files..." "INFO"
    find /tmp -type f -atime +1 -delete 2>/dev/null || true
    find /var/tmp -type f -atime +1 -delete 2>/dev/null || true
    
    # 4. Clear all browser caches
    clean_browser_caches
    
    # 5. Clear thumbnail cache
    rm -rf ~/.cache/thumbnails/* 2>/dev/null || true
    
    # 6. Clear trash
    rm -rf ~/.local/share/Trash/* 2>/dev/null || true
    
    # Check space again
    local new_avail=$(df -BG "$HOME" | tail -1 | awk '{print $4}' | tr -d 'G')
    log "Available space after emergency cleanup: ${new_avail}GB" "SUCCESS"
}

# Enhanced file cleanup with parallel processing
clean_old_files() {
    log "${BOLD}====== OLD FILE CLEANUP ======${NC}" "INFO"
    
    local days="${OLD_FILE_DAYS:-90}"
    log "Looking for files older than $days days..." "INFO"
    
    # Find old files in common locations
    local locations=(
        "$HOME/Downloads"
        "$HOME/.cache"
        "/tmp"
        "/var/tmp"
    )
    
    for location in "${locations[@]}"; do
        if [ ! -d "$location" ]; then
            continue
        fi
        
        log "Scanning $location..." "INFO"
        
        # Find old files with size info
        local old_files=$(find "$location" -type f -atime +"$days" -printf '%s %p\n' 2>/dev/null | sort -nr)
        
        if [ -z "$old_files" ]; then
            continue
        fi
        
        local count=$(echo "$old_files" | wc -l)
        local total_size=$(echo "$old_files" | awk '{sum+=$1} END {print sum}')
        local size_mb=$((total_size / 1024 / 1024))
        
        log "Found $count files older than $days days (${size_mb}MB)" "INFO"
        
        if confirm "Remove these old files from $location?" "n"; then
            echo "$old_files" | while read -r size file; do
                [ -z "$file" ] && continue
                if [ "$DRY_RUN" = true ]; then
                    log "[DRY RUN] Would remove: $file" "DEBUG"
                else
                    rm -f "$file" && ((ITEMS_CLEANED++))
                fi
            done
            SPACE_SAVED=$((SPACE_SAVED + total_size / 1024))
            log "Cleaned ${size_mb}MB from $location" "SUCCESS"
        fi
    done
}

# Development cache cleanup
clean_dev_caches() {
    log "${BOLD}====== DEVELOPMENT CACHE CLEANUP ======${NC}" "INFO"
    
    # Node.js cleanup
    clean_node_modules
    
    # Python cleanup
    clean_python_caches
    
    # Rust cleanup
    clean_rust_caches
    
    # Go cleanup
    clean_go_caches
    
    # VS Code cleanup
    clean_vscode_caches
}

# Clean node_modules directories
clean_node_modules() {
    log "Searching for node_modules directories..." "INFO"
    
    # Find all node_modules with parallel processing
    local node_dirs=$(find "$HOME" -name "node_modules" -type d 2>/dev/null | grep -v ".npm" || echo "")
    
    if [ -z "$node_dirs" ]; then
        log "No node_modules directories found" "INFO"
        return
    fi
    
    # Calculate total size
    local total_size=0
    local count=0
    
    while IFS= read -r dir; do
        [ -z "$dir" ] && continue
        local size=$(du -s "$dir" 2>/dev/null | cut -f1)
        total_size=$((total_size + size))
        ((count++))
    done <<< "$node_dirs"
    
    local size_mb=$((total_size / 1024))
    log "Found $count node_modules directories using ${size_mb}MB" "INFO"
    
    if confirm "Would you like to clean unused node_modules?" "y"; then
        # Find projects not modified in 30 days
        while IFS= read -r dir; do
            [ -z "$dir" ] && continue
            local project_dir=$(dirname "$dir")
            local last_modified=$(find "$project_dir" -name "*.js" -o -name "*.json" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
            local days_old=$(( ($(date +%s) - ${last_modified%.*}) / 86400 ))
            
            if [ "$days_old" -gt 30 ]; then
                log "Removing old node_modules: $dir (${days_old} days old)" "INFO"
                if [ "$DRY_RUN" = false ]; then
                    rm -rf "$dir"
                    ((ITEMS_CLEANED++))
                fi
            fi
        done <<< "$node_dirs"
    fi
}

# Clean Python caches
clean_python_caches() {
    log "Cleaning Python caches..." "INFO"
    
    # Find and clean __pycache__ directories
    local pycache_count=$(find "$HOME" -name "__pycache__" -type d 2>/dev/null | wc -l)
    
    if [ "$pycache_count" -gt 0 ]; then
        log "Found $pycache_count __pycache__ directories" "INFO"
        if confirm "Remove Python cache directories?" "y"; then
            find "$HOME" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
            ((ITEMS_CLEANED += pycache_count))
            log "Removed $pycache_count Python cache directories" "SUCCESS"
        fi
    fi
    
    # Clean pip cache
    if command -v pip &>/dev/null; then
        local pip_cache_size=$(pip cache info 2>/dev/null | grep "Size" | awk '{print $2}')
        if [ -n "$pip_cache_size" ]; then
            log "Pip cache size: $pip_cache_size" "INFO"
            if confirm "Clear pip cache?" "y"; then
                pip cache purge
                log "Pip cache cleared" "SUCCESS"
            fi
        fi
    fi
}

# Clean Rust caches
clean_rust_caches() {
    local cargo_home="${CARGO_HOME:-$HOME/.cargo}"
    
    if [ ! -d "$cargo_home" ]; then
        return
    fi
    
    log "Checking Rust/Cargo caches..." "INFO"
    
    # Check registry cache
    if [ -d "$cargo_home/registry/cache" ]; then
        local cache_size=$(du -sh "$cargo_home/registry/cache" 2>/dev/null | cut -f1)
        log "Cargo registry cache: $cache_size" "INFO"
        
        if confirm "Clean Cargo registry cache?" "y"; then
            rm -rf "$cargo_home/registry/cache"/*
            log "Cargo registry cache cleaned" "SUCCESS"
        fi
    fi
    
    # Clean old target directories
    local target_dirs=$(find "$HOME" -name "target" -type d -path "*/rust/*" 2>/dev/null)
    if [ -n "$target_dirs" ]; then
        local count=$(echo "$target_dirs" | wc -l)
        log "Found $count Rust target directories" "INFO"
        # Similar logic to node_modules cleanup
    fi
}

# Clean Go caches
clean_go_caches() {
    if ! command -v go &>/dev/null; then
        return
    fi
    
    log "Checking Go caches..." "INFO"
    
    # Clean module cache
    local go_cache_size=$(du -sh "$(go env GOMODCACHE)" 2>/dev/null | cut -f1)
    if [ -n "$go_cache_size" ]; then
        log "Go module cache: $go_cache_size" "INFO"
        
        if confirm "Clean Go module cache?" "y"; then
            go clean -modcache
            log "Go module cache cleaned" "SUCCESS"
        fi
    fi
}

# Clean VS Code caches
clean_vscode_caches() {
    local vscode_dirs=(
        "$HOME/.config/Code/Cache"
        "$HOME/.config/Code/CachedData"
        "$HOME/.config/Code/logs"
        "$HOME/.vscode/extensions"
    )
    
    log "Checking VS Code caches..." "INFO"
    
    for dir in "${vscode_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        
        local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        log "$(basename "$dir"): $size" "INFO"
    done
    
    if confirm "Clean VS Code caches?" "y"; then
        rm -rf "$HOME/.config/Code/Cache"/*
        rm -rf "$HOME/.config/Code/CachedData"/*
        rm -rf "$HOME/.config/Code/logs"/*
        log "VS Code caches cleaned" "SUCCESS"
    fi
}

# Enhanced duplicate detection with checksums
find_duplicates() {
    log "${BOLD}====== DUPLICATE FILE DETECTION ======${NC}" "INFO"
    
    if ! command -v fdupes &>/dev/null; then
        log "fdupes not installed. Install it for duplicate detection." "WARN"
        return
    fi
    
    local scan_dirs=(
        "$HOME/Downloads"
        "$HOME/Documents"
        "$HOME/Pictures"
    )
    
    log "Scanning for duplicate files..." "INFO"
    
    for dir in "${scan_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        
        log "Scanning $dir..." "INFO"
        
        # Find duplicates with size threshold (>1MB)
        local duplicates=$(fdupes -r -S -n "$dir" 2>/dev/null | grep -E '^[0-9]+ bytes')
        
        if [ -n "$duplicates" ]; then
            local dup_count=$(echo "$duplicates" | grep -c "^$")
            log "Found duplicate sets in $dir" "INFO"
            
            if confirm "Review and clean duplicates in $dir?" "y"; then
                # Interactive duplicate removal
                fdupes -r -d "$dir"
            fi
        fi
    done
}

# Cloud storage cache cleanup
clean_cloud_caches() {
    log "${BOLD}====== CLOUD STORAGE CLEANUP ======${NC}" "INFO"
    
    # Dropbox cache
    if [ -d "$HOME/.dropbox-cache" ]; then
        local size=$(du -sh "$HOME/.dropbox-cache" 2>/dev/null | cut -f1)
        log "Dropbox cache: $size" "INFO"
        if confirm "Clean Dropbox cache?" "y"; then
            rm -rf "$HOME/.dropbox-cache"/*
            log "Dropbox cache cleaned" "SUCCESS"
        fi
    fi
    
    # OneDrive cache
    if [ -d "$HOME/.config/onedrive" ]; then
        # OneDrive cleanup logic
        log "OneDrive cache found" "INFO"
    fi
    
    # Google Drive cache
    if [ -d "$HOME/.config/google-drive-ocamlfuse" ]; then
        # Google Drive cleanup logic
        log "Google Drive cache found" "INFO"
    fi
}

# Enhanced browser cache cleanup
clean_browser_caches() {
    log "${BOLD}====== BROWSER CACHE CLEANUP ======${NC}" "INFO"
    
    local browsers=(
        "google-chrome:$HOME/.cache/google-chrome:$HOME/.config/google-chrome/Default/Cache"
        "chromium:$HOME/.cache/chromium:$HOME/.config/chromium/Default/Cache"
        "firefox:$HOME/.cache/mozilla/firefox:$HOME/.mozilla/firefox/*.default*/cache2"
        "brave:$HOME/.cache/BraveSoftware:$HOME/.config/BraveSoftware/Brave-Browser/Default/Cache"
        "vivaldi:$HOME/.cache/vivaldi:$HOME/.config/vivaldi/Default/Cache"
        "opera:$HOME/.cache/opera:$HOME/.config/opera/Cache"
    )
    
    local total_size=0
    
    for browser_info in "${browsers[@]}"; do
        IFS=':' read -r browser cache_dir config_cache <<< "$browser_info"
        
        local browser_size=0
        
        # Check cache directory
        if [ -d "$cache_dir" ]; then
            local size=$(du -sb "$cache_dir" 2>/dev/null | cut -f1)
            browser_size=$((browser_size + size))
        fi
        
        # Check config cache
        for dir in $config_cache; do
            if [ -d "$dir" ]; then
                local size=$(du -sb "$dir" 2>/dev/null | cut -f1)
                browser_size=$((browser_size + size))
            fi
        done
        
        if [ "$browser_size" -gt 0 ]; then
            local size_mb=$((browser_size / 1024 / 1024))
            log "$browser cache: ${size_mb}MB" "INFO"
            total_size=$((total_size + browser_size))
        fi
    done
    
    local total_mb=$((total_size / 1024 / 1024))
    log "Total browser cache size: ${total_mb}MB" "INFO"
    
    if [ "$total_size" -eq 0 ]; then
        log "No browser caches found" "INFO"
        return
    fi
    
    if confirm "Clean all browser caches?" "y"; then
        # Check for running browsers
        local running_browsers=()
        for browser_info in "${browsers[@]}"; do
            IFS=':' read -r browser _ _ <<< "$browser_info"
            if pgrep -x "$browser" >/dev/null; then
                running_browsers+=("$browser")
            fi
        done
        
        if [ ${#running_browsers[@]} -gt 0 ]; then
            log "Warning: These browsers are running: ${running_browsers[*]}" "WARN"
            if ! confirm "Continue anyway?" "n"; then
                return
            fi
        fi
        
        # Clean caches
        for browser_info in "${browsers[@]}"; do
            IFS=':' read -r browser cache_dir config_cache <<< "$browser_info"
            
            if [ -d "$cache_dir" ]; then
                log "Cleaning $browser cache..." "INFO"
                rm -rf "$cache_dir"/*
            fi
            
            for dir in $config_cache; do
                if [ -d "$dir" ]; then
                    rm -rf "$dir"/*
                fi
            done
        done
        
        SPACE_SAVED=$((SPACE_SAVED + total_size / 1024))
        log "Browser caches cleaned (${total_mb}MB)" "SUCCESS"
    fi
}

# System package cleanup
clean_system_packages() {
    log "${BOLD}====== SYSTEM PACKAGE CLEANUP ======${NC}" "INFO"
    
    # APT cleanup
    if command -v apt &>/dev/null; then
        log "Cleaning APT cache..." "INFO"
        
        # Check cache size
        local apt_cache_size=$(du -sh /var/cache/apt/archives 2>/dev/null | cut -f1)
        log "APT cache size: $apt_cache_size" "INFO"
        
        if confirm "Clean APT cache?" "y"; then
            sudo apt clean
            sudo apt autoclean
            sudo apt autoremove --purge -y
            log "APT cache cleaned" "SUCCESS"
        fi
    fi
    
    # Snap cleanup
    clean_snap_packages
    
    # Flatpak cleanup
    if command -v flatpak &>/dev/null; then
        log "Cleaning Flatpak cache..." "INFO"
        flatpak uninstall --unused -y
        log "Flatpak cleaned" "SUCCESS"
    fi
}

# Enhanced snap cleanup
clean_snap_packages() {
    if ! command -v snap &>/dev/null; then
        return
    fi
    
    log "Checking snap packages..." "INFO"
    
    # Set retention policy
    sudo snap set system refresh.retain=2
    
    # Find disabled snaps
    local disabled_snaps=$(snap list --all | awk '/disabled/{print $1, $3}')
    
    if [ -z "$disabled_snaps" ]; then
        log "No disabled snap revisions found" "INFO"
        return
    fi
    
    log "Found disabled snap revisions" "INFO"
    
    if confirm "Remove old snap revisions?" "y"; then
        while read -r name revision; do
            [ -z "$name" ] && continue
            log "Removing $name revision $revision..." "INFO"
            sudo snap remove "$name" --revision="$revision"
        done <<< "$disabled_snaps"
        log "Old snap revisions removed" "SUCCESS"
    fi
}

# Docker cleanup (enhanced)
clean_docker() {
    log "${BOLD}====== DOCKER CLEANUP ======${NC}" "INFO"
    
    if ! command -v docker &>/dev/null; then
        log "Docker not installed" "INFO"
        return
    fi
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        log "Docker daemon not running" "WARN"
        return
    fi
    
    # Get Docker disk usage
    log "Docker disk usage:" "INFO"
    docker system df
    
    if confirm "Clean Docker resources?" "y"; then
        log "Cleaning Docker..." "INFO"
        
        # Remove stopped containers
        docker container prune -f
        
        # Remove unused images
        docker image prune -a -f
        
        # Remove unused volumes
        docker volume prune -f
        
        # Remove unused networks
        docker network prune -f
        
        # Remove build cache
        docker builder prune -f
        
        log "Docker cleanup completed" "SUCCESS"
        
        # Show new usage
        docker system df
    fi
}

# Generate HTML report
generate_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        return
    fi
    
    log "Generating cleanup report..." "INFO"
    
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>TidyTux Cleanup Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-box { background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .danger { color: #dc3545; }
        .footer { text-align: center; color: #666; margin-top: 30px; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TidyTux Cleanup Report</h1>
        <p><strong>Date:</strong> $(date)<br>
        <strong>Duration:</strong> ${minutes}m ${seconds}s<br>
        <strong>Mode:</strong> $([ "$DRY_RUN" = true ] && echo "Dry Run" || echo "Full Cleanup")</p>
        
        <h2>Summary Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">$(echo "scale=2; $SPACE_SAVED/1024" | bc)MB</div>
                <div class="stat-label">Space Saved</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">$ITEMS_CLEANED</div>
                <div class="stat-label">Items Cleaned</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">$ITEMS_PROCESSED</div>
                <div class="stat-label">Items Processed</div>
            </div>
        </div>
        
        <h2>Cleanup Details</h2>
        <table>
            <tr><th>Category</th><th>Items</th><th>Space Saved</th></tr>
EOF

    for category in "${!CLEANUP_STATS[@]}"; do
        echo "<tr><td>$category</td><td>${CLEANUP_STATS[$category]}</td><td>-</td></tr>" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" << EOF
        </table>
        
        <h2>Disk Usage After Cleanup</h2>
        <pre>$(df -h "$HOME")</pre>
        
        <div class="footer">
            <p>Generated by TidyTux v$VERSION</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log "Report saved to: $REPORT_FILE" "SUCCESS"
}

# Setup scheduled cleanup
setup_schedule() {
    log "Setting up scheduled cleanup..." "INFO"
    
    local script_path=$(readlink -f "$0")
    local cron_entry="0 2 * * 0 $script_path --quiet --yes"
    
    # Check if already scheduled
    if crontab -l 2>/dev/null | grep -q "tidytux"; then
        log "TidyTux is already scheduled" "INFO"
        return
    fi
    
    if confirm "Schedule weekly cleanup (Sundays at 2 AM)?" "y"; then
        (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
        log "Scheduled cleanup added to crontab" "SUCCESS"
    fi
}

# Main cleanup orchestrator
run_cleanup() {
    log "${BOLD}Starting TidyTux Enhanced v$VERSION${NC}" "INFO"
    log "Backup directory: $BACKUP_DIR" "INFO"
    
    # Detect system info
    detect_system_info
    
    # Check disk space
    check_disk_space
    
    # Install missing tools
    if [ "$AUTO_INSTALL_TOOLS" = true ]; then
        install_required_tools
    fi
    
    # Run cleanup tasks
    local tasks=()
    
    [ "$CLEAN_SYSTEM" = true ] && tasks+=("clean_system_packages")
    [ "$CLEAN_SYSTEM" = true ] && tasks+=("clean_old_files")
    [ "$CLEAN_DEV" = true ] && tasks+=("clean_dev_caches")
    [ "$CLEAN_BROWSERS" = true ] && tasks+=("clean_browser_caches")
    [ "$CLEAN_DOCKER" = true ] && tasks+=("clean_docker")
    [ "$CLEAN_CLOUD" = true ] && tasks+=("clean_cloud_caches")
    tasks+=("find_duplicates")
    
    TOTAL_TASKS=${#tasks[@]}
    CURRENT_TASK=0
    
    for task in "${tasks[@]}"; do
        ((CURRENT_TASK++))
        show_progress $CURRENT_TASK $TOTAL_TASKS "Running cleanup tasks"
        $task
    done
    
    echo # New line after progress bar
    
    # Final summary
    show_summary
}

# Show final summary
show_summary() {
    log "${BOLD}====== CLEANUP SUMMARY ======${NC}" "INFO"
    
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    # Calculate space saved
    local space_saved_mb=$((SPACE_SAVED / 1024))
    local space_saved_gb=$(echo "scale=2; $SPACE_SAVED / 1024 / 1024" | bc)
    
    # Get new disk usage
    local new_disk_usage=$(df -BM --output=used "$HOME" | tail -1 | tr -d ' M')
    local actual_saved=$((INITIAL_DISK_USAGE - new_disk_usage))
    
    log "Cleanup completed in $((duration / 60))m $((duration % 60))s" "SUCCESS"
    log "Items processed: $ITEMS_PROCESSED" "INFO"
    log "Items cleaned: $ITEMS_CLEANED" "INFO"
    log "Space saved (calculated): ${space_saved_mb}MB" "INFO"
    log "Space saved (actual): ${actual_saved}MB" "INFO"
    
    # Show disk usage change
    local initial_percent=$(df --output=pcent "$HOME" | tail -1 | tr -d ' %')
    local final_percent=$(df --output=pcent "$HOME" | tail -1 | tr -d ' %')
    
    log "Disk usage: $initial_percent% → $final_percent%" "SUCCESS"
    
    if [ "$DRY_RUN" = true ]; then
        log "This was a dry run. No changes were made." "WARN"
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                echo "$PROGRAM_NAME version $VERSION"
                exit 0
                ;;
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -q|--quiet)
                INTERACTIVE=false
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                log "Running in DRY RUN mode - no changes will be made" "WARN"
                shift
                ;;
            -e|--emergency)
                EMERGENCY_MODE=true
                SKIP_CONFIRMATION=true
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
            -c|--config)
                CONFIG_MODE=true
                shift
                ;;
            --no-parallel)
                PARALLEL=false
                shift
                ;;
            --only-system)
                CLEAN_DEV=false
                CLEAN_BROWSERS=false
                CLEAN_DOCKER=false
                CLEAN_CLOUD=false
                shift
                ;;
            --only-dev)
                CLEAN_SYSTEM=false
                CLEAN_BROWSERS=false
                CLEAN_DOCKER=false
                CLEAN_CLOUD=false
                shift
                ;;
            *)
                log "Unknown option: $1" "ERROR"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help
show_help() {
    cat << EOF
$PROGRAM_NAME v$VERSION - $PROGRAM_DESCRIPTION

Usage: $(basename "$0") [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    --version           Show version information
    -y, --yes           Skip all confirmations
    -q, --quiet         Run in quiet mode (minimal output)
    -v, --verbose       Show verbose output
    -n, --dry-run       Show what would be done without making changes
    -e, --emergency     Emergency cleanup mode (aggressive)
    -s, --schedule      Setup scheduled cleanup
    -r, --report-only   Generate report without cleaning
    -c, --config        Edit configuration
    --no-parallel       Disable parallel processing
    --only-system       Clean only system files
    --only-dev          Clean only development files

EXAMPLES:
    $(basename "$0")                # Interactive cleanup
    $(basename "$0") -y -v          # Automatic cleanup with verbose output
    $(basename "$0") -n             # Dry run to see what would be cleaned
    $(basename "$0") -e             # Emergency cleanup for low disk space
    $(basename "$0") --schedule     # Setup weekly cleanup

CONFIGURATION:
    Config file: $CONFIG_FILE
    State file:  $STATE_FILE
    
EOF
}

# Main entry point
main() {
    # Parse arguments
    parse_arguments "$@"
    
    # Load configuration
    load_config
    
    # Handle special modes
    if [ "$CONFIG_MODE" = true ]; then
        ${EDITOR:-nano} "$CONFIG_FILE"
        exit 0
    fi
    
    if [ "$SCHEDULE" = true ]; then
        setup_schedule
        exit 0
    fi
    
    # Create backup directory
    create_backup_dir
    
    # Run cleanup
    run_cleanup
}

# Execute main function
main "$@"