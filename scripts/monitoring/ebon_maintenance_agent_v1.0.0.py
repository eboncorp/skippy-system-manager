#!/usr/bin/env python3
"""
Ebon Media Server Maintenance Agent
Optimized for HP Z4 G4 media server with Docker containers and high load management
Based on ebonhawk agent with ebon-specific optimizations
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
import signal

# System monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Install with: pip3 install psutil")

@dataclass
class EbonServerConfig:
    """Ebon server configuration"""
    hostname: str = "ebon"
    ip_address: str = "10.0.0.29"
    ssh_port: int = 22
    monitoring_interval: int = 60  # 1 minute - more frequent due to issues
    
    # Services to monitor
    services: List[str] = None
    
    # Docker containers to monitor
    docker_containers: List[str] = None
    
    # Paths
    log_path: str = "/var/log/ebon-maintenance"
    data_path: str = "/var/lib/ebon-maintenance"
    
    # System specs - HP Z4 G4
    cpu_model: str = "Intel Xeon W-2125 @ 4.00GHz"
    cpu_cores: int = 4
    cpu_threads: int = 8
    ram_gb: int = 32
    disk_gb: int = 98  # Root partition
    media_disk_tb: float = 1.8  # Media partition
    
    # Thresholds adjusted for server
    cpu_threshold: float = 85.0
    memory_threshold: float = 85.0
    disk_threshold: float = 85.0  # Critical for root partition
    load_threshold: float = 6.0  # For 8 threads
    process_cpu_threshold: float = 90.0  # Single process limit
    
    def __post_init__(self):
        if self.services is None:
            self.services = [
                "ssh",
                "docker",
                "containerd",
                # Note: jellyfin runs in Docker
            ]
        
        if self.docker_containers is None:
            self.docker_containers = [
                "jellyfin",
                "homeassistant-fixed",
                "nexuscontroller-media-fixed",
                "nodered",
                "mosquitto"
            ]

@dataclass
class ProcessIssue:
    """Problematic process information"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    cmdline: str
    action_taken: str

