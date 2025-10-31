#!/bin/bash

# Google Drive Manager v2.0 - Complete Package
# Smart Backup • Auto-Organization • Sync • GUI Integration
# Compiled from conversations 2024-2025
# Features: rclone integration, mounting, syncing, backup, Python GUI

set -euo pipefail

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

VERSION="2.0.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROGRAM_NAME="Google Drive Manager"
MOUNT_POINT="$HOME/GoogleDrive"
CONFIG_DIR="$HOME/.config/gdrive-manager"
LOG_DIR="$HOME/.local/share/gdrive-manager/logs"
BACKUP_DIR="$HOME/.local/share/gdrive-manager/backups"
CONFIG_FILE="$CONFIG_DIR/config.conf"
LOG_FILE="$LOG_DIR/gdrive_$(date +%Y%m%d).log"

# Ensure directories exist
mkdir -p "$CONFIG_DIR" "$LOG_DIR" "$BACKUP_DIR"

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Configuration defaults
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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   Complete Google Drive Manager v${VERSION}${NC}"
    echo -e "${BLUE}   Smart Backup • Auto-Organization • Sync${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_progress() {
    echo -e "${PURPLE}[PROGRESS]${NC} $1"
}

log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        create_default_config
    fi
}

create_default_config() {
    cat > "$CONFIG_FILE" << EOF
# Google Drive Manager Configuration
# Version: $VERSION

# Core settings
SYNC_ENABLED=$SYNC_ENABLED
AUTO_CATEGORIZE=$AUTO_CATEGORIZE
SMART_BACKUP=$SMART_BACKUP
SCHEDULE_ENABLED=$SCHEDULE_ENABLED

# Transfer settings
BACKUP_COMPRESSION=$BACKUP_COMPRESSION
VERIFY_TRANSFERS=$VERIFY_TRANSFERS
BANDWIDTH_LIMIT="$BANDWIDTH_LIMIT"
MAX_TRANSFERS=$MAX_TRANSFERS

# File handling
EXCLUDE_HIDDEN=$EXCLUDE_HIDDEN
BACKUP_RETENTION_DAYS=$BACKUP_RETENTION_DAYS
CONFLICT_RESOLUTION="$CONFLICT_RESOLUTION"

# Notifications
NOTIFICATION_ENABLED=$NOTIFICATION_ENABLED

# Custom directories for organization
DOCUMENTS_DIR="Documents"
MEDIA_DIR="Media"
SCRIPTS_DIR="Scripts"
BACKUPS_DIR="Backups"
PROJECTS_DIR="Projects"
EOF
    print_status "Created default configuration at $CONFIG_FILE"
}

# ============================================================================
# RCLONE MANAGEMENT
# ============================================================================

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
    fi
}

install_rclone() {
    print_progress "Installing rclone..."
    
    # Download and install rclone
    curl https://rclone.org/install.sh | sudo bash
    
    if command -v rclone &> /dev/null; then
        print_status "rclone installed successfully"
    else
        print_error "rclone installation failed"
        exit 1
    fi
}

setup_gdrive() {
    print_banner
    print_progress "Setting up Google Drive integration..."
    
    check_rclone
    
    # Check if Google Drive is already configured
    if rclone listremotes | grep -q "^googledrive:$"; then
        print_status "Google Drive remote 'googledrive' already exists"
        read -p "Do you want to reconfigure it? (y/n): " reconfigure
        if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
            print_status "Using existing configuration"
            return
        fi
    fi
    
    print_progress "Configuring Google Drive remote..."
    print_status "This will open a browser for authentication"
    print_status "Please sign in to your Google account and grant permissions"
    
    # Configure Google Drive
    rclone config create googledrive drive
    
    # Test the connection
    if rclone lsd googledrive: > /dev/null 2>&1; then
        print_status "✓ Google Drive configured successfully!"
        
        # Create mount point
        mkdir -p "$MOUNT_POINT"
        print_status "✓ Mount point created at $MOUNT_POINT"
        
        # Load configuration
        load_config
        
        # Mount Google Drive
        print_progress "Mounting Google Drive..."
        mount_gdrive
        
        print_status "✓ Setup complete!"
        print_status "Google Drive is now available at: $MOUNT_POINT"
        print_status "Use '$0 help' to see all available commands"
        
    else
        print_error "Failed to connect to Google Drive"
        print_error "Please run '$0 setup' again to retry configuration"
        exit 1
    fi
}

