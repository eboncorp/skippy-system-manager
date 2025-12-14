"""
Unit tests for skippy_performance module.

Tests cover:
- PerformanceMetrics class
- PerformanceMonitor class
- Global convenience functions
- monitor_performance decorator
- SystemMonitor class
"""

import pytest
import time
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from skippy_performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    SystemMonitor,
    monitor_performance,
    monitor,
    get_performance_summary,
)


# =============================================================================
# PERFORMANCE METRICS TESTS
# =============================================================================

class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    def test_initialization(self):
        """Test basic initialization."""
        metrics = PerformanceMetrics("test_operation")
        assert metrics.name == "test_operation"
        assert metrics.start_time is None
        assert metrics.end_time is None
        assert metrics.duration is None
        assert metrics.cpu_percent_start is None
        assert metrics.cpu_percent_end is None
        assert metrics.memory_start is None
        assert metrics.memory_end is None
        assert metrics.disk_io_start is None
        assert metrics.disk_io_end is None
        assert metrics.custom_metrics == {}

    def test_to_dict_basic(self):
        """Test to_dict with minimal data."""
        metrics = PerformanceMetrics("test")
        result = metrics.to_dict()

        assert result["name"] == "test"
        assert result["duration_seconds"] is None
        assert result["cpu_usage_percent"]["start"] is None
        assert result["cpu_usage_percent"]["end"] is None
        assert result["cpu_usage_percent"]["delta"] is None
        assert result["memory_bytes"]["delta"] is None
        assert result["disk_io"]["read_bytes"] is None
        assert result["custom_metrics"] == {}
        assert "timestamp" in result

    def test_to_dict_full(self):
        """Test to_dict with all data populated."""
        metrics = PerformanceMetrics("full_test")
        metrics.start_time = 1000.0
        metrics.end_time = 1002.5
        metrics.duration = 2.5
        metrics.cpu_percent_start = 10.0
        metrics.cpu_percent_end = 25.0
        metrics.memory_start = 1000000
        metrics.memory_end = 1500000
        metrics.disk_io_start = {"read_bytes": 100, "write_bytes": 50}
        metrics.disk_io_end = {"read_bytes": 500, "write_bytes": 200}
        metrics.custom_metrics = {"items": 100}

        result = metrics.to_dict()

        assert result["name"] == "full_test"
        assert result["duration_seconds"] == 2.5
        assert result["cpu_usage_percent"]["start"] == 10.0
        assert result["cpu_usage_percent"]["end"] == 25.0
        assert result["cpu_usage_percent"]["delta"] == 15.0
        assert result["memory_bytes"]["start"] == 1000000
        assert result["memory_bytes"]["end"] == 1500000
        assert result["memory_bytes"]["delta"] == 500000
        assert result["disk_io"]["read_bytes"] == 400
        assert result["disk_io"]["write_bytes"] == 150
        assert result["custom_metrics"] == {"items": 100}

    def test_str_basic(self):
        """Test string representation with basic data."""
        metrics = PerformanceMetrics("test_op")
        result = str(metrics)
        assert "Performance Metrics: test_op" in result

    def test_str_with_duration(self):
        """Test string representation includes duration."""
        metrics = PerformanceMetrics("test_op")
        metrics.duration = 1.234
        result = str(metrics)
        assert "Duration: 1.234s" in result

    def test_str_with_cpu(self):
        """Test string representation includes CPU info."""
        metrics = PerformanceMetrics("test_op")
        metrics.cpu_percent_start = 10.0
        metrics.cpu_percent_end = 25.0
        result = str(metrics)
        assert "CPU:" in result
        assert "10.0%" in result
        assert "25.0%" in result

    def test_str_with_memory(self):
        """Test string representation includes memory info."""
        metrics = PerformanceMetrics("test_op")
        metrics.memory_start = 1000000
        metrics.memory_end = 2000000
        result = str(metrics)
        assert "Memory:" in result

    def test_str_with_disk_io(self):
        """Test string representation includes disk I/O."""
        metrics = PerformanceMetrics("test_op")
        metrics.disk_io_start = {"read_bytes": 100, "write_bytes": 50}
        metrics.disk_io_end = {"read_bytes": 1000, "write_bytes": 500}
        result = str(metrics)
        assert "Disk I/O:" in result
        assert "Read" in result
        assert "Write" in result

    def test_str_with_custom_metrics(self):
        """Test string representation includes custom metrics."""
        metrics = PerformanceMetrics("test_op")
        metrics.custom_metrics = {"items_processed": 100, "errors": 0}
        result = str(metrics)
        assert "Custom Metrics:" in result
        assert "items_processed: 100" in result
        assert "errors: 0" in result

    def test_format_bytes_small(self):
        """Test byte formatting for small values."""
        assert "100.00 B" in PerformanceMetrics._format_bytes(100)
        assert "512.00 B" in PerformanceMetrics._format_bytes(512)

    def test_format_bytes_kilobytes(self):
        """Test byte formatting for kilobytes."""
        result = PerformanceMetrics._format_bytes(1024)
        assert "KB" in result

    def test_format_bytes_megabytes(self):
        """Test byte formatting for megabytes."""
        result = PerformanceMetrics._format_bytes(1024 * 1024)
        assert "MB" in result

    def test_format_bytes_gigabytes(self):
        """Test byte formatting for gigabytes."""
        result = PerformanceMetrics._format_bytes(1024 * 1024 * 1024)
        assert "GB" in result

    def test_format_bytes_terabytes(self):
        """Test byte formatting for terabytes."""
        result = PerformanceMetrics._format_bytes(1024 * 1024 * 1024 * 1024)
        assert "TB" in result

    def test_format_bytes_petabytes(self):
        """Test byte formatting for petabytes."""
        result = PerformanceMetrics._format_bytes(1024 * 1024 * 1024 * 1024 * 1024)
        assert "PB" in result

    def test_format_bytes_signed_positive(self):
        """Test byte formatting with signed positive value."""
        result = PerformanceMetrics._format_bytes(1000, signed=True)
        assert result.startswith("+")

    def test_format_bytes_signed_negative(self):
        """Test byte formatting with negative value."""
        result = PerformanceMetrics._format_bytes(-1000, signed=True)
        # Negative values don't get a + sign
        assert not result.startswith("+")

    def test_format_bytes_zero(self):
        """Test byte formatting with zero."""
        result = PerformanceMetrics._format_bytes(0)
        assert "0.00 B" in result


