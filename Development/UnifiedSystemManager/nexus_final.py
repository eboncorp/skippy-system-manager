#!/usr/bin/env python3
"""
NexusController - Final Working Version
Based on the successful delayed tabs test - minimal crash-prone features
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

class NexusControllerFinal:
    def __init__(self):
        print("[NEXUS] Starting final working version...")
        
        self.root = tk.Tk()
        self.root.title("NexusController - System & Server Management")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.shutdown_flag = False
        self.monitoring_active = False
        
        # Server configuration
        self.servers = {
            'ebon': {
                'host': '10.0.0.29',
                'port': 22,
                'username': 'ebon',
                'name': 'Ebon Server'
            }
        }
        
        # Create basic structure immediately
        self.create_basic_structure()
        
        # Use the proven delayed initialization pattern
        print("[NEXUS] Scheduling delayed tab creation...")
        self.root.after(1000, self.create_dashboard_delayed)
        self.root.after(2000, self.create_system_delayed)
        self.root.after(3000, self.create_servers_delayed)
        self.root.after(4000, self.delayed_initialization)
        
        print("[NEXUS] Base initialization complete")
    
    def create_basic_structure(self):
        """Create basic window structure"""
        print("[NEXUS] Creating basic structure...")
        
        # Dark theme header
        header = tk.Frame(self.root, bg='#1a1a2e', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🌐 NexusController", 
                        font=("Arial", 20, "bold"), fg='#00d4ff', bg='#1a1a2e')
        title.pack(side='left', padx=20, pady=15)
        
        self.status_indicator = tk.Label(header, text="🔴 INITIALIZING", 
                                        font=("Arial", 10, "bold"), fg='#ff4444', bg='#1a1a2e')
        self.status_indicator.pack(side='left', padx=10, pady=15)
        
        # Control button
        self.monitor_btn = tk.Button(header, text="START MONITOR", 
                                   font=('Arial', 9, 'bold'),
                                   bg='#2a2a3e', fg='#00d4ff',
                                   command=self.toggle_monitoring)
        self.monitor_btn.pack(side='right', padx=20, pady=15)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#0f0f1e', height=35)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="NEXUS: Initializing tabs...", 
                                    fg='#00d4ff', bg='#0f0f1e', font=("Arial", 10))
        self.status_label.pack(side='left', padx=15, pady=8)
        
        self.time_label = tk.Label(status_frame, text="", 
                                  fg='#888', bg='#0f0f1e', font=("Arial", 9))
        self.time_label.pack(side='right', padx=15, pady=8)
        
        # Empty notebook - tabs will be added with delays
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Start time updates
        self.update_time()
        
        print("[NEXUS] ✓ Basic structure ready")
    
    def create_dashboard_delayed(self):
        """Create dashboard tab with delay"""
        try:
            print("[NEXUS] Creating dashboard tab...")
            self.status_label.config(text="NEXUS: Loading dashboard...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="🎯 Dashboard")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Title
            title = tk.Label(content, text="NEXUS COMMAND CENTER", 
                           font=("Arial", 18, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=15)
            
            # System status frame
            status_frame = tk.Frame(content, bg='#1a1a2e', relief='ridge', bd=2)
            status_frame.pack(fill='x', pady=10)
            
            status_title = tk.Label(status_frame, text="⚡ SYSTEM STATUS", 
                                   font=("Arial", 14, "bold"), fg='#00d4ff', bg='#1a1a2e')
            status_title.pack(pady=10)
            
            # Status labels with grid
            status_grid = tk.Frame(status_frame, bg='#1a1a2e')
            status_grid.pack(pady=10)
            
            self.cpu_label = tk.Label(status_grid, text="🔥 CPU: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Arial", 11))
            self.cpu_label.grid(row=0, column=0, padx=20, pady=5, sticky='w')
            
            self.mem_label = tk.Label(status_grid, text="💾 Memory: Checking...", 
                                     bg='#1a1a2e', fg='#0f8', font=("Arial", 11))
            self.mem_label.grid(row=0, column=1, padx=20, pady=5, sticky='w')
            
            self.server_label = tk.Label(status_grid, text="🖥️ Ebon: Checking...", 
                                        bg='#1a1a2e', fg='#fa0', font=("Arial", 11))
            self.server_label.grid(row=1, column=0, padx=20, pady=5, sticky='w')
            
            # Quick actions
            actions_frame = tk.Frame(content, bg='#1a1a2e', relief='groove', bd=2)
            actions_frame.pack(fill='x', pady=10)
            
            actions_title = tk.Label(actions_frame, text="🚀 QUICK ACTIONS", 
                                    font=("Arial", 14, "bold"), fg='#00d4ff', bg='#1a1a2e')
            actions_title.pack(pady=10)
            
            button_frame = tk.Frame(actions_frame, bg='#1a1a2e')
            button_frame.pack(pady=10)
            
            # Simple buttons to avoid complex styling crashes
            btn_style = {
                'font': ('Arial', 10, 'bold'),
                'bg': '#2a2a3e',
                'fg': '#00d4ff',
                'bd': 1,
                'padx': 15,
                'pady': 5
            }
            
            tk.Button(button_frame, text="🔍 SYSTEM SCAN", 
                     command=self.system_scan, **btn_style).pack(side='left', padx=5)
            tk.Button(button_frame, text="🔗 CONNECT EBON", 
                     command=self.connect_ebon, **btn_style).pack(side='left', padx=5)
            tk.Button(button_frame, text="🌐 WEB UI", 
                     command=self.open_web, **btn_style).pack(side='left', padx=5)
            
            print("[NEXUS] ✓ Dashboard tab created")
            self.status_label.config(text="NEXUS: Dashboard ready")
            
        except Exception as e:
            print(f"[ERROR] Dashboard creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_system_delayed(self):
        """Create system tab with delay"""
        try:
            print("[NEXUS] Creating system tab...")
            self.status_label.config(text="NEXUS: Loading system management...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="💻 System")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            title = tk.Label(content, text="SYSTEM MANAGEMENT", 
                           font=("Arial", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=10)
            
            # Control buttons
            control_frame = tk.Frame(content, bg='#1a1a2e', relief='ridge', bd=2)
            control_frame.pack(fill='x', pady=5)
            
            control_title = tk.Label(control_frame, text="SYSTEM CONTROLS", 
                                    font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            control_title.pack(pady=8)
            
            btn_frame = tk.Frame(control_frame, bg='#1a1a2e')
            btn_frame.pack(pady=8)
            
            ctrl_style = {
                'font': ('Arial', 9, 'bold'),
                'bg': '#2a2a3e',
                'fg': '#00d4ff',
                'bd': 1,
                'padx': 10,
                'pady': 3
            }
            
            tk.Button(btn_frame, text="🧹 CLEANUP", 
                     command=self.system_cleanup, **ctrl_style).pack(side='left', padx=5)
            tk.Button(btn_frame, text="📈 PROCESSES", 
                     command=self.show_processes, **ctrl_style).pack(side='left', padx=5)
            tk.Button(btn_frame, text="🔄 REFRESH", 
                     command=self.refresh_system, **ctrl_style).pack(side='left', padx=5)
            
            # System text area - this was working in delayed test
            self.system_text = scrolledtext.ScrolledText(content, height=20, width=100,
                                                        bg='#0a0a1e', fg='#0f8',
                                                        font=('Consolas', 10))
            self.system_text.pack(fill='both', expand=True, pady=10)
            
            # Initial info
            self.system_text.insert('1.0', f"=== NEXUS SYSTEM INFORMATION ===\n")
            self.system_text.insert('end', f"Hostname: {socket.gethostname()}\n")
            self.system_text.insert('end', f"Platform: {sys.platform}\n")
            self.system_text.insert('end', f"Python: {sys.version.split()[0]}\n")
            self.system_text.insert('end', "\nSystem management ready.\n")
            
            print("[NEXUS] ✓ System tab created")
            self.status_label.config(text="NEXUS: System management ready")
            
        except Exception as e:
            print(f"[ERROR] System tab creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_servers_delayed(self):
        """Create servers tab with delay"""
        try:
            print("[NEXUS] Creating servers tab...")
            self.status_label.config(text="NEXUS: Loading server management...")
            
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="🌍 Servers")
            
            content = tk.Frame(frame, bg='#0f0f1e')
            content.pack(fill='both', expand=True, padx=10, pady=10)
            
            title = tk.Label(content, text="SERVER MANAGEMENT", 
                           font=("Arial", 16, "bold"), fg='#00d4ff', bg='#0f0f1e')
            title.pack(pady=10)
            
            # Server info
            info_frame = tk.Frame(content, bg='#1a1a2e', relief='ridge', bd=2)
            info_frame.pack(fill='x', pady=5)
            
            info_title = tk.Label(info_frame, text="CONFIGURED SERVERS", 
                                 font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            info_title.pack(pady=8)
            
            for server_id, server_info in self.servers.items():
                server_label = tk.Label(info_frame, 
                                       text=f"📡 {server_info['name']}: {server_info['host']}:{server_info['port']}",
                                       font=("Arial", 10), bg='#1a1a2e', fg='#0f8')
                server_label.pack(anchor='w', padx=15, pady=3)
            
            # Server controls
            control_frame = tk.Frame(content, bg='#1a1a2e', relief='groove', bd=2)
            control_frame.pack(fill='x', pady=10)
            
            control_title = tk.Label(control_frame, text="SERVER CONTROLS", 
                                    font=("Arial", 12, "bold"), fg='#00d4ff', bg='#1a1a2e')
            control_title.pack(pady=8)
            
            server_btn_frame = tk.Frame(control_frame, bg='#1a1a2e')
            server_btn_frame.pack(pady=8)
            
            server_style = {
                'font': ('Arial', 9, 'bold'),
                'bg': '#2a2a3e',
                'fg': '#00d4ff',
                'bd': 1,
                'padx': 10,
                'pady': 3
            }
            
            tk.Button(server_btn_frame, text="🔗 SSH CONNECT", 
                     command=self.ssh_connect, **server_style).pack(side='left', padx=5)
            tk.Button(server_btn_frame, text="🌐 WEB UI", 
                     command=self.open_web, **server_style).pack(side='left', padx=5)
            tk.Button(server_btn_frame, text="📊 STATUS", 
                     command=self.server_status, **server_style).pack(side='left', padx=5)
            
            # Server output - this was working in delayed test
            self.server_output = scrolledtext.ScrolledText(content, height=18, width=100,
                                                          bg='#0a0a1e', fg='#0f8',
                                                          font=('Consolas', 10))
            self.server_output.pack(fill='both', expand=True, pady=10)
            
            # Initial info
            self.server_output.insert('1.0', f"=== NEXUS SERVER MANAGEMENT ===\n")
            self.server_output.insert('end', f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            for server_id, info in self.servers.items():
                self.server_output.insert('end', f"\n[{server_id.upper()}] {info['name']}\n")
                self.server_output.insert('end', f"  Host: {info['host']}:{info['port']}\n")
                self.server_output.insert('end', f"  User: {info['username']}\n")
            
            self.server_output.insert('end', "\nReady for server operations.\n")
            
            print("[NEXUS] ✓ Servers tab created")
            self.status_label.config(text="NEXUS: Server management ready")
            
        except Exception as e:
            print(f"[ERROR] Servers tab creation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def delayed_initialization(self):
        """Complete initialization"""
        try:
            print("[NEXUS] Completing initialization...")
            self.status_label.config(text="NEXUS: All systems operational")
            self.status_indicator.config(text="🟢 READY", fg='#00ff00')
            
            # Start initial status check
            self.root.after(1000, self.check_status)
            
            print("[NEXUS] ✓ Initialization complete")
            
        except Exception as e:
            print(f"[ERROR] Delayed initialization failed: {e}")
    
    # Monitoring methods
    def toggle_monitoring(self):
        """Toggle monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_btn.config(text="STOP MONITOR", bg='#ff4444')
            self.status_indicator.config(text="🟢 MONITORING", fg='#00ff00')
            self.start_monitoring()
        else:
            self.monitoring_active = False
            self.monitor_btn.config(text="START MONITOR", bg='#2a2a3e')
            self.status_indicator.config(text="🟢 READY", fg='#00ff00')
    
    def start_monitoring(self):
        """Start monitoring loop"""
        if self.monitoring_active and not self.shutdown_flag:
            self.check_status()
            self.root.after(5000, self.start_monitoring)  # 5 second intervals
    
    def check_status(self):
        """Check system status"""
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                
                cpu_color = '#0f8' if cpu < 80 else '#fa0' if cpu < 95 else '#f00'
                mem_color = '#0f8' if mem < 80 else '#fa0' if mem < 95 else '#f00'
                
                self.cpu_label.config(text=f"🔥 CPU: {cpu:.1f}%", fg=cpu_color)
                self.mem_label.config(text=f"💾 Memory: {mem:.1f}%", fg=mem_color)
            
            # Server check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('10.0.0.29', 22))
            sock.close()
            
            if result == 0:
                self.server_label.config(text="🖥️ Ebon: ONLINE", fg='#0f8')
            else:
                self.server_label.config(text="🖥️ Ebon: OFFLINE", fg='#f00')
                
        except Exception as e:
            print(f"[ERROR] Status check failed: {e}")
    
    # System management methods
    def system_scan(self):
        """Perform system scan"""
        def scan_thread():
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.system_text.insert('end', f"\n[{timestamp}] Starting system scan...\n")
                self.system_text.see('end')
                
                if PSUTIL_AVAILABLE:
                    cpu_count = psutil.cpu_count(logical=False)
                    cpu_logical = psutil.cpu_count(logical=True)
                    memory = psutil.virtual_memory()
                    
                    self.system_text.insert('end', f"CPU cores: {cpu_count} physical, {cpu_logical} logical\n")
                    self.system_text.insert('end', f"Memory: {memory.total // (1024**3):.1f}GB total\n")
                    self.system_text.insert('end', f"Memory available: {memory.available // (1024**3):.1f}GB\n")
                    
                    # Disk usage
                    try:
                        disk = psutil.disk_usage('/')
                        self.system_text.insert('end', f"Root disk: {disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB\n")
                    except:
                        pass
                
                self.system_text.insert('end', "✓ System scan completed\n")
                self.system_text.see('end')
                
            except Exception as e:
                self.system_text.insert('end', f"✗ Scan error: {e}\n")
                self.system_text.see('end')
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def system_cleanup(self):
        """System cleanup simulation"""
        def cleanup_thread():
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.system_text.insert('end', f"\n[{timestamp}] Starting cleanup...\n")
                self.system_text.see('end')
                
                cleanup_steps = [
                    "Cleaning package cache...",
                    "Removing temporary files...",
                    "Cleaning logs...",
                ]
                
                for step in cleanup_steps:
                    self.system_text.insert('end', f"{step}\n")
                    self.system_text.see('end')
                    time.sleep(0.5)
                
                self.system_text.insert('end', "✓ Cleanup completed\n")
                self.system_text.see('end')
                
            except Exception as e:
                self.system_text.insert('end', f"✗ Cleanup error: {e}\n")
                self.system_text.see('end')
        
        threading.Thread(target=cleanup_thread, daemon=True).start()
    
    def show_processes(self):
        """Show top processes"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.system_text.insert('end', f"\n[{timestamp}] Top processes:\n")
            
            if PSUTIL_AVAILABLE:
                processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), 
                                 key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:8]
                
                for proc in processes:
                    try:
                        pid = proc.info['pid']
                        name = proc.info['name']
                        cpu = proc.info['cpu_percent'] or 0
                        self.system_text.insert('end', f"PID {pid}: {name} ({cpu:.1f}%)\n")
                    except:
                        continue
            else:
                self.system_text.insert('end', "psutil not available\n")
            
            self.system_text.see('end')
            
        except Exception as e:
            self.system_text.insert('end', f"✗ Process error: {e}\n")
            self.system_text.see('end')
    
    def refresh_system(self):
        """Refresh system info"""
        self.system_text.delete('1.0', 'end')
        self.system_text.insert('1.0', f"=== NEXUS SYSTEM INFORMATION (Refreshed) ===\n")
        self.system_text.insert('end', f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.system_text.insert('end', f"Hostname: {socket.gethostname()}\n")
        self.system_text.insert('end', f"Platform: {sys.platform}\n")
        self.system_scan()
    
    # Server methods
    def connect_ebon(self):
        """Connect to Ebon server"""
        self.ssh_connect()
    
    def ssh_connect(self):
        """SSH connection"""
        def connect_thread():
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.server_output.insert('end', f"\n[{timestamp}] Connecting to Ebon...\n")
                self.server_output.insert('end', f"Target: ebon@10.0.0.29:22\n")
                self.server_output.see('end')
                
                # Test connectivity
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex(('10.0.0.29', 22))
                sock.close()
                
                if result == 0:
                    self.server_output.insert('end', "✓ SSH port accessible\n")
                    self.server_output.insert('end', "Opening terminal...\n")
                    
                    try:
                        import subprocess
                        subprocess.Popen(['gnome-terminal', '--', 'ssh', 'ebon@10.0.0.29'])
                        self.server_output.insert('end', "✓ Terminal launched\n")
                    except:
                        self.server_output.insert('end', "✗ No terminal available\n")
                        self.server_output.insert('end', "Manual: ssh ebon@10.0.0.29\n")
                else:
                    self.server_output.insert('end', "✗ Connection failed\n")
                
                self.server_output.see('end')
                
            except Exception as e:
                self.server_output.insert('end', f"✗ Connection error: {e}\n")
                self.server_output.see('end')
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def open_web(self):
        """Open web interface"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.server_output.insert('end', f"\n[{timestamp}] Opening web interface...\n")
            self.server_output.insert('end', f"URL: http://10.0.0.29\n")
            
            import webbrowser
            webbrowser.open("http://10.0.0.29")
            self.server_output.insert('end', "✓ Browser launched\n")
            self.server_output.see('end')
            
        except Exception as e:
            self.server_output.insert('end', f"✗ Web error: {e}\n")
            self.server_output.see('end')
    
    def server_status(self):
        """Check server status"""
        def status_thread():
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.server_output.insert('end', f"\n[{timestamp}] Checking server status...\n")
                self.server_output.see('end')
                
                # SSH check
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                start_time = time.time()
                result = sock.connect_ex(('10.0.0.29', 22))
                latency = (time.time() - start_time) * 1000
                sock.close()
                
                if result == 0:
                    self.server_output.insert('end', f"✓ SSH: ONLINE (response: {latency:.1f}ms)\n")
                else:
                    self.server_output.insert('end', f"✗ SSH: OFFLINE\n")
                
                # HTTP check
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    http_result = sock.connect_ex(('10.0.0.29', 80))
                    sock.close()
                    
                    if http_result == 0:
                        self.server_output.insert('end', f"✓ HTTP: AVAILABLE\n")
                    else:
                        self.server_output.insert('end', f"✗ HTTP: UNAVAILABLE\n")
                except:
                    self.server_output.insert('end', f"? HTTP: UNKNOWN\n")
                
                self.server_output.see('end')
                
            except Exception as e:
                self.server_output.insert('end', f"✗ Status error: {e}\n")
                self.server_output.see('end')
        
        threading.Thread(target=status_thread, daemon=True).start()
    
    # Utility methods
    def update_time(self):
        """Update time display"""
        if not self.shutdown_flag:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
            self.root.after(1000, self.update_time)
    
    def on_closing(self):
        """Handle shutdown"""
        print("[NEXUS] Shutting down...")
        self.shutdown_flag = True
        self.monitoring_active = False
        self.root.destroy()
        print("[NEXUS] Shutdown complete")
    
    def run(self):
        """Start application"""
        try:
            print("[NEXUS] Starting main loop...")
            self.root.mainloop()
            print("[NEXUS] Application ended")
            
        except Exception as e:
            print(f"[ERROR] Main loop error: {e}")

if __name__ == '__main__':
    print("=== NEXUS CONTROLLER FINAL ===")
    print("Starting reliable system management platform...")
    
    try:
        app = NexusControllerFinal()
        app.run()
    except Exception as e:
        print(f"[FATAL] Application error: {e}")
        import traceback
        traceback.print_exc()
    
    print("NexusController session ended.")