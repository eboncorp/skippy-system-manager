#!/usr/bin/env python3
"""
NexusController v2.0 State Management System
Advanced infrastructure state tracking and drift detection
"""

import os
import sys
import json
import asyncio
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from pathlib import Path
import copy

# Import event system
from nexus_event_system import Event, EventType, EventBus

class ResourceType(Enum):
    """Types of infrastructure resources"""
    SERVER = "server"
    NETWORK_DEVICE = "network_device"
    SSH_CONNECTION = "ssh_connection"
    SERVICE = "service"
    CONFIGURATION = "configuration"
    CLOUD_RESOURCE = "cloud_resource"
    BACKUP = "backup"
    USER = "user"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"

class ResourceState(Enum):
    """Resource state values"""
    UNKNOWN = "unknown"
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPDATING = "updating"
    DELETING = "deleting"
    ERROR = "error"
    DRIFT = "drift"

@dataclass
class Resource:
    """Infrastructure resource definition"""
    
    resource_id: str
    resource_type: ResourceType
    name: str
    state: ResourceState = ResourceState.UNKNOWN
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    checksum: str = ""
    
    def __post_init__(self):
        """Calculate checksum after initialization"""
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate resource checksum for drift detection"""
        # Create deterministic representation
        data = {
            'resource_type': self.resource_type.value,
            'name': self.name,
            'properties': self.properties,
            'metadata': self.metadata
        }
        
        # Convert to JSON string (sorted for consistency)
        json_str = json.dumps(data, sort_keys=True, default=str)
        
        # Calculate SHA256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def update_properties(self, properties: Dict[str, Any]):
        """Update resource properties"""
        self.properties.update(properties)
        self.updated_at = datetime.now()
        self.version += 1
        old_checksum = self.checksum
        self.checksum = self._calculate_checksum()
        
        return old_checksum != self.checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['resource_type'] = self.resource_type.value
        result['state'] = self.state.value
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Resource':
        """Create from dictionary"""
        data = data.copy()
        data['resource_type'] = ResourceType(data['resource_type'])
        data['state'] = ResourceState(data['state'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

@dataclass
class StateSnapshot:
    """Point-in-time state snapshot"""
    
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    resources: Dict[str, Resource] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'snapshot_id': self.snapshot_id,
            'timestamp': self.timestamp.isoformat(),
            'resources': {k: v.to_dict() for k, v in self.resources.items()},
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create from dictionary"""
        return cls(
            snapshot_id=data['snapshot_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            resources={k: Resource.from_dict(v) for k, v in data['resources'].items()},
            metadata=data['metadata']
        )

@dataclass
class DriftDetection:
    """Drift detection result"""
    
    resource_id: str
    drift_type: str  # 'property_changed', 'state_changed', 'missing', 'unexpected'
    expected_value: Any
    actual_value: Any
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)

