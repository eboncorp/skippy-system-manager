#!/usr/bin/env python3
"""
Ebonhawk Server Maintenance Agent
Comprehensive system monitoring and maintenance for ebonhawk server
Based on AI Maintenance Engine with ebonhawk-specific optimizations
"""

import os
import sys
import json
import time
import logging
import subprocess
import socket
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics

# System monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Install with: pip3 install psutil")

@dataclass
class ServerConfig:
    """Ebonhawk server configuration"""
    hostname: str = "ebonhawk"
    ip_address: str = "10.0.0.25"  # Local ebonhawk IP
    ssh_port: int = 22
    monitoring_interval: int = 300  # 5 minutes
    
    # Services to monitor
    services: List[str] = None
    
    # Paths (use home directory for non-root execution)
    log_path: str = str(Path.home() / ".ebonhawk-maintenance" / "logs")
    data_path: str = str(Path.home() / ".ebonhawk-maintenance" / "data")
    
    # System specs
    cpu_model: str = "Intel Celeron 6305 @ 1.80GHz"
    cpu_cores: int = 2
    ram_gb: int = 16
    disk_gb: int = 468
    
    def __post_init__(self):
        if self.services is None:
            self.services = [
                "ssh",
                "docker",
                "systemd-resolved",
                "NetworkManager",
                "cron",
                "snapd",
                "cups"  # printer service
            ]

@dataclass
class SystemStatus:
    """Current system status"""
    timestamp: datetime
    hostname: str
    uptime: float
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_stats: Dict[str, Any]
    service_status: Dict[str, bool]
    temperature: Optional[float]
    load_average: Tuple[float, float, float]

