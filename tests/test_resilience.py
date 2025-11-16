#!/usr/bin/env python3
"""
Tests for Skippy Resilience Library
Version: 1.0.0
Created: 2025-11-16

Tests for:
- Retry with exponential backoff
- Circuit breaker pattern
- Rate limiter
- Safe JSON parsing
- Health checker
"""

import pytest
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add lib/python to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))

from skippy_resilience import (
    retry_with_backoff,
    async_retry_with_backoff,
    RetryError,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    RateLimiter,
    safe_json_parse,
    safe_json_dumps,
    HealthChecker,
    HealthCheckResult,
    get_circuit_breaker,
    get_all_circuit_breaker_states
)

from skippy_config import (
    SkippyConfig,
    ConfigValidator,
    ConfigValidationError,
    validate_environment_variables,
    load_config_with_validation
)


# =============================================================================
# RETRY DECORATOR TESTS
# =============================================================================

class TestRetryWithBackoff:
    """Test retry with exponential backoff decorator."""

    def test_successful_first_attempt(self):
        """Function succeeds on first attempt."""
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def success():
            return "done"

        assert success() == "done"

    def test_success_after_retries(self):
        """Function succeeds after retries."""
        attempts = [0]

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky()
        assert result == "success"
        assert attempts[0] == 3

    def test_max_retries_exceeded(self):
        """Raises RetryError when max retries exceeded."""
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always_fails():
            raise ConnectionError("Network error")

        with pytest.raises(RetryError) as exc_info:
            always_fails()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ConnectionError)

    def test_non_retryable_exception(self):
        """Non-retryable exceptions are raised immediately."""
        attempts = [0]

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,)
        )
        def raises_value_error():
            attempts[0] += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            raises_value_error()

        # Should only attempt once for non-retryable exception
        assert attempts[0] == 1

    def test_on_retry_callback(self):
        """on_retry callback is called on each retry."""
        retry_info = []

        def on_retry(exc, attempt):
            retry_info.append((type(exc).__name__, attempt))

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry
        )
        def flaky():
            if len(retry_info) < 2:
                raise ConnectionError("Fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert len(retry_info) == 2
        assert retry_info[0] == ("ConnectionError", 1)
        assert retry_info[1] == ("ConnectionError", 2)

    def test_exponential_backoff_timing(self):
        """Delays increase exponentially."""
        # This test is more about the logic than actual timing
        # We use very small delays for testing
        attempts = [0]

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            exponential_base=2.0
        )
        def quick_fail():
            attempts[0] += 1
            raise ConnectionError("Fail")

        start = time.time()
        with pytest.raises(RetryError):
            quick_fail()
        elapsed = time.time() - start

        # Should have delays: 0.01s, 0.02s (total ~0.03s minimum)
        assert elapsed >= 0.02  # At least base_delay * (1 + 2)


