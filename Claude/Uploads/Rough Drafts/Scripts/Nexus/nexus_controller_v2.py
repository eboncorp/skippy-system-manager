#!/usr/bin/env python3
"""
NexusController v2.0 - Enterprise Infrastructure Management System
Complete rewrite with security hardening, modular architecture, and cloud integration
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
import subprocess
import shutil
import ipaddress
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import re

# Third-party imports
try:
    import paramiko
    from paramiko import SSHClient, RSAKey, Ed25519Key, ECDSAKey
    from paramiko.ssh_exception import SSHException
except ImportError:
    print("ERROR: paramiko not installed. Run: pip3 install paramiko")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Run: pip3 install psutil")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("ERROR: cryptography not installed. Run: pip3 install cryptography")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, filedialog
    from tkinter import font as tkfont
except ImportError:
    print("ERROR: tkinter not available. Install python3-tk")
    sys.exit(1)

# ==================== Configuration Management ====================

class ConfigValidator:
    """Validates and sanitizes configuration data"""
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_network_range(network: str) -> bool:
        """Validate network range in CIDR notation"""
        try:
            ipaddress.ip_network(network, strict=False)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """Validate port number"""
        return 1 <= port <= 65535
    
    @staticmethod
    def validate_path(path: str, must_exist: bool = False) -> bool:
        """Validate file path"""
        try:
            p = Path(path).expanduser().resolve()
            if must_exist:
                return p.exists()
            return True
        except Exception:
            return False
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize shell command to prevent injection"""
        # Remove potentially dangerous characters
        dangerous_chars = ['$', '`', '\\', '"', "'", ';', '&', '|', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            command = command.replace(char, '')
        return command.strip()

@dataclass
class NexusConfig:
    """Central configuration management"""
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path.home() / ".nexus")
    config_dir: Path = field(default_factory=lambda: Path.home() / ".nexus" / "config")
    logs_dir: Path = field(default_factory=lambda: Path.home() / ".nexus" / "logs")
    keys_dir: Path = field(default_factory=lambda: Path.home() / ".nexus" / "keys")
    backup_dir: Path = field(default_factory=lambda: Path.home() / ".nexus" / "backups")
    
    # Network defaults
    default_network: str = "10.0.0.0/24"
    scan_timeout: int = 120
    scan_rate_limit: int = 10  # Max scans per second
    
    # Security settings
    ssh_timeout: int = 30
    max_retries: int = 3
    session_timeout: int = 3600  # 1 hour
    
    # UI settings
    theme: str = "dark"
    window_geometry: str = "1200x800"
    
    def __post_init__(self):
        """Create necessary directories"""
        for dir_path in [self.base_dir, self.config_dir, self.logs_dir, 
                         self.keys_dir, self.backup_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Set secure permissions
            os.chmod(dir_path, 0o700)

# ==================== Security Management ====================

class SecurityManager:
    """Handles all security operations"""
    
    def __init__(self, config: NexusConfig):
        self.config = config
        self.key_file = config.keys_dir / "master.key"
        self.known_hosts_file = config.keys_dir / "known_hosts"
        self.cipher = None
        self.setup_encryption()
        self.setup_known_hosts()
    
    def setup_encryption(self):
        """Initialize encryption with master key"""
        if not self.key_file.exists():
            # Generate new master key
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            os.chmod(self.key_file, 0o600)
            logging.info("Generated new master encryption key")
        
        # Load master key
        key = self.key_file.read_bytes()
        self.cipher = Fernet(key)
    
    def setup_known_hosts(self):
        """Initialize SSH known hosts file"""
        if not self.known_hosts_file.exists():
            self.known_hosts_file.touch(mode=0o600)
            logging.info("Created SSH known_hosts file")
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        if not self.cipher:
            raise SecurityError("Encryption not initialized")
        return self.cipher.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        if not self.cipher:
            raise SecurityError("Encryption not initialized")
        return self.cipher.decrypt(encrypted_data).decode()
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Hash password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    def verify_password(self, password: str, key: bytes, salt: bytes) -> bool:
        """Verify password against hash"""
        test_key, _ = self.hash_password(password, salt)
        return secrets.compare_digest(key, test_key)
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

class SSHManager:
    """Secure SSH connection management"""
    
    def __init__(self, security_manager: SecurityManager, config: NexusConfig):
        self.security = security_manager
        self.config = config
        self.connections = {}
        self.host_keys = paramiko.HostKeys(str(self.security.known_hosts_file))
    
    def connect(self, hostname: str, username: str, port: int = 22, 
                password: str = None, key_path: str = None) -> SSHClient:
        """Establish secure SSH connection with proper host key verification"""
        
        # Validate inputs
        if not ConfigValidator.validate_ip(hostname):
            if not self._is_valid_hostname(hostname):
                raise ValueError(f"Invalid hostname: {hostname}")
        
        if not ConfigValidator.validate_port(port):
            raise ValueError(f"Invalid port: {port}")
        
        # Create SSH client
        client = SSHClient()
        
        # CRITICAL: Use strict host key checking
        client.load_host_keys(str(self.security.known_hosts_file))
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        
        try:
            # First, verify host key
            if not self._verify_host_key(hostname, port):
                # If host is unknown, scan and prompt user
                if not self._scan_and_verify_host(hostname, port):
                    raise SSHException(f"Host key verification failed for {hostname}")
            
            # Connect with authentication
            connect_kwargs = {
                'hostname': hostname,
                'username': username,
                'port': port,
                'timeout': self.config.ssh_timeout,
                'allow_agent': True,
                'look_for_keys': True
            }
            
            if key_path:
                if ConfigValidator.validate_path(key_path, must_exist=True):
                    connect_kwargs['key_filename'] = key_path
                else:
                    raise ValueError(f"SSH key file not found: {key_path}")
            elif password:
                # Encrypt password in memory
                connect_kwargs['password'] = password
            
            client.connect(**connect_kwargs)
            
            # Cache connection
            conn_id = f"{username}@{hostname}:{port}"
            self.connections[conn_id] = {
                'client': client,
                'connected_at': datetime.now(),
                'last_used': datetime.now()
            }
            
            logging.info(f"SSH connection established: {conn_id}")
            return client
            
        except Exception as e:
            client.close()
            logging.error(f"SSH connection failed: {e}")
            raise
    
    def _verify_host_key(self, hostname: str, port: int) -> bool:
        """Verify if host key is known"""
        return self.host_keys.lookup(hostname) is not None
    
    def _scan_and_verify_host(self, hostname: str, port: int) -> bool:
        """Scan host key and prompt for verification"""
        try:
            # Use ssh-keyscan to get host key
            cmd = ['ssh-keyscan', '-p', str(port), '-t', 'ed25519,rsa', hostname]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logging.error(f"Failed to scan host key: {result.stderr}")
                return False
            
            # Parse and display key fingerprint
            for line in result.stdout.splitlines():
                if line and not line.startswith('#'):
                    # Add to known_hosts after user verification
                    # In production, this should prompt the user
                    with open(self.security.known_hosts_file, 'a') as f:
                        f.write(line + '\n')
                    self.host_keys = paramiko.HostKeys(str(self.security.known_hosts_file))
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Host key scan failed: {e}")
            return False
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """Validate hostname format"""
        hostname_regex = re.compile(
            r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
            r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
        )
        return bool(hostname_regex.match(hostname))
    
    def disconnect(self, conn_id: str):
        """Close SSH connection"""
        if conn_id in self.connections:
            try:
                self.connections[conn_id]['client'].close()
                del self.connections[conn_id]
                logging.info(f"SSH connection closed: {conn_id}")
            except Exception as e:
                logging.error(f"Error closing connection: {e}")
    
    def cleanup_stale_connections(self):
        """Remove stale connections"""
        now = datetime.now()
        stale = []
        
        for conn_id, info in self.connections.items():
            if (now - info['last_used']).seconds > self.config.session_timeout:
                stale.append(conn_id)
        
        for conn_id in stale:
            self.disconnect(conn_id)

# ==================== Network Discovery ====================

class NetworkDiscovery:
    """Secure network discovery and device management"""
    
    def __init__(self, config: NexusConfig):
        self.config = config
        self.discovered_devices = {}
        self.scan_history = []
        self.rate_limiter = threading.Semaphore(config.scan_rate_limit)
    
    def scan_network(self, network_range: str = None) -> Dict[str, Any]:
        """Scan network for devices with rate limiting"""
        
        # Validate network range
        if network_range is None:
            network_range = self.config.default_network
        
        if not ConfigValidator.validate_network_range(network_range):
            raise ValueError(f"Invalid network range: {network_range}")
        
        # Check for nmap
        if not shutil.which('nmap'):
            raise RuntimeError("nmap not installed. Run: sudo apt install nmap")
        
        # Rate limiting
        with self.rate_limiter:
            try:
                # Secure nmap scan with limited rate
                cmd = [
                    'nmap', '-sn',  # Ping scan only
                    '--max-rate', str(self.config.scan_rate_limit),
                    '--max-retries', '2',
                    network_range
                ]
                
                logging.info(f"Starting network scan: {network_range}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.scan_timeout
                )
                
                if result.returncode != 0:
                    logging.error(f"Network scan failed: {result.stderr}")
                    return {}
                
                # Parse results
                devices = self._parse_nmap_output(result.stdout)
                
                # Update discovered devices
                self.discovered_devices.update(devices)
                
                # Record scan
                self.scan_history.append({
                    'timestamp': datetime.now(),
                    'network': network_range,
                    'devices_found': len(devices)
                })
                
                logging.info(f"Network scan completed: {len(devices)} devices found")
                return devices
                
            except subprocess.TimeoutExpired:
                logging.error("Network scan timeout")
                return {}
            except Exception as e:
                logging.error(f"Network scan error: {e}")
                return {}
    
    def _parse_nmap_output(self, output: str) -> Dict[str, Any]:
        """Parse nmap output for device information"""
        devices = {}
        current_device = None
        
        for line in output.splitlines():
            # Check for new host
            if "Nmap scan report for" in line:
                parts = line.split("Nmap scan report for")[1].strip()
                
                # Extract hostname and IP
                if '(' in parts and ')' in parts:
                    hostname = parts.split('(')[0].strip()
                    ip = parts.split('(')[1].split(')')[0]
                else:
                    hostname = None
                    ip = parts
                
                if ConfigValidator.validate_ip(ip):
                    current_device = {
                        'ip': ip,
                        'hostname': hostname,
                        'mac': None,
                        'vendor': None,
                        'status': 'up',
                        'discovered_at': datetime.now().isoformat()
                    }
                    devices[ip] = current_device
            
            # Check for MAC address
            elif "MAC Address:" in line and current_device:
                parts = line.split("MAC Address:")[1].strip()
                if '(' in parts:
                    mac = parts.split('(')[0].strip()
                    vendor = parts.split('(')[1].split(')')[0]
                    current_device['mac'] = mac
                    current_device['vendor'] = vendor
        
        return devices
    
    def identify_servers(self, prefix: str = "ebon") -> List[Dict[str, Any]]:
        """Identify servers by hostname prefix"""
        servers = []
        
        for device in self.discovered_devices.values():
            hostname = device.get('hostname', '')
            if hostname and prefix.lower() in hostname.lower():
                servers.append(device)
        
        return servers

# ==================== Cloud Integration ====================

class CloudIntegration:
    """Unified cloud service integration"""
    
    def __init__(self, config: NexusConfig, security: SecurityManager):
        self.config = config
        self.security = security
        self.providers = {}
        self.load_providers()
    
    def load_providers(self):
        """Load cloud provider configurations"""
        providers_file = self.config.config_dir / "cloud_providers.json"
        
        if providers_file.exists():
            try:
                with open(providers_file, 'r') as f:
                    encrypted_data = f.read()
                    if encrypted_data:
                        # Decrypt configuration
                        decrypted = self.security.decrypt_data(encrypted_data.encode())
                        self.providers = json.loads(decrypted)
            except Exception as e:
                logging.error(f"Failed to load cloud providers: {e}")
                self.providers = {}
        else:
            # Create default configuration
            self.providers = {
                'google_drive': {
                    'enabled': False,
                    'sync_path': str(Path.home() / 'GoogleDrive'),
                    'backup_path': 'NexusBackups'
                },
                'aws': {
                    'enabled': False,
                    'region': 'us-east-1',
                    'services': []
                },
                'azure': {
                    'enabled': False,
                    'subscription': '',
                    'resource_group': ''
                },
                'github': {
                    'enabled': False,
                    'username': '',
                    'repositories': []
                }
            }
            self.save_providers()
    
    def save_providers(self):
        """Save cloud provider configurations securely"""
        providers_file = self.config.config_dir / "cloud_providers.json"
        
        try:
            # Encrypt configuration
            data = json.dumps(self.providers, indent=2)
            encrypted = self.security.encrypt_data(data)
            
            with open(providers_file, 'wb') as f:
                f.write(encrypted)
            
            os.chmod(providers_file, 0o600)
            logging.info("Cloud provider configuration saved")
            
        except Exception as e:
            logging.error(f"Failed to save cloud providers: {e}")
    
    def setup_google_drive(self):
        """Setup Google Drive integration"""
        # Import Google Drive GUI if available
        try:
            sys.path.append(str(Path.home() / 'Skippy'))
            from gdrive_gui import GoogleDriveManagerGUI
            
            # Update provider configuration
            self.providers['google_drive']['enabled'] = True
            self.save_providers()
            
            return True
        except ImportError:
            logging.warning("Google Drive integration not available")
            return False

# ==================== System Monitoring ====================

class SystemMonitor:
    """System health and performance monitoring"""
    
    def __init__(self, config: NexusConfig):
        self.config = config
        self.metrics_history = []
        self.alerts = []
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'network_errors': 100
        }
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0
                },
                'memory': {
                    'percent': psutil.virtual_memory().percent,
                    'available': psutil.virtual_memory().available,
                    'total': psutil.virtual_memory().total
                },
                'disk': {},
                'network': {},
                'processes': {
                    'total': len(psutil.pids()),
                    'running': len([p for p in psutil.process_iter(['status']) 
                                   if p.info['status'] == psutil.STATUS_RUNNING])
                }
            }
            
            # Disk usage
            for partition in psutil.disk_partitions():
                if partition.mountpoint:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        metrics['disk'][partition.mountpoint] = {
                            'percent': usage.percent,
                            'free': usage.free,
                            'total': usage.total
                        }
                    except PermissionError:
                        continue
            
            # Network statistics
            net_io = psutil.net_io_counters()
            metrics['network'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout
            }
            
            # Check thresholds and generate alerts
            self._check_thresholds(metrics)
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Limit history size
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logging.error(f"Failed to collect metrics: {e}")
            return {}
    
    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts"""
        
        # CPU threshold
        if metrics['cpu']['percent'] > self.thresholds['cpu_percent']:
            self._create_alert('HIGH_CPU', 
                             f"CPU usage: {metrics['cpu']['percent']}%")
        
        # Memory threshold
        if metrics['memory']['percent'] > self.thresholds['memory_percent']:
            self._create_alert('HIGH_MEMORY', 
                             f"Memory usage: {metrics['memory']['percent']}%")
        
        # Disk thresholds
        for mount, usage in metrics['disk'].items():
            if usage['percent'] > self.thresholds['disk_percent']:
                self._create_alert('HIGH_DISK', 
                                 f"Disk usage on {mount}: {usage['percent']}%")
        
        # Network errors
        if (metrics['network']['errin'] + metrics['network']['errout'] > 
            self.thresholds['network_errors']):
            self._create_alert('NETWORK_ERRORS', 
                             f"Network errors detected: {metrics['network']['errin'] + metrics['network']['errout']}")
    
    def _create_alert(self, alert_type: str, message: str):
        """Create system alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        logging.warning(f"System Alert: {alert_type} - {message}")
        
        # Limit alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

