#!/usr/bin/env python3
"""
NexusController - Progressive Version 2
Starting from working minimal and adding features incrementally
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import socket
from datetime import datetime

# Optional imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class NexusProgressiveV2:
    def __init__(self):
        print("Starting NexusController Progressive V2...")
        
        # Basic window (we know this works)
        self.root = tk.Tk()
        self.root.title("NexusController - Progressive V2")
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
        
        # Feature flags - turn on one at a time
        self.ENABLE_DARK_THEME = True      # Test 1: Dark theme
        self.ENABLE_CUSTOM_COLORS = True   # Test 2: Custom colors
        self.ENABLE_FANCY_FONTS = False    # Test 3: Special fonts
        self.ENABLE_COMPLEX_LAYOUT = False # Test 4: Complex layouts
        
        print(f"Feature flags: Dark={self.ENABLE_DARK_THEME}, Colors={self.ENABLE_CUSTOM_COLORS}")
        
        # Create UI progressively
        self.create_progressive_ui()
        
        print("Progressive V2 ready!")
    
    def create_progressive_ui(self):
        """Create UI with progressive features"""
        print("Creating progressive UI...")
        
        # STEP 1: Basic or Dark Theme Header
        if self.ENABLE_DARK_THEME:
            print("Testing: Dark theme header...")
            header = tk.Frame(self.root, bg='#1a1a2e', height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            if self.ENABLE_CUSTOM_COLORS:
                print("Testing: Custom colors...")
                title = tk.Label(header, text="🌐 NexusController Progressive", 
                               font=("Arial", 18, "bold"), fg='#00d4ff', bg='#1a1a2e')
            else:
                title = tk.Label(header, text="🌐 NexusController Progressive", 
                               font=("Arial", 18, "bold"), fg='white', bg='#1a1a2e')
            title.pack(side='left', padx=20, pady=10)
        else:
            print("Using: Light theme header...")
            header = tk.Label(self.root, text="NexusController - Progressive V2", 
                             font=("Arial", 16), bg='lightgray')
            header.pack(fill='x', pady=5)
        
        # STEP 2: Status Bar
        if self.ENABLE_DARK_THEME:
            print("Testing: Dark status bar...")
            status_frame = tk.Frame(self.root, bg='#0f0f1e', height=30)
            status_frame.pack(fill='x', side='bottom')
            status_frame.pack_propagate(False)
            
            if self.ENABLE_CUSTOM_COLORS:
                self.status_label = tk.Label(status_frame, text="NEXUS: Progressive V2 Ready", 
                                            fg='#00d4ff', bg='#0f0f1e', font=("Arial", 9))
            else:
                self.status_label = tk.Label(status_frame, text="NEXUS: Progressive V2 Ready", 
                                            fg='white', bg='#0f0f1e', font=("Arial", 9))
            self.status_label.pack(side='left', padx=10)
        else:
            self.status_label = tk.Label(self.root, text="Status: Ready", bg='lightgray')
            self.status_label.pack(side='bottom', fill='x')
        
        # STEP 3: Notebook
        print("Creating notebook...")
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # STEP 4: Tabs
        print("Creating tabs...")
        self.create_dashboard_tab()
        self.create_system_tab()
        self.create_servers_tab()
        
        print("Progressive UI created successfully!")
    
    def create_dashboard_tab(self):
        """Create dashboard with progressive styling"""
        print("Creating dashboard tab...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎯 Dashboard")
        
        if self.ENABLE_DARK_THEME:
            print("Testing: Dark dashboard background...")
            content = tk.Frame(frame, bg='#0f0f1e')
        else:
            content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Dashboard title
        if self.ENABLE_DARK_THEME and self.ENABLE_CUSTOM_COLORS:
            print("Testing: Custom colored title...")
            title = tk.Label(content, text="NEXUS COMMAND CENTER", 
                           font=("Arial", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
        elif self.ENABLE_DARK_THEME:
            title = tk.Label(content, text="NEXUS COMMAND CENTER", 
                           font=("Arial", 16, "bold"), fg='white', bg='#0f0f1e')
        else:
            title = tk.Label(content, text="System Dashboard", 
                           font=("Arial", 16, "bold"), bg='white')
        title.pack(pady=10)
        
        # System status area
        if self.ENABLE_DARK_THEME:
            print("Testing: Dark status frame...")
            if self.ENABLE_CUSTOM_COLORS:
                status_frame = tk.Frame(content, bg='#1a1a2e', relief='ridge', bd=2)
            else:
                status_frame = tk.Frame(content, bg='#333333', relief='ridge', bd=2)
        else:
            status_frame = tk.Frame(content, bg='#f0f0f0', relief='ridge', bd=2)
        status_frame.pack(fill='x', pady=10)
        
        # Status labels
        if self.ENABLE_DARK_THEME and self.ENABLE_CUSTOM_COLORS:
            print("Testing: Custom colored status labels...")
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
            
        elif self.ENABLE_DARK_THEME:
            section_title = tk.Label(status_frame, text="SYSTEM STATUS", 
                                    font=("Arial", 12, "bold"), fg='white', bg='#333333')
            section_title.pack(pady=5)
            
            self.cpu_label = tk.Label(status_frame, text="⚡ CPU: Checking...", 
                                     bg='#333333', fg='lightgreen', font=("Arial", 10))
            self.cpu_label.pack(anchor='w', padx=10, pady=2)
            
            self.mem_label = tk.Label(status_frame, text="💾 Memory: Checking...", 
                                     bg='#333333', fg='lightgreen', font=("Arial", 10))
            self.mem_label.pack(anchor='w', padx=10, pady=2)
            
            self.server_label = tk.Label(status_frame, text="🖥️ Ebon: Checking...", 
                                        bg='#333333', fg='yellow', font=("Arial", 10))
            self.server_label.pack(anchor='w', padx=10, pady=2)
        else:
            section_title = tk.Label(status_frame, text="System Status", 
                                    font=("Arial", 12, "bold"), bg='#f0f0f0')
            section_title.pack(pady=5)
            
            self.cpu_label = tk.Label(status_frame, text="CPU: Checking...", 
                                     bg='#f0f0f0', font=("Arial", 10))
            self.cpu_label.pack(anchor='w', padx=10, pady=2)
            
            self.mem_label = tk.Label(status_frame, text="Memory: Checking...", 
                                     bg='#f0f0f0', font=("Arial", 10))
            self.mem_label.pack(anchor='w', padx=10, pady=2)
            
            self.server_label = tk.Label(status_frame, text="Ebon: Checking...", 
                                        bg='#f0f0f0', font=("Arial", 10))
            self.server_label.pack(anchor='w', padx=10, pady=2)
        
        # Quick actions
        if self.ENABLE_DARK_THEME:
            actions_frame = tk.Frame(content, bg='#1a1a2e' if self.ENABLE_CUSTOM_COLORS else '#333333', 
                                   relief='groove', bd=2)
        else:
            actions_frame = tk.Frame(content, bg='#f0f0f0', relief='groove', bd=2)
        actions_frame.pack(fill='x', pady=10)
        
        # THIS IS THE CRITICAL TEST - Complex button styling
        if self.ENABLE_DARK_THEME and self.ENABLE_CUSTOM_COLORS:
            print("Testing: CRITICAL - Complex button styling...")
            
            # This might be the crash point
            action_title = tk.Label(actions_frame, text="QUICK ACTIONS", 
                                   font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            action_title.pack(pady=10)
            
            button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
            button_frame.pack(pady=10)
            
            # Complex button styling - potential crash
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
            tk.Button(button_frame, text="📊 SERVER STATS", 
                     command=self.server_stats, **button_style).pack(side='left', padx=5)
            
        else:
            # Simple button styling
            action_title = tk.Label(actions_frame, text="Quick Actions", 
                                   font=("Arial", 12, "bold"), 
                                   bg='#f0f0f0' if not self.ENABLE_DARK_THEME else '#333333',
                                   fg='black' if not self.ENABLE_DARK_THEME else 'white')
            action_title.pack(pady=10)
            
            button_frame = tk.Frame(actions_frame, 
                                   bg='#f0f0f0' if not self.ENABLE_DARK_THEME else '#333333')
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="System Scan", 
                     command=self.check_status).pack(side='left', padx=5)
            tk.Button(button_frame, text="Connect Ebon", 
                     command=self.connect_ebon).pack(side='left', padx=5)
            tk.Button(button_frame, text="Server Stats", 
                     command=self.server_stats).pack(side='left', padx=5)
        
        print("Dashboard tab created successfully!")
    
    def create_system_tab(self):
        """Create system tab"""
        print("Creating system tab...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💻 System")
        
        if self.ENABLE_DARK_THEME:
            content = tk.Frame(frame, bg='#0f0f1e')
        else:
            content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        if self.ENABLE_DARK_THEME and self.ENABLE_CUSTOM_COLORS:
            title = tk.Label(content, text="SYSTEM MANAGEMENT", 
                           font=("Arial", 14, "bold"), fg='#00d4ff', bg='#0f0f1e')
        else:
            title = tk.Label(content, text="System Information", 
                           font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # System info area
        self.system_text = scrolledtext.ScrolledText(content, height=15, width=80,
                                                    bg='#0a0a1e' if self.ENABLE_DARK_THEME else 'white',
                                                    fg='#0f8' if self.ENABLE_CUSTOM_COLORS else 'black',
                                                    font=('Arial', 10))
        self.system_text.pack(fill='both', expand=True, pady=10)
        
        # Initialize
        self.system_text.insert('1.0', f"Hostname: {socket.gethostname()}\\n")
        self.system_text.insert('end', f"Platform: {sys.platform}\\n")
        
        print("System tab created successfully!")
    
    def create_servers_tab(self):
        """Create servers tab"""
        print("Creating servers tab...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🌍 Servers")
        
        if self.ENABLE_DARK_THEME:
            content = tk.Frame(frame, bg='#0f0f1e')
        else:
            content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        if self.ENABLE_DARK_THEME and self.ENABLE_CUSTOM_COLORS:
            title = tk.Label(content, text="SERVER MANAGEMENT", 
                           font=("Arial", 14, "bold"), fg='#00d4ff', bg='#0f0f1e')
        else:
            title = tk.Label(content, text="Server Management", 
                           font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Server info
        for server_id, server_info in self.servers.items():
            info = tk.Label(content, 
                           text=f"{server_info['name']}: {server_info['host']}",
                           font=("Arial", 10),
                           bg='#0f0f1e' if self.ENABLE_DARK_THEME else 'white',
                           fg='#0f8' if self.ENABLE_CUSTOM_COLORS else 'black')
            info.pack(anchor='w', padx=10, pady=2)
        
        # Server output
        self.server_output = scrolledtext.ScrolledText(content, height=15, width=80,
                                                      bg='#0a0a1e' if self.ENABLE_DARK_THEME else 'white',
                                                      fg='#0f8' if self.ENABLE_CUSTOM_COLORS else 'black',
                                                      font=('Arial', 10))
        self.server_output.pack(fill='both', expand=True, pady=10)
        
        self.server_output.insert('1.0', "NexusController Server Management\\n")
        self.server_output.insert('end', "Ready for server operations.\\n")
        
        print("Servers tab created successfully!")
    
    def check_status(self):
        """Check system status"""
        try:
            print("Checking status...")
            
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
                self.server_label.config(text="🖥️ Ebon: ONLINE")
                if self.ENABLE_CUSTOM_COLORS:
                    self.server_label.config(fg='#0f8')
                else:
                    self.server_label.config(fg='green')
            else:
                self.server_label.config(text="🖥️ Ebon: OFFLINE")
                if self.ENABLE_CUSTOM_COLORS:
                    self.server_label.config(fg='#f00')
                else:
                    self.server_label.config(fg='red')
                    
        except Exception as e:
            print(f"Status check error: {e}")
    
    def connect_ebon(self):
        """Connect to ebon"""
        self.server_output.insert('end', f"\\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to Ebon...\\n")
        self.server_output.see('end')
    
    def server_stats(self):
        """Get server stats"""
        self.server_output.insert('end', f"\\n[{datetime.now().strftime('%H:%M:%S')}] Getting server stats...\\n")
        self.server_output.see('end')
    
    def on_closing(self):
        """Handle shutdown"""
        print("Shutting down Progressive V2...")
        self.shutdown_flag = True
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            print("Starting Progressive V2 main loop...")
            
            # Schedule initial status check
            self.root.after(1000, self.check_status)
            
            self.root.mainloop()
            print("Progressive V2 ended.")
            
        except Exception as e:
            print(f"Error in Progressive V2: {e}")

if __name__ == '__main__':
    print("Starting NexusController Progressive V2...")
    print("This version tests dark theme + custom colors step by step")
    
    try:
        app = NexusProgressiveV2()
        app.run()
    except Exception as e:
        print(f"Fatal error in Progressive V2: {e}")
        import traceback
        traceback.print_exc()
    
    print("Progressive V2 test complete.")