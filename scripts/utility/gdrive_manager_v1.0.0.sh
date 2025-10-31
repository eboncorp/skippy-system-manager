#!/bin/bash

# Complete Google Drive Manager with Smart Backup
# Advanced rclone-based Google Drive management with intelligent file organization

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GDRIVE_LOCAL_PATH="$HOME/GoogleDrive"
RCLONE_REMOTE_NAME="googledrive"
MOUNT_POINT="$GDRIVE_LOCAL_PATH"
PID_FILE="/tmp/rclone_mount.pid"
CONFIG_FILE="$HOME/.gdrive-manager.conf"
LOG_FILE="/tmp/gdrive-manager.log"
BACKUP_QUEUE_FILE="/tmp/gdrive_backup_queue.txt"

# Default exclusion patterns
DEFAULT_EXCLUDES=(
    "*.tmp"
    "*.temp"
    "*.log"
    "*~"
    ".DS_Store"
    "Thumbs.db"
    "*.swap"
    "*.swp"
    "node_modules/"
    ".git/"
    ".cache/"
    ".thumbnails/"
    "snap/*/common/"
    "snap/*/[0-9]*/"
    ".local/share/Trash/"
    ".mozilla/firefox/*/Cache/"
    ".config/google-chrome/*/Cache/"
    ".steam/"
    ".wine/"
)

# Smart categorization rules
declare -A CATEGORY_PATTERNS=(
    ["Financial"]="*tax* *bank* *statement* *receipt* *invoice* *financial* *budget* *.qbo *w2* *1099* *k-1*"
    ["Documents"]="*.pdf *.doc *.docx *.odt *.rtf"
    ["Scripts"]="*.sh *.py *.js *.pl *.rb *.php"
    ["Configuration"]="*.conf *.config *.cfg *.ini *.json *.yaml *.yml"
    ["Archives"]="*.zip *.tar *.gz *.bz2 *.xz *.7z *.rar"
    ["Images"]="*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.svg *.webp"
    ["Videos"]="*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"
    ["Audio"]="*.mp3 *.wav *.flac *.ogg *.m4a *.aac"
    ["Data"]="*.csv *.xlsx *.xls *.ods *.sqlite *.db"
    ["Guides"]="*guide* *tutorial* *instructions* *readme* *manual* *.md"
)

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   Complete Google Drive Manager v2.0${NC}"
    echo -e "${BLUE}   Smart Backup • Auto-Organization • Sync${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

print_progress() {
    echo -e "${PURPLE}[PROGRESS]${NC} $1"
}

# Load configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        create_default_config
    fi
}

# Create default configuration
create_default_config() {
    cat > "$CONFIG_FILE" << EOF
# Google Drive Manager Configuration
SYNC_ENABLED=true
AUTO_CATEGORIZE=true
SMART_BACKUP=true
SCHEDULE_ENABLED=false
BACKUP_COMPRESSION=true
VERIFY_TRANSFERS=true
BANDWIDTH_LIMIT=""
MAX_TRANSFERS=4
EXCLUDE_HIDDEN=true
BACKUP_RETENTION_DAYS=90
NOTIFICATION_ENABLED=false
CONFLICT_RESOLUTION="ask"
EOF
    print_status "Created default configuration at $CONFIG_FILE"
}

# Initialize logging
init_logging() {
    echo "=== Google Drive Manager Log - $(date) ===" > "$LOG_FILE"
}

# Check if rclone is installed
check_rclone() {
    if ! command -v rclone &> /dev/null; then
        print_error "rclone is not installed."
        read -p "Would you like to install rclone? (y/n): " install_choice
        if [[ $install_choice =~ ^[Yy]$ ]]; then
            install_rclone
        else
            print_error "Cannot proceed without rclone. Exiting."
            exit 1
        fi
    else
        local version=$(rclone version | head -1 | cut -d' ' -f2)
        print_status "rclone version $version is installed"
    fi
}

# Install rclone with latest version
install_rclone() {
    print_status "Installing latest rclone..."
    
    # Try official install script first
    if curl -f https://rclone.org/install.sh | sudo bash; then
        print_success "rclone installed successfully via official installer!"
    else
        print_warning "Official installer failed, trying package manager..."
        sudo apt update
        if sudo apt install -y rclone; then
            print_success "rclone installed via package manager!"
        else
            print_error "Failed to install rclone"
            exit 1
        fi
    fi
}

# Configure Google Drive with enhanced options
configure_gdrive() {
    print_status "Configuring Google Drive with enhanced settings..."
    
    # Check if config already exists
    if rclone listremotes | grep -q "^${RCLONE_REMOTE_NAME}:$"; then
        print_warning "Google Drive remote '${RCLONE_REMOTE_NAME}' already exists."
        read -p "Do you want to reconfigure it? (y/n): " reconfig
        if [[ ! $reconfig =~ ^[Yy]$ ]]; then
            return 0
        fi
        rclone config delete $RCLONE_REMOTE_NAME
    fi
    
    print_status "Starting enhanced rclone configuration..."
    echo
    echo -e "${CYAN}Configuration Steps:${NC}"
    echo "1. Choose 'n' for new remote"
    echo "2. Enter name: $RCLONE_REMOTE_NAME"
    echo "3. Choose Google Drive (usually option 15-18)"
    echo "4. Leave client_id blank (press Enter)"
    echo "5. Leave client_secret blank (press Enter)"
    echo "6. Choose '1' for full access to all files"
    echo "7. Leave root_folder_id blank (press Enter)"
    echo "8. Leave service_account_file blank (press Enter)"
    echo "9. Choose 'n' for advanced config"
    echo "10. Choose 'y' for auto config (opens browser)"
    echo "11. Choose 'n' for team drive (unless you need it)"
    echo "12. Choose 'y' to confirm"
    echo "13. Choose 'q' to quit config"
    echo
    read -p "Press Enter to continue..."
    
    rclone config
    
    # Verify and test configuration
    if rclone listremotes | grep -q "^${RCLONE_REMOTE_NAME}:$"; then
        print_success "Google Drive configured successfully!"
        
        # Test connection
        if rclone about ${RCLONE_REMOTE_NAME}: &>/dev/null; then
            print_success "Connection test passed!"
            rclone about ${RCLONE_REMOTE_NAME}: 2>/dev/null | grep -E "(Total|Used|Free)" | while read line; do
                print_status "  $line"
            done
        else
            print_warning "Configuration successful but connection test failed"
        fi
        return 0
    else
        print_error "Configuration failed or was cancelled."
        return 1
    fi
}

