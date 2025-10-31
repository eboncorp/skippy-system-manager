#!/usr/bin/env python3
"""
NexusController - Absolute Minimal Working Version
Start with basic functionality and add features incrementally
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import socket
from datetime import datetime

class NexusMinimal:
    def __init__(self):
        print("Starting minimal NexusController...")
        
        # Basic window only
        self.root = tk.Tk()
        self.root.title("NexusController - Minimal Working")
        self.root.geometry("900x600")
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
        
        # Create absolutely minimal UI
        self.create_minimal_ui()
        
        print("Minimal NexusController ready!")
    
    def create_minimal_ui(self):
        """Create the most basic UI possible"""
        print("Creating minimal UI...")
        
        # Simple header
        header = tk.Label(self.root, text="NexusController - Minimal", 
                         font=("Arial", 16), bg='lightgray')
        header.pack(fill='x', pady=5)
        
        # Basic notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Dashboard tab - VERY simple
        self.create_simple_dashboard()
        
        # System tab
        self.create_simple_system()
        
        # Server tab
        self.create_simple_servers()
        
        print("Minimal UI created successfully!")
    
    def create_simple_dashboard(self):
        """Absolutely minimal dashboard"""
        print("Creating simple dashboard...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Dashboard")
        
        # Simple white background
        content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Basic title
        title = tk.Label(content, text="System Status", 
                        font=("Arial", 14), bg='white')
        title.pack(pady=10)
        
        # Simple status labels
        self.cpu_status = tk.Label(content, text="CPU: Checking...", 
                                  bg='white', font=("Arial", 10))
        self.cpu_status.pack(anchor='w', padx=10, pady=2)
        
        self.server_status = tk.Label(content, text="Ebon: Checking...", 
                                     bg='white', font=("Arial", 10))
        self.server_status.pack(anchor='w', padx=10, pady=2)
        
        # Simple button
        check_btn = tk.Button(content, text="Check Status", 
                             command=self.check_status,
                             font=("Arial", 10))
        check_btn.pack(pady=10)
        
        print("Simple dashboard created!")
    
    def create_simple_system(self):
        """Simple system tab"""
        print("Creating simple system tab...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="System")
        
        content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(content, text="System Information", 
                font=("Arial", 14), bg='white').pack(pady=10)
        
        # Simple text area
        self.system_text = tk.Text(content, height=10, width=60)
        self.system_text.pack(pady=10)
        
        # Add basic info
        self.system_text.insert('1.0', f"Hostname: {socket.gethostname()}\\n")
        self.system_text.insert('end', f"Platform: {sys.platform}\\n")
        
        print("Simple system tab created!")
    
    def create_simple_servers(self):
        """Simple servers tab"""
        print("Creating simple servers tab...")
        
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Servers")
        
        content = tk.Frame(frame, bg='white')
        content.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(content, text="Server Management", 
                font=("Arial", 14), bg='white').pack(pady=10)
        
        # Server info
        for server_id, server_info in self.servers.items():
            info = tk.Label(content, 
                           text=f"{server_info['name']}: {server_info['host']}",
                           bg='white', font=("Arial", 10))
            info.pack(anchor='w', padx=10, pady=2)
        
        # Simple buttons
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Connect", 
                 command=self.connect_ebon).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Web UI", 
                 command=self.open_web).pack(side='left', padx=5)
        
        # Output area
        self.server_output = scrolledtext.ScrolledText(content, height=10, width=60)
        self.server_output.pack(pady=10)
        
        self.server_output.insert('1.0', "NexusController Server Management\\n")
        self.server_output.insert('end', "Ready for server operations.\\n")
        
        print("Simple servers tab created!")
    
    def check_status(self):
        """Check system and server status"""
        try:
            print("Checking status...")
            
            # Simple CPU check
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                self.cpu_status.config(text=f"CPU: {cpu}%")
            except:
                self.cpu_status.config(text="CPU: N/A")
            
            # Simple server check
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('10.0.0.29', 22))
                sock.close()
                
                if result == 0:
                    self.server_status.config(text="Ebon: ONLINE", fg='green')
                else:
                    self.server_status.config(text="Ebon: OFFLINE", fg='red')
            except:
                self.server_status.config(text="Ebon: ERROR", fg='red')
                
        except Exception as e:
            print(f"Status check error: {e}")
    
    def connect_ebon(self):
        """Connect to ebon server"""
        self.server_output.insert('end', f"\\n[{datetime.now().strftime('%H:%M:%S')}] Connecting to Ebon...\\n")
        self.server_output.insert('end', "SSH: ebon@10.0.0.29\\n")
        self.server_output.see('end')
    
    def open_web(self):
        """Open web interface"""
        try:
            import webbrowser
            webbrowser.open("http://10.0.0.29")
            self.server_output.insert('end', f"\\n[{datetime.now().strftime('%H:%M:%S')}] Opening web interface...\\n")
        except Exception as e:
            self.server_output.insert('end', f"Web error: {e}\\n")
        self.server_output.see('end')
    
    def on_closing(self):
        """Handle shutdown"""
        print("Shutting down minimal NexusController...")
        self.shutdown_flag = True
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            print("Starting minimal main loop...")
            
            # Schedule initial status check after UI is ready
            self.root.after(1000, self.check_status)
            
            # Start main loop
            self.root.mainloop()
            print("Minimal NexusController ended.")
            
        except Exception as e:
            print(f"Error in minimal main loop: {e}")

if __name__ == '__main__':
    print("Starting NexusController Minimal Working Version...")
    
    try:
        app = NexusMinimal()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    print("Minimal version complete.")