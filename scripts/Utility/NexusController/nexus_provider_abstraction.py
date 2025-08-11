#!/usr/bin/env python3
"""
NexusController v2.0 Provider Abstraction Layer
Multi-cloud and infrastructure provider abstraction for unified management
"""

import os
import sys
import json
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Type, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from pathlib import Path
import importlib
import weakref

# Import core systems
from nexus_event_system import Event, EventType, EventBus
from nexus_plugin_system import PluginInterface, PluginMetadata, PluginType

class ProviderType(Enum):
    """Infrastructure provider types"""
    CLOUD_AWS = "cloud.aws"
    CLOUD_AZURE = "cloud.azure"
    CLOUD_GCP = "cloud.gcp"
    CLOUD_DIGITALOCEAN = "cloud.digitalocean"
    CLOUD_LINODE = "cloud.linode"
    VIRTUALIZATION_VMWARE = "virtualization.vmware"
    VIRTUALIZATION_PROXMOX = "virtualization.proxmox"
    CONTAINER_DOCKER = "container.docker"
    CONTAINER_KUBERNETES = "container.kubernetes"
    BARE_METAL = "bare_metal"
    CUSTOM = "custom"

class ResourceOperation(Enum):
    """Resource operations"""
    CREATE = "create"
    READ = "read" 
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    SCALE = "scale"
    BACKUP = "backup"
    RESTORE = "restore"

class ResourceStatus(Enum):
    """Resource status"""
    UNKNOWN = "unknown"
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    STOPPING = "stopping"
    STARTING = "starting"
    ERROR = "error"
    DELETING = "deleting"
    UPDATING = "updating"

