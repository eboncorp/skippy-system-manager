#!/usr/bin/env python3
"""
Home Server Master Controller v1.0
Unified management system integrating all server components
"""

import os
import sys
import json
import yaml
import time
import signal
import logging
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import queue

# Third-party imports with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

@dataclass
class ComponentStatus:
    """Status of a system component"""
    name: str
    enabled: bool
    running: bool
    health: str  # healthy, degraded, failed
    last_check: datetime
    message: str = ""
    metrics: Dict[str, Any] = None

@dataclass
class ServerConfig:
    """Main server configuration"""
    # Core settings
    server_name: str = "HomeServer"
    server_port: int = 8080
    enable_web_ui: bool = True
    enable_api: bool = True
    
    # Component settings
    enable_system_manager: bool = True
    enable_ethereum_node: bool = False
    enable_cloud_sync: bool = True
    enable_monitoring: bool = True
    enable_ai_maintenance: bool = True
    
    # Paths
    data_dir: Path = Path.home() / ".home-server"
    log_dir: Path = Path.home() / ".home-server" / "logs"
    config_dir: Path = Path.home() / ".home-server" / "config"
    
    # Performance
    max_workers: int = 4
    check_interval: int = 60  # seconds
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        d = asdict(self)
        # Convert Path objects to strings
        for key, value in d.items():
            if isinstance(value, Path):
                d[key] = str(value)
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ServerConfig':
        """Create from dictionary"""
        # Convert string paths back to Path objects
        for key in ['data_dir', 'log_dir', 'config_dir']:
            if key in data and isinstance(data[key], str):
                data[key] = Path(data[key])
        return cls(**data)