class StateBackend(ABC):
    """Abstract state storage backend"""
    
    @abstractmethod
    async def save_resource(self, resource: Resource):
        """Save resource state"""
        pass
    
    @abstractmethod
    async def load_resource(self, resource_id: str) -> Optional[Resource]:
        """Load resource state"""
        pass
    
    @abstractmethod
    async def list_resources(self, resource_type: ResourceType = None) -> List[Resource]:
        """List resources"""
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_id: str):
        """Delete resource"""
        pass
    
    @abstractmethod
    async def save_snapshot(self, snapshot: StateSnapshot):
        """Save state snapshot"""
        pass
    
    @abstractmethod
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Load state snapshot"""
        pass

class FileStateBackend(StateBackend):
    """File-based state storage"""
    
    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.resources_dir = self.state_dir / "resources"
        self.snapshots_dir = self.state_dir / "snapshots"
        
        # Create directories
        self.resources_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions
        os.chmod(self.state_dir, 0o700)
        os.chmod(self.resources_dir, 0o700)
        os.chmod(self.snapshots_dir, 0o700)
        
        self._lock = threading.RLock()
    
    async def save_resource(self, resource: Resource):
        """Save resource to file"""
        with self._lock:
            resource_file = self.resources_dir / f"{resource.resource_id}.json"
            
            with open(resource_file, 'w') as f:
                json.dump(resource.to_dict(), f, indent=2, default=str)
            
            os.chmod(resource_file, 0o600)
    
    async def load_resource(self, resource_id: str) -> Optional[Resource]:
        """Load resource from file"""
        with self._lock:
            resource_file = self.resources_dir / f"{resource_id}.json"
            
            if not resource_file.exists():
                return None
            
            try:
                with open(resource_file, 'r') as f:
                    data = json.load(f)
                return Resource.from_dict(data)
            except Exception as e:
                logging.error(f"Failed to load resource {resource_id}: {e}")
                return None
    
    async def list_resources(self, resource_type: ResourceType = None) -> List[Resource]:
        """List all resources"""
        with self._lock:
            resources = []
            
            for resource_file in self.resources_dir.glob("*.json"):
                try:
                    with open(resource_file, 'r') as f:
                        data = json.load(f)
                    
                    resource = Resource.from_dict(data)
                    
                    if resource_type is None or resource.resource_type == resource_type:
                        resources.append(resource)
                        
                except Exception as e:
                    logging.error(f"Failed to load resource from {resource_file}: {e}")
            
            return resources
    
    async def delete_resource(self, resource_id: str):
        """Delete resource file"""
        with self._lock:
            resource_file = self.resources_dir / f"{resource_id}.json"
            if resource_file.exists():
                resource_file.unlink()
    
    async def save_snapshot(self, snapshot: StateSnapshot):
        """Save snapshot to file"""
        with self._lock:
            snapshot_file = self.snapshots_dir / f"{snapshot.snapshot_id}.json"
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot.to_dict(), f, indent=2, default=str)
            
            os.chmod(snapshot_file, 0o600)
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Load snapshot from file"""
        with self._lock:
            snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
            
            if not snapshot_file.exists():
                return None
            
            try:
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)
                return StateSnapshot.from_dict(data)
            except Exception as e:
                logging.error(f"Failed to load snapshot {snapshot_id}: {e}")
                return None

