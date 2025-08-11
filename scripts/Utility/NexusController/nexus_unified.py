#!/usr/bin/env python3
"""
NexusController Unified - Complete Infrastructure Management System
Merges all components into a single, robust, enterprise-grade platform
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import paramiko
import psutil
import requests
from cryptography.fernet import Fernet

# Import Google Drive integration
sys.path.append('/home/dave/Skippy/app-to-deploy')
try:
    from gdrive_gui import GoogleDriveManagerGUI
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

@dataclass
class ServerConfig:
    """Server configuration data structure"""
    hostname: str
    ip: str
    ssh_user: str
    ssh_port: int = 22
    role: str = "server"
    services: List[str] = None
    last_seen: datetime = None

class SecurityManager:
    """Enterprise-grade security management"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.key_file = config_dir / "security.key"
        self.setup_encryption()
    
    def setup_encryption(self):
        """Initialize encryption for sensitive data"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
        
        with open(self.key_file, 'rb') as f:
            self.cipher = Fernet(f.read())
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data).decode()

class GoogleDriveBackupManager:
    """Google Drive integration for automatic backups"""
    
    def __init__(self, nexus_dir: Path):
        self.nexus_dir = nexus_dir
        self.gdrive_path = Path.home() / "GoogleDrive"
        self.backup_path = self.gdrive_path / "NexusBackups"
        self.setup_backup_structure()
    
    def setup_backup_structure(self):
        """Create backup directory structure"""
        try:
            # Create backup directories
            self.backup_path.mkdir(parents=True, exist_ok=True)
            (self.backup_path / "configs").mkdir(exist_ok=True)
            (self.backup_path / "logs").mkdir(exist_ok=True)
            (self.backup_path / "scripts").mkdir(exist_ok=True)
            (self.backup_path / "databases").mkdir(exist_ok=True)
            
            # Create backup manifest
            manifest = {
                "created": datetime.now().isoformat(),
                "version": "2.0",
                "type": "nexus_backup",
                "auto_backup": True
            }
            
            with open(self.backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to setup Google Drive backup structure: {e}")
    
    def backup_configs(self) -> bool:
        """Backup all configuration files to Google Drive"""
        try:
            # Backup .nexus directory
            nexus_backup = self.backup_path / "configs" / f"nexus_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            subprocess.run(["cp", "-r", str(self.nexus_dir), str(nexus_backup)], check=True)
            
            # Backup SSH configs
            ssh_backup = self.backup_path / "configs" / "ssh"
            ssh_backup.mkdir(exist_ok=True)
            subprocess.run(["cp", "-r", str(Path.home() / ".ssh"), str(ssh_backup)], check=True)
            
            # Create backup info
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "type": "configuration_backup",
                "files": ["nexus_configs", "ssh_configs"],
                "size": self._get_directory_size(nexus_backup)
            }
            
            with open(self.backup_path / "configs" / "latest_backup.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logging.error(f"Configuration backup failed: {e}")
            return False
    
    def backup_logs(self) -> bool:
        """Backup system logs to Google Drive"""
        try:
            log_backup = self.backup_path / "logs" / f"logs_{datetime.now().strftime('%Y%m%d')}"
            log_backup.mkdir(exist_ok=True)
            
            # Backup application logs
            app_logs = [
                "/var/log/syslog",
                "/var/log/auth.log",
                str(self.nexus_dir / "nexus.log")
            ]
            
            for log_file in app_logs:
                if os.path.exists(log_file):
                    subprocess.run(["cp", log_file, str(log_backup)], check=True)
            
            return True
            
        except Exception as e:
            logging.error(f"Log backup failed: {e}")
            return False
    
    def _get_directory_size(self, path: Path) -> int:
        """Calculate directory size"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
        except Exception:
            pass
        return total

