#!/usr/bin/env python3
"""
NexusController GUI - Thread-safe modern interface
Separate GUI module with proper thread safety and modern design
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from tkinter import font as tkfont

# Import core modules
from nexus_controller_v2 import (
    NexusConfig, SecurityManager, SSHManager, NetworkDiscovery,
    CloudIntegration, SystemMonitor, BackupManager
)

class ThreadSafeGUI:
    """Base class for thread-safe GUI operations"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.gui_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="NexusWorker")
        self.shutdown_flag = threading.Event()
        
        # Start GUI update processor
        self.root.after(100, self._process_gui_updates)
    
    def schedule_gui_update(self, func: Callable, *args, **kwargs):
        """Schedule a GUI update to run on the main thread"""
        self.gui_queue.put((func, args, kwargs))
    
    def _process_gui_updates(self):
        """Process queued GUI updates on main thread"""
        try:
            while True:
                try:
                    func, args, kwargs = self.gui_queue.get_nowait()
                    func(*args, **kwargs)
                except Empty:
                    break
                except Exception as e:
                    logging.error(f"GUI update error: {e}")
        except Exception as e:
            logging.error(f"GUI queue processing error: {e}")
        
        # Schedule next update
        if not self.shutdown_flag.is_set():
            self.root.after(100, self._process_gui_updates)
    
    def run_in_background(self, func: Callable, callback: Callable = None, *args, **kwargs):
        """Run function in background thread with optional callback"""
        def wrapper():
            try:
                result = func(*args, **kwargs)
                if callback:
                    self.schedule_gui_update(callback, result)
            except Exception as e:
                logging.error(f"Background task error: {e}")
                if callback:
                    self.schedule_gui_update(callback, None, error=str(e))
        
        self.executor.submit(wrapper)
    
    def shutdown(self):
        """Shutdown background threads"""
        self.shutdown_flag.set()
        self.executor.shutdown(wait=True)

class ModernTheme:
    """Modern dark theme configuration"""
    
    COLORS = {
        'bg_primary': '#1a1a2e',
        'bg_secondary': '#16213e',
        'bg_tertiary': '#0f1419',
        'accent': '#00d4ff',
        'accent_hover': '#00a8cc',
        'text_primary': '#ffffff',
        'text_secondary': '#b0b0b0',
        'text_muted': '#666666',
        'success': '#00ff88',
        'warning': '#ffaa00',
        'error': '#ff4444',
        'border': '#333333'
    }
    
    @classmethod
    def configure_ttk_style(cls):
        """Configure TTK style with modern theme"""
        style = ttk.Style()
        
        # Configure notebook
        style.configure('Modern.TNotebook', 
                       background=cls.COLORS['bg_primary'],
                       borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                       background=cls.COLORS['bg_secondary'],
                       foreground=cls.COLORS['text_secondary'],
                       padding=[20, 10])
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', cls.COLORS['accent']),
                           ('active', cls.COLORS['accent_hover'])],
                 foreground=[('selected', cls.COLORS['bg_primary']),
                           ('active', cls.COLORS['text_primary'])])
        
        # Configure buttons
        style.configure('Modern.TButton',
                       background=cls.COLORS['accent'],
                       foreground=cls.COLORS['bg_primary'],
                       borderwidth=0,
                       focuscolor=cls.COLORS['accent'],
                       padding=[20, 10])
        style.map('Modern.TButton',
                 background=[('active', cls.COLORS['accent_hover']),
                           ('pressed', cls.COLORS['accent_hover'])])
        
        # Configure frames
        style.configure('Modern.TFrame',
                       background=cls.COLORS['bg_secondary'],
                       borderwidth=1,
                       relief='solid')
        
        # Configure labels
        style.configure('Modern.TLabel',
                       background=cls.COLORS['bg_secondary'],
                       foreground=cls.COLORS['text_primary'])
        
        # Configure treeview
        style.configure('Modern.Treeview',
                       background=cls.COLORS['bg_tertiary'],
                       foreground=cls.COLORS['text_primary'],
                       fieldbackground=cls.COLORS['bg_tertiary'],
                       borderwidth=0,
                       selectbackground=cls.COLORS['accent'])
        style.configure('Modern.Treeview.Heading',
                       background=cls.COLORS['bg_secondary'],
                       foreground=cls.COLORS['text_primary'],
                       borderwidth=1,
                       relief='solid')