@dataclass
class ProviderCredentials:
    """Provider authentication credentials"""
    
    provider_type: ProviderType
    credential_type: str  # api_key, oauth, certificate, etc.
    credentials: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if credentials are expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without sensitive data)"""
        result = asdict(self)
        result['provider_type'] = self.provider_type.value
        result['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            result['expires_at'] = self.expires_at.isoformat()
        
        # Mask sensitive credentials
        result['credentials'] = {k: '***' for k in self.credentials.keys()}
        return result

@dataclass 
class CloudResource:
    """Abstract cloud resource representation"""
    
    resource_id: str
    provider_type: ProviderType
    resource_type: str  # instance, volume, network, etc.
    name: str
    status: ResourceStatus = ResourceStatus.UNKNOWN
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    region: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['provider_type'] = self.provider_type.value
        result['status'] = self.status.value
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudResource':
        """Create from dictionary"""
        data = data.copy()
        data['provider_type'] = ProviderType(data['provider_type'])
        data['status'] = ResourceStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

class ProviderInterface(ABC):
    """Abstract base class for infrastructure providers"""
    
    def __init__(self, provider_id: str, credentials: ProviderCredentials):
        self.provider_id = provider_id
        self.credentials = credentials
        self.provider_type = credentials.provider_type
        self.connected = False
        self.last_health_check = None
        self.logger = logging.getLogger(f"nexus.provider.{provider_id}")
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider display name"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity"""
        pass
    
    @abstractmethod 
    async def list_resources(self, resource_type: str = None, region: str = None) -> List[CloudResource]:
        """List resources"""
        pass
    
    @abstractmethod
    async def get_resource(self, resource_id: str) -> Optional[CloudResource]:
        """Get specific resource"""
        pass
    
    @abstractmethod
    async def create_resource(self, resource_type: str, config: Dict[str, Any]) -> CloudResource:
        """Create new resource"""
        pass
    
    @abstractmethod
    async def update_resource(self, resource_id: str, config: Dict[str, Any]) -> CloudResource:
        """Update existing resource"""
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete resource"""
        pass
    
    @abstractmethod
    async def get_resource_metrics(self, resource_id: str, 
                                 start_time: datetime = None,
                                 end_time: datetime = None) -> Dict[str, Any]:
        """Get resource metrics"""
        pass
    
    async def disconnect(self):
        """Disconnect from provider"""
        self.connected = False
        self.logger.info(f"Disconnected from {self.provider_name}")

class AWSProvider(ProviderInterface):
    """Amazon Web Services provider implementation"""
    
    def __init__(self, provider_id: str, credentials: ProviderCredentials):
        super().__init__(provider_id, credentials)
        self.ec2_client = None
        self.s3_client = None
        self.cloudwatch_client = None
    
    @property
    def provider_name(self) -> str:
        return "Amazon Web Services"
    
    async def authenticate(self) -> bool:
        """Authenticate with AWS"""
        try:
            # This would normally use boto3
            # import boto3
            # session = boto3.Session(
            #     aws_access_key_id=self.credentials.credentials.get('access_key_id'),
            #     aws_secret_access_key=self.credentials.credentials.get('secret_access_key'),
            #     region_name=self.credentials.credentials.get('region', 'us-east-1')
            # )
            # self.ec2_client = session.client('ec2')
            # self.s3_client = session.client('s3')
            # self.cloudwatch_client = session.client('cloudwatch')
            
            self.connected = True
            self.logger.info("AWS authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"AWS authentication failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check AWS connectivity"""
        try:
            # This would normally make actual AWS API calls
            # regions = self.ec2_client.describe_regions()
            
            self.last_health_check = datetime.now()
            return {
                'healthy': True,
                'provider': 'aws',
                'regions_available': 16,  # Mock data
                'last_check': self.last_health_check.isoformat(),
                'response_time_ms': 150
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'provider': 'aws',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def list_resources(self, resource_type: str = None, region: str = None) -> List[CloudResource]:
        """List AWS resources"""
        resources = []
        
        try:
            # Mock implementation - would normally use boto3
            if resource_type is None or resource_type == 'instance':
                # Mock EC2 instances
                resources.append(CloudResource(
                    resource_id="i-1234567890abcdef0",
                    provider_type=ProviderType.CLOUD_AWS,
                    resource_type="instance",
                    name="web-server-01",
                    status=ResourceStatus.RUNNING,
                    properties={
                        'instance_type': 't3.medium',
                        'public_ip': '54.123.45.67',
                        'private_ip': '10.0.1.100',
                        'availability_zone': 'us-east-1a'
                    },
                    region=region or 'us-east-1',
                    tags={'Environment': 'production', 'Service': 'web'}
                ))
            
            if resource_type is None or resource_type == 'volume':
                # Mock EBS volumes
                resources.append(CloudResource(
                    resource_id="vol-1234567890abcdef0",
                    provider_type=ProviderType.CLOUD_AWS,
                    resource_type="volume",
                    name="web-server-root",
                    status=ResourceStatus.RUNNING,
                    properties={
                        'size': 20,
                        'volume_type': 'gp3',
                        'iops': 3000,
                        'encrypted': True
                    },
                    region=region or 'us-east-1'
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to list AWS resources: {e}")
        
        return resources
    
    async def get_resource(self, resource_id: str) -> Optional[CloudResource]:
        """Get specific AWS resource"""
        try:
            # Mock implementation
            if resource_id.startswith('i-'):
                return CloudResource(
                    resource_id=resource_id,
                    provider_type=ProviderType.CLOUD_AWS,
                    resource_type="instance",
                    name=f"instance-{resource_id[-8:]}",
                    status=ResourceStatus.RUNNING
                )
        except Exception as e:
            self.logger.error(f"Failed to get AWS resource {resource_id}: {e}")
        
        return None
    
    async def create_resource(self, resource_type: str, config: Dict[str, Any]) -> CloudResource:
        """Create AWS resource"""
        try:
            # Mock implementation
            resource_id = f"{resource_type[0]}-{uuid.uuid4().hex[:16]}"
            
            resource = CloudResource(
                resource_id=resource_id,
                provider_type=ProviderType.CLOUD_AWS,
                resource_type=resource_type,
                name=config.get('name', f"{resource_type}-{resource_id[-8:]}"),
                status=ResourceStatus.CREATING,
                properties=config,
                region=config.get('region', 'us-east-1')
            )
            
            self.logger.info(f"Created AWS {resource_type}: {resource_id}")
            return resource
            
        except Exception as e:
            self.logger.error(f"Failed to create AWS {resource_type}: {e}")
            raise
    
    async def update_resource(self, resource_id: str, config: Dict[str, Any]) -> CloudResource:
        """Update AWS resource"""
        try:
            # Mock implementation
            resource = await self.get_resource(resource_id)
            if resource:
                resource.properties.update(config)
                resource.updated_at = datetime.now()
                resource.status = ResourceStatus.UPDATING
                
                self.logger.info(f"Updated AWS resource: {resource_id}")
                return resource
            else:
                raise ValueError(f"Resource not found: {resource_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update AWS resource {resource_id}: {e}")
            raise
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete AWS resource"""
        try:
            # Mock implementation
            self.logger.info(f"Deleted AWS resource: {resource_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete AWS resource {resource_id}: {e}")
            return False
    
    async def get_resource_metrics(self, resource_id: str,
                                 start_time: datetime = None,
                                 end_time: datetime = None) -> Dict[str, Any]:
        """Get AWS resource metrics"""
        try:
            # Mock CloudWatch metrics
            return {
                'resource_id': resource_id,
                'metrics': {
                    'CPUUtilization': {'value': 25.5, 'unit': 'Percent'},
                    'NetworkIn': {'value': 1024000, 'unit': 'Bytes'},
                    'NetworkOut': {'value': 2048000, 'unit': 'Bytes'},
                    'DiskReadOps': {'value': 100, 'unit': 'Count'},
                    'DiskWriteOps': {'value': 50, 'unit': 'Count'}
                },
                'period_start': (start_time or datetime.now() - timedelta(hours=1)).isoformat(),
                'period_end': (end_time or datetime.now()).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get AWS metrics for {resource_id}: {e}")
            return {}

class DockerProvider(ProviderInterface):
    """Docker container provider implementation"""
    
    def __init__(self, provider_id: str, credentials: ProviderCredentials):
        super().__init__(provider_id, credentials)
        self.docker_client = None
    
    @property
    def provider_name(self) -> str:
        return "Docker"
    
    async def authenticate(self) -> bool:
        """Authenticate with Docker"""
        try:
            # This would normally use docker-py
            # import docker
            # self.docker_client = docker.from_env()
            # self.docker_client.ping()
            
            self.connected = True
            self.logger.info("Docker authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Docker authentication failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Docker connectivity"""
        try:
            # Mock implementation
            self.last_health_check = datetime.now()
            return {
                'healthy': True,
                'provider': 'docker',
                'version': '24.0.7',  # Mock data
                'containers_running': 5,
                'images_available': 12,
                'last_check': self.last_health_check.isoformat()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'provider': 'docker',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def list_resources(self, resource_type: str = None, region: str = None) -> List[CloudResource]:
        """List Docker resources"""
        resources = []
        
        try:
            if resource_type is None or resource_type == 'container':
                # Mock containers
                resources.append(CloudResource(
                    resource_id="container_nginx_01",
                    provider_type=ProviderType.CONTAINER_DOCKER,
                    resource_type="container",
                    name="nginx-web",
                    status=ResourceStatus.RUNNING,
                    properties={
                        'image': 'nginx:latest',
                        'ports': ['80:8080', '443:8443'],
                        'memory_limit': '512MB',
                        'cpu_limit': '0.5'
                    },
                    tags={'service': 'web', 'environment': 'production'}
                ))
                
                resources.append(CloudResource(
                    resource_id="container_postgres_01",
                    provider_type=ProviderType.CONTAINER_DOCKER,
                    resource_type="container",
                    name="postgres-db",
                    status=ResourceStatus.RUNNING,
                    properties={
                        'image': 'postgres:15',
                        'ports': ['5432:5432'],
                        'memory_limit': '1GB',
                        'volumes': ['/data/postgres:/var/lib/postgresql/data']
                    },
                    tags={'service': 'database', 'environment': 'production'}
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to list Docker resources: {e}")
        
        return resources
    
    async def get_resource(self, resource_id: str) -> Optional[CloudResource]:
        """Get specific Docker resource"""
        try:
            # Mock implementation
            if resource_id.startswith('container_'):
                return CloudResource(
                    resource_id=resource_id,
                    provider_type=ProviderType.CONTAINER_DOCKER,
                    resource_type="container",
                    name=resource_id.replace('container_', '').replace('_', '-'),
                    status=ResourceStatus.RUNNING
                )
        except Exception as e:
            self.logger.error(f"Failed to get Docker resource {resource_id}: {e}")
        
        return None
    
    async def create_resource(self, resource_type: str, config: Dict[str, Any]) -> CloudResource:
        """Create Docker resource"""
        try:
            # Mock implementation
            resource_id = f"container_{config.get('name', 'unnamed')}_{uuid.uuid4().hex[:8]}"
            
            resource = CloudResource(
                resource_id=resource_id,
                provider_type=ProviderType.CONTAINER_DOCKER,
                resource_type=resource_type,
                name=config.get('name', resource_id),
                status=ResourceStatus.CREATING,
                properties=config
            )
            
            self.logger.info(f"Created Docker {resource_type}: {resource_id}")
            return resource
            
        except Exception as e:
            self.logger.error(f"Failed to create Docker {resource_type}: {e}")
            raise
    
    async def update_resource(self, resource_id: str, config: Dict[str, Any]) -> CloudResource:
        """Update Docker resource"""
        try:
            # Mock implementation
            resource = await self.get_resource(resource_id)
            if resource:
                resource.properties.update(config)
                resource.updated_at = datetime.now()
                resource.status = ResourceStatus.UPDATING
                
                self.logger.info(f"Updated Docker resource: {resource_id}")
                return resource
            else:
                raise ValueError(f"Resource not found: {resource_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update Docker resource {resource_id}: {e}")
            raise
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete Docker resource"""
        try:
            # Mock implementation
            self.logger.info(f"Deleted Docker resource: {resource_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete Docker resource {resource_id}: {e}")
            return False
    
    async def get_resource_metrics(self, resource_id: str,
                                 start_time: datetime = None,
                                 end_time: datetime = None) -> Dict[str, Any]:
        """Get Docker resource metrics"""
        try:
            # Mock Docker stats
            return {
                'resource_id': resource_id,
                'metrics': {
                    'cpu_percent': {'value': 15.2, 'unit': 'Percent'},
                    'memory_usage': {'value': 134217728, 'unit': 'Bytes'},  # 128MB
                    'memory_limit': {'value': 536870912, 'unit': 'Bytes'},  # 512MB
                    'network_rx': {'value': 1024000, 'unit': 'Bytes'},
                    'network_tx': {'value': 512000, 'unit': 'Bytes'},
                    'block_read': {'value': 50331648, 'unit': 'Bytes'},    # 48MB
                    'block_write': {'value': 25165824, 'unit': 'Bytes'}    # 24MB
                },
                'period_start': (start_time or datetime.now() - timedelta(hours=1)).isoformat(),
                'period_end': (end_time or datetime.now()).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Docker metrics for {resource_id}: {e}")
            return {}

class ProviderRegistry:
    """Registry for infrastructure providers"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderInterface] = {}
        self.provider_classes: Dict[ProviderType, Type[ProviderInterface]] = {}
        self.credentials_store: Dict[str, ProviderCredentials] = {}
        self._lock = threading.RLock()
        
        # Register built-in providers
        self._register_builtin_providers()
    
    def _register_builtin_providers(self):
        """Register built-in provider implementations"""
        self.provider_classes[ProviderType.CLOUD_AWS] = AWSProvider
        self.provider_classes[ProviderType.CONTAINER_DOCKER] = DockerProvider
        # Additional providers would be registered here
    
    def register_provider_class(self, provider_type: ProviderType, provider_class: Type[ProviderInterface]):
        """Register a provider implementation class"""
        self.provider_classes[provider_type] = provider_class
        logging.info(f"Registered provider class: {provider_type.value}")
    
    async def add_provider(self, provider_id: str, credentials: ProviderCredentials) -> bool:
        """Add and authenticate a provider"""
        try:
            provider_class = self.provider_classes.get(credentials.provider_type)
            if not provider_class:
                raise ValueError(f"No implementation for provider type: {credentials.provider_type}")
            
            # Create provider instance
            provider = provider_class(provider_id, credentials)
            
            # Authenticate
            if await provider.authenticate():
                with self._lock:
                    self.providers[provider_id] = provider
                    self.credentials_store[provider_id] = credentials
                
                logging.info(f"Provider added successfully: {provider_id}")
                return True
            else:
                logging.error(f"Provider authentication failed: {provider_id}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to add provider {provider_id}: {e}")
            return False
    
    async def remove_provider(self, provider_id: str):
        """Remove a provider"""
        with self._lock:
            if provider_id in self.providers:
                provider = self.providers[provider_id]
                await provider.disconnect()
                del self.providers[provider_id]
                
                if provider_id in self.credentials_store:
                    del self.credentials_store[provider_id]
                
                logging.info(f"Provider removed: {provider_id}")
    
    def get_provider(self, provider_id: str) -> Optional[ProviderInterface]:
        """Get provider by ID"""
        return self.providers.get(provider_id)
    
    def list_providers(self, provider_type: ProviderType = None) -> List[ProviderInterface]:
        """List providers with optional filtering"""
        with self._lock:
            providers = list(self.providers.values())
            
            if provider_type:
                providers = [p for p in providers if p.provider_type == provider_type]
            
            return providers
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all providers"""
        results = {}
        
        for provider_id, provider in self.providers.items():
            try:
                results[provider_id] = await provider.health_check()
            except Exception as e:
                results[provider_id] = {
                    'healthy': False,
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        return results

class MultiCloudManager:
    """Unified multi-cloud resource management"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.provider_registry = ProviderRegistry()
        self.resource_cache: Dict[str, CloudResource] = {}
        self._running = False
        self._health_check_task = None
        self._sync_task = None
        self._lock = threading.RLock()
        
        # Configuration
        self.health_check_interval = timedelta(minutes=5)
        self.sync_interval = timedelta(minutes=15)
        
        logging.info("MultiCloudManager initialized")
    
    async def start(self):
        """Start multi-cloud management services"""
        self._running = True
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._sync_task = asyncio.create_task(self._resource_sync_loop())
        
        logging.info("MultiCloudManager started")
    
    async def stop(self):
        """Stop multi-cloud management services"""
        self._running = False
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()
        
        # Wait for tasks to complete
        tasks = [self._health_check_task, self._sync_task]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Disconnect all providers
        provider_ids = list(self.provider_registry.providers.keys())
        for provider_id in provider_ids:
            await self.provider_registry.remove_provider(provider_id)
        
        logging.info("MultiCloudManager stopped")
    
    async def add_provider(self, provider_id: str, provider_type: ProviderType, 
                          credentials: Dict[str, Any]) -> bool:
        """Add cloud provider"""
        provider_credentials = ProviderCredentials(
            provider_type=provider_type,
            credential_type="api_key",  # Default, could be parameterized
            credentials=credentials
        )
        
        success = await self.provider_registry.add_provider(provider_id, provider_credentials)
        
        if success and self.event_bus:
            event = Event(
                event_type=EventType.CLOUD_SYNC_STARTED,
                source="nexus.multicloud",
                data={
                    'action': 'provider_added',
                    'provider_id': provider_id,
                    'provider_type': provider_type.value
                }
            )
            await self.event_bus.publish(event)
        
        return success
    
    async def list_all_resources(self, resource_type: str = None) -> List[CloudResource]:
        """List resources across all providers"""
        all_resources = []
        
        providers = self.provider_registry.list_providers()
        
        for provider in providers:
            try:
                resources = await provider.list_resources(resource_type)
                all_resources.extend(resources)
            except Exception as e:
                logging.error(f"Failed to list resources from {provider.provider_id}: {e}")
        
        # Update cache
        with self._lock:
            for resource in all_resources:
                self.resource_cache[resource.resource_id] = resource
        
        return all_resources
    
    async def get_resource(self, resource_id: str) -> Optional[CloudResource]:
        """Get resource by ID across all providers"""
        # Check cache first
        with self._lock:
            if resource_id in self.resource_cache:
                return self.resource_cache[resource_id]
        
        # Search across providers
        providers = self.provider_registry.list_providers()
        
        for provider in providers:
            try:
                resource = await provider.get_resource(resource_id)
                if resource:
                    # Update cache
                    with self._lock:
                        self.resource_cache[resource_id] = resource
                    return resource
            except Exception as e:
                logging.error(f"Error getting resource from {provider.provider_id}: {e}")
        
        return None
    
    async def create_resource(self, provider_id: str, resource_type: str, 
                            config: Dict[str, Any]) -> Optional[CloudResource]:
        """Create resource on specific provider"""
        provider = self.provider_registry.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")
        
        try:
            resource = await provider.create_resource(resource_type, config)
            
            # Update cache
            with self._lock:
                self.resource_cache[resource.resource_id] = resource
            
            # Emit event
            if self.event_bus:
                event = Event(
                    event_type=EventType.CLOUD_SYNC_COMPLETED,
                    source="nexus.multicloud",
                    data={
                        'action': 'resource_created',
                        'resource_id': resource.resource_id,
                        'provider_id': provider_id,
                        'resource_type': resource_type
                    }
                )
                await self.event_bus.publish(event)
            
            return resource
            
        except Exception as e:
            logging.error(f"Failed to create resource on {provider_id}: {e}")
            raise
    
    async def get_resource_metrics(self, resource_id: str,
                                 start_time: datetime = None,
                                 end_time: datetime = None) -> Optional[Dict[str, Any]]:
        """Get metrics for specific resource"""
        # Find which provider has this resource
        providers = self.provider_registry.list_providers()
        
        for provider in providers:
            try:
                resource = await provider.get_resource(resource_id)
                if resource:
                    return await provider.get_resource_metrics(resource_id, start_time, end_time)
            except Exception as e:
                logging.error(f"Error getting metrics from {provider.provider_id}: {e}")
        
        return None
    
    async def get_overview(self) -> Dict[str, Any]:
        """Get multi-cloud overview"""
        providers = self.provider_registry.list_providers()
        health_status = await self.provider_registry.health_check_all()
        
        overview = {
            'providers': len(providers),
            'healthy_providers': sum(1 for status in health_status.values() if status.get('healthy', False)),
            'total_resources': len(self.resource_cache),
            'resource_types': {},
            'provider_status': health_status,
            'last_sync': datetime.now().isoformat()
        }
        
        # Count resources by type
        with self._lock:
            for resource in self.resource_cache.values():
                resource_type = resource.resource_type
                if resource_type not in overview['resource_types']:
                    overview['resource_types'][resource_type] = 0
                overview['resource_types'][resource_type] += 1
        
        return overview
    
    async def _health_check_loop(self):
        """Background health checking for all providers"""
        while self._running:
            try:
                await self.provider_registry.health_check_all()
                await asyncio.sleep(self.health_check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _resource_sync_loop(self):
        """Background resource synchronization"""
        while self._running:
            try:
                # Refresh resource cache
                await self.list_all_resources()
                
                # Emit sync completed event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.CLOUD_SYNC_COMPLETED,
                        source="nexus.multicloud",
                        data={
                            'action': 'resource_sync',
                            'resource_count': len(self.resource_cache),
                            'provider_count': len(self.provider_registry.providers)
                        }
                    )
                    await self.event_bus.publish(event)
                
                await asyncio.sleep(self.sync_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Resource sync loop error: {e}")
                await asyncio.sleep(300)  # 5 minutes on error

def main():
    """Demo of provider abstraction system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create multi-cloud manager
        manager = MultiCloudManager()
        await manager.start()
        
        # Add AWS provider (mock credentials)
        aws_success = await manager.add_provider(
            "aws_production",
            ProviderType.CLOUD_AWS,
            {
                'access_key_id': 'AKIA...',
                'secret_access_key': '***',
                'region': 'us-east-1'
            }
        )
        print(f"AWS provider added: {aws_success}")
        
        # Add Docker provider
        docker_success = await manager.add_provider(
            "docker_local",
            ProviderType.CONTAINER_DOCKER,
            {
                'socket_path': '/var/run/docker.sock'
            }
        )
        print(f"Docker provider added: {docker_success}")
        
        # List all resources
        resources = await manager.list_all_resources()
        print(f"Total resources found: {len(resources)}")
        
        for resource in resources:
            print(f"  {resource.provider_type.value}: {resource.name} ({resource.resource_type}) - {resource.status.value}")
        
        # Get overview
        overview = await manager.get_overview()
        print(f"Multi-cloud overview: {overview}")
        
        # Test resource metrics
        if resources:
            resource_id = resources[0].resource_id
            metrics = await manager.get_resource_metrics(resource_id)
            if metrics:
                print(f"Metrics for {resource_id}: {len(metrics.get('metrics', {}))} metrics")
        
        await manager.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()