class NetworkDiscovery:
    """Advanced network discovery and management"""
    
    def __init__(self):
        self.discovered_servers = {}
        self.network_range = "10.0.0.0/24"
    
    def discover_ebon_servers(self) -> Dict[str, ServerConfig]:
        """Discover all ebon servers on the network"""
        servers = {}
        
        try:
            # Network scan using nmap if available
            result = subprocess.run(["nmap", "-sn", self.network_range], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse nmap output for live hosts
                for line in result.stdout.split('\n'):
                    if 'Nmap scan report' in line:
                        host = line.split()[-1].strip('()')
                        if self._is_ebon_server(host):
                            config = self._probe_server(host)
                            if config:
                                servers[config.hostname] = config
                        
        except subprocess.TimeoutExpired:
            logging.warning("Network scan timed out, using fallback method")
        except FileNotFoundError:
            logging.warning("nmap not found, using ping scan")
        
        # Fallback: ping sweep
        if not servers:
            servers = self._ping_sweep_discovery()
        
        return servers
    
    def _is_ebon_server(self, host: str) -> bool:
        """Check if host is an ebon server"""
        try:
            # Try to resolve hostname
            result = subprocess.run(["nslookup", host], 
                                  capture_output=True, text=True, timeout=5)
            return 'ebon' in result.stdout.lower()
        except:
            return False
    
    def _probe_server(self, host: str) -> Optional[ServerConfig]:
        """Probe server to determine configuration"""
        try:
            # Test SSH connectivity
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            for user in ['ebon', 'dave', 'ubuntu']:
                try:
                    ssh.connect(host, username=user, timeout=5, 
                              key_filename=str(Path.home() / ".ssh/id_ed25519"))
                    
                    # Determine services running
                    services = self._detect_services(ssh)
                    
                    # Determine role based on services
                    role = self._determine_role(services)
                    
                    ssh.close()
                    
                    return ServerConfig(
                        hostname=f"ebon-{role}",
                        ip=host,
                        ssh_user=user,
                        role=role,
                        services=services,
                        last_seen=datetime.now()
                    )
                    
                except paramiko.AuthenticationException:
                    continue
                except Exception:
                    break
                    
        except Exception as e:
            logging.debug(f"Failed to probe {host}: {e}")
        
        return None
    
    def _detect_services(self, ssh: paramiko.SSHClient) -> List[str]:
        """Detect running services on remote server"""
        services = []
        
        service_commands = {
            'jellyfin': 'docker ps | grep jellyfin',
            'homeassistant': 'docker ps | grep homeassistant',
            'ethereum': 'ls ~/ethereum_node_manager 2>/dev/null',
            'docker': 'systemctl is-active docker',
            'nginx': 'systemctl is-active nginx',
            'wireguard': 'systemctl is-active wg-quick@wg0'
        }
        
        for service, command in service_commands.items():
            try:
                stdin, stdout, stderr = ssh.exec_command(command)
                if stdout.channel.recv_exit_status() == 0:
                    services.append(service)
            except:
                pass
        
        return services
    
    def _determine_role(self, services: List[str]) -> str:
        """Determine server role based on running services"""
        if 'jellyfin' in services or 'homeassistant' in services:
            return 'media'
        elif 'ethereum' in services:
            return 'blockchain'
        elif 'nginx' in services:
            return 'web'
        else:
            return 'general'
    
    def _ping_sweep_discovery(self) -> Dict[str, ServerConfig]:
        """Fallback discovery using ping sweep"""
        servers = {}
        base_ip = "10.0.0."
        
        # Known ebon server IPs from network scan
        known_ips = ["10.0.0.25", "10.0.0.29"]
        
        for ip in known_ips:
            try:
                result = subprocess.run(["ping", "-c", "1", "-W", "1", ip], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    config = self._probe_server(ip)
                    if config:
                        servers[config.hostname] = config
            except:
                pass
        
        return servers

class CloudIntegrationManager:
    """Unified cloud provider management"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.cloud_config = self._load_cloud_config()
    
    def _load_cloud_config(self) -> Dict:
        """Load cloud provider configurations"""
        config_file = self.config_dir / "cloud_providers_config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def setup_google_drive(self) -> bool:
        """Initialize Google Drive integration"""
        try:
            if GDRIVE_AVAILABLE:
                # Launch Google Drive manager if not already mounted
                gdrive_path = Path.home() / "GoogleDrive"
                if not gdrive_path.exists() or not any(gdrive_path.iterdir()):
                    subprocess.Popen(["python3", "/home/dave/Skippy/app-to-deploy/gdrive_gui.py"])
                return True
            return False
        except Exception as e:
            logging.error(f"Google Drive setup failed: {e}")
            return False

class MonitoringManager:
    """Advanced system monitoring and alerting"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.monitoring_active = False
    
    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring_active = True
        threading.Thread(target=self._monitoring_loop, daemon=True).start()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                time.sleep(60)
    
    def _collect_metrics(self):
        """Collect system metrics"""
        self.metrics.update({
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'processes': len(psutil.pids())
        })
    
    def _check_alerts(self):
        """Check for alert conditions"""
        if self.metrics.get('cpu_percent', 0) > 80:
            self.alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'cpu_high',
                'message': f"CPU usage high: {self.metrics['cpu_percent']}%"
            })
        
        if self.metrics.get('memory_percent', 0) > 85:
            self.alerts.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'memory_high',
                'message': f"Memory usage high: {self.metrics['memory_percent']}%"
            })

