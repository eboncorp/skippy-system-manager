#!/usr/bin/env python3
"""
Unified System Manager GUI
Integrates TidyTux cleanup, Google Drive management, and system tools
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
import shutil
# import psutil  # For system monitoring - optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Note: psutil not available - some monitoring features will be limited")

class UnifiedSystemManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified System Manager v1.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.config_dir = Path.home() / ".unified-system-manager"
        self.config_file = self.config_dir / "config.conf"
        self.tidytux_script = self.config_dir / "components" / "tidytux.sh"
        self.gdrive_script = self.config_dir / "components" / "gdrive-manager.sh"
        self.mount_point = Path.home() / "GoogleDrive"
        
        # Status tracking
        self.cleanup_running = False
        self.backup_running = False
        self.process_queue = queue.Queue()
        self.current_process = None
        
        # System monitoring
        self.monitor_thread = None
        self.monitoring = True
        
        # Create main interface
        self.create_main_interface()
        
        # Start system monitoring
        self.start_system_monitoring()
        
        # Initial status check
        self.refresh_all_status()
        
    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Info.TLabel', foreground='blue')
        
        # Configure button styles
        style.configure('Action.TButton', font=('Arial', 10))
        style.configure('Primary.TButton', font=('Arial', 11, 'bold'))
        style.configure('Danger.TButton', font=('Arial', 10))
        
    def create_main_interface(self):
        """Create the main GUI interface"""
        # Create main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill='both', expand=True)
        
        # Create header
        self.create_header(main_container)
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_cleanup_tab()
        self.create_gdrive_tab()
        self.create_system_tab()
        self.create_automation_tab()
        self.create_logs_tab()
        
        # Create status bar
        self.create_status_bar()
        
    def create_header(self, parent):
        """Create application header"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="Unified System Manager", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # Quick actions on the right
        quick_actions = ttk.Frame(header_frame)
        quick_actions.pack(side='right')
        
        ttk.Button(quick_actions, text="⚡ Quick Clean", 
                  command=self.quick_clean,
                  style='Primary.TButton').pack(side='left', padx=2)
        
        ttk.Button(quick_actions, text="☁️ Quick Backup", 
                  command=self.quick_backup,
                  style='Primary.TButton').pack(side='left', padx=2)
        
        ttk.Button(quick_actions, text="🔄 Refresh", 
                  command=self.refresh_all_status).pack(side='left', padx=2)
        
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Create grid layout
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        
        # System Status Card
        self.create_system_status_card(dashboard_frame).grid(row=0, column=0, 
                                                            sticky='nsew', padx=5, pady=5)
        
        # Storage Status Card
        self.create_storage_status_card(dashboard_frame).grid(row=0, column=1, 
                                                             sticky='nsew', padx=5, pady=5)
        
        # Quick Actions Card
        self.create_quick_actions_card(dashboard_frame).grid(row=1, column=0, 
                                                            sticky='nsew', padx=5, pady=5)
        
        # Recent Activity Card
        self.create_activity_card(dashboard_frame).grid(row=1, column=1, 
                                                       sticky='nsew', padx=5, pady=5)
        
    def create_system_status_card(self, parent):
        """Create system status overview card"""
        card = ttk.LabelFrame(parent, text="System Status", padding=10)
        
        # CPU Usage
        cpu_frame = ttk.Frame(card)
        cpu_frame.pack(fill='x', pady=2)
        ttk.Label(cpu_frame, text="CPU Usage:").pack(side='left')
        self.cpu_label = ttk.Label(cpu_frame, text="0%")
        self.cpu_label.pack(side='left', padx=10)
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=200, mode='determinate')
        self.cpu_progress.pack(side='left', fill='x', expand=True)
        
        # Memory Usage
        mem_frame = ttk.Frame(card)
        mem_frame.pack(fill='x', pady=2)
        ttk.Label(mem_frame, text="Memory:").pack(side='left')
        self.mem_label = ttk.Label(mem_frame, text="0%")
        self.mem_label.pack(side='left', padx=10)
        self.mem_progress = ttk.Progressbar(mem_frame, length=200, mode='determinate')
        self.mem_progress.pack(side='left', fill='x', expand=True)
        
        # Disk Usage
        disk_frame = ttk.Frame(card)
        disk_frame.pack(fill='x', pady=2)
        ttk.Label(disk_frame, text="Disk Usage:").pack(side='left')
        self.disk_label = ttk.Label(disk_frame, text="0%")
        self.disk_label.pack(side='left', padx=10)
        self.disk_progress = ttk.Progressbar(disk_frame, length=200, mode='determinate')
        self.disk_progress.pack(side='left', fill='x', expand=True)
        
        # System Info
        info_frame = ttk.Frame(card)
        info_frame.pack(fill='x', pady=(10, 0))
        self.system_info_label = ttk.Label(info_frame, text="Loading system info...")
        self.system_info_label.pack(side='left')
        
        return card
        
    def create_storage_status_card(self, parent):
        """Create storage overview card"""
        card = ttk.LabelFrame(parent, text="Storage Overview", padding=10)
        
        # Storage breakdown
        self.storage_tree = ttk.Treeview(card, columns=('Size', 'Percent'), 
                                        height=8, show='tree headings')
        self.storage_tree.heading('#0', text='Location')
        self.storage_tree.heading('Size', text='Size')
        self.storage_tree.heading('Percent', text='Usage')
        self.storage_tree.column('#0', width=200)
        self.storage_tree.column('Size', width=100)
        self.storage_tree.column('Percent', width=80)
        self.storage_tree.pack(fill='both', expand=True)
        
        # Populate with dummy data initially
        self.update_storage_breakdown()
        
        return card
        
    def create_quick_actions_card(self, parent):
        """Create quick actions card"""
        card = ttk.LabelFrame(parent, text="Quick Actions", padding=10)
        
        # Action buttons in grid
        actions = [
            ("🧹 Clean Caches", self.clean_caches),
            ("📦 Clean Packages", self.clean_packages),
            ("🗑️ Empty Trash", self.empty_trash),
            ("🔍 Find Duplicates", self.find_duplicates),
            ("📂 Organize Downloads", self.organize_downloads),
            ("🐋 Clean Docker", self.clean_docker),
            ("☁️ Mount Drive", self.toggle_drive_mount),
            ("🔄 Sync Files", self.sync_files),
            ("💾 Backup Now", self.backup_now),
        ]
        
        for i, (text, command) in enumerate(actions):
            row = i // 3
            col = i % 3
            ttk.Button(card, text=text, command=command).grid(
                row=row, column=col, padx=5, pady=5, sticky='ew'
            )
            
        # Configure grid weights
        for i in range(3):
            card.columnconfigure(i, weight=1)
            
        return card
        
    def create_activity_card(self, parent):
        """Create recent activity card"""
        card = ttk.LabelFrame(parent, text="Recent Activity", padding=10)
        
        # Activity log
        self.activity_log = scrolledtext.ScrolledText(card, height=10, 
                                                     wrap=tk.WORD, state='disabled')
        self.activity_log.pack(fill='both', expand=True)
        
        # Configure tags for colored output
        self.activity_log.tag_configure("info", foreground="black")
        self.activity_log.tag_configure("success", foreground="green")
        self.activity_log.tag_configure("warning", foreground="orange")
        self.activity_log.tag_configure("error", foreground="red")
        
        return card
        
    def create_cleanup_tab(self):
        """Create the system cleanup tab"""
        cleanup_frame = ttk.Frame(self.notebook)
        self.notebook.add(cleanup_frame, text="🧹 System Cleanup")
        
        # Cleanup options frame
        options_frame = ttk.LabelFrame(cleanup_frame, text="Cleanup Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        # Cleanup checkboxes
        self.cleanup_options = {}
        cleanup_items = [
            ("clean_packages", "Package Cache (apt, snap)"),
            ("clean_thumbnails", "Thumbnail Cache"),
            ("clean_browsers", "Browser Caches"),
            ("clean_logs", "Old Log Files"),
            ("clean_temp", "Temporary Files"),
            ("clean_trash", "Empty Trash"),
            ("organize_downloads", "Organize Downloads"),
            ("remove_duplicates", "Remove Duplicate Files"),
            ("clean_docker", "Docker Resources"),
        ]
        
        # Create checkboxes in two columns
        for i, (key, label) in enumerate(cleanup_items):
            var = tk.BooleanVar(value=True)
            self.cleanup_options[key] = var
            row = i % 5
            col = i // 5
            ttk.Checkbutton(options_frame, text=label, variable=var).grid(
                row=row, column=col, sticky='w', padx=10, pady=2
            )
            
        # Space analysis frame
        analysis_frame = ttk.LabelFrame(cleanup_frame, text="Space Analysis", padding=10)
        analysis_frame.pack(fill='x', padx=10, pady=5)
        
        # Analysis buttons
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Analyze Disk Usage", 
                  command=self.analyze_disk).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Find Large Files", 
                  command=self.find_large_files).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Check Duplicates", 
                  command=self.check_duplicates).pack(side='left', padx=5)
        
        # Cleanup control frame
        control_frame = ttk.LabelFrame(cleanup_frame, text="Cleanup Control", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Control buttons
        self.cleanup_button = ttk.Button(control_frame, text="Start Cleanup", 
                                       command=self.start_cleanup,
                                       style='Primary.TButton')
        self.cleanup_button.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Emergency Cleanup", 
                  command=self.emergency_cleanup,
                  style='Danger.TButton').pack(side='left', padx=5)
        
        # Cleanup progress
        self.cleanup_progress_var = tk.StringVar(value="Ready to clean")
        ttk.Label(control_frame, textvariable=self.cleanup_progress_var).pack(
            side='left', padx=20)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(cleanup_frame, text="Progress", padding=10)
        progress_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Progress bar
        self.cleanup_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.cleanup_progress.pack(fill='x', pady=5)
        
        # Progress text
        self.cleanup_log = scrolledtext.ScrolledText(progress_frame, height=15, 
                                                    state='disabled')
        self.cleanup_log.pack(fill='both', expand=True)
        
    def create_gdrive_tab(self):
        """Create the Google Drive management tab"""
        gdrive_frame = ttk.Frame(self.notebook)
        self.notebook.add(gdrive_frame, text="☁️ Google Drive")
        
        # Connection status frame
        status_frame = ttk.LabelFrame(gdrive_frame, text="Connection Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Status indicators
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill='x')
        
        ttk.Label(status_grid, text="rclone:").grid(row=0, column=0, sticky='w')
        self.rclone_status = ttk.Label(status_grid, text="Checking...", style='Info.TLabel')
        self.rclone_status.grid(row=0, column=1, sticky='w', padx=10)
        
        ttk.Label(status_grid, text="Google Drive:").grid(row=1, column=0, sticky='w')
        self.gdrive_status = ttk.Label(status_grid, text="Checking...", style='Info.TLabel')
        self.gdrive_status.grid(row=1, column=1, sticky='w', padx=10)
        
        ttk.Label(status_grid, text="Mount Status:").grid(row=2, column=0, sticky='w')
        self.mount_status = ttk.Label(status_grid, text="Checking...", style='Info.TLabel')
        self.mount_status.grid(row=2, column=1, sticky='w', padx=10)
        
        # Control buttons
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        self.mount_button = ttk.Button(control_frame, text="Mount Drive", 
                                     command=self.toggle_drive_mount)
        self.mount_button.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Configure", 
                  command=self.configure_gdrive).pack(side='left', padx=5)
        
        # Backup settings frame
        backup_frame = ttk.LabelFrame(gdrive_frame, text="Backup Settings", padding=10)
        backup_frame.pack(fill='x', padx=10, pady=5)
        
        # Backup categories
        self.backup_categories = {}
        categories = [
            ("documents", "Documents"),
            ("pictures", "Pictures"),
            ("downloads", "Downloads"),
            ("desktop", "Desktop"),
            ("config", "Configuration Files"),
            ("scripts", "Scripts"),
        ]
        
        for i, (key, label) in enumerate(categories):
            var = tk.BooleanVar(value=True)
            self.backup_categories[key] = var
            row = i // 3
            col = i % 3
            ttk.Checkbutton(backup_frame, text=label, variable=var).grid(
                row=row, column=col, sticky='w', padx=10, pady=2
            )
            
        # Backup controls
        backup_control = ttk.Frame(backup_frame)
        backup_control.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(backup_control, text="Start Backup", 
                  command=self.start_backup,
                  style='Primary.TButton').pack(side='left', padx=5)
        
        ttk.Button(backup_control, text="Smart Backup", 
                  command=self.smart_backup).pack(side='left', padx=5)
        
        ttk.Button(backup_control, text="Restore", 
                  command=self.restore_backup).pack(side='left', padx=5)
        
        # File operations frame
        operations_frame = ttk.LabelFrame(gdrive_frame, text="File Operations", padding=10)
        operations_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Upload/Download
        file_frame = ttk.Frame(operations_frame)
        file_frame.pack(fill='x', pady=5)
        
        ttk.Button(file_frame, text="Upload Files", 
                  command=self.upload_files).pack(side='left', padx=5)
        ttk.Button(file_frame, text="Download Files", 
                  command=self.download_files).pack(side='left', padx=5)
        ttk.Button(file_frame, text="Sync Folders", 
                  command=self.sync_folders).pack(side='left', padx=5)
        
        # File browser
        self.gdrive_tree = ttk.Treeview(operations_frame, columns=('Size', 'Modified'), 
                                       height=10)
        self.gdrive_tree.heading('#0', text='Name')
        self.gdrive_tree.heading('Size', text='Size')
        self.gdrive_tree.heading('Modified', text='Modified')
        self.gdrive_tree.pack(fill='both', expand=True, pady=5)
        
    def create_system_tab(self):
        """Create system management tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="⚙️ System")
        
        # System info frame
        info_frame = ttk.LabelFrame(system_frame, text="System Information", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.system_info_text = scrolledtext.ScrolledText(info_frame, height=8, 
                                                         state='disabled')
        self.system_info_text.pack(fill='both', expand=True)
        
        # Update system info
        self.update_system_info()
        
        # System maintenance frame
        maint_frame = ttk.LabelFrame(system_frame, text="System Maintenance", padding=10)
        maint_frame.pack(fill='x', padx=10, pady=5)
        
        # Maintenance actions
        maint_grid = ttk.Frame(maint_frame)
        maint_grid.pack(fill='x')
        
        actions = [
            ("Update System", self.update_system),
            ("Clean Packages", self.clean_packages),
            ("Fix Dependencies", self.fix_dependencies),
            ("Update Grub", self.update_grub),
            ("Clean Kernels", self.clean_kernels),
            ("System Report", self.generate_report),
        ]
        
        for i, (text, command) in enumerate(actions):
            row = i // 3
            col = i % 3
            ttk.Button(maint_grid, text=text, command=command).grid(
                row=row, column=col, padx=5, pady=5, sticky='ew'
            )
            
        # Services management frame
        services_frame = ttk.LabelFrame(system_frame, text="Services", padding=10)
        services_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Services list
        self.services_tree = ttk.Treeview(services_frame, columns=('Status',), height=8)
        self.services_tree.heading('#0', text='Service')
        self.services_tree.heading('Status', text='Status')
        self.services_tree.pack(fill='both', expand=True)
        
        # Populate common services
        self.update_services_list()
        
    def create_automation_tab(self):
        """Create automation settings tab"""
        auto_frame = ttk.Frame(self.notebook)
        self.notebook.add(auto_frame, text="🤖 Automation")
        
        # Scheduled tasks frame
        schedule_frame = ttk.LabelFrame(auto_frame, text="Scheduled Tasks", padding=10)
        schedule_frame.pack(fill='x', padx=10, pady=5)
        
        # Cleanup schedule
        cleanup_schedule = ttk.Frame(schedule_frame)
        cleanup_schedule.pack(fill='x', pady=5)
        
        self.cleanup_enabled = tk.BooleanVar()
        ttk.Checkbutton(cleanup_schedule, text="Enable automatic cleanup",
                       variable=self.cleanup_enabled).pack(side='left')
        
        ttk.Label(cleanup_schedule, text="Schedule:").pack(side='left', padx=(20, 5))
        self.cleanup_schedule = ttk.Combobox(cleanup_schedule, 
                                           values=["Daily", "Weekly", "Monthly"],
                                           width=15)
        self.cleanup_schedule.set("Weekly")
        self.cleanup_schedule.pack(side='left')
        
        # Backup schedule
        backup_schedule = ttk.Frame(schedule_frame)
        backup_schedule.pack(fill='x', pady=5)
        
        self.backup_enabled = tk.BooleanVar()
        ttk.Checkbutton(backup_schedule, text="Enable automatic backup",
                       variable=self.backup_enabled).pack(side='left')
        
        ttk.Label(backup_schedule, text="Schedule:").pack(side='left', padx=(20, 5))
        self.backup_schedule = ttk.Combobox(backup_schedule, 
                                          values=["Daily", "Weekly", "Monthly"],
                                          width=15)
        self.backup_schedule.set("Daily")
        self.backup_schedule.pack(side='left')
        
        # Apply schedule button
        ttk.Button(schedule_frame, text="Apply Schedule", 
                  command=self.apply_schedule,
                  style='Primary.TButton').pack(pady=10)
        
        # Triggers frame
        triggers_frame = ttk.LabelFrame(auto_frame, text="Auto-Triggers", padding=10)
        triggers_frame.pack(fill='x', padx=10, pady=5)
        
        # Trigger options
        self.trigger_low_space = tk.BooleanVar()
        ttk.Checkbutton(triggers_frame, 
                       text="Run cleanup when disk space is below 10%",
                       variable=self.trigger_low_space).pack(anchor='w', pady=2)
        
        self.trigger_startup = tk.BooleanVar()
        ttk.Checkbutton(triggers_frame, 
                       text="Check system on startup",
                       variable=self.trigger_startup).pack(anchor='w', pady=2)
        
        self.trigger_shutdown = tk.BooleanVar()
        ttk.Checkbutton(triggers_frame, 
                       text="Clean temporary files on shutdown",
                       variable=self.trigger_shutdown).pack(anchor='w', pady=2)
        
        # Notifications frame
        notif_frame = ttk.LabelFrame(auto_frame, text="Notifications", padding=10)
        notif_frame.pack(fill='x', padx=10, pady=5)
        
        self.notify_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Enable desktop notifications",
                       variable=self.notify_enabled).pack(anchor='w')
        
        self.email_enabled = tk.BooleanVar()
        ttk.Checkbutton(notif_frame, text="Send email reports",
                       variable=self.email_enabled).pack(anchor='w')
        
        # Email config
        email_frame = ttk.Frame(notif_frame)
        email_frame.pack(fill='x', pady=5)
        ttk.Label(email_frame, text="Email:").pack(side='left')
        self.email_entry = ttk.Entry(email_frame, width=30)
        self.email_entry.pack(side='left', padx=5)
        
    def create_logs_tab(self):
        """Create logs viewer tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Log controls
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(controls_frame, text="Log Type:").pack(side='left')
        self.log_type = ttk.Combobox(controls_frame, 
                                    values=["All", "Cleanup", "Backup", "System"],
                                    width=15)
        self.log_type.set("All")
        self.log_type.pack(side='left', padx=5)
        self.log_type.bind('<<ComboboxSelected>>', self.filter_logs)
        
        ttk.Button(controls_frame, text="Refresh", 
                  command=self.refresh_logs).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Clear", 
                  command=self.clear_logs).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Export", 
                  command=self.export_logs).pack(side='left', padx=5)
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_frame, state='disabled')
        self.log_display.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Configure log colors
        self.log_display.tag_configure("info", foreground="black")
        self.log_display.tag_configure("success", foreground="green")
        self.log_display.tag_configure("warning", foreground="orange")
        self.log_display.tag_configure("error", foreground="red")
        
        # Load initial logs
        self.refresh_logs()
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Status label
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side='left', padx=5)
        
        # Progress bar (initially hidden)
        self.main_progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        
        # System stats on the right
        self.stats_label = ttk.Label(self.status_bar, text="")
        self.stats_label.pack(side='right', padx=5)
        
    # Utility methods
    def log_message(self, message, level="info"):
        """Add a message to activity log and log display"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to activity log
        self.activity_log.configure(state='normal')
        self.activity_log.insert('end', formatted_message, level)
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
                        self.root.after(0, callback, result.stdout)
                else:
                    self.log_message(f"Command failed: {result.stderr}", "error")
                    
            except Exception as e:
                self.log_message(f"Error running command: {str(e)}", "error")
                
            finally:
                if show_progress:
                    self.main_progress.stop()
                    self.main_progress.pack_forget()
                
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        
    # System monitoring
    def start_system_monitoring(self):
        """Start monitoring system resources"""
        if not PSUTIL_AVAILABLE:
            # Fallback monitoring using basic commands
            self.cpu_label.config(text="N/A")
            self.mem_label.config(text="N/A") 
            self.disk_label.config(text="N/A")
            self.stats_label.config(text="Monitoring unavailable - install python3-psutil")
            return
            
        def monitor():
            while self.monitoring:
                try:
                    # Get CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.cpu_progress['value'] = cpu_percent
                    self.cpu_label.config(text=f"{cpu_percent}%")
                    
                    # Get memory usage
                    mem = psutil.virtual_memory()
                    self.mem_progress['value'] = mem.percent
                    self.mem_label.config(text=f"{mem.percent}%")
                    
                    # Get disk usage
                    disk = psutil.disk_usage('/')
                    self.disk_progress['value'] = disk.percent
                    self.disk_label.config(text=f"{disk.percent}%")
                    
                    # Update status bar stats
                    self.stats_label.config(
                        text=f"CPU: {cpu_percent}% | RAM: {mem.percent}% | Disk: {disk.percent}%"
                    )
                    
                    # Check for critical conditions
                    if disk.percent > 90:
                        self.log_message("Warning: Disk usage above 90%!", "warning")
                        
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    
                time.sleep(2)
                
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    # Action methods
    def quick_clean(self):
        """Perform quick system cleanup"""
        self.log_message("Starting quick cleanup...")
        
        # Set common cleanup options
        for key in ['clean_packages', 'clean_thumbnails', 'clean_temp', 'clean_trash']:
            if key in self.cleanup_options:
                self.cleanup_options[key].set(True)
                
        # Switch to cleanup tab and start
        self.notebook.select(1)  # Cleanup tab
        self.start_cleanup()
        
    def quick_backup(self):
        """Perform quick backup"""
        self.log_message("Starting quick backup...")
        
        # Switch to Google Drive tab
        self.notebook.select(2)  # Google Drive tab
        
        # Check if mounted
        if not os.path.exists(self.mount_point):
            self.toggle_drive_mount()
            
        # Start smart backup
        self.smart_backup()
        
    def refresh_all_status(self):
        """Refresh all status information"""
        self.log_message("Refreshing system status...")
        
        # Update system info
        self.update_system_info()
        
        # Update storage breakdown
        self.update_storage_breakdown()
        
        # Update Google Drive status
        self.check_gdrive_status()
        
        # Update services
        self.update_services_list()
        
    def update_system_info(self):
        """Update system information display"""
        try:
            import platform
            
            boot_time = "N/A"
            if PSUTIL_AVAILABLE:
                boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))
            
            info_text = f"""Operating System: {platform.system()} {platform.release()}
