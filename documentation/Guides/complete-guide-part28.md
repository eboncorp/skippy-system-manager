# Complete Home Cloud Setup Guide - Part 28

## Part 10.23: Resource Monitoring System

### Resource Monitor
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
import numpy as np
from typing import Dict, List, Any, Optional
import psutil
import aiohttp
from enum import Enum
import os
import platform

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    IO = "io"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ResourceMonitor:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=21)
        self.load_config()
        self.setup_metrics()
        self.setup_alerts()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/resource_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load resource monitoring configuration"""
        self.config = {
            'monitoring': {
                'intervals': {
                    'basic': 10,     # 10 seconds
                    'detailed': 60,   # 1 minute
                    'extended': 300   # 5 minutes
                },
                'retention': {
                    'basic': 3600,    # 1 hour
                    'detailed': 86400,  # 1 day
                    'extended': 604800  # 1 week
                }
            },
            'thresholds': {
                'cpu': {
                    'warning': 70,
                    'error': 85,
                    'critical': 95
                },
                'memory': {
                    'warning': 75,
                    'error': 85,
                    'critical': 95
                },
                'disk': {
                    'warning': 80,
                    'error': 90,
                    'critical': 95
                },
                'io': {
                    'warning': 70,
                    'error': 85,
                    'critical': 95
                },
                'network': {
                    'warning': 70,
                    'error': 85,
                    'critical': 95
                }
            },
            'alerts': {
                'channels': {
                    'email': {
                        'enabled': True,
                        'recipients': ['admin@example.com'],
                        'min_severity': 'warning'
                    },
                    'slack': {
                        'enabled': True,
                        'webhook_url': 'https://hooks.slack.com/services/xxx',
                        'min_severity': 'error'
                    },
                    'webhook': {
                        'enabled': True,
                        'url': 'http://monitoring.local/webhook',
                        'min_severity': 'warning'
                    }
                },
                'throttling': {
                    'min_interval': 300,  # 5 minutes
                    'max_alerts_per_hour': 10,
                    'grouping_window': 60  # 1 minute
                },
                'escalation': {
                    'enabled': True,
                    'levels': [
                        {
                            'threshold': 15,  # minutes
                            'recipients': ['oncall@example.com']
                        },
                        {
                            'threshold': 30,
                            'recipients': ['manager@example.com']
                        },
                        {
                            'threshold': 60,
                            'recipients': ['director@example.com']
                        }
                    ]
                }
            },
            'analysis': {
                'anomaly_detection': {
                    'enabled': True,
                    'sensitivity': 2.0,
                    'min_data_points': 100,
                    'training_period': 86400  # 1 day
                },
                'trend_analysis': {
                    'enabled': True,
                    'window_size': 3600,  # 1 hour
                    'forecast_horizon': 3600  # 1 hour
                },
                'correlation': {
                    'enabled': True,
                    'min_correlation': 0.7,
                    'max_lag': 300  # 5 minutes
                }
            }
        }
        
    def setup_metrics(self):
        """Initialize metrics collection"""
        self.metrics = {
            'basic': defaultdict(list),
            'detailed': defaultdict(list),
            'extended': defaultdict(list)
        }
        
        self.metric_timestamps = {
            'basic': defaultdict(list),
            'detailed': defaultdict(list),
            'extended': defaultdict(list)
        }
        
    def setup_alerts(self):
        """Initialize alert system"""
        self.active_alerts = defaultdict(dict)
        self.alert_history = defaultdict(list)
        self.alert_counters = defaultdict(int)
        self.alert_throttles = defaultdict(lambda: datetime.now())
    
    async def collect_metrics(self):
        """Collect system metrics"""
        try:
            # Collect basic metrics
            basic_metrics = await self.collect_basic_metrics()
            await self.store_metrics('basic', basic_metrics)
            
            # Collect detailed metrics if interval elapsed
            if await self.should_collect_detailed():
                detailed_metrics = await self.collect_detailed_metrics()
                await self.store_metrics('detailed', detailed_metrics)
            
            # Collect extended metrics if interval elapsed
            if await self.should_collect_extended():
                extended_metrics = await self.collect_extended_metrics()
                await self.store_metrics('extended', extended_metrics)
            
            # Analyze metrics
            await self.analyze_metrics()
            
            # Check thresholds
            await self.check_thresholds()
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {str(e)}")
    
    async def collect_basic_metrics(self) -> Dict:
        """Collect basic system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'percent': psutil.disk_usage('/').percent
                },
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv,
                    'packets_sent': psutil.net_io_counters().packets_sent,
                    'packets_recv': psutil.net_io_counters().packets_recv
                }
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting basic metrics: {str(e)}")
            return {}
    
    async def collect_detailed_metrics(self) -> Dict:
        """Collect detailed system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                    'times': psutil.cpu_times()._asdict(),
                    'stats': psutil.cpu_stats()._asdict(),
                    'load_avg': psutil.getloadavg()
                },
                'memory': {
                    'swap': psutil.swap_memory()._asdict(),
                    'detailed': psutil.virtual_memory()._asdict()
                },
                'disk': {
                    'io_counters': psutil.disk_io_counters()._asdict(),
                    'partitions': [p._asdict() for p in psutil.disk_partitions()]
                },
                'network': {
                    'connections': len(psutil.net_connections()),
                    'interfaces': psutil.net_if_stats(),
                    'io_detailed': psutil.net_io_counters(pernic=True)
                },
                'system': {
                    'boot_time': psutil.boot_time(),
                    'users': len(psutil.users()),
                    'processes': len(psutil.pids())
                }
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting detailed metrics: {str(e)}")
            return {}
    
    async def collect_extended_metrics(self) -> Dict:
        """Collect extended system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'processes': await self.collect_process_metrics(),
                'files': await self.collect_file_metrics(),
                'services': await self.collect_service_metrics(),
                'hardware': await self.collect_hardware_metrics()
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting extended metrics: {str(e)}")
            return {}
    
    async def collect_process_metrics(self) -> Dict:
        """Collect process-related metrics"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 
                                           'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    pinfo['cpu_percent'] = proc.cpu_percent()
                    pinfo['memory_percent'] = proc.memory_percent()
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return {
                'top_cpu': processes[:10],
                'total_count': len(processes),
                'status_counts': defaultdict(int,
                    {p['status']: processes.count(p['status']) 
                     for p in processes}
                )
            }
            
        except Exception as e:
            logging.error(f"Error collecting process metrics: {str(e)}")
            return {}
    
    async def collect_file_metrics(self) -> Dict:
        """Collect file system metrics"""
        try:
            metrics = {
                'open_files': len(psutil.Process().open_files()),
                'disk_io': {
                    'read_count': psutil.disk_io_counters().read_count,
                    'write_count': psutil.disk_io_counters().write_count,
                    'read_bytes': psutil.disk_io_counters().read_bytes,
                    'write_bytes': psutil.disk_io_counters().write_bytes,
                    'read_time': psutil.disk_io_counters().read_time,
                    'write_time': psutil.disk_io_counters().write_time
                }
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting file metrics: {str(e)}")
            return {}
    
    async def collect_service_metrics(self) -> Dict:
        """Collect service status metrics"""
        try:
            services = []
            if platform.system() == 'Linux':
                import systemd.journal
                
                for unit in systemd.journal.Reader().query_unique('_SYSTEMD_UNIT'):
                    try:
                        service_name = unit.decode()
                        if service_name.endswith('.service'):
                            services.append({
                                'name': service_name,
                                'status': 'running' if os.system(f'systemctl is-active {service_name} >/dev/null') == 0 else 'stopped'
                            })
                    except Exception:
                        continue
            
            return {
                'services': services,
                'total_count': len(services),
                'running_count': sum(1 for s in services if s['status'] == 'running'),
                'stopped_count': sum(1 for s in services if s['status'] == 'stopped')
            }
            
        except Exception as e:
            logging.error(f"Error collecting service metrics: {str(e)}")
            return {}
    
    async def collect_hardware_metrics(self) -> Dict:
        """Collect hardware-related metrics"""
        try:
            metrics = {
                'temperatures': {},
                'fans': {},
                'power': {},
                'battery': None
            }
            
            # Temperatures
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    metrics['temperatures'] = {
                        name: [t._asdict() for t in temps[name]]
                        for name in temps
                    }
            
            # Fans
            if hasattr(psutil, 'sensors_fans'):
                fans = psutil.sensors_fans()
                if fans:
                    metrics['fans'] = {
                        name: [f._asdict() for f in fans[name]]
                        for name in fans
                    }
            
            # Battery
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    metrics['battery'] = battery._asdict()
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting hardware metrics: {str(e)}")
            return {}

    async def analyze_metrics(self):
        """Analyze collected metrics"""
        try:
            # Perform anomaly detection
            if self.config['analysis']['anomaly_detection']['enabled']:
                await self.detect_anomalies()
            
            # Perform trend analysis
            if self.config['analysis']['trend_analysis']['enabled']:
                await self.analyze_trends()
            
            # Perform correlation analysis
            if self.config['analysis']['correlation']['enabled']:
                await self.analyze_correlations()
            
        except Exception as e:
            logging.error(f"Error analyzing metrics: {str(e)}")

    async def start(self):
        """Start the resource monitor"""
        try:
            logging.info("Starting Resource Monitor")
            
            while True:
                # Collect metrics
                await self.collect_metrics()
                
                # Clean up old metrics
                await self.cleanup_old_metrics()
                
                # Sleep until next collection
                await asyncio.sleep(
                    self.config['monitoring']['intervals']['basic']
                )
                
        except Exception as e:
            logging.error(f"Error in resource monitor: {str(e)}")
            raise

# Run the resource monitor
if __name__ == "__main__":
    monitor = ResourceMonitor()
    asyncio.run(monitor.start())
```

I'll continue with the Alert Management and Analysis components next. Would you like me to proceed?