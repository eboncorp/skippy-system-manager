#!/usr/bin/env python3
"""
NexusController - Working Version
Based exactly on the successful nexus_delayed_tabs.py test
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import socket
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class NexusWorking:
    def __init__(self):
        print("Starting NexusController working version...")
        
        self.root = tk.Tk()
        self.root.title("NexusController - System & Server Management")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.shutdown_flag = False
        
        # Server config
        self.servers = {
            'ebon': {
                'host': '10.0.0.29',
                'port': 22,
                'username': 'ebon',
                'name': 'Ebon Server'
            }
        }
        
        # Create basic UI first
        self.create_basic_ui()
        
        # Schedule delayed tab creation (exact pattern from working test)
        print("Scheduling delayed tab creation...")
        self.root.after(1000, self.create_dashboard_delayed)
        self.root.after(2000, self.create_system_delayed)
        self.root.after(3000, self.create_servers_delayed)
        
        print("Basic UI ready, tabs will be created with delays...")
    
    def create_basic_ui(self):
        """Create basic UI structure (exact copy from working test)"""
        print("Creating basic UI structure...")
        
        # Dark theme header
        header = tk.Frame(self.root, bg='#1a1a2e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🌐 NexusController", 
                       font=("Arial", 18, "bold"), fg='#00d4ff', bg='#1a1a2e')
        title.pack(side='left', padx=20, pady=10)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#0f0f1e', height=30)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="NEXUS: Creating tabs with delays...", 
                                    fg='#00d4ff', bg='#0f0f1e', font=("Arial", 9))
        self.status_label.pack(side='left', padx=10)
        
        # Notebook
        print("Creating empty notebook...")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        print("Basic UI structure created!")
    
    def create_dashboard_delayed(self):
        """Create dashboard tab with delay (exact copy from working test)"""
        try:
            print("Creating dashboard tab (delayed)...")
            self.status_label.config(text="NEXUS: Creating dashboard tab...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="🎯 Dashboard")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            title = tk.Label(content, text="NEXUS COMMAND CENTER", 
                           font=("Arial", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=10)
            
            # System status
            status_frame = tk.Frame(content, bg='#1a1a2e', relief='ridge', bd=2)
            status_frame.pack(fill='x', pady=10)
            
            section_title = tk.Label(status_frame, text="SYSTEM STATUS", 
                                    font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            section_title.pack(pady=5)
            
            self.cpu_label = tk.Label(status_frame, text="⚡ CPU: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Arial", 10))
            self.cpu_label.pack(anchor='w', padx=10, pady=2)
            
            self.mem_label = tk.Label(status_frame, text="💾 Memory: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Arial", 10))
            self.mem_label.pack(anchor='w', padx=10, pady=2)
            
            self.server_label = tk.Label(status_frame, text="🖥️ Ebon: Checking...", 
                                        bg='#1a1a2e', fg='#fa0', font=("Arial", 10))
            self.server_label.pack(anchor='w', padx=10, pady=2)
            
            # Quick actions
            actions_frame = tk.Frame(content, bg='#1a1a2e', relief='groove', bd=2)
            actions_frame.pack(fill='x', pady=10)
            
            action_title = tk.Label(actions_frame, text="QUICK ACTIONS", 
                                   font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            action_title.pack(pady=10)
            
            button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
            button_frame.pack(pady=10)
            
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
            
            tk.Button(button_frame, text="🔍 SYSTEM SCAN", 
                     command=self.check_status, **button_style).pack(side='left', padx=5)
            tk.Button(button_frame, text="🔗 CONNECT EBON", 
                     command=self.connect_ebon, **button_style).pack(side='left', padx=5)
            
            print("✓ Dashboard tab created successfully!")
            self.status_label.config(text="NEXUS: Dashboard ready, creating system tab next...")
            
        except Exception as e:
            print(f"✗ Dashboard creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_system_delayed(self):
        """Create system tab with delay (exact copy from working test)"""
        try:
            print("Creating system tab (delayed)...")
            self.status_label.config(text="NEXUS: Creating system tab...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="💻 System")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            title = tk.Label(content, text="SYSTEM MANAGEMENT", 
                           font=("Arial", 14, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=10)
            
            # The critical ScrolledText that was crashing
            print("Creating ScrolledText with exact crash configuration...")
            self.system_text = scrolledtext.ScrolledText(content, height=15, width=80,
                                                        bg='#0a0a1e', fg='#0f8',
                                                        font=('Arial', 10))
            self.system_text.pack(fill='both', expand=True, pady=10)
            
            self.system_text.insert('1.0', f"Hostname: {socket.gethostname()}\n")
            self.system_text.insert('end', f"Platform: {sys.platform}\n")
            self.system_text.insert('end', "System tab created with delay - no crash!\n")
            
            print("✓ System tab created successfully!")
            self.status_label.config(text="NEXUS: System tab ready, creating servers tab next...")
            
        except Exception as e:
            print(f"✗ System tab creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_servers_delayed(self):
        """Create servers tab with delay (exact copy from working test)"""
        try:
            print("Creating servers tab (delayed)...")
            self.status_label.config(text="NEXUS: Creating servers tab...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="🌍 Servers")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            title = tk.Label(content, text="SERVER MANAGEMENT", 
                           font=("Arial", 14, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=10)
            
            # Server info
            for server_id, server_info in self.servers.items():
                info = tk.Label(content, 
                               text=f"{server_info['name']}: {server_info['host']}",
                               font=("Arial", 10), bg='#0f0f1e', fg='#0f8')
                info.pack(anchor='w', padx=10, pady=2)
            
            # Server output
            self.server_output = scrolledtext.ScrolledText(content, height=15, width=80,
                                                          bg='#0a0a1e', fg='#0f8',
                                                          font=('Arial', 10))
            self.server_output.pack(fill='both', expand=True, pady=10)
            
            self.server_output.insert('1.0', "NexusController Server Management\n")
            self.server_output.insert('end', "All tabs created successfully with delays!\n")
            
            print("✓ Servers tab created successfully!")
            self.status_label.config(text="NEXUS: All tabs ready - starting status check...")
            
            # Now that everything is ready, start monitoring
            self.root.after(1000, self.check_status)
            
        except Exception as e:
            print(f"✗ Servers tab creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def check_status(self):
        """Check system status"""
        try:
            print("Checking status...")
            self.status_label.config(text="NEXUS: Checking system status...")
            
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                self.cpu_label.config(text=f"⚡ CPU: {cpu}%")
                self.mem_label.config(text=f"💾 Memory: {mem}%")
            
            # Server check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('10.0.0.29', 22))
            sock.close()
            
            if result == 0:
                self.server_label.config(text="🖥️ Ebon: ONLINE", fg='#0f8')
            else:
                self.server_label.config(text="🖥️ Ebon: OFFLINE", fg='#f00')
            
            self.status_label.config(text="NEXUS: Status check complete - all systems operational!")
            print("✓ Status check completed successfully!")
            
        except Exception as e:
            print(f"Status check error: {e}")
    
    def connect_ebon(self):
        """Connect to ebon"""
        self.server_output.insert('end', f"\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to Ebon...\n")
        self.server_output.see('end')
        
        try:
            import subprocess
            subprocess.Popen(['gnome-terminal', '--', 'ssh', 'ebon@10.0.0.29'])
            self.server_output.insert('end', "✓ Terminal launched\n")
        except:
            self.server_output.insert('end', "Manual connection: ssh ebon@10.0.0.29\n")
        self.server_output.see('end')
    
    def on_closing(self):
        """Handle shutdown"""
        print("Shutting down working version...")
        self.shutdown_flag = True
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            print("Starting working version main loop...")
            self.root.mainloop()
            print("Working version ended.")
            
        except Exception as e:
            print(f"Error in working version: {e}")

if __name__ == '__main__':
    print("Testing NexusController working version...")
    print("Based on successful delayed tabs pattern")
    
    try:
        app = NexusWorking()
        app.run()
    except Exception as e:
        print(f"Fatal error in working version: {e}")
        import traceback
        traceback.print_exc()
    
    print("Working version test complete.")