class DriftAnalyzer:
    """Analyzes infrastructure drift"""
    
    def __init__(self):
        self.drift_detectors = {}
        self._setup_default_detectors()
    
    def _setup_default_detectors(self):
        """Setup default drift detection rules"""
        
        # Property change detector
        self.drift_detectors['property_change'] = self._detect_property_changes
        
        # State change detector
        self.drift_detectors['state_change'] = self._detect_state_changes
        
        # Configuration drift detector
        self.drift_detectors['config_drift'] = self._detect_config_drift
        
        # Network topology drift
        self.drift_detectors['network_drift'] = self._detect_network_drift
    
    def analyze(self, expected: Resource, actual: Resource) -> List[DriftDetection]:
        """Analyze drift between expected and actual state"""
        drifts = []
        
        # Basic sanity checks
        if expected.resource_id != actual.resource_id:
            return drifts
        
        # Run all drift detectors
        for detector_name, detector_func in self.drift_detectors.items():
            try:
                detected_drifts = detector_func(expected, actual)
                drifts.extend(detected_drifts)
            except Exception as e:
                logging.error(f"Drift detector {detector_name} failed: {e}")
        
        return drifts
    
    def _detect_property_changes(self, expected: Resource, actual: Resource) -> List[DriftDetection]:
        """Detect property changes"""
        drifts = []
        
        # Compare properties
        expected_props = expected.properties
        actual_props = actual.properties
        
        # Check for missing properties
        for key, expected_value in expected_props.items():
            if key not in actual_props:
                drifts.append(DriftDetection(
                    resource_id=expected.resource_id,
                    drift_type="property_missing",
                    expected_value=expected_value,
                    actual_value=None,
                    severity="medium",
                    description=f"Property '{key}' is missing"
                ))
            elif actual_props[key] != expected_value:
                drifts.append(DriftDetection(
                    resource_id=expected.resource_id,
                    drift_type="property_changed",
                    expected_value=expected_value,
                    actual_value=actual_props[key],
                    severity="low",
                    description=f"Property '{key}' changed from {expected_value} to {actual_props[key]}"
                ))
        
        # Check for unexpected properties
        for key, actual_value in actual_props.items():
            if key not in expected_props:
                drifts.append(DriftDetection(
                    resource_id=expected.resource_id,
                    drift_type="property_unexpected",
                    expected_value=None,
                    actual_value=actual_value,
                    severity="low",
                    description=f"Unexpected property '{key}' with value {actual_value}"
                ))
        
        return drifts
    
    def _detect_state_changes(self, expected: Resource, actual: Resource) -> List[DriftDetection]:
        """Detect state changes"""
        drifts = []
        
        if expected.state != actual.state:
            severity = "high" if actual.state == ResourceState.ERROR else "medium"
            
            drifts.append(DriftDetection(
                resource_id=expected.resource_id,
                drift_type="state_changed",
                expected_value=expected.state.value,
                actual_value=actual.state.value,
                severity=severity,
                description=f"State changed from {expected.state.value} to {actual.state.value}"
            ))
        
        return drifts
    
    def _detect_config_drift(self, expected: Resource, actual: Resource) -> List[DriftDetection]:
        """Detect configuration drift"""
        drifts = []
        
        # Check checksum for overall drift
        if expected.checksum != actual.checksum:
            drifts.append(DriftDetection(
                resource_id=expected.resource_id,
                drift_type="config_drift",
                expected_value=expected.checksum,
                actual_value=actual.checksum,
                severity="medium",
                description="Configuration checksum mismatch detected"
            ))
        
        return drifts
    
    def _detect_network_drift(self, expected: Resource, actual: Resource) -> List[DriftDetection]:
        """Detect network-specific drift"""
        drifts = []
        
        if expected.resource_type == ResourceType.NETWORK_DEVICE:
            # Check critical network properties
            critical_props = ['ip', 'hostname', 'mac_address', 'status']
            
            for prop in critical_props:
                if prop in expected.properties and prop in actual.properties:
                    if expected.properties[prop] != actual.properties[prop]:
                        drifts.append(DriftDetection(
                            resource_id=expected.resource_id,
                            drift_type="network_drift",
                            expected_value=expected.properties[prop],
                            actual_value=actual.properties[prop],
                            severity="high",
                            description=f"Critical network property '{prop}' changed"
                        ))
        
        return drifts