class HomeServerMaster:
    """Main home server controller"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.version = "1.0.0"
        self.start_time = datetime.now()
        
        # Load or create configuration
        self.config_path = config_path or Path.home() / ".home-server" / "server.yaml"
        self.config = self.load_config()
        
        # Ensure directories exist
        self.setup_directories()
        
        # Setup logging
        self.setup_logging()
        self.logger.info(f"Home Server Master v{self.version} initializing")
        
        # Component registry
        self.components = {}
        self.component_status = {}
        self.component_threads = {}
        
        # Runtime state
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=2)
        
        # Event system
        self.event_queue = queue.Queue()
        self.event_handlers = {}
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_directories(self):
        """Create necessary directories"""
        for dir_path in [self.config.data_dir, self.config.log_dir, self.config.config_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def setup_logging(self):
        """Configure logging system"""
        log_file = self.config.log_dir / f"home-server-{datetime.now():%Y%m%d}.log"
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Setup handlers
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger("HomeServerMaster")
        
    def load_config(self) -> ServerConfig:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix == '.yaml':
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                return ServerConfig.from_dict(data)
            except Exception as e:
                print(f"Error loading config: {e}")
                return ServerConfig()
        else:
            # Create default config
            config = ServerConfig()
            self.save_config(config)
            return config
            
    def save_config(self, config: Optional[ServerConfig] = None):
        """Save configuration to file"""
        config = config or self.config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            if self.config_path.suffix == '.yaml':
                yaml.dump(config.to_dict(), f, default_flow_style=False)
            else:
                json.dump(config.to_dict(), f, indent=2)
                
    def register_component(self, name: str, component: Any):
        """Register a system component"""
        self.components[name] = component
        self.component_status[name] = ComponentStatus(
            name=name,
            enabled=True,
            running=False,
            health="unknown",
            last_check=datetime.now()
        )
        self.logger.info(f"Registered component: {name}")
        
    def initialize_components(self):
        """Initialize all enabled components"""
        self.logger.info("Initializing components...")
        
        # System Manager
        if self.config.enable_system_manager:
            self.init_system_manager()
            
        # Ethereum Node
        if self.config.enable_ethereum_node:
            self.init_ethereum_node()
            
        # Cloud Sync
        if self.config.enable_cloud_sync:
            self.init_cloud_sync()
            
        # Monitoring
        if self.config.enable_monitoring:
            self.init_monitoring()
            
        # AI Maintenance
        if self.config.enable_ai_maintenance:
            self.init_ai_maintenance()
            
    def init_system_manager(self):
        """Initialize system management component"""
        try:
            # Check if the advanced system manager exists
            manager_path = Path(__file__).parent / "advanced_system_manager.py"
            if manager_path.exists():
                from advanced_system_manager import AdvancedSystemManager
                manager = AdvancedSystemManager()
                self.register_component("system_manager", manager)
            else:
                self.logger.warning("Advanced system manager not found, using basic manager")
                self.register_component("system_manager", BasicSystemManager())
        except Exception as e:
            self.logger.error(f"Failed to initialize system manager: {e}")
            
    def init_ethereum_node(self):
        """Initialize Ethereum node component"""
        try:
            eth_script = Path(__file__).parent / "Downloads" / "enhanced_ethereum_node_v29.sh"
            if eth_script.exists():
                self.register_component("ethereum_node", EthereumNodeManager(eth_script))
            else:
                self.logger.warning("Ethereum node script not found")
        except Exception as e:
            self.logger.error(f"Failed to initialize Ethereum node: {e}")
            
    def init_cloud_sync(self):
        """Initialize cloud sync component"""
        try:
            gdrive_script = Path(__file__).parent / "gdrive_manager.sh"
            if gdrive_script.exists():
                self.register_component("cloud_sync", CloudSyncManager(gdrive_script))
            else:
                self.logger.warning("Cloud sync script not found")
        except Exception as e:
            self.logger.error(f"Failed to initialize cloud sync: {e}")
            
    def init_monitoring(self):
        """Initialize monitoring component"""
        try:
            self.register_component("monitoring", MonitoringService(self))
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring: {e}")
            
    def init_ai_maintenance(self):
        """Initialize AI maintenance component"""
        try:
            ai_path = Path(__file__).parent / "ai_maintenance_engine.py"
            if ai_path.exists():
                from ai_maintenance_engine import AIMaintenanceEngine
                engine = AIMaintenanceEngine()
                self.register_component("ai_maintenance", engine)
            else:
                self.logger.warning("AI maintenance engine not found")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI maintenance: {e}")
            
    def start(self):
        """Start the home server"""
        self.logger.info("Starting Home Server Master...")
        self.running = True
        
        # Initialize components
        self.initialize_components()
        
        # Start component threads
        for name, component in self.components.items():
            if hasattr(component, 'start'):
                thread = threading.Thread(
                    target=self.run_component,
                    args=(name, component),
                    daemon=True
                )
                thread.start()
                self.component_threads[name] = thread
                
        # Start monitoring loop
        monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # Start event processor
        event_thread = threading.Thread(target=self.process_events, daemon=True)
        event_thread.start()
        
        # Start web UI if enabled
        if self.config.enable_web_ui:
            self.start_web_ui()
            
        self.logger.info("Home Server Master started successfully")
        
    def run_component(self, name: str, component: Any):
        """Run a component in its own thread"""
        try:
            self.component_status[name].running = True
            self.component_status[name].health = "healthy"
            
            if hasattr(component, 'start'):
                component.start()
            elif hasattr(component, 'run'):
                component.run()
                
        except Exception as e:
            self.logger.error(f"Component {name} failed: {e}")
            self.component_status[name].running = False
            self.component_status[name].health = "failed"
            self.component_status[name].message = str(e)
            
    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check component health
                for name, component in self.components.items():
                    self.check_component_health(name, component)
                    
                # Collect system metrics
                if PSUTIL_AVAILABLE:
                    metrics = self.collect_system_metrics()
                    self.publish_event("system_metrics", metrics)
                    
                # Sleep until next check
                time.sleep(self.config.check_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(10)
                
    def check_component_health(self, name: str, component: Any):
        """Check health of a component"""
        try:
            status = self.component_status[name]
            status.last_check = datetime.now()
            
            if hasattr(component, 'health_check'):
                health = component.health_check()
                status.health = health.get('status', 'unknown')
                status.message = health.get('message', '')
                status.metrics = health.get('metrics', {})
            elif hasattr(component, 'is_running'):
                status.running = component.is_running()
                status.health = 'healthy' if status.running else 'failed'
            else:
                # Basic check - component exists
                status.health = 'healthy' if status.running else 'unknown'
                
        except Exception as e:
            self.logger.error(f"Health check failed for {name}: {e}")
            status.health = 'failed'
            status.message = str(e)
            
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-wide metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'uptime': (datetime.now() - self.start_time).total_seconds()
        }
        
        if PSUTIL_AVAILABLE:
            try:
                metrics.update({
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory': {
                        'percent': psutil.virtual_memory().percent,
                        'available': psutil.virtual_memory().available,
                        'total': psutil.virtual_memory().total
                    },
                    'disk': {
                        'percent': psutil.disk_usage('/').percent,
                        'free': psutil.disk_usage('/').free,
                        'total': psutil.disk_usage('/').total
                    },
                    'network': {
                        'bytes_sent': psutil.net_io_counters().bytes_sent,
                        'bytes_recv': psutil.net_io_counters().bytes_recv
                    }
                })
            except Exception as e:
                self.logger.error(f"Failed to collect system metrics: {e}")
                
        return metrics
        
    def publish_event(self, event_type: str, data: Any):
        """Publish an event to the event queue"""
        self.event_queue.put({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now()
        })
        
    def process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                
                # Call registered handlers
                if event['type'] in self.event_handlers:
                    for handler in self.event_handlers[event['type']]:
                        try:
                            handler(event)
                        except Exception as e:
                            self.logger.error(f"Event handler error: {e}")
                            
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Event processing error: {e}")
                
    def register_event_handler(self, event_type: str, handler: callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def start_web_ui(self):
        """Start the web UI server"""
        try:
            web_path = Path(__file__).parent / "web_system_manager.py"
            if web_path.exists():
                from web_system_manager import WebSystemManager
                web_manager = WebSystemManager()
                self.register_component("web_ui", web_manager)
                self.logger.info(f"Web UI available at http://localhost:{self.config.server_port}")
            else:
                self.logger.warning("Web UI module not found")
        except Exception as e:
            self.logger.error(f"Failed to start web UI: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'version': self.version,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'components': {
                name: asdict(status)
                for name, status in self.component_status.items()
            },
            'config': self.config.to_dict()
        }
        
    def stop(self):
        """Stop the home server"""
        self.logger.info("Stopping Home Server Master...")
        self.running = False
        
        # Stop components
        for name, component in self.components.items():
            try:
                if hasattr(component, 'stop'):
                    component.stop()
                self.logger.info(f"Stopped component: {name}")
            except Exception as e:
                self.logger.error(f"Error stopping {name}: {e}")
                
        # Shutdown executors
        self.executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)
        
        self.logger.info("Home Server Master stopped")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

# Component implementations
class BasicSystemManager:
    """Basic system management functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger("BasicSystemManager")
        
    def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        return {
            'status': 'healthy',
            'message': 'Basic system manager running'
        }

