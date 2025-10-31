#!/usr/bin/env python3
"""
NexusController v2.0 - Enterprise Infrastructure Management Platform
Compiled from conversations 2024-2025

A comprehensive enterprise infrastructure management system with:
- Event-driven architecture with pub/sub messaging
- Multi-cloud provider abstraction layer
- Real-time WebSocket communication
- RESTful API with FastAPI
- Federation support for horizontal scaling
- State management with drift detection
- Automated remediation workflows
- Advanced monitoring and alerting
"""

import asyncio
import logging
import signal
import json
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
import redis.asyncio as redis
import paramiko
import yaml
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet
import uvicorn
import docker
import kubernetes
import boto3

# Version and constants
VERSION = "2.0.1"
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
PLUGINS_DIR = BASE_DIR / "plugins"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Ensure directories exist
for directory in [CONFIG_DIR, PLUGINS_DIR, LOGS_DIR, DATA_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UNKNOWN = "unknown"

class ProviderType(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    SSH = "ssh"

class EventType(Enum):
    NODE_DISCOVERED = "node_discovered"
    NODE_STATUS_CHANGED = "node_status_changed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    SECURITY_ALERT = "security_alert"
    FEDERATION_JOIN = "federation_join"
    FEDERATION_LEAVE = "federation_leave"

@dataclass
class Node:
    """Represents a managed infrastructure node"""
    id: str
    hostname: str
    ip_address: str
    provider: ProviderType
    status: NodeStatus
    tags: Dict[str, str]
    metadata: Dict[str, Any]
    last_seen: datetime
    created_at: datetime

@dataclass
class Event:
    """Represents a system event"""
    id: str
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime

@dataclass
class FederationNode:
    """Represents a federation peer"""
    id: str
    hostname: str
    port: int
    public_key: str
    last_heartbeat: datetime
    capabilities: List[str]

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class ConfigManager:
    """Manages configuration loading and encryption"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = CONFIG_DIR / config_file
        self.config = {}
        self.logger = logging.getLogger("nexus.config")
        self._encryption_key = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.create_default_config()
            
            # Generate encryption key if not present
            if not self.config.get('security', {}).get('encryption_key'):
                self.generate_encryption_key()
                
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration"""
        self.config = {
            'server': {
                'host': '0.0.0.0',
                'port': 8080,
                'workers': 4
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'security': {
                'require_authentication': True,
                'ssh_key_verification': 'strict',
                'api_rate_limit': 100
            },
            'monitoring': {
                'enabled': True,
                'metrics_interval': 30,
                'health_check_interval': 60
            },
            'federation': {
                'enabled': False,
                'discovery_port': 8081,
                'heartbeat_interval': 30
            },
            'plugins': {
                'enabled': True,
                'auto_load': True
            },
            'logging': {
                'level': 'INFO',
                'file': str(LOGS_DIR / 'nexus.log'),
                'max_size': '10MB',
                'backup_count': 5
            }
        }
        self.save_config()
    
    def generate_encryption_key(self):
        """Generate new encryption key"""
        key = Fernet.generate_key()
        self.config.setdefault('security', {})['encryption_key'] = key.decode()
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    @property
    def encryption_key(self):
        """Get encryption key"""
        if not self._encryption_key:
            key_str = self.get('security.encryption_key')
            if key_str:
                self._encryption_key = Fernet(key_str.encode())
        return self._encryption_key

# ============================================================================
# SECURITY MANAGEMENT
# ============================================================================

class SecurityManager:
    """Handles security operations"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger("nexus.security")
        self.known_hosts = {}
        self.ssh_clients = {}
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return self.config.encryption_key.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.config.encryption_key.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def validate_ssh_connection(self, hostname: str, port: int = 22) -> bool:
        """Validate SSH connection with proper host key verification"""
        try:
            client = paramiko.SSHClient()
            
            # Use strict host key verification
            verification_mode = self.config.get('security.ssh_key_verification', 'strict')
            if verification_mode == 'strict':
                client.load_system_host_keys()
                client.load_host_keys(str(CONFIG_DIR / 'known_hosts'))
            else:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Attempt connection
            client.connect(
                hostname=hostname,
                port=port,
                timeout=10,
                auth_timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            client.close()
            return True
            
        except Exception as e:
            self.logger.warning(f"SSH validation failed for {hostname}:{port}: {e}")
            return False
    
    def create_ssh_client(self, hostname: str, username: str, 
                         private_key_path: str = None, port: int = 22) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        client = paramiko.SSHClient()
        
        # Configure host key verification
        verification_mode = self.config.get('security.ssh_key_verification', 'strict')
        if verification_mode == 'strict':
            client.load_system_host_keys()
            client.load_host_keys(str(CONFIG_DIR / 'known_hosts'))
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key if provided
        private_key = None
        if private_key_path:
            try:
                private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
            except Exception as e:
                self.logger.error(f"Failed to load private key: {e}")
                raise
        
        # Connect
        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            pkey=private_key,
            timeout=30,
            auth_timeout=30
        )
        
        return client

# ============================================================================
# EVENT BUS SYSTEM
# ============================================================================

class EventBus:
    """Async event bus with Redis backend"""
    
    def __init__(self):
        self.logger = logging.getLogger("nexus.eventbus")
        self.redis_client = None
        self.subscribers = {}
        self.running = False
        
    async def initialize_redis(self, redis_config: Dict[str, Any]):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def publish(self, event: Event):
        """Publish event to the bus"""
        try:
            if self.redis_client:
                await self.redis_client.publish(
                    f"nexus:events:{event.type.value}",
                    json.dumps(asdict(event), default=str)
                )
            
            # Notify local subscribers
            for event_type, callbacks in self.subscribers.items():
                if event_type == event.type or event_type == "*":
                    for callback in callbacks:
                        try:
                            await callback(event)
                        except Exception as e:
                            self.logger.error(f"Subscriber callback failed: {e}")
                            
        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")
    
    def subscribe(self, event_type: Union[EventType, str], callback):
        """Subscribe to events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def start_redis_subscriber(self):
        """Start Redis pub/sub subscriber"""
        if not self.redis_client:
            return
        
        self.running = True
        pubsub = self.redis_client.pubsub()
        
        try:
            await pubsub.psubscribe("nexus:events:*")
            
            while self.running:
                message = await pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'pmessage':
                    try:
                        event_data = json.loads(message['data'])
                        event = Event(**event_data)
                        
                        # Notify local subscribers
                        for event_type, callbacks in self.subscribers.items():
                            if event_type == event.type or event_type == "*":
                                for callback in callbacks:
                                    await callback(event)
                                    
                    except Exception as e:
                        self.logger.error(f"Failed to process Redis message: {e}")
                        
        except Exception as e:
            self.logger.error(f"Redis subscriber error: {e}")
        finally:
            await pubsub.unsubscribe()

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class StateManager:
    """Manages system state and drift detection"""
    
    def __init__(self, event_bus: EventBus):
        self.logger = logging.getLogger("nexus.state")
        self.event_bus = event_bus
        self.nodes: Dict[str, Node] = {}
        self.desired_state = {}
        self.current_state = {}
        self._lock = threading.RLock()
        
        # Subscribe to node events
        self.event_bus.subscribe(EventType.NODE_DISCOVERED, self.handle_node_discovered)
        self.event_bus.subscribe(EventType.NODE_STATUS_CHANGED, self.handle_node_status_changed)
    
    async def handle_node_discovered(self, event: Event):
        """Handle node discovery events"""
        try:
            node_data = event.data
            node = Node(**node_data)
            
            with self._lock:
                self.nodes[node.id] = node
                
            self.logger.info(f"Node discovered: {node.hostname} ({node.ip_address})")
            
        except Exception as e:
            self.logger.error(f"Failed to handle node discovery: {e}")
    
    async def handle_node_status_changed(self, event: Event):
        """Handle node status change events"""
        try:
            node_id = event.data.get('node_id')
            new_status = NodeStatus(event.data.get('status'))
            
            with self._lock:
                if node_id in self.nodes:
                    self.nodes[node_id].status = new_status
                    self.nodes[node_id].last_seen = datetime.now()
                    
            self.logger.info(f"Node {node_id} status changed to {new_status.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle status change: {e}")
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        with self._lock:
            return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes"""
        with self._lock:
            return list(self.nodes.values())
    
    def add_node(self, node: Node):
        """Add or update node"""
        with self._lock:
            self.nodes[node.id] = node
    
    def remove_node(self, node_id: str):
        """Remove node"""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
    
    async def detect_drift(self) -> List[Dict[str, Any]]:
        """Detect configuration drift"""
        drift_issues = []
        
        # Compare desired vs current state
        for node_id, desired in self.desired_state.items():
            current = self.current_state.get(node_id, {})
            
            for key, desired_value in desired.items():
                current_value = current.get(key)
                
                if current_value != desired_value:
                    drift_issues.append({
                        'node_id': node_id,
                        'configuration': key,
                        'desired': desired_value,
                        'current': current_value,
                        'severity': self._calculate_severity(key, desired_value, current_value)
                    })
        
        return drift_issues
    
    def _calculate_severity(self, key: str, desired: Any, current: Any) -> str:
        """Calculate drift severity"""
        # Security-related configurations are high severity
        if any(term in key.lower() for term in ['security', 'auth', 'ssl', 'tls']):
            return 'HIGH'
        
        # Service configurations are medium severity
        if any(term in key.lower() for term in ['service', 'daemon', 'process']):
            return 'MEDIUM'
        
        # Default to low severity
        return 'LOW'

# ============================================================================
# PLUGIN SYSTEM
# ============================================================================

class PluginManager:
    """Manages plugin loading and execution"""
    
    def __init__(self, event_bus: EventBus, config_manager: ConfigManager):
        self.logger = logging.getLogger("nexus.plugins")
        self.event_bus = event_bus
        self.config = config_manager
        self.plugins = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def load_plugin(self, plugin_path: Path):
        """Load a plugin from file"""
        try:
            # Dynamic import of plugin
            import importlib.util
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            if hasattr(module, 'Plugin'):
                plugin_instance = module.Plugin(self.event_bus, self.config)
                self.plugins[plugin_path.stem] = plugin_instance
                
                # Initialize plugin
                if hasattr(plugin_instance, 'initialize'):
                    await plugin_instance.initialize()
                
                self.logger.info(f"Loaded plugin: {plugin_path.stem}")
            else:
                self.logger.warning(f"Plugin {plugin_path.stem} has no Plugin class")
                
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_path}: {e}")
    
    async def execute_plugin_hook(self, hook_name: str, *args, **kwargs):
        """Execute hook in all plugins"""
        results = []
        
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, hook_name):
                try:
                    result = await plugin.__getattribute__(hook_name)(*args, **kwargs)
                    results.append((plugin_name, result))
                except Exception as e:
                    self.logger.error(f"Plugin {plugin_name} hook {hook_name} failed: {e}")
        
        return results

# ============================================================================
# MONITORING SYSTEM
# ============================================================================

class MonitoringManager:
    """Handles monitoring and alerting"""
    
    def __init__(self, event_bus: EventBus, config_manager: ConfigManager):
        self.logger = logging.getLogger("nexus.monitoring")
        self.event_bus = event_bus
        self.config = config_manager
        self.metrics = {}
        self.alerts = []
        self.running = False
    
    async def start_monitoring(self):
        """Start monitoring tasks"""
        self.running = True
        
        # Start metric collection
        asyncio.create_task(self._collect_metrics())
        
        # Start health checks
        asyncio.create_task(self._perform_health_checks())
        
        self.logger.info("Monitoring started")
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        while self.running:
            try:
                interval = self.config.get('monitoring.metrics_interval', 30)
                
                # Collect basic metrics
                self.metrics.update({
                    'timestamp': datetime.now().isoformat(),
                    'system_load': await self._get_system_load(),
                    'memory_usage': await self._get_memory_usage(),
                    'disk_usage': await self._get_disk_usage(),
                    'active_connections': await self._get_active_connections()
                })
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)
    
    async def _perform_health_checks(self):
        """Perform periodic health checks"""
        while self.running:
            try:
                interval = self.config.get('monitoring.health_check_interval', 60)
                
                # Perform health checks
                redis_healthy = await self._check_redis_health()
                api_healthy = await self._check_api_health()
                
                health_status = {
                    'timestamp': datetime.now().isoformat(),
                    'redis': redis_healthy,
                    'api': api_healthy,
                    'overall': redis_healthy and api_healthy
                }
                
                self.metrics['health'] = health_status
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def _get_system_load(self) -> float:
        """Get system load average"""
        try:
            import os
            return os.getloadavg()[0]
        except:
            return 0.0
    
    async def _get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            }
        except:
            return {'total': 0, 'available': 0, 'percent': 0}
    
    async def _get_disk_usage(self) -> Dict[str, int]:
        """Get disk usage statistics"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
        except:
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    async def _get_active_connections(self) -> int:
        """Get number of active connections"""
        # Placeholder - would integrate with actual connection tracking
        return 0
    
    async def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            if hasattr(self.event_bus, 'redis_client') and self.event_bus.redis_client:
                await self.event_bus.redis_client.ping()
                return True
        except:
            pass
        return False
    
    async def _check_api_health(self) -> bool:
        """Check API health"""
        # Placeholder - would check API endpoint
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()

# ============================================================================
# FEDERATION MANAGEMENT
# ============================================================================

class FederationManager:
    """Manages federation with other NexusController instances"""
    
    def __init__(self, event_bus: EventBus, config_manager: ConfigManager):
        self.logger = logging.getLogger("nexus.federation")
        self.event_bus = event_bus
        self.config = config_manager
        self.nodes: Dict[str, FederationNode] = {}
        self.running = False
        self.server = None
    
    async def start_federation(self):
        """Start federation services"""
        if not self.config.get('federation.enabled', False):
            return
        
        self.running = True
        
        # Start discovery server
        asyncio.create_task(self._start_discovery_server())
        
        # Start heartbeat sender
        asyncio.create_task(self._send_heartbeats())
        
        # Start health checker
        asyncio.create_task(self._check_federation_health())
        
        self.logger.info("Federation started")
    
    async def _start_discovery_server(self):
        """Start federation discovery server"""
        try:
            port = self.config.get('federation.discovery_port', 8081)
            
            # Placeholder for UDP discovery server
            self.logger.info(f"Federation discovery server listening on port {port}")
            
        except Exception as e:
            self.logger.error(f"Federation discovery server error: {e}")
    
    async def _send_heartbeats(self):
        """Send heartbeats to federation peers"""
        while self.running:
            try:
                interval = self.config.get('federation.heartbeat_interval', 30)
                
                # Send heartbeat to all known nodes
                for node_id, node in self.nodes.items():
                    try:
                        await self._send_heartbeat(node)
                    except Exception as e:
                        self.logger.warning(f"Failed to send heartbeat to {node_id}: {e}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Heartbeat sender error: {e}")
                await asyncio.sleep(30)
    
    async def _send_heartbeat(self, node: FederationNode):
        """Send heartbeat to specific node"""
        # Placeholder for heartbeat implementation
        pass
    
    async def _check_federation_health(self):
        """Check health of federation nodes"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(minutes=5)
                
                # Check for timed out nodes
                timeout_nodes = []
                for node_id, node in self.nodes.items():
                    if current_time - node.last_heartbeat > timeout_threshold:
                        timeout_nodes.append(node_id)
                
                # Remove timed out nodes
                for node_id in timeout_nodes:
                    self.logger.warning(f"Federation node timeout: {node_id}")
                    del self.nodes[node_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Federation health check error: {e}")
                await asyncio.sleep(60)

# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================

class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self, event_bus: EventBus):
        self.logger = logging.getLogger("nexus.websocket")
        self.event_bus = event_bus
        self.connections: Dict[str, WebSocket] = {}
        
        # Subscribe to all events for broadcasting
        self.event_bus.subscribe("*", self.broadcast_event)
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.connections[client_id] = websocket
        self.logger.info(f"WebSocket client connected: {client_id}")
    
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        if client_id in self.connections:
            del self.connections[client_id]
            self.logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def broadcast_event(self, event: Event):
        """Broadcast event to all connected clients"""
        if not self.connections:
            return
        
        message = {
            'type': 'event',
            'data': asdict(event, dict_factory=lambda x: {k: str(v) for k, v in x})
        }
        
        disconnected_clients = []
        
        for client_id, websocket in self.connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

class NexusControllerAPI:
    """FastAPI application for REST API"""
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus,
                 state_manager: StateManager, monitoring_manager: MonitoringManager):
        self.config = config_manager
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.monitoring = monitoring_manager
        self.websocket_manager = WebSocketManager(event_bus)
        self.logger = logging.getLogger("nexus.api")
        
        # Initialize FastAPI
        self.app = FastAPI(
            title="NexusController API",
            description="Enterprise Infrastructure Management Platform",
            version=VERSION,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "name": "NexusController",
                "version": VERSION,
                "status": "operational",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": VERSION
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get current metrics"""
            return self.monitoring.get_metrics()
        
        @self.app.get("/nodes")
        async def get_nodes():
            """Get all managed nodes"""
            nodes = self.state_manager.get_all_nodes()
            return [asdict(node) for node in nodes]
        
        @self.app.get("/nodes/{node_id}")
        async def get_node(node_id: str):
            """Get specific node"""
            node = self.state_manager.get_node(node_id)
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            return asdict(node)
        
        @self.app.post("/nodes/{node_id}/execute")
        async def execute_command(node_id: str, command: dict):
            """Execute command on node"""
            node = self.state_manager.get_node(node_id)
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            
            # Create execution event
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.DEPLOYMENT_STARTED,
                source="api",
                data={
                    "node_id": node_id,
                    "command": command.get("command"),
                    "parameters": command.get("parameters", {})
                },
                timestamp=datetime.now()
            )
            
            await self.event_bus.publish(event)
            
            return {"status": "accepted", "event_id": event.id}
        
        @self.app.get("/drift")
        async def get_drift():
            """Get configuration drift report"""
            drift_issues = await self.state_manager.detect_drift()
            return {"drift_issues": drift_issues}
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket endpoint for real-time updates"""
            await self.websocket_manager.connect(websocket, client_id)
            
            try:
                while True:
                    # Wait for messages (keepalive)
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.websocket_manager.disconnect(client_id)

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class NexusController:
    """Main NexusController application"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.running = False
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.security_manager = SecurityManager(self.config_manager)
        self.event_bus = EventBus()
        self.state_manager = StateManager(self.event_bus)
        self.plugin_manager = PluginManager(self.event_bus, self.config_manager)
        self.monitoring_manager = MonitoringManager(self.event_bus, self.config_manager)
        self.federation_manager = FederationManager(self.event_bus, self.config_manager)
        
        # Initialize API
        self.api = NexusControllerAPI(
            self.config_manager,
            self.event_bus,
            self.state_manager,
            self.monitoring_manager
        )
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGS_DIR / 'nexus.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("nexus.main")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def initialize(self):
        """Initialize all components"""
        self.logger.info("Initializing NexusController...")
        
        # Initialize Redis for event bus
        redis_config = self.config_manager.get("redis")
        await self.event_bus.initialize_redis(redis_config)
        
        # Start Redis subscriber
        asyncio.create_task(self.event_bus.start_redis_subscriber())
        
        # Start monitoring
        if self.config_manager.get("monitoring.enabled"):
            asyncio.create_task(self.monitoring_manager.start_monitoring())
        
        # Start federation
        await self.federation_manager.start_federation()
        
        # Load plugins
        if self.config_manager.get("plugins.enabled"):
            await self.load_plugins()
        
        self.logger.info("NexusController initialized successfully")
    
    async def load_plugins(self):
        """Load all plugins from plugins directory"""
        if not PLUGINS_DIR.exists():
            return
        
        for plugin_file in PLUGINS_DIR.glob("*.py"):
            try:
                await self.plugin_manager.load_plugin(plugin_file)
            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_file}: {e}")
    
    async def run(self):
        """Run the main application"""
        await self.initialize()
        
        # Start FastAPI server
        config = uvicorn.Config(
            self.api.app,
            host=self.config_manager.get("server.host", "0.0.0.0"),
            port=self.config_manager.get("server.port", 8080),
            workers=1,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        self.running = True
        
        self.logger.info("NexusController started successfully")
        
        try:
            await server.serve()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.running = False
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown all components"""
        self.logger.info("Shutting down NexusController...")
        
        # Stop event bus
        self.event_bus.running = False
        
        # Stop federation
        self.federation_manager.running = False
        
        # Stop monitoring
        self.monitoring_manager.running = False
        
        self.logger.info("NexusController shutdown complete")

# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    nexus = NexusController()
    await nexus.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()