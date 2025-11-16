#!/usr/bin/env python3
"""
Skippy System Manager - Advanced Resilience Features
Version: 1.1.0
Author: Skippy Development Team
Created: 2025-11-16

Advanced resilience features including:
- Metrics persistence
- Request tracing
- Graceful degradation with caching
- Alert notifications
- Bulkhead pattern
"""

import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from collections import deque
import logging
import os

logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST TRACING
# =============================================================================

@dataclass
class RequestTrace:
    """Trace information for a single request."""
    request_id: str
    service: str
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = False
    attempt_count: int = 1
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "service": self.service,
            "operation": self.operation,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "attempt_count": self.attempt_count,
            "error": self.error,
            "metadata": self.metadata
        }


class RequestTracer:
    """
    Request tracing for debugging and monitoring.

    Tracks requests through retries and provides correlation IDs.

    Example:
        tracer = RequestTracer()
        with tracer.trace("google-drive", "search") as trace:
            result = api.search(query)
            trace.metadata["results"] = len(result)
    """

    def __init__(self, max_traces: int = 1000):
        """
        Initialize request tracer.

        Args:
            max_traces: Maximum number of traces to keep in memory
        """
        self.max_traces = max_traces
        self.traces: deque = deque(maxlen=max_traces)
        self._lock = threading.Lock()
        self._current_trace: Optional[RequestTrace] = None

    def start_trace(self, service: str, operation: str) -> RequestTrace:
        """Start a new request trace."""
        trace = RequestTrace(
            request_id=str(uuid.uuid4())[:8],
            service=service,
            operation=operation,
            start_time=datetime.now()
        )
        with self._lock:
            self._current_trace = trace
        return trace

    def end_trace(self, trace: RequestTrace, success: bool = True, error: Optional[str] = None):
        """End a request trace."""
        trace.end_time = datetime.now()
        trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        trace.success = success
        trace.error = error

        with self._lock:
            self.traces.append(trace)
            self._current_trace = None

        logger.debug(
            f"Request {trace.request_id} completed: {trace.service}/{trace.operation} "
            f"in {trace.duration_ms:.2f}ms (success={success})"
        )

    class TraceContext:
        """Context manager for request tracing."""
        def __init__(self, tracer: 'RequestTracer', service: str, operation: str):
            self.tracer = tracer
            self.trace = tracer.start_trace(service, operation)

        def __enter__(self):
            return self.trace

        def __exit__(self, exc_type, exc_val, exc_tb):
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            self.tracer.end_trace(self.trace, success, error)
            return False

    def trace(self, service: str, operation: str) -> TraceContext:
        """Context manager for tracing a request."""
        return self.TraceContext(self, service, operation)

    def get_recent_traces(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get most recent traces."""
        with self._lock:
            traces = list(self.traces)[-count:]
        return [t.to_dict() for t in traces]

    def get_traces_by_service(self, service: str) -> List[Dict[str, Any]]:
        """Get traces for a specific service."""
        with self._lock:
            traces = [t for t in self.traces if t.service == service]
        return [t.to_dict() for t in traces]

    def get_failed_traces(self) -> List[Dict[str, Any]]:
        """Get all failed traces."""
        with self._lock:
            traces = [t for t in self.traces if not t.success]
        return [t.to_dict() for t in traces]

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        with self._lock:
            traces = list(self.traces)

        if not traces:
            return {"total": 0, "success_rate": 0, "avg_duration_ms": 0}

        successful = sum(1 for t in traces if t.success)
        durations = [t.duration_ms for t in traces if t.duration_ms is not None]

        return {
            "total": len(traces),
            "successful": successful,
            "failed": len(traces) - successful,
            "success_rate": (successful / len(traces)) * 100 if traces else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0
        }


# =============================================================================
# METRICS PERSISTENCE
# =============================================================================

class MetricsPersistence:
    """
    Persist metrics to disk for analysis and recovery.

    Example:
        persistence = MetricsPersistence("/path/to/metrics")
        persistence.save_circuit_breaker_state("google-drive", cb.get_state())
        persistence.save_request_trace(trace)

        # On restart
        states = persistence.load_circuit_breaker_states()
    """

    def __init__(self, metrics_dir: Optional[str] = None):
        """
        Initialize metrics persistence.

        Args:
            metrics_dir: Directory to store metrics files
        """
        if metrics_dir:
            self.metrics_dir = Path(metrics_dir)
        else:
            base_path = os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")
            self.metrics_dir = Path(base_path) / "logs" / "metrics"

        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save_circuit_breaker_state(self, name: str, state: Dict[str, Any]):
        """Save circuit breaker state to disk."""
        try:
            cb_file = self.metrics_dir / "circuit_breakers.json"

            with self._lock:
                # Load existing states
                if cb_file.exists():
                    with open(cb_file, 'r') as f:
                        all_states = json.load(f)
                else:
                    all_states = {}

                # Update state
                all_states[name] = {
                    **state,
                    "last_updated": datetime.now().isoformat()
                }

                # Save
                with open(cb_file, 'w') as f:
                    json.dump(all_states, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save circuit breaker state: {e}")

    def load_circuit_breaker_states(self) -> Dict[str, Any]:
        """Load all circuit breaker states from disk."""
        try:
            cb_file = self.metrics_dir / "circuit_breakers.json"

            if cb_file.exists():
                with open(cb_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load circuit breaker states: {e}")
            return {}

    def save_request_traces(self, traces: List[Dict[str, Any]]):
        """Save request traces to disk."""
        try:
            traces_file = self.metrics_dir / f"traces_{datetime.now().strftime('%Y%m%d')}.jsonl"

            with self._lock:
                with open(traces_file, 'a') as f:
                    for trace in traces:
                        f.write(json.dumps(trace) + '\n')

        except Exception as e:
            logger.error(f"Failed to save request traces: {e}")

    def save_health_snapshot(self, health_data: Dict[str, Any]):
        """Save health check snapshot."""
        try:
            snapshot_file = self.metrics_dir / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(snapshot_file, 'w') as f:
                json.dump(health_data, f, indent=2)

            # Clean old snapshots (keep last 24 hours)
            self._cleanup_old_files("health_*.json", hours=24)

        except Exception as e:
            logger.error(f"Failed to save health snapshot: {e}")

    def save_alert(self, alert: Dict[str, Any]):
        """Save alert to disk for notification."""
        try:
            alerts_file = self.metrics_dir / "alerts.jsonl"

            with self._lock:
                with open(alerts_file, 'a') as f:
                    alert["timestamp"] = datetime.now().isoformat()
                    f.write(json.dumps(alert) + '\n')

        except Exception as e:
            logger.error(f"Failed to save alert: {e}")

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours."""
        try:
            alerts_file = self.metrics_dir / "alerts.jsonl"

            if not alerts_file.exists():
                return []

            cutoff = datetime.now() - timedelta(hours=hours)
            recent_alerts = []

            with open(alerts_file, 'r') as f:
                for line in f:
                    if line.strip():
                        alert = json.loads(line)
                        alert_time = datetime.fromisoformat(alert["timestamp"])
                        if alert_time > cutoff:
                            recent_alerts.append(alert)

            return recent_alerts

        except Exception as e:
            logger.error(f"Failed to load alerts: {e}")
            return []

    def _cleanup_old_files(self, pattern: str, hours: int):
        """Clean up old metrics files."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)

            for file in self.metrics_dir.glob(pattern):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()

        except Exception as e:
            logger.warning(f"Failed to cleanup old files: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of persisted metrics."""
        try:
            summary = {
                "metrics_dir": str(self.metrics_dir),
                "files": {},
                "total_size_mb": 0
            }

            for file in self.metrics_dir.iterdir():
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    summary["files"][file.name] = {
                        "size_mb": round(size_mb, 2),
                        "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    }
                    summary["total_size_mb"] += size_mb

            summary["total_size_mb"] = round(summary["total_size_mb"], 2)
            return summary

        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e)}