# =============================================================================
# PERFORMANCE MONITOR TESTS
# =============================================================================

class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    def test_initialization_default(self):
        """Test default initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"SKIPPY_METRICS_DIR": tmpdir}):
                monitor_instance = PerformanceMonitor()
                assert monitor_instance.metrics_dir == tmpdir
                assert monitor_instance.metrics_history == {}

    def test_initialization_custom_dir(self):
        """Test initialization with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "custom_metrics")
            monitor_instance = PerformanceMonitor(metrics_dir=custom_dir)
            assert monitor_instance.metrics_dir == custom_dir
            assert Path(custom_dir).exists()

    def test_start_monitoring(self):
        """Test starting performance monitoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = monitor_instance.start_monitoring("test_op")

            assert isinstance(metrics, PerformanceMetrics)
            assert metrics.name == "test_op"
            assert metrics.start_time is not None
            assert metrics.cpu_percent_start is not None
            assert metrics.memory_start is not None
            assert metrics.disk_io_start is not None

    def test_stop_monitoring(self):
        """Test stopping performance monitoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = monitor_instance.start_monitoring("test_op")

            # Do some minimal work
            time.sleep(0.01)

            result = monitor_instance.stop_monitoring(metrics)

            assert result.end_time is not None
            assert result.duration is not None
            assert result.duration > 0
            assert result.cpu_percent_end is not None
            assert result.memory_end is not None
            assert result.disk_io_end is not None

    def test_metrics_history_recorded(self):
        """Test that metrics are added to history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = monitor_instance.start_monitoring("test_op")
            monitor_instance.stop_monitoring(metrics)

            assert "test_op" in monitor_instance.metrics_history
            assert len(monitor_instance.metrics_history["test_op"]) == 1

    def test_metrics_saved_to_file(self):
        """Test that metrics are saved to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = monitor_instance.start_monitoring("file_test")
            monitor_instance.stop_monitoring(metrics)

            # Check file was created
            files = list(Path(tmpdir).glob("file_test_*.json"))
            assert len(files) == 1

            # Verify file content
            with open(files[0]) as f:
                data = json.load(f)
            assert data["name"] == "file_test"

    def test_context_manager(self):
        """Test context manager for monitoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            with monitor_instance.monitor("context_test") as metrics:
                time.sleep(0.01)
                metrics.custom_metrics["test_value"] = 42

            assert metrics.duration is not None
            assert metrics.custom_metrics["test_value"] == 42

    def test_context_manager_with_exception(self):
        """Test context manager properly cleans up on exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            with pytest.raises(ValueError):
                with monitor_instance.monitor("exception_test") as metrics:
                    raise ValueError("Test exception")

            # Metrics should still be recorded despite exception
            assert "exception_test" in monitor_instance.metrics_history

    def test_get_disk_io(self):
        """Test disk I/O retrieval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            io_counters = monitor_instance._get_disk_io()

            assert "read_bytes" in io_counters
            assert "write_bytes" in io_counters
            assert isinstance(io_counters["read_bytes"], int)
            assert isinstance(io_counters["write_bytes"], int)

    def test_get_disk_io_fallback(self):
        """Test disk I/O fallback on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Mock io_counters to raise exception
            with patch.object(monitor_instance.process, 'io_counters',
                            side_effect=Exception("No I/O counters")):
                io_counters = monitor_instance._get_disk_io()

            assert io_counters == {"read_bytes": 0, "write_bytes": 0}

    def test_get_summary_specific_operation(self):
        """Test getting summary for specific operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Run operation twice
            for _ in range(2):
                metrics = monitor_instance.start_monitoring("summary_test")
                time.sleep(0.01)
                monitor_instance.stop_monitoring(metrics)

            summary = monitor_instance.get_summary("summary_test")

            assert summary["operation"] == "summary_test"
            assert summary["total_executions"] == 2
            assert "duration" in summary
            assert summary["duration"]["min"] > 0
            assert summary["duration"]["max"] >= summary["duration"]["min"]
            assert summary["duration"]["avg"] > 0

    def test_get_summary_all_operations(self):
        """Test getting summary for all operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Run different operations
            for name in ["op1", "op2"]:
                metrics = monitor_instance.start_monitoring(name)
                monitor_instance.stop_monitoring(metrics)

            summary = monitor_instance.get_summary()

            assert summary["operation"] == "all"
            assert summary["total_executions"] == 2

    def test_get_summary_not_found(self):
        """Test getting summary for non-existent operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            summary = monitor_instance.get_summary("nonexistent")
            assert "error" in summary

    def test_get_summary_empty(self):
        """Test getting summary when no metrics recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            summary = monitor_instance.get_summary()
            assert "error" in summary

    def test_recent_metrics_limited(self):
        """Test that recent_metrics is limited to last 5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Run 10 operations
            for _ in range(10):
                metrics = monitor_instance.start_monitoring("limit_test")
                monitor_instance.stop_monitoring(metrics)

            summary = monitor_instance.get_summary("limit_test")
            assert len(summary["recent_metrics"]) == 5

    def test_save_metrics_error_handling(self):
        """Test that save metrics handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = PerformanceMetrics("test")

            # Make directory unwritable
            with patch('builtins.open', side_effect=PermissionError("No write")):
                # Should not raise, just log warning
                monitor_instance._save_metrics(metrics)

    def test_start_monitoring_error_handling(self):
        """Test that start_monitoring handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Mock process methods to raise exception
            with patch.object(monitor_instance.process, 'cpu_percent',
                            side_effect=Exception("CPU error")):
                metrics = monitor_instance.start_monitoring("error_test")

            # Should still return metrics object
            assert metrics.name == "error_test"
            assert metrics.start_time is not None

    def test_stop_monitoring_error_handling(self):
        """Test that stop_monitoring handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)
            metrics = monitor_instance.start_monitoring("error_test")

            # Mock process methods to raise exception
            with patch.object(monitor_instance.process, 'cpu_percent',
                            side_effect=Exception("CPU error")):
                result = monitor_instance.stop_monitoring(metrics)

            # Should still return metrics with duration
            assert result.duration is not None