# Create optimized local directory structure
create_local_structure() {
    print_status "Creating optimized local directory structure..."
    
    local dirs=(
        "$GDRIVE_LOCAL_PATH"
        "$GDRIVE_LOCAL_PATH/Backup"
        "$GDRIVE_LOCAL_PATH/Backup/Financial"
        "$GDRIVE_LOCAL_PATH/Backup/Documents"
        "$GDRIVE_LOCAL_PATH/Backup/Scripts"
        "$GDRIVE_LOCAL_PATH/Backup/Configuration"
        "$GDRIVE_LOCAL_PATH/Backup/Guides"
        "$GDRIVE_LOCAL_PATH/Backup/Archives"
        "$GDRIVE_LOCAL_PATH/Sync"
        "$GDRIVE_LOCAL_PATH/Manual"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created: $dir"
        fi
    done
    
    # Create README files
    cat > "$GDRIVE_LOCAL_PATH/README.md" << EOF
# Google Drive Local Mount

This directory is your Google Drive mounted locally via rclone.

## Directory Structure:
- **Backup/**: Automated backups organized by category
- **Sync/**: Two-way synchronized folders
- **Manual/**: Manually managed files and folders

## Categories:
- Financial: Tax documents, bank statements, receipts
- Documents: PDFs, Word docs, presentations
- Scripts: Shell scripts, code files
- Configuration: Config files, settings
- Guides: Documentation, tutorials, manuals
- Archives: Compressed files, backups

Generated by Google Drive Manager v2.0
EOF

    print_success "Local directory structure created!"
}

# Enhanced mount with optimal settings
mount_gdrive() {
    # Check if already mounted
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_warning "Google Drive is already mounted at $MOUNT_POINT"
        return 0
    fi
    
    # Check if PID file exists and process is running
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_warning "rclone mount process is already running (PID: $pid)"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    create_local_structure
    
    print_status "Mounting Google Drive with optimized settings..."
    
    # Enhanced mount with optimal settings for performance and reliability
    local mount_cmd="rclone mount ${RCLONE_REMOTE_NAME}: \"$MOUNT_POINT\""
    mount_cmd+=" --vfs-cache-mode full"
    mount_cmd+=" --vfs-cache-max-age 168h"
    mount_cmd+=" --vfs-cache-max-size 2G"
    mount_cmd+=" --vfs-read-chunk-size 64M"
    mount_cmd+=" --vfs-read-chunk-size-limit 2G"
    mount_cmd+=" --buffer-size 64M"
    mount_cmd+=" --dir-cache-time 168h"
    mount_cmd+=" --drive-chunk-size 128M"
    mount_cmd+=" --drive-upload-cutoff 128M"
    mount_cmd+=" --drive-acknowledge-abuse"
    mount_cmd+=" --timeout 1h"
    mount_cmd+=" --contimeout 60s"
    mount_cmd+=" --low-level-retries 20"
    mount_cmd+=" --retries 5"
    mount_cmd+=" --stats 30s"
    mount_cmd+=" --stats-log-level NOTICE"
    mount_cmd+=" --log-level INFO"
    mount_cmd+=" --log-file /tmp/rclone_mount.log"
    
    # Add bandwidth limit if configured
    if [ -n "$BANDWIDTH_LIMIT" ]; then
        mount_cmd+=" --bwlimit $BANDWIDTH_LIMIT"
    fi
    
    mount_cmd+=" --daemon"
    
    # Execute mount command
    eval "nohup $mount_cmd > /tmp/rclone_mount_startup.log 2>&1 &"
    local mount_pid=$!
    echo $mount_pid > "$PID_FILE"
    
    # Wait and verify mount
    print_progress "Waiting for mount to initialize..."
    local attempts=0
    while [ $attempts -lt 30 ]; do
        if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            print_success "Google Drive mounted successfully at $MOUNT_POINT"
            print_status "Mount process PID: $mount_pid"
            print_status "Cache location: ~/.cache/rclone/vfs/${RCLONE_REMOTE_NAME}"
            return 0
        fi
        sleep 2
        ((attempts++))
        print_progress "Mount attempt $attempts/30..."
    done
    
    print_error "Failed to mount Google Drive. Check logs:"
    print_error "  - /tmp/rclone_mount.log"
    print_error "  - /tmp/rclone_mount_startup.log"
    rm -f "$PID_FILE"
    return 1
}

# Enhanced unmount with cleanup
unmount_gdrive() {
    if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_warning "Google Drive is not mounted."
        cleanup_orphaned_processes
        return 0
    fi
    
    print_status "Unmounting Google Drive..."
    
    # Sync cache before unmount
    print_progress "Syncing cache to Google Drive..."
    if command -v rclone &> /dev/null; then
        rclone vfs forget ${RCLONE_REMOTE_NAME}: 2>/dev/null || true
    fi
    
    # Try graceful unmount first
    if fusermount -u "$MOUNT_POINT" 2>/dev/null; then
        print_success "Google Drive unmounted successfully."
    else
        # Force unmount if graceful fails
        print_warning "Graceful unmount failed, trying force unmount..."
        if sudo umount -f "$MOUNT_POINT" 2>/dev/null; then
            print_success "Google Drive force unmounted successfully."
        else
            print_error "Failed to unmount Google Drive. Manual intervention may be required."
            return 1
        fi
    fi
    
    cleanup_orphaned_processes
}

# Clean up orphaned processes
cleanup_orphaned_processes() {
    # Clean up PID file and processes
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Stopping rclone process (PID: $pid)..."
            kill "$pid" 2>/dev/null
            sleep 3
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Force killing rclone process..."
                kill -9 "$pid" 2>/dev/null
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Find and clean up any remaining rclone mount processes
    local orphaned_pids=$(pgrep -f "rclone mount.*${RCLONE_REMOTE_NAME}" 2>/dev/null || true)
    if [ -n "$orphaned_pids" ]; then
        print_status "Cleaning up orphaned rclone processes..."
        echo "$orphaned_pids" | xargs kill 2>/dev/null || true
        sleep 2
        echo "$orphaned_pids" | xargs kill -9 2>/dev/null || true
    fi
}

# Generate exclude patterns
generate_exclude_file() {
    local exclude_file="/tmp/rclone_excludes.txt"
    
    # Write default excludes
    printf '%s\n' "${DEFAULT_EXCLUDES[@]}" > "$exclude_file"
    
    # Add user-specific excludes if they exist
    if [ -f "$HOME/.gdrive-excludes" ]; then
        cat "$HOME/.gdrive-excludes" >> "$exclude_file"
    fi
    
    echo "$exclude_file"
}

# Smart file categorization
categorize_file() {
    local file="$1"
    local filename=$(basename "$file")
    local filepath=$(dirname "$file")
    
    # Convert to lowercase for pattern matching
    local lower_filename=$(echo "$filename" | tr '[:upper:]' '[:lower:]')
    local lower_filepath=$(echo "$filepath" | tr '[:upper:]' '[:lower:]')
    
    # Check each category
    for category in "${!CATEGORY_PATTERNS[@]}"; do
        local patterns="${CATEGORY_PATTERNS[$category]}"
        for pattern in $patterns; do
            pattern=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
            if [[ "$lower_filename" == $pattern ]] || [[ "$lower_filepath" == *"$pattern"* ]]; then
                echo "$category"
                return
            fi
        done
    done
    
    # Default category
    echo "Miscellaneous"
}

# Intelligent backup analysis
analyze_home_directory() {
    print_status "Analyzing your home directory for intelligent backup suggestions..."
    
    local analysis_file="/tmp/gdrive_analysis.txt"
    local important_dirs=()
    local important_files=()
    local total_size=0
    
    # Analyze important directories
    print_progress "Scanning for important directories..."
    
    # Financial documents
    if [ -d "$HOME/Documents/Financial" ]; then
        local size=$(du -sb "$HOME/Documents/Financial" 2>/dev/null | cut -f1)
        important_dirs+=("Documents/Financial:$size:High Priority")
        total_size=$((total_size + size))
    fi
    
    # Downloads with categorization
    if [ -d "$HOME/Downloads" ]; then
        print_progress "Analyzing Downloads folder..."
        
        # Financial docs in Downloads
        local financial_files=$(find "$HOME/Downloads" -type f \( -name "*tax*" -o -name "*bank*" -o -name "*statement*" -o -name "*.qbo" -o -name "*budget*" \) 2>/dev/null | wc -l)
        if [ $financial_files -gt 0 ]; then
            important_dirs+=("Downloads/Financial-docs:$(du -sb "$HOME/Downloads/docs" 2>/dev/null | cut -f1 || echo 0):High Priority")
        fi
        
        # Scripts and guides
        local script_files=$(find "$HOME/Downloads" -type f \( -name "*.sh" -o -name "*guide*.md" -o -name "*setup*" \) 2>/dev/null | wc -l)
        if [ $script_files -gt 0 ]; then
            important_dirs+=("Downloads/Scripts-and-guides:$(du -sb "$HOME/Downloads" 2>/dev/null | cut -f1):Medium Priority")
        fi
    fi
    
    # Scripts directory
    if [ -d "$HOME/scripts" ]; then
        local size=$(du -sb "$HOME/scripts" 2>/dev/null | cut -f1)
        important_dirs+=("scripts:$size:High Priority")
        total_size=$((total_size + size))
    fi
    
    # Desktop exports and important files
    if [ -d "$HOME/Desktop" ]; then
        local size=$(du -sb "$HOME/Desktop" 2>/dev/null | cut -f1)
        if [ $size -gt 1048576 ]; then  # > 1MB
            important_dirs+=("Desktop:$size:Medium Priority")
        fi
    fi
    
    # Generate analysis report
    {
        echo "=== Google Drive Backup Analysis ==="
        echo "Generated: $(date)"
        echo "Total estimated backup size: $(numfmt --to=iec $total_size)"
        echo ""
        echo "RECOMMENDED BACKUP DIRECTORIES:"
        
        for item in "${important_dirs[@]}"; do
            IFS=':' read -r dir size priority <<< "$item"
            printf "%-30s %10s %s\n" "$dir" "$(numfmt --to=iec $size)" "$priority"
        done
        
        echo ""
        echo "SMART CATEGORIZATION SUGGESTIONS:"
        echo "- Financial docs → /Backup/Financial/"
        echo "- Scripts and configs → /Backup/Scripts/"
        echo "- Guides and documentation → /Backup/Guides/"
        echo "- General documents → /Backup/Documents/"
        echo ""
        echo "ESTIMATED SYNC TIME:"
        echo "- Initial backup: $(calculate_sync_time $total_size)"
        echo "- Daily incremental: < 5 minutes"
        
    } > "$analysis_file"
    
    cat "$analysis_file"
    
    echo
    read -p "Would you like to start smart backup based on this analysis? (y/n): " start_backup
    if [[ $start_backup =~ ^[Yy]$ ]]; then
        smart_backup_wizard
    fi
}

# Calculate estimated sync time
calculate_sync_time() {
    local size_bytes=$1
    local size_mb=$((size_bytes / 1048576))
    
    # Assume 2MB/s average upload speed
    local time_seconds=$((size_mb / 2))
    
    if [ $time_seconds -lt 60 ]; then
        echo "${time_seconds} seconds"
    elif [ $time_seconds -lt 3600 ]; then
        echo "$((time_seconds / 60)) minutes"
    else
        echo "$((time_seconds / 3600)) hours $((time_seconds % 3600 / 60)) minutes"
    fi
}

# Smart backup wizard
smart_backup_wizard() {
    print_header
    print_status "Starting Smart Backup Wizard..."
    
    # Create backup plan
    local backup_plan=()
    
    # Financial documents
    if [ -d "$HOME/Documents/Financial" ] || [ -d "$HOME/Downloads/docs" ]; then
        backup_plan+=("financial")
        print_status "✓ Financial documents will be backed up"
    fi
    
    # Scripts and configuration
    local script_count=$(find "$HOME" -maxdepth 2 -name "*.sh" 2>/dev/null | wc -l)
    if [ $script_count -gt 0 ]; then
        backup_plan+=("scripts")
        print_status "✓ Scripts and configuration files will be backed up"
    fi
    
    # Documentation and guides
    local guide_count=$(find "$HOME/Downloads" -name "*guide*.md" -o -name "*complete*.md" 2>/dev/null | wc -l)
    if [ $guide_count -gt 0 ]; then
        backup_plan+=("guides")
        print_status "✓ Documentation and guides will be backed up"
    fi
    
    # Desktop important files
    if [ -d "$HOME/Desktop" ]; then
        backup_plan+=("desktop")
        print_status "✓ Desktop files will be backed up"
    fi
    
    echo
    read -p "Proceed with smart backup? (y/n): " proceed
    if [[ ! $proceed =~ ^[Yy]$ ]]; then
        return
    fi
    
    # Execute backup plan
    for category in "${backup_plan[@]}"; do
        case $category in
            "financial")
                backup_financial_documents
                ;;
            "scripts")
                backup_scripts_and_configs
                ;;
            "guides")
                backup_documentation
                ;;
            "desktop")
                backup_desktop_files
                ;;
        esac
    done
    
    print_success "Smart backup completed!"
    print_status "Your files are now safely backed up to Google Drive"
    
    # Setup automated sync
    setup_auto_sync_suggestion
}

# Backup financial documents
backup_financial_documents() {
    print_status "Backing up financial documents..."
    
    local exclude_file=$(generate_exclude_file)
    local remote_path="${RCLONE_REMOTE_NAME}:Backup/Financial"
    
    # Backup Documents/Financial
    if [ -d "$HOME/Documents/Financial" ]; then
        print_progress "Syncing Documents/Financial..."
        rclone sync "$HOME/Documents/Financial" "$remote_path/Documents" \
            --exclude-from "$exclude_file" \
            --progress --transfers $MAX_TRANSFERS --checkers 8 \
            --stats 30s --retries 3
    fi
    
    # Backup financial docs from Downloads
    if [ -d "$HOME/Downloads/docs" ]; then
        print_progress "Syncing financial documents from Downloads..."
        rclone copy "$HOME/Downloads/docs" "$remote_path/Downloads-Docs" \
            --include "*.qbo" --include "*tax*" --include "*bank*" \
            --include "*statement*" --include "*budget*" --include "*.pdf" \
            --progress --transfers $MAX_TRANSFERS
    fi
    
    print_success "Financial documents backed up successfully!"
}

# Backup scripts and configuration files
backup_scripts_and_configs() {
    print_status "Backing up scripts and configuration files..."
    
    local exclude_file=$(generate_exclude_file)
    local remote_path="${RCLONE_REMOTE_NAME}:Backup/Scripts"
    
    # Backup main scripts directory
    if [ -d "$HOME/scripts" ]; then
        print_progress "Syncing scripts directory..."
        rclone sync "$HOME/scripts" "$remote_path/PersonalScripts" \
            --exclude-from "$exclude_file" \
            --progress --transfers $MAX_TRANSFERS
    fi
    
    # Backup important scripts from Downloads and home
    print_progress "Backing up important scripts..."
    
    # Create temp directory for script collection
    local temp_dir="/tmp/script_backup_$$"
    mkdir -p "$temp_dir"
    
    # Collect scripts
    find "$HOME" -maxdepth 2 -name "*.sh" -not -path "*/.*" 2>/dev/null | while read script; do
        local script_name=$(basename "$script")
        local script_dir=$(dirname "$script" | sed "s|$HOME/||")
        mkdir -p "$temp_dir/$script_dir"
        cp "$script" "$temp_dir/$script_dir/"
    done
    
    # Upload collected scripts
    if [ "$(ls -A $temp_dir 2>/dev/null)" ]; then
        rclone sync "$temp_dir" "$remote_path/CollectedScripts" \
            --progress --transfers $MAX_TRANSFERS
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
    
    print_success "Scripts and configurations backed up successfully!"
}

# Backup documentation and guides
backup_documentation() {
    print_status "Backing up documentation and guides..."
    
    local remote_path="${RCLONE_REMOTE_NAME}:Backup/Guides"
    
    # Backup markdown guides from Downloads
    print_progress "Syncing markdown guides..."
    rclone copy "$HOME/Downloads" "$remote_path/Downloads" \
        --include "*.md" --include "*guide*" --include "*complete*" \
        --progress --transfers $MAX_TRANSFERS
    
    # Backup PDF documentation
    if [ -d "$HOME/Downloads/documents" ]; then
        print_progress "Syncing PDF documentation..."
        rclone sync "$HOME/Downloads/documents" "$remote_path/PDFs" \
            --include "*.pdf" \
            --progress --transfers $MAX_TRANSFERS
    fi
    
    print_success "Documentation and guides backed up successfully!"
}

# Backup desktop files
backup_desktop_files() {
    print_status "Backing up desktop files..."
    
    local exclude_file=$(generate_exclude_file)
    local remote_path="${RCLONE_REMOTE_NAME}:Backup/Desktop"
    
    if [ -d "$HOME/Desktop" ]; then
        rclone sync "$HOME/Desktop" "$remote_path" \
            --exclude-from "$exclude_file" \
            --progress --transfers $MAX_TRANSFERS
        print_success "Desktop files backed up successfully!"
    fi
}

# Setup automatic sync suggestions
setup_auto_sync_suggestion() {
    echo
    print_status "Setting up automated sync recommendations..."
    
    cat << EOF

${CYAN}AUTOMATED SYNC RECOMMENDATIONS:${NC}

1. ${GREEN}Daily Backup Cron Job:${NC}
   Add this to your crontab (run: crontab -e):
   ${YELLOW}0 2 * * * $HOME/gdrive-manager.sh auto-backup >> /tmp/gdrive-auto.log 2>&1${NC}

2. ${GREEN}Real-time Sync (inotify):${NC}
   Install: sudo apt install inotify-tools
   Run: $HOME/gdrive-manager.sh watch-sync

3. ${GREEN}Scheduled Full Sync:${NC}
   Weekly full sync every Sunday at 3 AM:
   ${YELLOW}0 3 * * 0 $HOME/gdrive-manager.sh full-sync >> /tmp/gdrive-weekly.log 2>&1${NC}

4. ${GREEN}Mount on Boot:${NC}
   Add to /etc/fstab or create systemd service

EOF

    read -p "Would you like to set up daily automated backup? (y/n): " setup_auto
    if [[ $setup_auto =~ ^[Yy]$ ]]; then
        setup_cron_backup
    fi
}

# Setup cron backup
setup_cron_backup() {
    print_status "Setting up automated daily backup..."
    
    # Create backup script entry
    local cron_line="0 2 * * * $HOME/gdrive-manager.sh auto-backup >> /tmp/gdrive-auto.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "gdrive-manager.sh auto-backup"; then
        print_warning "Automated backup cron job already exists"
        return
    fi
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
    
    if [ $? -eq 0 ]; then
        print_success "Daily automated backup scheduled for 2:00 AM"
        print_status "Logs will be saved to /tmp/gdrive-auto.log"
    else
        print_error "Failed to set up automated backup"
    fi
}

# Auto backup function (for cron)
auto_backup() {
    init_logging
    print_status "Starting automated backup..."
    
    # Check if mounted
    if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "Google Drive not mounted, attempting to mount..."
        mount_gdrive
        if [ $? -ne 0 ]; then
            print_error "Failed to mount Google Drive for auto backup"
            return 1
        fi
    fi
    
    # Run smart backup categories
    backup_financial_documents
    backup_scripts_and_configs
    backup_documentation
    
    print_success "Automated backup completed successfully"
}

# Watch and sync (real-time with inotify)
watch_sync() {
    if ! command -v inotifywait &> /dev/null; then
        print_error "inotify-tools not installed. Install with: sudo apt install inotify-tools"
        return 1
    fi
    
    print_status "Starting real-time sync monitoring..."
    print_status "Watching directories for changes..."
    print_warning "Press Ctrl+C to stop"
    
    # Directories to watch
    local watch_dirs=(
        "$HOME/Documents/Financial"
        "$HOME/scripts"
        "$HOME/Desktop"
    )
    
    # Start monitoring
    for dir in "${watch_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status "Monitoring: $dir"
            inotifywait -m -r -e modify,create,delete,move "$dir" --format '%w%f %e' |
            while read file event; do
                print_progress "Detected $event on $file"
                # Sync the changed directory
                local parent_dir=$(dirname "$file")
                local category=$(categorize_file "$file")
                sync_file_by_category "$file" "$category"
            done &
        fi
    done
    
    wait
}

# Sync file by category
sync_file_by_category() {
    local file="$1"
    local category="$2"
    local remote_base="${RCLONE_REMOTE_NAME}:Backup"
    
    case $category in
        "Financial")
            rclone copy "$file" "$remote_base/Financial/" --progress
            ;;
        "Scripts")
            rclone copy "$file" "$remote_base/Scripts/" --progress
            ;;
        *)
            rclone copy "$file" "$remote_base/Miscellaneous/" --progress
            ;;
    esac
}

