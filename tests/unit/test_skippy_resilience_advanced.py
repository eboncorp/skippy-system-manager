"""
Unit tests for skippy_resilience_advanced module.

Tests cover:
- RequestTrace dataclass
- RequestTracer class
- MetricsPersistence class
- CacheEntry dataclass
- GracefulCache class
- AlertLevel and Alert classes
- AlertManager class
- Alert handler factory functions
- Global convenience functions
"""

import pytest
import json
import time
import tempfile
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from skippy_resilience_advanced import (
    RequestTrace,
    RequestTracer,
    MetricsPersistence,
    CacheEntry,
    GracefulCache,
    AlertLevel,
    Alert,
    AlertManager,
    create_file_alert_handler,
    create_slack_webhook_handler,
    get_tracer,
    get_cache,
    get_alert_manager,
    init_metrics_persistence,
    get_metrics_persistence,
)


# =============================================================================
# REQUEST TRACE TESTS
# =============================================================================

class TestRequestTrace:
    """Tests for RequestTrace dataclass."""

    def test_creation_minimal(self):
        """Test creating trace with minimal parameters."""
        trace = RequestTrace(
            request_id="abc123",
            service="test-service",
            operation="test-op",
            start_time=datetime.now()
        )
        assert trace.request_id == "abc123"
        assert trace.service == "test-service"
        assert trace.operation == "test-op"
        assert trace.end_time is None
        assert trace.duration_ms is None
        assert trace.success is False
        assert trace.attempt_count == 1
        assert trace.error is None
        assert trace.metadata == {}

    def test_creation_full(self):
        """Test creating trace with all parameters."""
        start = datetime.now()
        end = start + timedelta(milliseconds=100)
        trace = RequestTrace(
            request_id="xyz789",
            service="api",
            operation="fetch",
            start_time=start,
            end_time=end,
            duration_ms=100.0,
            success=True,
            attempt_count=3,
            error="some error",
            metadata={"key": "value"}
        )
        assert trace.success is True
        assert trace.attempt_count == 3
        assert trace.error == "some error"
        assert trace.metadata == {"key": "value"}

    def test_to_dict(self):
        """Test converting trace to dictionary."""
        start = datetime(2025, 1, 1, 12, 0, 0)
        end = datetime(2025, 1, 1, 12, 0, 1)
        trace = RequestTrace(
            request_id="test123",
            service="myservice",
            operation="myop",
            start_time=start,
            end_time=end,
            duration_ms=1000.0,
            success=True,
            attempt_count=2,
            error=None,
            metadata={"count": 5}
        )
        result = trace.to_dict()

        assert result["request_id"] == "test123"
        assert result["service"] == "myservice"
        assert result["operation"] == "myop"
        assert result["start_time"] == start.isoformat()
        assert result["end_time"] == end.isoformat()
        assert result["duration_ms"] == 1000.0
        assert result["success"] is True
        assert result["attempt_count"] == 2
        assert result["error"] is None
        assert result["metadata"] == {"count": 5}

    def test_to_dict_no_end_time(self):
        """Test to_dict when end_time is None."""
        trace = RequestTrace(
            request_id="test",
            service="svc",
            operation="op",
            start_time=datetime.now()
        )
        result = trace.to_dict()
        assert result["end_time"] is None


# =============================================================================
# REQUEST TRACER TESTS
# =============================================================================

