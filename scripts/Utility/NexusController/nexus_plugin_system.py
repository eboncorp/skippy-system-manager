#!/usr/bin/env python3
"""
NexusController v2.0 Plugin Architecture System
Extensible plugin framework for cloud providers, monitoring, and custom integrations
"""

import os
import sys
import json
import asyncio
import logging
import importlib
import importlib.util
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Type, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from pathlib import Path
import inspect
import weakref

# Import event system
from nexus_event_system import Event, EventType, EventBus

class PluginType(Enum):
    """Types of plugins supported"""
    CLOUD_PROVIDER = "cloud_provider"
    MONITORING = "monitoring"
    BACKUP = "backup"
    NOTIFICATION = "notification"
    AUTHENTICATION = "authentication"
    DISCOVERY = "discovery"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    CUSTOM = "custom"

class PluginStatus(Enum):
    """Plugin status values"""
    UNKNOWN = "unknown"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class PluginMetadata:
    """Plugin metadata and configuration"""
    
    plugin_id: str
    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = "MIT"
    dependencies: List[str] = field(default_factory=list)
    min_nexus_version: str = "2.0.0"
    max_nexus_version: str = "3.0.0"
    configuration_schema: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['plugin_type'] = self.plugin_type.value
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary"""
        data = data.copy()
        data['plugin_type'] = PluginType(data['plugin_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metadata = None
        self.status = PluginStatus.UNKNOWN
        self.event_bus = None
        self.logger = logging.getLogger(f"nexus.plugin.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def plugin_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up plugin resources"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check plugin health"""
        pass
    
    def set_event_bus(self, event_bus: EventBus):
        """Set event bus for plugin communication"""
        self.event_bus = event_bus
    
    async def emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Emit event through event bus"""
        if self.event_bus:
            event = Event(
                event_type=event_type,
                source=f"plugin.{self.plugin_metadata.plugin_id}",
                data=data
            )
            await self.event_bus.publish(event)

class CloudProviderPlugin(PluginInterface):
    """Base class for cloud provider plugins"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with cloud provider"""
        pass
    
    @abstractmethod
    async def list_resources(self, resource_type: str = None) -> List[Dict[str, Any]]:
        """List cloud resources"""
        pass
    
    @abstractmethod
    async def create_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create cloud resource"""
        pass
    
    @abstractmethod
    async def update_resource(self, resource_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update cloud resource"""
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete cloud resource"""
        pass
    
    @abstractmethod
    async def get_resource_status(self, resource_id: str) -> Dict[str, Any]:
        """Get resource status"""
        pass

class MonitoringPlugin(PluginInterface):
    """Base class for monitoring plugins"""
    
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        pass
    
    @abstractmethod
    async def send_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Send alert/notification"""
        pass
    
    @abstractmethod
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        pass