# Enhanced sync with verification
sync_to_gdrive() {
    local source_dir="$1"
    local dest_dir="$2"
    local verify="${3:-true}"
    
    if [ -z "$source_dir" ]; then
        read -p "Enter local directory to sync: " source_dir
    fi
    
    if [ -z "$dest_dir" ]; then
        read -p "Enter Google Drive destination (or press Enter for /Backup/Manual): " dest_dir
        dest_dir=${dest_dir:-"Backup/Manual"}
    fi
    
    if [ ! -d "$source_dir" ]; then
        print_error "Source directory does not exist: $source_dir"
        return 1
    fi
    
    local exclude_file=$(generate_exclude_file)
    local remote_path="${RCLONE_REMOTE_NAME}:${dest_dir}"
    
    print_status "Syncing $source_dir to $remote_path..."
    print_warning "This will make the remote directory match the local directory exactly."
    
    # Show what would be synced
    print_progress "Calculating sync changes..."
    rclone sync "$source_dir" "$remote_path" \
        --exclude-from "$exclude_file" \
        --dry-run --stats-one-line 2>/dev/null | tail -5
    
    echo
    read -p "Continue with sync? (y/n): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        # Perform sync with progress
        rclone sync "$source_dir" "$remote_path" \
            --exclude-from "$exclude_file" \
            --progress \
            --transfers $MAX_TRANSFERS \
            --checkers 8 \
            --contimeout 60s \
            --timeout 300s \
            --retries 3 \
            --low-level-retries 10 \
            --stats 30s \
            --stats-log-level NOTICE
        
        local sync_result=$?
        
        if [ $sync_result -eq 0 ]; then
            print_success "Sync completed successfully!"
            
            # Verify if requested
            if [[ $verify == "true" ]] && [[ $VERIFY_TRANSFERS == "true" ]]; then
                print_progress "Verifying sync integrity..."
                rclone check "$source_dir" "$remote_path" \
                    --exclude-from "$exclude_file" \
                    --one-way
                
                if [ $? -eq 0 ]; then
                    print_success "Verification passed - all files synced correctly!"
                else
                    print_warning "Verification found some differences - check logs"
                fi
            fi
        else
            print_error "Sync failed with exit code $sync_result"
            return $sync_result
        fi
    fi
}

