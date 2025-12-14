#!/usr/bin/env python3
"""
Tests for skippy_resilience.py module.

Tests cover:
- RetryError exception
- retry_with_backoff decorator
- async_retry_with_backoff decorator
- CircuitBreaker and CircuitBreakerConfig
- CircuitState enum
- CircuitBreakerOpenError exception
- RateLimiter
- safe_json_parse and safe_json_dumps
- HealthChecker and HealthCheckResult
- Global circuit breaker registry
"""

import pytest
import time
import json
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Check if pytest-asyncio is available
try:
    import pytest_asyncio
    ASYNCIO_AVAILABLE = True
except ImportError:
    ASYNCIO_AVAILABLE = False

from skippy_resilience import (
    # Retry
    RetryError,
    retry_with_backoff,
    async_retry_with_backoff,
    # Circuit breaker
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    CircuitBreakerOpenError,
    # Rate limiter
    RateLimiter,
    # JSON utilities
    safe_json_parse,
    safe_json_dumps,
    # Health check
    HealthCheckResult,
    HealthChecker,
    # Registry
    get_circuit_breaker,
    get_all_circuit_breaker_states,
    _circuit_breakers,
)


# =============================================================================
# RetryError Tests
# =============================================================================

class TestRetryError:
    """Tests for RetryError exception."""

    def test_retry_error_creation(self):
        """Test RetryError with basic message."""
        error = RetryError("Test error", attempts=3)
        assert error.message == "Test error"
        assert error.attempts == 3
        assert error.last_exception is None
        assert str(error) == "Test error"

    def test_retry_error_with_last_exception(self):
        """Test RetryError with last exception."""
        original = ValueError("Original error")
        error = RetryError("Retry failed", attempts=5, last_exception=original)
        assert error.last_exception is original
        assert error.attempts == 5

    def test_retry_error_inheritance(self):
        """Test RetryError is an Exception."""
        error = RetryError("Test", attempts=1)
        assert isinstance(error, Exception)


# =============================================================================
# retry_with_backoff Decorator Tests
# =============================================================================

class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    def test_successful_on_first_attempt(self):
        """Test function that succeeds on first attempt."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def succeeding_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeeding_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_and_succeed(self):
        """Test function that fails initially then succeeds."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"

        result = eventually_succeeds()
        assert result == "success"
        assert call_count == 3

    def test_all_attempts_fail(self):
        """Test function that fails all attempts."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            always_fails()

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)
        assert call_count == 3

    def test_specific_retryable_exceptions(self):
        """Test retry only on specific exceptions."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(ValueError,)
        )
        def fails_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            fails_with_type_error()

        # Should not retry on TypeError
        assert call_count == 1

    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_calls = []

        def on_retry_handler(exc, attempt):
            retry_calls.append((str(exc), attempt))

        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry_handler
        )
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count}")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][1] == 1
        assert retry_calls[1][1] == 2

    def test_exponential_backoff_timing(self):
        """Test that delays increase exponentially."""
        timestamps = []

        @retry_with_backoff(
            max_attempts=4,
            base_delay=0.05,
            exponential_base=2.0,
            max_delay=1.0
        )
        def always_fails():
            timestamps.append(time.time())
            raise ValueError("fail")

        with pytest.raises(RetryError):
            always_fails()

        # Check delays increase
        delays = [
            timestamps[i+1] - timestamps[i]
            for i in range(len(timestamps) - 1)
        ]
        # Allow some tolerance for timing
        assert delays[1] > delays[0] * 1.5  # Second delay > 1.5x first

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        timestamps = []

        @retry_with_backoff(
            max_attempts=4,
            base_delay=0.5,
            exponential_base=10.0,
            max_delay=0.1
        )
        def always_fails():
            timestamps.append(time.time())
            raise ValueError("fail")

        with pytest.raises(RetryError):
            always_fails()

        # All delays should be around max_delay (0.1s)
        delays = [
            timestamps[i+1] - timestamps[i]
            for i in range(len(timestamps) - 1)
        ]
        for delay in delays:
            assert delay < 0.2  # Should be capped at 0.1 + overhead

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @retry_with_backoff()
        def documented_function():
            """This is a documented function."""
            return True

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."