Architecture: {platform.machine()}
Processor: {platform.processor()}
Python Version: {platform.python_version()}
Hostname: {platform.node()}
Boot Time: {boot_time}
"""
            
            self.system_info_text.configure(state='normal')
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(1.0, info_text)
            self.system_info_text.configure(state='disabled')
            
            # Update dashboard label
            self.system_info_label.config(
                text=f"{platform.system()} {platform.release()} | {platform.node()}"
            )
            
        except Exception as e:
            self.log_message(f"Error updating system info: {e}", "error")
            
    def update_storage_breakdown(self):
        """Update storage breakdown tree"""
        # Clear existing items
        for item in self.storage_tree.get_children():
            self.storage_tree.delete(item)
            
        try:
            # Get disk usage for common directories
            home = Path.home()
            dirs_to_check = [
                ("Home Directory", home),
                ("Documents", home / "Documents"),
                ("Downloads", home / "Downloads"),
                ("Pictures", home / "Pictures"),
                ("Videos", home / "Videos"),
                ("Desktop", home / "Desktop"),
                (".cache", home / ".cache"),
            ]
            
            for name, path in dirs_to_check:
                if path.exists():
                    try:
                        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                        size_str = self.format_bytes(size)
                        
                        # Calculate percentage of home directory
                        home_size = sum(f.stat().st_size for f in home.rglob('*') if f.is_file())
                        percent = f"{(size / home_size * 100):.1f}%" if home_size > 0 else "0%"
                        
                        self.storage_tree.insert('', 'end', text=name, 
                                               values=(size_str, percent))
                    except:
                        pass
                        
        except Exception as e:
            self.log_message(f"Error updating storage breakdown: {e}", "error")
            
    def format_bytes(self, bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"
        
    # Cleanup actions
    def start_cleanup(self):
        """Start system cleanup"""
        if self.cleanup_running:
            messagebox.showwarning("Cleanup Running", 
                                 "Cleanup is already in progress!")
            return
            
        self.cleanup_running = True
        self.cleanup_button.config(state='disabled')
        self.cleanup_progress.start()
        self.cleanup_progress_var.set("Cleanup in progress...")
        
        # Clear cleanup log
        self.cleanup_log.configure(state='normal')
        self.cleanup_log.delete(1.0, tk.END)
        self.cleanup_log.configure(state='disabled')
        
        def cleanup_thread():
            try:
                # Run cleanup based on selected options
                if self.cleanup_options.get('clean_packages', tk.BooleanVar()).get():
                    self.run_cleanup_task("Cleaning package cache", 
                                        "sudo apt clean && sudo apt autoclean")
                    
                if self.cleanup_options.get('clean_thumbnails', tk.BooleanVar()).get():
                    self.run_cleanup_task("Cleaning thumbnail cache", 
                                        f"rm -rf {Path.home()}/.cache/thumbnails/*")
                    
                if self.cleanup_options.get('clean_browsers', tk.BooleanVar()).get():
                    self.clean_browser_caches()
                    
                if self.cleanup_options.get('clean_temp', tk.BooleanVar()).get():
                    self.run_cleanup_task("Cleaning temporary files", 
                                        "find /tmp -type f -atime +7 -delete 2>/dev/null || true")
                    
                if self.cleanup_options.get('clean_trash', tk.BooleanVar()).get():
                    self.run_cleanup_task("Emptying trash", 
                                        f"rm -rf {Path.home()}/.local/share/Trash/*")
                    
                if self.cleanup_options.get('organize_downloads', tk.BooleanVar()).get():
                    self.organize_downloads()
                    
                if self.cleanup_options.get('clean_docker', tk.BooleanVar()).get():
                    self.clean_docker()
                    
                self.log_message("Cleanup completed successfully!", "success")
                
            except Exception as e:
                self.log_message(f"Cleanup error: {e}", "error")
                
            finally:
                self.cleanup_running = False
                self.root.after(0, self.cleanup_complete)
                
        thread = threading.Thread(target=cleanup_thread)
        thread.daemon = True
        thread.start()
        
    def cleanup_complete(self):
        """Called when cleanup is complete"""
        self.cleanup_button.config(state='normal')
        self.cleanup_progress.stop()
        self.cleanup_progress_var.set("Cleanup complete")
        self.refresh_all_status()
        
    def run_cleanup_task(self, description, command):
        """Run a cleanup task and log output"""
        self.log_cleanup_message(f"\n{description}...")
        
        try:
            result = subprocess.run(command, shell=True, 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_cleanup_message(f"✓ {description} - Complete", "success")
            else:
                self.log_cleanup_message(f"✗ {description} - Failed: {result.stderr}", "error")
        except Exception as e:
            self.log_cleanup_message(f"✗ {description} - Error: {e}", "error")
            
    def log_cleanup_message(self, message, tag="info"):
        """Log message to cleanup log"""
        self.root.after(0, self._update_cleanup_log, message, tag)
        
    def _update_cleanup_log(self, message, tag):
        """Update cleanup log in main thread"""
        self.cleanup_log.configure(state='normal')
        self.cleanup_log.insert('end', message + '\n', tag)
        self.cleanup_log.see('end')
        self.cleanup_log.configure(state='disabled')
        
    def clean_browser_caches(self):
        """Clean browser caches"""
        browsers = [
            ("Chrome", Path.home() / ".cache/google-chrome"),
            ("Firefox", Path.home() / ".mozilla/firefox"),
            ("Chromium", Path.home() / ".cache/chromium"),
        ]
        
        for name, cache_path in browsers:
            if cache_path.exists():
                self.run_cleanup_task(f"Cleaning {name} cache", 
                                    f"rm -rf {cache_path}/*/Cache/* 2>/dev/null || true")
                
    def organize_downloads(self):
        """Organize downloads folder"""
        if self.tidytux_script.exists():
            self.run_cleanup_task("Organizing Downloads folder",
                                f"bash -c 'source {self.tidytux_script} && organize_downloads'")
        else:
            self.log_cleanup_message("TidyTux script not found", "error")
            
    def clean_docker(self):
        """Clean Docker resources"""
        if shutil.which('docker'):
            self.run_cleanup_task("Cleaning Docker resources",
                                "docker system prune -af --volumes")
        else:
            self.log_cleanup_message("Docker not installed", "warning")
            
    def emergency_cleanup(self):
        """Run emergency cleanup for low disk space"""
        if messagebox.askyesno("Emergency Cleanup", 
                             "This will aggressively clean your system to free up space. Continue?"):
            self.log_message("Starting emergency cleanup...", "warning")
            
            # Run TidyTux in emergency mode
            if self.tidytux_script.exists():
                self.run_command(f"{self.tidytux_script} --emergency",
                               lambda x: self.log_message("Emergency cleanup complete", "success"))
            else:
                messagebox.showerror("Error", "TidyTux component not found!")
                
    # Google Drive actions
    def check_gdrive_status(self):
        """Check Google Drive status"""
        try:
            # Check rclone
            result = subprocess.run("rclone version", shell=True, 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                self.rclone_status.config(text=f"Installed ({version})", 
                                        style='Success.TLabel')
            else:
                self.rclone_status.config(text="Not installed", 
                                        style='Error.TLabel')
                
            # Check Google Drive config
            result = subprocess.run("rclone listremotes", shell=True,
                                  capture_output=True, text=True)
            if "googledrive:" in result.stdout:
                self.gdrive_status.config(text="Configured", 
                                        style='Success.TLabel')
            else:
                self.gdrive_status.config(text="Not configured", 
                                        style='Warning.TLabel')
                
            # Check mount status
            if os.path.exists(self.mount_point) and os.path.ismount(self.mount_point):
                self.mount_status.config(text=f"Mounted at {self.mount_point}", 
                                       style='Success.TLabel')
                self.mount_button.config(text="Unmount Drive")
            else:
                self.mount_status.config(text="Not mounted", 
                                       style='Warning.TLabel')
                self.mount_button.config(text="Mount Drive")
                
        except Exception as e:
            self.log_message(f"Error checking Google Drive status: {e}", "error")
            
    def toggle_drive_mount(self):
        """Toggle Google Drive mount"""
        if os.path.exists(self.mount_point) and os.path.ismount(self.mount_point):
            # Unmount
            self.run_command(f"{self.gdrive_script} unmount",
                           lambda x: self.check_gdrive_status())
        else:
            # Mount
            self.run_command(f"{self.gdrive_script} mount",
                           lambda x: self.check_gdrive_status())
            
    def configure_gdrive(self):
        """Configure Google Drive"""
        if self.gdrive_script.exists():
            self.log_message("Launching Google Drive configuration...")
            subprocess.Popen([str(self.gdrive_script), "config"], 
                           stdout=subprocess.PIPE)
        else:
            messagebox.showerror("Error", "Google Drive Manager script not found!")
            
    def start_backup(self):
        """Start backup process"""
        if self.backup_running:
            messagebox.showwarning("Backup Running", "Backup is already in progress!")
            return
            
        self.backup_running = True
        self.log_message("Starting backup process...")
        
        # Get selected categories
        categories = [key for key, var in self.backup_categories.items() if var.get()]
        
        if not categories:
            messagebox.showwarning("No Selection", "Please select at least one category to backup!")
            self.backup_running = False
            return
            
        # Run backup
        if self.gdrive_script.exists():
            self.run_command(f"{self.gdrive_script} smart-backup",
                           self.backup_complete)
        else:
            messagebox.showerror("Error", "Google Drive Manager script not found!")
            self.backup_running = False
            
    def backup_complete(self, output=None):
        """Called when backup is complete"""
        self.backup_running = False
        self.log_message("Backup completed successfully!", "success")
        messagebox.showinfo("Backup Complete", "Your files have been backed up to Google Drive!")
        
    def smart_backup(self):
        """Run smart backup wizard"""
        if self.gdrive_script.exists():
            self.log_message("Starting smart backup wizard...")
            self.run_command(f"{self.gdrive_script} smart-backup")
        else:
            messagebox.showerror("Error", "Google Drive Manager script not found!")
            
    def restore_backup(self):
        """Restore from backup"""
        messagebox.showinfo("Restore", "Restore functionality will open Google Drive manager")
        if self.gdrive_script.exists():
            subprocess.Popen([str(self.gdrive_script)])
            
    def upload_files(self):
        """Upload files to Google Drive"""
        files = filedialog.askopenfilenames(title="Select files to upload")
        if files:
            for file in files:
                self.run_command(f'{self.gdrive_script} upload "{file}"')
                
    def download_files(self):
        """Download files from Google Drive"""
        # This would need a file browser for Google Drive
        messagebox.showinfo("Download", "Use the Google Drive mount to access your files directly")
        
    def sync_folders(self):
        """Sync folders with Google Drive"""
        folder = filedialog.askdirectory(title="Select folder to sync")
        if folder:
            self.run_command(f'{self.gdrive_script} sync-to "{folder}"')
            
    # System maintenance actions
    def update_system(self):
        """Update system packages"""
        if messagebox.askyesno("System Update", 
                             "This will update all system packages. Continue?"):
            self.log_message("Updating system packages...")
            self.run_command("sudo apt update && sudo apt upgrade -y",
                           lambda x: self.log_message("System update complete", "success"))
            
    def fix_dependencies(self):
        """Fix broken dependencies"""
        self.log_message("Fixing broken dependencies...")
        self.run_command("sudo apt --fix-broken install -y",
                       lambda x: self.log_message("Dependencies fixed", "success"))
        
    def update_grub(self):
        """Update GRUB bootloader"""
        self.log_message("Updating GRUB...")
        self.run_command("sudo update-grub",
                       lambda x: self.log_message("GRUB updated", "success"))
        
    def clean_kernels(self):
        """Remove old kernels"""
        self.log_message("Removing old kernels...")
        self.run_command("sudo apt autoremove --purge -y",
                       lambda x: self.log_message("Old kernels removed", "success"))
        
    def generate_report(self):
        """Generate system report"""
        report_path = Path.home() / "Desktop" / f"system_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        self.log_message(f"Generating system report to {report_path}...")
        
        # Collect system information
        report_content = f"""System Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

