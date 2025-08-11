#!/usr/bin/env python3
"""
NexusController v2.0 Advanced Monitoring and Alerting System
Comprehensive monitoring, metrics collection, and intelligent alerting
"""

import os
import sys
import json
import asyncio
import logging
import threading
import statistics
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, NamedTuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from pathlib import Path
import collections

# Import core systems
from nexus_event_system import Event, EventType, EventBus
from nexus_provider_abstraction import ProviderType, CloudResource

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"          # Monotonically increasing
    GAUGE = "gauge"             # Point-in-time value
    HISTOGRAM = "histogram"      # Distribution of values
    SUMMARY = "summary"         # Pre-calculated quantiles
    RATE = "rate"               # Per-second rate

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertState(Enum):
    """Alert states"""
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class MonitoringTarget(Enum):
    """Monitoring targets"""
    SYSTEM = "system"
    NETWORK = "network"
    APPLICATION = "application"
    CLOUD_RESOURCE = "cloud_resource"
    SERVICE = "service"
    CUSTOM = "custom"

@dataclass
class MetricValue:
    """Single metric measurement"""
    
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels
        }

@dataclass
class Metric:
    """Metric definition and data"""
    
    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    values: collections.deque = field(default_factory=lambda: collections.deque(maxlen=1000))
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_value(self, value: Union[int, float], labels: Dict[str, str] = None):
        """Add metric value"""
        metric_value = MetricValue(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.values.append(metric_value)
    
    def get_latest_value(self) -> Optional[MetricValue]:
        """Get latest metric value"""
        return self.values[-1] if self.values else None
    
    def get_values_in_range(self, start_time: datetime, end_time: datetime) -> List[MetricValue]:
        """Get values within time range"""
        return [
            v for v in self.values 
            if start_time <= v.timestamp <= end_time
        ]
    
    def get_stats(self, duration: timedelta = None) -> Dict[str, float]:
        """Get statistical summary"""
        if not self.values:
            return {}
        
        # Filter by duration if specified
        values_to_analyze = self.values
        if duration:
            cutoff_time = datetime.now() - duration
            values_to_analyze = [v for v in self.values if v.timestamp >= cutoff_time]
        
        if not values_to_analyze:
            return {}
        
        numeric_values = [v.value for v in values_to_analyze]
        
        stats = {
            'count': len(numeric_values),
            'min': min(numeric_values),
            'max': max(numeric_values),
            'mean': statistics.mean(numeric_values),
            'latest': numeric_values[-1]
        }
        
        if len(numeric_values) > 1:
            stats['stdev'] = statistics.stdev(numeric_values)
            stats['median'] = statistics.median(numeric_values)
        
        return stats

@dataclass
class AlertRule:
    """Alert rule definition"""
    
    rule_id: str
    name: str
    metric_name: str
    condition: str  # e.g., "> 80", "< 10", "== 0"
    severity: AlertSeverity
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    cooldown: timedelta = field(default_factory=lambda: timedelta(minutes=15))
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    
    def evaluate(self, metric: Metric) -> bool:
        """Evaluate rule against metric"""
        if not self.enabled:
            return False
        
        latest_value = metric.get_latest_value()
        if not latest_value:
            return False
        
        # Check cooldown
        if self.last_triggered and self.cooldown:
            if datetime.now() - self.last_triggered < self.cooldown:
                return False
        
        # Parse and evaluate condition
        try:
            value = latest_value.value
            condition = self.condition.strip()
            
            if condition.startswith('>='):
                threshold = float(condition[2:].strip())
                return value >= threshold
            elif condition.startswith('<='):
                threshold = float(condition[2:].strip())
                return value <= threshold
            elif condition.startswith('>'):
                threshold = float(condition[1:].strip())
                return value > threshold
            elif condition.startswith('<'):
                threshold = float(condition[1:].strip())
                return value < threshold
            elif condition.startswith('=='):
                threshold = float(condition[2:].strip())
                return abs(value - threshold) < 0.001  # Float comparison
            elif condition.startswith('!='):
                threshold = float(condition[2:].strip())
                return abs(value - threshold) >= 0.001
            else:
                logging.warning(f"Unknown condition format: {condition}")
                return False
                
        except (ValueError, IndexError) as e:
            logging.error(f"Failed to evaluate rule {self.rule_id}: {e}")
            return False

@dataclass
class Alert:
    """Active alert instance"""
    
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    metric_name: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    state: AlertState = AlertState.PENDING
    message: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    value: Union[int, float] = 0
    threshold: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['severity'] = self.severity.value
        result['state'] = self.state.value
        result['started_at'] = self.started_at.isoformat()
        result['last_updated'] = self.last_updated.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        return result

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self._setup_system_metrics()
    
    def _setup_system_metrics(self):
        """Setup system metrics"""
        self.metrics['cpu_percent'] = Metric(
            name='cpu_percent',
            metric_type=MetricType.GAUGE,
            description='CPU utilization percentage',
            unit='percent'
        )
        
        self.metrics['memory_percent'] = Metric(
            name='memory_percent',
            metric_type=MetricType.GAUGE,
            description='Memory utilization percentage',
            unit='percent'
        )
        
        self.metrics['disk_percent'] = Metric(
            name='disk_percent',
            metric_type=MetricType.GAUGE,
            description='Disk utilization percentage',
            unit='percent'
        )
        
        self.metrics['network_bytes_sent'] = Metric(
            name='network_bytes_sent',
            metric_type=MetricType.COUNTER,
            description='Network bytes sent',
            unit='bytes'
        )
        
        self.metrics['network_bytes_recv'] = Metric(
            name='network_bytes_recv',
            metric_type=MetricType.COUNTER,
            description='Network bytes received',
            unit='bytes'
        )
        
        self.metrics['load_average'] = Metric(
            name='load_average',
            metric_type=MetricType.GAUGE,
            description='System load average (1 minute)',
            unit='load'
        )
    
    async def collect_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_percent'].add_value(cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics['memory_percent'].add_value(memory.percent)
            
            # Disk metrics (root filesystem)
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics['disk_percent'].add_value(disk_percent)
            
            # Network metrics
            network = psutil.net_io_counters()
            self.metrics['network_bytes_sent'].add_value(network.bytes_sent)
            self.metrics['network_bytes_recv'].add_value(network.bytes_recv)
            
            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()[0]  # 1-minute load average
                self.metrics['load_average'].add_value(load_avg)
            except (OSError, AttributeError):
                # Windows doesn't have getloadavg
                pass
            
        except Exception as e:
            logging.error(f"Failed to collect system metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Metric]:
        """Get all system metrics"""
        return self.metrics.copy()

class NetworkMonitor:
    """Network infrastructure monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self.device_stats = {}
        self._setup_network_metrics()
    
    def _setup_network_metrics(self):
        """Setup network metrics"""
        self.metrics['devices_discovered'] = Metric(
            name='devices_discovered',
            metric_type=MetricType.GAUGE,
            description='Number of discovered network devices',
            unit='count'
        )
        
        self.metrics['devices_online'] = Metric(
            name='devices_online',
            metric_type=MetricType.GAUGE,
            description='Number of online network devices',
            unit='count'
        )
        
        self.metrics['scan_duration'] = Metric(
            name='scan_duration',
            metric_type=MetricType.HISTOGRAM,
            description='Network scan duration',
            unit='seconds'
        )
        
        self.metrics['ping_response_time'] = Metric(
            name='ping_response_time',
            metric_type=MetricType.HISTOGRAM,
            description='Ping response time',
            unit='milliseconds'
        )
    
    async def collect_metrics(self, network_devices: List[Dict[str, Any]] = None):
        """Collect network metrics"""
        try:
            if network_devices is None:
                network_devices = []  # Would integrate with NetworkDiscovery
            
            # Device counts
            total_devices = len(network_devices)
            online_devices = sum(1 for device in network_devices 
                                if device.get('status') == 'online')
            
            self.metrics['devices_discovered'].add_value(total_devices)
            self.metrics['devices_online'].add_value(online_devices)
            
            # Mock ping metrics (would integrate with actual ping functionality)
            import random
            ping_time = random.uniform(1.0, 50.0)  # Mock ping time
            self.metrics['ping_response_time'].add_value(ping_time)
            
        except Exception as e:
            logging.error(f"Failed to collect network metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Metric]:
        """Get all network metrics"""
        return self.metrics.copy()

class ApplicationMonitor:
    """Application-specific monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self._setup_application_metrics()
    
    def _setup_application_metrics(self):
        """Setup application metrics"""
        self.metrics['ssh_connections_active'] = Metric(
            name='ssh_connections_active',
            metric_type=MetricType.GAUGE,
            description='Active SSH connections',
            unit='count'
        )
        
        self.metrics['ssh_connection_failures'] = Metric(
            name='ssh_connection_failures',
            metric_type=MetricType.COUNTER,
            description='SSH connection failures',
            unit='count'
        )
        
        self.metrics['backup_operations'] = Metric(
            name='backup_operations',
            metric_type=MetricType.COUNTER,
            description='Backup operations completed',
            unit='count'
        )
        
        self.metrics['security_events'] = Metric(
            name='security_events',
            metric_type=MetricType.COUNTER,
            description='Security events detected',
            unit='count'
        )
        
        self.metrics['api_request_duration'] = Metric(
            name='api_request_duration',
            metric_type=MetricType.HISTOGRAM,
            description='API request duration',
            unit='seconds'
        )
    
    def record_ssh_connection(self, success: bool):
        """Record SSH connection attempt"""
        if success:
            current_count = 0
            if self.metrics['ssh_connections_active'].values:
                current_count = self.metrics['ssh_connections_active'].get_latest_value().value
            self.metrics['ssh_connections_active'].add_value(current_count + 1)
        else:
            current_count = 0
            if self.metrics['ssh_connection_failures'].values:
                current_count = self.metrics['ssh_connection_failures'].get_latest_value().value
            self.metrics['ssh_connection_failures'].add_value(current_count + 1)
    
    def record_backup_operation(self):
        """Record backup operation"""
        current_count = 0
        if self.metrics['backup_operations'].values:
            current_count = self.metrics['backup_operations'].get_latest_value().value
        self.metrics['backup_operations'].add_value(current_count + 1)
    
    def record_security_event(self):
        """Record security event"""
        current_count = 0
        if self.metrics['security_events'].values:
            current_count = self.metrics['security_events'].get_latest_value().value
        self.metrics['security_events'].add_value(current_count + 1)
    
    def record_api_request(self, duration: float):
        """Record API request duration"""
        self.metrics['api_request_duration'].add_value(duration)
    
    def get_metrics(self) -> Dict[str, Metric]:
        """Get all application metrics"""
        return self.metrics.copy()

class AlertManager:
    """Alert management and notification system"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history = collections.deque(maxlen=1000)
        self.notification_channels = []
        self._lock = threading.RLock()
        
        # Setup default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        
        # High CPU usage
        self.add_rule(AlertRule(
            rule_id="high_cpu",
            name="High CPU Usage",
            metric_name="cpu_percent",
            condition="> 80",
            severity=AlertSeverity.HIGH,
            description="CPU usage is above 80%",
            duration=timedelta(minutes=2)
        ))
        
        # High memory usage
        self.add_rule(AlertRule(
            rule_id="high_memory",
            name="High Memory Usage",
            metric_name="memory_percent",
            condition="> 90",
            severity=AlertSeverity.CRITICAL,
            description="Memory usage is above 90%",
            duration=timedelta(minutes=1)
        ))
        
        # High disk usage
        self.add_rule(AlertRule(
            rule_id="high_disk",
            name="High Disk Usage",
            metric_name="disk_percent",
            condition="> 85",
            severity=AlertSeverity.HIGH,
            description="Disk usage is above 85%",
            duration=timedelta(minutes=5)
        ))
        
        # No network devices online
        self.add_rule(AlertRule(
            rule_id="no_devices_online",
            name="No Network Devices Online",
            metric_name="devices_online",
            condition="== 0",
            severity=AlertSeverity.CRITICAL,
            description="No network devices are responding",
            duration=timedelta(minutes=3)
        ))
        
        # SSH connection failures
        self.add_rule(AlertRule(
            rule_id="ssh_failures",
            name="SSH Connection Failures",
            metric_name="ssh_connection_failures",
            condition="> 5",
            severity=AlertSeverity.MEDIUM,
            description="Multiple SSH connection failures detected",
            duration=timedelta(minutes=10)
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self._lock:
            self.rules[rule.rule_id] = rule
        logging.info(f"Alert rule added: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logging.info(f"Alert rule removed: {rule_id}")
    
    def evaluate_rules(self, metrics: Dict[str, Metric]):
        """Evaluate all rules against current metrics"""
        with self._lock:
            for rule in self.rules.values():
                if rule.metric_name in metrics:
                    metric = metrics[rule.metric_name]
                    
                    if rule.evaluate(metric):
                        self._trigger_alert(rule, metric)
                    else:
                        self._resolve_alert(rule.rule_id)
    
    def _trigger_alert(self, rule: AlertRule, metric: Metric):
        """Trigger an alert"""
        latest_value = metric.get_latest_value()
        if not latest_value:
            return
        
        # Check if alert is already active
        existing_alert = None
        for alert in self.active_alerts.values():
            if alert.rule_id == rule.rule_id:
                existing_alert = alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.last_updated = datetime.now()
            existing_alert.value = latest_value.value
            if existing_alert.state == AlertState.PENDING:
                existing_alert.state = AlertState.FIRING
        else:
            # Create new alert
            alert = Alert(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                metric_name=rule.metric_name,
                severity=rule.severity,
                state=AlertState.FIRING,
                message=f"{rule.description} (current: {latest_value.value})",
                labels=rule.labels.copy(),
                value=latest_value.value,
                threshold=rule.condition
            )
            
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            
            # Update rule trigger time
            rule.last_triggered = datetime.now()
            
            # Send notifications
            asyncio.create_task(self._send_notifications(alert))
            
            logging.warning(f"Alert triggered: {rule.name} - {alert.message}")
    
    def _resolve_alert(self, rule_id: str):
        """Resolve alerts for a rule"""
        alerts_to_resolve = [
            alert for alert in self.active_alerts.values()
            if alert.rule_id == rule_id and alert.state == AlertState.FIRING
        ]
        
        for alert in alerts_to_resolve:
            alert.state = AlertState.RESOLVED
            alert.resolved_at = datetime.now()
            alert.last_updated = datetime.now()
            
            # Remove from active alerts
            if alert.alert_id in self.active_alerts:
                del self.active_alerts[alert.alert_id]
            
            # Send resolution notification
            asyncio.create_task(self._send_notifications(alert, resolved=True))
            
            logging.info(f"Alert resolved: {alert.rule_name}")
    
    async def _send_notifications(self, alert: Alert, resolved: bool = False):
        """Send alert notifications"""
        try:
            # Emit event
            if self.event_bus:
                event_type = EventType.SECURITY_ALERT if alert.severity == AlertSeverity.CRITICAL else EventType.SYSTEM_ERROR
                
                event = Event(
                    event_type=event_type,
                    source="nexus.alert_manager",
                    data={
                        'alert_id': alert.alert_id,
                        'rule_name': alert.rule_name,
                        'metric_name': alert.metric_name,
                        'severity': alert.severity.value,
                        'state': alert.state.value,
                        'message': alert.message,
                        'value': alert.value,
                        'threshold': alert.threshold,
                        'resolved': resolved
                    },
                    severity=alert.severity.value
                )
                await self.event_bus.publish(event)
            
            # Send to notification channels
            for channel in self.notification_channels:
                try:
                    await channel.send_notification(alert, resolved)
                except Exception as e:
                    logging.error(f"Failed to send notification via {channel}: {e}")
                    
        except Exception as e:
            logging.error(f"Failed to send notifications for alert {alert.alert_id}: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        with self._lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self._lock:
            stats = {
                'total_rules': len(self.rules),
                'active_alerts': len(self.active_alerts),
                'alerts_by_severity': {},
                'alerts_by_state': {}
            }
            
            # Count by severity and state
            for alert in self.active_alerts.values():
                severity = alert.severity.value
                state = alert.state.value
                
                stats['alerts_by_severity'][severity] = stats['alerts_by_severity'].get(severity, 0) + 1
                stats['alerts_by_state'][state] = stats['alerts_by_state'].get(state, 0) + 1
            
            return stats

class NotificationChannel(ABC):
    """Abstract notification channel"""
    
    @abstractmethod
    async def send_notification(self, alert: Alert, resolved: bool = False):
        """Send notification for alert"""
        pass

class LogNotificationChannel(NotificationChannel):
    """Log-based notification channel"""
    
    def __init__(self, log_level: str = "WARNING"):
        self.logger = logging.getLogger("nexus.alerts")
        self.log_level = getattr(logging, log_level.upper())
    
    async def send_notification(self, alert: Alert, resolved: bool = False):
        """Send notification via logging"""
        status = "RESOLVED" if resolved else "TRIGGERED"
        message = f"ALERT {status}: {alert.rule_name} - {alert.message}"
        
        severity_levels = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }
        
        level = severity_levels.get(alert.severity, logging.WARNING)
        self.logger.log(level, message)

class MonitoringSystem:
    """Central monitoring and alerting system"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.system_monitor = SystemMonitor()
        self.network_monitor = NetworkMonitor()
        self.application_monitor = ApplicationMonitor()
        self.alert_manager = AlertManager(event_bus)
        
        # Setup notification channels
        self.alert_manager.notification_channels.append(LogNotificationChannel())
        
        # Background tasks
        self._running = False
        self._collection_task = None
        self._evaluation_task = None
        
        # Configuration
        self.collection_interval = timedelta(seconds=30)
        self.evaluation_interval = timedelta(seconds=60)
        
        logging.info("MonitoringSystem initialized")
    
    async def start(self):
        """Start monitoring system"""
        self._running = True
        
        # Start background tasks
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        
        logging.info("MonitoringSystem started")
    
    async def stop(self):
        """Stop monitoring system"""
        self._running = False
        
        # Cancel background tasks
        if self._collection_task:
            self._collection_task.cancel()
        if self._evaluation_task:
            self._evaluation_task.cancel()
        
        # Wait for tasks to complete
        tasks = [self._collection_task, self._evaluation_task]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logging.info("MonitoringSystem stopped")
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while self._running:
            try:
                # Collect from all monitors
                await self.system_monitor.collect_metrics()
                await self.network_monitor.collect_metrics()
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _evaluation_loop(self):
        """Background alert evaluation loop"""
        while self._running:
            try:
                # Get all metrics
                all_metrics = {}
                all_metrics.update(self.system_monitor.get_metrics())
                all_metrics.update(self.network_monitor.get_metrics())
                all_metrics.update(self.application_monitor.get_metrics())
                
                # Evaluate alert rules
                self.alert_manager.evaluate_rules(all_metrics)
                
                # Wait for next evaluation
                await asyncio.sleep(self.evaluation_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(60)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics from all monitors"""
        all_metrics = {}
        all_metrics.update(self.system_monitor.get_metrics())
        all_metrics.update(self.network_monitor.get_metrics())
        all_metrics.update(self.application_monitor.get_metrics())
        return all_metrics
    
    def get_monitoring_overview(self) -> Dict[str, Any]:
        """Get monitoring system overview"""
        all_metrics = self.get_all_metrics()
        alert_stats = self.alert_manager.get_alert_stats()
        
        overview = {
            'metrics': {
                'total_metrics': len(all_metrics),
                'system_metrics': len(self.system_monitor.get_metrics()),
                'network_metrics': len(self.network_monitor.get_metrics()),
                'application_metrics': len(self.application_monitor.get_metrics())
            },
            'alerts': alert_stats,
            'monitoring_status': 'running' if self._running else 'stopped',
            'last_collection': datetime.now().isoformat(),
            'collection_interval_seconds': self.collection_interval.total_seconds(),
            'evaluation_interval_seconds': self.evaluation_interval.total_seconds()
        }
        
        # Add latest values for key metrics
        key_metrics = ['cpu_percent', 'memory_percent', 'disk_percent', 'devices_online']
        overview['key_metrics'] = {}
        
        for metric_name in key_metrics:
            if metric_name in all_metrics:
                latest_value = all_metrics[metric_name].get_latest_value()
                if latest_value:
                    overview['key_metrics'][metric_name] = {
                        'value': latest_value.value,
                        'timestamp': latest_value.timestamp.isoformat(),
                        'unit': all_metrics[metric_name].unit
                    }
        
        return overview
    
    def add_custom_metric(self, name: str, metric_type: MetricType, 
                         description: str = "", unit: str = "") -> Metric:
        """Add custom metric"""
        metric = Metric(
            name=name,
            metric_type=metric_type,
            description=description,
            unit=unit
        )
        
        # Add to application monitor for now
        self.application_monitor.metrics[name] = metric
        
        logging.info(f"Custom metric added: {name}")
        return metric
    
    def record_custom_metric(self, name: str, value: Union[int, float], 
                           labels: Dict[str, str] = None):
        """Record value for custom metric"""
        if name in self.application_monitor.metrics:
            self.application_monitor.metrics[name].add_value(value, labels)
        else:
            logging.warning(f"Custom metric not found: {name}")

def main():
    """Demo of monitoring system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create monitoring system
        monitor = MonitoringSystem()
        await monitor.start()
        
        print("Monitoring system started. Collecting metrics...")
        
        # Let it run for a bit to collect metrics
        await asyncio.sleep(5)
        
        # Add some custom metrics
        custom_metric = monitor.add_custom_metric(
            "demo_counter",
            MetricType.COUNTER,
            "Demo counter metric",
            "count"
        )
        
        # Record some values
        for i in range(5):
            monitor.record_custom_metric("demo_counter", i * 10)
            await asyncio.sleep(1)
        
        # Get overview
        overview = monitor.get_monitoring_overview()
        print(f"Monitoring Overview:")
        print(f"  Total metrics: {overview['metrics']['total_metrics']}")
        print(f"  Active alerts: {overview['alerts']['active_alerts']}")
        print(f"  Alert rules: {overview['alerts']['total_rules']}")
        
        # Show key metrics
        print("Key Metrics:")
        for name, data in overview['key_metrics'].items():
            print(f"  {name}: {data['value']}{data['unit']}")
        
        # Show active alerts
        active_alerts = monitor.alert_manager.get_active_alerts()
        if active_alerts:
            print(f"Active Alerts: {len(active_alerts)}")
            for alert in active_alerts:
                print(f"  {alert.rule_name}: {alert.message}")
        else:
            print("No active alerts")
        
        # Simulate high CPU to trigger alert
        print("\nSimulating high CPU usage...")
        monitor.system_monitor.metrics['cpu_percent'].add_value(95.0)
        
        # Wait for alert evaluation
        await asyncio.sleep(5)
        
        # Check for new alerts
        active_alerts = monitor.alert_manager.get_active_alerts()
        if active_alerts:
            print(f"New Active Alerts: {len(active_alerts)}")
            for alert in active_alerts:
                print(f"  {alert.rule_name}: {alert.message}")
        
        await monitor.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()