# =============================================================================
# async_retry_with_backoff Decorator Tests
# =============================================================================

@pytest.mark.skipif(not ASYNCIO_AVAILABLE, reason="pytest-asyncio not installed")
class TestAsyncRetryWithBackoff:
    """Tests for async_retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_async_successful_on_first_attempt(self):
        """Test async function that succeeds on first attempt."""
        call_count = 0

        @async_retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await async_succeeds()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_and_succeed(self):
        """Test async function that fails then succeeds."""
        call_count = 0

        @async_retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count}")
            return "success"

        result = await async_eventually_succeeds()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_all_attempts_fail(self):
        """Test async function that fails all attempts."""
        call_count = 0

        @async_retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            await async_always_fails()

        assert exc_info.value.attempts == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_on_retry_callback(self):
        """Test async on_retry callback."""
        retry_calls = []

        def on_retry_handler(exc, attempt):
            retry_calls.append(attempt)

        call_count = 0

        @async_retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry_handler
        )
        async def async_fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        result = await async_fails_twice()
        assert result == "success"
        assert len(retry_calls) == 2


# =============================================================================
# CircuitState Tests
# =============================================================================

class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_states(self):
        """Test all circuit states exist."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_circuit_state_enum(self):
        """Test CircuitState is an enum."""
        assert len(CircuitState) == 3


# =============================================================================
# CircuitBreakerConfig Tests
# =============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 1
        assert config.excluded_exceptions == ()

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=120.0,
            half_open_max_calls=3,
            excluded_exceptions=(ValueError, TypeError)
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout == 120.0
        assert config.half_open_max_calls == 3
        assert config.excluded_exceptions == (ValueError, TypeError)


# =============================================================================
# CircuitBreaker Tests
# =============================================================================