class StatusBar(tk.Frame):
    """Modern status bar with system information"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=ModernTheme.COLORS['bg_tertiary'], height=30)
        self.pack_propagate(False)
        
        # Status text
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            self, textvariable=self.status_var,
            bg=ModernTheme.COLORS['bg_tertiary'],
            fg=ModernTheme.COLORS['text_secondary'],
            font=('Arial', 9)
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Connection status
        self.connection_var = tk.StringVar(value="Disconnected")
        self.connection_label = tk.Label(
            self, textvariable=self.connection_var,
            bg=ModernTheme.COLORS['bg_tertiary'],
            fg=ModernTheme.COLORS['error'],
            font=('Arial', 9)
        )
        self.connection_label.pack(side='right', padx=10, pady=5)
        
        # Time
        self.time_var = tk.StringVar()
        self.time_label = tk.Label(
            self, textvariable=self.time_var,
            bg=ModernTheme.COLORS['bg_tertiary'],
            fg=ModernTheme.COLORS['text_muted'],
            font=('Arial', 9)
        )
        self.time_label.pack(side='right', padx=10, pady=5)
        
        self.update_time()
    
    def update_status(self, message: str, status_type: str = 'info'):
        """Update status message"""
        colors = {
            'info': ModernTheme.COLORS['text_secondary'],
            'success': ModernTheme.COLORS['success'],
            'warning': ModernTheme.COLORS['warning'],
            'error': ModernTheme.COLORS['error']
        }
        
        self.status_var.set(message)
        self.status_label.config(fg=colors.get(status_type, colors['info']))
    
    def update_connection_status(self, connected: bool, server: str = None):
        """Update connection status"""
        if connected and server:
            self.connection_var.set(f"Connected to {server}")
            self.connection_label.config(fg=ModernTheme.COLORS['success'])
        else:
            self.connection_var.set("Disconnected")
            self.connection_label.config(fg=ModernTheme.COLORS['error'])
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.after(1000, self.update_time)

class NetworkTab(ttk.Frame):
    """Network discovery and management tab"""
    
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.gui = gui_controller
        self.setup_ui()
        
        # Auto-refresh timer
        self.auto_refresh = False
        self.refresh_interval = 30000  # 30 seconds
    
    def setup_ui(self):
        """Setup network tab UI"""
        
        # Control frame
        control_frame = ttk.Frame(self, style='Modern.TFrame')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Network range input
        tk.Label(control_frame, text="Network Range:",
                bg=ModernTheme.COLORS['bg_secondary'],
                fg=ModernTheme.COLORS['text_primary']).pack(side='left', padx=5)
        
        self.network_var = tk.StringVar(value="10.0.0.0/24")
        self.network_entry = tk.Entry(control_frame, textvariable=self.network_var,
                                     bg=ModernTheme.COLORS['bg_tertiary'],
                                     fg=ModernTheme.COLORS['text_primary'],
                                     insertbackground=ModernTheme.COLORS['accent'],
                                     width=20)
        self.network_entry.pack(side='left', padx=5)
        
        # Scan button
        self.scan_btn = ttk.Button(control_frame, text="Scan Network",
                                  style='Modern.TButton',
                                  command=self.start_network_scan)
        self.scan_btn.pack(side='left', padx=5)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar()
        self.auto_refresh_cb = tk.Checkbutton(
            control_frame, text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
            bg=ModernTheme.COLORS['bg_secondary'],
            fg=ModernTheme.COLORS['text_primary'],
            selectcolor=ModernTheme.COLORS['bg_tertiary'],
            activebackground=ModernTheme.COLORS['bg_secondary']
        )
        self.auto_refresh_cb.pack(side='right', padx=5)
        
        # Results frame
        results_frame = ttk.Frame(self, style='Modern.TFrame')
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for devices
        columns = ('IP', 'Hostname', 'MAC', 'Vendor', 'Status', 'Last Seen')
        self.device_tree = ttk.Treeview(results_frame, columns=columns,
                                       show='tree headings',
                                       style='Modern.Treeview')
        
        # Configure columns
        self.device_tree.heading('#0', text='Type')
        self.device_tree.column('#0', width=80)
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient='vertical',
                                   command=self.device_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient='horizontal',
                                   command=self.device_tree.xview)
        
        self.device_tree.configure(yscrollcommand=v_scrollbar.set,
                                  xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.device_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0,
                                   bg=ModernTheme.COLORS['bg_secondary'],
                                   fg=ModernTheme.COLORS['text_primary'])
        self.context_menu.add_command(label="Connect", command=self.connect_to_device)
        self.context_menu.add_command(label="Ping", command=self.ping_device)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Properties", command=self.show_device_properties)
        
        self.device_tree.bind("<Button-3>", self.show_context_menu)
    
    def start_network_scan(self):
        """Start network scan in background"""
        network_range = self.network_var.get()
        
        # Disable scan button
        self.scan_btn.config(state='disabled', text='Scanning...')
        self.gui.status_bar.update_status(f"Scanning network: {network_range}", 'info')
        
        # Run scan in background
        self.gui.run_in_background(
            self.gui.network_discovery.scan_network,
            self.on_scan_complete,
            network_range
        )
    
    def on_scan_complete(self, devices: Dict[str, Any], error: str = None):
        """Handle scan completion"""
        # Re-enable scan button
        self.scan_btn.config(state='normal', text='Scan Network')
        
        if error:
            self.gui.status_bar.update_status(f"Scan failed: {error}", 'error')
            messagebox.showerror("Scan Error", f"Network scan failed:\n{error}")
            return
        
        if not devices:
            self.gui.status_bar.update_status("No devices found", 'warning')
            return
        
        # Update device tree
        self.update_device_tree(devices)
        self.gui.status_bar.update_status(f"Found {len(devices)} devices", 'success')
    
    def update_device_tree(self, devices: Dict[str, Any]):
        """Update device tree with scan results"""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Add devices
        for ip, device in devices.items():
            device_type = "🖥️" if device.get('hostname', '').startswith('ebon') else "📱"
            
            self.device_tree.insert('', 'end',
                                   text=device_type,
                                   values=(
                                       device['ip'],
                                       device.get('hostname', 'Unknown'),
                                       device.get('mac', 'Unknown'),
                                       device.get('vendor', 'Unknown'),
                                       device.get('status', 'Unknown'),
                                       device.get('discovered_at', '')
                                   ))
    
    def show_context_menu(self, event):
        """Show context menu"""
        item = self.device_tree.identify_row(event.y)
        if item:
            self.device_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def connect_to_device(self):
        """Connect to selected device"""
        selection = self.device_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.device_tree.item(item, 'values')
        ip = values[0]
        hostname = values[1]
        
        # Show connection dialog
        self.show_connection_dialog(ip, hostname)
    
    def ping_device(self):
        """Ping selected device"""
        selection = self.device_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.device_tree.item(item, 'values')
        ip = values[0]
        
        # Run ping in background
        self.gui.run_in_background(self.ping_host, self.on_ping_complete, ip)
    
    def ping_host(self, ip: str) -> Dict[str, Any]:
        """Ping host and return results"""
        import subprocess
        
        try:
            result = subprocess.run(
                ['ping', '-c', '3', '-W', '3', ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def on_ping_complete(self, result: Dict[str, Any], error: str = None):
        """Handle ping completion"""
        if error:
            messagebox.showerror("Ping Error", f"Ping failed:\n{error}")
            return
        
        if result['success']:
            messagebox.showinfo("Ping Success", result['output'])
        else:
            messagebox.showerror("Ping Failed", result['error'])
    
    def show_device_properties(self):
        """Show device properties dialog"""
        selection = self.device_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.device_tree.item(item, 'values')
        
        # Create properties window
        props_window = tk.Toplevel(self)
        props_window.title("Device Properties")
        props_window.geometry("400x300")
        props_window.configure(bg=ModernTheme.COLORS['bg_primary'])
        
        # Properties text
        props_text = scrolledtext.ScrolledText(
            props_window,
            bg=ModernTheme.COLORS['bg_tertiary'],
            fg=ModernTheme.COLORS['text_primary'],
            insertbackground=ModernTheme.COLORS['accent']
        )
        props_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Format properties
        properties = f"""Device Properties:

