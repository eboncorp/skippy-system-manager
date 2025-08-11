#!/usr/bin/env python3
"""
NexusController - Progressive Version
Adding features step by step to identify segfault cause
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import json
import socket
import threading
import time
from datetime import datetime, timedelta

# Import only what we need to test
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✓ psutil imported")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("✗ psutil not available")

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
    print("✓ paramiko imported")
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("✗ paramiko not available")

class NexusControllerProgressive:
    def __init__(self):
        print("Starting progressive NexusController...")
        
        try:
            # Step 1: Basic window
            print("Step 1: Creating window...")
            self.root = tk.Tk()
            self.root.title("NexusController - Progressive Test")
            self.root.geometry("1000x700")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Step 2: Initialize variables
            print("Step 2: Initializing variables...")
            self.shutdown_flag = False
            self.servers = {
                'ebon': {
                    'host': '10.0.0.29',
                    'port': 22,
                    'username': 'ebon',
                    'name': 'Ebon Server',
                    'services': ['SSH', 'HTTP']
                }
            }
            self.ssh_connections = {}
            
            # Step 3: Create UI
            print("Step 3: Creating UI...")
            self.create_ui()
            
            # Step 4: Delay system monitoring to avoid segfault
            print("Step 4: Scheduling delayed system monitoring...")
            if PSUTIL_AVAILABLE:
                # Use after() to delay system monitoring until UI is fully ready
                self.root.after(2000, self.test_system_monitoring)
            
            print("Progressive initialization complete!")
            
        except Exception as e:
            print(f"Error in progressive init: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def create_ui(self):
        """Create UI progressively"""
        try:
            # Header
            print("Creating header...")
            header = tk.Frame(self.root, bg='#1a1a2e', height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            title_label = tk.Label(header, text="🌐 NexusController - Progressive", 
                                  font=("Arial", 20, "bold"), fg='#00d4ff', bg='#1a1a2e')
            title_label.pack(expand=True)
            
            # Status bar
            print("Creating status bar...")
            status_frame = tk.Frame(self.root, bg='#0f0f1e', height=30)
            status_frame.pack(fill='x', side='bottom')
            status_frame.pack_propagate(False)
            
            self.status_label = tk.Label(status_frame, text="NEXUS: Progressive test mode", 
                                        fg='#00d4ff', bg='#0f0f1e')
            self.status_label.pack(side='left', padx=10)
            
            # Notebook
            print("Creating notebook...")
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Dashboard tab
            print("Creating dashboard...")
            self.create_dashboard_tab()
            
            # System tab  
            print("Creating system tab...")
            self.create_system_tab()
            
            # Test servers tab
            print("Creating servers tab...")
            self.create_servers_tab()
            
            print("UI creation complete!")
            
        except Exception as e:
            print(f"Error creating UI: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_dashboard_tab(self):
        """Create dashboard with system monitoring"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="🎯 Dashboard")
        
        main_frame = tk.Frame(dashboard_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # System overview
        overview_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='ridge', bd=2)
        overview_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(overview_frame, text="SYSTEM STATUS", 
                font=("Courier", 14, "bold"), fg='#00d4ff', bg='#1a1a2e').pack(pady=10)
        
        # System info labels
        self.cpu_label = tk.Label(overview_frame, text="⚡ CPU: Checking...", 
                                 bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.cpu_label.pack(anchor='w', padx=10, pady=2)
        
        self.mem_label = tk.Label(overview_frame, text="💾 Memory: Checking...", 
                                 bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.mem_label.pack(anchor='w', padx=10, pady=2)
        
        self.disk_label = tk.Label(overview_frame, text="💿 Disk: Checking...", 
                                  bg='#1a1a2e', fg='#0f8', font=("Courier", 10))
        self.disk_label.pack(anchor='w', padx=10, pady=2)
        
        # Server status
        self.server_label = tk.Label(overview_frame, text="🖥️ Ebon: Checking...", 
                                    bg='#1a1a2e', fg='#fa0', font=("Courier", 10))
        self.server_label.pack(anchor='w', padx=10, pady=2)
        
        # Quick actions
        actions_frame = tk.Frame(main_frame, bg='#1a1a2e', relief='groove', bd=2)
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(actions_frame, text="QUICK ACTIONS", 
                font=("Courier", 12, "bold"), fg='#00d4ff', bg='#1a1a2e').pack(pady=10)
        
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
        
        tk.Button(button_frame, text="🔍 SYSTEM SCAN", 
                 command=self.system_scan, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="🔗 TEST EBON", 
                 command=self.test_ebon, **button_style).pack(side='left', padx=5)
        tk.Button(button_frame, text="📊 UPDATE STATUS", 
                 command=self.update_status, **button_style).pack(side='left', padx=5)
    
    def create_system_tab(self):
        """Create system information tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="💻 System")
        
        main_frame = tk.Frame(system_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # System info text area
        info_frame = tk.LabelFrame(main_frame, text="SYSTEM INFORMATION", 
                                  font=("Courier", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.system_info_text = scrolledtext.ScrolledText(info_frame,
                                                         bg='#0a0a1e', fg='#0f8',
                                                         font=('Courier', 10))
        self.system_info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize with basic info
        self.system_info_text.insert(tk.END, "[NEXUS SYSTEM INFORMATION]\\n")
        self.system_info_text.insert(tk.END, "=" * 40 + "\\n")
        self.system_info_text.insert(tk.END, f"Hostname: {socket.gethostname()}\\n")
        self.system_info_text.insert(tk.END, f"Platform: {sys.platform}\\n")
    
    def create_servers_tab(self):
        """Create servers management tab"""
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="🌍 Servers")
        
        main_frame = tk.Frame(servers_frame, bg='#0f0f1e')
        main_frame.pack(fill='both', expand=True)
        
        # Server info
        info_frame = tk.LabelFrame(main_frame, text="SERVER REGISTRY", 
                                  font=("Courier", 10, "bold"),
                                  bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        for server_id, server_info in self.servers.items():
            server_label = tk.Label(info_frame, 
                                   text=f"🖥️ {server_info['name']}: {server_info['host']}",
                                   bg='#1a1a2e', fg='#0f8', font=('Courier', 10))
            server_label.pack(anchor='w', padx=10, pady=2)
        
        # Server output
        output_frame = tk.LabelFrame(main_frame, text="SERVER OUTPUT", 
                                    font=("Courier", 10, "bold"),
                                    bg='#1a1a2e', fg='#00d4ff', relief='groove', bd=2)
        output_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.server_output = scrolledtext.ScrolledText(output_frame,
                                                      bg='#0a0a1e', fg='#0f8',
                                                      font=('Courier', 10))
        self.server_output.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.server_output.insert(tk.END, "[NEXUS SERVER MANAGEMENT]\\n")
        self.server_output.insert(tk.END, "[INFO] Server management ready\\n")
    
    def test_system_monitoring(self):
        """Test system monitoring - potential segfault source"""
        try:
            print("Testing CPU monitoring...")
            cpu = psutil.cpu_percent(interval=0.1)  # Very short interval to avoid blocking
            print(f"CPU: {cpu}%")
            
            print("Testing memory monitoring...")
            mem = psutil.virtual_memory()
            print(f"Memory: {mem.percent}%")
            
            print("Testing disk monitoring...")
            disk = psutil.disk_usage('/')
            print(f"Disk: {disk.percent}%")
            
            # Update UI
            self.cpu_label.config(text=f"⚡ CPU: {cpu}%")
            self.mem_label.config(text=f"💾 Memory: {mem.percent}%")
            self.disk_label.config(text=f"💿 Disk: {disk.percent}%")
            
            print("System monitoring test passed!")
            
        except Exception as e:
            print(f"System monitoring error: {e}")
            self.cpu_label.config(text="⚡ CPU: Error")
            self.mem_label.config(text="💾 Memory: Error")
            self.disk_label.config(text="💿 Disk: Error")
    
    def system_scan(self):
        """Perform system scan"""
        try:
            self.status_label.config(text="NEXUS: Running system scan...")
            self.system_info_text.insert(tk.END, f"\\n[{datetime.now().strftime('%H:%M:%S')}] System scan initiated...\\n")
            
            if PSUTIL_AVAILABLE:
                # Get detailed system info
                info = f"CPU Count: {psutil.cpu_count()}\\n"
                info += f"Boot Time: {datetime.fromtimestamp(psutil.boot_time())}\\n"
                info += f"Load Average: {psutil.getloadavg()}\\n"
                
                self.system_info_text.insert(tk.END, info)
                self.system_info_text.see(tk.END)
            
            self.status_label.config(text="NEXUS: System scan complete")
            
        except Exception as e:
            print(f"System scan error: {e}")
            self.system_info_text.insert(tk.END, f"[ERROR] {e}\\n")
    
    def test_ebon(self):
        """Test connection to ebon server"""
        try:
            self.status_label.config(text="NEXUS: Testing ebon connection...")
            self.server_output.insert(tk.END, f"\\n[{datetime.now().strftime('%H:%M:%S')}] Testing ebon connection...\\n")
            
            # Simple connectivity test
            server_info = self.servers['ebon']
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_info['host'], server_info['port']))
            sock.close()
            
            if result == 0:
                self.server_label.config(text="🖥️ Ebon: ONLINE", fg='#0f8')
                self.server_output.insert(tk.END, "[✓] Ebon server is reachable\\n")
            else:
                self.server_label.config(text="🖥️ Ebon: OFFLINE", fg='#f00')
                self.server_output.insert(tk.END, "[✗] Ebon server is not reachable\\n")
            
            self.server_output.see(tk.END)
            self.status_label.config(text="NEXUS: Connection test complete")
            
        except Exception as e:
            print(f"Ebon test error: {e}")
            self.server_output.insert(tk.END, f"[ERROR] {e}\\n")
    
    def update_status(self):
        """Update all status information"""
        try:
            self.status_label.config(text="NEXUS: Updating status...")
            
            # Update system monitoring
            if PSUTIL_AVAILABLE:
                self.test_system_monitoring()
            
            # Test server connectivity
            self.test_ebon()
            
            self.status_label.config(text="NEXUS: Status update complete")
            
        except Exception as e:
            print(f"Status update error: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        print("Shutting down progressive test...")
        self.shutdown_flag = True
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            print("Starting progressive main loop...")
            self.root.mainloop()
            print("Progressive test ended.")
            
        except Exception as e:
            print(f"Error in progressive main loop: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Starting NexusController Progressive Test...")
    
    try:
        app = NexusControllerProgressive()
        app.run()
    except Exception as e:
        print(f"Fatal error in progressive test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("Progressive test completed.")