# ============================================================================
# MOUNT/UNMOUNT OPERATIONS
# ============================================================================

mount_gdrive() {
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "Google Drive is already mounted at $MOUNT_POINT"
        return 0
    fi
    
    print_progress "Mounting Google Drive at $MOUNT_POINT..."
    
    # Create mount point if it doesn't exist
    mkdir -p "$MOUNT_POINT"
    
    # Mount with optimal settings
    rclone mount googledrive: "$MOUNT_POINT" \
        --vfs-cache-mode writes \
        --vfs-cache-max-age 1h \
        --buffer-size 256M \
        --dir-cache-time 1h \
        --poll-interval 15s \
        --daemon \
        --allow-other 2>/dev/null || \
    rclone mount googledrive: "$MOUNT_POINT" \
        --vfs-cache-mode writes \
        --vfs-cache-max-age 1h \
        --buffer-size 256M \
        --dir-cache-time 1h \
        --poll-interval 15s \
        --daemon
    
    # Wait for mount to be ready
    sleep 3
    
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "✓ Google Drive mounted successfully at $MOUNT_POINT"
        log_message "INFO" "Google Drive mounted at $MOUNT_POINT"
        
        # Add to system startup (optional)
        setup_auto_mount
    else
        print_error "Failed to mount Google Drive"
        return 1
    fi
}

unmount_gdrive() {
    if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "Google Drive is not mounted"
        return 0
    fi
    
    print_progress "Unmounting Google Drive..."
    
    # Kill rclone mount process
    pkill -f "rclone mount googledrive:"
    
    # Wait for unmount
    sleep 2
    
    # Force unmount if necessary
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        fusermount -u "$MOUNT_POINT" 2>/dev/null || umount "$MOUNT_POINT" 2>/dev/null
    fi
    
    if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "✓ Google Drive unmounted successfully"
        log_message "INFO" "Google Drive unmounted"
    else
        print_warning "Google Drive may still be mounted"
    fi
}

setup_auto_mount() {
    read -p "Would you like to auto-mount Google Drive at startup? (y/n): " auto_mount
    if [[ $auto_mount =~ ^[Yy]$ ]]; then
        # Create systemd user service
        mkdir -p "$HOME/.config/systemd/user"
        
        cat > "$HOME/.config/systemd/user/gdrive-mount.service" << EOF
[Unit]
Description=Google Drive Mount
After=network-online.target

[Service]
Type=notify
ExecStart=$SCRIPT_DIR/$(basename "$0") mount
ExecStop=$SCRIPT_DIR/$(basename "$0") unmount
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
        
        systemctl --user daemon-reload
        systemctl --user enable gdrive-mount.service
        print_status "✓ Auto-mount configured"
    fi
}

# ============================================================================
# FILE OPERATIONS
# ============================================================================

