# Complete Home Cloud Setup Guide - Part 21

## Part 10.16: Cache Monitoring and Analytics System

### Cache Analytics Manager
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
import pandas as pd
from sklearn.ensemble import IsolationForest
import aiofiles
import os

class MetricType:
    PERFORMANCE = "performance"
    USAGE = "usage"
    HEALTH = "health"
    ERROR = "error"

class CacheAnalyticsManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=14)
        self.load_config()
        self.setup_metrics()
        self.anomaly_detector = IsolationForest(contamination=0.1)
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/cache_analytics.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load analytics configuration"""
        self.config = {
            'monitoring': {
                'metrics_interval': 60,    # 1 minute
                'health_check_interval': 300,  # 5 minutes
                'cleanup_interval': 3600,   # 1 hour
                'retention_period': 604800  # 7 days
            },
            'thresholds': {
                'performance': {
                    'latency_ms': {
                        'warning': 100,
                        'critical': 500
                    },
                    'hit_ratio': {
                        'warning': 0.7,
                        'critical': 0.5
                    },
                    'memory_usage': {
                        'warning': 0.8,
                        'critical': 0.9
                    }
                },
                'health': {
                    'error_rate': {
                        'warning': 0.05,
                        'critical': 0.1
                    },
                    'stale_entries': {
                        'warning': 100,
                        'critical': 1000
                    },
                    'consistency_errors': {
                        'warning': 10,
                        'critical': 50
                    }
                }
            },
            'anomaly_detection': {
                'sensitivity': 0.1,
                'training_window': 86400,  # 1 day
                'min_samples': 1000,
                'features': [
                    'latency_ms',
                    'hit_ratio',
                    'memory_usage',
                    'error_rate'
                ]
            },
            'alerts': {
                'channels': {
                    'email': {
                        'enabled': True,
                        'recipients': ['admin@example.com']
                    },
                    'slack': {
                        'enabled': True,
                        'webhook_url': 'https://hooks.slack.com/services/xxx'
                    }
                },
                'throttling': {
                    'min_interval': 300,  # 5 minutes
                    'max_alerts_per_hour': 10
                }
            }
        }
    
    def setup_metrics(self):
        """Initialize metrics collection"""
        self.metrics = {
            MetricType.PERFORMANCE: defaultdict(list),
            MetricType.USAGE: defaultdict(list),
            MetricType.HEALTH: defaultdict(list),
            MetricType.ERROR: defaultdict(list)
        }
        
        self.metric_aggregates = defaultdict(lambda: {
            'current': 0,
            'min': float('inf'),
            'max': float('-inf'),
            'avg': 0,
            'count': 0
        })
    
    async def collect_metrics(self):
        """Collect cache metrics"""
        try:
            # Collect performance metrics
            perf_metrics = await self.collect_performance_metrics()
            self.store_metrics(MetricType.PERFORMANCE, perf_metrics)
            
            # Collect usage metrics
            usage_metrics = await self.collect_usage_metrics()
            self.store_metrics(MetricType.USAGE, usage_metrics)
            
            # Collect health metrics
            health_metrics = await self.collect_health_metrics()
            self.store_metrics(MetricType.HEALTH, health_metrics)
            
            # Analyze for anomalies
            await self.detect_anomalies()
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {str(e)}")
    
    async def collect_performance_metrics(self) -> Dict:
        """Collect performance-related metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'latency_ms': await self.measure_latency(),
                'hit_ratio': await self.calculate_hit_ratio(),
                'memory_usage': psutil.Process().memory_percent(),
                'cpu_usage': psutil.Process().cpu_percent(),
                'io_ops': await self.measure_io_operations()
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting performance metrics: {str(e)}")
            return {}
    
    async def measure_latency(self) -> float:
        """Measure cache operation latency"""
        try:
            start_time = datetime.now()
            
            # Perform sample operations
            for _ in range(10):
                await self.perform_sample_operation()
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return duration / 10  # Average latency
            
        except Exception as e:
            logging.error(f"Error measuring latency: {str(e)}")
            return 0.0
    
    async def perform_sample_operation(self):
        """Perform a sample cache operation"""
        try:
            test_key = f"test_key_{datetime.now().timestamp()}"
            test_value = "test_value"
            
            # Test write
            await self.write_to_cache(test_key, test_value)
            
            # Test read
            await self.read_from_cache(test_key)
            
            # Cleanup
            await self.remove_from_cache(test_key)
            
        except Exception as e:
            logging.error(f"Error in sample operation: {str(e)}")
    
    async def calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        try:
            stats = await self.get_cache_stats()
            total_requests = stats['hits'] + stats['misses']
            
            if total_requests == 0:
                return 1.0
            
            return stats['hits'] / total_requests
            
        except Exception as e:
            logging.error(f"Error calculating hit ratio: {str(e)}")
            return 1.0
    
    async def measure_io_operations(self) -> Dict:
        """Measure I/O operations"""
        try:
            disk_io = psutil.disk_io_counters()
            return {
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes
            }
            
        except Exception as e:
            logging.error(f"Error measuring IO operations: {str(e)}")
            return {}
    
    async def collect_usage_metrics(self) -> Dict:
        """Collect cache usage metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'total_entries': await self.count_cache_entries(),
                'size_bytes': await self.calculate_cache_size(),
                'access_patterns': await self.analyze_access_patterns(),
                'entry_age_distribution': await self.analyze_entry_ages()
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting usage metrics: {str(e)}")
            return {}
    
    async def collect_health_metrics(self) -> Dict:
        """Collect cache health metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'error_rate': await self.calculate_error_rate(),
                'stale_entries': await self.count_stale_entries(),
                'consistency_status': await self.check_consistency(),
                'resource_usage': await self.check_resource_usage()
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting health metrics: {str(e)}")
            return {}
    
    def store_metrics(self, metric_type: str, metrics: Dict):
        """Store collected metrics"""
        try:
            # Store in memory
            self.metrics[metric_type].append(metrics)
            
            # Store in Redis
            self.redis.lpush(
                f"cache_metrics:{metric_type}",
                json.dumps(metrics)
            )
            
            # Update aggregates
            self.update_metric_aggregates(metric_type, metrics)
            
            # Cleanup old metrics
            self.cleanup_old_metrics(metric_type)
            
        except Exception as e:
            logging.error(f"Error storing metrics: {str(e)}")
    
    def update_metric_aggregates(self, metric_type: str, metrics: Dict):
        """Update metric aggregates"""
        try:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    agg = self.metric_aggregates[f"{metric_type}_{key}"]
                    agg['current'] = value
                    agg['min'] = min(agg['min'], value)
                    agg['max'] = max(agg['max'], value)
                    agg['count'] += 1
                    agg['avg'] = (agg['avg'] * (agg['count'] - 1) + value) / agg['count']
                    
        except Exception as e:
            logging.error(f"Error updating metric aggregates: {str(e)}")
    
    async def detect_anomalies(self):
        """Detect anomalies in metrics"""
        try:
            # Prepare feature matrix
            features = self.config['anomaly_detection']['features']
            data = []
            
            for metric_type in self.metrics:
                for metric in self.metrics[metric_type]:
                    row = [metric.get(feature, 0) for feature in features]
                    data.append(row)
            
            if len(data) < self.config['anomaly_detection']['min_samples']:
                return
            
            # Convert to numpy array
            X = np.array(data)
            
            # Fit and predict
            self.anomaly_detector.fit(X)
            predictions = self.anomaly_detector.predict(X)
            
            # Process anomalies
            anomalies = []
            for i, pred in enumerate(predictions):
                if pred == -1:  # Anomaly detected
                    anomalies.append(data[i])
            
            if anomalies:
                await self.handle_anomalies(anomalies)
            
        except Exception as e:
            logging.error(f"Error detecting anomalies: {str(e)}")
    
    async def handle_anomalies(self, anomalies: List):
        """Handle detected anomalies"""
        try:
            for anomaly in anomalies:
                # Create anomaly record
                record = {
                    'timestamp': datetime.now().isoformat(),
                    'features': dict(zip(
                        self.config['anomaly_detection']['features'],
                        anomaly
                    )),
                    'severity': self.calculate_anomaly_severity(anomaly)
                }
                
                # Store anomaly
                self.redis.lpush('cache_anomalies', json.dumps(record))
                
                # Send alert if needed
                if record['severity'] >= 0.7:  # High severity
                    await self.send_alert(record)
                
        except Exception as e:
            logging.error(f"Error handling anomalies: {str(e)}")
    
    def calculate_anomaly_severity(self, anomaly: List) -> float:
        """Calculate anomaly severity score"""
        try:
            # Calculate distance from normal ranges
            severity_scores = []
            for i, feature in enumerate(self.config['anomaly_detection']['features']):
                value = anomaly[i]
                agg = self.metric_aggregates.get(feature, {})
                if agg:
                    # Calculate z-score
                    mean = agg['avg']
                    std = np.sqrt(
                        ((agg['max'] - agg['min']) ** 2) / 12
                    )  # Approximate std dev
                    if std > 0:
                        z_score = abs(value - mean) / std
                        severity_scores.append(min(1.0, z_score / 3))  # Cap at 1.0
            
            return np.mean(severity_scores) if severity_scores else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating anomaly severity: {str(e)}")
            return 0.0

    async def start(self):
        """Start the analytics manager"""
        try:
            logging.info("Starting Cache Analytics Manager")
            
            while True:
                await self.collect_metrics()
                await asyncio.sleep(self.config['monitoring']['metrics_interval'])
                
        except Exception as e:
            logging.error(f"Error in analytics manager: {str(e)}")
            raise

# Run the analytics manager
if __name__ == "__main__":
    manager = CacheAnalyticsManager()
    asyncio.run(manager.start())
```

I'll continue with the Cache Performance Optimization system next. Would you like me to proceed?