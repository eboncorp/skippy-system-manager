#!/usr/bin/env python3
"""
NexusController - Your Central Command Hub
Unified control center for local and remote system management
"""

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
import json
import socket
import paramiko
from datetime import datetime, timedelta
import psutil
import time
import re

class NexusController:
    def __init__(self):
        # Initialize root window with error handling
        try:
            self.root = tk.Tk()
            self.root.title("NexusController - Central Command Hub")
            self.root.geometry("1100x700")
            
            # Configure window for stability
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.resizable(True, True)
            
            # Set window icon if available
            try:
                self.root.iconphoto(False, tk.PhotoImage(data=self.get_icon_data()))
            except:
                pass
                
        except Exception as e:
            print(f"Error initializing GUI: {e}")
            sys.exit(1)
        
        # Server configurations
        self.servers = {
            'ebon': {
                'host': '10.0.0.29',
                'port': 22,
                'username': 'ebon',
                'name': 'Ebon Server',
                'services': ['SSH', 'HTTP']
            }
        }
        
        # SSH connections cache
        self.ssh_connections = {}
        
        # Update management
        self.update_status = {
            'local': {'available': 0, 'security': 0, 'last_check': None},
            'servers': {}
        }
        self.update_scheduler_running = False
        self.shutdown_flag = False
        
        # Thread-safe UI update queue
        self.ui_update_queue = []
        
        try:
            self.setup_ui()
            # Start background tasks with delay to allow UI to fully initialize
            self.root.after(1000, self.delayed_initialization)
        except Exception as e:
            print(f"Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
    def get_icon_data(self):
        """Return base64 encoded icon data"""
        # Simple nexus-like icon
        return """
        R0lGODlhEAAQAPQAAP///wAAAPj4+Ojo6Li4uMjIyNjY2Ojo6Ozs7PT09Pr6+gAA
        AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        AAAAAAAAAAAAAAAAAAAAACH5BAEAABAALAAAAAAQABAAAAVVICSOZGmeKKCubGuY
        biwMwVAURHEYRjEYhjEQhjEIhjEEhjEAhgAQAiAEQAiAEAAhAEIAhAAIARAC
        """
        
    def setup_ui(self):
        # Title with branding
        title_frame = tk.Frame(self.root, bg='#1a1a2e', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🌐 NexusController", 
                              font=("Arial", 24, "bold"), fg='#00d4ff', bg='#1a1a2e')
        title_label.pack(side='left', padx=20, pady=10)
        
        subtitle = tk.Label(title_frame, text="Central Command Hub", 
                           font=("Arial", 12), fg='#888', bg='#1a1a2e')
        subtitle.pack(side='left', pady=20)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg='#0f0f1e', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_frame, text="Nexus Ready", 
                                    fg='#00d4ff', bg='#0f0f1e')
        self.status_label.pack(side='left', padx=10)
        
        # Custom style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#1a1a2e', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2a2a3e', foreground='white', 
                       padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', '#3a3a4e')])
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        
        # Nexus Central (Dashboard)
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🎯 Nexus Central")
        self.create_dashboard_tab(dashboard_frame)
        
        # Local Node
        local_frame = ttk.Frame(self.notebook)
        self.notebook.add(local_frame, text="💻 Local Node")
        self.create_local_system_tab(local_frame)
        
        # Remote Nodes
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="🌍 Remote Nodes")
        self.create_servers_tab(servers_frame)
        
        # Cloud Bridge
        gdrive_frame = ttk.Frame(self.notebook)
        self.notebook.add(gdrive_frame, text="☁️ Cloud Bridge")
        self.create_gdrive_tab(gdrive_frame)
        
        # Sync Matrix
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="🔄 Sync Matrix")
        self.create_backup_tab(backup_frame)
        
        # Update Center
        update_frame = ttk.Frame(self.notebook)
        self.notebook.add(update_frame, text="🔄 Update Center")
        self.create_update_tab(update_frame)
        
        # Blockchain Hub
        eth_frame = ttk.Frame(self.notebook)
        self.notebook.add(eth_frame, text="⟠ Blockchain Hub")
        self.create_ethereum_tab(eth_frame)
        
        # Control Panel
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Control Panel")
        self.create_settings_tab(settings_frame)
        
    def create_dashboard_tab(self, parent):
        # Main container with dark theme
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header = tk.Label(main_frame, text="NEXUS COMMAND CENTER", 
                         font=("Courier", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
        header.pack(pady=10)
        
        # System overview
        overview_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='ridge', bd=2)
        overview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Grid layout
        left_frame = tk.Frame(overview_frame, bg='#1a1a2e')
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        right_frame = tk.Frame(overview_frame, bg='#1a1a2e')
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # Local Node Status
        local_frame = tk.LabelFrame(left_frame, text="LOCAL NODE STATUS", 
                                   font=("Courier", 10, "bold"),
                                   bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        local_frame.pack(fill='x', pady=5)
        
        self.local_cpu_label = tk.Label(local_frame, text="⚡ CPU: Scanning...", 
                                       bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.local_cpu_label.pack(anchor='w', padx=10, pady=2)
        
        self.local_mem_label = tk.Label(local_frame, text="💾 Memory: Scanning...", 
                                       bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.local_mem_label.pack(anchor='w', padx=10, pady=2)
        
        self.local_disk_label = tk.Label(local_frame, text="💿 Disk: Scanning...", 
                                        bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.local_disk_label.pack(anchor='w', padx=10, pady=2)
        
        # Remote Nodes Status
        remote_frame = tk.LabelFrame(right_frame, text="REMOTE NODES", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        remote_frame.pack(fill='x', pady=5)
        
        self.server_status_labels = {}
        for server_id, server_info in self.servers.items():
            label = tk.Label(remote_frame, text=f"🖥️ {server_info['name']}: Probing...", 
                           bg='#1a1a2e', fg='#fa0', font=("Courier", 10))
            label.pack(anchor='w', padx=10, pady=2)
            self.server_status_labels[server_id] = label
        
        # Quick Launch Panel
        launch_frame = tk.LabelFrame(main_frame, text="QUICK LAUNCH", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        launch_frame.pack(fill='x', padx=10, pady=10)
        
        button_frame = tk.Frame(launch_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        # Styled buttons
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'activeforeground': '#00ff00',
            'relief': 'raised',
            'bd': 2,
            'padx': 15,
            'pady': 5
        }
        
        tk.Button(button_frame, text="🧹 PURGE CACHE", 
                 command=self.quick_cleanup, **button_style).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="📡 MOUNT CLOUD", 
                 command=self.mount_drive, **button_style).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="🔄 SYNC ALL", 
                 command=self.sync_all, **button_style).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(button_frame, text="🔗 LINK TO EBON", 
                 command=lambda: self.connect_to_server('ebon'), **button_style).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="🚀 SYSTEM SCAN", 
                 command=self.analyze_system, **button_style).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="⚡ EMERGENCY", 
                 command=self.emergency_cleanup, **button_style).grid(row=1, column=2, padx=5, pady=5)
        
        # Update status in dashboard
        update_status_frame = tk.LabelFrame(main_frame, text="UPDATE STATUS", 
                                           font=("Courier", 10, "bold"),
                                           bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        update_status_frame.pack(fill='x', padx=10, pady=10)
        
        self.update_summary_label = tk.Label(update_status_frame, 
                                            text="🔄 Updates: Checking...", 
                                            bg='#1a1a2e', fg='#fa0', font=("Courier", 10))
        self.update_summary_label.pack(anchor='w', padx=10, pady=5)
        
    def create_local_system_tab(self, parent):
        # Dark themed local system tab
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # System info
        info_frame = tk.LabelFrame(main_frame, text="SYSTEM INTEL", 
                                  font=("Courier", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.system_info_text = tk.Text(info_frame, height=6, wrap='word',
                                       bg='#0a0a1e', fg='#0f8', font=('Courier', 10))
        self.system_info_text.pack(fill='x', padx=5, pady=5)
        
        # Cleanup options
        cleanup_frame = tk.LabelFrame(main_frame, text="PURGE OPTIONS", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        cleanup_frame.pack(fill='x', padx=10, pady=5)
        
        self.cleanup_vars = {}
        cleanup_options = [
            ("📦 Package Cache", "package_cache"),
            ("🌐 Browser Data", "browser_cache"),
            ("🗑️ Temp Files", "temp_files"),
            ("🐋 Docker Waste", "docker"),
            ("📄 Old Logs", "old_logs"),
            ("♻️ Trash Bin", "trash")
        ]
        
        check_style = {
            'bg': '#1a1a2e',
            'fg': '#00d4ff',
            'selectcolor': '#2a2a3e',
            'activebackground': '#1a1a2e',
            'font': ('Courier', 10)
        }
        
        for i, (name, key) in enumerate(cleanup_options):
            var = tk.BooleanVar(value=True)
            self.cleanup_vars[key] = var
            row = i // 3
            col = i % 3
            tk.Checkbutton(cleanup_frame, text=name, variable=var, **check_style).grid(
                row=row, column=col, sticky='w', padx=10, pady=5)
        
        # Action buttons
        action_frame = tk.Frame(main_frame, bg='#0f0f1e')
        action_frame.pack(fill='x', padx=10, pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 10
        }
        
        tk.Button(action_frame, text="🔍 ANALYZE", 
                 command=self.analyze_system, **button_style).pack(side='left', padx=5)
        tk.Button(action_frame, text="🧹 EXECUTE PURGE", 
                 command=self.start_cleanup, **button_style).pack(side='left', padx=5)
        tk.Button(action_frame, text="⚡ CRISIS MODE", 
                 command=self.emergency_cleanup, **button_style).pack(side='left', padx=5)
        
        # Output console
        output_frame = tk.LabelFrame(main_frame, text="CONSOLE OUTPUT", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.local_output = scrolledtext.ScrolledText(output_frame, height=10,
                                                     bg='#0a0a1e', fg='#0f8',
                                                     font=('Courier', 10))
        self.local_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_servers_tab(self, parent):
        # Dark themed server management
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Node list
        list_frame = tk.LabelFrame(main_frame, text="REMOTE NODE REGISTRY", 
                                  font=("Courier", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Server tree with custom style
        tree_style = ttk.Style()
        tree_style.configure("Nexus.Treeview",
                           background="#0a0a1e",
                           foreground="#00d4ff",
                           fieldbackground="#0a0a1e")
        
        columns = ('Status', 'IP', 'Services', 'Last Ping')
        self.server_tree = ttk.Treeview(list_frame, columns=columns, height=6,
                                       style="Nexus.Treeview")
        self.server_tree.heading('#0', text='Node ID')
        for col in columns:
            self.server_tree.heading(col, text=col)
            self.server_tree.column(col, width=120)
        
        self.server_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Populate servers
        for server_id, server_info in self.servers.items():
            self.server_tree.insert('', 'end', server_id, 
                                   text=server_info['name'],
                                   values=('Initializing...', server_info['host'], 
                                          ', '.join(server_info['services']), 'Never'))
        
        # Node Control Panel
        control_frame = tk.LabelFrame(main_frame, text="NODE CONTROL", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2
        }
        
        tk.Button(button_frame, text="🔗 ESTABLISH LINK", 
                 command=self.ssh_to_selected, **button_style).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="🌐 WEB INTERFACE", 
                 command=self.open_server_web, **button_style).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="📊 NODE STATS", 
                 command=self.get_server_stats, **button_style).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(button_frame, text="🔄 REFRESH", 
                 command=self.refresh_servers, **button_style).grid(row=0, column=3, padx=5, pady=5)
        
        # Terminal
        terminal_frame = tk.LabelFrame(main_frame, text="REMOTE TERMINAL", 
                                      font=("Courier", 10, "bold"),
                                      bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        terminal_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.server_terminal = scrolledtext.ScrolledText(terminal_frame, 
                                                        bg='#0a0a1e', fg='#0f8',
                                                        font=('Courier', 10),
                                                        insertbackground='#00ff00')
        self.server_terminal.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Command input
        cmd_frame = tk.Frame(terminal_frame, bg='#1a1a2e')
        cmd_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(cmd_frame, text="nexus>", bg='#1a1a2e', fg='#00d4ff',
                font=('Courier', 10, 'bold')).pack(side='left')
        self.server_cmd_entry = tk.Entry(cmd_frame, bg='#0a0a1e', fg='#0f8',
                                        font=('Courier', 10), insertbackground='#00ff00')
        self.server_cmd_entry.pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(cmd_frame, text="EXECUTE", command=self.run_server_command,
                 **button_style).pack(side='left')
        
    def create_gdrive_tab(self, parent):
        # Cloud Bridge interface
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Status
        status_frame = tk.LabelFrame(main_frame, text="CLOUD BRIDGE STATUS", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.rclone_status = tk.Label(status_frame, text="🔧 rclone: Checking subsystem...",
                                     bg='#1a1a2e', fg='#fa0', font=('Courier', 10))
        self.rclone_status.pack(anchor='w', padx=10, pady=5)
        
        self.mount_status = tk.Label(status_frame, text="📁 Mount: Verifying connection...",
                                    bg='#1a1a2e', fg='#fa0', font=('Courier', 10))
        self.mount_status.pack(anchor='w', padx=10, pady=5)
        
        # Actions
        actions_frame = tk.LabelFrame(main_frame, text="CLOUD OPERATIONS", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 15
        }
        
        tk.Button(button_frame, text="⚙️ CONFIGURE", 
                 command=self.configure_gdrive, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📡 MOUNT", 
                 command=self.mount_drive, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="🔄 SYNC", 
                 command=self.sync_gdrive, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📊 STATS", 
                 command=self.gdrive_stats, **button_style).pack(side='left', padx=5)
        
        # Output
        output_frame = tk.LabelFrame(main_frame, text="TRANSMISSION LOG", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.gdrive_output = scrolledtext.ScrolledText(output_frame,
                                                      bg='#0a0a1e', fg='#0f8',
                                                      font=('Courier', 10))
        self.gdrive_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_backup_tab(self, parent):
        # Sync Matrix interface
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Matrix view
        matrix_frame = tk.LabelFrame(main_frame, text="SYNC MATRIX CONFIG", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        matrix_frame.pack(fill='x', padx=10, pady=5)
        
        # Profile list
        self.backup_profiles = {
            'documents': {
                'name': 'Document Vault',
                'source': '~/Documents',
                'dest': 'ebon:~/Backups/Documents',
                'schedule': 'Daily'
            },
            'projects': {
                'name': 'Project Mirror',
                'source': '~/Projects',
                'dest': 'GoogleDrive:Projects',
                'schedule': 'On Change'
            },
            'nexus': {
                'name': 'Nexus Core',
                'source': '~/.config',
                'dest': 'ebon:~/Backups/Config',
                'schedule': 'Weekly'
            }
        }
        
        # Custom tree style
        columns = ('Source', 'Target', 'Schedule', 'Last Sync')
        self.backup_tree = ttk.Treeview(matrix_frame, columns=columns, height=6,
                                       style="Nexus.Treeview")
        self.backup_tree.heading('#0', text='Sync Profile')
        for col in columns:
            self.backup_tree.heading(col, text=col)
        
        self.backup_tree.pack(fill='x', padx=5, pady=5)
        
        # Populate profiles
        for profile_id, profile in self.backup_profiles.items():
            self.backup_tree.insert('', 'end', profile_id,
                                   text=profile['name'],
                                   values=(profile['source'], profile['dest'],
                                          profile['schedule'], 'Never'))
        
        # Matrix Control
        control_frame = tk.LabelFrame(main_frame, text="MATRIX CONTROL", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 15
        }
        
        tk.Button(button_frame, text="▶️ EXECUTE SYNC", 
                 command=self.run_backup, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="➕ NEW PROFILE", 
                 command=self.new_backup_profile, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="🔄 SYNC ALL", 
                 command=self.sync_all_backups, **button_style).pack(side='left', padx=5)
        
        # Sync Log
        log_frame = tk.LabelFrame(main_frame, text="SYNC OPERATIONS LOG", 
                                 font=("Courier", 10, "bold"),
                                 bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.backup_output = scrolledtext.ScrolledText(log_frame,
                                                      bg='#0a0a1e', fg='#0f8',
                                                      font=('Courier', 10))
        self.backup_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_update_tab(self, parent):
        """Update Center interface"""
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Update Overview
        overview_frame = tk.LabelFrame(main_frame, text="UPDATE OVERVIEW", 
                                      font=("Courier", 10, "bold"),
                                      bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        overview_frame.pack(fill='x', padx=10, pady=5)
        
        # Two columns for local and remote
        left_col = tk.Frame(overview_frame, bg='#1a1a2e')
        left_col.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        right_col = tk.Frame(overview_frame, bg='#1a1a2e')
        right_col.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # Local updates
        local_frame = tk.LabelFrame(left_col, text="LOCAL NODE", 
                                   font=("Courier", 9, "bold"),
                                   bg='#1a1a2e', fg='#0f8', relief='groove', bd=1)
        local_frame.pack(fill='x', pady=5)
        
        self.local_updates_label = tk.Label(local_frame, text="📦 Available: Checking...",
                                           bg='#1a1a2e', fg='#0f8', font=('Courier', 9))
        self.local_updates_label.pack(anchor='w', padx=5, pady=2)
        
        self.local_security_label = tk.Label(local_frame, text="🔒 Security: Checking...",
                                            bg='#1a1a2e', fg='#f80', font=('Courier', 9))
        self.local_security_label.pack(anchor='w', padx=5, pady=2)
        
        self.local_last_check_label = tk.Label(local_frame, text="⏰ Last Check: Never",
                                              bg='#1a1a2e', fg='#888', font=('Courier', 9))
        self.local_last_check_label.pack(anchor='w', padx=5, pady=2)
        
        # Remote updates
        remote_frame = tk.LabelFrame(right_col, text="REMOTE NODES", 
                                    font=("Courier", 9, "bold"),
                                    bg='#1a1a2e', fg='#fa0', relief='groove', bd=1)
        remote_frame.pack(fill='x', pady=5)
        
        self.remote_updates_labels = {}
        for server_id, server_info in self.servers.items():
            label = tk.Label(remote_frame, text=f"🖥️ {server_info['name']}: Checking...",
                           bg='#1a1a2e', fg='#fa0', font=('Courier', 9))
            label.pack(anchor='w', padx=5, pady=2)
            self.remote_updates_labels[server_id] = label
        
        # Update Controls
        control_frame = tk.LabelFrame(main_frame, text="UPDATE CONTROL", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 15
        }
        
        tk.Button(button_frame, text="🔍 CHECK UPDATES", 
                 command=self.check_all_updates, **button_style).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="🔒 SECURITY ONLY", 
                 command=self.install_security_updates, **button_style).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="📦 ALL UPDATES", 
                 command=self.install_all_updates, **button_style).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(button_frame, text="⚙️ CONFIGURE", 
                 command=self.configure_updates, **button_style).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="📋 UPDATE LOG", 
                 command=self.show_update_log, **button_style).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="🛡️ AUTO MODE", 
                 command=self.toggle_auto_updates, **button_style).grid(row=1, column=2, padx=5, pady=5)
        
        # Update Schedule
        schedule_frame = tk.LabelFrame(main_frame, text="UPDATE SCHEDULE", 
                                      font=("Courier", 10, "bold"),
                                      bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        schedule_frame.pack(fill='x', padx=10, pady=5)
        
        schedule_grid = tk.Frame(schedule_frame, bg='#1a1a2e')
        schedule_grid.pack(padx=20, pady=10)
        
        label_style = {'bg': '#1a1a2e', 'fg': '#00d4ff', 'font': ('Courier', 9)}
        
        tk.Label(schedule_grid, text="Security Updates:", **label_style).grid(row=0, column=0, sticky='w', pady=2)
        self.security_schedule_var = tk.StringVar(value="Daily at 02:00")
        tk.Label(schedule_grid, textvariable=self.security_schedule_var, 
                bg='#1a1a2e', fg='#0f8', font=('Courier', 9)).grid(row=0, column=1, sticky='w', padx=10)
        
        tk.Label(schedule_grid, text="System Updates:", **label_style).grid(row=1, column=0, sticky='w', pady=2)
        self.system_schedule_var = tk.StringVar(value="Weekly on Sunday")
        tk.Label(schedule_grid, textvariable=self.system_schedule_var, 
                bg='#1a1a2e', fg='#0f8', font=('Courier', 9)).grid(row=1, column=1, sticky='w', padx=10)
        
        tk.Label(schedule_grid, text="Next Check:", **label_style).grid(row=2, column=0, sticky='w', pady=2)
        self.next_check_var = tk.StringVar(value="Calculating...")
        tk.Label(schedule_grid, textvariable=self.next_check_var, 
                bg='#1a1a2e', fg='#fa0', font=('Courier', 9)).grid(row=2, column=1, sticky='w', padx=10)
        
        # Update Log
        log_frame = tk.LabelFrame(main_frame, text="UPDATE OPERATIONS LOG", 
                                 font=("Courier", 10, "bold"),
                                 bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.update_log = scrolledtext.ScrolledText(log_frame,
                                                   bg='#0a0a1e', fg='#0f8',
                                                   font=('Courier', 9))
        self.update_log.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize with welcome message
        self.update_log.insert(tk.END, "[NEXUS UPDATE CENTER] Initializing...\n")
        self.update_log.insert(tk.END, "[INFO] Update checking will begin automatically\n")
        self.update_log.insert(tk.END, "[INFO] Security updates: Auto-install enabled\n")
        self.update_log.insert(tk.END, "[INFO] System updates: Manual approval required\n\n")
        
    def create_ethereum_tab(self, parent):
        # Blockchain Hub interface
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Chain Status
        status_frame = tk.LabelFrame(main_frame, text="BLOCKCHAIN STATUS", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.eth_status_label = tk.Label(status_frame, text="⟠ Node: Not initialized",
                                        bg='#1a1a2e', fg='#fa0', font=('Courier', 10))
        self.eth_status_label.pack(anchor='w', padx=10, pady=5)
        
        self.eth_sync_label = tk.Label(status_frame, text="📊 Sync: Offline",
                                      bg='#1a1a2e', fg='#fa0', font=('Courier', 10))
        self.eth_sync_label.pack(anchor='w', padx=10, pady=5)
        
        # Node Control
        control_frame = tk.LabelFrame(main_frame, text="NODE OPERATIONS", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 15
        }
        
        tk.Button(button_frame, text="🚀 DEPLOY", 
                 command=self.deploy_eth_node, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="▶️ START", 
                 command=self.start_eth_node, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="⏹️ STOP", 
                 command=self.stop_eth_node, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📊 STATS", 
                 command=self.eth_stats, **button_style).pack(side='left', padx=5)
        
        # Chain Console
        console_frame = tk.LabelFrame(main_frame, text="BLOCKCHAIN CONSOLE", 
                                     font=("Courier", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        console_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.eth_output = scrolledtext.ScrolledText(console_frame,
                                                   bg='#0a0a1e', fg='#0f8',
                                                   font=('Courier', 10))
        self.eth_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_settings_tab(self, parent):
        # Control Panel
        main_frame = tk.Frame(parent, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Node Configuration
        node_frame = tk.LabelFrame(main_frame, text="NODE CONFIGURATION", 
                                  font=("Courier", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        node_frame.pack(fill='x', padx=10, pady=5)
        
        button_style = {
            'font': ('Courier', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 20,
            'pady': 10
        }
        
        tk.Button(node_frame, text="➕ ADD REMOTE NODE", 
                 command=self.add_server_dialog, **button_style).pack(pady=20)
        
        # Nexus Settings
        nexus_frame = tk.LabelFrame(main_frame, text="NEXUS PARAMETERS", 
                                   font=("Courier", 10, "bold"),
                                   bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        nexus_frame.pack(fill='x', padx=10, pady=5)
        
        settings_grid = tk.Frame(nexus_frame, bg='#1a1a2e')
        settings_grid.pack(padx=20, pady=20)
        
        label_style = {'bg': '#1a1a2e', 'fg': '#00d4ff', 'font': ('Courier', 10)}
        entry_style = {'bg': '#0a0a1e', 'fg': '#0f8', 'font': ('Courier', 10),
                      'insertbackground': '#00ff00'}
        
        tk.Label(settings_grid, text="Cloud Mount:", **label_style).grid(row=0, column=0, sticky='w', pady=5)
        self.mount_path_var = tk.StringVar(value=str(Path.home() / "GoogleDrive"))
        tk.Entry(settings_grid, textvariable=self.mount_path_var, width=40, **entry_style).grid(row=0, column=1, padx=10)
        
        tk.Label(settings_grid, text="Backup Vault:", **label_style).grid(row=1, column=0, sticky='w', pady=5)
        self.backup_dir_var = tk.StringVar(value=str(Path.home() / "Backups"))
        tk.Entry(settings_grid, textvariable=self.backup_dir_var, width=40, **entry_style).grid(row=1, column=1, padx=10)
        
        tk.Label(settings_grid, text="Sync Interval:", **label_style).grid(row=2, column=0, sticky='w', pady=5)
        self.sync_interval_var = tk.StringVar(value="3600")
        tk.Entry(settings_grid, textvariable=self.sync_interval_var, width=10, **entry_style).grid(row=2, column=1, sticky='w', padx=10)
        
        # Save Configuration
        tk.Button(main_frame, text="💾 SAVE CONFIGURATION", 
                 command=self.save_settings, **button_style).pack(pady=30)
        
    # Core functionality methods (same as before but with updated status messages)
    def check_initial_status(self):
        """Initialize Nexus systems"""
        self.update_status("Initializing Nexus systems...")
        threading.Thread(target=self._check_status_thread, daemon=True).start()
        
    def _check_status_thread(self):
        """Background status monitor"""
        try:
            # Check local node
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.safe_ui_update(self.local_cpu_label.config, text=f"⚡ CPU: {cpu}% utilized")
            self.safe_ui_update(self.local_mem_label.config, text=f"💾 Memory: {mem}% allocated")
            self.safe_ui_update(self.local_disk_label.config, text=f"💿 Disk: {disk}% occupied")
            
            # Update system intel
            info = f"Node ID: {socket.gethostname()}\n"
            info += f"Platform: {sys.platform}\n"
            info += f"CPU Cores: {psutil.cpu_count()}\n"
            info += f"Total Memory: {psutil.virtual_memory().total // (1024**3)} GB"
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(1.0, info)
            
        except Exception as e:
            self.update_status(f"System scan error: {e}")
            
        # Probe remote nodes
        self.refresh_servers()
        
    def refresh_servers(self):
        """Probe all remote nodes"""
        for server_id, server_info in self.servers.items():
            self.check_server_status(server_id)
            
    def check_server_status(self, server_id):
        """Probe node status"""
        server_info = self.servers[server_id]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_info['host'], server_info['port']))
            sock.close()
            
            if result == 0:
                status = "🟢 ONLINE"
                self.safe_ui_update(self.server_status_labels[server_id].config,
                                   text=f"🖥️ {server_info['name']}: ACTIVE",
                                   fg='#0f8')
            else:
                status = "🔴 OFFLINE"
                self.safe_ui_update(self.server_status_labels[server_id].config,
                                   text=f"🖥️ {server_info['name']}: UNREACHABLE",
                                   fg='#f00')
                
            self.server_tree.set(server_id, 'Status', status)
            self.server_tree.set(server_id, 'Last Ping', 
                               datetime.now().strftime('%H:%M:%S'))
            
        except Exception as e:
            self.update_status(f"Node probe failed: {e}")
            
    def connect_to_server(self, server_id):
        """Establish link to remote node"""
        server_info = self.servers.get(server_id)
        if not server_info:
            messagebox.showerror("NEXUS ERROR", "Node not found in registry")
            return
            
        self.notebook.select(2)  # Switch to Remote Nodes
        self.server_terminal.insert(tk.END, f"\n[NEXUS] Establishing secure link to {server_info['name']}...\n")
        
        threading.Thread(target=self._ssh_connect_thread, 
                        args=(server_id,), daemon=True).start()
        
    def _ssh_connect_thread(self, server_id):
        """Secure link establishment"""
        server_info = self.servers[server_id]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                server_info['host'],
                port=server_info['port'],
                username=server_info['username'],
                timeout=10
            )
            
            self.ssh_connections[server_id] = ssh
            self.server_terminal.insert(tk.END, 
                f"[✓] Secure link established to {server_info['name']}\n\n")
            
            # Run system probe
            stdin, stdout, stderr = ssh.exec_command('uname -a && echo && df -h')
            output = stdout.read().decode()
            self.server_terminal.insert(tk.END, output + "\n")
            
        except Exception as e:
            self.server_terminal.insert(tk.END, 
                f"\n[✗] Link failed: {str(e)}\n")
            self.server_terminal.insert(tk.END, 
                "\n[!] Verify SSH keys or execute:\n")
            self.server_terminal.insert(tk.END, 
                f"ssh-copy-id {server_info['username']}@{server_info['host']}\n")
            
    def run_server_command(self):
        """Execute remote command"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("NEXUS", "Select target node")
            return
            
        server_id = selection[0]
        command = self.server_cmd_entry.get()
        if not command:
            return
            
        self.server_cmd_entry.delete(0, tk.END)
        self.server_terminal.insert(tk.END, f"\nnexus> {command}\n")
        
        threading.Thread(target=self._run_remote_command, 
                        args=(server_id, command), daemon=True).start()
        
    def _run_remote_command(self, server_id, command):
        """Execute on remote node"""
        try:
            ssh = self.ssh_connections.get(server_id)
            if not ssh:
                self._ssh_connect_thread(server_id)
                ssh = self.ssh_connections.get(server_id)
                
            if ssh:
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if output:
                    self.server_terminal.insert(tk.END, output)
                if error:
                    self.server_terminal.insert(tk.END, f"[ERROR] {error}")
                    
        except Exception as e:
            self.server_terminal.insert(tk.END, f"\n[NEXUS ERROR] {str(e)}\n")
            
    def update_status(self, message):
        """Update Nexus status"""
        self.status_label.config(text=f"NEXUS: {message}")
        
    def save_settings(self):
        """Save Nexus configuration"""
        settings = {
            'mount_path': self.mount_path_var.get(),
            'backup_dir': self.backup_dir_var.get(),
            'sync_interval': self.sync_interval_var.get(),
            'servers': self.servers
        }
        
        settings_file = Path.home() / '.config' / 'nexus-controller' / 'nexus.json'
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            
        messagebox.showinfo("NEXUS", "Configuration saved to nexus.json")
        
    def start_update_scheduler(self):
        """Start the update checking scheduler"""
        if not self.update_scheduler_running:
            self.update_scheduler_running = True
            threading.Thread(target=self._update_scheduler_loop, daemon=True).start()
            self.log_update("[NEXUS] Update scheduler started")
            
    def _update_scheduler_loop(self):
        """Background update checking loop"""
        while self.update_scheduler_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for updates
                if self.should_check_updates():
                    self.log_update(f"[SCHEDULED] Checking for updates at {current_time.strftime('%H:%M:%S')}")
                    self.check_all_updates()
                    
                # Sleep for 1 hour between checks
                time.sleep(3600)
                
            except Exception as e:
                self.log_update(f"[ERROR] Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
                
    def should_check_updates(self):
        """Determine if it's time to check for updates"""
        last_check = self.update_status['local'].get('last_check')
        if not last_check:
            return True
            
        # Check every 6 hours
        return datetime.now() - last_check > timedelta(hours=6)
        
    def check_all_updates(self):
        """Check for updates on all systems"""
        self.log_update("[NEXUS] Initiating system-wide update check...")
        
        # Check local updates
        threading.Thread(target=self.check_local_updates, daemon=True).start()
        
        # Check remote servers
        for server_id in self.servers:
            threading.Thread(target=self.check_remote_updates, args=(server_id,), daemon=True).start()
            
    def check_local_updates(self):
        """Check for updates on local system"""
        try:
            self.log_update("[LOCAL] Checking for available updates...")
            
            # Update package database
            result = subprocess.run("sudo apt update", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.log_update(f"[ERROR] Failed to update package database: {result.stderr}")
                return
                
            # Check for upgradable packages
            result = subprocess.run("apt list --upgradable", shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\\n')
                total_updates = len([line for line in lines if '/' in line and 'upgradable' in line])
                
                # Check for security updates
                security_result = subprocess.run(
                    "apt list --upgradable | grep -i security", 
                    shell=True, capture_output=True, text=True
                )
                security_lines = security_result.stdout.strip().split('\\n') if security_result.stdout else []
                security_updates = len([line for line in security_lines if line.strip()])
                
                # Update status
                self.update_status['local'] = {
                    'available': total_updates,
                    'security': security_updates,
                    'last_check': datetime.now()
                }
                
                # Update UI safely
                self.safe_ui_update(self.local_updates_label.config, text=f"📦 Available: {total_updates}")
                self.safe_ui_update(self.local_security_label.config, 
                                   text=f"🔒 Security: {security_updates}",
                                   fg='#f00' if security_updates > 0 else '#0f8')
                self.safe_ui_update(self.local_last_check_label.config,
                                   text=f"⏰ Last Check: {datetime.now().strftime('%H:%M:%S')}")
                
                # Update dashboard summary
                total_all = sum(server.get('available', 0) for server in self.update_status['servers'].values()) + total_updates
                total_security = sum(server.get('security', 0) for server in self.update_status['servers'].values()) + security_updates
                
                self.safe_ui_update(self.update_summary_label.config,
                                   text=f"🔄 Updates: {total_all} available ({total_security} security)",
                                   fg='#f00' if total_security > 0 else '#0f8')
                
                self.log_update(f"[LOCAL] Found {total_updates} updates ({security_updates} security)")
                
                # Auto-install security updates if enabled
                if security_updates > 0 and self.get_setting('auto_security_updates', True):
                    self.log_update("[AUTO] Installing security updates...")
                    threading.Thread(target=self.install_security_updates, daemon=True).start()
                    
        except Exception as e:
            self.log_update(f"[ERROR] Local update check failed: {e}")
            
    def check_remote_updates(self, server_id):
        """Check for updates on remote server"""
        try:
            server_info = self.servers[server_id]
            self.log_update(f"[{server_info['name'].upper()}] Checking for updates...")
            
            ssh = self.ssh_connections.get(server_id)
            if not ssh:
                # Try to connect
                self._ssh_connect_thread(server_id)
                ssh = self.ssh_connections.get(server_id)
                
            if not ssh:
                self.log_update(f"[ERROR] Cannot connect to {server_info['name']}")
                return
                
            # Check updates on remote server
            stdin, stdout, stderr = ssh.exec_command('sudo apt update && apt list --upgradable')
            output = stdout.read().decode()
            
            if output:
                lines = output.strip().split('\\n')
                total_updates = len([line for line in lines if '/' in line and 'upgradable' in line])
                
                # Check security updates
                stdin, stdout, stderr = ssh.exec_command('apt list --upgradable | grep -i security')
                security_output = stdout.read().decode()
                security_lines = security_output.strip().split('\\n') if security_output else []
                security_updates = len([line for line in security_lines if line.strip()])
                
                # Update status
                self.update_status['servers'][server_id] = {
                    'available': total_updates,
                    'security': security_updates,
                    'last_check': datetime.now()
                }
                
                # Update UI safely
                label = self.remote_updates_labels[server_id]
                self.safe_ui_update(label.config,
                                   text=f"🖥️ {server_info['name']}: {total_updates} updates ({security_updates} security)",
                                   fg='#f00' if security_updates > 0 else '#0f8')
                
                self.log_update(f"[{server_info['name'].upper()}] Found {total_updates} updates ({security_updates} security)")
                
        except Exception as e:
            self.log_update(f"[ERROR] Remote update check failed for {server_id}: {e}")
            
    def install_security_updates(self):
        """Install security updates on all systems"""
        self.log_update("[NEXUS] Installing security updates on all systems...")
        
        # Local security updates
        threading.Thread(target=self._install_local_security_updates, daemon=True).start()
        
        # Remote security updates
        for server_id in self.servers:
            threading.Thread(target=self._install_remote_security_updates, args=(server_id,), daemon=True).start()
            
    def _install_local_security_updates(self):
        """Install security updates locally"""
        try:
            self.log_update("[LOCAL] Installing security updates...")
            
            # Use unattended-upgrades for security updates
            result = subprocess.run(
                "sudo unattended-upgrade -d",
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.log_update("[LOCAL] Security updates installed successfully")
            else:
                self.log_update(f"[ERROR] Security update failed: {result.stderr}")
                
            # Recheck updates
            self.check_local_updates()
            
        except Exception as e:
            self.log_update(f"[ERROR] Local security update failed: {e}")
            
    def _install_remote_security_updates(self, server_id):
        """Install security updates on remote server"""
        try:
            server_info = self.servers[server_id]
            ssh = self.ssh_connections.get(server_id)
            
            if not ssh:
                self.log_update(f"[ERROR] No connection to {server_info['name']}")
                return
                
            self.log_update(f"[{server_info['name'].upper()}] Installing security updates...")
            
            # Install security updates
            stdin, stdout, stderr = ssh.exec_command('sudo unattended-upgrade -d')
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                self.log_update(f"[ERROR] {server_info['name']} security update failed: {error}")
            else:
                self.log_update(f"[{server_info['name'].upper()}] Security updates completed")
                
            # Recheck updates
            self.check_remote_updates(server_id)
            
        except Exception as e:
            self.log_update(f"[ERROR] Remote security update failed for {server_id}: {e}")
            
    def install_all_updates(self):
        """Install all available updates"""
        if messagebox.askyesno("NEXUS UPDATE", 
                              "Install ALL updates on all systems?\\n\\nThis may take several minutes."):
            self.log_update("[NEXUS] Installing ALL updates on all systems...")
            
            # Local updates
            threading.Thread(target=self._install_all_local_updates, daemon=True).start()
            
            # Remote updates
            for server_id in self.servers:
                threading.Thread(target=self._install_all_remote_updates, args=(server_id,), daemon=True).start()
                
    def _install_all_local_updates(self):
        """Install all updates locally"""
        try:
            self.log_update("[LOCAL] Installing all updates...")
            
            result = subprocess.run(
                "sudo apt upgrade -y",
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.log_update("[LOCAL] All updates installed successfully")
            else:
                self.log_update(f"[ERROR] Update failed: {result.stderr}")
                
            self.check_local_updates()
            
        except Exception as e:
            self.log_update(f"[ERROR] Local update failed: {e}")
            
    def _install_all_remote_updates(self, server_id):
        """Install all updates on remote server"""
        try:
            server_info = self.servers[server_id]
            ssh = self.ssh_connections.get(server_id)
            
            if not ssh:
                return
                
            self.log_update(f"[{server_info['name'].upper()}] Installing all updates...")
            
            stdin, stdout, stderr = ssh.exec_command('sudo apt upgrade -y')
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                self.log_update(f"[ERROR] {server_info['name']} update failed: {error}")
            else:
                self.log_update(f"[{server_info['name'].upper()}] All updates completed")
                
            self.check_remote_updates(server_id)
            
        except Exception as e:
            self.log_update(f"[ERROR] Remote update failed for {server_id}: {e}")
            
    def configure_updates(self):
        """Open update configuration dialog"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Update Configuration")
        config_window.geometry("500x400")
        config_window.configure(bg='#0f0f1e')
        
        # Configuration options
        frame = tk.Frame(config_window, bg='#1a1a2e', relief='groove', bd=2)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="UPDATE CONFIGURATION", 
                font=("Courier", 14, "bold"), fg='#00d4ff', bg='#1a1a2e').pack(pady=10)
        
        # Auto security updates
        self.auto_security_var = tk.BooleanVar(value=self.get_setting('auto_security_updates', True))
        tk.Checkbutton(frame, text="Auto-install security updates", 
                      variable=self.auto_security_var,
                      bg='#1a1a2e', fg='#0f8', selectcolor='#2a2a3e',
                      font=('Courier', 10)).pack(anchor='w', padx=20, pady=5)
        
        # Auto reboot
        self.auto_reboot_var = tk.BooleanVar(value=self.get_setting('auto_reboot', False))
        tk.Checkbutton(frame, text="Auto-reboot after kernel updates", 
                      variable=self.auto_reboot_var,
                      bg='#1a1a2e', fg='#0f8', selectcolor='#2a2a3e',
                      font=('Courier', 10)).pack(anchor='w', padx=20, pady=5)
        
        # Check interval
        tk.Label(frame, text="Check interval (hours):", 
                bg='#1a1a2e', fg='#00d4ff', font=('Courier', 10)).pack(anchor='w', padx=20, pady=(20,5))
        self.check_interval_var = tk.StringVar(value=str(self.get_setting('check_interval', 6)))
        tk.Entry(frame, textvariable=self.check_interval_var, width=10,
                bg='#0a0a1e', fg='#0f8', font=('Courier', 10)).pack(anchor='w', padx=20)
        
        # Save button
        tk.Button(frame, text="SAVE CONFIGURATION", 
                 command=lambda: self.save_update_config(config_window),
                 font=('Courier', 10, 'bold'), bg='#2a2a3e', fg='#00d4ff',
                 activebackground='#3a3a4e').pack(pady=20)
        
    def save_update_config(self, window):
        """Save update configuration"""
        try:
            settings = {
                'auto_security_updates': self.auto_security_var.get(),
                'auto_reboot': self.auto_reboot_var.get(),
                'check_interval': int(self.check_interval_var.get())
            }
            
            # Save to config file
            config_file = Path.home() / '.config' / 'nexus-controller' / 'update_config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            self.log_update("[CONFIG] Update configuration saved")
            window.destroy()
            
        except Exception as e:
            self.log_update(f"[ERROR] Failed to save config: {e}")
            
    def get_setting(self, key, default=None):
        """Get update setting"""
        try:
            config_file = Path.home() / '.config' / 'nexus-controller' / 'update_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                return settings.get(key, default)
        except:
            pass
        return default
        
    def show_update_log(self):
        """Show detailed update log"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Update History")
        log_window.geometry("800x600")
        log_window.configure(bg='#0f0f1e')
        
        # Log display
        log_text = scrolledtext.ScrolledText(log_window,
                                           bg='#0a0a1e', fg='#0f8',
                                           font=('Courier', 9))
        log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Load system update logs
        try:
            # Check apt history
            result = subprocess.run("grep 'upgrade\\|install' /var/log/apt/history.log | tail -50",
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                log_text.insert(tk.END, "[SYSTEM UPDATE HISTORY]\\n")
                log_text.insert(tk.END, "=" * 50 + "\\n")
                log_text.insert(tk.END, result.stdout)
                log_text.insert(tk.END, "\\n\\n")
                
            # Check unattended-upgrades log
            result = subprocess.run("tail -50 /var/log/unattended-upgrades/unattended-upgrades.log",
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                log_text.insert(tk.END, "[SECURITY UPDATE HISTORY]\\n")
                log_text.insert(tk.END, "=" * 50 + "\\n")
                log_text.insert(tk.END, result.stdout)
                
        except Exception as e:
            log_text.insert(tk.END, f"Error loading system logs: {e}")
            
    def toggle_auto_updates(self):
        """Toggle automatic update mode"""
        current = self.get_setting('auto_security_updates', True)
        new_value = not current
        
        # Update setting
        self.auto_security_var = tk.BooleanVar(value=new_value)
        config_window = tk.Toplevel()
        config_window.withdraw()  # Hide window
        self.save_update_config(config_window)
        
        mode = "ENABLED" if new_value else "DISABLED"
        self.log_update(f"[CONFIG] Auto security updates {mode}")
        
    def log_update(self, message):
        """Log update message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\\n"
        
        try:
            self.update_log.insert(tk.END, full_message)
            self.update_log.see(tk.END)
        except:
            pass  # UI might not be ready yet
            
        # Also log to file
        try:
            log_file = Path.home() / '.config' / 'nexus-controller' / 'update.log'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\\n")
        except:
            pass

    def delayed_initialization(self):
        """Initialize background tasks after UI is ready"""
        try:
            self.check_initial_status()
            self.start_update_scheduler()
            # Schedule UI update processing
            self.process_ui_updates()
        except Exception as e:
            print(f"Error in delayed initialization: {e}")
            
    def on_closing(self):
        """Handle application shutdown"""
        self.shutdown_flag = True
        self.update_scheduler_running = False
        
        # Close SSH connections
        for ssh in self.ssh_connections.values():
            try:
                ssh.close()
            except:
                pass
                
        self.root.destroy()
        
    def safe_ui_update(self, update_func, *args, **kwargs):
        """Thread-safe UI updates"""
        try:
            if not self.shutdown_flag:
                self.root.after_idle(update_func, *args, **kwargs)
        except Exception as e:
            print(f"UI update error: {e}")
            
    def process_ui_updates(self):
        """Process queued UI updates"""
        if not self.shutdown_flag:
            try:
                # Process any queued updates
                while self.ui_update_queue:
                    update_func, args, kwargs = self.ui_update_queue.pop(0)
                    try:
                        update_func(*args, **kwargs)
                    except Exception as e:
                        print(f"Error processing UI update: {e}")
                        
                # Schedule next update cycle
                self.root.after(100, self.process_ui_updates)
            except Exception as e:
                print(f"Error in UI update processing: {e}")

    def run(self):
        """Initialize Nexus Controller"""
        try:
            print("Starting NexusController main loop...")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Shutdown requested...")
            self.on_closing()
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        
    # All other methods remain the same...
    def ssh_to_selected(self):
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("NEXUS", "Select target node")
            return
        server_id = selection[0]
        self.connect_to_server(server_id)
        
    def open_server_web(self):
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("NEXUS", "Select target node")
            return
        server_id = selection[0]
        server_info = self.servers[server_id]
        import webbrowser
        webbrowser.open(f"http://{server_info['host']}")
        
    def get_server_stats(self):
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("NEXUS", "Select target node")
            return
        server_id = selection[0]
        commands = [
            "echo '[NEXUS SYSTEM PROBE]'",
            "echo '===================='",
            "uname -a",
            "echo '\n[CPU INTEL]'",
            "lscpu | grep 'Model name\\|CPU(s)'",
            "echo '\n[MEMORY BANKS]'",
            "free -h",
            "echo '\n[STORAGE MATRIX]'",
            "df -h",
            "echo '\n[NETWORK INTERFACES]'",
            "ip -s link | head -20",
            "echo '\n[ACTIVE SERVICES]'",
            "systemctl list-units --type=service --state=running | head -10"
        ]
        full_command = " && ".join(commands)
        self.server_cmd_entry.insert(0, full_command)
        self.run_server_command()
        
    def quick_cleanup(self):
        self.notebook.select(1)
        self.cleanup_vars['package_cache'].set(True)
        self.cleanup_vars['temp_files'].set(True)
        self.cleanup_vars['trash'].set(True)
        self.start_cleanup()
        
    def analyze_system(self):
        self.local_output.delete(1.0, tk.END)
        self.local_output.insert(tk.END, "[NEXUS] Initiating system scan...\n\n")
        threading.Thread(target=self._analyze_thread, daemon=True).start()
        
    def _analyze_thread(self):
        try:
            checks = [
                ("Package cache", "du -sh /var/cache/apt/archives 2>/dev/null"),
                ("Temp files", "du -sh /tmp 2>/dev/null"),
                ("User cache", f"du -sh {Path.home()}/.cache 2>/dev/null"),
                ("Trash", f"du -sh {Path.home()}/.local/share/Trash 2>/dev/null"),
            ]
            for name, cmd in checks:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    size = result.stdout.split()[0]
                    self.local_output.insert(tk.END, f"[✓] {name}: {size}\n")
            self.local_output.insert(tk.END, "\n[NEXUS] Scan complete.\n")
        except Exception as e:
            self.local_output.insert(tk.END, f"\n[ERROR] {str(e)}\n")
            
    def start_cleanup(self):
        self.local_output.delete(1.0, tk.END)
        self.local_output.insert(tk.END, "[NEXUS] Initiating purge sequence...\n\n")
        threading.Thread(target=self._cleanup_thread, daemon=True).start()
        
    def _cleanup_thread(self):
        try:
            if self.cleanup_vars['package_cache'].get():
                self.local_output.insert(tk.END, "[>] Purging package cache...\n")
                subprocess.run("sudo apt-get clean", shell=True)
            if self.cleanup_vars['temp_files'].get():
                self.local_output.insert(tk.END, "[>] Eliminating temp files...\n")
                subprocess.run("find /tmp -type f -atime +7 -delete 2>/dev/null", shell=True)
            if self.cleanup_vars['trash'].get():
                self.local_output.insert(tk.END, "[>] Emptying trash...\n")
                subprocess.run(f"rm -rf {Path.home()}/.local/share/Trash/*", shell=True)
            self.local_output.insert(tk.END, "\n[NEXUS] Purge sequence complete.\n")
        except Exception as e:
            self.local_output.insert(tk.END, f"\n[ERROR] {str(e)}\n")
            
    def emergency_cleanup(self):
        if messagebox.askyesno("NEXUS CRISIS MODE", 
                              "Execute aggressive system purge?"):
            for var in self.cleanup_vars.values():
                var.set(True)
            self.start_cleanup()
            
    def mount_drive(self):
        self.notebook.select(3)
        self.gdrive_output.delete(1.0, tk.END)
        self.gdrive_output.insert(tk.END, "[NEXUS] Establishing cloud bridge...\n")
        mount_point = self.mount_path_var.get()
        cmd = f"rclone mount googledrive: {mount_point} --daemon"
        threading.Thread(target=lambda: self.run_command(cmd, self.gdrive_output), 
                        daemon=True).start()
        
    def sync_all(self):
        self.notebook.select(4)
        self.sync_all_backups()
        
    def run_command(self, command, output_widget):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output_widget.insert(tk.END, result.stdout)
            if result.stderr:
                output_widget.insert(tk.END, f"\n[ERROR] {result.stderr}")
            output_widget.see(tk.END)
        except Exception as e:
            output_widget.insert(tk.END, f"\n[EXCEPTION] {str(e)}")
            
    def configure_gdrive(self):
        subprocess.Popen(['gnome-terminal', '--', 'rclone', 'config'])
        
    def sync_gdrive(self):
        self.gdrive_output.delete(1.0, tk.END)
        cmd = "rclone sync ~/Documents googledrive:Documents -P"
        threading.Thread(target=lambda: self.run_command(cmd, self.gdrive_output), 
                        daemon=True).start()
        
    def gdrive_stats(self):
        cmd = "rclone about googledrive:"
        threading.Thread(target=lambda: self.run_command(cmd, self.gdrive_output), 
                        daemon=True).start()
        
    def run_backup(self):
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("NEXUS", "Select sync profile")
            return
        
    def new_backup_profile(self):
        pass
        
    def sync_all_backups(self):
        self.backup_output.delete(1.0, tk.END)
        self.backup_output.insert(tk.END, "[NEXUS] Initiating matrix sync...\n")
        
    def deploy_eth_node(self):
        self.eth_output.insert(tk.END, "[NEXUS] Blockchain deployment pending...\n")
        
    def start_eth_node(self):
        self.eth_output.insert(tk.END, "[NEXUS] Starting blockchain node...\n")
        
    def stop_eth_node(self):
        self.eth_output.insert(tk.END, "[NEXUS] Stopping blockchain node...\n")
        
    def eth_stats(self):
        self.eth_output.insert(tk.END, "[NEXUS] Blockchain statistics unavailable\n")
        
    def add_server_dialog(self):
        pass

if __name__ == '__main__':
    # Verify dependencies
    try:
        import paramiko
    except ImportError:
        print("[NEXUS] Installing SSH subsystem...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"])
        import paramiko
        
    try:
        import psutil
    except ImportError:
        print("[NEXUS] Installing system monitor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
        
    # Initialize Nexus
    nexus = NexusController()
    nexus.run()