upload_file() {
    local file_path="$1"
    local remote_path="${2:-}"
    
    if [ ! -e "$file_path" ]; then
        print_error "File or directory does not exist: $file_path"
        return 1
    fi
    
    # Auto-categorize if enabled
    if [ "$AUTO_CATEGORIZE" = "true" ] && [ -z "$remote_path" ]; then
        remote_path=$(auto_categorize_path "$file_path")
    fi
    
    # Set default remote path if not specified
    if [ -z "$remote_path" ]; then
        remote_path=""
    fi
    
    print_progress "Uploading $(basename "$file_path") to googledrive:$remote_path"
    
    # Build rclone command with options
    local rclone_opts=()
    
    if [ "$VERIFY_TRANSFERS" = "true" ]; then
        rclone_opts+=("--checksum")
    fi
    
    if [ -n "$BANDWIDTH_LIMIT" ]; then
        rclone_opts+=("--bwlimit" "$BANDWIDTH_LIMIT")
    fi
    
    if [ "$MAX_TRANSFERS" -gt 1 ]; then
        rclone_opts+=("--transfers" "$MAX_TRANSFERS")
    fi
    
    if [ "$EXCLUDE_HIDDEN" = "true" ]; then
        rclone_opts+=("--exclude" ".*")
    fi
    
    # Upload file or directory
    if [ -f "$file_path" ]; then
        rclone copy "$file_path" "googledrive:$remote_path" "${rclone_opts[@]}" --progress
    elif [ -d "$file_path" ]; then
        rclone copy "$file_path" "googledrive:$remote_path/$(basename "$file_path")" "${rclone_opts[@]}" --progress
    fi
    
    if [ $? -eq 0 ]; then
        print_status "✓ Upload completed successfully"
        log_message "INFO" "Uploaded: $file_path -> googledrive:$remote_path"
    else
        print_error "Upload failed"
        return 1
    fi
}

auto_categorize_path() {
    local file_path="$1"
    local extension="${file_path##*.}"
    local basename=$(basename "$file_path")
    
    # Document types
    case "${extension,,}" in
        pdf|doc|docx|txt|odt|rtf)
            echo "$DOCUMENTS_DIR"
            ;;
        jpg|jpeg|png|gif|bmp|svg|mp4|avi|mkv|mov|mp3|wav|flac)
            echo "$MEDIA_DIR"
            ;;
        sh|py|js|html|css|php|java|cpp|c|h)
            echo "$SCRIPTS_DIR"
            ;;
        tar|gz|zip|rar|7z|bak)
            echo "$BACKUPS_DIR"
            ;;
        *)
            # Check if it's a project directory
            if [ -d "$file_path" ]; then
                if [ -f "$file_path/.git/config" ] || [ -f "$file_path/package.json" ] || [ -f "$file_path/Cargo.toml" ]; then
                    echo "$PROJECTS_DIR"
                else
                    echo ""
                fi
            else
                echo ""
            fi
            ;;
    esac
}

sync_directories() {
    local local_dir="$1"
    local remote_dir="$2"
    local direction="${3:-to}"  # "to" for local->remote, "from" for remote->local
    
    print_progress "Syncing directories..."
    
    # Build rclone command
    local rclone_opts=()
    
    if [ "$VERIFY_TRANSFERS" = "true" ]; then
        rclone_opts+=("--checksum")
    fi
    
    if [ -n "$BANDWIDTH_LIMIT" ]; then
        rclone_opts+=("--bwlimit" "$BANDWIDTH_LIMIT")
    fi
    
    if [ "$EXCLUDE_HIDDEN" = "true" ]; then
        rclone_opts+=("--exclude" ".*")
    fi
    
    case "$direction" in
        "to")
            print_progress "Syncing $local_dir -> googledrive:$remote_dir"
            rclone sync "$local_dir" "googledrive:$remote_dir" "${rclone_opts[@]}" --progress
            ;;
        "from")
            print_progress "Syncing googledrive:$remote_dir -> $local_dir"
            rclone sync "googledrive:$remote_dir" "$local_dir" "${rclone_opts[@]}" --progress
            ;;
        "bidirectional")
            print_progress "Bidirectional sync between $local_dir and googledrive:$remote_dir"
            rclone bisync "$local_dir" "googledrive:$remote_dir" "${rclone_opts[@]}" --progress
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "✓ Sync completed successfully"
        log_message "INFO" "Synced: $local_dir <-> googledrive:$remote_dir ($direction)"
    else
        print_error "Sync failed"
        return 1
    fi
}

# ============================================================================
# BACKUP OPERATIONS
# ============================================================================