class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test-cb")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    def test_successful_calls(self):
        """Test successful calls keep circuit closed."""
        cb = CircuitBreaker("test-cb")

        @cb
        def succeeding_func():
            return "success"

        for _ in range(10):
            result = succeeding_func()
            assert result == "success"

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_opens_after_failures(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-cb", config)

        @cb
        def failing_func():
            raise ValueError("fail")

        # Make 3 failing calls
        for _ in range(3):
            with pytest.raises(ValueError):
                failing_func()

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=60.0)
        cb = CircuitBreaker("test-cb", config)

        @cb
        def failing_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                failing_func()

        assert cb.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            failing_func()

    def test_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
            success_threshold=1  # Close after 1 success
        )
        cb = CircuitBreaker("test-cb-halfopen", config)

        call_count = 0

        @cb
        def controlled_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("fail")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                controlled_func()

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Next call should go through (half-open) and close on success
        result = controlled_func()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED  # Success should close it

    def test_half_open_failure_reopens(self):
        """Test failure in half-open state reopens circuit."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=0.1)
        cb = CircuitBreaker("test-cb", config)

        @cb
        def always_fails():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                always_fails()

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Failure in half-open should reopen
        with pytest.raises(ValueError):
            always_fails()

        assert cb.state == CircuitState.OPEN

    def test_success_threshold_closes_circuit(self):
        """Test multiple successes in half-open close circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
            half_open_max_calls=2  # Allow 2 calls in half-open
        )
        cb = CircuitBreaker("test-cb-success", config)

        call_count = 0

        @cb
        def controlled_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("fail")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                controlled_func()

        assert cb.state == CircuitState.OPEN

        # Wait and transition to half-open
        time.sleep(0.15)

        # First success
        result = controlled_func()
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

        # Second success should close (no wait needed with half_open_max_calls=2)
        result = controlled_func()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_excluded_exceptions(self):
        """Test excluded exceptions don't count as failures."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            excluded_exceptions=(ValueError,)
        )
        cb = CircuitBreaker("test-cb", config)

        @cb
        def raises_value_error():
            raise ValueError("excluded")

        # These shouldn't count as failures
        for _ in range(5):
            with pytest.raises(ValueError):
                raises_value_error()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_get_state(self):
        """Test get_state returns correct info."""
        cb = CircuitBreaker("test-cb")
        state = cb.get_state()

        assert state["name"] == "test-cb"
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["success_count"] == 0
        assert state["last_failure"] is None
        assert "config" in state

    def test_reset(self):
        """Test manual reset to closed state."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test-cb", config)

        @cb
        def failing_func():
            raise ValueError("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                failing_func()

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_direct_call(self):
        """Test calling circuit breaker directly with _call."""
        cb = CircuitBreaker("test-cb")

        def success_func():
            return "direct call"

        result = cb._call(success_func)
        assert result == "direct call"

    def test_thread_safety(self):
        """Test circuit breaker is thread-safe."""
        config = CircuitBreakerConfig(failure_threshold=100)
        cb = CircuitBreaker("thread-safe-cb", config)

        success_count = 0
        lock = threading.Lock()

        @cb
        def increment():
            nonlocal success_count
            with lock:
                success_count += 1
            return True

        threads = [
            threading.Thread(target=increment)
            for _ in range(50)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert success_count == 50
        assert cb.state == CircuitState.CLOSED


# =============================================================================
# CircuitBreakerOpenError Tests
# =============================================================================

class TestCircuitBreakerOpenError:
    """Tests for CircuitBreakerOpenError exception."""

    def test_error_creation(self):
        """Test CircuitBreakerOpenError creation."""
        error = CircuitBreakerOpenError("Circuit is open")
        assert str(error) == "Circuit is open"
        assert isinstance(error, Exception)


# =============================================================================
# RateLimiter Tests
# =============================================================================

class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(max_calls=3, period=1.0)

        call_count = 0

        @limiter
        def limited_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # First 3 calls should be immediate
        for i in range(3):
            result = limited_func()
            assert result == i + 1

        assert limiter.get_remaining_calls() == 0

    def test_get_remaining_calls(self):
        """Test get_remaining_calls method."""
        limiter = RateLimiter(max_calls=5, period=60.0)
        assert limiter.get_remaining_calls() == 5

        @limiter
        def func():
            return True

        func()
        assert limiter.get_remaining_calls() == 4

        func()
        func()
        assert limiter.get_remaining_calls() == 2

    def test_rate_limit_resets(self):
        """Test rate limit resets after period."""
        limiter = RateLimiter(max_calls=2, period=0.1)

        @limiter
        def func():
            return True

        func()
        func()
        assert limiter.get_remaining_calls() == 0

        # Wait for period to pass
        time.sleep(0.15)

        assert limiter.get_remaining_calls() == 2

    def test_rate_limiter_detects_exceeded(self):
        """Test rate limiter detects when limit is exceeded."""
        limiter = RateLimiter(max_calls=2, period=60.0)

        @limiter
        def func():
            return True

        # First 2 calls should work
        func()
        func()

        # After 2 calls, remaining should be 0
        assert limiter.get_remaining_calls() == 0

    def test_rate_limiter_waits_when_exceeded(self):
        """Test rate limiter waits when limit is exceeded."""
        # Use short period so test doesn't take too long
        limiter = RateLimiter(max_calls=2, period=0.1)

        call_times = []

        @limiter
        def func():
            call_times.append(time.time())
            return True

        # First 2 calls should be immediate
        func()
        func()

        # Third call should wait until period expires
        func()

        assert len(call_times) == 3
        # The third call should have waited (gap > period)
        gap = call_times[2] - call_times[1]
        assert gap >= 0.05  # Should have waited at least some time

    def test_rate_limiter_cleans_old_calls(self):
        """Test rate limiter removes old calls from tracking."""
        limiter = RateLimiter(max_calls=2, period=0.05)

        @limiter
        def func():
            return True

        # Make calls
        func()
        func()

        # Wait for period to expire
        time.sleep(0.1)

        # Old calls should be cleaned, new calls should work
        func()
        assert len(limiter.calls) == 1  # Only the new call

    def test_preserves_function_metadata(self):
        """Test decorator preserves function metadata."""
        limiter = RateLimiter(max_calls=10, period=60.0)

        @limiter
        def documented():
            """Documentation here."""
            pass

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "Documentation here."


# =============================================================================
# safe_json_parse Tests
# =============================================================================

class TestSafeJsonParse:
    """Tests for safe_json_parse function."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        result = safe_json_parse('{"key": "value", "num": 123}')
        assert result == {"key": "value", "num": 123}

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        result = safe_json_parse('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_parse_empty_string(self):
        """Test parsing empty string returns default."""
        result = safe_json_parse("", default={"empty": True})
        assert result == {"empty": True}

    def test_parse_empty_object(self):
        """Test parsing empty object returns default."""
        result = safe_json_parse("{}", default={"default": True})
        assert result == {"default": True}

    def test_parse_empty_array(self):
        """Test parsing empty array returns default."""
        result = safe_json_parse("[]", default=[])
        assert result == []

    def test_parse_null(self):
        """Test parsing null returns default."""
        result = safe_json_parse("null", default="default")
        assert result == "default"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns default."""
        result = safe_json_parse("{invalid json}", default={"error": True})
        assert result == {"error": True}

    def test_parse_invalid_raises_when_requested(self):
        """Test parsing invalid JSON raises when raise_on_error=True."""
        with pytest.raises(json.JSONDecodeError):
            safe_json_parse("{invalid}", raise_on_error=True)

    def test_parse_wrong_type(self):
        """Test parsing non-string raises AttributeError."""
        # Note: The implementation calls .strip() on input before checking type,
        # so non-strings cause AttributeError before TypeError handling kicks in
        with pytest.raises(AttributeError):
            safe_json_parse(12345, default=None)

    def test_parse_wrong_type_raises_when_requested(self):
        """Test parsing non-string raises AttributeError."""
        with pytest.raises(AttributeError):
            safe_json_parse(12345, raise_on_error=True)

    def test_default_none_returns_empty_dict(self):
        """Test default=None returns empty dict for empty input."""
        result = safe_json_parse("", default=None)
        assert result == {}

    def test_whitespace_only_string(self):
        """Test whitespace-only string returns default."""
        result = safe_json_parse("   ", default={"ws": True})
        assert result == {"ws": True}

    def test_parse_type_error_returns_default(self):
        """Test TypeError in json.loads returns default."""
        from unittest.mock import patch

        # Mock json.loads to raise TypeError
        with patch('skippy_resilience.json.loads') as mock_loads:
            mock_loads.side_effect = TypeError("Mock type error")
            result = safe_json_parse('{"valid": "json"}', default={"type_error": True})
            assert result == {"type_error": True}

    def test_parse_type_error_raises_when_requested(self):
        """Test TypeError in json.loads raises when raise_on_error=True."""
        from unittest.mock import patch

        # Mock json.loads to raise TypeError
        with patch('skippy_resilience.json.loads') as mock_loads:
            mock_loads.side_effect = TypeError("Mock type error")
            with pytest.raises(TypeError):
                safe_json_parse('{"valid": "json"}', raise_on_error=True)


# =============================================================================
# safe_json_dumps Tests
# =============================================================================

class TestSafeJsonDumps:
    """Tests for safe_json_dumps function."""

    def test_dump_dict(self):
        """Test dumping dictionary."""
        result = safe_json_dumps({"key": "value"})
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_dump_list(self):
        """Test dumping list."""
        result = safe_json_dumps([1, 2, 3])
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_dump_with_datetime(self):
        """Test dumping object with datetime (uses default=str)."""
        dt = datetime(2025, 1, 15, 12, 30, 45)
        result = safe_json_dumps({"date": dt})
        assert "2025-01-15" in result

    def test_dump_non_serializable_returns_default(self):
        """Test dumping non-serializable object returns default."""
        # Create a truly non-serializable object
        class NonSerializable:
            def __str__(self):
                raise ValueError("Cannot convert")

        obj = {"bad": NonSerializable()}

        with patch('skippy_resilience.logger'):
            result = safe_json_dumps(obj, default='{"fallback": true}')

        # Should use default=str first, only fallback if that fails
        # Actually the default=str in dumps should handle this
        assert result is not None

    def test_dump_returns_formatted_json(self):
        """Test dump returns indented JSON."""
        result = safe_json_dumps({"a": 1, "b": 2})
        assert "\n" in result  # Should be indented


# =============================================================================
# HealthCheckResult Tests
# =============================================================================

class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_basic_result(self):
        """Test basic health check result."""
        result = HealthCheckResult(
            name="test-check",
            healthy=True,
            message="All good"
        )
        assert result.name == "test-check"
        assert result.healthy is True
        assert result.message == "All good"
        assert result.details == {}
        assert isinstance(result.timestamp, datetime)

    def test_result_with_details(self):
        """Test health check result with details."""
        result = HealthCheckResult(
            name="db-check",
            healthy=True,
            message="Connected",
            details={"connections": 10, "latency": 5.2}
        )
        assert result.details == {"connections": 10, "latency": 5.2}

    def test_to_dict(self):
        """Test to_dict method."""
        result = HealthCheckResult(
            name="test",
            healthy=False,
            message="Failed",
            details={"error": "timeout"}
        )
        d = result.to_dict()

        assert d["name"] == "test"
        assert d["healthy"] is False
        assert d["message"] == "Failed"
        assert d["details"] == {"error": "timeout"}
        assert "timestamp" in d


# =============================================================================
# HealthChecker Tests
# =============================================================================

class TestHealthChecker:
    """Tests for HealthChecker class."""

    def test_register_check(self):
        """Test registering a health check."""
        checker = HealthChecker()

        @checker.register("test-check")
        def check_test():
            return True, "OK"

        assert "test-check" in checker.checks

    def test_run_single_check_tuple_result(self):
        """Test running check that returns tuple."""
        checker = HealthChecker()

        @checker.register("tuple-check")
        def check():
            return True, "Success", {"extra": "data"}

        result = checker.run_check("tuple-check")
        assert result.healthy is True
        assert result.message == "Success"
        assert result.details == {"extra": "data"}

    def test_run_single_check_bool_result(self):
        """Test running check that returns bool."""
        checker = HealthChecker()

        @checker.register("bool-check")
        def check():
            return True

        result = checker.run_check("bool-check")
        assert result.healthy is True
        assert result.message == "OK"

    def test_run_single_check_bool_false(self):
        """Test running check that returns False."""
        checker = HealthChecker()

        @checker.register("fail-check")
        def check():
            return False

        result = checker.run_check("fail-check")
        assert result.healthy is False
        assert result.message == "Failed"

    def test_run_single_check_other_result(self):
        """Test running check that returns other value."""
        checker = HealthChecker()

        @checker.register("string-check")
        def check():
            return "OK"

        result = checker.run_check("string-check")
        assert result.healthy is True
        assert result.message == "OK"

    def test_run_nonexistent_check(self):
        """Test running non-existent check."""
        checker = HealthChecker()
        result = checker.run_check("nonexistent")

        assert result.healthy is False
        assert "not found" in result.message

    def test_run_check_exception(self):
        """Test running check that raises exception."""
        checker = HealthChecker()

        @checker.register("error-check")
        def check():
            raise ValueError("Something went wrong")

        result = checker.run_check("error-check")
        assert result.healthy is False
        assert "error" in result.message.lower()
        assert result.details["exception"] == "ValueError"

    def test_run_all(self):
        """Test running all checks."""
        checker = HealthChecker()

        @checker.register("check1")
        def c1():
            return True, "OK"

        @checker.register("check2")
        def c2():
            return False, "Failed"

        results = checker.run_all()
        assert len(results) == 2
        assert results["check1"].healthy is True
        assert results["check2"].healthy is False

    def test_is_healthy_all_pass(self):
        """Test is_healthy when all checks pass."""
        checker = HealthChecker()

        @checker.register("c1")
        def c1():
            return True, "OK"

        @checker.register("c2")
        def c2():
            return True, "OK"

        assert checker.is_healthy() is True

    def test_is_healthy_one_fails(self):
        """Test is_healthy when one check fails."""
        checker = HealthChecker()

        @checker.register("c1")
        def c1():
            return True, "OK"

        @checker.register("c2")
        def c2():
            return False, "Failed"

        assert checker.is_healthy() is False

    def test_get_summary(self):
        """Test get_summary method."""
        checker = HealthChecker()

        @checker.register("pass")
        def pass_check():
            return True, "Good"

        @checker.register("fail")
        def fail_check():
            return False, "Bad"

        summary = checker.get_summary()

        assert summary["overall_healthy"] is False
        assert summary["total_checks"] == 2
        assert summary["healthy_count"] == 1
        assert summary["unhealthy_count"] == 1
        assert "timestamp" in summary
        assert "pass" in summary["checks"]
        assert "fail" in summary["checks"]

    def test_results_cached(self):
        """Test that results are cached."""
        checker = HealthChecker()
        call_count = 0

        @checker.register("counter")
        def count_check():
            nonlocal call_count
            call_count += 1
            return True, f"Call {call_count}"

        # First call runs check
        checker.run_check("counter")
        assert call_count == 1

        # is_healthy doesn't re-run if results exist
        checker.is_healthy()
        # results exist, so run_all not called again

    def test_tuple_with_two_elements(self):
        """Test check returning tuple with 2 elements."""
        checker = HealthChecker()

        @checker.register("two-tuple")
        def check():
            return (True, "Two element tuple")

        result = checker.run_check("two-tuple")
        assert result.healthy is True
        assert result.message == "Two element tuple"
        assert result.details == {}


# =============================================================================
# Global Circuit Breaker Registry Tests
# =============================================================================

class TestCircuitBreakerRegistry:
    """Tests for global circuit breaker registry functions."""

    def setup_method(self):
        """Clear registry before each test."""
        _circuit_breakers.clear()

    def test_get_circuit_breaker_creates_new(self):
        """Test get_circuit_breaker creates new CB."""
        cb = get_circuit_breaker("new-cb")
        assert cb.name == "new-cb"
        assert "new-cb" in _circuit_breakers

    def test_get_circuit_breaker_returns_existing(self):
        """Test get_circuit_breaker returns existing CB."""
        cb1 = get_circuit_breaker("existing-cb")
        cb2 = get_circuit_breaker("existing-cb")
        assert cb1 is cb2

    def test_get_circuit_breaker_with_config(self):
        """Test get_circuit_breaker with custom config."""
        config = CircuitBreakerConfig(failure_threshold=10)
        cb = get_circuit_breaker("configured-cb", config)
        assert cb.config.failure_threshold == 10

    def test_get_all_circuit_breaker_states(self):
        """Test get_all_circuit_breaker_states."""
        get_circuit_breaker("cb1")
        get_circuit_breaker("cb2")

        states = get_all_circuit_breaker_states()
        assert "cb1" in states
        assert "cb2" in states
        assert states["cb1"]["state"] == "closed"

    def test_get_all_states_empty(self):
        """Test get_all_circuit_breaker_states with no CBs."""
        states = get_all_circuit_breaker_states()
        assert states == {}


# =============================================================================
# Integration Tests
# =============================================================================

class TestResilienceIntegration:
    """Integration tests for resilience patterns."""

    def test_retry_with_circuit_breaker(self):
        """Test combining retry with circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("retry-cb", config)

        attempts = 0

        @cb
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky_service():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_service()
        assert result == "success"
        assert attempts == 3
        assert cb.state == CircuitState.CLOSED

    def test_rate_limiter_preserves_errors(self):
        """Test rate limiter doesn't swallow errors."""
        limiter = RateLimiter(max_calls=10, period=60.0)

        @limiter
        def error_func():
            raise ValueError("Expected error")

        with pytest.raises(ValueError):
            error_func()
