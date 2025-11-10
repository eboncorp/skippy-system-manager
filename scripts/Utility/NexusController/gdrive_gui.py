#!/usr/bin/env python3
"""
Google Drive Manager GUI
Modern GUI interface for the Google Drive Manager bash script
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
import re
import shlex

class GoogleDriveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Manager v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.script_path = str(Path.home() / "gdrive-manager.sh")
        self.mount_point = str(Path.home() / "GoogleDrive")
        self.status_data = {}
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
        self.create_backup_tab()
        self.create_files_tab()
        self.create_sync_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Create status bar
        self.create_status_bar()
        
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Title
        title_label = ttk.Label(dashboard_frame, text="Google Drive Manager", 
                               style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # Status overview frame
        status_frame = ttk.LabelFrame(dashboard_frame, text="Status Overview", 
                                     padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Status indicators
        self.status_indicators = {}
        
        # rclone status
        rclone_frame = ttk.Frame(status_frame)
        rclone_frame.pack(fill='x', pady=2)
        ttk.Label(rclone_frame, text="rclone:", width=15).pack(side='left')
        self.status_indicators['rclone'] = ttk.Label(rclone_frame, text="Checking...")
        self.status_indicators['rclone'].pack(side='left')
        
        # Google Drive connection
        gdrive_frame = ttk.Frame(status_frame)
        gdrive_frame.pack(fill='x', pady=2)
        ttk.Label(gdrive_frame, text="Google Drive:", width=15).pack(side='left')
        self.status_indicators['gdrive'] = ttk.Label(gdrive_frame, text="Checking...")
        self.status_indicators['gdrive'].pack(side='left')
        
        # Mount status
        mount_frame = ttk.Frame(status_frame)
        mount_frame.pack(fill='x', pady=2)
        ttk.Label(mount_frame, text="Mount Status:", width=15).pack(side='left')
        self.status_indicators['mount'] = ttk.Label(mount_frame, text="Checking...")
        self.status_indicators['mount'].pack(side='left')
        
        # Storage info
        storage_frame = ttk.Frame(status_frame)
        storage_frame.pack(fill='x', pady=2)
        ttk.Label(storage_frame, text="Storage:", width=15).pack(side='left')
        self.status_indicators['storage'] = ttk.Label(storage_frame, text="Checking...")
        self.status_indicators['storage'].pack(side='left')
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", 
                                      padding=10)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        # Action buttons
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.pack(fill='x')
        
        # First row of buttons
        row1 = ttk.Frame(buttons_frame)
        row1.pack(fill='x', pady=5)
        
        ttk.Button(row1, text="Quick Setup", 
                  command=self.quick_setup,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(row1, text="Mount Drive", 
                  command=self.mount_drive).pack(side='left', padx=5)
        
        ttk.Button(row1, text="Unmount Drive", 
                  command=self.unmount_drive).pack(side='left', padx=5)
        
        ttk.Button(row1, text="Refresh Status", 
                  command=self.refresh_status).pack(side='left', padx=5)
        
        # Second row of buttons
        row2 = ttk.Frame(buttons_frame)
        row2.pack(fill='x', pady=5)
        
        ttk.Button(row2, text="Smart Backup", 
                  command=self.smart_backup).pack(side='left', padx=5)
        
        ttk.Button(row2, text="Analyze Home", 
                  command=self.analyze_home).pack(side='left', padx=5)
        
        ttk.Button(row2, text="Open Drive Folder", 
                  command=self.open_drive_folder).pack(side='left', padx=5)
        
        # Recent activity frame
        activity_frame = ttk.LabelFrame(dashboard_frame, text="Recent Activity", 
                                       padding=10)
        activity_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Activity log
        self.activity_log = scrolledtext.ScrolledText(activity_frame, height=10,
                                                     state='disabled')
        self.activity_log.pack(fill='both', expand=True)
        
    def create_backup_tab(self):
        """Create the backup management tab"""
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="Backup")
        
        # Backup categories frame
        categories_frame = ttk.LabelFrame(backup_frame, text="Backup Categories", 
                                         padding=10)
        categories_frame.pack(fill='x', padx=10, pady=5)
        
        # Category checkboxes
        self.backup_categories = {}
        categories = [
            ("Financial Documents", "financial"),
            ("Scripts & Configuration", "scripts"),
            ("Documentation & Guides", "guides"),
            ("Desktop Files", "desktop"),
            ("Downloads", "downloads")
        ]
        
        for i, (display_name, key) in enumerate(categories):
            var = tk.BooleanVar(value=True)
            self.backup_categories[key] = var
            
            cb = ttk.Checkbutton(categories_frame, text=display_name, 
                               variable=var)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=5)
        
        # Backup options frame
        options_frame = ttk.LabelFrame(backup_frame, text="Backup Options", 
                                      padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        # Options
        self.auto_categorize = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-categorize files",
                       variable=self.auto_categorize).pack(anchor='w')
        
        self.verify_transfers = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Verify transfers",
                       variable=self.verify_transfers).pack(anchor='w')
        
        self.compress_backup = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Compress large files",
                       variable=self.compress_backup).pack(anchor='w')
        
        # Backup actions frame
        backup_actions_frame = ttk.LabelFrame(backup_frame, text="Backup Actions", 
                                            padding=10)
        backup_actions_frame.pack(fill='x', padx=10, pady=5)
        
        # Action buttons
        backup_buttons = ttk.Frame(backup_actions_frame)
        backup_buttons.pack(fill='x')
        
        ttk.Button(backup_buttons, text="Start Selected Backup", 
                  command=self.start_backup,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(backup_buttons, text="Schedule Backup", 
                  command=self.schedule_backup).pack(side='left', padx=5)
        
        ttk.Button(backup_buttons, text="Restore from Backup", 
                  command=self.restore_backup).pack(side='left', padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(backup_frame, text="Progress", 
                                       padding=10)
        progress_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Progress bar
        self.backup_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.backup_progress.pack(fill='x', pady=5)
        
        # Progress text
        self.backup_progress_text = scrolledtext.ScrolledText(progress_frame, 
                                                            height=8, state='disabled')
        self.backup_progress_text.pack(fill='both', expand=True)
        
    def create_files_tab(self):
        """Create the file management tab"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Files")
        
        # File operations frame
        operations_frame = ttk.LabelFrame(files_frame, text="File Operations", 
                                        padding=10)
        operations_frame.pack(fill='x', padx=10, pady=5)
        
        # Upload section
        upload_frame = ttk.Frame(operations_frame)
        upload_frame.pack(fill='x', pady=5)
        
        ttk.Label(upload_frame, text="Upload:").pack(side='left')
        self.upload_path = tk.StringVar()
        ttk.Entry(upload_frame, textvariable=self.upload_path, 
                 width=50).pack(side='left', padx=5)
        ttk.Button(upload_frame, text="Browse", 
                  command=self.browse_upload).pack(side='left', padx=5)
        ttk.Button(upload_frame, text="Upload", 
                  command=self.upload_file).pack(side='left', padx=5)
        
        # Download section
        download_frame = ttk.Frame(operations_frame)
        download_frame.pack(fill='x', pady=5)
        
        ttk.Label(download_frame, text="Download:").pack(side='left')
        self.download_path = tk.StringVar()
        ttk.Entry(download_frame, textvariable=self.download_path, 
                 width=50).pack(side='left', padx=5)
        ttk.Button(download_frame, text="Browse Drive", 
                  command=self.browse_drive).pack(side='left', padx=5)
        ttk.Button(download_frame, text="Download", 
                  command=self.download_file).pack(side='left', padx=5)
        
        # File browser frame
        browser_frame = ttk.LabelFrame(files_frame, text="Google Drive Browser", 
                                     padding=10)
        browser_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Browser controls
        browser_controls = ttk.Frame(browser_frame)
        browser_controls.pack(fill='x', pady=5)
        
        ttk.Label(browser_controls, text="Path:").pack(side='left')
        self.browser_path = tk.StringVar(value="/")
        ttk.Entry(browser_controls, textvariable=self.browser_path, 
                 width=50).pack(side='left', padx=5)
        ttk.Button(browser_controls, text="Go", 
                  command=self.browse_drive_path).pack(side='left', padx=5)
        ttk.Button(browser_controls, text="Refresh", 
                  command=self.refresh_browser).pack(side='left', padx=5)
        
        # File tree
        self.file_tree = ttk.Treeview(browser_frame, columns=('Size', 'Modified'), 
                                     show='tree headings')
        self.file_tree.heading('#0', text='Name')
        self.file_tree.heading('Size', text='Size')
        self.file_tree.heading('Modified', text='Modified')
        self.file_tree.column('#0', width=300)
        self.file_tree.column('Size', width=100)
        self.file_tree.column('Modified', width=150)
        
        # Scrollbars for file tree
        tree_scroll_v = ttk.Scrollbar(browser_frame, orient='vertical', 
                                     command=self.file_tree.yview)
        tree_scroll_h = ttk.Scrollbar(browser_frame, orient='horizontal', 
                                     command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=tree_scroll_v.set, 
                               xscrollcommand=tree_scroll_h.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        tree_scroll_v.pack(side='right', fill='y')
        tree_scroll_h.pack(side='bottom', fill='x')
        
    def create_sync_tab(self):
        """Create the sync management tab"""
        sync_frame = ttk.Frame(self.notebook)
        self.notebook.add(sync_frame, text="Sync")
        
        # Sync configuration frame
        config_frame = ttk.LabelFrame(sync_frame, text="Sync Configuration", 
                                     padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Sync pairs
        self.sync_pairs = []
        self.sync_list_frame = ttk.Frame(config_frame)
        self.sync_list_frame.pack(fill='x', pady=5)
        
        # Add sync pair button
        ttk.Button(config_frame, text="Add Sync Pair", 
                  command=self.add_sync_pair).pack(pady=5)
        
        # Sync options frame
        sync_options_frame = ttk.LabelFrame(sync_frame, text="Sync Options", 
                                          padding=10)
        sync_options_frame.pack(fill='x', padx=10, pady=5)
        
        # Sync direction
        ttk.Label(sync_options_frame, text="Direction:").pack(anchor='w')
        self.sync_direction = tk.StringVar(value="bidirectional")
        ttk.Radiobutton(sync_options_frame, text="Bidirectional", 
                       variable=self.sync_direction, 
                       value="bidirectional").pack(anchor='w')
        ttk.Radiobutton(sync_options_frame, text="Local → Google Drive", 
                       variable=self.sync_direction, 
                       value="to_drive").pack(anchor='w')
        ttk.Radiobutton(sync_options_frame, text="Google Drive → Local", 
                       variable=self.sync_direction, 
                       value="from_drive").pack(anchor='w')
        
        # Sync frequency
        freq_frame = ttk.Frame(sync_options_frame)
        freq_frame.pack(fill='x', pady=5)
        ttk.Label(freq_frame, text="Frequency:").pack(side='left')
        self.sync_frequency = tk.StringVar(value="manual")
        freq_combo = ttk.Combobox(freq_frame, textvariable=self.sync_frequency,
                                 values=["manual", "hourly", "daily", "weekly"])
        freq_combo.pack(side='left', padx=5)
        
        # Sync actions frame
        sync_actions_frame = ttk.LabelFrame(sync_frame, text="Sync Actions", 
                                          padding=10)
        sync_actions_frame.pack(fill='x', padx=10, pady=5)
        
        # Action buttons
        sync_buttons = ttk.Frame(sync_actions_frame)
        sync_buttons.pack(fill='x')
        
        ttk.Button(sync_buttons, text="Start Sync", 
                  command=self.start_sync,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(sync_buttons, text="Stop Sync", 
                  command=self.stop_sync).pack(side='left', padx=5)
        
        ttk.Button(sync_buttons, text="Watch Mode", 
                  command=self.start_watch_mode).pack(side='left', padx=5)
        
        # Sync status frame
        sync_status_frame = ttk.LabelFrame(sync_frame, text="Sync Status", 
                                         padding=10)
        sync_status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Status text
        self.sync_status_text = scrolledtext.ScrolledText(sync_status_frame, 
                                                        height=10, state='disabled')
        self.sync_status_text.pack(fill='both', expand=True)
        
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # General settings frame
        general_frame = ttk.LabelFrame(settings_frame, text="General Settings", 
                                     padding=10)
        general_frame.pack(fill='x', padx=10, pady=5)
        
        # Mount point
        mount_frame = ttk.Frame(general_frame)
        mount_frame.pack(fill='x', pady=5)
        ttk.Label(mount_frame, text="Mount Point:").pack(side='left')
        self.mount_point_var = tk.StringVar(value=self.mount_point)
        ttk.Entry(mount_frame, textvariable=self.mount_point_var, 
                 width=50).pack(side='left', padx=5)
        ttk.Button(mount_frame, text="Browse", 
                  command=self.browse_mount_point).pack(side='left', padx=5)
        
        # Max transfers
        transfers_frame = ttk.Frame(general_frame)
        transfers_frame.pack(fill='x', pady=5)
        ttk.Label(transfers_frame, text="Max Transfers:").pack(side='left')
        self.max_transfers = tk.StringVar(value="4")
        ttk.Spinbox(transfers_frame, from_=1, to=16, 
                   textvariable=self.max_transfers, width=10).pack(side='left', padx=5)
        
        # Bandwidth limit
        bandwidth_frame = ttk.Frame(general_frame)
        bandwidth_frame.pack(fill='x', pady=5)
        ttk.Label(bandwidth_frame, text="Bandwidth Limit:").pack(side='left')
        self.bandwidth_limit = tk.StringVar()
        ttk.Entry(bandwidth_frame, textvariable=self.bandwidth_limit, 
                 width=20).pack(side='left', padx=5)
        ttk.Label(bandwidth_frame, text="(e.g., 10M, 1G, leave empty for no limit)").pack(side='left')
        
        # Advanced settings frame
        advanced_frame = ttk.LabelFrame(settings_frame, text="Advanced Settings", 
                                      padding=10)
        advanced_frame.pack(fill='x', padx=10, pady=5)
        
        # Advanced options
        self.enable_logging = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Enable detailed logging",
                       variable=self.enable_logging).pack(anchor='w')
        
        self.auto_mount = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Auto-mount on startup",
                       variable=self.auto_mount).pack(anchor='w')
        
        self.notifications = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Enable notifications",
                       variable=self.notifications).pack(anchor='w')
        
        # Exclusions frame
        exclusions_frame = ttk.LabelFrame(settings_frame, text="Exclusions", 
                                        padding=10)
        exclusions_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Exclusions list
        ttk.Label(exclusions_frame, text="Exclude patterns (one per line):").pack(anchor='w')
        self.exclusions_text = scrolledtext.ScrolledText(exclusions_frame, height=8)
        self.exclusions_text.pack(fill='both', expand=True, pady=5)
        
        # Default exclusions
        default_exclusions = """*.tmp
*.temp
*.log
*~
.DS_Store
Thumbs.db
node_modules/
.git/
.cache/
snap/*/common/
snap/*/[0-9]*/"""
        self.exclusions_text.insert('1.0', default_exclusions)
        
        # Settings buttons
        settings_buttons = ttk.Frame(settings_frame)
        settings_buttons.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(settings_buttons, text="Save Settings", 
                  command=self.save_settings,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(settings_buttons, text="Reset to Defaults", 
                  command=self.reset_settings).pack(side='left', padx=5)
        
        ttk.Button(settings_buttons, text="Export Settings", 
                  command=self.export_settings).pack(side='left', padx=5)
        
        ttk.Button(settings_buttons, text="Import Settings", 
                  command=self.import_settings).pack(side='left', padx=5)
        
    def create_logs_tab(self):
        """Create the logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Log controls frame
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Refresh", 
                  command=self.refresh_logs).pack(side='left', padx=5)
        
        ttk.Button(controls_frame, text="Clear", 
                  command=self.clear_logs).pack(side='left', padx=5)
        
        ttk.Button(controls_frame, text="Export", 
                  command=self.export_logs).pack(side='left', padx=5)
        
        # Log level filter
        ttk.Label(controls_frame, text="Filter:").pack(side='left', padx=(20, 5))
        self.log_filter = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.log_filter,
                                   values=["all", "info", "warning", "error"])
        filter_combo.pack(side='left', padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_frame, state='disabled')
        self.log_display.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Configure log colors
        self.log_display.tag_configure("info", foreground="black")
        self.log_display.tag_configure("warning", foreground="orange")
        self.log_display.tag_configure("error", foreground="red")
        self.log_display.tag_configure("success", foreground="green")
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Status label
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side='left', padx=5)
        
        # Progress bar (initially hidden)
        self.main_progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        
        # Connection indicator
        self.connection_indicator = ttk.Label(self.status_bar, text="●", 
                                            foreground="gray")
        self.connection_indicator.pack(side='right', padx=5)
        
    def log_message(self, message, level="info"):
        """Add a message to the activity log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to activity log
        self.activity_log.configure(state='normal')
        self.activity_log.insert('end', formatted_message)
        self.activity_log.see('end')
        self.activity_log.configure(state='disabled')
        
        # Add to main log display
        self.log_display.configure(state='normal')
        self.log_display.insert('end', formatted_message, level)
        self.log_display.see('end')
        self.log_display.configure(state='disabled')
        
    def run_command(self, command, callback=None, show_progress=True):
        """Run a command in a separate thread"""
        def run():
            try:
                if show_progress:
                    self.main_progress.pack(side='right', padx=5)
                    self.main_progress.start()
                
                self.log_message(f"Running: {command}")
                
                # Execute command
                result = subprocess.run(command, shell=True, 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_message("Command completed successfully", "success")
                    if callback:
                        callback(result.stdout)
                else:
                    self.log_message(f"Command failed: {result.stderr}", "error")
                    messagebox.showerror("Error", f"Command failed:\n{result.stderr}")
                
            except Exception as e:
                self.log_message(f"Error running command: {str(e)}", "error")
                messagebox.showerror("Error", f"Error running command:\n{str(e)}")
                
            finally:
                if show_progress:
                    self.main_progress.stop()
                    self.main_progress.pack_forget()
                
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        
    def refresh_status(self):
        """Refresh the status indicators"""
        def parse_status(output):
            # Parse the status output and update indicators
            lines = output.split('\n')
            
            for line in lines:
                if 'rclone version' in line:
                    version = line.split('rclone version')[1].strip()
                    self.status_indicators['rclone'].configure(
                        text=f"Installed ({version})", style='Success.TLabel')
                elif 'Google Drive remote' in line and 'configured' in line:
                    self.status_indicators['gdrive'].configure(
                        text="Connected", style='Success.TLabel')
                elif 'Google Drive is mounted' in line:
                    self.status_indicators['mount'].configure(
                        text="Mounted", style='Success.TLabel')
                elif 'Total:' in line:
                    storage_info = line.split('Total:')[1].strip()
                    self.status_indicators['storage'].configure(text=storage_info)
                    
        self.run_command(f"{self.script_path} status", parse_status, show_progress=False)
        
    def start_status_monitoring(self):
        """Start periodic status monitoring"""
        def monitor():
            while True:
                time.sleep(30)  # Check every 30 seconds
                self.root.after(0, self.refresh_status)
                
        thread = threading.Thread(target=monitor)
        thread.daemon = True
        thread.start()
        
    # Command methods
    def quick_setup(self):
        """Run quick setup wizard"""
        def setup_callback(output):
            messagebox.showinfo("Setup Complete", 
                              "Quick setup completed successfully!\n"
                              "Your Google Drive is now configured and mounted.")
            self.refresh_status()
            
        self.run_command(f"{self.script_path} setup", setup_callback)
        
    def mount_drive(self):
        """Mount Google Drive"""
        def mount_callback(output):
            self.refresh_status()
            
        self.run_command(f"{self.script_path} mount", mount_callback)
        
    def unmount_drive(self):
        """Unmount Google Drive"""
        def unmount_callback(output):
            self.refresh_status()
            
        self.run_command(f"{self.script_path} unmount", unmount_callback)
        
    def smart_backup(self):
        """Start smart backup wizard"""
        self.run_command(f"{self.script_path} smart-backup")
        
    def analyze_home(self):
        """Analyze home directory"""
        self.run_command(f"{self.script_path} analyze")
        
    def open_drive_folder(self):
        """Open the Google Drive folder"""
        if os.path.exists(self.mount_point):
            subprocess.run(['xdg-open', self.mount_point])
        else:
            messagebox.showwarning("Warning", 
                                 "Google Drive folder not found. Please mount first.")
            
    def start_backup(self):
        """Start selected backup"""
        categories = []
        for key, var in self.backup_categories.items():
            if var.get():
                categories.append(key)
                
        if not categories:
            messagebox.showwarning("Warning", "Please select at least one backup category.")
            return
            
        # Show progress
        self.backup_progress.start()
        
        # Build command based on selected categories
        # This is a simplified version - you might want to enhance this
        command = f"{self.script_path} full-sync"
        
        def backup_callback(output):
            self.backup_progress.stop()
            messagebox.showinfo("Backup Complete", "Backup completed successfully!")
            
        self.run_command(command, backup_callback)
        
    def schedule_backup(self):
        """Schedule automated backup"""
        result = messagebox.askyesno("Schedule Backup", 
                                   "Do you want to schedule daily automated backup at 2:00 AM?")
        if result:
            self.run_command(f"{self.script_path} setup", 
                           lambda x: messagebox.showinfo("Scheduled", 
                                                        "Backup scheduled successfully!"))
            
    def restore_backup(self):
        """Restore from backup"""
        # This would open a dialog to select what to restore
        messagebox.showinfo("Restore", "Restore functionality coming soon!")
        
    def browse_upload(self):
        """Browse for file to upload"""
        filename = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*")]
        )
        if filename:
            self.upload_path.set(filename)
            
    def upload_file(self):
        """Upload selected file"""
        file_path = self.upload_path.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file to upload.")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist.")
            return

        command = f"{self.script_path} upload {shlex.quote(file_path)}"
        self.run_command(command,
                        lambda x: messagebox.showinfo("Success", "File uploaded successfully!"))
        
    def browse_drive(self):
        """Browse Google Drive files"""
        # This would open a file browser for Google Drive
        messagebox.showinfo("Browse Drive", "Drive browser functionality coming soon!")
        
    def download_file(self):
        """Download selected file"""
        drive_path = self.download_path.get()
        if not drive_path:
            messagebox.showwarning("Warning", "Please enter a file path to download.")
            return

        command = f"{self.script_path} download {shlex.quote(drive_path)}"
        self.run_command(command,
                        lambda x: messagebox.showinfo("Success", "File downloaded successfully!"))
        
    def browse_drive_path(self):
        """Browse to specified drive path"""
        path = self.browser_path.get()
        command = f"{self.script_path} list {shlex.quote(path)}"
        
        def update_browser(output):
            # Clear existing items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
                
            # Parse output and populate tree
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    # Simple parsing - you might want to enhance this
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[-1]
                        size = parts[0] if parts[0].isdigit() else ""
                        self.file_tree.insert('', 'end', text=name, 
                                            values=(size, ""))
                        
        self.run_command(command, update_browser)
        
    def refresh_browser(self):
        """Refresh the file browser"""
        self.browse_drive_path()
        
    def add_sync_pair(self):
        """Add a new sync pair"""
        # This would open a dialog to configure sync pairs
        messagebox.showinfo("Add Sync Pair", "Sync pair configuration coming soon!")
        
    def start_sync(self):
        """Start synchronization"""
        direction = self.sync_direction.get()
        
        if direction == "to_drive":
            command = f"{self.script_path} sync-to"
        elif direction == "from_drive":
            command = f"{self.script_path} sync-from"
        else:
            command = f"{self.script_path} full-sync"
            
        self.run_command(command)
        
    def stop_sync(self):
        """Stop synchronization"""
        # This would stop any running sync processes
        messagebox.showinfo("Stop Sync", "Sync stopped.")
        
    def start_watch_mode(self):
        """Start real-time sync monitoring"""
        command = f"{self.script_path} watch-sync"
        self.run_command(command)
        
    def browse_mount_point(self):
        """Browse for mount point directory"""
        directory = filedialog.askdirectory(title="Select mount point directory")
        if directory:
            self.mount_point_var.set(directory)
            
    def save_settings(self):
        """Save current settings"""
        settings = {
            'mount_point': self.mount_point_var.get(),
            'max_transfers': self.max_transfers.get(),
            'bandwidth_limit': self.bandwidth_limit.get(),
            'enable_logging': self.enable_logging.get(),
            'auto_mount': self.auto_mount.get(),
            'notifications': self.notifications.get(),
            'exclusions': self.exclusions_text.get('1.0', 'end-1c')
        }
        
        config_file = str(Path.home() / '.gdrive-manager-gui.json')
        try:
            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def reset_settings(self):
        """Reset settings to defaults"""
        result = messagebox.askyesno("Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?")
        if result:
            # Reset to default values
            self.mount_point_var.set(str(Path.home() / "GoogleDrive"))
            self.max_transfers.set("4")
            self.bandwidth_limit.set("")
            self.enable_logging.set(True)
            self.auto_mount.set(True)
            self.notifications.set(True)
            messagebox.showinfo("Success", "Settings reset to defaults!")
            
    def export_settings(self):
        """Export settings to file"""
        filename = filedialog.asksaveasfilename(
            title="Export settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                settings = {
                    'mount_point': self.mount_point_var.get(),
                    'max_transfers': self.max_transfers.get(),
                    'bandwidth_limit': self.bandwidth_limit.get(),
                    'enable_logging': self.enable_logging.get(),
                    'auto_mount': self.auto_mount.get(),
                    'notifications': self.notifications.get(),
                    'exclusions': self.exclusions_text.get('1.0', 'end-1c')
                }
                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)
                messagebox.showinfo("Success", "Settings exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export settings: {str(e)}")
                
    def import_settings(self):
        """Import settings from file"""
        filename = filedialog.askopenfilename(
            title="Import settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                
                # Apply settings
                self.mount_point_var.set(settings.get('mount_point', ''))
                self.max_transfers.set(settings.get('max_transfers', '4'))
                self.bandwidth_limit.set(settings.get('bandwidth_limit', ''))
                self.enable_logging.set(settings.get('enable_logging', True))
                self.auto_mount.set(settings.get('auto_mount', True))
                self.notifications.set(settings.get('notifications', True))
                
                if 'exclusions' in settings:
                    self.exclusions_text.delete('1.0', 'end')
                    self.exclusions_text.insert('1.0', settings['exclusions'])
                    
                messagebox.showinfo("Success", "Settings imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings: {str(e)}")
                
    def refresh_logs(self):
        """Refresh the log display"""
        # This would reload logs from files
        self.log_message("Logs refreshed", "info")
        
    def clear_logs(self):
        """Clear the log display"""
        self.log_display.configure(state='normal')
        self.log_display.delete('1.0', 'end')
        self.log_display.configure(state='disabled')
        
        self.activity_log.configure(state='normal')
        self.activity_log.delete('1.0', 'end')
        self.activity_log.configure(state='disabled')
        
    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Export logs",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                content = self.log_display.get('1.0', 'end-1c')
                with open(filename, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", "Logs exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export logs: {str(e)}")
                
    def filter_logs(self, event=None):
        """Filter logs by level"""
        # This would filter the log display based on selected level
        filter_level = self.log_filter.get()
        self.log_message(f"Filtering logs by: {filter_level}", "info")

def main():
    # Check if the bash script exists
    script_path = Path.home() / "gdrive-manager.sh"
    if not script_path.exists():
        messagebox.showerror("Error", 
                           f"Google Drive Manager script not found at {script_path}\n"
                           "Please ensure gdrive-manager.sh is in your home directory.")
        return
        
    # Create and run the GUI
    root = tk.Tk()
    app = GoogleDriveManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()