class EbonMaintenanceAgent:
    """Main maintenance agent for ebon media server"""
    
    def __init__(self, config: EbonServerConfig = None):
        self.config = config or EbonServerConfig()
        self.hostname = socket.gethostname()
        self.running = False
        
        # Setup paths
        self.setup_paths()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize state
        self.state = self.load_state()
        
        # Process blacklist - known problematic processes
        self.process_blacklist = [
            'noip2',  # Known to run away on this server
        ]
        
        # Cleanup tracking
        self.last_cleanup = None
        self.last_docker_prune = None
        
        self.logger.info(f"Ebon Maintenance Agent initialized for {self.hostname}")
        
    def setup_paths(self):
        """Create necessary directories"""
        for path in [self.config.log_path, self.config.data_path]:
            Path(path).mkdir(parents=True, exist_ok=True)
            
    def setup_logging(self):
        """Configure logging"""
        log_file = Path(self.config.log_path) / "ebon-maintenance.log"
        
        # Rotate log if too large
        if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
            log_file.rename(log_file.with_suffix('.log.old'))
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EbonMaintenanceAgent')
        
    def load_state(self) -> dict:
        """Load persistent state"""
        state_file = Path(self.config.data_path) / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
        
        return {
            'alerts': [],
            'maintenance_history': [],
            'process_kills': [],
            'last_cleanup': None,
            'last_docker_prune': None,
            'disk_cleanups': 0,
            'process_kills_count': 0
        }
        
    def save_state(self):
        """Save persistent state"""
        state_file = Path(self.config.data_path) / "state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            
    def check_runaway_processes(self) -> List[ProcessIssue]:
        """Check and handle runaway processes"""
        issues = []
        
        if not PSUTIL_AVAILABLE:
            return issues
            
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
                try:
                    # Get CPU usage with interval for accuracy
                    cpu_percent = proc.cpu_percent(interval=0.5)
                    
                    if cpu_percent > self.config.process_cpu_threshold:
                        proc_info = proc.info
                        proc_name = proc_info['name']
                        cmdline = ' '.join(proc_info.get('cmdline', [])[:5]) if proc_info.get('cmdline') else proc_name
                        
                        issue = ProcessIssue(
                            pid=proc_info['pid'],
                            name=proc_name,
                            cpu_percent=cpu_percent,
                            memory_percent=proc_info.get('memory_percent', 0),
                            cmdline=cmdline,
                            action_taken='none'
                        )
                        
                        # Kill if in blacklist
                        if any(blacklisted in proc_name.lower() for blacklisted in self.process_blacklist):
                            self.logger.warning(f"Killing runaway {proc_name} (PID: {proc_info['pid']}, CPU: {cpu_percent:.1f}%)")
                            try:
                                proc.terminate()
                                time.sleep(2)
                                if proc.is_running():
                                    proc.kill()
                                issue.action_taken = 'killed'
                                self.record_process_kill(issue)
                            except Exception as e:
                                # Try with sudo
                                subprocess.run(['sudo', 'kill', '-9', str(proc_info['pid'])], capture_output=True)
                                issue.action_taken = 'force_killed'
                                self.record_process_kill(issue)
                        else:
                            self.logger.warning(f"High CPU process: {cmdline} (CPU: {cpu_percent:.1f}%)")
                            issue.action_taken = 'monitored'
                            
                        issues.append(issue)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking processes: {e}")
            
        return issues
        
    def record_process_kill(self, issue: ProcessIssue):
        """Record a process kill action"""
        self.state['process_kills'].append({
            'timestamp': datetime.now().isoformat(),
            'pid': issue.pid,
            'name': issue.name,
            'cpu_percent': issue.cpu_percent,
            'action': issue.action_taken
        })
        self.state['process_kills_count'] += 1
        # Keep only last 100 kills
        self.state['process_kills'] = self.state['process_kills'][-100:]
        self.save_state()
        self.add_maintenance_action(f"Killed process: {issue.name} (PID: {issue.pid}, CPU: {issue.cpu_percent:.1f}%)")
        
    def check_disk_usage(self) -> Dict[str, float]:
        """Check disk usage and clean if necessary"""
        disk_usage = {}
        
        if not PSUTIL_AVAILABLE:
            return disk_usage
            
        for partition in psutil.disk_partitions():
            if partition.mountpoint in ['/', '/mnt/media']:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = usage.percent
                
                # Critical cleanup for root partition
                if partition.mountpoint == '/' and usage.percent > self.config.disk_threshold:
                    self.logger.warning(f"Root disk critical: {usage.percent:.1f}% used")
                    self.emergency_disk_cleanup()
                    
        return disk_usage
        
    def emergency_disk_cleanup(self):
        """Emergency disk cleanup when space is critical"""
        self.logger.info("Starting emergency disk cleanup...")
        
        cleanup_commands = [
            # Clean package cache
            ['sudo', 'apt-get', 'clean'],
            ['sudo', 'apt-get', 'autoremove', '-y'],
            
            # Clean journal logs older than 3 days
            ['sudo', 'journalctl', '--vacuum-time=3d'],
            
            # Clean old kernels
            ['sudo', 'apt-get', 'autoremove', '--purge', '-y'],
            
            # Clean tmp
            ['sudo', 'find', '/tmp', '-type', 'f', '-atime', '+1', '-delete'],
            ['sudo', 'find', '/var/tmp', '-type', 'f', '-atime', '+1', '-delete'],
            
            # Clean old logs
            ['sudo', 'find', '/var/log', '-name', '*.gz', '-delete'],
            ['sudo', 'find', '/var/log', '-name', '*.1', '-delete'],
            ['sudo', 'find', '/var/log', '-name', '*.old', '-delete'],
        ]
        
        for cmd in cleanup_commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
            except Exception as e:
                self.logger.error(f"Cleanup command failed: {' '.join(cmd)}: {e}")
                
        # Docker cleanup if available
        if self.is_service_running('docker'):
            self.cleanup_docker()
            
        self.state['disk_cleanups'] += 1
        self.state['last_cleanup'] = datetime.now().isoformat()
        self.save_state()
        self.add_maintenance_action("Performed emergency disk cleanup")
        
    def cleanup_docker(self):
        """Clean up Docker resources"""
        self.logger.info("Cleaning Docker resources...")
        
        docker_commands = [
            ['sudo', 'docker', 'container', 'prune', '-f'],
            ['sudo', 'docker', 'image', 'prune', '-a', '-f'],
            ['sudo', 'docker', 'volume', 'prune', '-f'],
            ['sudo', 'docker', 'network', 'prune', '-f'],
            ['sudo', 'docker', 'system', 'prune', '-f'],
        ]
        
        for cmd in docker_commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
            except Exception as e:
                self.logger.error(f"Docker cleanup failed: {' '.join(cmd)}: {e}")
                
        self.state['last_docker_prune'] = datetime.now().isoformat()
        self.save_state()
        
    def check_docker_containers(self) -> Dict[str, str]:
        """Monitor Docker containers"""
        container_status = {}
        
        try:
            result = subprocess.run(
                ['sudo', 'docker', 'ps', '-a', '--format', '{{.Names}}:{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )
            
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    name, status = line.split(':', 1)
                    if name in self.config.docker_containers:
                        container_status[name] = status
                        
                        # Restart if not running
                        if 'Exited' in status or 'Dead' in status:
                            self.logger.warning(f"Container {name} is down: {status}")
                            self.restart_docker_container(name)
                            
        except Exception as e:
            self.logger.error(f"Failed to check Docker containers: {e}")
            
        return container_status
        
    def restart_docker_container(self, container: str):
        """Restart a Docker container"""
        try:
            subprocess.run(['sudo', 'docker', 'restart', container], capture_output=True, timeout=30)
            self.logger.info(f"Restarted Docker container: {container}")
            self.add_maintenance_action(f"Restarted Docker container: {container}")
        except Exception as e:
            self.logger.error(f"Failed to restart container {container}: {e}")
            
    def check_services(self) -> Dict[str, bool]:
        """Check critical services"""
        service_status = {}
        
        for service in self.config.services:
            status = self.is_service_running(service)
            service_status[service] = status
            
            if not status:
                self.logger.warning(f"Service {service} is not running")
                self.restart_service(service)
                
        return service_status
        
    def is_service_running(self, service: str) -> bool:
        """Check if a service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() == 'active'
        except:
            return False
            
    def restart_service(self, service: str):
        """Restart a service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', service], capture_output=True, timeout=30)
            self.logger.info(f"Restarted service: {service}")
            self.add_maintenance_action(f"Restarted service: {service}")
        except Exception as e:
            self.logger.error(f"Failed to restart service {service}: {e}")
            
    def add_maintenance_action(self, action: str):
        """Record a maintenance action"""
        self.state['maintenance_history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': action
        })
        # Keep only last 200 actions
        self.state['maintenance_history'] = self.state['maintenance_history'][-200:]
        self.save_state()
        
    def check_media_services(self):
        """Check media-specific services"""
        # Check Jellyfin health
        try:
            result = subprocess.run(
                ['curl', '-s', 'http://localhost:8096/health'],
                capture_output=True, text=True, timeout=5
            )
            if 'Healthy' not in result.stdout:
                self.logger.warning("Jellyfin health check failed")
                self.restart_docker_container('jellyfin')
        except:
            pass
            
        # Check media mount
        if not os.path.exists('/mnt/media'):
            self.logger.error("Media mount point not found!")
        else:
            # Check media disk usage
            usage = psutil.disk_usage('/mnt/media')
            if usage.percent > 90:
                self.logger.warning(f"Media disk usage high: {usage.percent:.1f}%")
                
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            'hostname': self.hostname,
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': 0,
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_usage': {},
            'load_average': (0, 0, 0),
            'services': {},
            'containers': {},
            'process_issues': []
        }
        
        if PSUTIL_AVAILABLE:
            # CPU and Memory
            status['cpu_percent'] = psutil.cpu_percent(interval=1)
            status['memory_percent'] = psutil.virtual_memory().percent
            
            # Uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            status['uptime_hours'] = uptime.total_seconds() / 3600
            
            # Load average
            status['load_average'] = os.getloadavg()
            
            # Disk usage
            status['disk_usage'] = self.check_disk_usage()
            
        # Services
        status['services'] = self.check_services()
        
        # Docker containers
        status['containers'] = self.check_docker_containers()
        
        # Process issues
        issues = self.check_runaway_processes()
        status['process_issues'] = [asdict(issue) for issue in issues]
        
        return status
        
    def run_maintenance_cycle(self):
        """Run a complete maintenance cycle"""
        self.logger.info("Starting maintenance cycle...")
        
        try:
            # Get system status
            status = self.get_system_status()
            
            # Check media services
            self.check_media_services()
            
            # Log status
            self.logger.info(f"System Status - CPU: {status['cpu_percent']:.1f}%, "
                           f"Memory: {status['memory_percent']:.1f}%, "
                           f"Load: {status['load_average'][0]:.2f}")
            
            # Check for high load
            if status['load_average'][0] > self.config.load_threshold:
                self.logger.warning(f"High system load: {status['load_average'][0]:.2f}")
                
            # Periodic cleanups
            if self.should_run_cleanup():
                self.emergency_disk_cleanup()
                
            if self.should_run_docker_prune():
                self.cleanup_docker()
                
        except Exception as e:
            self.logger.error(f"Maintenance cycle error: {e}")
            
    def should_run_cleanup(self) -> bool:
        """Check if cleanup should run"""
        if not self.state.get('last_cleanup'):
            return True
            
        last_cleanup = datetime.fromisoformat(self.state['last_cleanup'])
        return datetime.now() - last_cleanup > timedelta(days=1)
        
    def should_run_docker_prune(self) -> bool:
        """Check if Docker prune should run"""
        if not self.state.get('last_docker_prune'):
            return True
            
        last_prune = datetime.fromisoformat(self.state['last_docker_prune'])
        return datetime.now() - last_prune > timedelta(days=3)
        
    def run(self):
        """Main monitoring loop"""
        self.running = True
        self.logger.info("Starting monitoring loop")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        while self.running:
            try:
                self.run_maintenance_cycle()
                time.sleep(self.config.monitoring_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.config.monitoring_interval)
                
        self.logger.info("Monitoring loop stopped")
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.running = False
        
    def get_status(self) -> dict:
        """Get agent status for external queries"""
        return {
            'hostname': self.hostname,
            'status': self.get_system_status(),
            'recent_alerts': self.state.get('alerts', [])[-20:],
            'maintenance_history': self.state.get('maintenance_history', [])[-20:],
            'process_kills': self.state.get('process_kills_count', 0),
            'disk_cleanups': self.state.get('disk_cleanups', 0)
        }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ebon Media Server Maintenance Agent')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Get current status')
    parser.add_argument('--check', action='store_true', help='Run single check')
    parser.add_argument('--cleanup', action='store_true', help='Run disk cleanup')
    parser.add_argument('--kill-noip2', action='store_true', help='Kill all noip2 processes')
    
    args = parser.parse_args()
    
    agent = EbonMaintenanceAgent()
    
    if args.status:
        print(json.dumps(agent.get_status(), indent=2, default=str))
    elif args.check:
        agent.run_maintenance_cycle()
        print("Maintenance check completed")
    elif args.cleanup:
        agent.emergency_disk_cleanup()
        print("Disk cleanup completed")
    elif args.kill_noip2:
        # Special command to kill all noip2 processes
        subprocess.run(['sudo', 'pkill', '-9', 'noip2'], capture_output=True)
        print("Killed all noip2 processes")
    elif args.daemon:
        agent.run()
    else:
        # Run in foreground
        agent.run()

if __name__ == '__main__':
    main()