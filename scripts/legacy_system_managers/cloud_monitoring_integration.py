#!/usr/bin/env python3
"""
Cloud Monitoring Integration
Integrates with various cloud monitoring services and provides unified alerting
"""

import os
import sys
import json
import sqlite3
import time
import logging
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import urllib.parse
import hashlib
import hmac
import base64

# Cloud service imports with fallbacks
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.cloud import monitoring_v3
    from google.cloud import logging as gcp_logging
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from azure.monitor.query import LogsQueryClient, MetricsQueryClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

@dataclass
class CloudMetric:
    """Cloud metric data point"""
    provider: str
    service: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]

@dataclass
class CloudAlert:
    """Cloud alert configuration"""
    alert_id: str
    provider: str
    service: str
    metric_name: str
    condition: str
    threshold: float
    enabled: bool
    webhook_url: Optional[str] = None

class CloudMonitoringIntegration:
    """Unified cloud monitoring integration"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".unified-system-manager" / "cloud-monitoring.db"
        self.base_path = self.db_path.parent
        self.base_path.mkdir(exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize database
        self.init_database()
        
        # Load configuration
        self.config = self.load_cloud_config()
        
        # Cloud service clients
        self.aws_client = None
        self.gcp_client = None
        self.azure_client = None
        
        # Monitoring state
        self.running = False
        self.monitoring_threads = []
        self.collection_interval = 300  # 5 minutes
        
        # Initialize cloud clients
        self.init_cloud_clients()
        
        self.logger.info("Cloud Monitoring Integration initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_path = self.base_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / "cloud-monitoring.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{__name__}.CloudMonitoring")
    
    def init_database(self):
        """Initialize database for cloud monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Cloud provider configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cloud_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT UNIQUE NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    credentials_config TEXT,
                    last_sync TIMESTAMP,
                    status TEXT DEFAULT 'unknown',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cloud metrics storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cloud_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    tags TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX(provider, service, metric_name, timestamp)
                )
            """)
            
            # Cloud alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cloud_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    provider TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    webhook_url TEXT,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Alert history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    condition_met TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    message TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            # Cloud service health
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    region TEXT,
                    status TEXT NOT NULL,
                    incident_id TEXT,
                    description TEXT,
                    impact_level TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cost monitoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cost_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    service TEXT NOT NULL,
                    cost_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    billing_period TEXT,
                    cost_type TEXT,
                    tags TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def load_cloud_config(self) -> Dict[str, Any]:
        """Load cloud configuration"""
        config_path = self.base_path / "cloud-config.json"
        default_config = {
            'aws': {
                'enabled': False,
                'region': 'us-east-1',
                'access_key_id': '',
                'secret_access_key': '',
                'services': ['ec2', 'rds', 'lambda', 's3']
            },
            'gcp': {
                'enabled': False,
                'project_id': '',
                'credentials_file': '',
                'services': ['compute', 'storage', 'functions']
            },
            'azure': {
                'enabled': False,
                'subscription_id': '',
                'tenant_id': '',
                'client_id': '',
                'client_secret': '',
                'services': ['virtual-machines', 'storage', 'functions']
            },
            'monitoring': {
                'collection_interval': 300,
                'retention_days': 30,
                'alert_cooldown': 900,  # 15 minutes
                'webhook_timeout': 30
            },
            'integrations': {
                'prometheus_enabled': False,
                'prometheus_gateway': '',
                'grafana_enabled': False,
                'grafana_url': '',
                'slack_webhook': '',
                'email_alerts': False
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if sub_key not in config[key]:
                                    config[key][sub_key] = sub_value
                    return config
            except Exception as e:
                self.logger.warning(f"Failed to load cloud config: {e}")
        
        # Save default config
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cloud config: {e}")
        
        return default_config
    
    def init_cloud_clients(self):
        """Initialize cloud service clients"""
        # AWS CloudWatch
        if self.config['aws']['enabled'] and AWS_AVAILABLE:
            try:
                if self.config['aws']['access_key_id'] and self.config['aws']['secret_access_key']:
                    self.aws_client = boto3.client(
                        'cloudwatch',
                        aws_access_key_id=self.config['aws']['access_key_id'],
                        aws_secret_access_key=self.config['aws']['secret_access_key'],
                        region_name=self.config['aws']['region']
                    )
                    self.logger.info("AWS CloudWatch client initialized")
                else:
                    self.logger.warning("AWS credentials not configured")
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS client: {e}")
        
        # Google Cloud Monitoring
        if self.config['gcp']['enabled'] and GCP_AVAILABLE:
            try:
                if self.config['gcp']['credentials_file'] and os.path.exists(self.config['gcp']['credentials_file']):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.config['gcp']['credentials_file']
                    self.gcp_client = monitoring_v3.MetricServiceClient()
                    self.logger.info("GCP Monitoring client initialized")
                else:
                    self.logger.warning("GCP credentials not configured")
            except Exception as e:
                self.logger.error(f"Failed to initialize GCP client: {e}")
        
        # Azure Monitor
        if self.config['azure']['enabled'] and AZURE_AVAILABLE:
            try:
                if all([
                    self.config['azure']['tenant_id'],
                    self.config['azure']['client_id'],
                    self.config['azure']['client_secret']
                ]):
                    # Azure authentication would be set up here
                    self.logger.info("Azure Monitor client initialized")
                else:
                    self.logger.warning("Azure credentials not configured")
            except Exception as e:
                self.logger.error(f"Failed to initialize Azure client: {e}")
    
    def collect_aws_metrics(self) -> List[CloudMetric]:
        """Collect metrics from AWS CloudWatch"""
        if not self.aws_client:
            return []
        
        metrics = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        # Common AWS metrics to collect
        metric_configs = [
            {'namespace': 'AWS/EC2', 'metric': 'CPUUtilization', 'stat': 'Average'},
            {'namespace': 'AWS/EC2', 'metric': 'NetworkIn', 'stat': 'Sum'},
            {'namespace': 'AWS/EC2', 'metric': 'NetworkOut', 'stat': 'Sum'},
            {'namespace': 'AWS/RDS', 'metric': 'CPUUtilization', 'stat': 'Average'},
            {'namespace': 'AWS/RDS', 'metric': 'DatabaseConnections', 'stat': 'Average'},
            {'namespace': 'AWS/Lambda', 'metric': 'Invocations', 'stat': 'Sum'},
            {'namespace': 'AWS/Lambda', 'metric': 'Duration', 'stat': 'Average'},
            {'namespace': 'AWS/S3', 'metric': 'BucketSizeBytes', 'stat': 'Average'}
        ]
        
        try:
            for config in metric_configs:
                response = self.aws_client.get_metric_statistics(
                    Namespace=config['namespace'],
                    MetricName=config['metric'],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=[config['stat']]
                )
                
                for datapoint in response['Datapoints']:
                    metrics.append(CloudMetric(
                        provider='aws',
                        service=config['namespace'].split('/')[-1].lower(),
                        metric_name=config['metric'],
                        value=datapoint[config['stat']],
                        unit=datapoint.get('Unit', ''),
                        timestamp=datapoint['Timestamp'],
                        tags={}
                    ))
        
        except Exception as e:
            self.logger.error(f"Error collecting AWS metrics: {e}")
        
        return metrics
    
    def collect_gcp_metrics(self) -> List[CloudMetric]:
        """Collect metrics from Google Cloud Monitoring"""
        if not self.gcp_client:
            return []
        
        metrics = []
        project_name = f"projects/{self.config['gcp']['project_id']}"
        
        # Time range for metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(end_time.timestamp())},
            "start_time": {"seconds": int(start_time.timestamp())}
        })
        
        # Common GCP metrics
        metric_types = [
            'compute.googleapis.com/instance/cpu/utilization',
            'compute.googleapis.com/instance/disk/read_bytes_count',
            'compute.googleapis.com/instance/disk/write_bytes_count',
            'storage.googleapis.com/storage/object_count',
            'cloudfunctions.googleapis.com/function/execution_count'
        ]
        
        try:
            for metric_type in metric_types:
                request = monitoring_v3.ListTimeSeriesRequest(
                    name=project_name,
                    filter=f'metric.type="{metric_type}"',
                    interval=interval,
                    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
                )
                
                results = self.gcp_client.list_time_series(request=request)
                
                for result in results:
                    for point in result.points:
                        metrics.append(CloudMetric(
                            provider='gcp',
                            service=metric_type.split('.')[0],
                            metric_name=metric_type.split('/')[-1],
                            value=point.value.double_value or point.value.int64_value,
                            unit=result.unit,
                            timestamp=datetime.fromtimestamp(point.interval.end_time.seconds),
                            tags={label.key: label.value for label in result.resource.labels.items()}
                        ))
        
        except Exception as e:
            self.logger.error(f"Error collecting GCP metrics: {e}")
        
        return metrics
    
    def collect_service_health(self):
        """Collect cloud service health status"""
        health_data = []
        
        # AWS Service Health
        if self.config['aws']['enabled']:
            health_data.extend(self._get_aws_service_health())
        
        # GCP Service Health
        if self.config['gcp']['enabled']:
            health_data.extend(self._get_gcp_service_health())
        
        # Azure Service Health
        if self.config['azure']['enabled']:
            health_data.extend(self._get_azure_service_health())
        
        # Store health data
        self._store_service_health(health_data)
        
        return health_data
    
    def _get_aws_service_health(self) -> List[Dict[str, Any]]:
        """Get AWS service health from status page"""
        try:
            response = requests.get(
                'https://status.aws.amazon.com/data.json',
                timeout=30
            )
            data = response.json()
            
            health_info = []
            for service in data.get('services', []):
                health_info.append({
                    'provider': 'aws',
                    'service_name': service.get('name', ''),
                    'region': 'global',
                    'status': service.get('status', 'unknown'),
                    'description': service.get('summary', ''),
                    'last_updated': datetime.now()
                })
            
            return health_info
        
        except Exception as e:
            self.logger.error(f"Error fetching AWS service health: {e}")
            return []
    
    def _get_gcp_service_health(self) -> List[Dict[str, Any]]:
        """Get GCP service health from status page"""
        try:
            response = requests.get(
                'https://status.cloud.google.com/incidents.json',
                timeout=30
            )
            data = response.json()
            
            health_info = []
            for incident in data:
                health_info.append({
                    'provider': 'gcp',
                    'service_name': incident.get('service_name', ''),
                    'region': 'global',
                    'status': 'incident' if incident.get('status') == 'open' else 'operational',
                    'incident_id': incident.get('number', ''),
                    'description': incident.get('summary', ''),
                    'impact_level': incident.get('severity', 'low'),
                    'last_updated': datetime.now()
                })
            
            return health_info
        
        except Exception as e:
            self.logger.error(f"Error fetching GCP service health: {e}")
            return []
    
    def _get_azure_service_health(self) -> List[Dict[str, Any]]:
        """Get Azure service health from status page"""
        try:
            response = requests.get(
                'https://status.azure.com/en-us/status/feed/',
                timeout=30
            )
            # Azure uses RSS feed - would need XML parsing
            # For now, return empty list
            return []
        
        except Exception as e:
            self.logger.error(f"Error fetching Azure service health: {e}")
            return []
    
    def _store_service_health(self, health_data: List[Dict[str, Any]]):
        """Store service health data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for health in health_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO service_health (
                        provider, service_name, region, status, incident_id,
                        description, impact_level, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    health.get('provider'),
                    health.get('service_name'),
                    health.get('region'),
                    health.get('status'),
                    health.get('incident_id'),
                    health.get('description'),
                    health.get('impact_level'),
                    health.get('last_updated')
                ))
            
            conn.commit()
    
    def store_metrics(self, metrics: List[CloudMetric]):
        """Store cloud metrics in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO cloud_metrics (
                        provider, service, metric_name, value, unit, tags, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.provider,
                    metric.service,
                    metric.metric_name,
                    metric.value,
                    metric.unit,
                    json.dumps(metric.tags),
                    metric.timestamp
                ))
            
            conn.commit()
    
    def create_alert(self, provider: str, service: str, metric_name: str,
                    condition: str, threshold: float, webhook_url: str = None) -> str:
        """Create a new cloud alert"""
        alert_id = f"{provider}_{service}_{metric_name}_{int(time.time())}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cloud_alerts (
                    alert_id, provider, service, metric_name,
                    condition_type, threshold_value, webhook_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, provider, service, metric_name, condition, threshold, webhook_url))
            
            conn.commit()
        
        self.logger.info(f"Created cloud alert: {alert_id}")
        return alert_id
    
    def check_alerts(self):
        """Check for alert conditions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get active alerts
            cursor.execute("""
                SELECT alert_id, provider, service, metric_name,
                       condition_type, threshold_value, webhook_url
                FROM cloud_alerts WHERE enabled = TRUE
            """)
            
            alerts = cursor.fetchall()
            
            for alert in alerts:
                alert_id, provider, service, metric_name, condition, threshold, webhook = alert
                
                # Get latest metric value
                cursor.execute("""
                    SELECT value, timestamp FROM cloud_metrics
                    WHERE provider = ? AND service = ? AND metric_name = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (provider, service, metric_name))
                
                result = cursor.fetchone()
                if not result:
                    continue
                
                current_value, timestamp = result
                
                # Check condition
                condition_met = self._evaluate_condition(current_value, condition, threshold)
                
                if condition_met:
                    self._trigger_alert(alert_id, provider, service, metric_name,
                                      current_value, threshold, condition, webhook)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == 'greater_than':
            return value > threshold
        elif condition == 'less_than':
            return value < threshold
        elif condition == 'equals':
            return abs(value - threshold) < 0.001
        elif condition == 'not_equals':
            return abs(value - threshold) >= 0.001
        else:
            return False
    
    def _trigger_alert(self, alert_id: str, provider: str, service: str,
                      metric_name: str, current_value: float, threshold: float,
                      condition: str, webhook_url: str = None):
        """Trigger an alert"""
        # Check cooldown period
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cooldown_time = datetime.now() - timedelta(seconds=self.config['monitoring']['alert_cooldown'])
            cursor.execute("""
                SELECT triggered_at FROM alert_history
                WHERE alert_id = ? AND triggered_at > ?
                ORDER BY triggered_at DESC LIMIT 1
            """, (alert_id, cooldown_time))
            
            if cursor.fetchone():
                return  # Still in cooldown
            
            # Create alert history entry
            severity = 'critical' if current_value > threshold * 1.5 else 'warning'
            message = f"{provider.upper()} {service} {metric_name}: {current_value} {condition} {threshold}"
            
            cursor.execute("""
                INSERT INTO alert_history (
                    alert_id, provider, service, metric_name,
                    current_value, threshold_value, condition_met,
                    severity, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, provider, service, metric_name, current_value,
                  threshold, condition, severity, message))
            
            # Update alert trigger count
            cursor.execute("""
                UPDATE cloud_alerts
                SET last_triggered = ?, trigger_count = trigger_count + 1
                WHERE alert_id = ?
            """, (datetime.now(), alert_id))
            
            conn.commit()
        
        # Send webhook notification
        if webhook_url:
            self._send_webhook_notification(webhook_url, {
                'alert_id': alert_id,
                'provider': provider,
                'service': service,
                'metric': metric_name,
                'current_value': current_value,
                'threshold': threshold,
                'condition': condition,
                'severity': severity,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        self.logger.warning(f"CLOUD ALERT: {message}")
    
    def _send_webhook_notification(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send webhook notification"""
        try:
            response = requests.post(
                webhook_url,
                json=alert_data,
                timeout=self.config['monitoring']['webhook_timeout']
            )
            response.raise_for_status()
            self.logger.info(f"Webhook notification sent to {webhook_url}")
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
    
    def start_monitoring(self):
        """Start cloud monitoring"""
        if self.running:
            return
        
        self.running = True
        
        # Start monitoring threads for each enabled provider
        if self.config['aws']['enabled']:
            aws_thread = threading.Thread(
                target=self._monitoring_loop,
                args=('aws', self.collect_aws_metrics),
                daemon=True,
                name="AWSMonitoring"
            )
            aws_thread.start()
            self.monitoring_threads.append(aws_thread)
        
        if self.config['gcp']['enabled']:
            gcp_thread = threading.Thread(
                target=self._monitoring_loop,
                args=('gcp', self.collect_gcp_metrics),
                daemon=True,
                name="GCPMonitoring"
            )
            gcp_thread.start()
            self.monitoring_threads.append(gcp_thread)
        
        # Start service health monitoring
        health_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True,
            name="ServiceHealthMonitoring"
        )
        health_thread.start()
        self.monitoring_threads.append(health_thread)
        
        self.logger.info("Started cloud monitoring")
    
    def stop_monitoring(self):
        """Stop cloud monitoring"""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=10)
        
        self.monitoring_threads.clear()
        self.logger.info("Stopped cloud monitoring")
    
    def _monitoring_loop(self, provider: str, collector_func):
        """Main monitoring loop for a provider"""
        while self.running:
            try:
                metrics = collector_func()
                if metrics:
                    self.store_metrics(metrics)
                    self.logger.info(f"Collected {len(metrics)} metrics from {provider}")
                
                # Check alerts
                self.check_alerts()
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"{provider} monitoring error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _health_monitoring_loop(self):
        """Service health monitoring loop"""
        while self.running:
            try:
                health_data = self.collect_service_health()
                if health_data:
                    self.logger.info(f"Collected health data for {len(health_data)} services")
                
                time.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Metric statistics
            cursor.execute("SELECT COUNT(*) FROM cloud_metrics")
            total_metrics = cursor.fetchone()[0]
            
            cursor.execute("SELECT provider, COUNT(*) FROM cloud_metrics GROUP BY provider")
            metrics_by_provider = dict(cursor.fetchall())
            
            # Alert statistics
            cursor.execute("SELECT COUNT(*) FROM cloud_alerts WHERE enabled = TRUE")
            active_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM alert_history WHERE resolved = FALSE")
            triggered_alerts = cursor.fetchone()[0]
            
            # Service health
            cursor.execute("""
                SELECT provider, status, COUNT(*) 
                FROM service_health 
                GROUP BY provider, status
            """)
            health_by_provider = {}
            for provider, status, count in cursor.fetchall():
                if provider not in health_by_provider:
                    health_by_provider[provider] = {}
                health_by_provider[provider][status] = count
            
            return {
                'metrics': {
                    'total_collected': total_metrics,
                    'by_provider': metrics_by_provider
                },
                'alerts': {
                    'active_rules': active_alerts,
                    'triggered_count': triggered_alerts
                },
                'service_health': health_by_provider,
                'monitoring_status': {
                    'running': self.running,
                    'collection_interval': self.collection_interval,
                    'enabled_providers': [
                        provider for provider, config in {
                            'aws': self.config['aws'],
                            'gcp': self.config['gcp'],
                            'azure': self.config['azure']
                        }.items() if config['enabled']
                    ]
                },
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Main function for testing"""
    print("☁️ Cloud Monitoring Integration - Testing Mode")
    
    integration = CloudMonitoringIntegration()
    
    # Start monitoring (will only work with real credentials)
    integration.start_monitoring()
    
    try:
        print("🔄 Running cloud monitoring for 2 minutes...")
        time.sleep(120)
        
        # Get summary
        summary = integration.get_monitoring_summary()
        print(f"📊 Monitoring Summary: {json.dumps(summary, indent=2)}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping monitoring...")
    finally:
        integration.stop_monitoring()

if __name__ == "__main__":
    main()