class StateManager:
    """Infrastructure state management system"""
    
    def __init__(self, backend: StateBackend, event_bus: EventBus = None):
        self.backend = backend
        self.event_bus = event_bus
        self.drift_analyzer = DriftAnalyzer()
        self.resources = {}  # In-memory cache
        self.snapshots = {}  # Snapshot cache
        self._lock = threading.RLock()
        
        # Drift detection settings
        self.drift_check_interval = timedelta(minutes=15)
        self.auto_remediation = False
        
        # Background tasks
        self._running = False
        self._drift_check_task = None
        
        logging.info("StateManager initialized")
    
    async def start(self):
        """Start state management services"""
        self._running = True
        
        # Load existing resources
        await self._load_all_resources()
        
        # Start drift detection task
        self._drift_check_task = asyncio.create_task(self._drift_check_loop())
        
        logging.info("StateManager started")
    
    async def stop(self):
        """Stop state management services"""
        self._running = False
        
        if self._drift_check_task:
            self._drift_check_task.cancel()
            try:
                await self._drift_check_task
            except asyncio.CancelledError:
                pass
        
        logging.info("StateManager stopped")
    
    async def _load_all_resources(self):
        """Load all resources from backend"""
        try:
            resources = await self.backend.list_resources()
            
            with self._lock:
                for resource in resources:
                    self.resources[resource.resource_id] = resource
            
            logging.info(f"Loaded {len(resources)} resources from state backend")
            
        except Exception as e:
            logging.error(f"Failed to load resources: {e}")
    
    async def register_resource(self, resource: Resource):
        """Register a new resource"""
        with self._lock:
            self.resources[resource.resource_id] = resource
        
        # Persist to backend
        await self.backend.save_resource(resource)
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.INFRA_STATE_DRIFT,
                source="nexus.state_manager",
                data={
                    'action': 'resource_registered',
                    'resource_id': resource.resource_id,
                    'resource_type': resource.resource_type.value,
                    'resource_name': resource.name
                }
            )
            await self.event_bus.publish(event)
        
        logging.info(f"Resource registered: {resource.resource_id}")
    
    async def update_resource(self, resource_id: str, properties: Dict[str, Any]) -> Optional[Resource]:
        """Update resource properties"""
        with self._lock:
            if resource_id not in self.resources:
                logging.warning(f"Resource not found: {resource_id}")
                return None
            
            resource = self.resources[resource_id]
            old_checksum = resource.checksum
            
            # Update properties
            has_changed = resource.update_properties(properties)
            
            if has_changed:
                # Persist to backend
                await self.backend.save_resource(resource)
                
                # Emit event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.INFRA_STATE_DRIFT,
                        source="nexus.state_manager",
                        data={
                            'action': 'resource_updated',
                            'resource_id': resource_id,
                            'old_checksum': old_checksum,
                            'new_checksum': resource.checksum,
                            'properties': properties
                        }
                    )
                    await self.event_bus.publish(event)
                
                logging.info(f"Resource updated: {resource_id}")
            
            return resource
    
    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID"""
        with self._lock:
            return self.resources.get(resource_id)
    
    async def list_resources(self, resource_type: ResourceType = None) -> List[Resource]:
        """List resources"""
        with self._lock:
            if resource_type:
                return [r for r in self.resources.values() if r.resource_type == resource_type]
            return list(self.resources.values())
    
    async def delete_resource(self, resource_id: str):
        """Delete a resource"""
        with self._lock:
            if resource_id in self.resources:
                resource = self.resources[resource_id]
                del self.resources[resource_id]
                
                # Delete from backend
                await self.backend.delete_resource(resource_id)
                
                # Emit event
                if self.event_bus:
                    event = Event(
                        event_type=EventType.INFRA_STATE_DRIFT,
                        source="nexus.state_manager",
                        data={
                            'action': 'resource_deleted',
                            'resource_id': resource_id,
                            'resource_type': resource.resource_type.value
                        }
                    )
                    await self.event_bus.publish(event)
                
                logging.info(f"Resource deleted: {resource_id}")
    
    async def create_snapshot(self, name: str = None) -> StateSnapshot:
        """Create state snapshot"""
        snapshot = StateSnapshot(
            metadata={
                'name': name or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'resource_count': len(self.resources)
            }
        )
        
        # Copy current resources
        with self._lock:
            snapshot.resources = copy.deepcopy(self.resources)
        
        # Save snapshot
        await self.backend.save_snapshot(snapshot)
        
        # Cache snapshot
        self.snapshots[snapshot.snapshot_id] = snapshot
        
        logging.info(f"Snapshot created: {snapshot.snapshot_id}")
        return snapshot
    
    async def restore_snapshot(self, snapshot_id: str):
        """Restore from snapshot"""
        snapshot = await self.backend.load_snapshot(snapshot_id)
        
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
        
        # Replace current state
        with self._lock:
            self.resources = copy.deepcopy(snapshot.resources)
        
        # Persist all resources
        for resource in self.resources.values():
            await self.backend.save_resource(resource)
        
        # Emit event
        if self.event_bus:
            event = Event(
                event_type=EventType.INFRA_STATE_DRIFT,
                source="nexus.state_manager",
                data={
                    'action': 'snapshot_restored',
                    'snapshot_id': snapshot_id,
                    'resource_count': len(self.resources)
                }
            )
            await self.event_bus.publish(event)
        
        logging.info(f"Snapshot restored: {snapshot_id}")
    
    async def detect_drift(self, resource_id: str = None) -> List[DriftDetection]:
        """Detect infrastructure drift"""
        drifts = []
        
        if resource_id:
            # Check single resource
            resource = await self.get_resource(resource_id)
            if resource:
                # Compare with actual state (would need discovery integration)
                # For now, just return empty list
                pass
        else:
            # Check all resources
            resources = await self.list_resources()
            
            for resource in resources:
                # Get current actual state
                actual_resource = await self._discover_actual_state(resource)
                
                if actual_resource:
                    resource_drifts = self.drift_analyzer.analyze(resource, actual_resource)
                    drifts.extend(resource_drifts)
        
        # Emit drift events
        for drift in drifts:
            if self.event_bus:
                event = Event(
                    event_type=EventType.INFRA_STATE_DRIFT,
                    source="nexus.state_manager",
                    data={
                        'drift_type': drift.drift_type,
                        'resource_id': drift.resource_id,
                        'severity': drift.severity,
                        'description': drift.description,
                        'expected_value': drift.expected_value,
                        'actual_value': drift.actual_value
                    },
                    severity=drift.severity
                )
                await self.event_bus.publish(event)
        
        return drifts
    
    async def _discover_actual_state(self, resource: Resource) -> Optional[Resource]:
        """Discover actual resource state (integration point)"""
        # This would integrate with network discovery, SSH connections, etc.
        # For now, return a copy with potential changes for demo
        
        if resource.resource_type == ResourceType.NETWORK_DEVICE:
            # Simulate network device state discovery
            actual = copy.deepcopy(resource)
            # Simulate some drift
            if 'last_seen' in actual.properties:
                actual.properties['last_seen'] = datetime.now().isoformat()
            return actual
        
        return None
    
    async def _drift_check_loop(self):
        """Background drift checking loop"""
        while self._running:
            try:
                # Run drift detection
                drifts = await self.detect_drift()
                
                if drifts:
                    logging.info(f"Drift detection found {len(drifts)} issues")
                    
                    # Auto-remediation if enabled
                    if self.auto_remediation:
                        await self._auto_remediate(drifts)
                
                # Wait for next check
                await asyncio.sleep(self.drift_check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Drift check failed: {e}")
                await asyncio.sleep(60)  # Wait a minute before retry
    
    async def _auto_remediate(self, drifts: List[DriftDetection]):
        """Auto-remediate detected drifts"""
        for drift in drifts:
            try:
                if drift.severity in ['high', 'critical']:
                    # Attempt remediation
                    await self._remediate_drift(drift)
                    
            except Exception as e:
                logging.error(f"Remediation failed for {drift.resource_id}: {e}")
    
    async def _remediate_drift(self, drift: DriftDetection):
        """Remediate specific drift (integration point)"""
        # This would integrate with configuration management, service restarts, etc.
        logging.info(f"Remediating drift: {drift.description}")
        
        if self.event_bus:
            event = Event(
                event_type=EventType.INFRA_REMEDIATION_STARTED,
                source="nexus.state_manager",
                data={
                    'drift_type': drift.drift_type,
                    'resource_id': drift.resource_id,
                    'action': 'auto_remediation'
                }
            )
            await self.event_bus.publish(event)

def main():
    """Demo of state management system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create backend and state manager
        backend = FileStateBackend(Path("/tmp/nexus_state"))
        state_manager = StateManager(backend)
        
        await state_manager.start()
        
        # Create test resources
        server = Resource(
            resource_id="server_001",
            resource_type=ResourceType.SERVER,
            name="web-server-01",
            state=ResourceState.ACTIVE,
            properties={
                'ip': '10.0.0.100',
                'hostname': 'web01.example.com',
                'os': 'Ubuntu 22.04',
                'services': ['nginx', 'postgresql']
            }
        )
        
        await state_manager.register_resource(server)
        
        # Create snapshot
        snapshot = await state_manager.create_snapshot("initial_state")
        print(f"Created snapshot: {snapshot.snapshot_id}")
        
        # Update resource
        await state_manager.update_resource("server_001", {
            'services': ['nginx', 'postgresql', 'redis'],
            'last_updated': datetime.now().isoformat()
        })
        
        # Check for drift
        drifts = await state_manager.detect_drift()
        print(f"Detected drifts: {len(drifts)}")
        
        # List resources
        resources = await state_manager.list_resources()
        print(f"Total resources: {len(resources)}")
        
        await state_manager.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()