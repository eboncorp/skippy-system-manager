#!/usr/bin/env python3
"""
NexusController - Fixed Version
Avoiding the specific font/color combination that causes segfault
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
        print("Initializing NexusController (Fixed Version)...")
        
        try:
            self.root = tk.Tk()
            self.root.title("NexusController - Central Command Hub")
            self.root.geometry("1100x700")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.resizable(True, True)
            
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
        
        try:
            print("Creating UI...")
            self.setup_ui()
            print("Scheduling delayed initialization...")
            self.root.after(1000, self.delayed_initialization)
        except Exception as e:
            print(f"Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
    def setup_ui(self):
        """Create UI with safe styling"""
        # Title with safe styling
        title_frame = tk.Frame(self.root, bg='#1a1a2e', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        # Use Arial instead of Courier to avoid segfault
        title_label = tk.Label(title_frame, text="🌐 NexusController", 
                              font=("Arial", 20, "bold"), fg='#00d4ff', bg='#1a1a2e')
        title_label.pack(side='left', padx=20, pady=10)
        
        subtitle = tk.Label(title_frame, text="Central Command Hub", 
                           font=("Arial", 10), fg='#888', bg='#1a1a2e')
        subtitle.pack(side='left', pady=20)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg='#0f0f1e', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_frame, text="Nexus Ready", 
                                    fg='#00d4ff', bg='#0f0f1e', font=("Arial", 9))
        self.status_label.pack(side='left', padx=10)
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        print("Creating dashboard...")
        self.create_safe_dashboard()
        
        print("Creating system tab...")
        self.create_system_tab()
        
        print("Creating servers tab...")
        self.create_servers_tab()
        
        print("Creating update tab...")
        self.create_update_tab()
        
        print("Creating settings tab...")
        self.create_settings_tab()
        
    def create_safe_dashboard(self):
        """Create dashboard with safe styling to avoid segfault"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🎯 Dashboard")
        
        main_frame = tk.Frame(dashboard_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Header with safe font
        header = tk.Label(main_frame, text="NEXUS COMMAND CENTER", 
                         font=("Arial", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
        header.pack(pady=10)
        
        # System overview
        overview_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='ridge', bd=2)
        overview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Two columns
        left_frame = tk.Frame(overview_frame, bg='#1a1a2e')
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        right_frame = tk.Frame(overview_frame, bg='#1a1a2e')
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # Local system status - using Arial font
        local_frame = tk.LabelFrame(left_frame, text="LOCAL NODE STATUS", 
                                   font=("Arial", 10, "bold"),
                                   bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        local_frame.pack(fill='x', pady=5)
        
        self.local_cpu_label = tk.Label(local_frame, text="⚡ CPU: Scanning...", 
                                       bg='#1a1a2e', fg='#0f8', font=("Arial", 9))
        self.local_cpu_label.pack(anchor='w', padx=10, pady=2)
        
        self.local_mem_label = tk.Label(local_frame, text="💾 Memory: Scanning...", 
                                       bg='#1a1a2e', fg='#0f8', font=("Arial", 9))
        self.local_mem_label.pack(anchor='w', padx=10, pady=2)
        
        self.local_disk_label = tk.Label(local_frame, text="💿 Disk: Scanning...", 
                                        bg='#1a1a2e', fg='#0f8', font=("Arial", 9))
        self.local_disk_label.pack(anchor='w', padx=10, pady=2)
        
        # Remote servers status
        remote_frame = tk.LabelFrame(right_frame, text="REMOTE NODES", 
                                    font=("Arial", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        remote_frame.pack(fill='x', pady=5)
        
        self.server_status_labels = {}
        for server_id, server_info in self.servers.items():
            label = tk.Label(remote_frame, text=f"🖥️ {server_info['name']}: Probing...", 
                           bg='#1a1a2e', fg='#fa0', font=("Arial", 9))
            label.pack(anchor='w', padx=10, pady=2)
            self.server_status_labels[server_id] = label
        
        # Quick actions with safe styling
        actions_frame = tk.LabelFrame(main_frame, text="QUICK LAUNCH", 
                                    font=("Arial", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        # Safe button styling
        button_style = {
            'font': ('Arial', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'activeforeground': '#00ff00',
            'relief': 'raised',
            'bd': 2,
            'padx': 15,
            'pady': 5
        }
        
        tk.Button(button_frame, text="🧹 SYSTEM SCAN", 
                 command=self.analyze_system, **button_style).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="🔗 CONNECT EBON", 
                 command=lambda: self.connect_to_server('ebon'), **button_style).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(button_frame, text="🔄 CHECK UPDATES", 
                 command=self.check_all_updates, **button_style).grid(row=0, column=2, padx=5, pady=5)
        
        # Update status
        update_frame = tk.LabelFrame(main_frame, text="UPDATE STATUS", 
                                    font=("Arial", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        update_frame.pack(fill='x', padx=10, pady=10)
        
        self.update_summary_label = tk.Label(update_frame, 
                                            text="🔄 Updates: Checking...", 
                                            bg='#1a1a2e', fg='#fa0', font=("Arial", 10))
        self.update_summary_label.pack(anchor='w', padx=10, pady=5)
        
    def create_system_tab(self):
        """Create system management tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="💻 Local System")
        
        main_frame = tk.Frame(system_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # System info
        info_frame = tk.LabelFrame(main_frame, text="SYSTEM INFORMATION", 
                                  font=("Arial", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.system_info_text = tk.Text(info_frame, height=6, wrap='word',
                                       bg='#0a0a1e', fg='#0f8', font=('Arial', 10))
        self.system_info_text.pack(fill='x', padx=5, pady=5)
        
        # Output
        output_frame = tk.LabelFrame(main_frame, text="SYSTEM OUTPUT", 
                                    font=("Arial", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.local_output = scrolledtext.ScrolledText(output_frame, height=15,
                                                     bg='#0a0a1e', fg='#0f8',
                                                     font=('Arial', 10))
        self.local_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_servers_tab(self):
        """Create server management tab"""
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="🌍 Remote Servers")
        
        main_frame = tk.Frame(servers_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Server list
        list_frame = tk.LabelFrame(main_frame, text="SERVER REGISTRY", 
                                  font=("Arial", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        list_frame.pack(fill='x', padx=10, pady=5)
        
        for server_id, server_info in self.servers.items():
            label = tk.Label(list_frame, 
                           text=f"🖥️ {server_info['name']}: {server_info['host']}:{server_info['port']}",
                           bg='#1a1a2e', fg='#0f8', font=('Arial', 10))
            label.pack(anchor='w', padx=10, pady=2)
        
        # Server actions
        actions_frame = tk.LabelFrame(main_frame, text="SERVER ACTIONS", 
                                     font=("Arial", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Arial', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2
        }
        
        tk.Button(button_frame, text="🔗 CONNECT SSH", 
                 command=lambda: self.connect_to_server('ebon'), **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="🌐 WEB INTERFACE", 
                 command=self.open_ebon_web, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📊 SERVER STATS", 
                 command=self.get_ebon_stats, **button_style).pack(side='left', padx=5)
        
        # Terminal
        terminal_frame = tk.LabelFrame(main_frame, text="REMOTE TERMINAL", 
                                      font=("Arial", 10, "bold"),
                                      bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        terminal_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.server_terminal = scrolledtext.ScrolledText(terminal_frame, 
                                                        bg='#0a0a1e', fg='#0f8',
                                                        font=('Arial', 10))
        self.server_terminal.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_update_tab(self):
        """Create update management tab"""
        update_frame = ttk.Frame(self.notebook)
        self.notebook.add(update_frame, text="🔄 Update Center")
        
        main_frame = tk.Frame(update_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Update overview
        overview_frame = tk.LabelFrame(main_frame, text="UPDATE OVERVIEW", 
                                      font=("Arial", 10, "bold"),
                                      bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        overview_frame.pack(fill='x', padx=10, pady=5)
        
        self.local_updates_label = tk.Label(overview_frame, text="📦 Local: Checking...",
                                           bg='#1a1a2e', fg='#0f8', font=('Arial', 10))
        self.local_updates_label.pack(anchor='w', padx=10, pady=2)
        
        self.remote_updates_label = tk.Label(overview_frame, text="🖥️ Remote: Checking...",
                                            bg='#1a1a2e', fg='#fa0', font=('Arial', 10))
        self.remote_updates_label.pack(anchor='w', padx=10, pady=2)
        
        # Update controls
        control_frame = tk.LabelFrame(main_frame, text="UPDATE CONTROL", 
                                     font=("Arial", 10, "bold"),
                                     bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        button_style = {
            'font': ('Arial', 10, 'bold'),
            'bg': '#2a2a3e',
            'fg': '#00d4ff',
            'activebackground': '#3a3a4e',
            'relief': 'raised',
            'bd': 2,
            'padx': 15
        }
        
        tk.Button(button_frame, text="🔍 CHECK UPDATES", 
                 command=self.check_all_updates, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="🔒 SECURITY ONLY", 
                 command=self.install_security_updates, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📦 ALL UPDATES", 
                 command=self.install_all_updates, **button_style).pack(side='left', padx=5)
        
        # Update log
        log_frame = tk.LabelFrame(main_frame, text="UPDATE LOG", 
                                 font=("Arial", 10, "bold"),
                                 bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.update_log = scrolledtext.ScrolledText(log_frame,
                                                   bg='#0a0a1e', fg='#0f8',
                                                   font=('Arial', 10))
        self.update_log.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize log
        self.update_log.insert(tk.END, "[NEXUS UPDATE CENTER] Initialized\\n")
        self.update_log.insert(tk.END, "[INFO] Ready for update management\\n\\n")
        
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        main_frame = tk.Frame(settings_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Settings info
        info_frame = tk.LabelFrame(main_frame, text="NEXUS CONFIGURATION", 
                                  font=("Arial", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        info_text = tk.Text(info_frame, height=10, wrap='word',
                           bg='#0a0a1e', fg='#0f8', font=('Arial', 10))
        info_text.pack(fill='x', padx=10, pady=10)
        
        info_text.insert(tk.END, "NexusController Settings\\n")
        info_text.insert(tk.END, "=" * 30 + "\\n\\n")
        info_text.insert(tk.END, f"Version: 1.0\\n")
        info_text.insert(tk.END, f"Config Path: ~/.config/nexus-controller/\\n")
        info_text.insert(tk.END, f"Servers: {len(self.servers)}\\n")
        info_text.insert(tk.END, f"SSH Connections: {len(self.ssh_connections)}\\n")
        
    # Core functionality methods
    def delayed_initialization(self):
        """Initialize background tasks after UI is ready"""
        try:
            print("Starting delayed initialization...")
            self.check_initial_status()
            self.start_update_scheduler()
            print("Delayed initialization complete!")
        except Exception as e:
            print(f"Error in delayed initialization: {e}")
            
    def check_initial_status(self):
        """Check initial system status"""
        self.update_status_label("Checking system status...")
        threading.Thread(target=self._check_status_thread, daemon=True).start()
        
    def _check_status_thread(self):
        """Background status check"""
        try:
            # Check local system
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.safe_ui_update(self.local_cpu_label.config, text=f"⚡ CPU: {cpu}%")
            self.safe_ui_update(self.local_mem_label.config, text=f"💾 Memory: {mem}%")
            self.safe_ui_update(self.local_disk_label.config, text=f"💿 Disk: {disk}%")
            
            # Update system info
            info = f"Node ID: {socket.gethostname()}\\n"
            info += f"Platform: {sys.platform}\\n"
            info += f"CPU Cores: {psutil.cpu_count()}\\n"
            info += f"Total Memory: {psutil.virtual_memory().total // (1024**3)} GB"
            
            self.safe_ui_update(self.system_info_text.delete, 1.0, tk.END)
            self.safe_ui_update(self.system_info_text.insert, 1.0, info)
            
        except Exception as e:
            self.update_status_label(f"System check error: {e}")
            
        # Check servers
        self.check_server_status('ebon')
        
    def check_server_status(self, server_id):
        """Check server connectivity"""
        try:
            server_info = self.servers[server_id]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_info['host'], server_info['port']))
            sock.close()
            
            if result == 0:
                self.safe_ui_update(self.server_status_labels[server_id].config,
                                   text=f"🖥️ {server_info['name']}: ONLINE",
                                   fg='#0f8')
            else:
                self.safe_ui_update(self.server_status_labels[server_id].config,
                                   text=f"🖥️ {server_info['name']}: OFFLINE",
                                   fg='#f00')
                
        except Exception as e:
            print(f"Server check error: {e}")
    
    def start_update_scheduler(self):
        """Start update checking"""
        if not self.update_scheduler_running:
            self.update_scheduler_running = True
            self.log_update("[NEXUS] Update scheduler started")
            # Check for updates after 5 seconds
            self.root.after(5000, self.check_all_updates)
    
    def safe_ui_update(self, update_func, *args, **kwargs):
        """Thread-safe UI updates"""
        try:
            if not self.shutdown_flag:
                self.root.after_idle(update_func, *args, **kwargs)
        except Exception as e:
            print(f"UI update error: {e}")
    
    def update_status_label(self, message):
        """Update status bar"""
        self.safe_ui_update(self.status_label.config, text=f"NEXUS: {message}")
    
    def log_update(self, message):
        """Log update message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\\n"
        
        try:
            self.update_log.insert(tk.END, full_message)
            self.update_log.see(tk.END)
        except:
            pass
    
    # Simplified functionality
    def analyze_system(self):
        """System analysis"""
        self.local_output.delete(1.0, tk.END)
        self.local_output.insert(tk.END, "[NEXUS] System analysis started...\\n")
        threading.Thread(target=self._analyze_thread, daemon=True).start()
    
    def _analyze_thread(self):
        """Background analysis"""
        try:
            self.local_output.insert(tk.END, f"Hostname: {socket.gethostname()}\\n")
            self.local_output.insert(tk.END, f"CPU Usage: {psutil.cpu_percent()}%\\n")
            self.local_output.insert(tk.END, f"Memory Usage: {psutil.virtual_memory().percent}%\\n")
            self.local_output.insert(tk.END, "Analysis complete!\\n")
        except Exception as e:
            self.local_output.insert(tk.END, f"Analysis error: {e}\\n")
    
    def connect_to_server(self, server_id):
        """Connect to server"""
        server_info = self.servers.get(server_id)
        if server_info:
            self.server_terminal.insert(tk.END, f"\\nConnecting to {server_info['name']}...\\n")
            self.server_terminal.insert(tk.END, f"SSH: {server_info['username']}@{server_info['host']}\\n")
    
    def open_ebon_web(self):
        """Open ebon web interface"""
        import webbrowser
        webbrowser.open("http://10.0.0.29")
    
    def get_ebon_stats(self):
        """Get ebon server stats"""
        self.server_terminal.insert(tk.END, "\\nEbon server statistics:\\n")
        self.server_terminal.insert(tk.END, "Host: 10.0.0.29\\n")
        self.server_terminal.insert(tk.END, "Status: Checking...\\n")
    
    def check_all_updates(self):
        """Check for updates"""
        self.log_update("[NEXUS] Checking for updates...")
        self.update_status_label("Checking updates...")
        threading.Thread(target=self._check_updates_thread, daemon=True).start()
    
    def _check_updates_thread(self):
        """Background update check"""
        try:
            # Simple update check
            result = subprocess.run("apt list --upgradable", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\\n')
                updates = len([line for line in lines if '/' in line and 'upgradable' in line])
                
                self.safe_ui_update(self.local_updates_label.config, 
                                   text=f"📦 Local: {updates} updates available")
                self.safe_ui_update(self.update_summary_label.config,
                                   text=f"🔄 Updates: {updates} available")
                
                self.log_update(f"[LOCAL] Found {updates} updates")
            else:
                self.log_update("[ERROR] Update check failed")
                
        except Exception as e:
            self.log_update(f"[ERROR] Update check error: {e}")
    
    def install_security_updates(self):
        """Install security updates"""
        self.log_update("[NEXUS] Security update installation not implemented")
    
    def install_all_updates(self):
        """Install all updates"""
        self.log_update("[NEXUS] Full update installation not implemented")
    
    def on_closing(self):
        """Handle shutdown"""
        print("Shutting down NexusController...")
        self.shutdown_flag = True
        self.update_scheduler_running = False
        
        for ssh in self.ssh_connections.values():
            try:
                ssh.close()
            except:
                pass
                
        self.root.destroy()
    
    def run(self):
        """Start NexusController"""
        try:
            print("Starting NexusController main loop...")
            self.root.mainloop()
            print("NexusController ended.")
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Starting NexusController (Fixed Version)...")
    
    try:
        # Check dependencies
        import paramiko
    except ImportError:
        print("Installing paramiko...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"])
        
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
        
    # Start application
    app = NexusController()
    app.run()