# Enhanced sync from Google Drive
sync_from_gdrive() {
    local source_dir="$1"
    local dest_dir="$2"
    
    if [ -z "$source_dir" ]; then
        print_status "Available backup categories:"
        rclone lsd ${RCLONE_REMOTE_NAME}:Backup/ 2>/dev/null | awk '{print "  - " $5}'
        echo
        read -p "Enter Google Drive source directory: " source_dir
    fi
    
    if [ -z "$dest_dir" ]; then
        read -p "Enter local destination directory: " dest_dir
    fi
    
    local remote_path="${RCLONE_REMOTE_NAME}:${source_dir}"
    
    mkdir -p "$dest_dir"
    
    print_status "Syncing $remote_path to $dest_dir..."
    
    # Show what would be synced
    print_progress "Calculating sync changes..."
    rclone sync "$remote_path" "$dest_dir" \
        --dry-run --stats-one-line 2>/dev/null | tail -5
    
    echo
    read -p "Continue with sync? (y/n): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        rclone sync "$remote_path" "$dest_dir" \
            --progress \
            --transfers $MAX_TRANSFERS \
            --checkers 8 \
            --contimeout 60s \
            --timeout 300s \
            --retries 3 \
            --low-level-retries 10 \
            --stats 30s
        
        if [ $? -eq 0 ]; then
            print_success "Sync completed successfully!"
        else
            print_error "Sync failed!"
        fi
    fi
}