class TestRequestTracer:
    """Tests for RequestTracer class."""

    def test_initialization_default(self):
        """Test default initialization."""
        tracer = RequestTracer()
        assert tracer.max_traces == 1000
        assert len(tracer.traces) == 0

    def test_initialization_custom_max(self):
        """Test initialization with custom max_traces."""
        tracer = RequestTracer(max_traces=50)
        assert tracer.max_traces == 50

    def test_start_trace(self):
        """Test starting a trace."""
        tracer = RequestTracer()
        trace = tracer.start_trace("test-service", "test-operation")

        assert trace.service == "test-service"
        assert trace.operation == "test-operation"
        assert trace.start_time is not None
        assert len(trace.request_id) == 8

    def test_end_trace(self):
        """Test ending a trace."""
        tracer = RequestTracer()
        trace = tracer.start_trace("svc", "op")
        time.sleep(0.01)
        tracer.end_trace(trace, success=True)

        assert trace.end_time is not None
        assert trace.duration_ms is not None
        assert trace.duration_ms > 0
        assert trace.success is True
        assert len(tracer.traces) == 1

    def test_end_trace_with_error(self):
        """Test ending a trace with error."""
        tracer = RequestTracer()
        trace = tracer.start_trace("svc", "op")
        tracer.end_trace(trace, success=False, error="Connection failed")

        assert trace.success is False
        assert trace.error == "Connection failed"

    def test_context_manager_success(self):
        """Test context manager for successful operation."""
        tracer = RequestTracer()

        with tracer.trace("service", "operation") as trace:
            time.sleep(0.01)
            trace.metadata["result"] = "success"

        assert trace.success is True
        assert trace.duration_ms is not None
        assert trace.metadata["result"] == "success"
        assert len(tracer.traces) == 1

    def test_context_manager_exception(self):
        """Test context manager captures exception."""
        tracer = RequestTracer()

        with pytest.raises(ValueError):
            with tracer.trace("service", "operation") as trace:
                raise ValueError("Test error")

        assert trace.success is False
        assert "Test error" in trace.error
        assert len(tracer.traces) == 1

    def test_get_recent_traces(self):
        """Test getting recent traces."""
        tracer = RequestTracer()

        for i in range(5):
            with tracer.trace("svc", f"op{i}"):
                pass

        recent = tracer.get_recent_traces(3)
        assert len(recent) == 3
        assert recent[0]["operation"] == "op2"
        assert recent[2]["operation"] == "op4"

    def test_get_traces_by_service(self):
        """Test filtering traces by service."""
        tracer = RequestTracer()

        with tracer.trace("service-a", "op1"):
            pass
        with tracer.trace("service-b", "op2"):
            pass
        with tracer.trace("service-a", "op3"):
            pass

        traces = tracer.get_traces_by_service("service-a")
        assert len(traces) == 2
        assert all(t["service"] == "service-a" for t in traces)

    def test_get_failed_traces(self):
        """Test getting failed traces."""
        tracer = RequestTracer()

        with tracer.trace("svc", "success"):
            pass

        try:
            with tracer.trace("svc", "fail"):
                raise Exception("Failure")
        except Exception:
            pass

        failed = tracer.get_failed_traces()
        assert len(failed) == 1
        assert failed[0]["operation"] == "fail"

    def test_get_statistics_empty(self):
        """Test statistics with no traces."""
        tracer = RequestTracer()
        stats = tracer.get_statistics()

        assert stats["total"] == 0
        assert stats["success_rate"] == 0
        assert stats["avg_duration_ms"] == 0

    def test_get_statistics_with_traces(self):
        """Test statistics with traces."""
        tracer = RequestTracer()

        # 2 successful, 1 failed
        with tracer.trace("svc", "op1"):
            time.sleep(0.01)
        with tracer.trace("svc", "op2"):
            time.sleep(0.01)
        try:
            with tracer.trace("svc", "op3"):
                raise Exception("fail")
        except Exception:
            pass

        stats = tracer.get_statistics()

        assert stats["total"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert 60 < stats["success_rate"] < 70  # ~66.67%
        assert stats["avg_duration_ms"] > 0
        assert stats["max_duration_ms"] >= stats["min_duration_ms"]

    def test_max_traces_limit(self):
        """Test that traces are limited by max_traces."""
        tracer = RequestTracer(max_traces=5)

        for i in range(10):
            with tracer.trace("svc", f"op{i}"):
                pass

        assert len(tracer.traces) == 5
        # Should have most recent 5
        operations = [t.operation for t in tracer.traces]
        assert "op5" in operations
        assert "op9" in operations
        assert "op0" not in operations

    def test_thread_safety(self):
        """Test thread safety of tracer."""
        tracer = RequestTracer()
        errors = []

        def trace_operation(n):
            try:
                with tracer.trace("svc", f"op{n}"):
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=trace_operation, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(tracer.traces) == 20


# =============================================================================
# METRICS PERSISTENCE TESTS
# =============================================================================

class TestMetricsPersistence:
    """Tests for MetricsPersistence class."""

    def test_initialization_custom_dir(self):
        """Test initialization with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            assert persistence.metrics_dir == Path(tmpdir)

    def test_initialization_default_dir(self):
        """Test initialization with default directory."""
        with patch.dict('os.environ', {"SKIPPY_BASE_PATH": "/tmp/test_skippy"}):
            persistence = MetricsPersistence()
            assert "metrics" in str(persistence.metrics_dir)

    def test_save_circuit_breaker_state(self):
        """Test saving circuit breaker state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            persistence.save_circuit_breaker_state("test-cb", {
                "state": "open",
                "failure_count": 5
            })

            cb_file = Path(tmpdir) / "circuit_breakers.json"
            assert cb_file.exists()

            with open(cb_file) as f:
                data = json.load(f)
            assert "test-cb" in data
            assert data["test-cb"]["state"] == "open"
            assert "last_updated" in data["test-cb"]

    def test_save_circuit_breaker_state_multiple(self):
        """Test saving multiple circuit breaker states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            persistence.save_circuit_breaker_state("cb1", {"state": "closed"})
            persistence.save_circuit_breaker_state("cb2", {"state": "open"})

            states = persistence.load_circuit_breaker_states()
            assert len(states) == 2
            assert "cb1" in states
            assert "cb2" in states

    def test_load_circuit_breaker_states_empty(self):
        """Test loading when no states saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            states = persistence.load_circuit_breaker_states()
            assert states == {}

    def test_save_request_traces(self):
        """Test saving request traces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            traces = [
                {"request_id": "1", "service": "svc", "operation": "op1"},
                {"request_id": "2", "service": "svc", "operation": "op2"}
            ]
            persistence.save_request_traces(traces)

            # Check file exists
            trace_files = list(Path(tmpdir).glob("traces_*.jsonl"))
            assert len(trace_files) == 1

            # Check content
            with open(trace_files[0]) as f:
                lines = f.readlines()
            assert len(lines) == 2

    def test_save_health_snapshot(self):
        """Test saving health snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            persistence.save_health_snapshot({
                "status": "healthy",
                "cpu_percent": 25.0
            })

            snapshot_files = list(Path(tmpdir).glob("health_*.json"))
            assert len(snapshot_files) == 1

    def test_save_alert(self):
        """Test saving alert."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            persistence.save_alert({
                "level": "warning",
                "title": "Test Alert",
                "message": "Test message"
            })

            alerts_file = Path(tmpdir) / "alerts.jsonl"
            assert alerts_file.exists()

            with open(alerts_file) as f:
                line = f.readline()
            alert = json.loads(line)
            assert alert["title"] == "Test Alert"
            assert "timestamp" in alert

    def test_get_recent_alerts(self):
        """Test getting recent alerts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)

            # Save some alerts
            for i in range(3):
                persistence.save_alert({
                    "level": "info",
                    "title": f"Alert {i}",
                    "message": "Test"
                })

            alerts = persistence.get_recent_alerts(hours=1)
            assert len(alerts) == 3

    def test_get_recent_alerts_empty(self):
        """Test getting alerts when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)
            alerts = persistence.get_recent_alerts()
            assert alerts == []

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)

            # Create some files
            persistence.save_circuit_breaker_state("cb", {"state": "closed"})
            persistence.save_alert({"title": "test"})

            summary = persistence.get_metrics_summary()

            assert summary["metrics_dir"] == tmpdir
            assert "files" in summary
            assert "total_size_mb" in summary
            assert len(summary["files"]) >= 1

    def test_cleanup_old_files(self):
        """Test cleanup of old files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)

            # Create an old file
            old_file = Path(tmpdir) / "health_old.json"
            old_file.write_text("{}")
            # Set modification time to 48 hours ago
            import os
            old_time = time.time() - (48 * 3600)
            os.utime(old_file, (old_time, old_time))

            # Create a new file
            persistence.save_health_snapshot({"status": "ok"})

            # Trigger cleanup
            persistence._cleanup_old_files("health_*.json", hours=24)

            # Old file should be deleted
            assert not old_file.exists()

    def test_error_handling_save(self):
        """Test error handling on save failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)

            # Mock file open to raise exception
            with patch('builtins.open', side_effect=PermissionError("No write")):
                # Should not raise, just log
                persistence.save_circuit_breaker_state("cb", {"state": "open"})

    def test_error_handling_load(self):
        """Test error handling on load failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = MetricsPersistence(tmpdir)

            # Create invalid JSON file
            cb_file = Path(tmpdir) / "circuit_breakers.json"
            cb_file.write_text("invalid json")

            states = persistence.load_circuit_breaker_states()
            assert states == {}