IP Address: {values[0]}
Hostname: {values[1]}
MAC Address: {values[2]}
Vendor: {values[3]}
Status: {values[4]}
Last Seen: {values[5]}
"""
        
        props_text.insert('1.0', properties)
        props_text.config(state='disabled')
    
    def show_connection_dialog(self, ip: str, hostname: str):
        """Show SSH connection dialog"""
        # Create connection window
        conn_window = tk.Toplevel(self)
        conn_window.title(f"Connect to {hostname or ip}")
        conn_window.geometry("400x300")
        conn_window.configure(bg=ModernTheme.COLORS['bg_primary'])
        
        # Connection form
        form_frame = ttk.Frame(conn_window, style='Modern.TFrame')
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Username
        tk.Label(form_frame, text="Username:",
                bg=ModernTheme.COLORS['bg_secondary'],
                fg=ModernTheme.COLORS['text_primary']).grid(row=0, column=0, sticky='w', pady=5)
        
        username_var = tk.StringVar(value="ebon")
        username_entry = tk.Entry(form_frame, textvariable=username_var,
                                 bg=ModernTheme.COLORS['bg_tertiary'],
                                 fg=ModernTheme.COLORS['text_primary'],
                                 insertbackground=ModernTheme.COLORS['accent'])
        username_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Port
        tk.Label(form_frame, text="Port:",
                bg=ModernTheme.COLORS['bg_secondary'],
                fg=ModernTheme.COLORS['text_primary']).grid(row=1, column=0, sticky='w', pady=5)
        
        port_var = tk.StringVar(value="22")
        port_entry = tk.Entry(form_frame, textvariable=port_var,
                             bg=ModernTheme.COLORS['bg_tertiary'],
                             fg=ModernTheme.COLORS['text_primary'],
                             insertbackground=ModernTheme.COLORS['accent'])
        port_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Authentication method
        tk.Label(form_frame, text="Authentication:",
                bg=ModernTheme.COLORS['bg_secondary'],
                fg=ModernTheme.COLORS['text_primary']).grid(row=2, column=0, sticky='w', pady=5)
        
        auth_var = tk.StringVar(value="key")
        auth_combo = ttk.Combobox(form_frame, textvariable=auth_var,
                                 values=["key", "password"],
                                 state="readonly")
        auth_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Password/Key file
        tk.Label(form_frame, text="Password/Key:",
                bg=ModernTheme.COLORS['bg_secondary'],
                fg=ModernTheme.COLORS['text_primary']).grid(row=3, column=0, sticky='w', pady=5)
        
        auth_value_var = tk.StringVar()
        auth_value_entry = tk.Entry(form_frame, textvariable=auth_value_var,
                                   bg=ModernTheme.COLORS['bg_tertiary'],
                                   fg=ModernTheme.COLORS['text_primary'],
                                   insertbackground=ModernTheme.COLORS['accent'],
                                   show="*")
        auth_value_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Browse button for key file
        def browse_key():
            if auth_var.get() == "key":
                filename = filedialog.askopenfilename(
                    title="Select SSH Key",
                    filetypes=[("SSH Keys", "id_*"), ("All Files", "*")]
                )
                if filename:
                    auth_value_var.set(filename)
        
        browse_btn = ttk.Button(form_frame, text="Browse",
                               command=browse_key,
                               style='Modern.TButton')
        browse_btn.grid(row=3, column=2, padx=5, pady=5)
        
        # Connect button
        def do_connect():
            try:
                username = username_var.get()
                port = int(port_var.get())
                auth_method = auth_var.get()
                auth_value = auth_value_var.get()
                
                if auth_method == "password":
                    # Connect with password
                    self.gui.run_in_background(
                        self.gui.ssh_manager.connect,
                        lambda client, error=None: self.on_connection_complete(client, error, conn_window, ip),
                        ip, username, port, password=auth_value
                    )
                else:
                    # Connect with key
                    self.gui.run_in_background(
                        self.gui.ssh_manager.connect,
                        lambda client, error=None: self.on_connection_complete(client, error, conn_window, ip),
                        ip, username, port, key_path=auth_value
                    )
                
                conn_window.destroy()
                
            except ValueError as e:
                messagebox.showerror("Connection Error", f"Invalid port number: {port_var.get()}")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        
        connect_btn = ttk.Button(form_frame, text="Connect",
                                command=do_connect,
                                style='Modern.TButton')
        connect_btn.grid(row=4, column=1, pady=20)
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Update password field visibility
        def on_auth_change(*args):
            if auth_var.get() == "password":
                auth_value_entry.config(show="*")
                browse_btn.config(state='disabled')
            else:
                auth_value_entry.config(show="")
                browse_btn.config(state='normal')
        
        auth_var.trace('w', on_auth_change)
    
    def on_connection_complete(self, client, error: str = None, window=None, server_ip: str = None):
        """Handle SSH connection completion"""
        if error:
            messagebox.showerror("Connection Failed", f"SSH connection failed:\n{error}")
            self.gui.status_bar.update_connection_status(False)
        else:
            messagebox.showinfo("Connection Success", f"Connected to {server_ip}")
            self.gui.status_bar.update_connection_status(True, server_ip)
            # Store active connection
            self.gui.active_ssh_client = client
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh of network scan"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self.schedule_refresh()
    
    def schedule_refresh(self):
        """Schedule next refresh"""
        if self.auto_refresh:
            self.after(self.refresh_interval, self.auto_scan)
    
    def auto_scan(self):
        """Perform automatic scan"""
        if self.auto_refresh:
            self.start_network_scan()
            self.schedule_refresh()

class SystemTab(ttk.Frame):
    """System monitoring and management tab"""
    
    def __init__(self, parent, gui_controller):
        super().__init__(parent)
        self.gui = gui_controller
        self.setup_ui()
        
        # Start monitoring
        self.monitoring = True
        self.update_system_info()
    
    def setup_ui(self):
        """Setup system tab UI"""
        
        # System info frame
        info_frame = ttk.LabelFrame(self, text="System Information",
                                   style='Modern.TFrame')
        info_frame.pack(fill='x', padx=10, pady=5)
        
        # Create info labels
        self.info_labels = {}
        info_items = [
            ('CPU Usage', 'cpu_usage'),
            ('Memory Usage', 'memory_usage'),
            ('Disk Usage', 'disk_usage'),
            ('Network I/O', 'network_io'),
            ('Active Processes', 'processes'),
            ('Uptime', 'uptime')
        ]
        
        for i, (label, key) in enumerate(info_items):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(info_frame, text=f"{label}:",
                    bg=ModernTheme.COLORS['bg_secondary'],
                    fg=ModernTheme.COLORS['text_primary']).grid(
                row=row, column=col, sticky='w', padx=10, pady=5)
            
            value_label = tk.Label(info_frame, text="Loading...",
                                  bg=ModernTheme.COLORS['bg_secondary'],
                                  fg=ModernTheme.COLORS['accent'])
            value_label.grid(row=row, column=col+1, sticky='w', padx=10, pady=5)
            
            self.info_labels[key] = value_label
        
        # Alerts frame
        alerts_frame = ttk.LabelFrame(self, text="System Alerts",
                                     style='Modern.TFrame')
        alerts_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Alerts list
        self.alerts_tree = ttk.Treeview(alerts_frame,
                                       columns=('Time', 'Type', 'Message'),
                                       show='headings',
                                       style='Modern.Treeview')
        
        self.alerts_tree.heading('Time', text='Time')
        self.alerts_tree.heading('Type', text='Type')
        self.alerts_tree.heading('Message', text='Message')
        
        self.alerts_tree.column('Time', width=120)
        self.alerts_tree.column('Type', width=100)
        self.alerts_tree.column('Message', width=400)
        
        # Scrollbar for alerts
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient='vertical',
                                        command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_tree.pack(side='left', fill='both', expand=True)
        alerts_scrollbar.pack(side='right', fill='y')
    
    def update_system_info(self):
        """Update system information display"""
        if not self.monitoring:
            return
        
        # Get system metrics in background
        self.gui.run_in_background(
            self.gui.system_monitor.collect_metrics,
            self.on_metrics_collected
        )
        
        # Schedule next update
        self.after(5000, self.update_system_info)  # Update every 5 seconds
    
    def on_metrics_collected(self, metrics: Dict[str, Any], error: str = None):
        """Handle collected metrics"""
        if error or not metrics:
            return
        
        try:
            # Update CPU usage
            cpu_percent = metrics['cpu']['percent']
            self.info_labels['cpu_usage'].config(
                text=f"{cpu_percent:.1f}%",
                fg=ModernTheme.COLORS['error'] if cpu_percent > 80 else ModernTheme.COLORS['accent']
            )
            
            # Update memory usage
            memory_percent = metrics['memory']['percent']
            self.info_labels['memory_usage'].config(
                text=f"{memory_percent:.1f}%",
                fg=ModernTheme.COLORS['error'] if memory_percent > 85 else ModernTheme.COLORS['accent']
            )
            
            # Update disk usage (show worst disk)
            worst_disk = 0
            for mount, usage in metrics.get('disk', {}).items():
                if usage['percent'] > worst_disk:
                    worst_disk = usage['percent']
            
            self.info_labels['disk_usage'].config(
                text=f"{worst_disk:.1f}%",
                fg=ModernTheme.COLORS['error'] if worst_disk > 90 else ModernTheme.COLORS['accent']
            )
            
            # Update network I/O
            network = metrics.get('network', {})
            bytes_sent = network.get('bytes_sent', 0)
            bytes_recv = network.get('bytes_recv', 0)
            self.info_labels['network_io'].config(
                text=f"↑{self.format_bytes(bytes_sent)} ↓{self.format_bytes(bytes_recv)}"
            )
            
            # Update processes
            processes = metrics.get('processes', {})
            total = processes.get('total', 0)
            running = processes.get('running', 0)
            self.info_labels['processes'].config(
                text=f"{total} ({running} running)"
            )
            
            # Update uptime (simple calculation)
            import uptime
            uptime_seconds = uptime.uptime()
            uptime_str = self.format_uptime(uptime_seconds)
            self.info_labels['uptime'].config(text=uptime_str)
            
            # Update alerts
            self.update_alerts(self.gui.system_monitor.alerts)
            
        except Exception as e:
            logging.error(f"Error updating system info: {e}")
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"
    
    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def update_alerts(self, alerts: List[Dict[str, Any]]):
        """Update alerts display"""
        # Clear existing alerts
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        # Add recent alerts (last 20)
        recent_alerts = alerts[-20:] if len(alerts) > 20 else alerts
        
        for alert in reversed(recent_alerts):  # Show newest first
            timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
            
            self.alerts_tree.insert('', 'end', values=(
                timestamp,
                alert['type'],
                alert['message']
            ))

class NexusGUI(ThreadSafeGUI):
    """Main NexusController GUI application"""
    
    def __init__(self):
        # Initialize configuration
        self.config = NexusConfig()
        
        # Initialize core components
        self.security_manager = SecurityManager(self.config)
        self.ssh_manager = SSHManager(self.security_manager, self.config)
        self.network_discovery = NetworkDiscovery(self.config)
        self.system_monitor = SystemMonitor(self.config)
        self.backup_manager = BackupManager(self.config, self.security_manager)
        self.cloud_integration = CloudIntegration(self.config, self.security_manager)
        
        # Active connections
        self.active_ssh_client = None
        
        # Initialize GUI
        self.root = tk.Tk()
        super().__init__(self.root)
        
        self.setup_main_window()
        self.setup_ui()
        
        # Setup logging
        self.setup_logging()
        
        logging.info("NexusController GUI initialized")
    
    def setup_main_window(self):
        """Setup main window properties"""
        self.root.title("NexusController v2.0 - Infrastructure Management")
        self.root.geometry(self.config.window_geometry)
        self.root.configure(bg=ModernTheme.COLORS['bg_primary'])
        
        # Configure style
        ModernTheme.configure_ttk_style()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set minimum size
        self.root.minsize(800, 600)
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup main UI components"""
        
        # Title bar
        title_frame = tk.Frame(self.root, bg=ModernTheme.COLORS['bg_primary'], height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🌐 NexusController v2.0",
            font=('Arial', 24, 'bold'),
            fg=ModernTheme.COLORS['accent'],
            bg=ModernTheme.COLORS['bg_primary']
        )
        title_label.pack(side='left', padx=20, pady=15)
        
        subtitle = tk.Label(
            title_frame,
            text="Enterprise Infrastructure Management",
            font=('Arial', 12),
            fg=ModernTheme.COLORS['text_secondary'],
            bg=ModernTheme.COLORS['bg_primary']
        )
        subtitle.pack(side='left', padx=(0, 20), pady=20)
        
        # Main notebook
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create tabs
        self.network_tab = NetworkTab(self.notebook, self)
        self.system_tab = SystemTab(self.notebook, self)
        
        self.notebook.add(self.network_tab, text='🌐 Network')
        self.notebook.add(self.system_tab, text='📊 System')
        
        # Status bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        # Initial status
        self.status_bar.update_status("NexusController v2.0 Ready")
    
    def setup_logging(self):
        """Setup GUI logging"""
        # Create log handler that updates GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui
            
            def emit(self, record):
                msg = self.format(record)
                # Update status bar with log messages
                if record.levelno >= logging.WARNING:
                    status_type = 'error' if record.levelno >= logging.ERROR else 'warning'
                    self.gui.schedule_gui_update(
                        self.gui.status_bar.update_status,
                        record.getMessage(),
                        status_type
                    )
        
        # Add GUI handler to logger
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.WARNING)
        logging.getLogger().addHandler(gui_handler)
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Close SSH connections
            if hasattr(self, 'ssh_manager'):
                for conn_id in list(self.ssh_manager.connections.keys()):
                    self.ssh_manager.disconnect(conn_id)
            
            # Stop monitoring
            if hasattr(self, 'system_tab'):
                self.system_tab.monitoring = False
            
            # Shutdown background threads
            self.shutdown()
            
            # Save configuration
            # (Configuration is automatically saved by components)
            
            logging.info("NexusController GUI shutdown complete")
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
            self.on_closing()
        except Exception as e:
            logging.error(f"Application error: {e}")
            raise

def main():
    """Main entry point for GUI"""
    try:
        app = NexusGUI()
        app.run()
    except Exception as e:
        logging.error(f"Failed to start NexusController GUI: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())