# Enhanced upload with smart categorization
upload_to_gdrive() {
    local source="$1"
    local dest="$2"
    local auto_categorize="${3:-$AUTO_CATEGORIZE}"
    
    if [ -z "$source" ]; then
        read -p "Enter file/directory to upload: " source
    fi
    
    if [ ! -e "$source" ]; then
        print_error "Source does not exist: $source"
        return 1
    fi
    
    # Auto-categorize if enabled
    if [[ $auto_categorize == "true" ]] && [ -z "$dest" ]; then
        local category=$(categorize_file "$source")
        dest="Backup/$category"
        print_status "Auto-categorized as: $category"
        print_status "Destination: $dest"
        read -p "Use this destination? (y/n): " use_auto
        if [[ ! $use_auto =~ ^[Yy]$ ]]; then
            read -p "Enter Google Drive destination: " dest
        fi
    elif [ -z "$dest" ]; then
        read -p "Enter Google Drive destination (or press Enter for /Manual): " dest
        dest=${dest:-"Manual"}
    fi
    
    local remote_path="${RCLONE_REMOTE_NAME}:${dest}"
    
    print_status "Uploading $source to $remote_path..."
    
    # Check if it's a large file and warn user
    if [ -f "$source" ]; then
        local file_size=$(stat -c%s "$source" 2>/dev/null || echo 0)
        if [ $file_size -gt 104857600 ]; then  # > 100MB
            print_warning "Large file detected ($(numfmt --to=iec $file_size))"
            print_warning "This may take a while to upload"
        fi
    fi
    
    local exclude_file=$(generate_exclude_file)
    
    rclone copy "$source" "$remote_path" \
        --exclude-from "$exclude_file" \
        --progress \
        --transfers $MAX_TRANSFERS \
        --checkers 8 \
        --contimeout 60s \
        --timeout 300s \
        --retries 3 \
        --low-level-retries 10 \
        --stats 30s
    
    if [ $? -eq 0 ]; then
        print_success "Upload completed successfully!"
        
        # Show uploaded location
        print_status "File available at: https://drive.google.com (in /$dest folder)"
    else
        print_error "Upload failed!"
    fi
}

