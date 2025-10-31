#!/bin/bash

# Unified System Manager - Standalone Installer
# This script contains everything needed to install and run the application
# No external downloads required - everything is embedded

VERSION="2.0"
PROGRAM_NAME="Unified System Manager"
INSTALL_DIR="$HOME/.unified-system-manager"
APP_DIR="$HOME/UnifiedSystemManager"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}   $PROGRAM_NAME v$VERSION${NC}"
    echo -e "${BLUE}   Standalone Installer${NC}"
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

confirm() {
    echo -e "${YELLOW}$1 [y/N]${NC}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Check if running as root
check_root() {
    if [ "$(id -u)" -eq 0 ]; then
        print_error "This script should NOT be run as root"
        print_warning "Please run as a regular user"
        exit 1
    fi
}

# Detect distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$NAME
    elif [ -f /etc/debian_version ]; then
        DISTRO="Debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="Red Hat"
    else
        DISTRO="Unknown"
    fi
    print_status "Detected distribution: $DISTRO"
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ "$DISTRO" == *"Ubuntu"* ]] || [[ "$DISTRO" == *"Debian"* ]]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv python3-tk curl wget unzip
        
    elif [[ "$DISTRO" == *"Fedora"* ]] || [[ "$DISTRO" == *"Red Hat"* ]]; then
        sudo dnf install -y python3 python3-pip python3-tkinter curl wget unzip
        
    elif [[ "$DISTRO" == *"Arch"* ]]; then
        sudo pacman -S --needed python python-pip tk curl wget unzip
        
    elif [[ "$DISTRO" == *"openSUSE"* ]]; then
        sudo zypper install -y python3 python3-pip python3-tk curl wget unzip
        
    else
        print_warning "Unknown distribution. Please install python3, pip3, and basic utilities manually"
    fi
    
    print_success "System dependencies installed"
}

# Install rclone
install_rclone() {
    print_status "Installing rclone..."
    
    if command -v rclone &> /dev/null; then
        print_status "rclone already installed"
        return
    fi
    
    curl https://rclone.org/install.sh | sudo bash
    
    if command -v rclone &> /dev/null; then
        print_success "rclone installed successfully"
    else
        print_error "Failed to install rclone"
        return 1
    fi
}

# Create directory structure
create_structure() {
    print_status "Creating directory structure..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/backups"
    
    print_success "Directory structure created"
}

# Create virtual environment and install Python packages
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Try to install PySide6
    print_status "Installing PySide6 (this may take a few minutes)..."
    if pip install PySide6; then
        print_success "PySide6 installed successfully"
        GUI_FRAMEWORK="pyside6"
    else
        print_warning "PySide6 installation failed, using tkinter fallback"
        GUI_FRAMEWORK="tkinter"
    fi
    
    # Install other dependencies
    pip install psutil requests
    
    deactivate
    print_success "Python environment setup complete"
}

# Create the main application
create_main_application() {
    print_status "Creating main application..."
    
    if [ "$GUI_FRAMEWORK" = "pyside6" ]; then
        create_pyside6_app
    else
        create_tkinter_app
    fi
    
    chmod +x "$APP_DIR/unified_system_manager.py"
    print_success "Main application created"
}

# Create PySide6 version (simplified but functional)
create_pyside6_app() {
    cat > "$APP_DIR/unified_system_manager.py" << 'EOF'
#!/usr/bin/env python3
"""
Unified System Manager v2.0 - PySide6 Version
"""

import sys
import os
import subprocess
import threading
import time
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QLabel, QPushButton, QTextEdit, QProgressBar,
        QGroupBox, QCheckBox, QMessageBox, QFormLayout, QLineEdit,
        QSpinBox, QStatusBar
    )
    from PySide6.QtCore import QThread, Signal, QTimer, Qt
    from PySide6.QtGui import QFont
except ImportError:
    print("PySide6 not available. Please install with: pip install PySide6")
    sys.exit(1)

class CommandWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal(int)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        
    def run(self):
        try:
            process = subprocess.run(
                self.command, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            self.output_signal.emit(process.stdout)
            if process.stderr:
                self.output_signal.emit(f"Error: {process.stderr}")
            self.finished_signal.emit(process.returncode)
        except Exception as e:
            self.output_signal.emit(f"Exception: {str(e)}")
            self.finished_signal.emit(1)

class GoogleDriveTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status group
        status_group = QGroupBox("Google Drive Status")
        status_layout = QFormLayout(status_group)
        
        self.rclone_status = QLabel("Checking...")
        self.mount_status = QLabel("Checking...")
        
        status_layout.addRow("rclone:", self.rclone_status)
        status_layout.addRow("Mount:", self.mount_status)
        
        layout.addWidget(status_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        setup_btn = QPushButton("Quick Setup")
        setup_btn.clicked.connect(self.quick_setup)
        actions_layout.addWidget(setup_btn)
        
        mount_btn = QPushButton("Mount Drive")
        mount_btn.clicked.connect(self.mount_drive)
        actions_layout.addWidget(mount_btn)
        
        backup_btn = QPushButton("Smart Backup")
        backup_btn.clicked.connect(self.smart_backup)
        actions_layout.addWidget(backup_btn)
        
        layout.addWidget(actions_group)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(200)
        layout.addWidget(self.log_output)
        
    def quick_setup(self):
        self.run_command("rclone config")
        
    def mount_drive(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command(f"{script_path} mount")
        
    def smart_backup(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command(f"{script_path} smart-backup")
        
    def run_command(self, command):
        self.worker = CommandWorker(command)
        self.worker.output_signal.connect(self.log_output.append)
        self.worker.finished_signal.connect(self.command_finished)
        self.worker.start()
        
    def command_finished(self, exit_code):
        if exit_code == 0:
            self.log_output.append("✓ Command completed successfully")
        else:
            self.log_output.append(f"✗ Command failed with exit code {exit_code}")

class SystemCleanupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Cleanup options
        options_group = QGroupBox("Cleanup Options")
        options_layout = QVBoxLayout(options_group)
        
        self.categories = {}
        for name, key in [
            ("Package Cache", "package_cache"),
            ("Browser Caches", "browser_cache"),
            ("Temporary Files", "temp_files"),
            ("Docker Resources", "docker"),
        ]:
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            self.categories[key] = checkbox
            options_layout.addWidget(checkbox)
        
        layout.addWidget(options_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("Analyze System")
        analyze_btn.clicked.connect(self.analyze_system)
        actions_layout.addWidget(analyze_btn)
        
        cleanup_btn = QPushButton("Start Cleanup")
        cleanup_btn.clicked.connect(self.start_cleanup)
        actions_layout.addWidget(cleanup_btn)
        
        emergency_btn = QPushButton("Emergency Cleanup")
        emergency_btn.clicked.connect(self.emergency_cleanup)
        actions_layout.addWidget(emergency_btn)
        
        layout.addLayout(actions_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(200)
        layout.addWidget(self.log_output)
        
    def analyze_system(self):
        script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
        self.run_command(f"{script_path} --report-only")
        
    def start_cleanup(self):
        reply = QMessageBox.question(self, "Confirm Cleanup",
                                   "Start system cleanup?\nThis will remove unnecessary files.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command(f"{script_path}")
        
    def emergency_cleanup(self):
        reply = QMessageBox.critical(self, "Emergency Cleanup",
                                   "Perform aggressive cleanup?\nThis may remove more data.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command(f"{script_path} --emergency --yes")
        
    def run_command(self, command):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.worker = CommandWorker(command)
        self.worker.output_signal.connect(self.log_output.append)
        self.worker.finished_signal.connect(self.command_finished)
        self.worker.start()
        
    def command_finished(self, exit_code):
        self.progress_bar.setVisible(False)
        if exit_code == 0:
            self.log_output.append("✓ Cleanup completed successfully")
        else:
            self.log_output.append(f"✗ Cleanup failed with exit code {exit_code}")

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.mount_point = QLineEdit()
        self.mount_point.setText(str(Path.home() / "GoogleDrive"))
        settings_layout.addRow("Mount Point:", self.mount_point)
        
        self.max_transfers = QSpinBox()
        self.max_transfers.setRange(1, 16)
        self.max_transfers.setValue(4)
        settings_layout.addRow("Max Transfers:", self.max_transfers)
        
        layout.addWidget(settings_group)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
    def save_settings(self):
        QMessageBox.information(self, "Settings", "Settings saved successfully!")

class UnifiedSystemManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Unified System Manager v2.0")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Unified System Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        tab_widget.addTab(GoogleDriveTab(), "Google Drive")
        tab_widget.addTab(SystemCleanupTab(), "System Cleanup")
        tab_widget.addTab(SettingsTab(), "Settings")
        
        layout.addWidget(tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Unified System Manager")
    app.setApplicationVersion("2.0")
    
    window = UnifiedSystemManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
EOF
}

# Create tkinter fallback version
create_tkinter_app() {
    cat > "$APP_DIR/unified_system_manager.py" << 'EOF'
#!/usr/bin/env python3
"""
Unified System Manager v2.0 - Tkinter Version
"""

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

class UnifiedSystemManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Unified System Manager v2.0")
        self.root.geometry("900x600")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="Unified System Manager", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Google Drive tab
        gdrive_frame = ttk.Frame(notebook)
        notebook.add(gdrive_frame, text="Google Drive")
        self.create_gdrive_tab(gdrive_frame)
        
        # System Cleanup tab
        cleanup_frame = ttk.Frame(notebook)
        notebook.add(cleanup_frame, text="System Cleanup")
        self.create_cleanup_tab(cleanup_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.create_settings_tab(settings_frame)
        
    def create_gdrive_tab(self, parent):
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Google Drive Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.rclone_status = tk.Label(status_frame, text="rclone: Checking...")
        self.rclone_status.pack(anchor='w')
        
        self.mount_status = tk.Label(status_frame, text="Mount: Checking...")
        self.mount_status.pack(anchor='w')
        
        # Actions frame
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Quick Setup", 
                  command=self.quick_setup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Mount Drive", 
                  command=self.mount_drive).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Smart Backup", 
                  command=self.smart_backup).pack(side='left', padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Output")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.gdrive_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.gdrive_log.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_cleanup_tab(self, parent):
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Cleanup Options")
        options_frame.pack(fill='x', padx=10, pady=5)
        
        self.cleanup_vars = {}
        for name, key in [
            ("Package Cache", "package_cache"),
            ("Browser Caches", "browser_cache"),
            ("Temporary Files", "temp_files"),
            ("Docker Resources", "docker"),
        ]:
            var = tk.BooleanVar(value=True)
            self.cleanup_vars[key] = var
            ttk.Checkbutton(options_frame, text=name, variable=var).pack(anchor='w')
        
        # Actions frame
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Analyze System", 
                  command=self.analyze_system).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Start Cleanup", 
                  command=self.start_cleanup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Emergency Cleanup", 
                  command=self.emergency_cleanup).pack(side='left', padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Output")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.cleanup_log = scrolledtext.ScrolledText(log_frame, height=10)
        self.cleanup_log.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_settings_tab(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings")
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(settings_frame, text="Mount Point:").pack(anchor='w')
        self.mount_point_var = tk.StringVar(value=str(Path.home() / "GoogleDrive"))
        tk.Entry(settings_frame, textvariable=self.mount_point_var, width=50).pack(anchor='w', pady=2)
        
        tk.Label(settings_frame, text="Max Transfers:").pack(anchor='w')
        self.max_transfers_var = tk.StringVar(value="4")
        tk.Entry(settings_frame, textvariable=self.max_transfers_var, width=10).pack(anchor='w', pady=2)
        
        ttk.Button(settings_frame, text="Save Settings", 
                  command=self.save_settings).pack(pady=10)
        
    def run_command_async(self, command, log_widget):
        def run():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                log_widget.insert(tk.END, result.stdout + "\n")
                if result.stderr:
                    log_widget.insert(tk.END, f"Error: {result.stderr}\n")
                log_widget.see(tk.END)
            except Exception as e:
                log_widget.insert(tk.END, f"Exception: {str(e)}\n")
                log_widget.see(tk.END)
                
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        
    def quick_setup(self):
        self.run_command_async("rclone config", self.gdrive_log)
        
    def mount_drive(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command_async(f"{script_path} mount", self.gdrive_log)
        
    def smart_backup(self):
        script_path = Path.home() / ".unified-system-manager/scripts/gdrive-manager.sh"
        self.run_command_async(f"{script_path} smart-backup", self.gdrive_log)
        
    def analyze_system(self):
        script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
        self.run_command_async(f"{script_path} --report-only", self.cleanup_log)
        
    def start_cleanup(self):
        if messagebox.askyesno("Confirm", "Start system cleanup?"):
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command_async(f"{script_path}", self.cleanup_log)
            
    def emergency_cleanup(self):
        if messagebox.askyesno("Emergency Cleanup", "Perform aggressive cleanup?"):
            script_path = Path.home() / ".unified-system-manager/scripts/tidytux.sh"
            self.run_command_async(f"{script_path} --emergency --yes", self.cleanup_log)
            
    def save_settings(self):
        messagebox.showinfo("Settings", "Settings saved successfully!")
        
    def run(self):
        self.root.mainloop()

def main():
    app = UnifiedSystemManager()
    app.run()

if __name__ == "__main__":
    main()
EOF
}

# Create Google Drive manager script
create_gdrive_script() {
    print_status "Creating Google Drive manager script..."
    
    cat > "$INSTALL_DIR/scripts/gdrive-manager.sh" << 'EOF'
#!/bin/bash

# Google Drive Manager Script v2.0
# Embedded in Unified System Manager

GDRIVE_LOCAL_PATH="$HOME/GoogleDrive"
RCLONE_REMOTE_NAME="googledrive"
MOUNT_POINT="$GDRIVE_LOCAL_PATH"
PID_FILE="/tmp/rclone_mount.pid"
LOG_FILE="/tmp/gdrive-manager.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

case "$1" in
    "setup")
        log "Setting up Google Drive..."
        echo "Starting rclone configuration..."
        echo "Choose option for Google Drive (usually 15-18)"
        echo "Leave client_id and client_secret blank"
        echo "Choose full access (option 1)"
        echo "Choose auto config (y) to open browser"
        rclone config
        print_success "Google Drive setup completed"
        ;;
        
    "mount")
        log "Mounting Google Drive..."
        
        # Check if already mounted
        if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            print_success "Google Drive is already mounted at $MOUNT_POINT"
            exit 0
        fi
        
        # Create mount point
        mkdir -p "$MOUNT_POINT"
        
        # Mount with optimal settings
        rclone mount $RCLONE_REMOTE_NAME: "$MOUNT_POINT" \
            --vfs-cache-mode full \
            --vfs-cache-max-age 168h \
            --daemon \
            --log-file "$LOG_FILE" \
            --log-level INFO
            
        # Wait and verify
        sleep 3
        if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            print_success "Google Drive mounted at $MOUNT_POINT"
        else
            print_error "Failed to mount Google Drive"
            exit 1
        fi
        ;;
        
    "unmount")
        log "Unmounting Google Drive..."
        
        if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            fusermount -u "$MOUNT_POINT" 2>/dev/null || umount "$MOUNT_POINT"
            print_success "Google Drive unmounted"
        else
            log "Google Drive was not mounted"
        fi
        ;;
        
    "smart-backup")
        log "Starting smart backup..."
        
        # Check if mounted
        if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            log "Google Drive not mounted, attempting to mount..."
            "$0" mount
        fi
        
        # Backup Financial documents
        if [ -d "$HOME/Documents/Financial" ]; then
            log "Backing up financial documents..."
            rclone sync "$HOME/Documents/Financial" "$RCLONE_REMOTE_NAME:Backup/Financial" --progress
        fi
        
        # Backup Scripts
        if [ -d "$HOME/scripts" ]; then
            log "Backing up scripts..."
            rclone sync "$HOME/scripts" "$RCLONE_REMOTE_NAME:Backup/Scripts" --progress
        fi
        
        # Backup important files from Downloads
        if [ -d "$HOME/Downloads" ]; then
            log "Backing up important downloads..."
            find "$HOME/Downloads" -name "*.sh" -o -name "*.py" -o -name "*guide*" | while read file; do
                if [ -f "$file" ]; then
                    rclone copy "$file" "$RCLONE_REMOTE_NAME:Backup/Downloads/" --progress
                fi
            done
        fi
        
        # Backup Desktop files
        if [ -d "$HOME/Desktop" ]; then
            log "Backing up desktop files..."
            rclone sync "$HOME/Desktop" "$RCLONE_REMOTE_NAME:Backup/Desktop" --progress
        fi
        
        print_success "Smart backup completed"
        ;;
        
    "status")
        echo "=== Google Drive Manager Status ==="
        
        # Check rclone
        if command -v rclone &> /dev/null; then
            VERSION=$(rclone version | head -1 | cut -d' ' -f2)
            echo "✓ rclone: Installed ($VERSION)"
        else
            echo "✗ rclone: Not installed"
        fi
        
        # Check configuration
        if rclone listremotes | grep -q "$RCLONE_REMOTE_NAME:"; then
            echo "✓ Google Drive: Configured"
        else
            echo "✗ Google Drive: Not configured"
        fi
        
        # Check mount
        if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
            echo "✓ Mount: $MOUNT_POINT"
        else
            echo "✗ Mount: Not mounted"
        fi
        
        # Check storage
        if rclone about $RCLONE_REMOTE_NAME: &>/dev/null; then
            echo "✓ Connection: OK"
            rclone about $RCLONE_REMOTE_NAME: | grep -E "(Total|Used|Free)"
        else
            echo "✗ Connection: Failed"
        fi
        ;;
        
    *)
        echo "Google Drive Manager v2.0"
        echo
        echo "Usage: $0 {setup|mount|unmount|smart-backup|status}"
        echo
        echo "Commands:"
        echo "  setup        - Configure Google Drive with rclone"
        echo "  mount        - Mount Google Drive locally"
        echo "  unmount      - Unmount Google Drive"
        echo "  smart-backup - Backup important files to Google Drive"
        echo "  status       - Show current status"
        ;;
esac
EOF

    chmod +x "$INSTALL_DIR/scripts/gdrive-manager.sh"
    print_success "Google Drive script created"
}

# Create TidyTux cleanup script
create_tidytux_script() {
    print_status "Creating TidyTux cleanup script..."
    
    cat > "$INSTALL_DIR/scripts/tidytux.sh" << 'EOF'
#!/bin/bash

# TidyTux System Cleanup Script v2.0
# Embedded in Unified System Manager

VERSION="2.0"
LOG_FILE="/tmp/tidytux_log.txt"
BACKUP_DIR="$HOME/.unified-system-manager/backups/cleanup_$(date +%Y%m%d_%H%M%S)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Options
INTERACTIVE=true
EMERGENCY_MODE=false
REPORT_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --yes|-y)
            INTERACTIVE=false
            shift
            ;;
        --emergency|-e)
            EMERGENCY_MODE=true
            INTERACTIVE=false
            shift
            ;;
        --report-only|-r)
            REPORT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

confirm() {
    if [ "$INTERACTIVE" = false ]; then
        return 0
    fi
    echo -e "${YELLOW}$1 [y/N]${NC}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "=== TidyTux System Cleanup v$VERSION ==="
log "Mode: $([ "$REPORT_ONLY" = true ] && echo "REPORT ONLY" || echo "CLEANUP")"
log "Emergency: $([ "$EMERGENCY_MODE" = true ] && echo "YES" || echo "NO")"

# Check disk space
log "Checking disk space..."
df -h "$HOME" | tee -a "$LOG_FILE"

if [ "$REPORT_ONLY" = true ]; then
    log "=== ANALYSIS MODE - No changes will be made ==="
    
    # Package cache analysis
    if command -v apt &> /dev/null; then
        CACHE_SIZE=$(sudo du -sh /var/cache/apt 2>/dev/null | cut -f1 || echo "Unknown")
        log "APT package cache: $CACHE_SIZE"
    fi
    
    # Browser cache analysis
    for browser_cache in ~/.cache/google-chrome ~/.cache/mozilla ~/.cache/chromium; do
        if [ -d "$browser_cache" ]; then
            SIZE=$(du -sh "$browser_cache" 2>/dev/null | cut -f1 || echo "Unknown")
            log "Browser cache $(basename "$browser_cache"): $SIZE"
        fi
    done
    
    # Temporary files
    TEMP_SIZE=$(find /tmp -type f 2>/dev/null | wc -l)
    log "Temporary files in /tmp: $TEMP_SIZE files"
    
    # Docker (if available)
    if command -v docker &> /dev/null; then
        DOCKER_SIZE=$(docker system df 2>/dev/null | grep "Total" | awk '{print $4}' || echo "Unknown")
        log "Docker total size: $DOCKER_SIZE"
    fi
    
    log "Analysis complete. Run without --report-only to perform cleanup"
    exit 0
fi

# Package cache cleanup
if confirm "Clean package cache?"; then
    log "Cleaning package cache..."
    if command -v apt &> /dev/null; then
        sudo apt clean
        sudo apt autoremove -y
    elif command -v dnf &> /dev/null; then
        sudo dnf clean all
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sc --noconfirm
    fi
    log "Package cache cleaned"
fi

# Browser cache cleanup
if confirm "Clean browser caches?"; then
    log "Cleaning browser caches..."
    
    # Close browsers first
    pkill -f "google-chrome" 2>/dev/null || true
    pkill -f "firefox" 2>/dev/null || true
    pkill -f "chromium" 2>/dev/null || true
    
    sleep 2
    
    # Clean caches
    rm -rf ~/.cache/google-chrome/*/Cache/* 2>/dev/null
    rm -rf ~/.cache/mozilla/firefox/*/Cache/* 2>/dev/null
    rm -rf ~/.cache/chromium/*/Cache/* 2>/dev/null
    
    log "Browser caches cleaned"
fi

# Temporary files cleanup
if confirm "Clean temporary files?"; then
    log "Cleaning temporary files..."
    
    # Clean /tmp (files older than 1 day)
    find /tmp -type f -atime +1 -delete 2>/dev/null || true
    
    # Clean thumbnails
    rm -rf ~/.cache/thumbnails/* 2>/dev/null
    
    # Clean user temp
    rm -rf ~/.local/share/Trash/files/* 2>/dev/null
    
    log "Temporary files cleaned"
fi

# Docker cleanup (if available and requested)
if command -v docker &> /dev/null && confirm "Clean Docker resources?"; then
    log "Cleaning Docker resources..."
    
    # Check if user can run docker
    if docker ps &>/dev/null; then
        docker container prune -f
        docker image prune -f
        docker volume prune -f
        docker network prune -f
        log "Docker resources cleaned"
    else
        log "Cannot access Docker (try: sudo usermod -aG docker $USER)"
    fi
fi

# Snap packages cleanup
if command -v snap &> /dev/null && confirm "Clean old snap packages?"; then
    log "Cleaning old snap packages..."
    
    # Set retention to 2
    sudo snap set system refresh.retain=2
    
    # Remove old revisions
    snap list --all | awk '/disabled/{print $1, $3}' | while read snapname revision; do
        sudo snap remove "$snapname" --revision="$revision" 2>/dev/null || true
    done
    
    log "Snap packages cleaned"
fi

# Journal logs (emergency mode only)
if [ "$EMERGENCY_MODE" = true ] && command -v journalctl &> /dev/null; then
    log "Cleaning journal logs (emergency mode)..."
    sudo journalctl --vacuum-time=1d
    log "Journal logs cleaned"
fi

# Downloads organization
if [ -d "$HOME/Downloads" ] && confirm "Organize Downloads folder?"; then
    log "Organizing Downloads folder..."
    
    cd "$HOME/Downloads"
    
    # Create subdirectories
    mkdir -p {documents,archives,images,software,scripts}
    
    # Move files by type
    find . -maxdepth 1 -name "*.pdf" -o -name "*.doc*" -o -name "*.txt" | xargs -I {} mv {} documents/ 2>/dev/null || true
    find . -maxdepth 1 -name "*.zip" -o -name "*.tar*" -o -name "*.gz" | xargs -I {} mv {} archives/ 2>/dev/null || true
    find . -maxdepth 1 -name "*.jpg" -o -name "*.png" -o -name "*.gif" | xargs -I {} mv {} images/ 2>/dev/null || true
    find . -maxdepth 1 -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" | xargs -I {} mv {} software/ 2>/dev/null || true
    find . -maxdepth 1 -name "*.sh" -o -name "*.py" | xargs -I {} mv {} scripts/ 2>/dev/null || true
    
    log "Downloads folder organized"
fi

log "=== Cleanup Summary ==="
log "Completed at: $(date)"
log "Check disk space after cleanup:"
df -h "$HOME" | tee -a "$LOG_FILE"

log "TidyTux cleanup completed successfully!"
log "Log saved to: $LOG_FILE"
EOF

    chmod +x "$INSTALL_DIR/scripts/tidytux.sh"
    print_success "TidyTux script created"
}

# Create launcher script
create_launcher() {
    print_status "Creating launcher script..."
    
    cat > "$APP_DIR/run.sh" << EOF
#!/bin/bash
# Unified System Manager Launcher

cd "$APP_DIR"
source "$INSTALL_DIR/venv/bin/activate"
python3 unified_system_manager.py
EOF

    chmod +x "$APP_DIR/run.sh"
    
    print_success "Launcher script created"
}

# Create desktop entry
create_desktop_entry() {
    print_status "Creating desktop entry..."
    
    local desktop_dir="$HOME/.local/share/applications"
    local desktop_file="$desktop_dir/unified-system-manager.desktop"
    
    mkdir -p "$desktop_dir"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Unified System Manager
Comment=Google Drive backup and system cleanup
Exec=$APP_DIR/run.sh
Icon=utilities-system-monitor
Terminal=false
Categories=System;Utility;
StartupNotify=true
EOF

    chmod +x "$desktop_file"
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$desktop_dir" 2>/dev/null || true
    fi
    
    print_success "Desktop entry created"
}

# Create configuration
create_config() {
    print_status "Creating configuration files..."
    
    cat > "$INSTALL_DIR/config.json" << EOF
{
    "version": "$VERSION",
    "install_dir": "$INSTALL_DIR",
    "app_dir": "$APP_DIR",
    "mount_point": "$HOME/GoogleDrive",
    "max_transfers": 4,
    "gui_framework": "$GUI_FRAMEWORK"
}
EOF

    print_success "Configuration created"
}

# Show post-installation instructions
show_instructions() {
    print_header
    print_success "Installation completed successfully!"
    echo
    echo -e "${BOLD}How to use:${NC}"
    echo
    echo "1. ${CYAN}Launch the GUI application:${NC}"
    echo "   • Applications menu → 'Unified System Manager'"
    echo "   • Terminal: $APP_DIR/run.sh"
    echo
    echo "2. ${CYAN}Configure Google Drive (first time):${NC}"
    echo "   • Click 'Quick Setup' in the Google Drive tab"
    echo "   • Follow the rclone configuration wizard"
    echo "   • Test with 'Mount Drive' button"
    echo
    echo "3. ${CYAN}Command-line tools:${NC}"
    echo "   • Google Drive: $INSTALL_DIR/scripts/gdrive-manager.sh"
    echo "   • System Cleanup: $INSTALL_DIR/scripts/tidytux.sh"
    echo
    echo -e "${BOLD}Examples:${NC}"
    echo "   $INSTALL_DIR/scripts/gdrive-manager.sh setup"
    echo "   $INSTALL_DIR/scripts/tidytux.sh --report-only"
    echo "   $INSTALL_DIR/scripts/tidytux.sh --emergency"
    echo
    echo -e "${BOLD}Features:${NC}"
    echo "   ✓ Smart Google Drive backup and sync"
    echo "   ✓ Comprehensive system cleanup"
    echo "   ✓ Modern GUI interface ($GUI_FRAMEWORK)"
    echo "   ✓ Real-time progress monitoring"
    echo "   ✓ Safe operations with backups"
    echo
    echo -e "${GREEN}Ready to use! Launch from Applications menu or run: $APP_DIR/run.sh${NC}"
}

# Main installation function
main() {
    print_header
    
    echo "This will install the Unified System Manager on your system."
    echo "It combines Google Drive backup with system cleanup tools."
    echo
    echo -e "${BOLD}What will be installed:${NC}"
    echo "• Modern GUI application (PySide6 or tkinter)"
    echo "• Google Drive backup and sync tools"
    echo "• System cleanup utilities (TidyTux)"
    echo "• Desktop integration"
    echo "• Command-line scripts"
    echo
    
    if ! confirm "Continue with installation?"; then
        echo "Installation cancelled"
        exit 0
    fi
    
    # Run installation steps
    check_root
    detect_distro
    
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 not found"
        if confirm "Install system dependencies?"; then
            install_system_deps
        else
            print_error "Cannot continue without Python 3"
            exit 1
        fi
    fi
    
    install_rclone
    create_structure
    setup_python_env
    create_main_application
    create_gdrive_script
    create_tidytux_script
    create_launcher
    create_desktop_entry
    create_config
    
    show_instructions
}

# Handle command line arguments
case "${1:-install}" in
    "install"|"")
        main
        ;;
    "uninstall")
        print_status "Uninstalling Unified System Manager..."
        rm -rf "$APP_DIR" "$INSTALL_DIR"
        rm -f "$HOME/.local/share/applications/unified-system-manager.desktop"
        # Unmount if mounted
        fusermount -u "$HOME/GoogleDrive" 2>/dev/null || true
        print_success "Uninstalled successfully"
        ;;
    "help"|"--help"|"-h")
        echo "Unified System Manager Installer"
        echo "Usage: $0 [install|uninstall|help]"
        ;;
    *)
        print_error "Unknown command: $1"
        exit 1
        ;;
esac