class BackupPlugin(PluginInterface):
    """Base class for backup plugins"""
    
    @abstractmethod
    async def create_backup(self, source_path: str, backup_name: str) -> Dict[str, Any]:
        """Create backup"""
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_id: str, restore_path: str) -> bool:
        """Restore from backup"""
        pass
    
    @abstractmethod
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        pass
    
    @abstractmethod
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete backup"""
        pass

@dataclass
class PluginInstance:
    """Running plugin instance"""
    
    plugin_id: str
    metadata: PluginMetadata
    instance: PluginInterface
    status: PluginStatus = PluginStatus.LOADED
    config: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    loaded_at: datetime = field(default_factory=datetime.now)
    last_health_check: datetime = None
    health_status: Dict[str, Any] = field(default_factory=dict)

class PluginLoader:
    """Plugin loading and management"""
    
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Security: Set secure permissions
        os.chmod(self.plugin_dir, 0o700)
        
        self.loaded_modules = {}
        self._lock = threading.RLock()
    
    async def discover_plugins(self) -> List[PluginMetadata]:
        """Discover available plugins"""
        plugins = []
        
        # Look for Python files and packages
        for item in self.plugin_dir.iterdir():
            if item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                plugin = await self._load_plugin_metadata(item)
                if plugin:
                    plugins.append(plugin)
            elif item.is_dir() and not item.name.startswith('_'):
                # Look for __init__.py or plugin.py
                plugin_file = item / "plugin.py"
                if not plugin_file.exists():
                    plugin_file = item / "__init__.py"
                
                if plugin_file.exists():
                    plugin = await self._load_plugin_metadata(plugin_file)
                    if plugin:
                        plugins.append(plugin)
        
        return plugins
    
    async def _load_plugin_metadata(self, plugin_file: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from file"""
        try:
            # Look for metadata.json first
            metadata_file = plugin_file.parent / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                return PluginMetadata.from_dict(data)
            
            # Try to extract from Python file
            spec = importlib.util.spec_from_file_location("temp_plugin", plugin_file)
            module = importlib.util.module_from_spec(spec)
            
            # Execute module to get metadata
            spec.loader.exec_module(module)
            
            # Look for PLUGIN_METADATA constant
            if hasattr(module, 'PLUGIN_METADATA'):
                data = module.PLUGIN_METADATA
                if isinstance(data, dict):
                    return PluginMetadata.from_dict(data)
            
            # Look for plugin class with metadata
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, PluginInterface) and 
                    hasattr(obj, 'plugin_metadata')):
                    
                    # Instantiate to get metadata
                    instance = obj()
                    return instance.plugin_metadata
            
        except Exception as e:
            logging.error(f"Failed to load plugin metadata from {plugin_file}: {e}")
        
        return None
    
    async def load_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> Optional[PluginInterface]:
        """Load and instantiate plugin"""
        with self._lock:
            try:
                # Find plugin file
                plugin_file = self._find_plugin_file(plugin_id)
                if not plugin_file:
                    logging.error(f"Plugin file not found: {plugin_id}")
                    return None
                
                # Load module
                spec = importlib.util.spec_from_file_location(plugin_id, plugin_file)
                module = importlib.util.module_from_spec(spec)
                
                # Execute module
                spec.loader.exec_module(module)
                
                # Find plugin class
                plugin_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, PluginInterface) and 
                        obj != PluginInterface and
                        hasattr(obj, 'plugin_metadata')):
                        plugin_class = obj
                        break
                
                if not plugin_class:
                    logging.error(f"No plugin class found in {plugin_file}")
                    return None
                
                # Instantiate plugin
                instance = plugin_class(config)
                
                # Store loaded module
                self.loaded_modules[plugin_id] = module
                
                return instance
                
            except Exception as e:
                logging.error(f"Failed to load plugin {plugin_id}: {e}")
                return None
    
    def _find_plugin_file(self, plugin_id: str) -> Optional[Path]:
        """Find plugin file by ID"""
        # Try direct file
        plugin_file = self.plugin_dir / f"{plugin_id}.py"
        if plugin_file.exists():
            return plugin_file
        
        # Try package directory
        plugin_dir = self.plugin_dir / plugin_id
        if plugin_dir.is_dir():
            plugin_file = plugin_dir / "plugin.py"
            if plugin_file.exists():
                return plugin_file
            
            plugin_file = plugin_dir / "__init__.py"
            if plugin_file.exists():
                return plugin_file
        
        return None
    
    async def unload_plugin(self, plugin_id: str):
        """Unload plugin module"""
        with self._lock:
            if plugin_id in self.loaded_modules:
                del self.loaded_modules[plugin_id]
                
                # Remove from sys.modules if present
                module_names = [name for name in sys.modules.keys() 
                              if name.startswith(plugin_id)]
                for name in module_names:
                    del sys.modules[name]