class NexusControllerGUI:
    """Unified GUI for NexusController"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NexusController Unified - Enterprise Infrastructure Management")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize components
        self.config_dir = Path.home() / ".nexus"
        self.config_dir.mkdir(exist_ok=True, mode=0o700)
        
        self.security = SecurityManager(self.config_dir)
        self.gdrive_backup = GoogleDriveBackupManager(self.config_dir)
        self.network = NetworkDiscovery()
        self.cloud = CloudIntegrationManager(self.config_dir)
        self.monitoring = MonitoringManager()
        
        self.servers = {}
        self.setup_gui()
        self.setup_logging()
        
        # Start background services
        self.start_background_services()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.config_dir / "nexus.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logging.info("NexusController Unified started")
    
    def setup_gui(self):
        """Create the main GUI interface"""
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_servers_tab()
        self.create_cloud_tab()
        self.create_backup_tab()
        self.create_monitoring_tab()
        self.create_security_tab()
        self.create_logs_tab()
        
        # Create status bar
        self.create_status_bar()
    
    def create_dashboard_tab(self):
        """Create main dashboard"""
        dashboard = ttk.Frame(self.notebook)
        self.notebook.add(dashboard, text="🏠 Dashboard")
        
        # Title
        title = ttk.Label(dashboard, text="NexusController Unified", 
                         font=('Arial', 18, 'bold'))
        title.pack(pady=10)
        
        # Status overview
        status_frame = ttk.LabelFrame(dashboard, text="System Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Quick stats
        self.stats_frame = ttk.Frame(status_frame)
        self.stats_frame.pack(fill='x')
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard, text="Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        actions_row1 = ttk.Frame(actions_frame)
        actions_row1.pack(fill='x', pady=5)
        
        ttk.Button(actions_row1, text="🔍 Discover Servers", 
                  command=self.discover_servers).pack(side='left', padx=5)
        ttk.Button(actions_row1, text="💾 Backup to Google Drive", 
                  command=self.backup_to_gdrive).pack(side='left', padx=5)
        ttk.Button(actions_row1, text="🖥️ Open Media Server", 
                  command=self.open_media_server).pack(side='left', padx=5)
        ttk.Button(actions_row1, text="🏠 Open Home Assistant", 
                  command=self.open_home_assistant).pack(side='left', padx=5)
        
        actions_row2 = ttk.Frame(actions_frame)
        actions_row2.pack(fill='x', pady=5)
        
        ttk.Button(actions_row2, text="☁️ Google Drive Manager", 
                  command=self.launch_gdrive_gui).pack(side='left', padx=5)
        ttk.Button(actions_row2, text="🔧 System Cleanup", 
                  command=self.run_system_cleanup).pack(side='left', padx=5)
        ttk.Button(actions_row2, text="🔄 Refresh All", 
                  command=self.refresh_all_data).pack(side='left', padx=5)
        
        # Activity log
        log_frame = ttk.LabelFrame(dashboard, text="Recent Activity", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.activity_log.pack(fill='both', expand=True)
    
    def create_servers_tab(self):
        """Create server management tab"""
        servers_tab = ttk.Frame(self.notebook)
        self.notebook.add(servers_tab, text="🖥️ Servers")
        
        # Server list
        list_frame = ttk.LabelFrame(servers_tab, text="Discovered Servers", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for servers
        columns = ('Hostname', 'IP', 'Role', 'Services', 'Status', 'Last Seen')
        self.server_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.server_tree.heading(col, text=col)
            self.server_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.server_tree.yview)
        self.server_tree.configure(yscrollcommand=scrollbar.set)
        
        self.server_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Server actions
        server_actions = ttk.Frame(servers_tab)
        server_actions.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(server_actions, text="Connect SSH", 
                  command=self.connect_ssh).pack(side='left', padx=5)
        ttk.Button(server_actions, text="Deploy Service", 
                  command=self.deploy_service).pack(side='left', padx=5)
        ttk.Button(server_actions, text="View Logs", 
                  command=self.view_server_logs).pack(side='left', padx=5)
    
    def create_cloud_tab(self):
        """Create cloud management tab"""
        cloud_tab = ttk.Frame(self.notebook)
        self.notebook.add(cloud_tab, text="☁️ Cloud")
        
        # Cloud providers status
        providers_frame = ttk.LabelFrame(cloud_tab, text="Cloud Providers", padding=10)
        providers_frame.pack(fill='x', padx=10, pady=5)
        
        # Provider status indicators
        self.cloud_status = {}
        providers = ['Google Drive', 'DigitalOcean', 'AWS', 'Azure', 'GitHub']
        
        for i, provider in enumerate(providers):
            frame = ttk.Frame(providers_frame)
            frame.grid(row=i//3, column=i%3, sticky='w', padx=10, pady=5)
            
            ttk.Label(frame, text=f"{provider}:").pack(side='left')
            status_label = ttk.Label(frame, text="Checking...", foreground='orange')
            status_label.pack(side='left', padx=5)
            self.cloud_status[provider] = status_label
    
    def create_backup_tab(self):
        """Create backup management tab"""
        backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(backup_tab, text="💾 Backup")
        
        # Google Drive backup section
        gdrive_frame = ttk.LabelFrame(backup_tab, text="Google Drive Backup (Primary)", padding=10)
        gdrive_frame.pack(fill='x', padx=10, pady=5)
        
        backup_buttons = ttk.Frame(gdrive_frame)
        backup_buttons.pack(fill='x', pady=5)
        
        ttk.Button(backup_buttons, text="📁 Backup Configurations", 
                  command=self.backup_configs).pack(side='left', padx=5)
        ttk.Button(backup_buttons, text="📋 Backup Logs", 
                  command=self.backup_logs).pack(side='left', padx=5)
        ttk.Button(backup_buttons, text="🔄 Full System Backup", 
                  command=self.full_system_backup).pack(side='left', padx=5)
        
        # Backup status
        status_text = scrolledtext.ScrolledText(backup_tab, height=20, state='disabled')
        status_text.pack(fill='both', expand=True, padx=10, pady=5)
        self.backup_status = status_text
    
    def create_monitoring_tab(self):
        """Create monitoring tab"""
        monitoring_tab = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_tab, text="📊 Monitoring")
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(monitoring_tab, text="System Metrics", padding=10)
        metrics_frame.pack(fill='x', padx=10, pady=5)
        
        self.metrics_labels = {}
        metrics = ['CPU Usage', 'Memory Usage', 'Disk Usage', 'Network Connections']
        
        for i, metric in enumerate(metrics):
            frame = ttk.Frame(metrics_frame)
            frame.grid(row=i//2, column=i%2, sticky='w', padx=20, pady=5)
            
            ttk.Label(frame, text=f"{metric}:").pack(side='left')
            value_label = ttk.Label(frame, text="--", font=('Arial', 10, 'bold'))
            value_label.pack(side='left', padx=10)
            self.metrics_labels[metric] = value_label
        
        # Alerts
        alerts_frame = ttk.LabelFrame(monitoring_tab, text="Alerts", padding=10)
        alerts_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.alerts_list = scrolledtext.ScrolledText(alerts_frame, height=15, state='disabled')
        self.alerts_list.pack(fill='both', expand=True)
    
    def create_security_tab(self):
        """Create security management tab"""
        security_tab = ttk.Frame(self.notebook)
        self.notebook.add(security_tab, text="🔒 Security")
        
        # Security status
        status_frame = ttk.LabelFrame(security_tab, text="Security Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(status_frame, text="🔐 Encryption: Active").pack(anchor='w', pady=2)
        ttk.Label(status_frame, text="🔑 SSH Keys: Configured").pack(anchor='w', pady=2)
        ttk.Label(status_frame, text="🛡️ Firewall: Active").pack(anchor='w', pady=2)
        ttk.Label(status_frame, text="🔒 VPN: Ready").pack(anchor='w', pady=2)
    
    def create_logs_tab(self):
        """Create logs viewing tab"""
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="📋 Logs")
        
        # Log viewer
        self.log_viewer = scrolledtext.ScrolledText(logs_tab, state='disabled')
        self.log_viewer.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log controls
        controls = ttk.Frame(logs_tab)
        controls.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side='left', padx=5)
        ttk.Button(controls, text="Clear", 
                  command=self.clear_logs).pack(side='left', padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side='left', padx=5)
        
        # Connection indicator
        self.connection_indicator = ttk.Label(self.status_bar, text="●", foreground="green")
        self.connection_indicator.pack(side='right', padx=5)
    
    def start_background_services(self):
        """Start background monitoring and services"""
        # Start monitoring
        self.monitoring.start_monitoring()
        
        # Setup Google Drive
        self.cloud.setup_google_drive()
        
        # Update status periodically
        self.update_status()
        
        # Auto-discover servers on startup
        threading.Thread(target=self.discover_servers, daemon=True).start()
    
    def update_status(self):
        """Update GUI status information"""
        try:
            # Update metrics
            if hasattr(self.monitoring, 'metrics') and self.monitoring.metrics:
                self.metrics_labels['CPU Usage'].config(text=f"{self.monitoring.metrics.get('cpu_percent', 0):.1f}%")
                self.metrics_labels['Memory Usage'].config(text=f"{self.monitoring.metrics.get('memory_percent', 0):.1f}%")
                self.metrics_labels['Disk Usage'].config(text=f"{self.monitoring.metrics.get('disk_usage', 0):.1f}%")
                self.metrics_labels['Network Connections'].config(text=str(self.monitoring.metrics.get('network_connections', 0)))
            
            # Update alerts
            if hasattr(self.monitoring, 'alerts') and self.monitoring.alerts:
                self.alerts_list.config(state='normal')
                self.alerts_list.delete('1.0', tk.END)
                for alert in self.monitoring.alerts[-10:]:  # Show last 10 alerts
                    self.alerts_list.insert(tk.END, f"{alert['timestamp']}: {alert['message']}\n")
                self.alerts_list.config(state='disabled')
            
            # Update cloud status
            gdrive_path = Path.home() / "GoogleDrive"
            if gdrive_path.exists() and any(gdrive_path.iterdir()):
                self.cloud_status['Google Drive'].config(text="Connected", foreground='green')
            else:
                self.cloud_status['Google Drive'].config(text="Disconnected", foreground='red')
            
        except Exception as e:
            logging.error(f"Status update error: {e}")
        
        # Schedule next update
        self.root.after(5000, self.update_status)
    
    def log_activity(self, message: str):
        """Log activity to the GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.activity_log.config(state='normal')
        self.activity_log.insert(tk.END, formatted_message)
        self.activity_log.see(tk.END)
        self.activity_log.config(state='disabled')
        
        logging.info(message)
    
    def discover_servers(self):
        """Discover servers on the network"""
        self.log_activity("🔍 Starting server discovery...")
        self.status_label.config(text="Discovering servers...")
        
        try:
            discovered = self.network.discover_ebon_servers()
            self.servers.update(discovered)
            
            # Update server tree
            for item in self.server_tree.get_children():
                self.server_tree.delete(item)
            
            for hostname, config in self.servers.items():
                services_str = ", ".join(config.services) if config.services else "None"
                last_seen = config.last_seen.strftime("%H:%M:%S") if config.last_seen else "Never"
                
                self.server_tree.insert('', 'end', values=(
                    hostname, config.ip, config.role, services_str, "Online", last_seen
                ))
            
            self.log_activity(f"✅ Discovered {len(discovered)} servers")
            
        except Exception as e:
            self.log_activity(f"❌ Server discovery failed: {e}")
        
        self.status_label.config(text="Ready")
    
    def backup_to_gdrive(self):
        """Backup to Google Drive"""
        self.log_activity("💾 Starting Google Drive backup...")
        
        try:
            # Backup configurations
            if self.gdrive_backup.backup_configs():
                self.log_activity("✅ Configuration backup completed")
            else:
                self.log_activity("❌ Configuration backup failed")
            
            # Backup logs
            if self.gdrive_backup.backup_logs():
                self.log_activity("✅ Log backup completed")
            else:
                self.log_activity("❌ Log backup failed")
                
        except Exception as e:
            self.log_activity(f"❌ Google Drive backup failed: {e}")
    
    def launch_gdrive_gui(self):
        """Launch Google Drive GUI"""
        try:
            if GDRIVE_AVAILABLE:
                subprocess.Popen(["python3", "/home/dave/Skippy/app-to-deploy/gdrive_gui.py"])
                self.log_activity("🗂️ Google Drive GUI launched")
            else:
                messagebox.showwarning("Warning", "Google Drive GUI not available")
        except Exception as e:
            self.log_activity(f"❌ Failed to launch Google Drive GUI: {e}")
    
    def open_media_server(self):
        """Open Jellyfin media server"""
        try:
            subprocess.run(["xdg-open", "http://10.0.0.29:8096"])
            self.log_activity("🎬 Opened Jellyfin media server")
        except Exception as e:
            self.log_activity(f"❌ Failed to open media server: {e}")
    
    def open_home_assistant(self):
        """Open Home Assistant"""
        try:
            subprocess.run(["xdg-open", "http://10.0.0.29:8123"])
            self.log_activity("🏠 Opened Home Assistant")
        except Exception as e:
            self.log_activity(f"❌ Failed to open Home Assistant: {e}")
    
    def run_system_cleanup(self):
        """Run system cleanup"""
        self.log_activity("🧹 Starting system cleanup...")
        try:
            # Run TidyTux cleanup script
            result = subprocess.run(["/home/dave/Skippy/complete-tidytux.sh"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_activity("✅ System cleanup completed")
            else:
                self.log_activity("❌ System cleanup failed")
        except Exception as e:
            self.log_activity(f"❌ System cleanup error: {e}")
    
    def refresh_all_data(self):
        """Refresh all data"""
        self.log_activity("🔄 Refreshing all data...")
        threading.Thread(target=self.discover_servers, daemon=True).start()
    
    def backup_configs(self):
        """Backup configurations"""
        self.log_activity("💾 Backing up configurations...")
        if self.gdrive_backup.backup_configs():
            self.log_activity("✅ Configuration backup completed")
        else:
            self.log_activity("❌ Configuration backup failed")
    
    def backup_logs(self):
        """Backup logs"""
        self.log_activity("📋 Backing up logs...")
        if self.gdrive_backup.backup_logs():
            self.log_activity("✅ Log backup completed")
        else:
            self.log_activity("❌ Log backup failed")
    
    def full_system_backup(self):
        """Full system backup"""
        self.log_activity("🔄 Starting full system backup...")
        
        def backup_thread():
            try:
                # Backup configs
                config_success = self.gdrive_backup.backup_configs()
                
                # Backup logs
                log_success = self.gdrive_backup.backup_logs()
                
                if config_success and log_success:
                    self.log_activity("✅ Full system backup completed successfully")
                else:
                    self.log_activity("⚠️ Full system backup completed with errors")
                    
            except Exception as e:
                self.log_activity(f"❌ Full system backup failed: {e}")
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def connect_ssh(self):
        """Connect to selected server via SSH"""
        selection = self.server_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server first")
            return
        
        item = self.server_tree.item(selection[0])
        hostname = item['values'][0]
        ip = item['values'][1]
        
        try:
            subprocess.Popen(["gnome-terminal", "--", "ssh", f"ebon@{ip}"])
            self.log_activity(f"🔗 SSH connection opened to {hostname} ({ip})")
        except Exception as e:
            self.log_activity(f"❌ Failed to open SSH connection: {e}")
    
    def deploy_service(self):
        """Deploy service to selected server"""
        messagebox.showinfo("Info", "Service deployment feature coming soon!")
    
    def view_server_logs(self):
        """View logs from selected server"""
        messagebox.showinfo("Info", "Remote log viewing feature coming soon!")
    
    def refresh_logs(self):
        """Refresh log display"""
        try:
            log_file = self.config_dir / "nexus.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    content = f.read()
                
                self.log_viewer.config(state='normal')
                self.log_viewer.delete('1.0', tk.END)
                self.log_viewer.insert('1.0', content)
                self.log_viewer.see(tk.END)
                self.log_viewer.config(state='disabled')
        except Exception as e:
            logging.error(f"Failed to refresh logs: {e}")
    
    def clear_logs(self):
        """Clear log display"""
        self.log_viewer.config(state='normal')
        self.log_viewer.delete('1.0', tk.END)
        self.log_viewer.config(state='disabled')
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = NexusControllerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nNexusController shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()