# =============================================================================
# CIRCUIT BREAKER TESTS
# =============================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_initial_state_closed(self):
        """Circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_transitions_to_open_after_failures(self):
        """Opens after failure threshold is reached."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        @cb
        def failing_service():
            raise ConnectionError("Service down")

        # Trigger failures
        for _ in range(3):
            try:
                failing_service()
            except ConnectionError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_fails_fast(self):
        """Open circuit fails immediately without calling function."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)

        call_count = [0]

        @cb
        def service():
            call_count[0] += 1
            raise ConnectionError()

        # First call fails and opens circuit
        try:
            service()
        except ConnectionError:
            pass

        # Second call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            service()

        # Function was only called once
        assert call_count[0] == 1

    def test_half_open_transition(self):
        """Circuit transitions to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        cb = CircuitBreaker("test", config)

        @cb
        def service():
            raise ConnectionError()

        # Open the circuit
        try:
            service()
        except ConnectionError:
            pass

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Check that it can execute (will transition to half-open)
        assert cb._can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_recovery_to_closed(self):
        """Circuit closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.01
        )
        cb = CircuitBreaker("test", config)

        # Force to HALF_OPEN state
        cb.state = CircuitState.HALF_OPEN
        cb.success_count = 0

        @cb
        def service():
            return "ok"

        # Successful calls
        service()
        assert cb.state == CircuitState.HALF_OPEN

        service()
        assert cb.state == CircuitState.CLOSED

    def test_get_state_returns_details(self):
        """get_state returns comprehensive state info."""
        cb = CircuitBreaker("test-service")
        cb.failure_count = 3

        state = cb.get_state()

        assert state["name"] == "test-service"
        assert state["state"] == "closed"
        assert state["failure_count"] == 3
        assert "config" in state

    def test_manual_reset(self):
        """Circuit can be manually reset."""
        cb = CircuitBreaker("test")
        cb.state = CircuitState.OPEN
        cb.failure_count = 10

        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================

class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_allows_calls_within_limit(self):
        """Allows calls when under limit."""
        limiter = RateLimiter(max_calls=5, period=1.0)

        @limiter
        def api_call():
            return "response"

        for _ in range(5):
            result = api_call()
            assert result == "response"

    def test_get_remaining_calls(self):
        """Tracks remaining calls correctly."""
        limiter = RateLimiter(max_calls=3, period=1.0)

        assert limiter.get_remaining_calls() == 3

        @limiter
        def call():
            return "ok"

        call()
        assert limiter.get_remaining_calls() == 2

        call()
        call()
        assert limiter.get_remaining_calls() == 0

    def test_cleans_old_calls(self):
        """Removes calls outside the period window."""
        limiter = RateLimiter(max_calls=2, period=0.1)

        @limiter
        def call():
            return "ok"

        call()
        call()
        assert limiter.get_remaining_calls() == 0

        # Wait for period to expire
        time.sleep(0.15)

        assert limiter.get_remaining_calls() == 2


# =============================================================================
# SAFE JSON PARSING TESTS
# =============================================================================

class TestSafeJsonParse:
    """Test safe JSON parsing functionality."""

    def test_parse_valid_json(self):
        """Parses valid JSON correctly."""
        json_str = '{"key": "value", "number": 42}'
        result = safe_json_parse(json_str)

        assert result == {"key": "value", "number": 42}

    def test_parse_empty_string_returns_default(self):
        """Empty string returns default value."""
        result = safe_json_parse("", default={"empty": True})
        assert result == {"empty": True}

    def test_parse_empty_object(self):
        """Empty JSON object returns empty dict."""
        result = safe_json_parse("{}")
        assert result == {}

    def test_parse_invalid_json_returns_default(self):
        """Invalid JSON returns default without raising."""
        result = safe_json_parse("{invalid json}", default={"error": True})
        assert result == {"error": True}

    def test_parse_invalid_json_raises_on_request(self):
        """Can raise error on invalid JSON if requested."""
        with pytest.raises(json.JSONDecodeError):
            safe_json_parse("{invalid}", default={}, raise_on_error=True)

    def test_parse_array(self):
        """Parses JSON arrays correctly."""
        result = safe_json_parse('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_null(self):
        """Handles null JSON value."""
        result = safe_json_parse("null", default={"default": True})
        assert result == {"default": True}


class TestSafeJsonDumps:
    """Test safe JSON serialization."""

    def test_dumps_dict(self):
        """Serializes dictionary to JSON."""
        obj = {"key": "value", "list": [1, 2, 3]}
        result = safe_json_dumps(obj)

        assert '"key": "value"' in result
        assert '"list": [' in result

    def test_dumps_with_non_serializable(self):
        """Returns default for non-serializable objects."""
        obj = {"func": lambda x: x}  # Functions aren't JSON serializable
        # But our implementation uses default=str, so it should work
        result = safe_json_dumps(obj)
        assert "func" in result


# =============================================================================
# HEALTH CHECKER TESTS
# =============================================================================

class TestHealthChecker:
    """Test health check infrastructure."""

    def test_register_health_check(self):
        """Can register health check functions."""
        checker = HealthChecker()

        @checker.register("database")
        def check_db():
            return True, "Database OK"

        assert "database" in checker.checks

    def test_run_single_check(self):
        """Runs individual health check."""
        checker = HealthChecker()

        @checker.register("api")
        def check_api():
            return True, "API responding", {"latency_ms": 50}

        result = checker.run_check("api")

        assert result.name == "api"
        assert result.healthy is True
        assert result.message == "API responding"
        assert result.details == {"latency_ms": 50}

    def test_run_all_checks(self):
        """Runs all registered health checks."""
        checker = HealthChecker()

        @checker.register("service1")
        def check1():
            return True, "OK"

        @checker.register("service2")
        def check2():
            return False, "Down"

        results = checker.run_all()

        assert len(results) == 2
        assert results["service1"].healthy is True
        assert results["service2"].healthy is False

    def test_is_healthy_overall(self):
        """Reports overall health status."""
        checker = HealthChecker()

        @checker.register("healthy_service")
        def check_healthy():
            return True, "OK"

        @checker.register("unhealthy_service")
        def check_unhealthy():
            return False, "Down"

        assert checker.is_healthy() is False

    def test_get_summary(self):
        """Generates health check summary."""
        checker = HealthChecker()

        @checker.register("db")
        def check_db():
            return True, "OK"

        @checker.register("cache")
        def check_cache():
            return False, "Error"

        summary = checker.get_summary()

        assert summary["overall_healthy"] is False
        assert summary["total_checks"] == 2
        assert summary["healthy_count"] == 1
        assert summary["unhealthy_count"] == 1
        assert "checks" in summary

    def test_handles_exception_in_check(self):
        """Catches exceptions in health check functions."""
        checker = HealthChecker()

        @checker.register("failing_check")
        def check_fails():
            raise RuntimeError("Unexpected error")

        result = checker.run_check("failing_check")

        assert result.healthy is False
        assert "Unexpected error" in result.message

    def test_nonexistent_check(self):
        """Returns error for nonexistent check."""
        checker = HealthChecker()
        result = checker.run_check("nonexistent")

        assert result.healthy is False
        assert "not found" in result.message


# =============================================================================
# CONFIGURATION VALIDATION TESTS
# =============================================================================

class TestSkippyConfig:
    """Test configuration dataclass."""

    def test_from_env_with_defaults(self):
        """Loads config with default values."""
        config = SkippyConfig.from_env()

        assert config.skippy_base_path is not None
        assert config.retry_max_attempts == 3
        assert config.validate_paths is True

    def test_to_dict(self):
        """Converts config to dictionary."""
        config = SkippyConfig(
            skippy_base_path="/test/path",
            retry_max_attempts=5
        )

        d = config.to_dict()

        assert d["skippy_base_path"] == "/test/path"
        assert d["retry_max_attempts"] == 5

    def test_to_json(self):
        """Converts config to JSON."""
        config = SkippyConfig(skippy_base_path="/test")
        json_str = config.to_json()

        assert '"skippy_base_path": "/test"' in json_str

    def test_from_dict(self):
        """Creates config from dictionary."""
        data = {
            "skippy_base_path": "/custom/path",
            "max_concurrent_requests": 20
        }

        config = SkippyConfig.from_dict(data)

        assert config.skippy_base_path == "/custom/path"
        assert config.max_concurrent_requests == 20


class TestConfigValidator:
    """Test configuration validation."""

    def test_validates_valid_config(self):
        """Valid config passes validation."""
        config = SkippyConfig(
            skippy_base_path="/tmp",
            ebon_host="user@10.0.0.1",
            retry_max_attempts=3,
            retry_base_delay=1.0,
            request_timeout=30.0,
            max_concurrent_requests=10
        )

        validator = ConfigValidator(config)
        # May have warnings for non-existent paths, but no errors
        validator.validate()

        # Should not have fundamental errors
        critical_errors = [e for e in validator.errors if "must be" in e]
        assert len(critical_errors) == 0

    def test_invalid_ebon_host_format(self):
        """Invalid EBON_HOST format is caught."""
        config = SkippyConfig(
            ebon_host="invalid-format"
        )

        validator = ConfigValidator(config)
        validator.validate()

        assert any("ebon_host" in e for e in validator.errors)

    def test_invalid_performance_settings(self):
        """Invalid performance settings are caught."""
        config = SkippyConfig(
            max_concurrent_requests=0,
            request_timeout=-1,
            retry_max_attempts=0
        )

        validator = ConfigValidator(config)
        validator.validate()

        assert any("max_concurrent_requests" in e for e in validator.errors)
        assert any("request_timeout" in e for e in validator.errors)
        assert any("retry_max_attempts" in e for e in validator.errors)

    def test_security_warnings(self):
        """Security warnings are generated."""
        config = SkippyConfig(
            validate_paths=False,
            validate_commands=False,
            audit_logging=False
        )

        validator = ConfigValidator(config)
        validator.validate()

        assert any("Path validation is disabled" in w for w in validator.warnings)
        assert any("Command validation is disabled" in w for w in validator.warnings)

    def test_get_validation_report(self):
        """Generates comprehensive validation report."""
        config = SkippyConfig(
            skippy_base_path="/tmp",
            retry_max_attempts=3
        )

        validator = ConfigValidator(config)
        report = validator.get_validation_report()

        assert "valid" in report
        assert "errors" in report
        assert "warnings" in report
        assert "config" in report
        assert "timestamp" in report


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestResilienceIntegration:
    """Integration tests combining multiple resilience features."""

    def test_circuit_breaker_with_retry(self):
        """Circuit breaker integrates with retry logic."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("test-service", config)
        attempts = [0]

        @cb
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky_service():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = flaky_service()
        assert result == "success"
        # Circuit breaker should still be closed after successful recovery
        assert cb.state == CircuitState.CLOSED

    def test_global_circuit_breaker_registry(self):
        """Global circuit breaker registry works correctly."""
        cb1 = get_circuit_breaker("service-a")
        cb2 = get_circuit_breaker("service-a")  # Same name

        # Should return same instance
        assert cb1 is cb2

        cb3 = get_circuit_breaker("service-b")
        assert cb1 is not cb3

        states = get_all_circuit_breaker_states()
        assert "service-a" in states
        assert "service-b" in states


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