class PluginManager:
    """Central plugin management system"""
    
    def __init__(self, plugin_dir: Path, event_bus: EventBus = None):
        self.plugin_dir = Path(plugin_dir)
        self.event_bus = event_bus
        self.loader = PluginLoader(plugin_dir)
        
        self.plugins = {}  # plugin_id -> PluginInstance
        self.plugin_types = defaultdict(list)  # plugin_type -> [plugin_ids]
        self.hooks = defaultdict(list)  # hook_name -> [plugin_ids]
        
        self._lock = threading.RLock()
        
        # Health check task
        self._running = False
        self._health_check_task = None
        
        logging.info(f"PluginManager initialized with directory: {plugin_dir}")
    
    async def start(self):
        """Start plugin manager"""
        self._running = True
        
        # Discover and load plugins
        await self.discover_plugins()
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logging.info("PluginManager started")
    
    async def stop(self):
        """Stop plugin manager"""
        self._running = False
        
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all plugins
        plugin_ids = list(self.plugins.keys())
        for plugin_id in plugin_ids:
            await self.unload_plugin(plugin_id)
        
        logging.info("PluginManager stopped")
    
    async def discover_plugins(self):
        """Discover and catalog available plugins"""
        try:
            discovered = await self.loader.discover_plugins()
            logging.info(f"Discovered {len(discovered)} plugins")
            
            for metadata in discovered:
                logging.info(f"Found plugin: {metadata.name} v{metadata.version} ({metadata.plugin_type.value})")
            
        except Exception as e:
            logging.error(f"Plugin discovery failed: {e}")
    
    async def load_plugin(self, plugin_id: str, config: Dict[str, Any] = None, auto_start: bool = True) -> bool:
        """Load and optionally start a plugin"""
        try:
            with self._lock:
                if plugin_id in self.plugins:
                    logging.warning(f"Plugin already loaded: {plugin_id}")
                    return True
            
            # Load plugin instance
            instance = await self.loader.load_plugin(plugin_id, config)
            if not instance:
                return False
            
            # Create plugin instance record
            plugin_instance = PluginInstance(
                plugin_id=plugin_id,
                metadata=instance.plugin_metadata,
                instance=instance,
                config=config or {}
            )
            
            # Set event bus
            instance.set_event_bus(self.event_bus)
            
            with self._lock:
                # Store plugin
                self.plugins[plugin_id] = plugin_instance
                
                # Index by type
                self.plugin_types[instance.plugin_metadata.plugin_type].append(plugin_id)
            
            # Initialize if auto-start
            if auto_start:
                success = await self.start_plugin(plugin_id)
                if not success:
                    await self.unload_plugin(plugin_id)
                    return False
            
            # Emit plugin loaded event
            if self.event_bus:
                event = Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="nexus.plugin_manager",
                    data={
                        'action': 'plugin_loaded',
                        'plugin_id': plugin_id,
                        'plugin_name': instance.plugin_metadata.name,
                        'plugin_type': instance.plugin_metadata.plugin_type.value
                    }
                )
                await self.event_bus.publish(event)
            
            logging.info(f"Plugin loaded: {plugin_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load plugin {plugin_id}: {e}")
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        try:
            with self._lock:
                if plugin_id not in self.plugins:
                    logging.warning(f"Plugin not loaded: {plugin_id}")
                    return True
                
                plugin_instance = self.plugins[plugin_id]
            
            # Stop plugin if active
            if plugin_instance.status == PluginStatus.ACTIVE:
                await self.stop_plugin(plugin_id)
            
            # Cleanup plugin
            try:
                await plugin_instance.instance.cleanup()
            except Exception as e:
                logging.error(f"Plugin cleanup failed for {plugin_id}: {e}")
            
            with self._lock:
                # Remove from indexes
                plugin_type = plugin_instance.metadata.plugin_type
                if plugin_id in self.plugin_types[plugin_type]:
                    self.plugin_types[plugin_type].remove(plugin_id)
                
                # Remove plugin
                del self.plugins[plugin_id]
            
            # Unload from loader
            await self.loader.unload_plugin(plugin_id)
            
            # Emit plugin unloaded event
            if self.event_bus:
                event = Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="nexus.plugin_manager",
                    data={
                        'action': 'plugin_unloaded',
                        'plugin_id': plugin_id
                    }
                )
                await self.event_bus.publish(event)
            
            logging.info(f"Plugin unloaded: {plugin_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    async def start_plugin(self, plugin_id: str) -> bool:
        """Start/activate a plugin"""
        try:
            with self._lock:
                if plugin_id not in self.plugins:
                    logging.error(f"Plugin not loaded: {plugin_id}")
                    return False
                
                plugin_instance = self.plugins[plugin_id]
            
            if plugin_instance.status == PluginStatus.ACTIVE:
                logging.warning(f"Plugin already active: {plugin_id}")
                return True
            
            # Initialize plugin
            plugin_instance.status = PluginStatus.LOADING
            success = await plugin_instance.instance.initialize()
            
            if success:
                plugin_instance.status = PluginStatus.ACTIVE
                plugin_instance.error_message = ""
                
                # Emit plugin started event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.CUSTOM_EVENT,
                        source="nexus.plugin_manager",
                        data={
                            'action': 'plugin_started',
                            'plugin_id': plugin_id
                        }
                    )
                    await self.event_bus.publish(event)
                
                logging.info(f"Plugin started: {plugin_id}")
                return True
            else:
                plugin_instance.status = PluginStatus.ERROR
                plugin_instance.error_message = "Plugin initialization failed"
                logging.error(f"Plugin initialization failed: {plugin_id}")
                return False
                
        except Exception as e:
            with self._lock:
                if plugin_id in self.plugins:
                    self.plugins[plugin_id].status = PluginStatus.ERROR
                    self.plugins[plugin_id].error_message = str(e)
            
            logging.error(f"Failed to start plugin {plugin_id}: {e}")
            return False
    
    async def stop_plugin(self, plugin_id: str) -> bool:
        """Stop/deactivate a plugin"""
        try:
            with self._lock:
                if plugin_id not in self.plugins:
                    logging.error(f"Plugin not loaded: {plugin_id}")
                    return False
                
                plugin_instance = self.plugins[plugin_id]
            
            if plugin_instance.status != PluginStatus.ACTIVE:
                logging.warning(f"Plugin not active: {plugin_id}")
                return True
            
            # Cleanup plugin
            success = await plugin_instance.instance.cleanup()
            
            plugin_instance.status = PluginStatus.INACTIVE if success else PluginStatus.ERROR
            
            # Emit plugin stopped event
            if self.event_bus:
                event = Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="nexus.plugin_manager",
                    data={
                        'action': 'plugin_stopped',
                        'plugin_id': plugin_id
                    }
                )
                await self.event_bus.publish(event)
            
            logging.info(f"Plugin stopped: {plugin_id}")
            return success
            
        except Exception as e:
            logging.error(f"Failed to stop plugin {plugin_id}: {e}")
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Get plugin instance"""
        with self._lock:
            if plugin_id in self.plugins:
                return self.plugins[plugin_id].instance
        return None
    
    def list_plugins(self, plugin_type: PluginType = None, status: PluginStatus = None) -> List[PluginInstance]:
        """List plugins with optional filtering"""
        with self._lock:
            plugins = list(self.plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """Get all active plugins of specific type"""
        plugins = []
        
        with self._lock:
            plugin_ids = self.plugin_types.get(plugin_type, [])
            
            for plugin_id in plugin_ids:
                if (plugin_id in self.plugins and 
                    self.plugins[plugin_id].status == PluginStatus.ACTIVE):
                    plugins.append(self.plugins[plugin_id].instance)
        
        return plugins
    
    async def _health_check_loop(self):
        """Background health checking for all plugins"""
        while self._running:
            try:
                plugin_ids = list(self.plugins.keys())
                
                for plugin_id in plugin_ids:
                    try:
                        with self._lock:
                            if plugin_id not in self.plugins:
                                continue
                            
                            plugin_instance = self.plugins[plugin_id]
                        
                        if plugin_instance.status == PluginStatus.ACTIVE:
                            # Run health check
                            health_status = await plugin_instance.instance.health_check()
                            
                            with self._lock:
                                plugin_instance.last_health_check = datetime.now()
                                plugin_instance.health_status = health_status
                                
                                # Check if plugin is unhealthy
                                if not health_status.get('healthy', True):
                                    plugin_instance.status = PluginStatus.ERROR
                                    plugin_instance.error_message = health_status.get('error', 'Health check failed')
                        
                    except Exception as e:
                        logging.error(f"Health check failed for plugin {plugin_id}: {e}")
                        
                        with self._lock:
                            if plugin_id in self.plugins:
                                self.plugins[plugin_id].status = PluginStatus.ERROR
                                self.plugins[plugin_id].error_message = str(e)
                
                # Wait before next health check round
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

# Built-in Plugins

class GoogleDriveCloudPlugin(CloudProviderPlugin):
    """Google Drive cloud provider plugin"""
    
    @property
    def plugin_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="google_drive",
            name="Google Drive Cloud Provider",
            version="1.0.0",
            plugin_type=PluginType.CLOUD_PROVIDER,
            description="Google Drive integration for file storage and backup",
            author="NexusController Team",
            dependencies=["google-auth", "google-api-python-client"],
            permissions=["cloud:read", "cloud:write", "backup:create"]
        )
    
    async def initialize(self) -> bool:
        """Initialize Google Drive plugin"""
        try:
            # Initialize Google Drive API client
            # This would normally set up OAuth credentials
            self.logger.info("Google Drive plugin initialized")
            return True
        except Exception as e:
            self.logger.error(f"Google Drive initialization failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup Google Drive plugin"""
        self.logger.info("Google Drive plugin cleaned up")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Google Drive connectivity"""
        try:
            # This would normally test API connectivity
            return {
                'healthy': True,
                'connectivity': 'ok',
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Google Drive"""
        # Implementation would handle OAuth flow
        return True
    
    async def list_resources(self, resource_type: str = None) -> List[Dict[str, Any]]:
        """List Google Drive files"""
        # Implementation would list files
        return []
    
    async def create_resource(self, resource_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create file/folder in Google Drive"""
        # Implementation would create resources
        return {}
    
    async def update_resource(self, resource_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update Google Drive resource"""
        # Implementation would update resources
        return {}
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete Google Drive resource"""
        # Implementation would delete resources
        return True
    
    async def get_resource_status(self, resource_id: str) -> Dict[str, Any]:
        """Get Google Drive resource status"""
        # Implementation would get resource status
        return {}

def main():
    """Demo of plugin system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create plugin directory
        plugin_dir = Path("/tmp/nexus_plugins")
        plugin_dir.mkdir(exist_ok=True)
        
        # Create plugin manager
        manager = PluginManager(plugin_dir)
        await manager.start()
        
        # Create a simple plugin file for demo
        demo_plugin = plugin_dir / "demo_plugin.py"
        demo_plugin.write_text('''
from nexus_plugin_system import MonitoringPlugin, PluginMetadata, PluginType

class DemoMonitoringPlugin(MonitoringPlugin):
    @property
    def plugin_metadata(self):
        return PluginMetadata(
            plugin_id="demo_monitoring",
            name="Demo Monitoring Plugin",
            version="1.0.0",
            plugin_type=PluginType.MONITORING,
            description="Demo monitoring plugin"
        )
    
    async def initialize(self):
        return True
    
    async def cleanup(self):
        return True
    
    async def health_check(self):
        return {"healthy": True}
    
    async def collect_metrics(self):
        return {"demo_metric": 42}
    
    async def send_alert(self, alert_type, message, severity="info"):
        print(f"Alert: {alert_type} - {message}")
    
    async def get_dashboard_data(self):
        return {"demo_data": "Hello World"}
''')
        
        # Discover and load plugins
        await manager.discover_plugins()
        
        # Load demo plugin
        success = await manager.load_plugin("demo_plugin")
        print(f"Demo plugin loaded: {success}")
        
        # List plugins
        plugins = manager.list_plugins()
        print(f"Active plugins: {len(plugins)}")
        
        for plugin in plugins:
            print(f"  {plugin.metadata.name} v{plugin.metadata.version} - {plugin.status.value}")
        
        # Test plugin functionality
        demo_plugin_instance = manager.get_plugin("demo_plugin")
        if demo_plugin_instance:
            metrics = await demo_plugin_instance.collect_metrics()
            print(f"Demo metrics: {metrics}")
        
        await manager.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()