#!/usr/bin/env python3
"""
AI-Powered Predictive Maintenance Engine v2.0
Enhanced with modern Python features, better error handling, and monitoring
Analyzes system metrics and predicts maintenance needs using machine learning
"""

import os
import sys
import json
import sqlite3
import time
import logging
import statistics
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from contextlib import asynccontextmanager
import math
import collections
import functools
import uuid

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/ai-maintenance-v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ML imports with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available - using fallback statistical methods")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available - using basic data structures")

# System monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.error("psutil not available - system monitoring limited")

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertType(Enum):
    """Types of maintenance alerts"""
    THRESHOLD_VIOLATION = "threshold_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    TREND_PREDICTION = "trend_prediction"
    SYSTEM_HEALTH = "system_health"
    PREDICTIVE_FAILURE = "predictive_failure"

class MetricType(Enum):
    """System metric types"""
    CPU_PERCENT = "cpu_percent"
    MEMORY_PERCENT = "memory_percent"
    DISK_PERCENT = "disk_percent"
    DISK_IO_WAIT = "disk_io_wait"
    NETWORK_ERRORS = "network_errors"
    TEMPERATURE = "temperature"
    LOAD_AVERAGE = "load_average"
    UPTIME = "uptime"
    PROCESS_COUNT = "process_count"

