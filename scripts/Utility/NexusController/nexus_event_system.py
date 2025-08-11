#!/usr/bin/env python3
"""
NexusController v2.0 Event-Driven Architecture
Advanced event bus and reactive automation system
"""

import os
import sys
import json
import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import weakref
from collections import defaultdict, deque

try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiokafka
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

class EventType(Enum):
    """Event types for infrastructure management"""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    
    # Network events
    NETWORK_SCAN_STARTED = "network.scan.started"
    NETWORK_SCAN_COMPLETED = "network.scan.completed"
    DEVICE_DISCOVERED = "network.device.discovered"
    DEVICE_LOST = "network.device.lost"
    DEVICE_STATE_CHANGED = "network.device.state_changed"
    
    # SSH events
    SSH_CONNECTION_ESTABLISHED = "ssh.connection.established"
    SSH_CONNECTION_FAILED = "ssh.connection.failed"
    SSH_CONNECTION_CLOSED = "ssh.connection.closed"
    SSH_COMMAND_EXECUTED = "ssh.command.executed"
    
    # Security events
    SECURITY_ALERT = "security.alert"
    AUTHENTICATION_SUCCESS = "security.auth.success"
    AUTHENTICATION_FAILURE = "security.auth.failure"
    UNAUTHORIZED_ACCESS = "security.unauthorized"
    
    # Infrastructure events
    INFRA_STATE_DRIFT = "infra.state.drift"
    INFRA_REMEDIATION_STARTED = "infra.remediation.started"
    INFRA_REMEDIATION_COMPLETED = "infra.remediation.completed"
    
    # Cloud events
    CLOUD_SYNC_STARTED = "cloud.sync.started"
    CLOUD_SYNC_COMPLETED = "cloud.sync.completed"
    CLOUD_BACKUP_CREATED = "cloud.backup.created"
    
    # Custom events
    CUSTOM_EVENT = "custom.event"