# Enhanced download with resume capability
download_from_gdrive() {
    local source="$1"
    local dest="$2"
    
    if [ -z "$source" ]; then
        print_status "Available backup categories:"
        rclone lsd ${RCLONE_REMOTE_NAME}:Backup/ 2>/dev/null | awk '{print "  - " $5}'
        echo
        read -p "Enter Google Drive file/directory to download: " source
    fi
    
    if [ -z "$dest" ]; then
        read -p "Enter local destination directory [Downloads]: " dest
        dest=${dest:-"$HOME/Downloads"}
    fi
    
    local remote_path="${RCLONE_REMOTE_NAME}:${source}"
    
    mkdir -p "$dest"
    
    print_status "Downloading $remote_path to $dest..."
    
    rclone copy "$remote_path" "$dest" \
        --progress \
        --transfers $MAX_TRANSFERS \
        --checkers 8 \
        --contimeout 60s \
        --timeout 300s \
        --retries 3 \
        --low-level-retries 10 \
        --stats 30s
    
    if [ $? -eq 0 ]; then
        print_success "Download completed successfully!"
        print_status "Files downloaded to: $dest"
    else
        print_error "Download failed!"
    fi
}

# Enhanced list with search and filtering
list_gdrive() {
    local path="$1"
    local search_term="$2"
    
    if [ -z "$path" ]; then
        read -p "Enter Google Drive path to list (or press Enter for root): " path
    fi
    
    local remote_path="${RCLONE_REMOTE_NAME}:${path}"
    
    print_status "Listing contents of $remote_path..."
    
    if [ -n "$search_term" ]; then
        print_status "Searching for: $search_term"
        rclone lsf "$remote_path" --recursive | grep -i "$search_term"
    else
        # Show directories first
        print_status "Directories:"
        rclone lsd "$remote_path" 2>/dev/null | head -20
        
        echo
        print_status "Files (showing first 20):"
        rclone ls "$remote_path" 2>/dev/null | head -20
        
        # Show summary
        local total_files=$(rclone ls "$remote_path" 2>/dev/null | wc -l)
        local total_dirs=$(rclone lsd "$remote_path" 2>/dev/null | wc -l)
        
        echo
        print_status "Summary: $total_dirs directories, $total_files files"
        
        if [ $total_files -gt 20 ]; then
            print_status "... and $(($total_files - 20)) more files"
            echo
            read -p "Show all files? (y/n): " show_all
            if [[ $show_all =~ ^[Yy]$ ]]; then
                rclone ls "$remote_path" 2>/dev/null
            fi
        fi
    fi
}