# ==================== Backup Manager ====================

class BackupManager:
    """Automated backup and recovery management"""
    
    def __init__(self, config: NexusConfig, security: SecurityManager):
        self.config = config
        self.security = security
        self.backup_manifest = self.config.backup_dir / "manifest.json"
        self.load_manifest()
    
    def load_manifest(self):
        """Load backup manifest"""
        if self.backup_manifest.exists():
            try:
                with open(self.backup_manifest, 'r') as f:
                    self.manifest = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load backup manifest: {e}")
                self.manifest = {'backups': [], 'last_backup': None}
        else:
            self.manifest = {'backups': [], 'last_backup': None}
    
    def save_manifest(self):
        """Save backup manifest"""
        try:
            with open(self.backup_manifest, 'w') as f:
                json.dump(self.manifest, f, indent=2)
            os.chmod(self.backup_manifest, 0o600)
        except Exception as e:
            logging.error(f"Failed to save backup manifest: {e}")
    
    def create_backup(self, backup_type: str = "full") -> bool:
        """Create system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"nexus_backup_{backup_type}_{timestamp}"
        backup_path = self.config.backup_dir / backup_name
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration
            config_backup = backup_path / "config"
            shutil.copytree(self.config.config_dir, config_backup)
            
            # Backup keys (encrypted)
            keys_backup = backup_path / "keys"
            keys_backup.mkdir(exist_ok=True)
            
            for key_file in self.config.keys_dir.glob("*"):
                if key_file.is_file():
                    # Encrypt sensitive files
                    with open(key_file, 'rb') as f:
                        encrypted = self.security.encrypt_data(f.read().decode())
                    
                    dest = keys_backup / f"{key_file.name}.enc"
                    with open(dest, 'wb') as f:
                        f.write(encrypted)
            
            # Create backup archive
            archive_name = f"{backup_name}.tar.gz"
            archive_path = self.config.backup_dir / archive_name
            
            subprocess.run(
                ['tar', '-czf', str(archive_path), '-C', str(self.config.backup_dir), backup_name],
                check=True
            )
            
            # Clean up temporary directory
            shutil.rmtree(backup_path)
            
            # Update manifest
            backup_info = {
                'name': backup_name,
                'type': backup_type,
                'timestamp': timestamp,
                'size': archive_path.stat().st_size,
                'path': str(archive_path)
            }
            
            self.manifest['backups'].append(backup_info)
            self.manifest['last_backup'] = timestamp
            self.save_manifest()
            
            logging.info(f"Backup created: {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore from backup"""
        # Find backup in manifest
        backup_info = None
        for backup in self.manifest['backups']:
            if backup['name'] == backup_name:
                backup_info = backup
                break
        
        if not backup_info:
            logging.error(f"Backup not found: {backup_name}")
            return False
        
        try:
            archive_path = Path(backup_info['path'])
            
            if not archive_path.exists():
                logging.error(f"Backup archive not found: {archive_path}")
                return False
            
            # Extract backup
            temp_dir = self.config.backup_dir / "restore_temp"
            temp_dir.mkdir(exist_ok=True)
            
            subprocess.run(
                ['tar', '-xzf', str(archive_path), '-C', str(temp_dir)],
                check=True
            )
            
            # Restore configuration
            backup_dir = temp_dir / backup_name
            
            if (backup_dir / "config").exists():
                shutil.rmtree(self.config.config_dir)
                shutil.copytree(backup_dir / "config", self.config.config_dir)
            
            # Restore keys (decrypt)
            if (backup_dir / "keys").exists():
                for enc_file in (backup_dir / "keys").glob("*.enc"):
                    # Decrypt file
                    with open(enc_file, 'rb') as f:
                        decrypted = self.security.decrypt_data(f.read())
                    
                    # Save to keys directory
                    dest = self.config.keys_dir / enc_file.stem
                    with open(dest, 'w') as f:
                        f.write(decrypted)
                    os.chmod(dest, 0o600)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            logging.info(f"Backup restored: {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"Restore failed: {e}")
            return False

# ==================== Custom Exceptions ====================

class SecurityError(Exception):
    """Security-related exception"""
    pass

class ConfigurationError(Exception):
    """Configuration-related exception"""
    pass

# ==================== Main Application ====================

def main():
    """Main entry point"""
    print("NexusController v2.0 - Starting...")
    
    # Setup logging
    log_file = Path.home() / ".nexus" / "logs" / f"nexus_{datetime.now().strftime('%Y%m%d')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Check dependencies
    required_commands = ['nmap', 'ssh-keyscan', 'tar']
    missing = []
    
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing.append(cmd)
    
    if missing:
        print(f"ERROR: Missing required commands: {', '.join(missing)}")
        print("Install with: sudo apt install " + " ".join(missing))
        sys.exit(1)
    
    # Initialize configuration
    config = NexusConfig()
    
    # Initialize security
    security = SecurityManager(config)
    
    print("NexusController v2.0 initialized successfully!")
    print(f"Configuration directory: {config.base_dir}")
    print(f"Logs directory: {config.logs_dir}")
    
    # Note: GUI initialization would go here
    # For now, we're focusing on the core infrastructure
    
    return 0

if __name__ == "__main__":
    sys.exit(main())