class EbonhawkMaintenanceAgent:
    """Main maintenance agent for ebonhawk server"""
    
    def __init__(self, config: ServerConfig = None):
        self.config = config or ServerConfig()
        self.running = False
        self.monitor_thread = None
        self.update_thread = None
        
        # Setup paths
        self.log_path = Path(self.config.log_path)
        self.data_path = Path(self.config.data_path)
        
        # Create directories
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Maintenance history
        self.maintenance_history = []
        self.alerts = []
        
        # Auto-update settings
        self.last_update_check = 0
        self.update_check_interval = 86400  # 24 hours
        self.last_system_update = 0
        self.system_update_interval = 86400  # 24 hours
        self.system_update_hour = 3  # 3 AM for system updates
        
        # Thresholds (adjusted for 2-core Celeron system)
        self.thresholds = {
            'cpu_percent': {'warning': 75, 'critical': 90},
            'memory_percent': {'warning': 80, 'critical': 90},
            'disk_percent': {'warning': 80, 'critical': 90},
            'temperature': {'warning': 65, 'critical': 75},  # Celeron runs cooler
            'load_average': {'warning': 2.0, 'critical': 4.0}  # 2 cores
        }
        
        self.logger.info(f"Ebonhawk Maintenance Agent initialized for {self.config.hostname}")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.log_path / f"maintenance_{datetime.now():%Y%m%d}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("EbonhawkMaintenanceAgent")
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        status = SystemStatus(
            timestamp=datetime.now(),
            hostname=socket.gethostname(),
            uptime=0,
            cpu_percent=0,
            memory_percent=0,
            disk_usage={},
            network_stats={},
            service_status={},
            temperature=None,
            load_average=(0, 0, 0)
        )
        
        if PSUTIL_AVAILABLE:
            # CPU and Memory
            status.cpu_percent = psutil.cpu_percent(interval=1)
            status.memory_percent = psutil.virtual_memory().percent
            
            # Uptime
            boot_time = psutil.boot_time()
            status.uptime = time.time() - boot_time
            
            # Disk usage
            for partition in psutil.disk_partitions():
                if partition.mountpoint in ['/', '/home', '/var', '/mnt']:
                    usage = psutil.disk_usage(partition.mountpoint)
                    status.disk_usage[partition.mountpoint] = usage.percent
            
            # Network stats
            net_io = psutil.net_io_counters()
            status.network_stats = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors': net_io.errin + net_io.errout
            }
            
            # Load average
            status.load_average = os.getloadavg()
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.label in ['Core 0', 'CPU', 'Package']:
                                status.temperature = entry.current
                                break
            except:
                pass
        
        # Service status
        for service in self.config.services:
            status.service_status[service] = self.check_service(service)
        
        return status
    
    def check_service(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def analyze_status(self, status: SystemStatus) -> List[Dict]:
        """Analyze system status and generate alerts"""
        alerts = []
        
        # CPU check
        if status.cpu_percent > self.thresholds['cpu_percent']['critical']:
            alerts.append({
                'level': 'CRITICAL',
                'component': 'CPU',
                'message': f"CPU usage critical: {status.cpu_percent:.1f}%",
                'value': status.cpu_percent
            })
        elif status.cpu_percent > self.thresholds['cpu_percent']['warning']:
            alerts.append({
                'level': 'WARNING',
                'component': 'CPU',
                'message': f"CPU usage high: {status.cpu_percent:.1f}%",
                'value': status.cpu_percent
            })
        
        # Memory check
        if status.memory_percent > self.thresholds['memory_percent']['critical']:
            alerts.append({
                'level': 'CRITICAL',
                'component': 'Memory',
                'message': f"Memory usage critical: {status.memory_percent:.1f}%",
                'value': status.memory_percent
            })
        elif status.memory_percent > self.thresholds['memory_percent']['warning']:
            alerts.append({
                'level': 'WARNING',
                'component': 'Memory',
                'message': f"Memory usage high: {status.memory_percent:.1f}%",
                'value': status.memory_percent
            })
        
        # Disk check
        for mount, usage in status.disk_usage.items():
            if usage > self.thresholds['disk_percent']['critical']:
                alerts.append({
                    'level': 'CRITICAL',
                    'component': 'Disk',
                    'message': f"Disk {mount} critical: {usage:.1f}%",
                    'value': usage
                })
            elif usage > self.thresholds['disk_percent']['warning']:
                alerts.append({
                    'level': 'WARNING',
                    'component': 'Disk',
                    'message': f"Disk {mount} filling up: {usage:.1f}%",
                    'value': usage
                })
        
        # Service check
        for service, is_running in status.service_status.items():
            if not is_running:
                alerts.append({
                    'level': 'WARNING',
                    'component': 'Service',
                    'message': f"Service {service} is not running",
                    'service': service
                })
        
        # Temperature check
        if status.temperature:
            if status.temperature > self.thresholds['temperature']['critical']:
                alerts.append({
                    'level': 'CRITICAL',
                    'component': 'Temperature',
                    'message': f"System temperature critical: {status.temperature}°C",
                    'value': status.temperature
                })
            elif status.temperature > self.thresholds['temperature']['warning']:
                alerts.append({
                    'level': 'WARNING',
                    'component': 'Temperature',
                    'message': f"System temperature high: {status.temperature}°C",
                    'value': status.temperature
                })
        
        # Load average check
        if status.load_average[0] > self.thresholds['load_average']['critical']:
            alerts.append({
                'level': 'CRITICAL',
                'component': 'Load',
                'message': f"System load critical: {status.load_average[0]:.2f}",
                'value': status.load_average[0]
            })
        elif status.load_average[0] > self.thresholds['load_average']['warning']:
            alerts.append({
                'level': 'WARNING',
                'component': 'Load',
                'message': f"System load high: {status.load_average[0]:.2f}",
                'value': status.load_average[0]
            })
        
        return alerts
    
    def perform_maintenance(self, alerts: List[Dict]):
        """Perform maintenance based on alerts"""
        maintenance_actions = []
        
        for alert in alerts:
            action = None
            
            # Auto-remediation for specific issues
            if alert['component'] == 'Service' and alert.get('service'):
                # Try to restart failed services
                service = alert['service']
                if self.restart_service(service):
                    action = f"Restarted service: {service}"
                else:
                    action = f"Failed to restart service: {service}"
            
            elif alert['component'] == 'Disk' and alert['level'] == 'WARNING':
                # Clean up disk space
                cleaned = self.cleanup_disk()
                if cleaned > 0:
                    action = f"Cleaned {cleaned / (1024**3):.2f} GB disk space"
            
            elif alert['component'] == 'Memory' and alert['level'] == 'WARNING':
                # Clear caches
                if self.clear_caches():
                    action = "Cleared system caches"
            
            if action:
                maintenance_actions.append({
                    'timestamp': datetime.now(),
                    'alert': alert,
                    'action': action
                })
                self.logger.info(f"Maintenance action: {action}")
        
        return maintenance_actions
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            subprocess.run(
                ['sudo', 'systemctl', 'restart', service_name],
                check=True,
                timeout=30
            )
            time.sleep(2)
            return self.check_service(service_name)
        except:
            return False
    
    def cleanup_disk(self) -> int:
        """Clean up disk space"""
        cleaned = 0
        
        # Clean apt cache
        try:
            result = subprocess.run(
                ['sudo', 'apt-get', 'clean'],
                capture_output=True,
                timeout=60
            )
            if result.returncode == 0:
                cleaned += 1024 * 1024 * 100  # Estimate
        except:
            pass
        
        # Clean old logs
        try:
            subprocess.run(
                ['sudo', 'journalctl', '--vacuum-time=7d'],
                capture_output=True,
                timeout=30
            )
            cleaned += 1024 * 1024 * 50  # Estimate
        except:
            pass
        
        # Clean tmp files older than 7 days
        try:
            subprocess.run(
                ['find', '/tmp', '-type', 'f', '-mtime', '+7', '-delete'],
                capture_output=True,
                timeout=30
            )
            cleaned += 1024 * 1024 * 20  # Estimate
        except:
            pass
        
        return cleaned
    
    def clear_caches(self) -> bool:
        """Clear system caches"""
        try:
            # Clear PageCache, dentries and inodes
            subprocess.run(
                ['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'],
                check=True,
                timeout=10
            )
            return True
        except:
            return False
    
    def check_for_updates(self):
        """Check for agent updates"""
        try:
            # Run the updater script
            updater_path = Path.home() / "Scripts" / "ebonhawk_agent_updater.py"
            if updater_path.exists():
                result = subprocess.run(
                    ['python3', str(updater_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if "Update available" in result.stdout:
                    self.logger.info("Agent update available and installed")
                    # The updater will restart the service if needed
        except Exception as e:
            self.logger.debug(f"Update check failed: {e}")
    
    def perform_system_updates(self) -> Dict:
        """Perform automatic system updates"""
        update_results = {
            'timestamp': datetime.now(),
            'apt_updates': 0,
            'snap_updates': 0,
            'security_updates': 0,
            'errors': []
        }
        
        try:
            # Update package lists
            self.logger.info("Checking for system updates...")
            subprocess.run(
                ['sudo', 'apt-get', 'update'],
                capture_output=True,
                timeout=300,
                check=True
            )
            
            # Check for security updates
            result = subprocess.run(
                ['apt', 'list', '--upgradable'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if 'security' in result.stdout.lower():
                update_results['security_updates'] = result.stdout.lower().count('security')
                
                # Apply security updates automatically
                self.logger.info("Installing security updates...")
                subprocess.run(
                    ['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'upgrade', '-y', 
                     '-o', 'Dpkg::Options::=--force-confdef',
                     '-o', 'Dpkg::Options::=--force-confold'],
                    capture_output=True,
                    timeout=600,
                    shell=True
                )
                update_results['apt_updates'] = update_results['security_updates']
            
            # Clean up
            subprocess.run(
                ['sudo', 'apt-get', 'autoremove', '-y'],
                capture_output=True,
                timeout=300
            )
            subprocess.run(
                ['sudo', 'apt-get', 'autoclean'],
                capture_output=True,
                timeout=300
            )
            
            # Update snap packages
            try:
                result = subprocess.run(
                    ['sudo', 'snap', 'refresh'],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if 'refreshed' in result.stdout:
                    # Count refreshed snaps
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'refreshed' in line:
                            update_results['snap_updates'] += 1
            except:
                pass  # Snap might not be installed
            
            # Log results
            if update_results['apt_updates'] > 0 or update_results['snap_updates'] > 0:
                self.logger.info(f"System updates installed: {update_results['apt_updates']} apt, {update_results['snap_updates']} snap")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"System update failed: {e}"
            self.logger.error(error_msg)
            update_results['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during system update: {e}"
            self.logger.error(error_msg)
            update_results['errors'].append(error_msg)
        
        return update_results
    
    def check_and_install_kernel_updates(self) -> bool:
        """Check and install kernel updates if available"""
        try:
            # Check current kernel
            current_kernel = subprocess.check_output(['uname', '-r'], text=True).strip()
            
            # Check for kernel updates
            result = subprocess.run(
                ['apt', 'list', '--upgradable', 'linux-image-*'],
                capture_output=True,
                text=True
            )
            
            if 'linux-image' in result.stdout and 'upgradable' in result.stdout:
                self.logger.info("Kernel update available")
                
                # Install kernel updates
                subprocess.run(
                    ['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '-y',
                     'linux-image-generic', 'linux-headers-generic'],
                    capture_output=True,
                    timeout=900,
                    shell=True
                )
                
                # Schedule reboot if kernel was updated
                new_kernel = subprocess.check_output(['uname', '-r'], text=True).strip()
                if new_kernel != current_kernel:
                    self.schedule_reboot()
                    return True
            
        except Exception as e:
            self.logger.error(f"Kernel update check failed: {e}")
        
        return False
    
    def schedule_reboot(self):
        """Schedule a system reboot during maintenance window"""
        try:
            # Schedule reboot at 3 AM
            subprocess.run(
                ['sudo', 'shutdown', '-r', '03:00', 'System reboot scheduled for kernel update'],
                check=True
            )
            self.logger.info("System reboot scheduled for 3:00 AM")
            
            # Send notification
            subprocess.run(
                ['notify-send', 'Ebonhawk Maintenance', 
                 'System reboot scheduled for 3:00 AM for kernel update'],
                capture_output=True
            )
        except Exception as e:
            self.logger.error(f"Failed to schedule reboot: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                # Get system status
                status = self.get_system_status()
                
                # Analyze status
                alerts = self.analyze_status(status)
                
                # Log alerts
                for alert in alerts:
                    self.logger.warning(f"{alert['level']}: {alert['message']}")
                
                # Perform maintenance if needed
                if alerts:
                    maintenance_actions = self.perform_maintenance(alerts)
                    self.maintenance_history.extend(maintenance_actions)
                
                # Save status to file
                self.save_status(status, alerts)
                
                # Check for updates periodically
                current_time = time.time()
                current_hour = datetime.now().hour
                
                # Check for agent updates
                if current_time - self.last_update_check > self.update_check_interval:
                    self.check_for_updates()
                    self.last_update_check = current_time
                
                # Perform system updates at scheduled hour
                if (current_time - self.last_system_update > self.system_update_interval and 
                    current_hour == self.system_update_hour):
                    self.logger.info("Starting scheduled system updates...")
                    update_results = self.perform_system_updates()
                    self.last_system_update = current_time
                    
                    # Check for kernel updates
                    self.check_and_install_kernel_updates()
                
                # Sleep until next check
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def save_status(self, status: SystemStatus, alerts: List[Dict]):
        """Save status and alerts to file"""
        data = {
            'timestamp': status.timestamp.isoformat(),
            'hostname': status.hostname,
            'uptime_hours': status.uptime / 3600,
            'cpu_percent': status.cpu_percent,
            'memory_percent': status.memory_percent,
            'disk_usage': status.disk_usage,
            'network_stats': status.network_stats,
            'service_status': status.service_status,
            'temperature': status.temperature,
            'load_average': status.load_average,
            'alerts': alerts
        }
        
        # Save to daily log file
        log_file = self.data_path / f"status_{datetime.now():%Y%m%d}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def start(self):
        """Start the maintenance agent"""
        if self.running:
            self.logger.warning("Agent already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("Ebonhawk Maintenance Agent started")
    
    def stop(self):
        """Stop the maintenance agent"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("Ebonhawk Maintenance Agent stopped")
    
    def get_summary(self) -> Dict:
        """Get summary of current status and recent maintenance"""
        status = self.get_system_status()
        
        return {
            'hostname': self.config.hostname,
            'status': {
                'cpu': f"{status.cpu_percent:.1f}%",
                'memory': f"{status.memory_percent:.1f}%",
                'disk': status.disk_usage,
                'uptime': f"{status.uptime / 3600:.1f} hours",
                'services': status.service_status
            },
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'maintenance_history': self.maintenance_history[-10:] if self.maintenance_history else []
        }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ebonhawk Server Maintenance Agent')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    # Load config if provided
    config = ServerConfig()
    if args.config:
        with open(args.config) as f:
            config_data = json.load(f)
            config = ServerConfig(**config_data)
    
    # Create agent
    agent = EbonhawkMaintenanceAgent(config)
    
    if args.status:
        # Show current status
        summary = agent.get_summary()
        print(json.dumps(summary, indent=2, default=str))
    
    elif args.daemon:
        # Run as daemon
        print(f"Starting Ebonhawk Maintenance Agent for {config.hostname}...")
        agent.start()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping agent...")
            agent.stop()
    
    else:
        # Run once
        status = agent.get_system_status()
        alerts = agent.analyze_status(status)
        
        print(f"System Status for {config.hostname}:")
        print(f"  CPU: {status.cpu_percent:.1f}%")
        print(f"  Memory: {status.memory_percent:.1f}%")
        print(f"  Disk Usage: {status.disk_usage}")
        print(f"  Load: {status.load_average}")
        
        if alerts:
            print("\nAlerts:")
            for alert in alerts:
                print(f"  [{alert['level']}] {alert['message']}")
        else:
            print("\nNo alerts - system healthy")

if __name__ == "__main__":
    main()