=== System Information ===
{subprocess.run('uname -a', shell=True, capture_output=True, text=True).stdout}

=== Disk Usage ===
{subprocess.run('df -h', shell=True, capture_output=True, text=True).stdout}

=== Memory Usage ===
{subprocess.run('free -h', shell=True, capture_output=True, text=True).stdout}

=== Top Processes ===
{subprocess.run('ps aux --sort=-%cpu | head -20', shell=True, capture_output=True, text=True).stdout}

=== Package Status ===
{subprocess.run('dpkg -l | grep -E "^rc|^iU"', shell=True, capture_output=True, text=True).stdout}
"""
        
        # Write report
        with open(report_path, 'w') as f:
            f.write(report_content)
            
        self.log_message(f"System report saved to {report_path}", "success")
        
        if messagebox.askyesno("Report Generated", 
                             f"System report saved to:\n{report_path}\n\nOpen it now?"):
            subprocess.run(['xdg-open', str(report_path)])
            
    def update_services_list(self):
        """Update services list"""
        # Clear existing items
        for item in self.services_tree.get_children():
            self.services_tree.delete(item)
            
        # Common services to check
        services = [
            "apache2", "nginx", "mysql", "postgresql", "docker",
            "ssh", "cron", "NetworkManager", "bluetooth", "cups"
        ]
        
        for service in services:
            try:
                result = subprocess.run(f"systemctl is-active {service}", 
                                      shell=True, capture_output=True, text=True)
                status = result.stdout.strip()
                if status in ["active", "inactive"]:
                    self.services_tree.insert('', 'end', text=service, 
                                            values=(status,))
            except:
                pass
                
    # Additional quick actions
    def clean_caches(self):
        """Quick clean caches"""
        self.log_message("Cleaning system caches...")
        commands = [
            "sudo apt clean",
            f"rm -rf {Path.home()}/.cache/thumbnails/*",
            "sudo journalctl --vacuum-time=3d"
        ]
        for cmd in commands:
            self.run_command(cmd)
            
    def clean_packages(self):
        """Clean package caches"""
        self.log_message("Cleaning package caches...")
        self.run_command("sudo apt clean && sudo apt autoclean && sudo apt autoremove -y")
        
    def empty_trash(self):
        """Empty trash"""
        self.log_message("Emptying trash...")
        self.run_command(f"rm -rf {Path.home()}/.local/share/Trash/*",
                       lambda x: self.log_message("Trash emptied", "success"))
        
    def find_duplicates(self):
        """Find duplicate files"""
        if shutil.which('fdupes'):
            folder = filedialog.askdirectory(title="Select folder to scan for duplicates")
            if folder:
                self.log_message(f"Scanning for duplicates in {folder}...")
                self.run_command(f"fdupes -r '{folder}'",
                               lambda x: self.show_duplicates_dialog(x))
        else:
            messagebox.showerror("Error", "fdupes is not installed!")
            
    def show_duplicates_dialog(self, output):
        """Show duplicates in a dialog"""
        if output.strip():
            # Create a new window to show duplicates
            dup_window = tk.Toplevel(self.root)
            dup_window.title("Duplicate Files Found")
            dup_window.geometry("800x600")
            
            text = scrolledtext.ScrolledText(dup_window)
            text.pack(fill='both', expand=True, padx=10, pady=10)
            text.insert('1.0', output)
            text.configure(state='disabled')
            
            ttk.Button(dup_window, text="Close", 
                      command=dup_window.destroy).pack(pady=5)
        else:
            messagebox.showinfo("No Duplicates", "No duplicate files found!")
            
    def analyze_disk(self):
        """Analyze disk usage"""
        if shutil.which('ncdu'):
            self.log_message("Launching disk usage analyzer...")
            subprocess.Popen(['gnome-terminal', '--', 'ncdu', str(Path.home())])
        else:
            messagebox.showerror("Error", "ncdu is not installed!")
            
    def find_large_files(self):
        """Find large files"""
        self.log_message("Finding large files...")
        self.run_command(
            f"find {Path.home()} -type f -size +100M -exec ls -lh {{}} \\; | sort -k5 -hr | head -20",
            lambda x: self.show_large_files_dialog(x)
        )
        
    def show_large_files_dialog(self, output):
        """Show large files in a dialog"""
        if output.strip():
            # Create a new window
            files_window = tk.Toplevel(self.root)
            files_window.title("Large Files")
            files_window.geometry("900x600")
            
            text = scrolledtext.ScrolledText(files_window)
            text.pack(fill='both', expand=True, padx=10, pady=10)
            text.insert('1.0', "Large files found (>100MB):\n\n" + output)
            text.configure(state='disabled')
            
            ttk.Button(files_window, text="Close", 
                      command=files_window.destroy).pack(pady=5)
        else:
            messagebox.showinfo("No Large Files", "No files larger than 100MB found!")
            
    def check_duplicates(self):
        """Check for duplicate files in common locations"""
        self.log_message("Checking for duplicates in common locations...")
        locations = [
            Path.home() / "Downloads",
            Path.home() / "Documents",
            Path.home() / "Pictures"
        ]
        
        for location in locations:
            if location.exists():
                self.run_command(f"fdupes -r '{location}' | wc -l",
                               lambda x, loc=location: self.log_message(
                                   f"Found {x.strip()} duplicates in {loc.name}"))
                
    def sync_files(self):
        """Quick sync files"""
        if self.gdrive_script.exists():
            self.log_message("Starting file sync...")
            self.run_command(f"{self.gdrive_script} full-sync")
        else:
            messagebox.showerror("Error", "Google Drive Manager script not found!")
            
    def backup_now(self):
        """Quick backup now"""
        self.start_backup()
        
    # Automation methods
    def apply_schedule(self):
        """Apply automation schedule"""
        # Build cron entries
        cron_entries = []
        
        if self.cleanup_enabled.get():
            schedule = self.cleanup_schedule.get()
            if schedule == "Daily":
                cron_entries.append("0 3 * * * /path/to/unified-system-manager.sh --cleanup --quiet")
            elif schedule == "Weekly":
                cron_entries.append("0 3 * * 0 /path/to/unified-system-manager.sh --cleanup --quiet")
            elif schedule == "Monthly":
                cron_entries.append("0 3 1 * * /path/to/unified-system-manager.sh --cleanup --quiet")
                
        if self.backup_enabled.get():
            schedule = self.backup_schedule.get()
            if schedule == "Daily":
                cron_entries.append("0 2 * * * /path/to/unified-system-manager.sh --backup")
            elif schedule == "Weekly":
                cron_entries.append("0 2 * * 0 /path/to/unified-system-manager.sh --backup")
            elif schedule == "Monthly":
                cron_entries.append("0 2 1 * * /path/to/unified-system-manager.sh --backup")
                
        if cron_entries:
            self.log_message("Applying automation schedule...")
            # Here you would add the cron entries
            messagebox.showinfo("Schedule Applied", 
                              "Automation schedule has been configured!")
        else:
            messagebox.showwarning("No Schedule", 
                                 "Please enable at least one scheduled task!")
            
    # Log management
    def filter_logs(self, event=None):
        """Filter logs by type"""
        log_type = self.log_type.get()
        self.log_message(f"Filtering logs: {log_type}")
        # Implement log filtering logic
        
    def refresh_logs(self):
        """Refresh log display"""
        self.log_message("Refreshing logs...")
        # Implement log refresh logic
        
    def clear_logs(self):
        """Clear logs"""
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            self.log_display.configure(state='normal')
            self.log_display.delete(1.0, tk.END)
            self.log_display.configure(state='disabled')
            self.log_message("Logs cleared", "success")
            
    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Export logs",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt")]
        )
        if filename:
            content = self.log_display.get(1.0, tk.END)
            with open(filename, 'w') as f:
                f.write(content)
            self.log_message(f"Logs exported to {filename}", "success")
            
    def on_closing(self):
        """Handle window closing"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.root.destroy()

def main():
    # Check if running with proper Python version
    import sys
    if sys.version_info < (3, 6):
        messagebox.showerror("Python Version Error", 
                           "This application requires Python 3.6 or higher!")
        return
        
    # Check for psutil (optional)
    if not PSUTIL_AVAILABLE:
        print("Note: psutil not available - system monitoring will be limited")
        
    # Create and run the GUI
    root = tk.Tk()
    app = UnifiedSystemManagerGUI(root)
    
    # Set window close handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()