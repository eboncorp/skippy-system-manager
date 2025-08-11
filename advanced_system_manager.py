#!/usr/bin/env python3
"""
Advanced Unified System Manager v3.0
Plugin-based architecture with advanced automation, security, and remote capabilities
Linux-focused enterprise-grade system management
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import time
import json
# import yaml  # Fallback to JSON if YAML not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
import sqlite3
from pathlib import Path
import queue
import re
import shutil
import signal
import hashlib
import tempfile
import importlib.util
import inspect
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod
import logging
import configparser

# Advanced dependencies with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/advanced-system-manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    cpu_temperature: Optional[float]
    load_average: List[float]
    uptime: timedelta
    processes: int
    timestamp: datetime

@dataclass
class CleanupTask:
    """Cleanup task configuration"""
    id: str
    name: str
    description: str
    command: str
    category: str
    size_estimate: int
    risk_level: str  # low, medium, high
    dependencies: List[str]
    enabled: bool = True

@dataclass
class AutomationRule:
    """Automation rule configuration"""
    id: str
    name: str
    trigger: str  # time, event, condition
    condition: str
    action: str
    enabled: bool = True
    last_run: Optional[datetime] = None

class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def initialize(self, manager) -> bool:
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        pass
    
    @abstractmethod
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return menu items for the plugin"""
        pass