# =============================================================================
# DECORATOR TESTS
# =============================================================================

class TestMonitorPerformanceDecorator:
    """Tests for monitor_performance decorator."""

    def test_decorator_basic(self):
        """Test decorator with default name."""
        @monitor_performance()
        def sample_function():
            return "result"

        result = sample_function()
        assert result == "result"

    def test_decorator_custom_name(self):
        """Test decorator with custom operation name."""
        @monitor_performance(name="custom_operation")
        def sample_function():
            return 42

        result = sample_function()
        assert result == 42

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @monitor_performance()
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_decorator_passes_arguments(self):
        """Test decorator passes arguments correctly."""
        @monitor_performance()
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_decorator_passes_kwargs(self):
        """Test decorator passes keyword arguments correctly."""
        @monitor_performance()
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("World", greeting="Hi")
        assert result == "Hi, World!"

    def test_decorator_with_custom_metrics(self):
        """Test decorator can capture custom metrics from return value."""
        class ResultWithMetrics:
            def __init__(self, value):
                self.value = value
                self.__performance_metrics__ = {"custom_key": "custom_value"}

        @monitor_performance()
        def function_with_metrics():
            return ResultWithMetrics(42)

        result = function_with_metrics()
        assert result.value == 42


# =============================================================================
# GLOBAL FUNCTION TESTS
# =============================================================================