# =============================================================================
# CACHE ENTRY TESTS
# =============================================================================

class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_creation(self):
        """Test creating cache entry."""
        entry = CacheEntry(
            key="test-key",
            value={"data": "value"},
            timestamp=datetime.now(),
            ttl_seconds=3600
        )
        assert entry.key == "test-key"
        assert entry.value == {"data": "value"}
        assert entry.hit_count == 0

    def test_is_expired_false(self):
        """Test entry is not expired."""
        entry = CacheEntry(
            key="test",
            value="data",
            timestamp=datetime.now(),
            ttl_seconds=3600
        )
        assert entry.is_expired() is False

    def test_is_expired_true(self):
        """Test entry is expired."""
        entry = CacheEntry(
            key="test",
            value="data",
            timestamp=datetime.now() - timedelta(seconds=10),
            ttl_seconds=5
        )
        assert entry.is_expired() is True


# =============================================================================
# GRACEFUL CACHE TESTS
# =============================================================================

class TestGracefulCache:
    """Tests for GracefulCache class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        cache = GracefulCache()
        assert cache.max_entries == 1000
        assert cache.default_ttl == 3600

    def test_initialization_custom(self):
        """Test custom initialization."""
        cache = GracefulCache(max_entries=100, default_ttl=1800)
        assert cache.max_entries == 100
        assert cache.default_ttl == 1800

    def test_set_and_get(self):
        """Test basic set and get."""
        cache = GracefulCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent(self):
        """Test getting non-existent key."""
        cache = GracefulCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_set_with_custom_ttl(self):
        """Test set with custom TTL."""
        cache = GracefulCache()
        cache.set("key", "value", ttl=1)
        time.sleep(1.1)

        result = cache.get("key")
        assert result is None

    def test_get_expired_entry(self):
        """Test getting expired entry."""
        cache = GracefulCache(default_ttl=1)
        cache.set("key", "value")
        time.sleep(1.1)

        # Without allow_stale
        result = cache.get("key")
        assert result is None

    def test_get_stale_allowed(self):
        """Test getting stale entry when allowed."""
        cache = GracefulCache(default_ttl=1)
        cache.set("key", "stale_value")
        time.sleep(1.1)

        result = cache.get("key", allow_stale=True)
        assert result == "stale_value"

    def test_hit_count_incremented(self):
        """Test that hit count is incremented."""
        cache = GracefulCache()
        cache.set("key", "value")

        cache.get("key")
        cache.get("key")
        cache.get("key")

        stats = cache.get_statistics()
        assert stats["total_hits"] == 3

    def test_get_with_metadata(self):
        """Test getting value with metadata."""
        cache = GracefulCache(default_ttl=3600)
        cache.set("key", "value")

        cache.get("key")  # Increment hit count

        meta = cache.get_with_metadata("key")

        assert meta["value"] == "value"
        assert meta["hit_count"] == 1
        assert meta["age_seconds"] < 1
        assert meta["is_stale"] is False
        assert meta["ttl_remaining"] > 0

    def test_get_with_metadata_nonexistent(self):
        """Test get_with_metadata for non-existent key."""
        cache = GracefulCache()
        result = cache.get_with_metadata("nonexistent")
        assert result is None

    def test_invalidate(self):
        """Test invalidating single entry."""
        cache = GracefulCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.invalidate("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_invalidate_nonexistent(self):
        """Test invalidating non-existent key (should not raise)."""
        cache = GracefulCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_invalidate_pattern(self):
        """Test invalidating by pattern."""
        cache = GracefulCache()
        cache.set("user:1:profile", "profile1")
        cache.set("user:2:profile", "profile2")
        cache.set("product:1:info", "product1")

        cache.invalidate_pattern("user:")

        assert cache.get("user:1:profile") is None
        assert cache.get("user:2:profile") is None
        assert cache.get("product:1:info") == "product1"

    def test_clear(self):
        """Test clearing all entries."""
        cache = GracefulCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        stats = cache.get_statistics()
        assert stats["total_entries"] == 0

    def test_eviction_on_capacity(self):
        """Test eviction when at capacity."""
        cache = GracefulCache(max_entries=3)

        cache.set("key1", "value1")
        time.sleep(0.01)
        cache.set("key2", "value2")
        time.sleep(0.01)
        cache.set("key3", "value3")
        time.sleep(0.01)
        cache.set("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_get_statistics(self):
        """Test getting cache statistics."""
        cache = GracefulCache(max_entries=100, default_ttl=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=3600)  # Long TTL
        time.sleep(1.1)  # Let key1 expire

        stats = cache.get_statistics()

        assert stats["total_entries"] == 2
        assert stats["stale_entries"] == 1
        assert stats["valid_entries"] == 1
        assert stats["capacity_percent"] == 2.0

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = GracefulCache(default_ttl=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=3600)
        time.sleep(1.1)

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("key1", allow_stale=True) is None
        assert cache.get("key2") == "value2"

    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        cache = GracefulCache()
        errors = []

        def write_operations(n):
            try:
                for i in range(10):
                    cache.set(f"key{n}_{i}", f"value{n}_{i}")
            except Exception as e:
                errors.append(e)

        def read_operations(n):
            try:
                for i in range(10):
                    cache.get(f"key{n}_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=write_operations, args=(i,)))
            threads.append(threading.Thread(target=read_operations, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# =============================================================================
# ALERT TESTS
# =============================================================================

class TestAlertLevel:
    """Tests for AlertLevel class."""

    def test_alert_levels(self):
        """Test alert level values."""
        assert AlertLevel.INFO == "info"
        assert AlertLevel.WARNING == "warning"
        assert AlertLevel.ERROR == "error"
        assert AlertLevel.CRITICAL == "critical"


class TestAlert:
    """Tests for Alert dataclass."""

    def test_creation_minimal(self):
        """Test creating alert with minimal parameters."""
        alert = Alert(
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="Test message"
        )
        assert alert.level == "warning"
        assert alert.title == "Test Alert"
        assert alert.message == "Test message"
        assert alert.service is None
        assert alert.metadata == {}
        assert alert.timestamp is not None

    def test_creation_full(self):
        """Test creating alert with all parameters."""
        alert = Alert(
            level=AlertLevel.CRITICAL,
            title="Critical Alert",
            message="Something bad happened",
            service="test-service",
            metadata={"error_code": 500}
        )
        assert alert.service == "test-service"
        assert alert.metadata == {"error_code": 500}

    def test_to_dict(self):
        """Test converting alert to dictionary."""
        alert = Alert(
            level=AlertLevel.ERROR,
            title="Error Alert",
            message="An error occurred",
            service="api",
            metadata={"details": "info"}
        )
        result = alert.to_dict()

        assert result["level"] == "error"
        assert result["title"] == "Error Alert"
        assert result["message"] == "An error occurred"
        assert result["service"] == "api"
        assert result["metadata"] == {"details": "info"}
        assert "timestamp" in result


# =============================================================================
# ALERT MANAGER TESTS
# =============================================================================

class TestAlertManager:
    """Tests for AlertManager class."""

    def test_initialization(self):
        """Test initialization with default handler."""
        manager = AlertManager()
        assert "log" in manager.handlers

    def test_add_handler(self):
        """Test adding custom handler."""
        manager = AlertManager()

        def custom_handler(alert):
            pass

        manager.add_handler("custom", custom_handler)
        assert "custom" in manager.handlers

    def test_remove_handler(self):
        """Test removing handler."""
        manager = AlertManager()
        manager.remove_handler("log")
        assert "log" not in manager.handlers

    def test_remove_nonexistent_handler(self):
        """Test removing non-existent handler (should not raise)."""
        manager = AlertManager()
        manager.remove_handler("nonexistent")

    def test_alert_basic(self):
        """Test sending basic alert."""
        manager = AlertManager()
        manager.remove_handler("log")  # Remove to avoid log output

        alerts_received = []
        manager.add_handler("test", lambda a: alerts_received.append(a))

        manager.alert(AlertLevel.WARNING, "Test Title", "Test message")

        assert len(alerts_received) == 1
        assert alerts_received[0].title == "Test Title"
        assert alerts_received[0].level == "warning"

    def test_alert_with_service(self):
        """Test sending alert with service."""
        manager = AlertManager()
        manager.remove_handler("log")

        alerts_received = []
        manager.add_handler("test", lambda a: alerts_received.append(a))

        manager.alert(
            AlertLevel.ERROR,
            "Service Error",
            "Service failed",
            service="my-service"
        )

        assert alerts_received[0].service == "my-service"

    def test_alert_with_metadata(self):
        """Test sending alert with metadata."""
        manager = AlertManager()
        manager.remove_handler("log")

        alerts_received = []
        manager.add_handler("test", lambda a: alerts_received.append(a))

        manager.alert(
            AlertLevel.INFO,
            "Info Alert",
            "Info message",
            custom_field="custom_value",
            count=42
        )

        assert alerts_received[0].metadata["custom_field"] == "custom_value"
        assert alerts_received[0].metadata["count"] == 42

    def test_alert_history(self):
        """Test that alerts are stored in history."""
        manager = AlertManager()
        manager.remove_handler("log")

        for i in range(3):
            manager.alert(AlertLevel.INFO, f"Alert {i}", "Message")

        assert len(manager.alert_history) == 3

    def test_get_recent_alerts(self):
        """Test getting recent alerts."""
        manager = AlertManager()
        manager.remove_handler("log")

        for i in range(10):
            manager.alert(AlertLevel.INFO, f"Alert {i}", "Message")

        recent = manager.get_recent_alerts(5)
        assert len(recent) == 5
        assert recent[0]["title"] == "Alert 5"
        assert recent[4]["title"] == "Alert 9"

    def test_get_alerts_by_level(self):
        """Test filtering alerts by level."""
        manager = AlertManager()
        manager.remove_handler("log")

        manager.alert(AlertLevel.INFO, "Info", "msg")
        manager.alert(AlertLevel.WARNING, "Warning", "msg")
        manager.alert(AlertLevel.ERROR, "Error", "msg")
        manager.alert(AlertLevel.WARNING, "Warning 2", "msg")

        warnings = manager.get_alerts_by_level(AlertLevel.WARNING)
        assert len(warnings) == 2
        assert all(a["level"] == "warning" for a in warnings)

    def test_handler_exception_handling(self):
        """Test that handler exceptions don't break alert system."""
        manager = AlertManager()
        manager.remove_handler("log")

        def failing_handler(alert):
            raise Exception("Handler failed")

        good_alerts = []
        manager.add_handler("failing", failing_handler)
        manager.add_handler("good", lambda a: good_alerts.append(a))

        # Should not raise
        manager.alert(AlertLevel.INFO, "Test", "Message")

        # Good handler should still receive alert
        assert len(good_alerts) == 1

    def test_log_handler(self):
        """Test default log handler."""
        manager = AlertManager()

        # Just verify it doesn't raise for different levels
        for level in [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]:
            manager.alert(level, "Test", "Message")