@dataclass
class Event:
    """Infrastructure event data structure"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM_EVENT
    source: str = "nexus.controller"
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    severity: str = "info"  # debug, info, warning, error, critical
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        data = data.copy()
        data['event_type'] = EventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event"""
        pass
    
    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can process the event"""
        pass

class EventFilter:
    """Event filtering and routing logic"""
    
    def __init__(self):
        self.filters = {}
    
    def add_filter(self, name: str, condition: Callable[[Event], bool]):
        """Add a named filter condition"""
        self.filters[name] = condition
    
    def matches(self, event: Event, filter_names: List[str] = None) -> bool:
        """Check if event matches specified filters"""
        if not filter_names:
            return True
        
        for filter_name in filter_names:
            if filter_name in self.filters:
                if not self.filters[filter_name](event):
                    return False
        return True

class EventStore:
    """Event persistence and querying"""
    
    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self.events = deque(maxlen=10000)  # In-memory store with rotation
        self.event_index = defaultdict(list)  # Index by event type
        self._lock = threading.RLock()
    
    async def store(self, event: Event):
        """Store an event"""
        with self._lock:
            self.events.append(event)
            self.event_index[event.event_type.value].append(event)
            
            # Maintain index size
            if len(self.event_index[event.event_type.value]) > 1000:
                self.event_index[event.event_type.value] = \
                    self.event_index[event.event_type.value][-1000:]
    
    async def query(self, 
                   event_types: List[EventType] = None,
                   start_time: datetime = None,
                   end_time: datetime = None,
                   source: str = None,
                   limit: int = 100) -> List[Event]:
        """Query events with filters"""
        with self._lock:
            results = []
            
            if event_types:
                # Query specific event types
                for event_type in event_types:
                    events = self.event_index.get(event_type.value, [])
                    results.extend(events)
            else:
                # Query all events
                results = list(self.events)
            
            # Apply filters
            if start_time:
                results = [e for e in results if e.timestamp >= start_time]
            if end_time:
                results = [e for e in results if e.timestamp <= end_time]
            if source:
                results = [e for e in results if e.source == source]
            
            # Sort by timestamp (newest first) and limit
            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[:limit]

class EventBus:
    """Central event bus for publish/subscribe messaging"""
    
    def __init__(self, backend: str = "memory"):
        self.backend = backend
        self.subscribers = defaultdict(list)
        self.event_store = EventStore()
        self.event_filter = EventFilter()
        self._running = False
        self._tasks = []
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics = {
            'events_published': 0,
            'events_processed': 0,
            'handlers_executed': 0,
            'errors': 0
        }
        
        logging.info(f"EventBus initialized with backend: {backend}")
    
    def subscribe(self, event_types: Union[EventType, List[EventType]], 
                 handler: EventHandler,
                 filters: List[str] = None):
        """Subscribe handler to specific event types"""
        if isinstance(event_types, EventType):
            event_types = [event_types]
        
        with self._lock:
            for event_type in event_types:
                self.subscribers[event_type].append({
                    'handler': handler,
                    'filters': filters or []
                })
        
        logging.info(f"Handler subscribed to {len(event_types)} event types")
    
    def unsubscribe(self, event_types: Union[EventType, List[EventType]], 
                   handler: EventHandler):
        """Unsubscribe handler from event types"""
        if isinstance(event_types, EventType):
            event_types = [event_types]
        
        with self._lock:
            for event_type in event_types:
                self.subscribers[event_type] = [
                    sub for sub in self.subscribers[event_type]
                    if sub['handler'] != handler
                ]
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        try:
            # Store event
            await self.event_store.store(event)
            
            # Update metrics
            self.metrics['events_published'] += 1
            
            # Find and notify subscribers
            subscribers = self.subscribers.get(event.event_type, [])
            
            for subscriber in subscribers:
                handler = subscriber['handler']
                filters = subscriber['filters']
                
                try:
                    # Check filters
                    if not self.event_filter.matches(event, filters):
                        continue
                    
                    # Check if handler can process event
                    if not handler.can_handle(event):
                        continue
                    
                    # Execute handler asynchronously
                    task = asyncio.create_task(self._execute_handler(handler, event))
                    self._tasks.append(task)
                    
                except Exception as e:
                    logging.error(f"Error processing event {event.event_id}: {e}")
                    self.metrics['errors'] += 1
            
            self.metrics['events_processed'] += 1
            logging.debug(f"Event published: {event.event_type.value}")
            
        except Exception as e:
            logging.error(f"Error publishing event: {e}")
            self.metrics['errors'] += 1
    
    async def _execute_handler(self, handler: EventHandler, event: Event):
        """Execute event handler with error handling"""
        try:
            await handler.handle(event)
            self.metrics['handlers_executed'] += 1
        except Exception as e:
            logging.error(f"Handler execution failed: {e}")
            self.metrics['errors'] += 1
            
            # Publish error event
            error_event = Event(
                event_type=EventType.SYSTEM_ERROR,
                source="nexus.event_bus",
                data={
                    'original_event_id': event.event_id,
                    'handler': str(handler.__class__.__name__),
                    'error': str(e)
                },
                severity="error"
            )
            # Avoid infinite recursion by not publishing error events for error events
            if event.event_type != EventType.SYSTEM_ERROR:
                await self.publish(error_event)
    
    async def query_events(self, **kwargs) -> List[Event]:
        """Query stored events"""
        return await self.event_store.query(**kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return self.metrics.copy()
    
    async def start(self):
        """Start the event bus"""
        self._running = True
        logging.info("EventBus started")
    
    async def stop(self):
        """Stop the event bus"""
        self._running = False
        
        # Wait for pending tasks
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logging.info("EventBus stopped")

# Built-in Event Handlers

class LoggingEventHandler(EventHandler):
    """Handler that logs all events"""
    
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("nexus.events")
        self.log_level = getattr(logging, log_level.upper())
    
    async def handle(self, event: Event):
        """Log the event"""
        message = f"Event: {event.event_type.value} from {event.source}"
        if event.data:
            message += f" - {json.dumps(event.data, default=str)}"
        
        severity_level = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(event.severity, logging.INFO)
        
        self.logger.log(severity_level, message)
    
    def can_handle(self, event: Event) -> bool:
        """Can handle all events"""
        return True

class MetricsEventHandler(EventHandler):
    """Handler that collects metrics from events"""
    
    def __init__(self):
        self.metrics = defaultdict(int)
        self._lock = threading.RLock()
    
    async def handle(self, event: Event):
        """Update metrics"""
        with self._lock:
            self.metrics[f"events.{event.event_type.value}"] += 1
            self.metrics[f"sources.{event.source}"] += 1
            self.metrics[f"severity.{event.severity}"] += 1
    
    def can_handle(self, event: Event) -> bool:
        """Can handle all events"""
        return True
    
    def get_metrics(self) -> Dict[str, int]:
        """Get collected metrics"""
        with self._lock:
            return dict(self.metrics)

class SecurityEventHandler(EventHandler):
    """Handler for security-related events"""
    
    def __init__(self, alert_threshold: int = 5):
        self.alert_threshold = alert_threshold
        self.failed_attempts = defaultdict(list)
        self._lock = threading.RLock()
    
    async def handle(self, event: Event):
        """Handle security events"""
        if event.event_type == EventType.AUTHENTICATION_FAILURE:
            await self._handle_auth_failure(event)
        elif event.event_type == EventType.UNAUTHORIZED_ACCESS:
            await self._handle_unauthorized_access(event)
        elif event.event_type == EventType.SECURITY_ALERT:
            await self._handle_security_alert(event)
    
    async def _handle_auth_failure(self, event: Event):
        """Handle authentication failures"""
        source_ip = event.data.get('source_ip', 'unknown')
        
        with self._lock:
            # Track failed attempts
            now = datetime.now()
            self.failed_attempts[source_ip].append(now)
            
            # Clean old attempts (last hour only)
            cutoff = now - timedelta(hours=1)
            self.failed_attempts[source_ip] = [
                attempt for attempt in self.failed_attempts[source_ip]
                if attempt > cutoff
            ]
            
            # Check if threshold exceeded
            if len(self.failed_attempts[source_ip]) >= self.alert_threshold:
                # Generate security alert
                alert_event = Event(
                    event_type=EventType.SECURITY_ALERT,
                    source="nexus.security_handler",
                    data={
                        'alert_type': 'brute_force_detected',
                        'source_ip': source_ip,
                        'attempt_count': len(self.failed_attempts[source_ip]),
                        'time_window': '1 hour'
                    },
                    severity="critical"
                )
                
                # Would normally publish this, but we need access to event bus
                logging.critical(f"Security Alert: Brute force detected from {source_ip}")
    
    async def _handle_unauthorized_access(self, event: Event):
        """Handle unauthorized access attempts"""
        logging.warning(f"Unauthorized access attempt: {event.data}")
    
    async def _handle_security_alert(self, event: Event):
        """Handle general security alerts"""
        logging.error(f"Security Alert: {event.data}")
    
    def can_handle(self, event: Event) -> bool:
        """Handle security-related events"""
        return event.event_type in [
            EventType.AUTHENTICATION_FAILURE,
            EventType.UNAUTHORIZED_ACCESS,
            EventType.SECURITY_ALERT
        ]

class ReactiveAutomationEngine:
    """Reactive automation engine for infrastructure events"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.rules = []
        self.actions = {}
        self._setup_default_rules()
    
    def add_rule(self, name: str, 
                condition: Callable[[Event], bool],
                action: Callable[[Event], Any],
                cooldown: timedelta = None):
        """Add automation rule"""
        rule = {
            'name': name,
            'condition': condition,
            'action': action,
            'cooldown': cooldown,
            'last_executed': None
        }
        self.rules.append(rule)
        logging.info(f"Automation rule added: {name}")
    
    def _setup_default_rules(self):
        """Setup default automation rules"""
        
        # Auto-reconnect on SSH failure
        self.add_rule(
            name="ssh_auto_reconnect",
            condition=lambda e: e.event_type == EventType.SSH_CONNECTION_FAILED,
            action=self._retry_ssh_connection,
            cooldown=timedelta(minutes=5)
        )
        
        # Network rescan on device loss
        self.add_rule(
            name="device_loss_rescan",
            condition=lambda e: e.event_type == EventType.DEVICE_LOST,
            action=self._trigger_network_rescan,
            cooldown=timedelta(minutes=10)
        )
        
        # Auto-backup on configuration changes
        self.add_rule(
            name="config_change_backup",
            condition=lambda e: e.event_type == EventType.INFRA_STATE_DRIFT and 
                              e.data.get('component') == 'configuration',
            action=self._trigger_backup,
            cooldown=timedelta(hours=1)
        )
    
    async def _retry_ssh_connection(self, event: Event):
        """Retry failed SSH connection"""
        logging.info(f"Auto-retry SSH connection: {event.data}")
        # Implementation would integrate with SSHManager
    
    async def _trigger_network_rescan(self, event: Event):
        """Trigger network rescan on device loss"""
        logging.info(f"Auto-triggering network rescan due to device loss: {event.data}")
        # Implementation would integrate with NetworkDiscovery
    
    async def _trigger_backup(self, event: Event):
        """Trigger backup on configuration changes"""
        logging.info(f"Auto-triggering backup due to config changes: {event.data}")
        # Implementation would integrate with BackupManager
    
    async def process_event(self, event: Event):
        """Process event against automation rules"""
        for rule in self.rules:
            try:
                # Check cooldown
                if rule['last_executed'] and rule['cooldown']:
                    if datetime.now() - rule['last_executed'] < rule['cooldown']:
                        continue
                
                # Check condition
                if rule['condition'](event):
                    logging.info(f"Executing automation rule: {rule['name']}")
                    
                    # Execute action
                    result = rule['action'](event)
                    if asyncio.iscoroutine(result):
                        await result
                    
                    # Update last executed
                    rule['last_executed'] = datetime.now()
                    
            except Exception as e:
                logging.error(f"Automation rule execution failed: {rule['name']} - {e}")