create_smart_backup() {
    print_progress "Creating smart backup..."
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local temp_backup_dir="/tmp/$backup_name"
    
    mkdir -p "$temp_backup_dir"
    
    # Intelligent backup suggestions based on common directories
    local backup_candidates=(
        "$HOME/Documents"
        "$HOME/Downloads"
        "$HOME/Desktop"
        "$HOME/Pictures"
        "$HOME/Videos"
        "$HOME/Music"
        "$HOME/.ssh"
        "$HOME/.config"
        "$HOME/scripts"
        "$HOME/projects"
    )
    
    print_status "Analyzing directories for backup..."
    
    for dir in "${backup_candidates[@]}"; do
        if [ -d "$dir" ] && [ "$(find "$dir" -type f | wc -l)" -gt 0 ]; then
            local dir_size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            print_status "Found: $dir ($dir_size)"
            
            read -p "Include $dir in backup? (y/n): " include_dir
            if [[ $include_dir =~ ^[Yy]$ ]]; then
                print_progress "Adding $(basename "$dir") to backup..."
                
                if [ "$BACKUP_COMPRESSION" = "true" ]; then
                    tar -czf "$temp_backup_dir/$(basename "$dir").tar.gz" -C "$(dirname "$dir")" "$(basename "$dir")"
                else
                    cp -r "$dir" "$temp_backup_dir/"
                fi
            fi
        fi
    done
    
    # Upload backup to Google Drive
    if [ "$(find "$temp_backup_dir" -type f | wc -l)" -gt 0 ]; then
        print_progress "Uploading backup to Google Drive..."
        upload_file "$temp_backup_dir" "$BACKUPS_DIR/$backup_name"
        
        # Local backup copy
        cp -r "$temp_backup_dir" "$BACKUP_DIR/"
        
        print_status "✓ Smart backup completed: $backup_name"
    else
        print_warning "No files selected for backup"
    fi
    
    # Cleanup
    rm -rf "$temp_backup_dir"
}

cleanup_old_backups() {
    print_progress "Cleaning up old backups..."
    
    # Clean local backups
    find "$BACKUP_DIR" -name "backup_*" -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} \;
    
    # Clean remote backups (if configured)
    if [ "$BACKUP_RETENTION_DAYS" -gt 0 ]; then
        local cutoff_date=$(date -d "$BACKUP_RETENTION_DAYS days ago" +%Y%m%d)
        
        # List and remove old backups from Google Drive
        rclone lsf "googledrive:$BACKUPS_DIR" | while read backup; do
            if [[ $backup =~ backup_([0-9]{8})_ ]]; then
                local backup_date="${BASH_REMATCH[1]}"
                if [ "$backup_date" -lt "$cutoff_date" ]; then
                    print_progress "Removing old backup: $backup"
                    rclone delete "googledrive:$BACKUPS_DIR/$backup"
                fi
            fi
        done
    fi
    
    print_status "✓ Backup cleanup completed"
}

# ============================================================================
# STATUS AND MONITORING
# ============================================================================