# =============================================================================
# GRACEFUL DEGRADATION WITH CACHING
# =============================================================================

@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    key: str
    value: Any
    timestamp: datetime
    ttl_seconds: int
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl_seconds


class GracefulCache:
    """
    Cache for graceful degradation when services are unavailable.

    Stores successful API responses and serves them when circuit breaker is open.

    Example:
        cache = GracefulCache()

        # On successful call
        result = api.search(query)
        cache.set(f"search:{query}", result, ttl=3600)

        # When circuit breaker is open
        if circuit_breaker_open:
            cached = cache.get(f"search:{query}")
            if cached:
                return cached  # Stale but better than nothing
    """

    def __init__(self, max_entries: int = 1000, default_ttl: int = 3600):
        """
        Initialize graceful cache.

        Args:
            max_entries: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
        """
        ttl = ttl or self.default_ttl

        with self._lock:
            # Evict oldest entries if at capacity
            if len(self.cache) >= self.max_entries and key not in self.cache:
                self._evict_oldest()

            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl_seconds=ttl
            )

    def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key
            allow_stale: If True, return expired entries (for degradation)

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]

            if entry.is_expired() and not allow_stale:
                del self.cache[key]
                return None

            entry.hit_count += 1
            return entry.value

    def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value with metadata (age, hit count, etc.)."""
        with self._lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]
            age_seconds = (datetime.now() - entry.timestamp).total_seconds()

            return {
                "value": entry.value,
                "age_seconds": age_seconds,
                "hit_count": entry.hit_count,
                "is_stale": entry.is_expired(),
                "ttl_remaining": max(0, entry.ttl_seconds - age_seconds)
            }

    def invalidate(self, key: str):
        """Remove a specific entry from cache."""
        with self._lock:
            self.cache.pop(key, None)

    def invalidate_pattern(self, pattern: str):
        """Remove all entries matching pattern."""
        with self._lock:
            keys_to_remove = [k for k in self.cache if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()

    def _evict_oldest(self):
        """Evict the oldest cache entry."""
        if not self.cache:
            return

        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_key]

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = len(self.cache)
            stale = sum(1 for e in self.cache.values() if e.is_expired())
            total_hits = sum(e.hit_count for e in self.cache.values())

            return {
                "total_entries": total,
                "stale_entries": stale,
                "valid_entries": total - stale,
                "total_hits": total_hits,
                "capacity_percent": (total / self.max_entries) * 100 if self.max_entries else 0
            }

    def cleanup_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)


# =============================================================================
# ALERT SYSTEM
# =============================================================================

class AlertLevel:
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert notification."""
    level: str
    title: str
    message: str
    service: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "service": self.service,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class AlertManager:
    """
    Manages alert notifications for resilience events.

    Example:
        alert_mgr = AlertManager()

        # Register handlers
        alert_mgr.add_handler("log", log_alert_handler)
        alert_mgr.add_handler("file", file_alert_handler)

        # Send alert
        alert_mgr.alert(
            AlertLevel.CRITICAL,
            "Circuit Breaker Open",
            "Google Drive API circuit breaker opened after 5 failures"
        )
    """

    def __init__(self):
        """Initialize alert manager."""
        self.handlers: Dict[str, Callable[[Alert], None]] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

        # Register default handlers
        self.add_handler("log", self._log_handler)

    def add_handler(self, name: str, handler: Callable[[Alert], None]):
        """Add an alert handler."""
        self.handlers[name] = handler

    def remove_handler(self, name: str):
        """Remove an alert handler."""
        self.handlers.pop(name, None)

    def alert(
        self,
        level: str,
        title: str,
        message: str,
        service: Optional[str] = None,
        **metadata
    ):
        """
        Send an alert through all registered handlers.

        Args:
            level: Alert severity (INFO, WARNING, ERROR, CRITICAL)
            title: Alert title
            message: Alert message
            service: Related service name (optional)
            **metadata: Additional metadata
        """
        alert = Alert(
            level=level,
            title=title,
            message=message,
            service=service,
            metadata=metadata
        )

        with self._lock:
            self.alert_history.append(alert)

        # Send to all handlers
        for name, handler in self.handlers.items():
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler '{name}' failed: {e}")

    def _log_handler(self, alert: Alert):
        """Default handler that logs alerts."""
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(alert.level, logger.info)

        log_func(f"ALERT [{alert.level.upper()}] {alert.title}: {alert.message}")

    def get_recent_alerts(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        with self._lock:
            alerts = list(self.alert_history)[-count:]
        return [a.to_dict() for a in alerts]

    def get_alerts_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get alerts of a specific level."""
        with self._lock:
            alerts = [a for a in self.alert_history if a.level == level]
        return [a.to_dict() for a in alerts]


# =============================================================================
# FILE-BASED ALERT HANDLER
# =============================================================================

def create_file_alert_handler(filepath: str) -> Callable[[Alert], None]:
    """
    Create an alert handler that writes to a file.

    Args:
        filepath: Path to alert log file

    Returns:
        Alert handler function
    """
    file_lock = threading.Lock()

    def handler(alert: Alert):
        with file_lock:
            with open(filepath, 'a') as f:
                f.write(json.dumps(alert.to_dict()) + '\n')

    return handler


def create_slack_webhook_handler(webhook_url: str) -> Callable[[Alert], None]:
    """
    Create an alert handler that sends to Slack webhook.

    Args:
        webhook_url: Slack incoming webhook URL

    Returns:
        Alert handler function
    """
    import httpx

    def handler(alert: Alert):
        try:
            emoji = {
                AlertLevel.INFO: ":information_source:",
                AlertLevel.WARNING: ":warning:",
                AlertLevel.ERROR: ":x:",
                AlertLevel.CRITICAL: ":rotating_light:"
            }.get(alert.level, ":bell:")

            payload = {
                "text": f"{emoji} *{alert.title}*\n{alert.message}",
                "attachments": [
                    {
                        "color": {
                            AlertLevel.INFO: "#36a64f",
                            AlertLevel.WARNING: "#ffcc00",
                            AlertLevel.ERROR: "#ff0000",
                            AlertLevel.CRITICAL: "#990000"
                        }.get(alert.level, "#cccccc"),
                        "fields": [
                            {"title": "Level", "value": alert.level, "short": True},
                            {"title": "Service", "value": alert.service or "N/A", "short": True},
                            {"title": "Time", "value": alert.timestamp.isoformat(), "short": False}
                        ]
                    }
                ]
            }

            httpx.post(webhook_url, json=payload, timeout=10)

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    return handler


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Global request tracer
_global_tracer = RequestTracer()

# Global metrics persistence
_global_persistence: Optional[MetricsPersistence] = None

# Global cache for graceful degradation
_global_cache = GracefulCache()

# Global alert manager
_global_alerts = AlertManager()


def get_tracer() -> RequestTracer:
    """Get global request tracer."""
    return _global_tracer


def get_cache() -> GracefulCache:
    """Get global graceful cache."""
    return _global_cache


def get_alert_manager() -> AlertManager:
    """Get global alert manager."""
    return _global_alerts


def init_metrics_persistence(metrics_dir: Optional[str] = None) -> MetricsPersistence:
    """Initialize global metrics persistence."""
    global _global_persistence
    _global_persistence = MetricsPersistence(metrics_dir)
    return _global_persistence


def get_metrics_persistence() -> Optional[MetricsPersistence]:
    """Get global metrics persistence (may be None if not initialized)."""
    return _global_persistence


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("Advanced Resilience Features - Examples")
    print("=" * 60)

    # Example 1: Request Tracing
    print("\n1. Request Tracing:")
    tracer = RequestTracer()

    with tracer.trace("google-drive", "search") as trace:
        time.sleep(0.05)
        trace.metadata["results"] = 42

    with tracer.trace("github", "create-pr") as trace:
        time.sleep(0.03)
        trace.metadata["pr_number"] = 123

    stats = tracer.get_statistics()
    print(f"   Total traces: {stats['total']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Avg duration: {stats['avg_duration_ms']:.2f}ms")

    # Example 2: Graceful Cache
    print("\n2. Graceful Cache:")
    cache = GracefulCache(default_ttl=2)

    cache.set("search:policy", {"files": ["doc1.pdf", "doc2.pdf"]})
    result = cache.get("search:policy")
    print(f"   Cached result: {result}")

    cache_stats = cache.get_statistics()
    print(f"   Cache entries: {cache_stats['total_entries']}")
    print(f"   Total hits: {cache_stats['total_hits']}")

    # Example 3: Metrics Persistence
    print("\n3. Metrics Persistence:")
    with tempfile.TemporaryDirectory() as tmpdir:
        persistence = MetricsPersistence(tmpdir)

        persistence.save_circuit_breaker_state("google-drive", {
            "state": "open",
            "failure_count": 5
        })

        states = persistence.load_circuit_breaker_states()
        print(f"   Loaded states: {list(states.keys())}")

    # Example 4: Alert System
    print("\n4. Alert System:")
    alert_mgr = AlertManager()

    alert_mgr.alert(
        AlertLevel.WARNING,
        "Rate Limit Warning",
        "Google Drive API rate limit at 90%",
        service="google-drive"
    )

    alert_mgr.alert(
        AlertLevel.CRITICAL,
        "Circuit Breaker Open",
        "GitHub API circuit breaker opened",
        service="github"
    )

    recent = alert_mgr.get_recent_alerts(10)
    print(f"   Recent alerts: {len(recent)}")
    for alert in recent:
        print(f"     - [{alert['level']}] {alert['title']}")

    print("\n" + "=" * 60)
    print("Advanced resilience examples completed!")