# Event Bus Factory

class EventBusFactory:
    """Factory for creating event bus instances"""
    
    @staticmethod
    def create_event_bus(backend: str = "memory", **kwargs) -> EventBus:
        """Create event bus with specified backend"""
        
        if backend == "memory":
            return EventBus(backend="memory")
        
        elif backend == "redis" and REDIS_AVAILABLE:
            # Redis-based event bus (future implementation)
            return EventBus(backend="redis")
        
        elif backend == "kafka" and KAFKA_AVAILABLE:
            # Kafka-based event bus (future implementation)
            return EventBus(backend="kafka")
        
        else:
            logging.warning(f"Backend '{backend}' not available, falling back to memory")
            return EventBus(backend="memory")

# Integration Helper

class NexusEventIntegration:
    """Integration helper for NexusController components"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.automation_engine = ReactiveAutomationEngine(event_bus)
        
        # Setup default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default event handlers"""
        
        # Logging handler
        logging_handler = LoggingEventHandler()
        self.event_bus.subscribe(
            [event_type for event_type in EventType],
            logging_handler
        )
        
        # Metrics handler
        metrics_handler = MetricsEventHandler()
        self.event_bus.subscribe(
            [event_type for event_type in EventType],
            metrics_handler
        )
        
        # Security handler
        security_handler = SecurityEventHandler()
        self.event_bus.subscribe([
            EventType.AUTHENTICATION_FAILURE,
            EventType.UNAUTHORIZED_ACCESS,
            EventType.SECURITY_ALERT
        ], security_handler)
    
    async def emit_network_scan_started(self, network_range: str, scan_id: str):
        """Emit network scan started event"""
        event = Event(
            event_type=EventType.NETWORK_SCAN_STARTED,
            source="nexus.network_discovery",
            data={
                'network_range': network_range,
                'scan_id': scan_id
            }
        )
        await self.event_bus.publish(event)
    
    async def emit_device_discovered(self, device_info: Dict[str, Any]):
        """Emit device discovered event"""
        event = Event(
            event_type=EventType.DEVICE_DISCOVERED,
            source="nexus.network_discovery",
            data=device_info
        )
        await self.event_bus.publish(event)
    
    async def emit_ssh_connection_established(self, connection_info: Dict[str, Any]):
        """Emit SSH connection established event"""
        event = Event(
            event_type=EventType.SSH_CONNECTION_ESTABLISHED,
            source="nexus.ssh_manager",
            data=connection_info
        )
        await self.event_bus.publish(event)
    
    async def emit_security_alert(self, alert_type: str, details: Dict[str, Any]):
        """Emit security alert event"""
        event = Event(
            event_type=EventType.SECURITY_ALERT,
            source="nexus.security",
            data={
                'alert_type': alert_type,
                'details': details
            },
            severity="warning"
        )
        await self.event_bus.publish(event)

def main():
    """Demo of event system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create event bus
        event_bus = EventBusFactory.create_event_bus("memory")
        await event_bus.start()
        
        # Create integration
        integration = NexusEventIntegration(event_bus)
        
        # Emit some test events
        await integration.emit_network_scan_started("10.0.0.0/24", "scan_001")
        
        await integration.emit_device_discovered({
            'ip': '10.0.0.100',
            'hostname': 'test-server',
            'mac': '00:11:22:33:44:55'
        })
        
        await integration.emit_ssh_connection_established({
            'hostname': '10.0.0.100',
            'username': 'admin',
            'connection_id': 'conn_001'
        })
        
        # Wait a bit for processing
        await asyncio.sleep(1)
        
        # Show metrics
        metrics = event_bus.get_metrics()
        print(f"Event Bus Metrics: {metrics}")
        
        # Query events
        events = await event_bus.query_events(limit=10)
        print(f"Recent Events: {len(events)}")
        
        await event_bus.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()