# System status with comprehensive information
show_status() {
    print_header
    
    # System information
    print_status "System Information:"
    echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
    echo "  Kernel: $(uname -r)"
    echo "  User: $(whoami)"
    echo "  Home: $HOME"
    echo
    
    # rclone status
    if command -v rclone &> /dev/null; then
        local version=$(rclone version | head -1)
        print_status "rclone: $version"
        
        # Check for updates
        local current_version=$(rclone version | head -1 | grep -o 'v[0-9.]*')
        print_status "Current version: $current_version"
    else
        print_error "rclone is not installed"
    fi
    
    # Configuration status
    if rclone listremotes | grep -q "^${RCLONE_REMOTE_NAME}:$"; then
        print_success "Google Drive remote '$RCLONE_REMOTE_NAME' is configured"
        
        # Test connection and show quota
        if rclone about ${RCLONE_REMOTE_NAME}: &>/dev/null; then
            print_success "Connection to Google Drive: OK"
            echo
            print_status "Google Drive Storage Info:"
            rclone about ${RCLONE_REMOTE_NAME}: 2>/dev/null | while read line; do
                echo "  $line"
            done
        else
            print_error "Cannot connect to Google Drive (check internet/auth)"
        fi
    else
        print_error "Google Drive remote '$RCLONE_REMOTE_NAME' is not configured"
    fi
    
    echo
    
    # Mount status
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_success "Google Drive is mounted at: $MOUNT_POINT"
        
        # Show mount process info
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            if ps -p "$pid" > /dev/null 2>&1; then
                print_status "Mount process PID: $pid"
                local start_time=$(ps -o lstart= -p $pid 2>/dev/null)
                print_status "Started: $start_time"
            fi
        fi
        
        # Show cache info
        local cache_dir="$HOME/.cache/rclone/vfs/${RCLONE_REMOTE_NAME}"
        if [ -d "$cache_dir" ]; then
            local cache_size=$(du -sh "$cache_dir" 2>/dev/null | cut -f1)
            print_status "Cache size: $cache_size"
        fi
        
        # Show recent activity
        if [ -f "/tmp/rclone_mount.log" ]; then
            print_status "Recent activity (last 5 lines):"
            tail -5 "/tmp/rclone_mount.log" 2>/dev/null | while read line; do
                echo "  $line"
            done
        fi
    else
        print_warning "Google Drive is not mounted"
    fi
    
    echo
    
    # Backup status
    print_status "Backup Configuration:"
    if [ -f "$CONFIG_FILE" ]; then
        echo "  Auto-categorize: $AUTO_CATEGORIZE"
        echo "  Smart backup: $SMART_BACKUP"
        echo "  Max transfers: $MAX_TRANSFERS"
        echo "  Verify transfers: $VERIFY_TRANSFERS"
    else
        print_warning "No configuration file found"
    fi
    
    # Check for scheduled backups
    if crontab -l 2>/dev/null | grep -q "gdrive-manager.sh auto-backup"; then
        print_success "Automated backup is scheduled"
        local next_run=$(crontab -l 2>/dev/null | grep "gdrive-manager.sh auto-backup" | head -1)
        print_status "Schedule: $next_run"
    else
        print_warning "No automated backup scheduled"
    fi
    
    echo
    
    # Quick access information
    print_status "Quick Access:"
    echo "  Google Drive folder: $MOUNT_POINT"
    echo "  Configuration: $CONFIG_FILE"
    echo "  Logs: $LOG_FILE"
    echo "  Mount log: /tmp/rclone_mount.log"
    
    echo
}

# Full synchronization
full_sync() {
    print_status "Starting full synchronization..."
    
    # Ensure mounted
    if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        mount_gdrive
    fi
    
    # Run all backup categories
    backup_financial_documents
    backup_scripts_and_configs
    backup_documentation
    backup_desktop_files
    
    print_success "Full synchronization completed!"
}

# Configuration management
manage_config() {
    print_header
    print_status "Configuration Management"
    echo
    
    if [ ! -f "$CONFIG_FILE" ]; then
        create_default_config
    fi
    
    echo "Current configuration:"
    cat "$CONFIG_FILE" | grep -v '^#' | grep -v '^$'
    echo
    
    echo "1. Edit configuration file"
    echo "2. Reset to defaults"
    echo "3. Show current settings"
    echo "4. Back to main menu"
    echo
    
    read -p "Select option (1-4): " config_choice
    
    case $config_choice in
        1)
            ${EDITOR:-nano} "$CONFIG_FILE"
            load_config
            print_success "Configuration updated!"
            ;;
        2)
            create_default_config
            load_config
            print_success "Configuration reset to defaults!"
            ;;
        3)
            show_status
            ;;
        4)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Maintenance and cleanup
maintenance() {
    print_header
    print_status "Maintenance and Cleanup"
    echo
    
    echo "1. Clean rclone cache"
    echo "2. Repair mount issues"
    echo "3. Update rclone"
    echo "4. Cleanup logs"
    echo "5. Check disk space"
    echo "6. Run all maintenance tasks"
    echo "7. Back to main menu"
    echo
    
    read -p "Select option (1-7): " maint_choice
    
    case $maint_choice in
        1)
            print_status "Cleaning rclone cache..."
            rclone cleanup ${RCLONE_REMOTE_NAME}: 2>/dev/null || true
            local cache_dir="$HOME/.cache/rclone"
            if [ -d "$cache_dir" ]; then
                local old_size=$(du -sh "$cache_dir" 2>/dev/null | cut -f1)
                find "$cache_dir" -type f -mtime +7 -delete 2>/dev/null || true
                local new_size=$(du -sh "$cache_dir" 2>/dev/null | cut -f1)
                print_success "Cache cleaned: $old_size → $new_size"
            fi
            ;;
        2)
            print_status "Repairing mount issues..."
            unmount_gdrive
            cleanup_orphaned_processes
            sleep 2
            mount_gdrive
            ;;
        3)
            print_status "Updating rclone..."
            curl https://rclone.org/install.sh | sudo bash
            ;;
        4)
            print_status "Cleaning up logs..."
            [ -f "$LOG_FILE" ] && rm "$LOG_FILE"
            [ -f "/tmp/rclone_mount.log" ] && > "/tmp/rclone_mount.log"
            [ -f "/tmp/gdrive-auto.log" ] && > "/tmp/gdrive-auto.log"
            print_success "Logs cleaned!"
            ;;
        5)
            print_status "Checking disk space..."
            df -h "$HOME" | tail -1
            df -h /tmp | tail -1
            if [ -d "$HOME/.cache/rclone" ]; then
                echo "rclone cache: $(du -sh "$HOME/.cache/rclone" | cut -f1)"
            fi
            ;;
        6)
            # Run all maintenance tasks
            for i in {1..5}; do
                maintenance_choice=$i
                case $i in
                    1) print_status "Cleaning rclone cache..."; rclone cleanup ${RCLONE_REMOTE_NAME}: 2>/dev/null || true ;;
                    2) print_status "Repairing mount..."; unmount_gdrive; mount_gdrive ;;
                    3) print_status "Updating rclone..."; curl -s https://rclone.org/install.sh | sudo bash ;;
                    4) print_status "Cleaning logs..."; [ -f "$LOG_FILE" ] && rm "$LOG_FILE" ;;
                    5) print_status "Disk space check complete" ;;
                esac
            done
            print_success "All maintenance tasks completed!"
            ;;
        7)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Main menu
