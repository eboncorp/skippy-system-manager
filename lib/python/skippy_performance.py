#!/usr/bin/env python3
"""
Skippy System Manager - Performance Monitoring
Version: 1.0.0
Purpose: Performance tracking, profiling, and metrics collection
"""

import time
import psutil
import os
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from functools import wraps
import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Container for performance metrics"""

    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.cpu_percent_start: Optional[float] = None
        self.cpu_percent_end: Optional[float] = None
        self.memory_start: Optional[int] = None
        self.memory_end: Optional[int] = None
        self.disk_io_start: Optional[Dict[str, int]] = None
        self.disk_io_end: Optional[Dict[str, int]] = None
        self.custom_metrics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "name": self.name,
            "duration_seconds": self.duration,
            "cpu_usage_percent": {
                "start": self.cpu_percent_start,
                "end": self.cpu_percent_end,
                "delta": self.cpu_percent_end - self.cpu_percent_start if self.cpu_percent_end and self.cpu_percent_start else None
            },
            "memory_bytes": {
                "start": self.memory_start,
                "end": self.memory_end,
                "delta": self.memory_end - self.memory_start if self.memory_end and self.memory_start else None
            },
            "disk_io": {
                "read_bytes": self.disk_io_end.get("read_bytes", 0) - self.disk_io_start.get("read_bytes", 0) if self.disk_io_end and self.disk_io_start else None,
                "write_bytes": self.disk_io_end.get("write_bytes", 0) - self.disk_io_start.get("write_bytes", 0) if self.disk_io_end and self.disk_io_start else None
            },
            "custom_metrics": self.custom_metrics,
            "timestamp": datetime.now().isoformat()
        }

    def __str__(self) -> str:
        """Human-readable metrics"""
        lines = [f"Performance Metrics: {self.name}"]

        if self.duration:
            lines.append(f"  Duration: {self.duration:.3f}s")

        if self.cpu_percent_start is not None and self.cpu_percent_end is not None:
            delta = self.cpu_percent_end - self.cpu_percent_start
            lines.append(f"  CPU: {self.cpu_percent_start:.1f}% → {self.cpu_percent_end:.1f}% (Δ {delta:+.1f}%)")

        if self.memory_start is not None and self.memory_end is not None:
            delta = self.memory_end - self.memory_start
            lines.append(f"  Memory: {self._format_bytes(self.memory_start)} → {self._format_bytes(self.memory_end)} (Δ {self._format_bytes(delta, signed=True)})")

        if self.disk_io_start and self.disk_io_end:
            read_delta = self.disk_io_end.get("read_bytes", 0) - self.disk_io_start.get("read_bytes", 0)
            write_delta = self.disk_io_end.get("write_bytes", 0) - self.disk_io_start.get("write_bytes", 0)
            lines.append(f"  Disk I/O: Read {self._format_bytes(read_delta)}, Write {self._format_bytes(write_delta)}")

        if self.custom_metrics:
            lines.append("  Custom Metrics:")
            for key, value in self.custom_metrics.items():
                lines.append(f"    {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def _format_bytes(bytes_val: int, signed: bool = False) -> str:
        """Format bytes to human-readable string"""
        sign = "+" if signed and bytes_val > 0 else ""
        abs_val = abs(bytes_val)

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs_val < 1024.0:
                return f"{sign}{bytes_val:.2f} {unit}"
            abs_val /= 1024.0
            bytes_val /= 1024.0

        return f"{sign}{bytes_val:.2f} PB"


class PerformanceMonitor:
    """Performance monitoring and profiling"""

    def __init__(self, metrics_dir: Optional[str] = None):
        self.metrics_dir = metrics_dir or os.getenv("SKIPPY_METRICS_DIR", "/tmp/skippy_metrics")
        Path(self.metrics_dir).mkdir(parents=True, exist_ok=True)
        self.process = psutil.Process()
        self.metrics_history: Dict[str, list] = {}

    def start_monitoring(self, name: str) -> PerformanceMetrics:
        """Start monitoring performance for a named operation"""
        metrics = PerformanceMetrics(name)
        metrics.start_time = time.time()

        # Capture initial system state
        try:
            metrics.cpu_percent_start = self.process.cpu_percent()
            metrics.memory_start = self.process.memory_info().rss
            metrics.disk_io_start = self._get_disk_io()
        except Exception as e:
            logger.warning(f"Failed to capture initial metrics: {e}")

        return metrics

    def stop_monitoring(self, metrics: PerformanceMetrics) -> PerformanceMetrics:
        """Stop monitoring and finalize metrics"""
        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time

        # Capture final system state
        try:
            metrics.cpu_percent_end = self.process.cpu_percent()
            metrics.memory_end = self.process.memory_info().rss
            metrics.disk_io_end = self._get_disk_io()
        except Exception as e:
            logger.warning(f"Failed to capture final metrics: {e}")

        # Store in history
        if metrics.name not in self.metrics_history:
            self.metrics_history[metrics.name] = []
        self.metrics_history[metrics.name].append(metrics.to_dict())

        # Save to file
        self._save_metrics(metrics)

        return metrics

    @contextmanager
    def monitor(self, name: str):
        """Context manager for monitoring a code block"""
        metrics = self.start_monitoring(name)
        try:
            yield metrics
        finally:
            self.stop_monitoring(metrics)
            logger.info(str(metrics))

    def _get_disk_io(self) -> Dict[str, int]:
        """Get current disk I/O counters"""
        try:
            io_counters = self.process.io_counters()
            return {
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes
            }
        except Exception:
            return {"read_bytes": 0, "write_bytes": 0}

    def _save_metrics(self, metrics: PerformanceMetrics) -> None:
        """Save metrics to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metrics.name}_{timestamp}.json"
            filepath = Path(self.metrics_dir) / filename

            with open(filepath, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save metrics to file: {e}")

    def get_summary(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for operations"""
        if name and name in self.metrics_history:
            history = self.metrics_history[name]
        elif name:
            return {"error": f"No metrics found for: {name}"}
        else:
            # Flatten all metrics
            history = [m for metrics_list in self.metrics_history.values() for m in metrics_list]

        if not history:
            return {"error": "No metrics available"}

        durations = [m.get("duration_seconds", 0) for m in history if m.get("duration_seconds")]

        return {
            "operation": name or "all",
            "total_executions": len(history),
            "duration": {
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0,
                "avg": sum(durations) / len(durations) if durations else 0,
                "total": sum(durations) if durations else 0
            },
            "recent_metrics": history[-5:]  # Last 5 executions
        }


# Global monitor instance
_global_monitor = PerformanceMonitor()


def monitor_performance(name: Optional[str] = None):
    """
    Decorator to monitor function performance

    Usage:
        @monitor_performance()
        def my_function():
            # function code

        @monitor_performance(name="custom_operation")
        def another_function():
            # function code
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            with _global_monitor.monitor(operation_name) as metrics:
                result = func(*args, **kwargs)
                # Allow functions to add custom metrics
                if hasattr(result, "__performance_metrics__"):
                    metrics.custom_metrics.update(result.__performance_metrics__)
                return result
        return wrapper
    return decorator


@contextmanager
def monitor(name: str):
    """Convenience function for context manager monitoring"""
    with _global_monitor.monitor(name) as metrics:
        yield metrics


def get_performance_summary(name: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get performance summary"""
    return _global_monitor.get_summary(name)


class SystemMonitor:
    """Monitor overall system health"""

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system-wide metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}

    @staticmethod
    def check_health() -> Dict[str, Any]:
        """Check system health and return status"""
        metrics = SystemMonitor.get_system_metrics()

        if "error" in metrics:
            return {"status": "unknown", "error": metrics["error"]}

        warnings = []
        critical = []

        # Check CPU
        if metrics["cpu"]["percent"] > 90:
            critical.append(f"CPU usage critical: {metrics['cpu']['percent']:.1f}%")
        elif metrics["cpu"]["percent"] > 75:
            warnings.append(f"CPU usage high: {metrics['cpu']['percent']:.1f}%")

        # Check Memory
        if metrics["memory"]["percent"] > 95:
            critical.append(f"Memory usage critical: {metrics['memory']['percent']:.1f}%")
        elif metrics["memory"]["percent"] > 80:
            warnings.append(f"Memory usage high: {metrics['memory']['percent']:.1f}%")

        # Check Disk
        if metrics["disk"]["percent"] > 95:
            critical.append(f"Disk usage critical: {metrics['disk']['percent']:.1f}%")
        elif metrics["disk"]["percent"] > 80:
            warnings.append(f"Disk usage high: {metrics['disk']['percent']:.1f}%")

        if critical:
            status = "critical"
        elif warnings:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "metrics": metrics,
            "warnings": warnings,
            "critical": critical,
            "timestamp": metrics["timestamp"]
        }


if __name__ == "__main__":
    # Example usage
    print("Skippy Performance Monitoring - Examples\n")

    # Example 1: Context manager
    print("Example 1: Context Manager")
    with monitor("example_operation") as metrics:
        time.sleep(0.5)
        # Simulate some work
        data = [i**2 for i in range(100000)]
        metrics.custom_metrics["items_processed"] = len(data)

    print(metrics)
    print("\n" + "="*60 + "\n")

    # Example 2: Decorator
    print("Example 2: Decorator")

    @monitor_performance(name="expensive_calculation")
    def calculate_fibonacci(n: int) -> int:
        """Calculate fibonacci number"""
        if n <= 1:
            return n
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

    # Note: Using small n to avoid long execution
    result = calculate_fibonacci(10)
    print(f"Fibonacci(10) = {result}")
    print("\n" + "="*60 + "\n")

    # Example 3: System health check
    print("Example 3: System Health Check")
    health = SystemMonitor.check_health()
    print(f"System Status: {health['status']}")
    print(f"CPU: {health['metrics']['cpu']['percent']:.1f}%")
    print(f"Memory: {health['metrics']['memory']['percent']:.1f}%")
    print(f"Disk: {health['metrics']['disk']['percent']:.1f}%")

    if health['warnings']:
        print("\nWarnings:")
        for warning in health['warnings']:
            print(f"  - {warning}")

    if health['critical']:
        print("\nCritical Issues:")
        for issue in health['critical']:
            print(f"  - {issue}")

    print("\n" + "="*60 + "\n")

    # Example 4: Performance summary
    print("Example 4: Performance Summary")
    summary = get_performance_summary("example_operation")
    print(json.dumps(summary, indent=2))
