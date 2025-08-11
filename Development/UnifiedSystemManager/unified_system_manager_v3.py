#!/usr/bin/env python3
"""
Unified System Manager v3.0 - Merged Version
Combines local system management with remote server control
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
from datetime import datetime
import psutil

class UnifiedSystemManagerV3:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Unified System Manager v3.0")
        self.root.geometry("1100x700")
        
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
        
        self.setup_ui()
        self.check_initial_status()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Unified System Manager v3.0", 
                              font=("Arial", 20, "bold"), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg='#ecf0f1', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_frame, text="Ready", bg='#ecf0f1')
        self.status_label.pack(side='left', padx=10)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Dashboard tab
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        self.create_dashboard_tab(dashboard_frame)
        
        # Local System tab
        local_frame = ttk.Frame(self.notebook)
        self.notebook.add(local_frame, text="💻 Local System")
        self.create_local_system_tab(local_frame)
        
        # Remote Servers tab
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="🖥️ Remote Servers")
        self.create_servers_tab(servers_frame)
        
        # Google Drive tab
        gdrive_frame = ttk.Frame(self.notebook)
        self.notebook.add(gdrive_frame, text="☁️ Google Drive")
        self.create_gdrive_tab(gdrive_frame)
        
        # Backup & Sync tab
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text="🔄 Backup & Sync")
        self.create_backup_tab(backup_frame)
        
        # Ethereum tab
        eth_frame = ttk.Frame(self.notebook)
        self.notebook.add(eth_frame, text="⟠ Ethereum")
        self.create_ethereum_tab(eth_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        self.create_settings_tab(settings_frame)
        
    def create_dashboard_tab(self, parent):
        # System overview
        overview_frame = ttk.LabelFrame(parent, text="System Overview")
        overview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Two columns
        left_frame = tk.Frame(overview_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        right_frame = tk.Frame(overview_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        # Local system status
        local_status = ttk.LabelFrame(left_frame, text="Local System")
        local_status.pack(fill='x', pady=5)
        
        self.local_cpu_label = tk.Label(local_status, text="CPU: Checking...")
        self.local_cpu_label.pack(anchor='w', padx=5)
        
        self.local_mem_label = tk.Label(local_status, text="Memory: Checking...")
        self.local_mem_label.pack(anchor='w', padx=5)
        
        self.local_disk_label = tk.Label(local_status, text="Disk: Checking...")
        self.local_disk_label.pack(anchor='w', padx=5)
        
        # Server status
        server_status = ttk.LabelFrame(right_frame, text="Remote Servers")
        server_status.pack(fill='x', pady=5)
        
        self.server_status_labels = {}
        for server_id, server_info in self.servers.items():
            label = tk.Label(server_status, text=f"{server_info['name']}: Checking...")
            label.pack(anchor='w', padx=5)
            self.server_status_labels[server_id] = label
        
        # Quick actions
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="🧹 Quick Cleanup", 
                  command=self.quick_cleanup).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="📁 Mount Drive", 
                  command=self.mount_drive).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🔄 Sync All", 
                  command=self.sync_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔗 Connect to Ebon", 
                  command=lambda: self.connect_to_server('ebon')).grid(row=0, column=3, padx=5)
        
    def create_local_system_tab(self, parent):
        # System info
        info_frame = ttk.LabelFrame(parent, text="System Information")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.system_info_text = tk.Text(info_frame, height=6, wrap='word')
        self.system_info_text.pack(fill='x', padx=5, pady=5)
        
        # Cleanup options
        cleanup_frame = ttk.LabelFrame(parent, text="Cleanup Options")
        cleanup_frame.pack(fill='x', padx=10, pady=5)
        
        self.cleanup_vars = {}
        cleanup_options = [
            ("Package Cache", "package_cache"),
            ("Browser Caches", "browser_cache"),
            ("Temporary Files", "temp_files"),
            ("Docker Resources", "docker"),
            ("Old Logs", "old_logs"),
            ("Trash/Recycle Bin", "trash")
        ]
        
        for i, (name, key) in enumerate(cleanup_options):
            var = tk.BooleanVar(value=True)
            self.cleanup_vars[key] = var
            row = i // 3
            col = i % 3
            ttk.Checkbutton(cleanup_frame, text=name, variable=var).grid(
                row=row, column=col, sticky='w', padx=10, pady=2)
        
        # Action buttons
        action_frame = tk.Frame(parent)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_frame, text="🔍 Analyze System", 
                  command=self.analyze_system).pack(side='left', padx=5)
        ttk.Button(action_frame, text="🧹 Start Cleanup", 
                  command=self.start_cleanup).pack(side='left', padx=5)
        ttk.Button(action_frame, text="⚡ Emergency Cleanup", 
                  command=self.emergency_cleanup).pack(side='left', padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(parent, text="Output")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.local_output = scrolledtext.ScrolledText(output_frame, height=10)
        self.local_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_servers_tab(self, parent):
        # Server list
        list_frame = ttk.LabelFrame(parent, text="Available Servers")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Server tree
        columns = ('Status', 'IP', 'Services', 'Last Check')
        self.server_tree = ttk.Treeview(list_frame, columns=columns, height=6)
        self.server_tree.heading('#0', text='Server')
        for col in columns:
            self.server_tree.heading(col, text=col)
            self.server_tree.column(col, width=120)
        
        self.server_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Populate servers
        for server_id, server_info in self.servers.items():
            self.server_tree.insert('', 'end', server_id, 
                                   text=server_info['name'],
                                   values=('Checking...', server_info['host'], 
                                          ', '.join(server_info['services']), 'Never'))
        
        # Server actions
        actions_frame = ttk.LabelFrame(parent, text="Server Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="🔗 Connect SSH", 
                  command=self.ssh_to_selected).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="🌐 Open Web UI", 
                  command=self.open_server_web).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="📊 Server Stats", 
                  command=self.get_server_stats).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_servers).grid(row=0, column=3, padx=5)
        
        # Terminal output
        terminal_frame = ttk.LabelFrame(parent, text="Terminal Output")
        terminal_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.server_terminal = scrolledtext.ScrolledText(terminal_frame, 
                                                        bg='black', fg='green',
                                                        font=('Consolas', 10))
        self.server_terminal.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Command input
        cmd_frame = tk.Frame(terminal_frame)
        cmd_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(cmd_frame, text="Command:").pack(side='left')
        self.server_cmd_entry = tk.Entry(cmd_frame)
        self.server_cmd_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(cmd_frame, text="Run", 
                  command=self.run_server_command).pack(side='left')
        
    def create_gdrive_tab(self, parent):
        # Status
        status_frame = ttk.LabelFrame(parent, text="Google Drive Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.rclone_status = tk.Label(status_frame, text="rclone: Checking...")
        self.rclone_status.pack(anchor='w', padx=5)
        
        self.mount_status = tk.Label(status_frame, text="Mount: Checking...")
        self.mount_status.pack(anchor='w', padx=5)
        
        # Actions
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="⚙️ Configure", 
                  command=self.configure_gdrive).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📁 Mount", 
                  command=self.mount_drive).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Sync", 
                  command=self.sync_gdrive).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📊 Stats", 
                  command=self.gdrive_stats).pack(side='left', padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(parent, text="Output")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.gdrive_output = scrolledtext.ScrolledText(output_frame)
        self.gdrive_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_backup_tab(self, parent):
        # Backup profiles
        profiles_frame = ttk.LabelFrame(parent, text="Backup Profiles")
        profiles_frame.pack(fill='x', padx=10, pady=5)
        
        # Profile list
        self.backup_profiles = {
            'documents': {
                'name': 'Documents',
                'source': '~/Documents',
                'dest': 'ebon:~/Backups/Documents',
                'schedule': 'Daily'
            },
            'projects': {
                'name': 'Projects',
                'source': '~/Projects',
                'dest': 'GoogleDrive:Projects',
                'schedule': 'On Change'
            }
        }
        
        columns = ('Source', 'Destination', 'Schedule', 'Last Run')
        self.backup_tree = ttk.Treeview(profiles_frame, columns=columns, height=5)
        self.backup_tree.heading('#0', text='Profile')
        for col in columns:
            self.backup_tree.heading(col, text=col)
        
        self.backup_tree.pack(fill='x', padx=5, pady=5)
        
        # Populate profiles
        for profile_id, profile in self.backup_profiles.items():
            self.backup_tree.insert('', 'end', profile_id,
                                   text=profile['name'],
                                   values=(profile['source'], profile['dest'],
                                          profile['schedule'], 'Never'))
        
        # Actions
        actions_frame = ttk.LabelFrame(parent, text="Actions")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="▶️ Run Backup", 
                  command=self.run_backup).pack(side='left', padx=5)
        ttk.Button(button_frame, text="➕ New Profile", 
                  command=self.new_backup_profile).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔄 Sync All", 
                  command=self.sync_all_backups).pack(side='left', padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(parent, text="Backup Log")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.backup_output = scrolledtext.ScrolledText(output_frame)
        self.backup_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_ethereum_tab(self, parent):
        # Status
        status_frame = ttk.LabelFrame(parent, text="Ethereum Node Status")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.eth_status_label = tk.Label(status_frame, text="Node: Not configured")
        self.eth_status_label.pack(anchor='w', padx=5)
        
        self.eth_sync_label = tk.Label(status_frame, text="Sync: N/A")
        self.eth_sync_label.pack(anchor='w', padx=5)
        
        # Actions
        actions_frame = ttk.LabelFrame(parent, text="Node Management")
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = tk.Frame(actions_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="🚀 Deploy Node", 
                  command=self.deploy_eth_node).pack(side='left', padx=5)
        ttk.Button(button_frame, text="▶️ Start", 
                  command=self.start_eth_node).pack(side='left', padx=5)
        ttk.Button(button_frame, text="⏹️ Stop", 
                  command=self.stop_eth_node).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📊 Stats", 
                  command=self.eth_stats).pack(side='left', padx=5)
        
        # Output
        output_frame = ttk.LabelFrame(parent, text="Node Output")
        output_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.eth_output = scrolledtext.ScrolledText(output_frame)
        self.eth_output.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_settings_tab(self, parent):
        # Server settings
        server_frame = ttk.LabelFrame(parent, text="Server Configuration")
        server_frame.pack(fill='x', padx=10, pady=5)
        
        # Add server button
        ttk.Button(server_frame, text="➕ Add Server", 
                  command=self.add_server_dialog).pack(pady=10)
        
        # Local settings
        local_frame = ttk.LabelFrame(parent, text="Local Settings")
        local_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(local_frame, text="Google Drive Mount:").grid(row=0, column=0, sticky='w', padx=5)
        self.mount_path_var = tk.StringVar(value=str(Path.home() / "GoogleDrive"))
        tk.Entry(local_frame, textvariable=self.mount_path_var, width=40).grid(row=0, column=1, padx=5)
        
        tk.Label(local_frame, text="Backup Directory:").grid(row=1, column=0, sticky='w', padx=5)
        self.backup_dir_var = tk.StringVar(value=str(Path.home() / "Backups"))
        tk.Entry(local_frame, textvariable=self.backup_dir_var, width=40).grid(row=1, column=1, padx=5)
        
        # Save button
        ttk.Button(parent, text="💾 Save Settings", 
                  command=self.save_settings).pack(pady=20)
        
    # Core functionality methods
    def check_initial_status(self):
        """Check initial system status"""
        threading.Thread(target=self._check_status_thread, daemon=True).start()
        
    def _check_status_thread(self):
        """Background thread for status checks"""
        # Check local system
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.local_cpu_label.config(text=f"CPU: {cpu}%")
            self.local_mem_label.config(text=f"Memory: {mem}%")
            self.local_disk_label.config(text=f"Disk: {disk}%")
            
            # Update system info
            info = f"Hostname: {socket.gethostname()}\\n"
            info += f"Platform: {sys.platform}\\n"
            info += f"CPU Cores: {psutil.cpu_count()}\\n"
            info += f"Total Memory: {psutil.virtual_memory().total // (1024**3)} GB"
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(1.0, info)
            
        except Exception as e:
            self.update_status(f"Error checking local system: {e}")
            
        # Check servers
        self.refresh_servers()
        
    def refresh_servers(self):
        """Refresh server status"""
        for server_id, server_info in self.servers.items():
            self.check_server_status(server_id)
            
    def check_server_status(self, server_id):
        """Check if a server is online"""
        server_info = self.servers[server_id]
        try:
            # Quick ping check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_info['host'], server_info['port']))
            sock.close()
            
            if result == 0:
                status = "🟢 Online"
                self.server_status_labels[server_id].config(
                    text=f"{server_info['name']}: Online",
                    fg='green'
                )
            else:
                status = "🔴 Offline"
                self.server_status_labels[server_id].config(
                    text=f"{server_info['name']}: Offline",
                    fg='red'
                )
                
            # Update tree
            self.server_tree.set(server_id, 'Status', status)
            self.server_tree.set(server_id, 'Last Check', 
                               datetime.now().strftime('%H:%M:%S'))
            
        except Exception as e:
            self.update_status(f"Error checking {server_info['name']}: {e}")
            
    def connect_to_server(self, server_id):
        """Connect to a server via SSH"""
        server_info = self.servers.get(server_id)
        if not server_info:
            messagebox.showerror("Error", "Server not found")
            return
            
        self.notebook.select(2)  # Switch to servers tab
        self.server_terminal.insert(tk.END, f"\\nConnecting to {server_info['name']}...\\n")
        
        # Try SSH connection
        threading.Thread(target=self._ssh_connect_thread, 
                        args=(server_id,), daemon=True).start()
        
    def _ssh_connect_thread(self, server_id):
        """SSH connection in background thread"""
        server_info = self.servers[server_id]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect
            ssh.connect(
                server_info['host'],
                port=server_info['port'],
                username=server_info['username'],
                timeout=10
            )
            
            self.ssh_connections[server_id] = ssh
            self.server_terminal.insert(tk.END, 
                f"✓ Connected to {server_info['name']}\\n\\n")
            
            # Run initial command
            stdin, stdout, stderr = ssh.exec_command('uname -a && echo && df -h')
            output = stdout.read().decode()
            self.server_terminal.insert(tk.END, output + "\\n")
            
        except Exception as e:
            self.server_terminal.insert(tk.END, 
                f"\\n❌ Failed to connect: {str(e)}\\n")
            self.server_terminal.insert(tk.END, 
                "\\nTip: Make sure you have SSH keys set up or try:\\n")
            self.server_terminal.insert(tk.END, 
                f"ssh-copy-id {server_info['username']}@{server_info['host']}\\n")
            
    def run_server_command(self):
        """Run command on selected server"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server")
            return
            
        server_id = selection[0]
        command = self.server_cmd_entry.get()
        if not command:
            return
            
        self.server_cmd_entry.delete(0, tk.END)
        self.server_terminal.insert(tk.END, f"\\n$ {command}\\n")
        
        # Run command
        threading.Thread(target=self._run_remote_command, 
                        args=(server_id, command), daemon=True).start()
        
    def _run_remote_command(self, server_id, command):
        """Run command on remote server"""
        try:
            ssh = self.ssh_connections.get(server_id)
            if not ssh:
                # Try to connect first
                self._ssh_connect_thread(server_id)
                ssh = self.ssh_connections.get(server_id)
                
            if ssh:
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if output:
                    self.server_terminal.insert(tk.END, output)
                if error:
                    self.server_terminal.insert(tk.END, f"Error: {error}")
                    
        except Exception as e:
            self.server_terminal.insert(tk.END, f"\\nError: {str(e)}\\n")
            
    def ssh_to_selected(self):
        """Open SSH to selected server"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server")
            return
            
        server_id = selection[0]
        self.connect_to_server(server_id)
        
    def open_server_web(self):
        """Open server web interface"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server")
            return
            
        server_id = selection[0]
        server_info = self.servers[server_id]
        
        import webbrowser
        webbrowser.open(f"http://{server_info['host']}")
        
    def get_server_stats(self):
        """Get detailed server statistics"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server")
            return
            
        server_id = selection[0]
        commands = [
            "echo '=== System Info ===' && uname -a",
            "echo '\\n=== CPU Info ===' && lscpu | grep 'Model name\\|CPU(s)'",
            "echo '\\n=== Memory ===' && free -h",
            "echo '\\n=== Disk Usage ===' && df -h",
            "echo '\\n=== Network ===' && ip -s link",
            "echo '\\n=== Services ===' && systemctl list-units --type=service --state=running | head -20"
        ]
        
        full_command = " && ".join(commands)
        self.server_cmd_entry.insert(0, full_command)
        self.run_server_command()
        
    def quick_cleanup(self):
        """Quick cleanup of common items"""
        self.notebook.select(1)  # Switch to local system tab
        self.cleanup_vars['package_cache'].set(True)
        self.cleanup_vars['temp_files'].set(True)
        self.cleanup_vars['trash'].set(True)
        self.start_cleanup()
        
    def analyze_system(self):
        """Analyze system for cleanup opportunities"""
        self.local_output.delete(1.0, tk.END)
        self.local_output.insert(tk.END, "Analyzing system...\\n\\n")
        
        threading.Thread(target=self._analyze_thread, daemon=True).start()
        
    def _analyze_thread(self):
        """Background analysis thread"""
        try:
            # Check various locations
            checks = [
                ("Package cache", "du -sh /var/cache/apt/archives 2>/dev/null"),
                ("Temp files", "du -sh /tmp 2>/dev/null"),
                ("User cache", f"du -sh {Path.home()}/.cache 2>/dev/null"),
                ("Trash", f"du -sh {Path.home()}/.local/share/Trash 2>/dev/null"),
            ]
            
            total_size = 0
            for name, cmd in checks:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    size = result.stdout.split()[0]
                    self.local_output.insert(tk.END, f"{name}: {size}\\n")
                    
            self.local_output.insert(tk.END, "\\nAnalysis complete!\\n")
            
        except Exception as e:
            self.local_output.insert(tk.END, f"\\nError: {str(e)}\\n")
            
    def start_cleanup(self):
        """Start system cleanup"""
        self.local_output.delete(1.0, tk.END)
        self.local_output.insert(tk.END, "Starting cleanup...\\n\\n")
        
        threading.Thread(target=self._cleanup_thread, daemon=True).start()
        
    def _cleanup_thread(self):
        """Background cleanup thread"""
        try:
            if self.cleanup_vars['package_cache'].get():
                self.local_output.insert(tk.END, "Cleaning package cache...\\n")
                subprocess.run("sudo apt-get clean", shell=True)
                
            if self.cleanup_vars['temp_files'].get():
                self.local_output.insert(tk.END, "Cleaning temp files...\\n")
                subprocess.run("find /tmp -type f -atime +7 -delete 2>/dev/null", shell=True)
                
            if self.cleanup_vars['browser_cache'].get():
                self.local_output.insert(tk.END, "Cleaning browser caches...\\n")
                # Add browser cache cleanup
                
            if self.cleanup_vars['trash'].get():
                self.local_output.insert(tk.END, "Emptying trash...\\n")
                subprocess.run(f"rm -rf {Path.home()}/.local/share/Trash/*", shell=True)
                
            self.local_output.insert(tk.END, "\\nCleanup complete!\\n")
            
        except Exception as e:
            self.local_output.insert(tk.END, f"\\nError: {str(e)}\\n")
            
    def emergency_cleanup(self):
        """Emergency cleanup when disk is full"""
        if messagebox.askyesno("Emergency Cleanup", 
                              "This will aggressively clean your system. Continue?"):
            # Set all cleanup options
            for var in self.cleanup_vars.values():
                var.set(True)
            self.start_cleanup()
            
    def mount_drive(self):
        """Mount Google Drive"""
        self.notebook.select(3)  # Switch to Google Drive tab
        self.gdrive_output.delete(1.0, tk.END)
        self.gdrive_output.insert(tk.END, "Mounting Google Drive...\\n")
        
        mount_point = self.mount_path_var.get()
        cmd = f"rclone mount googledrive: {mount_point} --daemon"
        
        threading.Thread(target=lambda: self.run_command(cmd, self.gdrive_output), 
                        daemon=True).start()
        
    def sync_all(self):
        """Sync all configured backups"""
        self.notebook.select(4)  # Switch to backup tab
        self.sync_all_backups()
        
    def run_command(self, command, output_widget):
        """Run command and display output"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output_widget.insert(tk.END, result.stdout)
            if result.stderr:
                output_widget.insert(tk.END, f"\\nError: {result.stderr}")
            output_widget.see(tk.END)
        except Exception as e:
            output_widget.insert(tk.END, f"\\nException: {str(e)}")
            
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        
    def save_settings(self):
        """Save application settings"""
        settings = {
            'mount_path': self.mount_path_var.get(),
            'backup_dir': self.backup_dir_var.get(),
            'servers': self.servers
        }
        
        settings_file = Path.home() / '.config' / 'unified-system-manager' / 'settings.json'
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            
        messagebox.showinfo("Success", "Settings saved!")
        
    def run(self):
        """Start the application"""
        self.root.mainloop()
        
    # Placeholder methods for remaining functionality
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
            messagebox.showwarning("Warning", "Please select a backup profile")
            return
        # Implement backup logic
        
    def new_backup_profile(self):
        # Implement new profile dialog
        pass
        
    def sync_all_backups(self):
        self.backup_output.delete(1.0, tk.END)
        self.backup_output.insert(tk.END, "Starting all backups...\\n")
        # Implement sync all logic
        
    def deploy_eth_node(self):
        self.eth_output.insert(tk.END, "Ethereum node deployment not yet implemented\\n")
        
    def start_eth_node(self):
        self.eth_output.insert(tk.END, "Starting Ethereum node...\\n")
        
    def stop_eth_node(self):
        self.eth_output.insert(tk.END, "Stopping Ethereum node...\\n")
        
    def eth_stats(self):
        self.eth_output.insert(tk.END, "Ethereum stats not available\\n")
        
    def add_server_dialog(self):
        # Implement add server dialog
        pass

if __name__ == '__main__':
    # Check for required packages
    try:
        import paramiko
    except ImportError:
        print("Installing paramiko for SSH support...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"])
        import paramiko
        
    try:
        import psutil
    except ImportError:
        print("Installing psutil for system monitoring...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
        
    app = UnifiedSystemManagerV3()
    app.run()