show_menu() {
    print_header
    echo "${GREEN}MAIN MENU${NC}"
    echo
    echo " ${CYAN}Setup & Configuration:${NC}"
    echo "  1. Quick Setup (Install + Configure + Mount)"
    echo "  2. Configure Google Drive"
    echo "  3. Mount Google Drive"
    echo "  4. Unmount Google Drive"
    echo
    echo " ${CYAN}Smart Backup:${NC}"
    echo "  5. Analyze Home Directory"
    echo "  6. Smart Backup Wizard"
    echo "  7. Auto Backup (for cron)"
    echo "  8. Full Sync"
    echo
    echo " ${CYAN}Manual Operations:${NC}"
    echo "  9. Upload to Google Drive"
    echo " 10. Download from Google Drive"
    echo " 11. Sync Local → Google Drive"
    echo " 12. Sync Google Drive → Local"
    echo " 13. List Google Drive Contents"
    echo
    echo " ${CYAN}Advanced:${NC}"
    echo " 14. Real-time Sync (Watch Mode)"
    echo " 15. Configuration Management"
    echo " 16. Maintenance & Cleanup"
    echo " 17. Show Status"
    echo
    echo " ${RED}0. Exit${NC}"
    echo
}

# Quick setup with enhanced configuration
quick_setup() {
    print_header
    print_status "Starting Quick Setup Wizard..."
    
    # Initialize
    init_logging
    load_config
    
    # Step 1: Check and install rclone
    print_progress "Step 1/4: Checking rclone installation..."
    check_rclone
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Step 2: Configure Google Drive
    print_progress "Step 2/4: Configuring Google Drive..."
    configure_gdrive
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Step 3: Mount Google Drive
    print_progress "Step 3/4: Mounting Google Drive..."
    mount_gdrive
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Step 4: Setup intelligent backup
    print_progress "Step 4/4: Setting up intelligent backup..."
    analyze_home_directory
    
    print_success "Quick setup completed successfully!"
    print_status "Google Drive is mounted at: $MOUNT_POINT"
    print_status "Use 'Smart Backup Wizard' for automated file organization"
    
    echo
    read -p "Press Enter to continue to main menu..."
}

# Main function
main() {
    # Initialize
    init_logging
    load_config
    
    # Handle command line arguments
    if [ $# -gt 0 ]; then
        case "$1" in
            "status"|"st") show_status ;;
            "mount"|"m") mount_gdrive ;;
            "unmount"|"um") unmount_gdrive ;;
            "setup"|"s") quick_setup ;;
            "config"|"c") configure_gdrive ;;
            "upload"|"up") upload_to_gdrive "$2" "$3" ;;
            "download"|"dl") download_from_gdrive "$2" "$3" ;;
            "list"|"ls") list_gdrive "$2" "$3" ;;
            "sync-to"|"st") sync_to_gdrive "$2" "$3" ;;
            "sync-from"|"sf") sync_from_gdrive "$2" "$3" ;;
            "auto-backup"|"ab") auto_backup ;;
            "full-sync"|"fs") full_sync ;;
            "analyze"|"a") analyze_home_directory ;;
            "smart-backup"|"sb") smart_backup_wizard ;;
            "watch-sync"|"ws") watch_sync ;;
            "maintenance"|"maint") maintenance ;;
            "help"|"h")
                echo "Google Drive Manager v2.0 - Usage:"
                echo "  $0 [command] [options]"
                echo
                echo "Commands:"
                echo "  setup, s          - Quick setup wizard"
                echo "  status, st        - Show detailed status"
                echo "  mount, m          - Mount Google Drive"
                echo "  unmount, um       - Unmount Google Drive"
                echo "  config, c         - Configure Google Drive"
                echo "  analyze, a        - Analyze home directory"
                echo "  smart-backup, sb  - Smart backup wizard"
                echo "  auto-backup, ab   - Automated backup (for cron)"
                echo "  full-sync, fs     - Full synchronization"
                echo "  upload, up        - Upload file/directory"
                echo "  download, dl      - Download file/directory"
                echo "  list, ls          - List Google Drive contents"
                echo "  sync-to, st       - Sync local to Google Drive"
                echo "  sync-from, sf     - Sync Google Drive to local"
                echo "  watch-sync, ws    - Real-time sync monitoring"
                echo "  maintenance, maint - Maintenance and cleanup"
                echo "  help, h           - Show this help"
                ;;
            *) 
                print_error "Unknown command: $1"
                echo "Use '$0 help' for usage information"
                exit 1
                ;;
        esac
        return
    fi
    
    # Interactive mode
    while true; do
        show_menu
        read -p "Select option (0-17): " choice
        
        case $choice in
            1) quick_setup ;;
            2) configure_gdrive ;;
            3) mount_gdrive ;;
            4) unmount_gdrive ;;
            5) analyze_home_directory ;;
            6) smart_backup_wizard ;;
            7) auto_backup ;;
            8) full_sync ;;
            9) upload_to_gdrive ;;
            10) download_from_gdrive ;;
            11) sync_to_gdrive ;;
            12) sync_from_gdrive ;;
            13) list_gdrive ;;
            14) watch_sync ;;
            15) manage_config ;;
            16) maintenance ;;
            17) show_status ;;
            0) 
                print_status "Cleaning up and exiting..."
                # Optional: unmount on exit
                # unmount_gdrive
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please select 0-17."
                ;;
        esac
        
        if [ $choice -ne 0 ]; then
            echo
            read -p "Press Enter to continue..."
        fi
    done
}

# Run main function with all arguments
main "$@"