# =============================================================================
# ALERT HANDLER FACTORY TESTS
# =============================================================================

class TestFileAlertHandler:
    """Tests for create_file_alert_handler."""

    def test_file_handler_writes(self):
        """Test that file handler writes alerts."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            filepath = f.name

        try:
            handler = create_file_alert_handler(filepath)
            alert = Alert(
                level=AlertLevel.WARNING,
                title="Test",
                message="Test message"
            )

            handler(alert)

            with open(filepath) as f:
                line = f.readline()
            data = json.loads(line)
            assert data["title"] == "Test"

        finally:
            Path(filepath).unlink()

    def test_file_handler_thread_safety(self):
        """Test file handler thread safety."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            filepath = f.name

        try:
            handler = create_file_alert_handler(filepath)
            errors = []

            def write_alert(n):
                try:
                    alert = Alert(
                        level=AlertLevel.INFO,
                        title=f"Alert {n}",
                        message="Test"
                    )
                    handler(alert)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=write_alert, args=(i,)) for i in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0

            with open(filepath) as f:
                lines = f.readlines()
            assert len(lines) == 10

        finally:
            Path(filepath).unlink()


class TestSlackWebhookHandler:
    """Tests for create_slack_webhook_handler."""

    def test_slack_handler_creation(self):
        """Test creating Slack webhook handler."""
        handler = create_slack_webhook_handler("https://hooks.slack.com/test")
        assert callable(handler)

    def test_slack_handler_sends_request(self):
        """Test Slack handler sends HTTP request."""
        with patch('httpx.post') as mock_post:
            handler = create_slack_webhook_handler("https://hooks.slack.com/test")
            alert = Alert(
                level=AlertLevel.ERROR,
                title="Error Alert",
                message="Something went wrong",
                service="test-service"
            )

            handler(alert)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "hooks.slack.com" in call_args[0][0]
            assert "json" in call_args[1]

    def test_slack_handler_error_handling(self):
        """Test Slack handler handles errors gracefully."""
        with patch('httpx.post', side_effect=Exception("Network error")):
            handler = create_slack_webhook_handler("https://hooks.slack.com/test")
            alert = Alert(
                level=AlertLevel.INFO,
                title="Test",
                message="Test"
            )

            # Should not raise
            handler(alert)