@dataclass
class SystemMetric:
    """Enhanced system metric data point with metadata"""
    server_id: int
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # Data quality indicator (0-1)

    def __post_init__(self):
        """Validate metric data"""
        if not isinstance(self.metric_type, MetricType):
            if isinstance(self.metric_type, str):
                try:
                    self.metric_type = MetricType(self.metric_type)
                except ValueError:
                    logger.warning(f"Unknown metric type: {self.metric_type}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metric_type'] = self.metric_type.value if isinstance(self.metric_type, MetricType) else str(self.metric_type)
        return data

@dataclass
class MaintenanceAlert:
    """Enhanced maintenance alert with action tracking"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server_id: int = 0
    alert_type: AlertType = AlertType.SYSTEM_HEALTH
    severity: AlertSeverity = AlertSeverity.INFO
    component: str = ""
    prediction: str = ""
    confidence: float = 0.0
    recommended_action: str = ""
    time_to_failure: Optional[int] = None  # hours
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure enums are properly set"""
        if not isinstance(self.alert_type, AlertType):
            if isinstance(self.alert_type, str):
                try:
                    self.alert_type = AlertType(self.alert_type)
                except ValueError:
                    self.alert_type = AlertType.SYSTEM_HEALTH

        if not isinstance(self.severity, AlertSeverity):
            if isinstance(self.severity, str):
                try:
                    self.severity = AlertSeverity(self.severity)
                except ValueError:
                    self.severity = AlertSeverity.INFO

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data

@dataclass
class PredictionResult:
    """Result of a trend prediction analysis"""
    metric_type: MetricType
    current_value: float
    predicted_value: float
    confidence: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    time_horizon_hours: int
    anomalies_count: int = 0
    quality_score: float = 1.0

class DatabaseManager:
    """Enhanced database manager with connection pooling and error handling"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.init_database()

    @asynccontextmanager
    async def get_connection(self):
        """Async context manager for database connections"""
        conn = None
        try:
            loop = asyncio.get_event_loop()
            conn = await loop.run_in_executor(None, sqlite3.connect, str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                await loop.run_in_executor(None, conn.rollback)
            raise
        finally:
            if conn:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, conn.close)

    def init_database(self):
        """Initialize database with improved schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Enhanced metric history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metric_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    quality_score REAL DEFAULT 1.0
                )
            """)

            # Create index separately
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metric_history
                ON metric_history(server_id, metric_type, timestamp)
            """)

            # Enhanced predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    current_value REAL,
                    predicted_value REAL,
                    confidence REAL NOT NULL,
                    time_horizon_hours INTEGER,
                    slope REAL,
                    trend TEXT,
                    model_version TEXT DEFAULT '2.0',
                    features_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Enhanced alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    server_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    component TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    recommended_action TEXT,
                    time_to_failure INTEGER,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)

            # System health summary
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL,
                    health_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    active_alerts INTEGER DEFAULT 0,
                    last_maintenance TIMESTAMP,
                    next_maintenance TIMESTAMP,
                    metadata TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    async def store_metric(self, metric: SystemMetric) -> bool:
        """Store a system metric asynchronously"""
        try:
            async with self.get_connection() as conn:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._store_metric_sync, conn, metric)
                return True
        except Exception as e:
            logger.error(f"Failed to store metric: {e}")
            return False

    def _store_metric_sync(self, conn: sqlite3.Connection, metric: SystemMetric):
        """Synchronous metric storage"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metric_history
            (server_id, metric_type, value, unit, timestamp, metadata, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.server_id,
            metric.metric_type.value if isinstance(metric.metric_type, MetricType) else str(metric.metric_type),
            metric.value,
            metric.unit,
            metric.timestamp,
            json.dumps(metric.metadata),
            metric.quality_score
        ))
        conn.commit()

    async def get_metrics_history(self, server_id: int, metric_type: MetricType,
                                 hours: int = 168) -> List[SystemMetric]:
        """Get metric history for analysis"""
        try:
            async with self.get_connection() as conn:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, self._get_metrics_history_sync, conn, server_id, metric_type, hours
                )
        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return []

    def _get_metrics_history_sync(self, conn: sqlite3.Connection, server_id: int,
                                 metric_type: MetricType, hours: int) -> List[SystemMetric]:
        """Synchronous metrics history retrieval"""
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(hours=hours)

        cursor.execute("""
            SELECT server_id, metric_type, value, unit, timestamp, metadata, quality_score
            FROM metric_history
            WHERE server_id = ? AND metric_type = ? AND timestamp > ?
            ORDER BY timestamp
        """, (server_id, metric_type.value, cutoff_time))

        metrics = []
        for row in cursor.fetchall():
            try:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                metric = SystemMetric(
                    server_id=row['server_id'],
                    metric_type=MetricType(row['metric_type']),
                    value=row['value'],
                    unit=row['unit'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=metadata,
                    quality_score=row['quality_score']
                )
                metrics.append(metric)
            except Exception as e:
                logger.warning(f"Failed to parse metric row: {e}")

        return metrics

class AIMaintenanceEngine:
    """Enhanced AI-powered predictive maintenance engine"""

    def __init__(self, db_path: Optional[Path] = None, config: Optional[Dict] = None):
        self.db_path = db_path or Path.home() / ".unified-system-manager" / "ai-maintenance-v2.db"
        self.config = config or self._get_default_config()

        # Initialize components
        self.db_manager = DatabaseManager(self.db_path)
        self.setup_logging()

        # Analysis parameters
        self.analysis_window = self.config.get('analysis_window_hours', 168)
        self.prediction_horizon = self.config.get('prediction_horizon_hours', 72)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)

        # Thresholds
        self.thresholds = self.config.get('thresholds', {
            MetricType.CPU_PERCENT: {'warning': 80, 'critical': 95},
            MetricType.MEMORY_PERCENT: {'warning': 85, 'critical': 95},
            MetricType.DISK_PERCENT: {'warning': 80, 'critical': 90},
            MetricType.TEMPERATURE: {'warning': 70, 'critical': 80},
            MetricType.LOAD_AVERAGE: {'warning': 2.0, 'critical': 4.0}
        })

        # State management
        self.running = False
        self.analysis_tasks = set()
        self.last_analysis = {}

        logger.info("AI Maintenance Engine v2.0 initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'analysis_window_hours': 168,
            'prediction_horizon_hours': 72,
            'confidence_threshold': 0.7,
            'anomaly_threshold_factor': 2.0,
            'max_concurrent_analysis': 5,
            'enable_auto_remediation': False,
            'notification_channels': ['log'],
            'thresholds': {}
        }

    def setup_logging(self):
        """Setup enhanced logging"""
        log_level = self.config.get('log_level', 'INFO')
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)

        # Create AI engine specific logger
        self.logger = logging.getLogger(f"{__name__}.AIMaintenanceEngine")
        self.logger.setLevel(numeric_level)

    async def collect_system_metrics(self, server_id: int) -> Dict[MetricType, SystemMetric]:
        """Collect comprehensive system metrics asynchronously"""
        metrics = {}

        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available - limited metric collection")
            return metrics

        try:
            # CPU metrics
            cpu_percent = await self._get_cpu_metrics()
            if cpu_percent is not None:
                metrics[MetricType.CPU_PERCENT] = SystemMetric(
                    server_id=server_id,
                    metric_type=MetricType.CPU_PERCENT,
                    value=cpu_percent,
                    unit='percent',
                    metadata={'cpu_count': psutil.cpu_count()}
                )

            # Memory metrics
            memory_info = await self._get_memory_metrics()
            if memory_info:
                metrics[MetricType.MEMORY_PERCENT] = SystemMetric(
                    server_id=server_id,
                    metric_type=MetricType.MEMORY_PERCENT,
                    value=memory_info['percent'],
                    unit='percent',
                    metadata={'total_gb': memory_info['total_gb'], 'available_gb': memory_info['available_gb']}
                )

            # Disk metrics
            disk_info = await self._get_disk_metrics()
            if disk_info:
                metrics[MetricType.DISK_PERCENT] = SystemMetric(
                    server_id=server_id,
                    metric_type=MetricType.DISK_PERCENT,
                    value=disk_info['percent'],
                    unit='percent',
                    metadata={'total_gb': disk_info['total_gb'], 'free_gb': disk_info['free_gb']}
                )

            # System load
            load_avg = await self._get_load_average()
            if load_avg is not None:
                metrics[MetricType.LOAD_AVERAGE] = SystemMetric(
                    server_id=server_id,
                    metric_type=MetricType.LOAD_AVERAGE,
                    value=load_avg,
                    unit='load',
                    metadata={'cpu_count': psutil.cpu_count()}
                )

            # Temperature (if available)
            temp = await self._get_temperature()
            if temp is not None:
                metrics[MetricType.TEMPERATURE] = SystemMetric(
                    server_id=server_id,
                    metric_type=MetricType.TEMPERATURE,
                    value=temp,
                    unit='celsius'
                )

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

        return metrics

    async def _get_cpu_metrics(self) -> Optional[float]:
        """Get CPU usage percentage"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, psutil.cpu_percent, 1)
        except Exception as e:
            self.logger.warning(f"Failed to get CPU metrics: {e}")
            return None

    async def _get_memory_metrics(self) -> Optional[Dict[str, float]]:
        """Get memory usage information"""
        try:
            loop = asyncio.get_event_loop()
            memory = await loop.run_in_executor(None, psutil.virtual_memory)
            return {
                'percent': memory.percent,
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get memory metrics: {e}")
            return None

    async def _get_disk_metrics(self) -> Optional[Dict[str, float]]:
        """Get disk usage information"""
        try:
            loop = asyncio.get_event_loop()
            disk = await loop.run_in_executor(None, psutil.disk_usage, '/')
            return {
                'percent': (disk.used / disk.total) * 100,
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get disk metrics: {e}")
            return None

    async def _get_load_average(self) -> Optional[float]:
        """Get system load average"""
        try:
            if hasattr(os, 'getloadavg'):
                loop = asyncio.get_event_loop()
                load_avg = await loop.run_in_executor(None, os.getloadavg)
                return load_avg[0]  # 1-minute load average
        except Exception as e:
            self.logger.warning(f"Failed to get load average: {e}")
        return None

    async def _get_temperature(self) -> Optional[float]:
        """Get system temperature"""
        try:
            loop = asyncio.get_event_loop()
            temps = await loop.run_in_executor(None, psutil.sensors_temperatures)
            if temps:
                all_temps = [
                    temp.current for sensor_temps in temps.values()
                    for temp in sensor_temps if temp.current
                ]
                if all_temps:
                    return statistics.mean(all_temps)
        except Exception as e:
            self.logger.debug(f"Temperature not available: {e}")
        return None

    async def analyze_server(self, server_id: int) -> List[MaintenanceAlert]:
        """Perform comprehensive AI analysis on a server"""
        alerts = []

        try:
            # Collect current metrics
            current_metrics = await self.collect_system_metrics(server_id)

            # Store metrics
            for metric in current_metrics.values():
                await self.db_manager.store_metric(metric)

            # Analyze each metric type
            for metric_type in [MetricType.CPU_PERCENT, MetricType.MEMORY_PERCENT,
                              MetricType.DISK_PERCENT, MetricType.LOAD_AVERAGE]:
                try:
                    # Get historical data
                    history = await self.db_manager.get_metrics_history(
                        server_id, metric_type, self.analysis_window
                    )

                    if len(history) < 10:
                        continue

                    # Perform analysis
                    analysis_results = await self._analyze_metric(metric_type, history)

                    # Generate alerts
                    metric_alerts = await self._generate_alerts(
                        server_id, metric_type, analysis_results, current_metrics.get(metric_type)
                    )
                    alerts.extend(metric_alerts)

                except Exception as e:
                    self.logger.error(f"Error analyzing {metric_type.value} for server {server_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error analyzing server {server_id}: {e}")

        return alerts

    async def _analyze_metric(self, metric_type: MetricType,
                            history: List[SystemMetric]) -> Dict[str, Any]:
        """Analyze a specific metric"""
        values = [metric.value for metric in history]
        timestamps = [metric.timestamp for metric in history]

        # Statistical analysis
        mean_value = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            stdev = 0

        # Anomaly detection
        anomalies = self._detect_anomalies(values, timestamps)

        # Trend prediction
        prediction = self._predict_trend(values, timestamps)

        return {
            'mean': mean_value,
            'stdev': stdev,
            'anomalies': anomalies,
            'prediction': prediction,
            'data_quality': self._assess_data_quality(history)
        }

    def _detect_anomalies(self, values: List[float], timestamps: List[datetime],
                         threshold_factor: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        if len(values) < 10:
            return []

        mean = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            return []

        anomalies = []
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            if stdev > 0:
                z_score = abs(value - mean) / stdev
                if z_score > threshold_factor:
                    anomalies.append({
                        'timestamp': timestamp,
                        'value': value,
                        'z_score': z_score,
                        'deviation': value - mean
                    })

        return anomalies

    def _predict_trend(self, values: List[float], timestamps: List[datetime]) -> PredictionResult:
        """Predict future trend using linear regression"""
        if len(values) < 5:
            return PredictionResult(
                metric_type=MetricType.CPU_PERCENT,  # Will be overridden
                current_value=values[-1] if values else 0,
                predicted_value=values[-1] if values else 0,
                confidence=0,
                trend='insufficient_data',
                slope=0,
                time_horizon_hours=self.prediction_horizon
            )

        # Convert timestamps to hours since start
        start_time = timestamps[0]
        x_values = [(ts - start_time).total_seconds() / 3600 for ts in timestamps]

        # Simple linear regression
        n = len(values)
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)

        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
            intercept = sum_y / n
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

        # Predict future value
        future_x = x_values[-1] + self.prediction_horizon
        predicted_value = slope * future_x + intercept

        # Calculate confidence (correlation coefficient)
        mean_x = sum_x / n
        mean_y = sum_y / n

        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
        denom_x = sum((x - mean_x) ** 2 for x in x_values)
        denom_y = sum((y - mean_y) ** 2 for y in values)

        correlation = numerator / math.sqrt(denom_x * denom_y) if denom_x * denom_y > 0 else 0
        confidence = abs(correlation)

        # Determine trend
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        return PredictionResult(
            metric_type=MetricType.CPU_PERCENT,  # Will be overridden
            current_value=values[-1],
            predicted_value=predicted_value,
            confidence=confidence,
            trend=trend,
            slope=slope,
            time_horizon_hours=self.prediction_horizon
        )

    def _assess_data_quality(self, history: List[SystemMetric]) -> float:
        """Assess the quality of metric data"""
        if not history:
            return 0.0

        # Check for gaps in data
        timestamps = [metric.timestamp for metric in history]
        timestamps.sort()

        total_time = (timestamps[-1] - timestamps[0]).total_seconds()
        expected_points = total_time / 60  # Assuming 1-minute intervals
        actual_points = len(history)

        completeness = min(1.0, actual_points / expected_points) if expected_points > 0 else 1.0

        # Check quality scores
        avg_quality = statistics.mean([metric.quality_score for metric in history])

        return (completeness + avg_quality) / 2

    async def _generate_alerts(self, server_id: int, metric_type: MetricType,
                             analysis: Dict[str, Any], current_metric: Optional[SystemMetric]) -> List[MaintenanceAlert]:
        """Generate maintenance alerts based on analysis"""
        alerts = []

        if not current_metric:
            return alerts

        current_value = current_metric.value
        thresholds = self.thresholds.get(metric_type, {})

        # Threshold-based alerts
        if 'critical' in thresholds and current_value >= thresholds['critical']:
            alerts.append(MaintenanceAlert(
                server_id=server_id,
                alert_type=AlertType.THRESHOLD_VIOLATION,
                severity=AlertSeverity.CRITICAL,
                component=metric_type.value,
                prediction=f"{metric_type.value} is critically high: {current_value:.1f}",
                confidence=0.95,
                recommended_action=self._get_recommended_action(metric_type, AlertSeverity.CRITICAL),
                metadata={'threshold': thresholds['critical'], 'current_value': current_value}
            ))
        elif 'warning' in thresholds and current_value >= thresholds['warning']:
            alerts.append(MaintenanceAlert(
                server_id=server_id,
                alert_type=AlertType.THRESHOLD_VIOLATION,
                severity=AlertSeverity.WARNING,
                component=metric_type.value,
                prediction=f"{metric_type.value} is elevated: {current_value:.1f}",
                confidence=0.85,
                recommended_action=self._get_recommended_action(metric_type, AlertSeverity.WARNING),
                metadata={'threshold': thresholds['warning'], 'current_value': current_value}
            ))

        # Anomaly-based alerts
        anomalies = analysis.get('anomalies', [])
        recent_anomalies = [
            a for a in anomalies
            if (datetime.now() - a['timestamp']).total_seconds() < 3600
        ]

        if recent_anomalies:
            avg_z_score = statistics.mean([a['z_score'] for a in recent_anomalies])
            severity = AlertSeverity.CRITICAL if avg_z_score > 3 else AlertSeverity.WARNING

            alerts.append(MaintenanceAlert(
                server_id=server_id,
                alert_type=AlertType.ANOMALY_DETECTED,
                severity=severity,
                component=metric_type.value,
                prediction=f"Unusual {metric_type.value} pattern detected (Z-score: {avg_z_score:.1f})",
                confidence=min(0.9, avg_z_score / 3),
                recommended_action="Investigate recent system changes and resource usage",
                metadata={'z_score': avg_z_score, 'anomaly_count': len(recent_anomalies)}
            ))

        # Predictive alerts
        prediction = analysis.get('prediction')
        if prediction and prediction.confidence > self.confidence_threshold:
            if prediction.trend == 'increasing' and 'critical' in thresholds:
                time_to_critical = self._estimate_time_to_threshold(
                    prediction, thresholds['critical']
                )
                if time_to_critical and time_to_critical < 24:  # Within 24 hours
                    alerts.append(MaintenanceAlert(
                        server_id=server_id,
                        alert_type=AlertType.PREDICTIVE_FAILURE,
                        severity=AlertSeverity.WARNING,
                        component=metric_type.value,
                        prediction=f"{metric_type.value} predicted to reach critical level in {time_to_critical:.1f} hours",
                        confidence=prediction.confidence,
                        recommended_action=self._get_recommended_action(metric_type, AlertSeverity.CRITICAL),
                        time_to_failure=int(time_to_critical),
                        metadata={'predicted_value': prediction.predicted_value, 'slope': prediction.slope}
                    ))

        return alerts

    def _estimate_time_to_threshold(self, prediction: PredictionResult, threshold: float) -> Optional[float]:
        """Estimate time until threshold is reached"""
        if prediction.slope <= 0:
            return None

        hours_to_threshold = (threshold - prediction.current_value) / prediction.slope
        return max(0, hours_to_threshold) if hours_to_threshold > 0 else None

    def _get_recommended_action(self, metric_type: MetricType, severity: AlertSeverity) -> str:
        """Get recommended action for alert"""
        actions = {
            MetricType.CPU_PERCENT: {
                AlertSeverity.WARNING: "Monitor processes, consider load balancing",
                AlertSeverity.CRITICAL: "Investigate high CPU processes, scale resources"
            },
            MetricType.MEMORY_PERCENT: {
                AlertSeverity.WARNING: "Monitor memory usage, restart memory-intensive services",
                AlertSeverity.CRITICAL: "Free memory immediately, restart services if needed"
            },
            MetricType.DISK_PERCENT: {
                AlertSeverity.WARNING: "Clean up old files, monitor disk usage",
                AlertSeverity.CRITICAL: "Free disk space immediately, move large files"
            },
            MetricType.TEMPERATURE: {
                AlertSeverity.WARNING: "Check cooling system, monitor temperature",
                AlertSeverity.CRITICAL: "Reduce load, check hardware cooling immediately"
            }
        }

        return actions.get(metric_type, {}).get(severity, "Monitor system and investigate")

    async def start_monitoring(self, server_ids: List[int], interval_seconds: int = 300):
        """Start continuous monitoring of servers"""
        self.running = True
        self.logger.info(f"Starting monitoring for servers: {server_ids}")

        async def monitor_server(server_id: int):
            while self.running:
                try:
                    alerts = await self.analyze_server(server_id)
                    if alerts:
                        await self._process_alerts(alerts)
                except Exception as e:
                    self.logger.error(f"Error monitoring server {server_id}: {e}")

                await asyncio.sleep(interval_seconds)

        # Start monitoring tasks for each server
        for server_id in server_ids:
            task = asyncio.create_task(monitor_server(server_id))
            self.analysis_tasks.add(task)

        try:
            await asyncio.gather(*self.analysis_tasks)
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.running = False

    async def _process_alerts(self, alerts: List[MaintenanceAlert]):
        """Process and store generated alerts"""
        for alert in alerts:
            try:
                # Store alert in database
                await self._store_alert(alert)

                # Send notifications
                await self._send_notification(alert)

                self.logger.info(f"Generated {alert.severity.value} alert: {alert.prediction}")
            except Exception as e:
                self.logger.error(f"Error processing alert: {e}")

    async def _store_alert(self, alert: MaintenanceAlert):
        """Store alert in database"""
        try:
            async with self.db_manager.get_connection() as conn:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._store_alert_sync, conn, alert)
        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")

    def _store_alert_sync(self, conn: sqlite3.Connection, alert: MaintenanceAlert):
        """Synchronously store alert"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_alerts
            (alert_id, server_id, alert_type, severity, component, prediction,
             confidence, recommended_action, time_to_failure, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.alert_id,
            alert.server_id,
            alert.alert_type.value,
            alert.severity.value,
            alert.component,
            alert.prediction,
            alert.confidence,
            alert.recommended_action,
            alert.time_to_failure,
            json.dumps(alert.metadata)
        ))
        conn.commit()

    async def _send_notification(self, alert: MaintenanceAlert):
        """Send alert notification"""
        channels = self.config.get('notification_channels', ['log'])

        for channel in channels:
            if channel == 'log':
                level = logging.CRITICAL if alert.severity == AlertSeverity.CRITICAL else logging.WARNING
                self.logger.log(level, f"ALERT: {alert.prediction} - {alert.recommended_action}")
            # Add other notification channels (email, slack, etc.) here

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        for task in self.analysis_tasks:
            task.cancel()
        self.analysis_tasks.clear()
        self.logger.info("Monitoring stopped")


async def main():
    """Main demonstration function"""
    print("🤖 AI Maintenance Engine v2.0 - Enhanced Demo")
    print("="*50)

    # Initialize engine
    engine = AIMaintenanceEngine()

    try:
        # Analyze current server
        print("\n📊 Analyzing local server...")
        alerts = await engine.analyze_server(server_id=1)

        print(f"\n🚨 Generated {len(alerts)} alerts:")
        for alert in alerts:
            icon = "🔴" if alert.severity == AlertSeverity.CRITICAL else "🟡"
            print(f"{icon} {alert.severity.value.upper()}: {alert.prediction}")
            print(f"   📋 Action: {alert.recommended_action}")
            print(f"   🎯 Confidence: {alert.confidence:.2f}")
            if alert.time_to_failure:
                print(f"   ⏰ Time to failure: {alert.time_to_failure} hours")
            print()

        if not alerts:
            print("✅ No alerts generated - system appears healthy")

        print("\n💾 Results stored in database")
        print(f"📍 Database location: {engine.db_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())