class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_monitor_context_manager(self):
        """Test global monitor context manager."""
        with monitor("global_test") as metrics:
            time.sleep(0.01)

        assert metrics.duration is not None
        assert metrics.duration > 0

    def test_get_performance_summary(self):
        """Test global get_performance_summary function."""
        # Run some operations first
        with monitor("summary_global_test"):
            time.sleep(0.01)

        summary = get_performance_summary("summary_global_test")
        assert summary["operation"] == "summary_global_test"

    def test_get_performance_summary_all(self):
        """Test global get_performance_summary for all operations."""
        summary = get_performance_summary()
        # Should return something (either metrics or error)
        assert "operation" in summary or "error" in summary


# =============================================================================
# SYSTEM MONITOR TESTS
# =============================================================================

class TestSystemMonitor:
    """Tests for SystemMonitor class."""

    def test_get_system_metrics(self):
        """Test getting system metrics."""
        metrics = SystemMonitor.get_system_metrics()

        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "timestamp" in metrics

        assert "percent" in metrics["cpu"]
        assert "count" in metrics["cpu"]

        assert "total" in metrics["memory"]
        assert "available" in metrics["memory"]
        assert "percent" in metrics["memory"]

        assert "total" in metrics["disk"]
        assert "free" in metrics["disk"]
        assert "percent" in metrics["disk"]

    def test_get_system_metrics_cpu_count(self):
        """Test that CPU count is positive integer."""
        metrics = SystemMonitor.get_system_metrics()
        assert metrics["cpu"]["count"] > 0
        assert isinstance(metrics["cpu"]["count"], int)

    def test_get_system_metrics_memory_values(self):
        """Test that memory values are reasonable."""
        metrics = SystemMonitor.get_system_metrics()
        assert metrics["memory"]["total"] > 0
        assert metrics["memory"]["available"] > 0
        assert 0 <= metrics["memory"]["percent"] <= 100

    def test_get_system_metrics_disk_values(self):
        """Test that disk values are reasonable."""
        metrics = SystemMonitor.get_system_metrics()
        assert metrics["disk"]["total"] > 0
        assert metrics["disk"]["free"] >= 0
        assert 0 <= metrics["disk"]["percent"] <= 100

    def test_get_system_metrics_error_handling(self):
        """Test error handling in get_system_metrics."""
        with patch('psutil.cpu_percent', side_effect=Exception("CPU error")):
            metrics = SystemMonitor.get_system_metrics()
            assert "error" in metrics

    def test_check_health_healthy(self):
        """Test health check returns healthy status."""
        # Mock low resource usage
        mock_metrics = {
            "cpu": {"percent": 20.0},
            "memory": {"percent": 40.0},
            "disk": {"percent": 50.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "healthy"
        assert health["warnings"] == []
        assert health["critical"] == []

    def test_check_health_warning_cpu(self):
        """Test health check with high CPU usage."""
        mock_metrics = {
            "cpu": {"percent": 80.0},
            "memory": {"percent": 40.0},
            "disk": {"percent": 50.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "warning"
        assert len(health["warnings"]) == 1
        assert "CPU" in health["warnings"][0]

    def test_check_health_warning_memory(self):
        """Test health check with high memory usage."""
        mock_metrics = {
            "cpu": {"percent": 20.0},
            "memory": {"percent": 85.0},
            "disk": {"percent": 50.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "warning"
        assert any("Memory" in w for w in health["warnings"])

    def test_check_health_warning_disk(self):
        """Test health check with high disk usage."""
        mock_metrics = {
            "cpu": {"percent": 20.0},
            "memory": {"percent": 40.0},
            "disk": {"percent": 85.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "warning"
        assert any("Disk" in w for w in health["warnings"])

    def test_check_health_critical_cpu(self):
        """Test health check with critical CPU usage."""
        mock_metrics = {
            "cpu": {"percent": 95.0},
            "memory": {"percent": 40.0},
            "disk": {"percent": 50.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "critical"
        assert len(health["critical"]) == 1
        assert "CPU" in health["critical"][0]

    def test_check_health_critical_memory(self):
        """Test health check with critical memory usage."""
        mock_metrics = {
            "cpu": {"percent": 20.0},
            "memory": {"percent": 97.0},
            "disk": {"percent": 50.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "critical"
        assert any("Memory" in c for c in health["critical"])

    def test_check_health_critical_disk(self):
        """Test health check with critical disk usage."""
        mock_metrics = {
            "cpu": {"percent": 20.0},
            "memory": {"percent": 40.0},
            "disk": {"percent": 97.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "critical"
        assert any("Disk" in c for c in health["critical"])

    def test_check_health_multiple_issues(self):
        """Test health check with multiple issues."""
        mock_metrics = {
            "cpu": {"percent": 95.0},
            "memory": {"percent": 85.0},
            "disk": {"percent": 97.0},
            "timestamp": "2025-01-01T00:00:00"
        }

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "critical"
        assert len(health["critical"]) == 2  # CPU and Disk
        assert len(health["warnings"]) == 1  # Memory

    def test_check_health_error(self):
        """Test health check when metrics retrieval fails."""
        mock_metrics = {"error": "Failed to get metrics"}

        with patch.object(SystemMonitor, 'get_system_metrics', return_value=mock_metrics):
            health = SystemMonitor.check_health()

        assert health["status"] == "unknown"
        assert "error" in health

    def test_check_health_includes_timestamp(self):
        """Test that health check includes timestamp."""
        health = SystemMonitor.check_health()
        assert "timestamp" in health


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPerformanceIntegration:
    """Integration tests for performance monitoring workflow."""

    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Start monitoring
            metrics = monitor_instance.start_monitoring("integration_test")

            # Simulate work
            data = [i**2 for i in range(10000)]
            metrics.custom_metrics["items_computed"] = len(data)

            # Stop monitoring
            monitor_instance.stop_monitoring(metrics)

            # Verify metrics
            assert metrics.duration > 0
            assert metrics.custom_metrics["items_computed"] == 10000

            # Verify file saved
            files = list(Path(tmpdir).glob("*.json"))
            assert len(files) == 1

            # Verify summary
            summary = monitor_instance.get_summary("integration_test")
            assert summary["total_executions"] == 1

    def test_multiple_operations_tracking(self):
        """Test tracking multiple different operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor_instance = PerformanceMonitor(metrics_dir=tmpdir)

            # Run different operations
            for op_name in ["read_files", "process_data", "write_results"]:
                with monitor_instance.monitor(op_name):
                    time.sleep(0.01)

            # Verify all tracked
            assert len(monitor_instance.metrics_history) == 3
            assert "read_files" in monitor_instance.metrics_history
            assert "process_data" in monitor_instance.metrics_history
            assert "write_results" in monitor_instance.metrics_history

    def test_decorator_and_context_manager_together(self):
        """Test using both decorator and context manager."""
        @monitor_performance(name="decorated_operation")
        def decorated_function():
            return sum(range(1000))

        with monitor("context_operation"):
            result = decorated_function()

        assert result == 499500