check_status() {
    print_banner
    
    # Check rclone
    if command -v rclone &> /dev/null; then
        print_status "✓ rclone is installed ($(rclone version | head -1))"
    else
        print_error "✗ rclone is not installed"
    fi
    
    # Check Google Drive configuration
    if rclone listremotes | grep -q "^googledrive:$"; then
        print_status "✓ Google Drive remote configured"
        
        # Test connection
        if rclone lsd googledrive: > /dev/null 2>&1; then
            print_status "✓ Google Drive connection working"
        else
            print_warning "⚠ Google Drive connection failed"
        fi
    else
        print_error "✗ Google Drive remote not configured"
    fi
    
    # Check mount status
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        print_status "✓ Google Drive mounted at $MOUNT_POINT"
        
        # Show usage
        local usage=$(df -h "$MOUNT_POINT" 2>/dev/null | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')
        if [ -n "$usage" ]; then
            print_status "  Storage: $usage"
        fi
    else
        print_warning "⚠ Google Drive not mounted"
    fi
    
    # Show configuration
    print_status "Configuration:"
    echo "  Config file: $CONFIG_FILE"
    echo "  Log file: $LOG_FILE"
    echo "  Mount point: $MOUNT_POINT"
    echo "  Backup directory: $BACKUP_DIR"
    
    # Show recent activity
    if [ -f "$LOG_FILE" ]; then
        print_status "Recent activity:"
        tail -5 "$LOG_FILE" | while read line; do
            echo "  $line"
        done
    fi
}

# ============================================================================
# GUI INTEGRATION
# ============================================================================

create_gui_frontend() {
    print_progress "Creating Python GUI frontend..."
    
    cat > "$SCRIPT_DIR/gdrive_gui.py" << 'EOF'
#!/usr/bin/env python3
"""
Google Drive Manager GUI v2.0
Modern Python GUI frontend for the Google Drive Manager
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import time
import json
from pathlib import Path
import queue

class GoogleDriveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Manager v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.script_path = str(Path(__file__).parent / "gdrive-manager.sh")
        self.mount_point = str(Path.home() / "GoogleDrive")
        self.process_queue = queue.Queue()
        self.current_process = None
        
        # Create main interface
        self.create_main_interface()
        
        # Start status monitoring
        self.start_status_monitoring()
        
        # Initial status check
        self.refresh_status()
        
    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
        # Configure button styles
        style.configure('Action.TButton', font=('Arial', 10))
        style.configure('Primary.TButton', font=('Arial', 10, 'bold'))
        
    def create_main_interface(self):
        """Create the main GUI interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_files_tab()
        self.create_sync_tab()
        self.create_backup_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Create status bar
        self.create_status_bar()
        
    def create_dashboard_tab(self):
        """Create dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Title
        title_label = ttk.Label(dashboard_frame, text="Google Drive Manager", 
                               style='Title.TLabel')
        title_label.pack(pady=20)
        
        # Status section
        status_frame = ttk.LabelFrame(dashboard_frame, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_text = tk.Text(status_frame, height=8, width=80)
        status_scroll = ttk.Scrollbar(status_frame, orient='vertical', 
                                     command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)
        
        self.status_text.pack(side='left', fill='both', expand=True)
        status_scroll.pack(side='right', fill='y')
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=20, pady=10)
        
        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack()
        
        # Action buttons
        ttk.Button(actions_grid, text="Setup Google Drive", 
                  command=self.setup_drive, style='Primary.TButton').grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(actions_grid, text="Mount Drive", 
                  command=self.mount_drive).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(actions_grid, text="Unmount Drive", 
                  command=self.unmount_drive).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(actions_grid, text="Refresh Status", 
                  command=self.refresh_status).grid(row=0, column=3, padx=5, pady=5)
        
    def create_files_tab(self):
        """Create files management tab"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Files")
        
        # Upload section
        upload_frame = ttk.LabelFrame(files_frame, text="Upload Files", padding=10)
        upload_frame.pack(fill='x', padx=20, pady=10)
        
        upload_buttons = ttk.Frame(upload_frame)
        upload_buttons.pack()
        
        ttk.Button(upload_buttons, text="Upload File", 
                  command=self.upload_file).pack(side='left', padx=5)
        ttk.Button(upload_buttons, text="Upload Folder", 
                  command=self.upload_folder).pack(side='left', padx=5)
        
        # File browser
        browser_frame = ttk.LabelFrame(files_frame, text="Google Drive Files", padding=10)
        browser_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview for file listing
        self.file_tree = ttk.Treeview(browser_frame, columns=('Size', 'Modified'), show='tree headings')
        self.file_tree.heading('#0', text='Name')
        self.file_tree.heading('Size', text='Size')
        self.file_tree.heading('Modified', text='Modified')
        
        file_scroll = ttk.Scrollbar(browser_frame, orient='vertical', 
                                   command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scroll.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        file_scroll.pack(side='right', fill='y')
        
    def create_sync_tab(self):
        """Create sync tab"""
        sync_frame = ttk.Frame(self.notebook)
        self.notebook.add(sync_frame, text="Sync")
        
        # Sync configuration
        config_frame = ttk.LabelFrame(sync_frame, text="Sync Configuration", padding=10)
        config_frame.pack(fill='x', padx=20, pady=10)
        
        # Local directory selection
        ttk.Label(config_frame, text="Local Directory:").grid(row=0, column=0, sticky='w', pady=5)
        self.local_dir_var = tk.StringVar()
        local_dir_entry = ttk.Entry(config_frame, textvariable=self.local_dir_var, width=50)
        local_dir_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", 
                  command=self.browse_local_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # Remote directory
        ttk.Label(config_frame, text="Remote Directory:").grid(row=1, column=0, sticky='w', pady=5)
        self.remote_dir_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.remote_dir_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        
        # Sync direction
        ttk.Label(config_frame, text="Sync Direction:").grid(row=2, column=0, sticky='w', pady=5)
        self.sync_direction_var = tk.StringVar(value="to")
        direction_frame = ttk.Frame(config_frame)
        direction_frame.grid(row=2, column=1, sticky='w', pady=5)
        
        ttk.Radiobutton(direction_frame, text="Local → Remote", variable=self.sync_direction_var, 
                       value="to").pack(side='left', padx=5)
        ttk.Radiobutton(direction_frame, text="Remote → Local", variable=self.sync_direction_var, 
                       value="from").pack(side='left', padx=5)
        ttk.Radiobutton(direction_frame, text="Bidirectional", variable=self.sync_direction_var, 
                       value="bidirectional").pack(side='left', padx=5)
        
        # Sync button
        ttk.Button(config_frame, text="Start Sync", command=self.start_sync, 
                  style='Primary.TButton').grid(row=3, column=1, pady=10)
        
    def create_backup_tab(self):
        """Create backup tab"""
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="Backup")
        
        # Backup controls
        controls_frame = ttk.LabelFrame(backup_frame, text="Backup Controls", padding=10)
        controls_frame.pack(fill='x', padx=20, pady=10)
        
        backup_buttons = ttk.Frame(controls_frame)
        backup_buttons.pack()
        
        ttk.Button(backup_buttons, text="Create Smart Backup", 
                  command=self.create_smart_backup, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(backup_buttons, text="Cleanup Old Backups", 
                  command=self.cleanup_backups).pack(side='left', padx=5)
        
        # Backup history
        history_frame = ttk.LabelFrame(backup_frame, text="Backup History", padding=10)
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.backup_tree = ttk.Treeview(history_frame, columns=('Date', 'Size', 'Status'), show='tree headings')
        self.backup_tree.heading('#0', text='Backup Name')
        self.backup_tree.heading('Date', text='Date')
        self.backup_tree.heading('Size', text='Size')
        self.backup_tree.heading('Status', text='Status')
        
        backup_scroll = ttk.Scrollbar(history_frame, orient='vertical', 
                                     command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scroll.set)
        
        self.backup_tree.pack(side='left', fill='both', expand=True)
        backup_scroll.pack(side='right', fill='y')
        
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Settings will be populated from config file
        # For now, placeholder
        ttk.Label(settings_frame, text="Settings configuration will be added here", 
                 style='Heading.TLabel').pack(pady=20)
        
    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Log viewer
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.log_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Auto-update logs
        self.update_logs()
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side='left', padx=10, pady=5)
        
        self.progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress.pack(side='right', padx=10, pady=5)
        
    def run_script_command(self, command, callback=None):
        """Run script command in background thread"""
        def run_command():
            try:
                self.progress.start()
                self.status_label.config(text=f"Running: {command}")
                
                result = subprocess.run(
                    [self.script_path, command],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                self.progress.stop()
                
                if result.returncode == 0:
                    self.status_label.config(text="Command completed successfully")
                    if callback:
                        self.root.after(0, callback)
                else:
                    self.status_label.config(text="Command failed")
                    messagebox.showerror("Error", f"Command failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.progress.stop()
                self.status_label.config(text="Command timed out")
                messagebox.showerror("Error", "Command timed out")
            except Exception as e:
                self.progress.stop()
                self.status_label.config(text="Command error")
                messagebox.showerror("Error", f"Error running command: {e}")
        
        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()
        
    def setup_drive(self):
        """Setup Google Drive"""
        response = messagebox.askyesno(
            "Setup Google Drive",
            "This will open a browser for Google authentication. Continue?"
        )
        if response:
            self.run_script_command("setup", self.refresh_status)
    
    def mount_drive(self):
        """Mount Google Drive"""
        self.run_script_command("mount", self.refresh_status)
    
    def unmount_drive(self):
        """Unmount Google Drive"""
        self.run_script_command("unmount", self.refresh_status)
    
    def upload_file(self):
        """Upload a single file"""
        file_path = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*")]
        )
        if file_path:
            self.run_script_command(f"upload '{file_path}'")
    
    def upload_folder(self):
        """Upload a folder"""
        folder_path = filedialog.askdirectory(title="Select folder to upload")
        if folder_path:
            self.run_script_command(f"upload '{folder_path}'")
    
    def browse_local_dir(self):
        """Browse for local directory"""
        directory = filedialog.askdirectory(title="Select local directory")
        if directory:
            self.local_dir_var.set(directory)
    
    def start_sync(self):
        """Start synchronization"""
        local_dir = self.local_dir_var.get()
        remote_dir = self.remote_dir_var.get()
        direction = self.sync_direction_var.get()
        
        if not local_dir or not remote_dir:
            messagebox.showerror("Error", "Please specify both local and remote directories")
            return
        
        command = f"sync '{local_dir}' '{remote_dir}' {direction}"
        self.run_script_command(command)
    
    def create_smart_backup(self):
        """Create smart backup"""
        self.run_script_command("backup")
    
    def cleanup_backups(self):
        """Cleanup old backups"""
        response = messagebox.askyesno(
            "Cleanup Backups",
            "This will remove old backups. Continue?"
        )
        if response:
            self.run_script_command("cleanup")
    
    def refresh_status(self):
        """Refresh status display"""
        def update_status():
            try:
                result = subprocess.run(
                    [self.script_path, "status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, result.stdout)
                
            except Exception as e:
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, f"Error getting status: {e}")
        
        thread = threading.Thread(target=update_status, daemon=True)
        thread.start()
    
    def update_logs(self):
        """Update log display"""
        try:
            log_file = Path.home() / ".local/share/gdrive-manager/logs" / f"gdrive_{time.strftime('%Y%m%d')}.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = f.read()
                
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, logs)
                self.log_text.see(tk.END)
        except Exception as e:
            pass
        
        # Schedule next update
        self.root.after(5000, self.update_logs)
    
    def start_status_monitoring(self):
        """Start background status monitoring"""
        def monitor():
            while True:
                time.sleep(30)
                self.root.after(0, self.refresh_status)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

def main():
    """Main function"""
    root = tk.Tk()
    app = GoogleDriveManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$SCRIPT_DIR/gdrive_gui.py"
    print_status "Python GUI frontend created: $SCRIPT_DIR/gdrive_gui.py"
}

create_launcher() {
    cat > "$SCRIPT_DIR/launch_gui.sh" << 'EOF'
#!/bin/bash

# Google Drive Manager GUI Launcher
# Ensures Python dependencies and launches GUI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Check tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Installing tkinter..."
    sudo apt install -y python3-tk
fi

# Launch GUI
cd "$SCRIPT_DIR"
python3 gdrive_gui.py
EOF
    
    chmod +x "$SCRIPT_DIR/launch_gui.sh"
    print_status "GUI launcher created: $SCRIPT_DIR/launch_gui.sh"
}

# ============================================================================
# HELP AND DOCUMENTATION
# ============================================================================

show_help() {
    cat << 'EOF'
Google Drive Manager v2.0 - Complete Package
Smart Backup • Auto-Organization • Sync • GUI Integration

USAGE:
    gdrive-manager.sh [COMMAND] [OPTIONS]

COMMANDS:
    setup                   Initial setup and Google Drive configuration
    mount                   Mount Google Drive at ~/GoogleDrive
    unmount                 Unmount Google Drive
    status                  Show current status and configuration
    
    upload <file> [remote]  Upload file or directory to Google Drive
    sync <local> <remote>   Sync directories (bidirectional)
    backup                  Create smart backup with auto-categorization
    
    gui                     Launch Python GUI interface
    help                    Show this help message

FILE OPERATIONS:
    Upload single file:     ./gdrive-manager.sh upload ~/Documents/file.pdf
    Upload with path:       ./gdrive-manager.sh upload ~/Projects Documents/Projects
    Upload directory:       ./gdrive-manager.sh upload ~/Pictures
    
    Sync directories:       ./gdrive-manager.sh sync ~/Documents Documents
    Bidirectional sync:     ./gdrive-manager.sh sync ~/Music Music bidirectional

BACKUP FEATURES:
    - Smart categorization of files by type
    - Compression options for large backups
    - Retention policy for old backups
    - Intelligent backup suggestions

GUI INTERFACE:
    Launch GUI:            ./gdrive-manager.sh gui
    Or run directly:       ./gdrive_gui.py

CONFIGURATION:
    Config file:           ~/.config/gdrive-manager/config.conf
    Log files:             ~/.local/share/gdrive-manager/logs/
    Local backups:         ~/.local/share/gdrive-manager/backups/

EXAMPLES:
    # Initial setup
    ./gdrive-manager.sh setup
    
    # Quick backup
    ./gdrive-manager.sh backup
    
    # Upload and organize
    ./gdrive-manager.sh upload ~/Downloads/document.pdf Documents
    
    # Launch GUI
    ./gdrive-manager.sh gui

For more information, visit: https://github.com/username/gdrive-manager
EOF
}

# ============================================================================
# MAIN COMMAND DISPATCHER
# ============================================================================

main() {
    # Initialize logging
    log_message "INFO" "Google Drive Manager v$VERSION started"
    log_message "INFO" "Command: ${*:-'(no arguments)'}"
    
    case "${1:-}" in
        setup)
            setup_gdrive
            ;;
        mount)
            check_rclone
            load_config
            mount_gdrive
            ;;
        unmount)
            unmount_gdrive
            ;;
        upload)
            if [[ -z "${2:-}" ]]; then
                print_error "Please specify a file to upload"
                exit 1
            fi
            check_rclone
            load_config
            upload_file "$2" "${3:-}"
            ;;
        sync)
            if [[ -z "${2:-}" || -z "${3:-}" ]]; then
                print_error "Please specify local and remote directories"
                exit 1
            fi
            check_rclone
            load_config
            sync_directories "$2" "$3" "${4:-to}"
            ;;
        backup)
            check_rclone
            load_config
            create_smart_backup
            ;;
        cleanup)
            load_config
            cleanup_old_backups
            ;;
        status)
            check_status
            ;;
        gui)
            # Create GUI if it doesn't exist
            if [ ! -f "$SCRIPT_DIR/gdrive_gui.py" ]; then
                create_gui_frontend
                create_launcher
            fi
            python3 "$SCRIPT_DIR/gdrive_gui.py"
            ;;
        create-gui)
            create_gui_frontend
            create_launcher
            print_status "GUI components created successfully!"
            print_status "Launch with: $0 gui"
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_banner
            echo "Use '$0 help' for usage information"
            echo "Quick start: '$0 setup'"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    # Log completion
    log_message "INFO" "Google Drive Manager completed"
}

# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

# Run main function
main "$@"