# =============================================================================
# GLOBAL FUNCTION TESTS
# =============================================================================

class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_get_tracer(self):
        """Test getting global tracer."""
        tracer = get_tracer()
        assert isinstance(tracer, RequestTracer)

    def test_get_cache(self):
        """Test getting global cache."""
        cache = get_cache()
        assert isinstance(cache, GracefulCache)

    def test_get_alert_manager(self):
        """Test getting global alert manager."""
        manager = get_alert_manager()
        assert isinstance(manager, AlertManager)

    def test_init_and_get_metrics_persistence(self):
        """Test initializing and getting metrics persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = init_metrics_persistence(tmpdir)
            assert isinstance(persistence, MetricsPersistence)

            retrieved = get_metrics_persistence()
            assert retrieved is persistence


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestResilienceIntegration:
    """Integration tests for advanced resilience features."""

    def test_full_workflow(self):
        """Test complete resilience workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            tracer = RequestTracer()
            cache = GracefulCache(default_ttl=3600)
            persistence = MetricsPersistence(tmpdir)
            alert_mgr = AlertManager()
            alert_mgr.remove_handler("log")

            alerts = []
            alert_mgr.add_handler("test", lambda a: alerts.append(a))

            # Simulate successful API call
            with tracer.trace("api", "fetch-data") as trace:
                result = {"data": [1, 2, 3]}
                cache.set("api:fetch-data:latest", result)
                trace.metadata["items"] = len(result["data"])

            # Save trace
            persistence.save_request_traces(tracer.get_recent_traces(10))

            # Simulate circuit breaker opening
            persistence.save_circuit_breaker_state("api", {
                "state": "open",
                "failure_count": 5
            })

            alert_mgr.alert(
                AlertLevel.WARNING,
                "Circuit Breaker Open",
                "API circuit breaker opened",
                service="api"
            )

            # Use cached data (graceful degradation)
            cached_result = cache.get("api:fetch-data:latest")
            assert cached_result == result

            # Verify everything recorded
            stats = tracer.get_statistics()
            assert stats["total"] == 1
            assert stats["success_rate"] == 100

            cb_states = persistence.load_circuit_breaker_states()
            assert "api" in cb_states

            assert len(alerts) == 1
            assert alerts[0].title == "Circuit Breaker Open"