class EthereumNodeManager:
    """Ethereum node management"""
    
    def __init__(self, script_path: Path):
        self.script_path = script_path
        self.logger = logging.getLogger("EthereumNodeManager")
        self.process = None
        
    def start(self):
        """Start Ethereum node"""
        try:
            self.process = subprocess.Popen(
                ['bash', str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.logger.info("Ethereum node started")
        except Exception as e:
            self.logger.error(f"Failed to start Ethereum node: {e}")
            
    def stop(self):
        """Stop Ethereum node"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.logger.info("Ethereum node stopped")
            
    def health_check(self) -> Dict[str, Any]:
        """Check node health"""
        if self.process and self.process.poll() is None:
            return {'status': 'healthy', 'message': 'Node running'}
        else:
            return {'status': 'failed', 'message': 'Node not running'}

class CloudSyncManager:
    """Cloud synchronization management"""
    
    def __init__(self, script_path: Path):
        self.script_path = script_path
        self.logger = logging.getLogger("CloudSyncManager")
        
    def health_check(self) -> Dict[str, Any]:
        """Check sync status"""
        return {
            'status': 'healthy',
            'message': 'Cloud sync available'
        }

class MonitoringService:
    """System monitoring service"""
    
    def __init__(self, server: 'HomeServerMaster'):
        self.server = server
        self.logger = logging.getLogger("MonitoringService")
        
    def health_check(self) -> Dict[str, Any]:
        """Check monitoring health"""
        return {
            'status': 'healthy',
            'message': 'Monitoring active',
            'metrics': {
                'components_monitored': len(self.server.components)
            }
        }

# CLI Interface
def create_cli():
    """Create command-line interface"""
    if not CLICK_AVAILABLE:
        return None
        
    @click.group()
    @click.version_option(version='1.0.0')
    def cli():
        """Home Server Master Controller"""
        pass
        
    @cli.command()
    @click.option('--config', type=click.Path(), help='Configuration file path')
    def start(config):
        """Start the home server"""
        server = HomeServerMaster(Path(config) if config else None)
        server.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            
    @cli.command()
    @click.option('--config', type=click.Path(), help='Configuration file path')
    def status(config):
        """Show server status"""
        server = HomeServerMaster(Path(config) if config else None)
        status = server.get_status()
        print(json.dumps(status, indent=2, default=str))
        
    @cli.command()
    @click.option('--enable-ethereum', is_flag=True, help='Enable Ethereum node')
    @click.option('--enable-ai', is_flag=True, help='Enable AI maintenance')
    @click.option('--port', type=int, help='Web UI port')
    def configure(enable_ethereum, enable_ai, port):
        """Configure server settings"""
        server = HomeServerMaster()
        
        if enable_ethereum:
            server.config.enable_ethereum_node = True
        if enable_ai:
            server.config.enable_ai_maintenance = True
        if port:
            server.config.server_port = port
            
        server.save_config()
        print("Configuration saved")
        
    return cli

# Main entry point
if __name__ == "__main__":
    if CLICK_AVAILABLE:
        cli = create_cli()
        cli()
    else:
        # Fallback to basic operation
        print("Home Server Master Controller")
        print("1. Start server")
        print("2. Show status")
        print("3. Exit")
        
        choice = input("Select option: ")
        
        if choice == "1":
            server = HomeServerMaster()
            server.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                server.stop()
        elif choice == "2":
            server = HomeServerMaster()
            print(json.dumps(server.get_status(), indent=2, default=str))
        else:
            print("Exiting...")