class DatabaseManager:
    """SQLite database manager for persistent storage"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # System metrics history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    temperature REAL,
                    load_1min REAL,
                    load_5min REAL,
                    load_15min REAL,
                    processes INTEGER
                )
            """)
            
            # Cleanup history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    task_id TEXT,
                    task_name TEXT,
                    space_saved INTEGER,
                    duration REAL,
                    status TEXT
                )
            """)
            
            # Automation rules
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    trigger_type TEXT,
                    condition_expr TEXT,
                    action_command TEXT,
                    enabled BOOLEAN,
                    last_run DATETIME,
                    run_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Security events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    severity TEXT,
                    description TEXT,
                    details TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Plugin settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugin_settings (
                    plugin_name TEXT,
                    setting_key TEXT,
                    setting_value TEXT,
                    PRIMARY KEY (plugin_name, setting_key)
                )
            """)
            
            conn.commit()
            
    def store_metrics(self, metrics: SystemMetrics):
        """Store system metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics_history 
                (cpu_percent, memory_percent, disk_percent, temperature, 
                 load_1min, load_5min, load_15min, processes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_percent,
                metrics.cpu_temperature,
                metrics.load_average[0] if len(metrics.load_average) > 0 else 0,
                metrics.load_average[1] if len(metrics.load_average) > 1 else 0,
                metrics.load_average[2] if len(metrics.load_average) > 2 else 0,
                metrics.processes
            ))
            conn.commit()
            
    def get_metrics_history(self, hours: int = 24) -> List[Dict]:
        """Get metrics history for specified hours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metrics_history 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class ConfigurationManager:
    """Advanced configuration management"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = config_dir / "advanced_config.yaml"
        self.load_configuration()
        
    def load_configuration(self):
        """Load configuration from YAML or JSON file"""
        # Try JSON first if YAML not available
        json_file = self.config_dir / "advanced_config.json"
        
        if not YAML_AVAILABLE and json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    self.config = json.load(f)
                return
            except Exception as e:
                logger.error(f"Error loading JSON configuration: {e}")
        
        if YAML_AVAILABLE and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading YAML configuration: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_configuration()
            
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'system': {
                'monitoring_interval': 2,
                'history_retention_days': 30,
                'auto_cleanup_threshold': 85,
                'cpu_alert_threshold': 80,
                'memory_alert_threshold': 85,
                'disk_alert_threshold': 90,
                'log_level': 'INFO'
            },
            'cleanup': {
                'backup_before_cleanup': True,
                'verify_actions': True,
                'parallel_tasks': 4,
                'safe_mode': True,
                'custom_excludes': [
                    '*.important',
                    'backup_*',
                    'production_*'
                ]
            },
            'automation': {
                'enabled': True,
                'max_concurrent_rules': 5,
                'rule_timeout': 300,
                'notification_on_failure': True
            },
            'security': {
                'file_integrity_check': True,
                'permission_monitor': True,
                'suspicious_process_detection': True,
                'security_scan_interval': 3600
            },
            'plugins': {
                'auto_load': True,
                'plugin_dirs': [
                    'plugins',
                    '~/.config/system-manager/plugins'
                ],
                'enabled_plugins': []
            },
            'ui': {
                'theme': 'dark',
                'auto_refresh': True,
                'refresh_interval': 5,
                'show_notifications': True,
                'minimize_to_tray': True
            }
        }
        
    def save_configuration(self):
        """Save configuration to YAML or JSON file"""
        try:
            if YAML_AVAILABLE:
                with open(self.config_file, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
            else:
                # Fallback to JSON
                json_file = self.config_dir / "advanced_config.json"
                with open(json_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        config[keys[-1]] = value
        self.save_configuration()

class PluginManager:
    """Advanced plugin management system"""
    
    def __init__(self, plugin_dirs: List[str], config_manager: ConfigurationManager):
        self.plugin_dirs = [Path(d).expanduser() for d in plugin_dirs]
        self.config_manager = config_manager
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_modules = {}
        
        # Create plugin directories
        for plugin_dir in self.plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue
                    
                plugins.append(str(plugin_file))
                
        return plugins
        
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a single plugin"""
        try:
            plugin_path = Path(plugin_path)
            module_name = plugin_path.stem
            
            # Load module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    break
                    
            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_path}")
                return False
                
            # Initialize plugin
            plugin_instance = plugin_class()
            if plugin_instance.initialize(self):
                self.plugins[plugin_instance.name] = plugin_instance
                self.plugin_modules[plugin_instance.name] = module
                logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                return True
            else:
                logger.error(f"Failed to initialize plugin: {plugin_instance.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_path}: {e}")
            return False
            
    def load_all_plugins(self):
        """Load all discovered plugins"""
        plugins = self.discover_plugins()
        loaded_count = 0
        
        for plugin_path in plugins:
            if self.load_plugin(plugin_path):
                loaded_count += 1
                
        logger.info(f"Loaded {loaded_count}/{len(plugins)} plugins")
        
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin"""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
                if plugin_name in self.plugin_modules:
                    del self.plugin_modules[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")
                
    def get_plugin_menu_items(self) -> Dict[str, List[Dict]]:
        """Get menu items from all plugins"""
        menu_items = {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                items = plugin.get_menu_items()
                if items:
                    menu_items[plugin_name] = items
            except Exception as e:
                logger.error(f"Error getting menu items from {plugin_name}: {e}")
                
        return menu_items

class SecurityManager:
    """System security and integrity monitoring"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigurationManager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.file_hashes = {}
        self.monitored_paths = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/etc/ssh/sshd_config',
            '/etc/hosts',
            '/boot/grub/grub.cfg'
        ]
        
    def initialize_file_integrity(self):
        """Initialize file integrity monitoring"""
        if not self.config_manager.get('security.file_integrity_check', True):
            return
            
        logger.info("Initializing file integrity monitoring...")
        
        for file_path in self.monitored_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    with open(path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        self.file_hashes[file_path] = file_hash
                except Exception as e:
                    logger.error(f"Error hashing {file_path}: {e}")
                    
    def check_file_integrity(self):
        """Check file integrity"""
        violations = []
        
        for file_path, expected_hash in self.file_hashes.items():
            path = Path(file_path)
            if not path.exists():
                violations.append(f"Critical file missing: {file_path}")
                continue
                
            try:
                with open(path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                    
                if current_hash != expected_hash:
                    violations.append(f"File integrity violation: {file_path}")
                    self.log_security_event("file_integrity", "high", 
                                          f"File modified: {file_path}")
                    
            except Exception as e:
                violations.append(f"Error checking {file_path}: {e}")
                
        return violations
        
    def check_suspicious_processes(self):
        """Check for suspicious processes"""
        if not PSUTIL_AVAILABLE:
            return []
            
        suspicious = []
        
        # Common suspicious process patterns
        suspicious_patterns = [
            r'.*\.tmp$',
            r'.*[0-9]{8,}$',
            r'.*\.(sh|py|pl)$',
            r'nc|netcat',
            r'nmap',
            r'john|hashcat',
            r'metasploit',
        ]
        
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
                try:
                    process_info = process.info
                    process_name = process_info['name']
                    
                    for pattern in suspicious_patterns:
                        if re.match(pattern, process_name, re.IGNORECASE):
                            suspicious.append({
                                'pid': process_info['pid'],
                                'name': process_name,
                                'cmdline': ' '.join(process_info['cmdline'] or []),
                                'user': process_info['username']
                            })
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
            
        return suspicious
        
    def check_network_connections(self):
        """Check for suspicious network connections"""
        if not PSUTIL_AVAILABLE:
            return []
            
        suspicious = []
        
        try:
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                # Check for listening on unusual ports
                if (conn.status == 'LISTEN' and 
                    conn.laddr.port not in [22, 80, 443, 53, 25, 110, 143, 993, 995]):
                    
                    try:
                        process = psutil.Process(conn.pid) if conn.pid else None
                        suspicious.append({
                            'port': conn.laddr.port,
                            'address': conn.laddr.ip,
                            'process': process.name() if process else 'Unknown',
                            'pid': conn.pid
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
        except Exception as e:
            logger.error(f"Error checking network connections: {e}")
            
        return suspicious
        
    def run_security_scan(self):
        """Run comprehensive security scan"""
        results = {
            'file_integrity': self.check_file_integrity(),
            'suspicious_processes': self.check_suspicious_processes(),
            'network_connections': self.check_network_connections(),
            'timestamp': datetime.now()
        }
        
        # Log critical issues
        total_issues = (len(results['file_integrity']) + 
                       len(results['suspicious_processes']) + 
                       len(results['network_connections']))
        
        if total_issues > 0:
            self.log_security_event("security_scan", "medium", 
                                  f"Security scan found {total_issues} issues")
                                  
        return results
        
    def log_security_event(self, event_type: str, severity: str, description: str, details: str = ""):
        """Log security event to database"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO security_events (event_type, severity, description, details)
                VALUES (?, ?, ?, ?)
            """, (event_type, severity, description, details))
            conn.commit()

class AutomationEngine:
    """Advanced automation and scheduling engine"""
    
    def __init__(self, db_manager: DatabaseManager, config_manager: ConfigurationManager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.rules: Dict[str, AutomationRule] = {}
        self.running = False
        self.thread = None
        
    def load_rules(self):
        """Load automation rules from database"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM automation_rules WHERE enabled = 1")
            
            for row in cursor.fetchall():
                rule = AutomationRule(
                    id=row[0],
                    name=row[1],
                    trigger=row[2],
                    condition=row[3],
                    action=row[4],
                    enabled=bool(row[5]),
                    last_run=datetime.fromisoformat(row[6]) if row[6] else None
                )
                self.rules[rule.id] = rule
                
        logger.info(f"Loaded {len(self.rules)} automation rules")
        
    def add_rule(self, rule: AutomationRule):
        """Add automation rule"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO automation_rules 
                (id, name, trigger_type, condition_expr, action_command, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule.id, rule.name, rule.trigger, rule.condition, rule.action, rule.enabled))
            conn.commit()
            
        self.rules[rule.id] = rule
        
    def evaluate_condition(self, condition: str, metrics: SystemMetrics) -> bool:
        """Evaluate automation condition"""
        try:
            # Create evaluation context
            context = {
                'cpu': metrics.cpu_percent,
                'memory': metrics.memory_percent,
                'disk': metrics.disk_percent,
                'load': metrics.load_average[0] if metrics.load_average else 0,
                'uptime_hours': metrics.uptime.total_seconds() / 3600,
                'processes': metrics.processes,
                'datetime': datetime,
                'time': time
            }
            
            # Safely evaluate condition
            return eval(condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
            
    def execute_action(self, action: str) -> bool:
        """Execute automation action"""
        try:
            if action.startswith("command:"):
                command = action[8:]  # Remove "command:" prefix
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.returncode == 0
                
            elif action.startswith("cleanup:"):
                task_id = action[8:]  # Remove "cleanup:" prefix
                # Integration with cleanup system
                return True
                
            elif action.startswith("notification:"):
                message = action[13:]  # Remove "notification:" prefix
                # Send notification
                return True
                
            else:
                logger.error(f"Unknown action type: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            return False
            
    def run_automation_loop(self):
        """Main automation loop"""
        while self.running:
            try:
                # Get current metrics (would be passed from main system)
                if PSUTIL_AVAILABLE:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
                    processes = len(psutil.pids())
                    
                    metrics = SystemMetrics(
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        disk_percent=(disk.used / disk.total) * 100,
                        network_io={},
                        cpu_temperature=None,
                        load_average=list(load_avg),
                        uptime=uptime,
                        processes=processes,
                        timestamp=datetime.now()
                    )
                    
                    # Check each rule
                    for rule in self.rules.values():
                        if not rule.enabled:
                            continue
                            
                        # Check trigger conditions
                        should_run = False
                        
                        if rule.trigger == "condition":
                            should_run = self.evaluate_condition(rule.condition, metrics)
                        elif rule.trigger == "time":
                            # Time-based triggers (cron-like)
                            should_run = self.check_time_trigger(rule.condition)
                        elif rule.trigger == "event":
                            # Event-based triggers
                            should_run = self.check_event_trigger(rule.condition, metrics)
                            
                        if should_run:
                            logger.info(f"Executing automation rule: {rule.name}")
                            success = self.execute_action(rule.action)
                            
                            # Update rule execution info
                            rule.last_run = datetime.now()
                            self.update_rule_execution(rule.id, success)
                            
                time.sleep(self.config_manager.get('automation.check_interval', 30))
                
            except Exception as e:
                logger.error(f"Error in automation loop: {e}")
                time.sleep(30)
                
    def start(self):
        """Start automation engine"""
        if not self.config_manager.get('automation.enabled', True):
            return
            
        self.load_rules()
        self.running = True
        self.thread = threading.Thread(target=self.run_automation_loop, daemon=True)
        self.thread.start()
        logger.info("Automation engine started")
        
    def stop(self):
        """Stop automation engine"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Automation engine stopped")
        
    def check_time_trigger(self, time_expr: str) -> bool:
        """Check if time-based trigger should fire"""
        # Simplified cron-like expression evaluation
        # Format: "hour:minute" or "daily", "hourly", etc.
        try:
            now = datetime.now()
            
            if time_expr == "hourly":
                return now.minute == 0
            elif time_expr == "daily":
                return now.hour == 2 and now.minute == 0  # 2 AM daily
            elif ":" in time_expr:
                hour, minute = map(int, time_expr.split(":"))
                return now.hour == hour and now.minute == minute
                
        except Exception as e:
            logger.error(f"Error checking time trigger '{time_expr}': {e}")
            
        return False
        
    def check_event_trigger(self, event_expr: str, metrics: SystemMetrics) -> bool:
        """Check if event-based trigger should fire"""
        # Event-based triggers (e.g., "disk_full", "high_cpu", etc.)
        try:
            if event_expr == "disk_full":
                return metrics.disk_percent > 90
            elif event_expr == "high_cpu":
                return metrics.cpu_percent > 80
            elif event_expr == "high_memory":
                return metrics.memory_percent > 85
            elif event_expr == "system_boot":
                return metrics.uptime.total_seconds() < 300  # Within 5 minutes of boot
                
        except Exception as e:
            logger.error(f"Error checking event trigger '{event_expr}': {e}")
            
        return False
        
    def update_rule_execution(self, rule_id: str, success: bool):
        """Update rule execution statistics"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE automation_rules 
                SET last_run = datetime('now'), run_count = run_count + 1
                WHERE id = ?
            """, (rule_id,))
            conn.commit()

class AdvancedSystemManager:
    """Main advanced system manager class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced System Manager v3.0")
        self.root.geometry("1800x1200")
        self.root.minsize(1600, 900)
        
        # Initialize core components
        self.config_dir = Path.home() / ".advanced-system-manager"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.config_manager = ConfigurationManager(self.config_dir)
        self.db_manager = DatabaseManager(self.config_dir / "system_manager.db")
        self.plugin_manager = PluginManager(
            self.config_manager.get('plugins.plugin_dirs', ['plugins']),
            self.config_manager
        )
        self.security_manager = SecurityManager(self.db_manager, self.config_manager)
        self.automation_engine = AutomationEngine(self.db_manager, self.config_manager)
        
        # Application state
        self.monitoring = True
        self.monitor_thread = None
        self.current_metrics = None
        
        # Create built-in plugins directory and examples
        self.create_plugin_examples()
        
        # Load plugins
        if self.config_manager.get('plugins.auto_load', True):
            self.plugin_manager.load_all_plugins()
            
        # Initialize security monitoring
        self.security_manager.initialize_file_integrity()
        
        # Create enhanced interface
        self.create_advanced_interface()
        
        # Start systems
        self.start_advanced_monitoring()
        self.automation_engine.start()
        
        # Handle shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_shutdown)
        
        logger.info("Advanced System Manager initialized")
        
    def create_plugin_examples(self):
        """Create example plugins"""
        plugins_dir = self.config_dir / "plugins"
        plugins_dir.mkdir(exist_ok=True)
        
        # Network monitoring plugin example
        network_plugin = plugins_dir / "network_monitor.py"
        if not network_plugin.exists():
            network_plugin.write_text('''
import time
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from advanced_system_manager import PluginInterface

class NetworkMonitorPlugin(PluginInterface):
    def __init__(self):
        self.active = False
        
    @property
    def name(self) -> str:
        return "Network Monitor"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "Network interface and connection monitoring"
        
    def initialize(self, manager) -> bool:
        self.manager = manager
        self.active = True
        return True
        
    def cleanup(self) -> None:
        self.active = False
        
    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "label": "Network Status",
                "command": self.show_network_status
            },
            {
                "label": "Port Scanner",
                "command": self.run_port_scan
            }
        ]
        
    def show_network_status(self):
        """Show network interface status"""
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            # Display in a popup or log
            print("Network interfaces:", result.stdout)
        except Exception as e:
            print(f"Error getting network status: {e}")
            
    def run_port_scan(self):
        """Run basic port scan"""
        try:
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
            print("Open ports:", result.stdout)
        except Exception as e:
            print(f"Error scanning ports: {e}")
''')
        
        # System hardening plugin example
        hardening_plugin = plugins_dir / "system_hardening.py"
        if not hardening_plugin.exists():
            hardening_plugin.write_text('''
import subprocess
from typing import Dict, List, Any
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from advanced_system_manager import PluginInterface

class SystemHardeningPlugin(PluginInterface):
    def __init__(self):
        self.active = False
        
    @property
    def name(self) -> str:
        return "System Hardening"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def description(self) -> str:
        return "System security hardening tools"
        
    def initialize(self, manager) -> bool:
        self.manager = manager
        self.active = True
        return True
        
    def cleanup(self) -> None:
        self.active = False
        
    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "label": "Security Audit",
                "command": self.run_security_audit
            },
            {
                "label": "Firewall Status",
                "command": self.check_firewall
            },
            {
                "label": "Update System",
                "command": self.update_system
            }
        ]
        
    def run_security_audit(self):
        """Run basic security audit"""
        print("Running security audit...")
        
    def check_firewall(self):
        """Check firewall status"""
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
            print("Firewall status:", result.stdout)
        except Exception as e:
            print(f"Error checking firewall: {e}")
            
    def update_system(self):
        """Update system packages"""
        print("Updating system packages...")
''')
        
    def create_advanced_interface(self):
        """Create advanced interface with plugin integration"""
        # Configure modern dark theme (reusing from previous version)
        self.root.configure(bg="#1e1e1e")
        
        # Create main container
        self.main_container = ttk.Frame(self.root, padding="15")
        self.main_container.pack(fill='both', expand=True)
        
        # Create menu bar with plugin integration
        self.create_menu_bar()
        
        # Create header with system status
        self.create_system_header()
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, pady=(15, 0))
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_automation_tab()
        self.create_security_tab()
        self.create_plugins_tab()
        self.create_analytics_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create menu bar with plugin integration"""
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="white")
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Configuration", command=self.export_config)
        file_menu.add_command(label="Import Configuration", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_shutdown)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="System Information", command=self.show_system_info)
        tools_menu.add_command(label="Performance Monitor", command=self.show_performance_monitor)
        tools_menu.add_command(label="Security Scan", command=self.run_security_scan)
        
        # Plugins menu
        self.plugins_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menubar.add_cascade(label="Plugins", menu=self.plugins_menu)
        self.update_plugins_menu()
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
    def update_plugins_menu(self):
        """Update plugins menu with loaded plugins"""
        self.plugins_menu.delete(0, 'end')
        
        # Add plugin management options
        self.plugins_menu.add_command(label="Manage Plugins", command=self.show_plugin_manager)
        self.plugins_menu.add_command(label="Reload Plugins", command=self.reload_plugins)
        self.plugins_menu.add_separator()
        
        # Add plugin-specific menu items
        plugin_menus = self.plugin_manager.get_plugin_menu_items()
        
        for plugin_name, menu_items in plugin_menus.items():
            plugin_submenu = tk.Menu(self.plugins_menu, tearoff=0, bg="#2d2d2d", fg="white")
            self.plugins_menu.add_cascade(label=plugin_name, menu=plugin_submenu)
            
            for item in menu_items:
                plugin_submenu.add_command(
                    label=item['label'],
                    command=item['command']
                )
                
    def create_system_header(self):
        """Create system status header"""
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Left side - Title and status
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side='left', fill='y')
        
        title = ttk.Label(left_frame, text="🔧 Advanced System Manager", 
                         font=('Segoe UI', 18, 'bold'))
        title.pack(anchor='w')
        
        self.system_status = ttk.Label(left_frame, text="Initializing...",
                                      font=('Segoe UI', 10))
        self.system_status.pack(anchor='w')
        
        # Right side - Quick metrics
        right_frame = ttk.Frame(header_frame)
        right_frame.pack(side='right', fill='y')
        
        self.quick_metrics = ttk.Label(right_frame, text="Loading metrics...",
                                      font=('Segoe UI', 10))
        self.quick_metrics.pack(anchor='e')
        
    def create_dashboard_tab(self):
        """Enhanced dashboard with analytics"""
        dashboard = ttk.Frame(self.notebook)
        self.notebook.add(dashboard, text="📊 Dashboard")
        
        # Create metrics display
        metrics_frame = ttk.LabelFrame(dashboard, text="System Metrics", padding=10)
        metrics_frame.pack(fill='x', padx=10, pady=5)
        
        # Real-time metrics (simplified for space)
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=6,
                                                     font=('Consolas', 9))
        self.metrics_text.pack(fill='x')
        
        # Recent activity
        activity_frame = ttk.LabelFrame(dashboard, text="Recent Activity", padding=10)
        activity_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.activity_text = scrolledtext.ScrolledText(activity_frame, height=15,
                                                      font=('Consolas', 9))
        self.activity_text.pack(fill='both', expand=True)
        
    def create_automation_tab(self):
        """Advanced automation management"""
        auto_frame = ttk.Frame(self.notebook)
        self.notebook.add(auto_frame, text="🤖 Automation")
        
        # Rules management
        rules_frame = ttk.LabelFrame(auto_frame, text="Automation Rules", padding=10)
        rules_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Rules list
        self.rules_tree = ttk.Treeview(rules_frame, 
                                      columns=('Trigger', 'Condition', 'Status'),
                                      show='tree headings')
        self.rules_tree.heading('#0', text='Rule Name')
        self.rules_tree.heading('Trigger', text='Trigger Type')
        self.rules_tree.heading('Condition', text='Condition')
        self.rules_tree.heading('Status', text='Status')
        
        rules_scroll = ttk.Scrollbar(rules_frame, orient='vertical', 
                                    command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=rules_scroll.set)
        
        self.rules_tree.pack(side='left', fill='both', expand=True)
        rules_scroll.pack(side='right', fill='y')
        
        # Rule controls
        controls_frame = ttk.Frame(auto_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Add Rule", 
                  command=self.add_automation_rule).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Edit Rule", 
                  command=self.edit_automation_rule).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Delete Rule", 
                  command=self.delete_automation_rule).pack(side='left', padx=5)
        
        # Load existing rules
        self.load_automation_rules()
        
    def create_security_tab(self):
        """Security monitoring and management"""
        security_frame = ttk.Frame(self.notebook)
        self.notebook.add(security_frame, text="🔒 Security")
        
        # Security status
        status_frame = ttk.LabelFrame(security_frame, text="Security Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Security controls
        controls_frame = ttk.Frame(status_frame)
        controls_frame.pack(fill='x', pady=5)
        
        ttk.Button(controls_frame, text="Run Security Scan", 
                  command=self.run_security_scan).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Check File Integrity", 
                  command=self.check_file_integrity).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Monitor Processes", 
                  command=self.monitor_processes).pack(side='left', padx=5)
        
        # Security log
        self.security_log = scrolledtext.ScrolledText(security_frame, height=20,
                                                     font=('Consolas', 9))
        self.security_log.pack(fill='both', expand=True, padx=10, pady=5)
        
    def create_plugins_tab(self):
        """Plugin management interface"""
        plugins_frame = ttk.Frame(self.notebook)
        self.notebook.add(plugins_frame, text="🔌 Plugins")
        
        # Plugin list
        list_frame = ttk.LabelFrame(plugins_frame, text="Installed Plugins", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.plugins_tree = ttk.Treeview(list_frame, 
                                        columns=('Version', 'Status', 'Description'),
                                        show='tree headings')
        self.plugins_tree.heading('#0', text='Plugin Name')
        self.plugins_tree.heading('Version', text='Version')
        self.plugins_tree.heading('Status', text='Status')
        self.plugins_tree.heading('Description', text='Description')
        
        plugins_scroll = ttk.Scrollbar(list_frame, orient='vertical', 
                                      command=self.plugins_tree.yview)
        self.plugins_tree.configure(yscrollcommand=plugins_scroll.set)
        
        self.plugins_tree.pack(side='left', fill='both', expand=True)
        plugins_scroll.pack(side='right', fill='y')
        
        # Plugin controls
        plugin_controls = ttk.Frame(plugins_frame)
        plugin_controls.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(plugin_controls, text="Load Plugin", 
                  command=self.load_plugin_dialog).pack(side='left', padx=5)
        ttk.Button(plugin_controls, text="Unload Plugin", 
                  command=self.unload_selected_plugin).pack(side='left', padx=5)
        ttk.Button(plugin_controls, text="Reload All", 
                  command=self.reload_plugins).pack(side='left', padx=5)
        
        # Update plugin list
        self.update_plugin_list()
        
    def create_analytics_tab(self):
        """System analytics and reporting"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📈 Analytics")
        
        # Analytics controls
        controls_frame = ttk.Frame(analytics_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate Report", 
                  command=self.generate_system_report).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Export Data", 
                  command=self.export_analytics_data).pack(side='left', padx=5)
        
        # Analytics display
        self.analytics_text = scrolledtext.ScrolledText(analytics_frame, 
                                                       font=('Consolas', 9))
        self.analytics_text.pack(fill='both', expand=True, padx=10, pady=5)
        
    def create_settings_tab(self):
        """Advanced settings management"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Settings notebook
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # General settings
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text="General")
        
        # Monitoring settings
        monitoring_frame = ttk.LabelFrame(general_frame, text="Monitoring", padding=10)
        monitoring_frame.pack(fill='x', pady=5)
        
        self.monitoring_interval = tk.IntVar(value=self.config_manager.get('system.monitoring_interval', 2))
        ttk.Label(monitoring_frame, text="Monitoring Interval (seconds):").pack(anchor='w')
        ttk.Scale(monitoring_frame, from_=1, to=60, variable=self.monitoring_interval,
                 orient='horizontal').pack(fill='x', pady=5)
        
        # Save settings button
        ttk.Button(settings_frame, text="Save Settings", 
                  command=self.save_settings).pack(pady=10)
        
    def create_status_bar(self):
        """Create enhanced status bar"""
        self.status_bar = ttk.Frame(self.main_container)
        self.status_bar.pack(fill='x', side='bottom', pady=(10, 0))
        
        # Status indicators
        self.status_left = ttk.Label(self.status_bar, text="🟢 Ready")
        self.status_left.pack(side='left')
        
        self.status_right = ttk.Label(self.status_bar, text="")
        self.status_right.pack(side='right')
        
    def start_advanced_monitoring(self):
        """Start advanced system monitoring"""
        def monitor_loop():
            while self.monitoring:
                try:
                    if PSUTIL_AVAILABLE:
                        # Collect comprehensive metrics
                        cpu_percent = psutil.cpu_percent(interval=1)
                        memory = psutil.virtual_memory()
                        disk = psutil.disk_usage('/')
                        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
                        processes = len(psutil.pids())
                        
                        # Get CPU temperature if available
                        cpu_temp = None
                        try:
                            temps = psutil.sensors_temperatures()
                            if 'coretemp' in temps:
                                cpu_temp = temps['coretemp'][0].current
                        except:
                            pass
                            
                        # Create metrics object
                        self.current_metrics = SystemMetrics(
                            cpu_percent=cpu_percent,
                            memory_percent=memory.percent,
                            disk_percent=(disk.used / disk.total) * 100,
                            network_io={},
                            cpu_temperature=cpu_temp,
                            load_average=list(load_avg),
                            uptime=uptime,
                            processes=processes,
                            timestamp=datetime.now()
                        )
                        
                        # Store metrics in database
                        self.db_manager.store_metrics(self.current_metrics)
                        
                        # Update UI
                        self.root.after(0, self.update_monitoring_display)
                        
                    time.sleep(self.config_manager.get('system.monitoring_interval', 2))
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(5)
                    
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def update_monitoring_display(self):
        """Update monitoring display in UI"""
        if not self.current_metrics:
            return
            
        # Update header status
        status_text = f"CPU: {self.current_metrics.cpu_percent:.1f}% | "
        status_text += f"RAM: {self.current_metrics.memory_percent:.1f}% | "
        status_text += f"Disk: {self.current_metrics.disk_percent:.1f}%"
        
        if self.current_metrics.cpu_temperature:
            status_text += f" | Temp: {self.current_metrics.cpu_temperature:.1f}°C"
            
        self.quick_metrics.config(text=status_text)
        
        # Update metrics display
        metrics_text = f"""System Metrics - {self.current_metrics.timestamp.strftime('%H:%M:%S')}
CPU Usage: {self.current_metrics.cpu_percent:.1f}%
Memory Usage: {self.current_metrics.memory_percent:.1f}%
Disk Usage: {self.current_metrics.disk_percent:.1f}%
Load Average: {', '.join(f'{x:.2f}' for x in self.current_metrics.load_average)}
Uptime: {str(self.current_metrics.uptime).split('.')[0]}
Processes: {self.current_metrics.processes}
"""
        
        if self.current_metrics.cpu_temperature:
            metrics_text += f"CPU Temperature: {self.current_metrics.cpu_temperature:.1f}°C\n"
            
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(1.0, metrics_text)
        
        # Check for alerts
        self.check_system_alerts()
        
    def check_system_alerts(self):
        """Check for system alerts and notifications"""
        if not self.current_metrics:
            return
            
        alerts = []
        
        # Check thresholds
        if self.current_metrics.cpu_percent > self.config_manager.get('system.cpu_alert_threshold', 80):
            alerts.append(f"High CPU usage: {self.current_metrics.cpu_percent:.1f}%")
            
        if self.current_metrics.memory_percent > self.config_manager.get('system.memory_alert_threshold', 85):
            alerts.append(f"High memory usage: {self.current_metrics.memory_percent:.1f}%")
            
        if self.current_metrics.disk_percent > self.config_manager.get('system.disk_alert_threshold', 90):
            alerts.append(f"Low disk space: {self.current_metrics.disk_percent:.1f}% used")
            
        # Log alerts
        for alert in alerts:
            self.log_activity(f"⚠️ ALERT: {alert}", "warning")
            
    def log_activity(self, message: str, level: str = "info"):
        """Log activity to the activity display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to activity display
        self.activity_text.insert(tk.END, formatted_message)
        self.activity_text.see(tk.END)
        
        # Keep only last 1000 lines
        lines = self.activity_text.get('1.0', tk.END).count('\n')
        if lines > 1000:
            self.activity_text.delete('1.0', '100.end')
            
    # Plugin management methods
    def show_plugin_manager(self):
        """Show plugin manager dialog"""
        self.notebook.select(3)  # Switch to plugins tab
        
    def load_plugin_dialog(self):
        """Show load plugin dialog"""
        plugin_file = filedialog.askopenfilename(
            title="Load Plugin",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if plugin_file:
            if self.plugin_manager.load_plugin(plugin_file):
                self.update_plugin_list()
                self.update_plugins_menu()
                messagebox.showinfo("Success", f"Plugin loaded successfully!")
            else:
                messagebox.showerror("Error", "Failed to load plugin!")
                
    def unload_selected_plugin(self):
        """Unload selected plugin"""
        selection = self.plugins_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plugin to unload.")
            return
            
        plugin_name = self.plugins_tree.item(selection[0], 'text')
        
        if messagebox.askyesno("Confirm", f"Unload plugin '{plugin_name}'?"):
            self.plugin_manager.unload_plugin(plugin_name)
            self.update_plugin_list()
            self.update_plugins_menu()
            
    def reload_plugins(self):
        """Reload all plugins"""
        # Unload all plugins
        for plugin_name in list(self.plugin_manager.plugins.keys()):
            self.plugin_manager.unload_plugin(plugin_name)
            
        # Reload all plugins
        self.plugin_manager.load_all_plugins()
        self.update_plugin_list()
        self.update_plugins_menu()
        
        messagebox.showinfo("Success", "All plugins reloaded!")
        
    def update_plugin_list(self):
        """Update the plugin list display"""
        # Clear existing items
        for item in self.plugins_tree.get_children():
            self.plugins_tree.delete(item)
            
        # Add loaded plugins
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            self.plugins_tree.insert('', 'end', 
                                   text=plugin_name,
                                   values=(plugin.version, "Loaded", plugin.description))
                                   
    # Automation methods
    def load_automation_rules(self):
        """Load automation rules into the tree"""
        # Clear existing items
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        # Load rules from automation engine
        for rule_id, rule in self.automation_engine.rules.items():
            status = "Enabled" if rule.enabled else "Disabled"
            self.rules_tree.insert('', 'end',
                                 text=rule.name,
                                 values=(rule.trigger, rule.condition, status))
                                 
    def add_automation_rule(self):
        """Add new automation rule"""
        self.show_rule_editor()
        
    def edit_automation_rule(self):
        """Edit selected automation rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to edit.")
            return
            
        rule_name = self.rules_tree.item(selection[0], 'text')
        # Find rule by name and edit
        self.show_rule_editor(rule_name)
        
    def delete_automation_rule(self):
        """Delete selected automation rule"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a rule to delete.")
            return
            
        rule_name = self.rules_tree.item(selection[0], 'text')
        
        if messagebox.askyesno("Confirm", f"Delete rule '{rule_name}'?"):
            # Find and delete rule
            for rule_id, rule in self.automation_engine.rules.items():
                if rule.name == rule_name:
                    del self.automation_engine.rules[rule_id]
                    break
                    
            self.load_automation_rules()
            
    def show_rule_editor(self, rule_name=None):
        """Show rule editor dialog"""
        # Create rule editor window
        editor = tk.Toplevel(self.root)
        editor.title("Automation Rule Editor")
        editor.geometry("500x400")
        editor.configure(bg="#1e1e1e")
        
        # Rule name
        ttk.Label(editor, text="Rule Name:").pack(anchor='w', padx=10, pady=5)
        name_entry = ttk.Entry(editor, width=50)
        name_entry.pack(padx=10, pady=5)
        
        # Trigger type
        ttk.Label(editor, text="Trigger Type:").pack(anchor='w', padx=10, pady=5)
        trigger_combo = ttk.Combobox(editor, values=["condition", "time", "event"])
        trigger_combo.pack(padx=10, pady=5)
        
        # Condition
        ttk.Label(editor, text="Condition:").pack(anchor='w', padx=10, pady=5)
        condition_text = scrolledtext.ScrolledText(editor, height=5, width=60)
        condition_text.pack(padx=10, pady=5)
        
        # Action
        ttk.Label(editor, text="Action:").pack(anchor='w', padx=10, pady=5)
        action_text = scrolledtext.ScrolledText(editor, height=5, width=60)
        action_text.pack(padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(editor)
        button_frame.pack(pady=10)
        
        def save_rule():
            rule = AutomationRule(
                id=f"rule_{int(time.time())}",
                name=name_entry.get(),
                trigger=trigger_combo.get(),
                condition=condition_text.get(1.0, tk.END).strip(),
                action=action_text.get(1.0, tk.END).strip()
            )
            
            self.automation_engine.add_rule(rule)
            self.load_automation_rules()
            editor.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_rule).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=editor.destroy).pack(side='left', padx=5)
        
    # Security methods
    def run_security_scan(self):
        """Run comprehensive security scan"""
        self.log_activity("🔒 Starting security scan...", "info")
        
        def scan_thread():
            try:
                results = self.security_manager.run_security_scan()
                
                # Format results for display
                report = f"Security Scan Results - {results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                report += "=" * 50 + "\n\n"
                
                # File integrity results
                if results['file_integrity']:
                    report += "FILE INTEGRITY VIOLATIONS:\n"
                    for violation in results['file_integrity']:
                        report += f"- {violation}\n"
                    report += "\n"
                    
                # Suspicious processes
                if results['suspicious_processes']:
                    report += "SUSPICIOUS PROCESSES:\n"
                    for process in results['suspicious_processes']:
                        report += f"- PID {process['pid']}: {process['name']} ({process['user']})\n"
                    report += "\n"
                    
                # Network connections
                if results['network_connections']:
                    report += "UNUSUAL NETWORK CONNECTIONS:\n"
                    for conn in results['network_connections']:
                        report += f"- Port {conn['port']} ({conn['address']}) - {conn['process']}\n"
                    report += "\n"
                    
                if not any([results['file_integrity'], results['suspicious_processes'], results['network_connections']]):
                    report += "✅ No security issues detected.\n"
                    
                # Update security log
                self.root.after(0, lambda: self.update_security_log(report))
                self.root.after(0, lambda: self.log_activity("🔒 Security scan completed", "success"))
                
            except Exception as e:
                error_msg = f"Error during security scan: {e}"
                self.root.after(0, lambda: self.log_activity(error_msg, "error"))
                
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def update_security_log(self, content):
        """Update security log display"""
        self.security_log.insert(tk.END, content + "\n" + "="*50 + "\n\n")
        self.security_log.see(tk.END)
        
    def check_file_integrity(self):
        """Check file integrity"""
        self.log_activity("🔍 Checking file integrity...", "info")
        
        def check_thread():
            try:
                violations = self.security_manager.check_file_integrity()
                
                if violations:
                    report = "FILE INTEGRITY VIOLATIONS:\n"
                    for violation in violations:
                        report += f"- {violation}\n"
                else:
                    report = "✅ File integrity check passed - no violations detected.\n"
                    
                self.root.after(0, lambda: self.update_security_log(report))
                self.root.after(0, lambda: self.log_activity("🔍 File integrity check completed", "success"))
                
            except Exception as e:
                error_msg = f"Error checking file integrity: {e}"
                self.root.after(0, lambda: self.log_activity(error_msg, "error"))
                
        threading.Thread(target=check_thread, daemon=True).start()
        
    def monitor_processes(self):
        """Monitor processes for suspicious activity"""
        self.log_activity("👁️ Monitoring processes...", "info")
        
        def monitor_thread():
            try:
                suspicious = self.security_manager.check_suspicious_processes()
                
                if suspicious:
                    report = "SUSPICIOUS PROCESSES DETECTED:\n"
                    for process in suspicious:
                        report += f"- PID {process['pid']}: {process['name']} ({process['user']})\n"
                        report += f"  Command: {process['cmdline']}\n\n"
                else:
                    report = "✅ No suspicious processes detected.\n"
                    
                self.root.after(0, lambda: self.update_security_log(report))
                self.root.after(0, lambda: self.log_activity("👁️ Process monitoring completed", "success"))
                
            except Exception as e:
                error_msg = f"Error monitoring processes: {e}"
                self.root.after(0, lambda: self.log_activity(error_msg, "error"))
                
        threading.Thread(target=monitor_thread, daemon=True).start()
        
    # System information and reporting
    def show_system_info(self):
        """Show detailed system information"""
        info_window = tk.Toplevel(self.root)
        info_window.title("System Information")
        info_window.geometry("800x600")
        info_window.configure(bg="#1e1e1e")
        
        info_text = scrolledtext.ScrolledText(info_window, font=('Consolas', 10),
                                             bg="#2d2d2d", fg="white")
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Generate system information
        def generate_info():
            try:
                info = "ADVANCED SYSTEM INFORMATION\n"
                info += "=" * 50 + "\n\n"
                
                # Basic system info
                import platform
                info += f"System: {platform.system()} {platform.release()}\n"
                info += f"Architecture: {platform.machine()}\n"
                info += f"Processor: {platform.processor()}\n"
                info += f"Python: {platform.python_version()}\n"
                info += f"Hostname: {platform.node()}\n\n"
                
                if PSUTIL_AVAILABLE:
                    # CPU information
                    info += "CPU INFORMATION:\n"
                    info += f"Physical cores: {psutil.cpu_count(logical=False)}\n"
                    info += f"Logical cores: {psutil.cpu_count(logical=True)}\n"
                    info += f"Current usage: {psutil.cpu_percent(interval=1):.1f}%\n"
                    
                    # Memory information
                    memory = psutil.virtual_memory()
                    info += f"\nMEMORY INFORMATION:\n"
                    info += f"Total: {memory.total / (1024**3):.2f} GB\n"
                    info += f"Available: {memory.available / (1024**3):.2f} GB\n"
                    info += f"Used: {memory.percent:.1f}%\n"
                    
                    # Disk information
                    info += f"\nDISK INFORMATION:\n"
                    for partition in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            info += f"Device: {partition.device}\n"
                            info += f"  Mountpoint: {partition.mountpoint}\n"
                            info += f"  File system: {partition.fstype}\n"
                            info += f"  Total: {usage.total / (1024**3):.2f} GB\n"
                            info += f"  Used: {usage.used / (1024**3):.2f} GB ({usage.used / usage.total * 100:.1f}%)\n"
                            info += f"  Free: {usage.free / (1024**3):.2f} GB\n\n"
                        except PermissionError:
                            continue
                            
                    # Network information
                    info += "NETWORK INFORMATION:\n"
                    for interface, addrs in psutil.net_if_addrs().items():
                        info += f"Interface: {interface}\n"
                        for addr in addrs:
                            info += f"  {addr.family.name}: {addr.address}\n"
                        info += "\n"
                        
                info_text.insert(tk.END, info)
                
            except Exception as e:
                info_text.insert(tk.END, f"Error generating system information: {e}")
                
        threading.Thread(target=generate_info, daemon=True).start()
        
    def show_performance_monitor(self):
        """Show performance monitoring window"""
        perf_window = tk.Toplevel(self.root)
        perf_window.title("Performance Monitor")
        perf_window.geometry("900x700")
        perf_window.configure(bg="#1e1e1e")
        
        # Create performance display
        perf_text = scrolledtext.ScrolledText(perf_window, font=('Consolas', 9),
                                             bg="#2d2d2d", fg="white")
        perf_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Performance monitoring loop
        def update_performance():
            if not perf_window.winfo_exists():
                return
                
            try:
                if PSUTIL_AVAILABLE:
                    perf_text.delete(1.0, tk.END)
                    
                    # Current time
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    perf_text.insert(tk.END, f"Performance Monitor - {current_time}\n")
                    perf_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    # CPU usage per core
                    cpu_percents = psutil.cpu_percent(interval=1, percpu=True)
                    perf_text.insert(tk.END, "CPU Usage per Core:\n")
                    for i, percent in enumerate(cpu_percents):
                        bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
                        perf_text.insert(tk.END, f"Core {i:2d}: [{bar}] {percent:5.1f}%\n")
                    
                    # Memory details
                    memory = psutil.virtual_memory()
                    swap = psutil.swap_memory()
                    perf_text.insert(tk.END, f"\nMemory Usage:\n")
                    perf_text.insert(tk.END, f"Physical: {memory.percent:5.1f}% ({memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB)\n")
                    perf_text.insert(tk.END, f"Swap:     {swap.percent:5.1f}% ({swap.used / (1024**3):.2f} GB / {swap.total / (1024**3):.2f} GB)\n")
                    
                    # Top processes by CPU
                    perf_text.insert(tk.END, f"\nTop Processes by CPU:\n")
                    perf_text.insert(tk.END, f"{'PID':>8} {'Name':<20} {'CPU%':>8} {'Memory%':>10}\n")
                    perf_text.insert(tk.END, "-" * 50 + "\n")
                    
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                        try:
                            processes.append(proc.info)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
                    # Sort by CPU usage
                    processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                    
                    for proc in processes[:10]:  # Top 10
                        perf_text.insert(tk.END, f"{proc['pid']:>8} {proc['name'][:20]:<20} {proc['cpu_percent'] or 0:>7.1f}% {proc['memory_percent'] or 0:>9.1f}%\n")
                        
                    # Network I/O
                    net_io = psutil.net_io_counters()
                    perf_text.insert(tk.END, f"\nNetwork I/O:\n")
                    perf_text.insert(tk.END, f"Bytes sent:     {net_io.bytes_sent / (1024**2):8.2f} MB\n")
                    perf_text.insert(tk.END, f"Bytes received: {net_io.bytes_recv / (1024**2):8.2f} MB\n")
                    
                    # Disk I/O
                    disk_io = psutil.disk_io_counters()
                    if disk_io:
                        perf_text.insert(tk.END, f"\nDisk I/O:\n")
                        perf_text.insert(tk.END, f"Read:  {disk_io.read_bytes / (1024**2):8.2f} MB\n")
                        perf_text.insert(tk.END, f"Write: {disk_io.write_bytes / (1024**2):8.2f} MB\n")
                        
            except Exception as e:
                perf_text.insert(tk.END, f"Error updating performance data: {e}\n")
                
            # Schedule next update
            perf_window.after(2000, update_performance)
            
        # Start performance monitoring
        update_performance()
        
    def generate_system_report(self):
        """Generate comprehensive system report"""
        self.log_activity("📊 Generating system report...", "info")
        
        def generate_report():
            try:
                report_path = Path.home() / f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(report_path, 'w') as f:
                    f.write("ADVANCED SYSTEM MANAGER - COMPREHENSIVE REPORT\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # System information
                    import platform
                    f.write("SYSTEM INFORMATION:\n")
                    f.write(f"OS: {platform.system()} {platform.release()}\n")
                    f.write(f"Architecture: {platform.machine()}\n")
                    f.write(f"Hostname: {platform.node()}\n")
                    f.write(f"Python: {platform.python_version()}\n\n")
                    
                    if PSUTIL_AVAILABLE:
                        # Current metrics
                        if self.current_metrics:
                            f.write("CURRENT SYSTEM METRICS:\n")
                            f.write(f"CPU Usage: {self.current_metrics.cpu_percent:.1f}%\n")
                            f.write(f"Memory Usage: {self.current_metrics.memory_percent:.1f}%\n")
                            f.write(f"Disk Usage: {self.current_metrics.disk_percent:.1f}%\n")
                            f.write(f"Load Average: {', '.join(f'{x:.2f}' for x in self.current_metrics.load_average)}\n")
                            f.write(f"Uptime: {str(self.current_metrics.uptime).split('.')[0]}\n")
                            f.write(f"Processes: {self.current_metrics.processes}\n\n")
                            
                        # Historical data
                        history = self.db_manager.get_metrics_history(24)  # Last 24 hours
                        if history:
                            f.write("HISTORICAL METRICS (Last 24 Hours):\n")
                            f.write(f"Total data points: {len(history)}\n")
                            
                            avg_cpu = sum(h['cpu_percent'] for h in history) / len(history)
                            avg_memory = sum(h['memory_percent'] for h in history) / len(history)
                            avg_disk = sum(h['disk_percent'] for h in history) / len(history)
                            
                            f.write(f"Average CPU: {avg_cpu:.1f}%\n")
                            f.write(f"Average Memory: {avg_memory:.1f}%\n")
                            f.write(f"Average Disk: {avg_disk:.1f}%\n\n")
                            
                    # Plugin information
                    f.write("LOADED PLUGINS:\n")
                    for plugin_name, plugin in self.plugin_manager.plugins.items():
                        f.write(f"- {plugin_name} v{plugin.version}: {plugin.description}\n")
                    f.write(f"\nTotal plugins loaded: {len(self.plugin_manager.plugins)}\n\n")
                    
                    # Automation rules
                    f.write("AUTOMATION RULES:\n")
                    for rule_id, rule in self.automation_engine.rules.items():
                        status = "Enabled" if rule.enabled else "Disabled"
                        f.write(f"- {rule.name} ({status}): {rule.trigger} -> {rule.action}\n")
                    f.write(f"\nTotal rules: {len(self.automation_engine.rules)}\n\n")
                    
                    # Configuration summary
                    f.write("CONFIGURATION SUMMARY:\n")
                    f.write(f"Monitoring interval: {self.config_manager.get('system.monitoring_interval')} seconds\n")
                    f.write(f"CPU alert threshold: {self.config_manager.get('system.cpu_alert_threshold')}%\n")
                    f.write(f"Memory alert threshold: {self.config_manager.get('system.memory_alert_threshold')}%\n")
                    f.write(f"Disk alert threshold: {self.config_manager.get('system.disk_alert_threshold')}%\n")
                    f.write(f"Security monitoring: {self.config_manager.get('security.file_integrity_check')}\n")
                    f.write(f"Automation enabled: {self.config_manager.get('automation.enabled')}\n\n")
                    
                self.root.after(0, lambda: self.log_activity(f"📊 Report generated: {report_path}", "success"))
                self.root.after(0, lambda: messagebox.showinfo("Report Generated", f"System report saved to:\n{report_path}"))
                
            except Exception as e:
                error_msg = f"Error generating report: {e}"
                self.root.after(0, lambda: self.log_activity(error_msg, "error"))
                
        threading.Thread(target=generate_report, daemon=True).start()
        
    def export_analytics_data(self):
        """Export analytics data to CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Export Analytics Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            def export_data():
                try:
                    import csv
                    
                    history = self.db_manager.get_metrics_history(24 * 7)  # Last week
                    
                    with open(file_path, 'w', newline='') as csvfile:
                        fieldnames = ['timestamp', 'cpu_percent', 'memory_percent', 'disk_percent', 
                                     'temperature', 'load_1min', 'load_5min', 'load_15min', 'processes']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for row in history:
                            writer.writerow({
                                'timestamp': row['timestamp'],
                                'cpu_percent': row['cpu_percent'],
                                'memory_percent': row['memory_percent'],
                                'disk_percent': row['disk_percent'],
                                'temperature': row['temperature'],
                                'load_1min': row['load_1min'],
                                'load_5min': row['load_5min'],
                                'load_15min': row['load_15min'],
                                'processes': row['processes']
                            })
                            
                    self.root.after(0, lambda: self.log_activity(f"📊 Analytics data exported: {file_path}", "success"))
                    self.root.after(0, lambda: messagebox.showinfo("Export Complete", f"Data exported to:\n{file_path}"))
                    
                except Exception as e:
                    error_msg = f"Error exporting data: {e}"
                    self.root.after(0, lambda: self.log_activity(error_msg, "error"))
                    
            threading.Thread(target=export_data, daemon=True).start()
            
    # Configuration methods
    def save_settings(self):
        """Save current settings"""
        try:
            # Update configuration with current UI values
            self.config_manager.set('system.monitoring_interval', self.monitoring_interval.get())
            
            self.log_activity("⚙️ Settings saved successfully", "success")
            messagebox.showinfo("Settings Saved", "Configuration has been saved successfully!")
            
        except Exception as e:
            error_msg = f"Error saving settings: {e}"
            self.log_activity(error_msg, "error")
            messagebox.showerror("Error", error_msg)
            
    def export_config(self):
        """Export configuration to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(self.config_manager.config, f, indent=2)
                else:
                    with open(file_path, 'w') as f:
                        yaml.dump(self.config_manager.config, f, default_flow_style=False, indent=2)
                        
                self.log_activity(f"⚙️ Configuration exported: {file_path}", "success")
                messagebox.showinfo("Export Complete", f"Configuration exported to:\n{file_path}")
                
            except Exception as e:
                error_msg = f"Error exporting configuration: {e}"
                self.log_activity(error_msg, "error")
                messagebox.showerror("Error", error_msg)
                
    def import_config(self):
        """Import configuration from file"""
        file_path = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("YAML files", "*.yaml"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                else:
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                        
                self.config_manager.config = config
                self.config_manager.save_configuration()
                
                self.log_activity(f"⚙️ Configuration imported: {file_path}", "success")
                messagebox.showinfo("Import Complete", "Configuration imported successfully!\nRestart may be required for some changes.")
                
            except Exception as e:
                error_msg = f"Error importing configuration: {e}"
                self.log_activity(error_msg, "error")
                messagebox.showerror("Error", error_msg)
                
    def show_documentation(self):
        """Show documentation window"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("800x600")
        doc_window.configure(bg="#1e1e1e")
        
        doc_text = scrolledtext.ScrolledText(doc_window, font=('Segoe UI', 10),
                                            bg="#2d2d2d", fg="white", wrap=tk.WORD)
        doc_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        documentation = """
ADVANCED SYSTEM MANAGER v3.0 - DOCUMENTATION

OVERVIEW:
The Advanced System Manager is a comprehensive Linux system management tool with plugin architecture, advanced automation, and security monitoring capabilities.

KEY FEATURES:

1. PLUGIN ARCHITECTURE:
   - Extensible plugin system for custom functionality
   - Dynamic plugin loading and unloading
   - Plugin-specific menu integration
   - Example plugins included for network monitoring and system hardening

2. ADVANCED AUTOMATION:
   - Rule-based automation engine
   - Time-based, condition-based, and event-based triggers
   - Custom action execution
   - Automation rule management interface

3. SECURITY MONITORING:
   - File integrity checking
   - Suspicious process detection
   - Network connection monitoring
   - Security event logging and analysis

4. COMPREHENSIVE MONITORING:
   - Real-time system metrics collection
   - Historical data storage and analysis
   - Performance monitoring with detailed process information
   - System health alerts and notifications

5. CONFIGURATION MANAGEMENT:
   - YAML-based configuration system
   - Import/export configuration
   - Per-plugin settings storage
   - Advanced configuration options

PLUGIN DEVELOPMENT:

To create a plugin, inherit from PluginInterface and implement:
- name: Plugin name
- version: Plugin version
- description: Plugin description
- initialize(manager): Initialize plugin
- cleanup(): Cleanup resources
- get_menu_items(): Return menu items

Example plugin structure:
```python
class MyPlugin(PluginInterface):
    @property
    def name(self) -> str:
        return "My Plugin"
    
    def initialize(self, manager) -> bool:
        # Initialize plugin
        return True
```

AUTOMATION RULES:

Condition examples:
- cpu > 80 (CPU usage above 80%)
- memory > 85 (Memory usage above 85%)
- disk > 90 (Disk usage above 90%)
- uptime_hours > 24 (System uptime over 24 hours)

Action examples:
- command:sudo apt update
- cleanup:cache
- notification:High CPU usage detected

SECURITY FEATURES:

The security manager monitors:
- Critical system files (/etc/passwd, /etc/shadow, etc.)
- Running processes for suspicious patterns
- Network connections on unusual ports
- System changes and modifications

KEYBOARD SHORTCUTS:

Ctrl+R - Refresh all data
F1 - Show this documentation
F5 - Refresh monitoring data
Ctrl+S - Save settings
Ctrl+E - Export configuration

CONFIGURATION:

The system uses YAML configuration files stored in:
~/.advanced-system-manager/advanced_config.yaml

Key configuration sections:
- system: Monitoring and alert settings
- cleanup: Cleanup behavior settings
- automation: Automation engine settings
- security: Security monitoring settings
- plugins: Plugin management settings
- ui: User interface settings

DATABASE:

System data is stored in SQLite database:
~/.advanced-system-manager/system_manager.db

Tables include:
- metrics_history: System metrics over time
- cleanup_history: Cleanup operation history
- automation_rules: Automation rule definitions
- security_events: Security event log
- plugin_settings: Plugin-specific settings

TROUBLESHOOTING:

1. Plugin loading issues:
   - Check plugin syntax and PluginInterface implementation
   - Review error logs in /tmp/advanced-system-manager.log
   - Ensure plugin dependencies are installed

2. Monitoring not working:
   - Install psutil: sudo apt install python3-psutil
   - Check monitoring interval in settings
   - Verify system permissions

3. Automation rules not firing:
   - Check rule conditions and syntax
   - Verify automation is enabled in settings
   - Review automation logs

4. Security scan issues:
   - Ensure sufficient permissions for file access
   - Check monitored file paths exist
   - Review security settings configuration

For more information and support, check the logs in /tmp/advanced-system-manager.log
"""
        
        doc_text.insert(1.0, documentation)
        doc_text.configure(state='disabled')
        
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
Advanced System Manager v3.0

A comprehensive Linux system management tool with:
- Plugin architecture for extensibility
- Advanced automation and scheduling
- Security monitoring and integrity checking
- Real-time system monitoring and analytics
- Configuration management and reporting

Developed with Python {sys.version.split()[0]}
SQLite database for persistent storage
YAML configuration management

Licensed under MIT License
© 2024 Advanced System Manager Project
"""
        messagebox.showinfo("About Advanced System Manager", about_text)
        
    def on_shutdown(self):
        """Handle application shutdown"""
        try:
            logger.info("Shutting down Advanced System Manager...")
            
            # Stop monitoring
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
                
            # Stop automation engine
            self.automation_engine.stop()
            
            # Cleanup plugins
            for plugin_name in list(self.plugin_manager.plugins.keys()):
                self.plugin_manager.unload_plugin(plugin_name)
                
            logger.info("Shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
        finally:
            self.root.quit()
            self.root.destroy()

def main():
    """Main application entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            messagebox.showerror("Python Version Error", 
                               "This application requires Python 3.7 or higher!")
            return
            
        # Create and run the advanced GUI
        root = tk.Tk()
        app = AdvancedSystemManager(root)
        
        # Center window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Handle signals
        def signal_handler(sig, frame):
            app.on_shutdown()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting Advanced System Manager v3.0")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        messageback.showerror("Fatal Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()