#!/usr/bin/env python3
"""
Skippy System Manager - Resilience and Retry Library
Version: 1.0.0
Author: Skippy Development Team
Created: 2025-11-16

Provides network retry logic, circuit breaker patterns, and fault tolerance.

Features:
- Exponential backoff retry decorator
- Circuit breaker pattern for external services
- Rate limiting
- Timeout handling
- Health monitoring
"""

import time
import functools
import logging
import json
from typing import Callable, Optional, Any, Dict, List, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# RETRY DECORATOR WITH EXPONENTIAL BACKOFF
# =============================================================================

class RetryError(Exception):
    """Raised when all retry attempts have been exhausted."""
    def __init__(self, message: str, attempts: int, last_exception: Optional[Exception] = None):
        self.message = message
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(message)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay between retries (default 60.0)
        exponential_base: Base for exponential calculation (default 2.0)
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry (exception, attempt_number)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_attempts=3, base_delay=2.0)
        def fetch_data():
            return requests.get('https://api.example.com/data')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise RetryError(
                            f"Max retry attempts ({max_attempts}) exceeded for {func.__name__}",
                            attempts=attempt,
                            last_exception=e
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise RetryError(
                f"Unexpected retry loop exit for {func.__name__}",
                attempts=max_attempts,
                last_exception=last_exception
            )

        return wrapper
    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Async version of retry_with_backoff decorator.

    Example:
        @async_retry_with_backoff(max_attempts=3)
        async def fetch_data():
            async with httpx.AsyncClient() as client:
                return await client.get('https://api.example.com/data')
    """
    import asyncio

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise RetryError(
                            f"Max retry attempts ({max_attempts}) exceeded for {func.__name__}",
                            attempts=attempt,
                            last_exception=e
                        ) from e

                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(delay)

            raise RetryError(
                f"Unexpected retry loop exit for {func.__name__}",
                attempts=max_attempts,
                last_exception=last_exception
            )

        return wrapper
    return decorator


# =============================================================================
# CIRCUIT BREAKER PATTERN
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation, requests pass through
    OPEN = "open"           # Circuit is tripped, requests fail immediately
    HALF_OPEN = "half_open" # Testing if service is recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5           # Number of failures before opening circuit
    success_threshold: int = 3           # Number of successes to close circuit
    timeout: float = 60.0                 # Time in seconds before attempting half-open
    half_open_max_calls: int = 1          # Max concurrent calls in half-open state
    excluded_exceptions: tuple = ()       # Exceptions that don't count as failures


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.

    States:
    - CLOSED: Normal operation, failures are counted
    - OPEN: Service is considered down, fail fast
    - HALF_OPEN: Testing if service has recovered

    Example:
        cb = CircuitBreaker("payment-api")

        @cb
        def process_payment():
            return payment_api.charge(amount)
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the circuit (for logging/monitoring)
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()

        logger.info(f"Circuit breaker '{name}' initialized in CLOSED state")

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._call(func, *args, **kwargs)
        return wrapper

    def _call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker logic."""
        with self._lock:
            if not self._can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
                )

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.excluded_exceptions:
            # Don't count excluded exceptions as failures
            raise
        except Exception as e:
            self._on_failure()
            raise

    def _can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.timeout:
                    self._transition_to_half_open()
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls

        return False

    def _on_success(self):
        """Handle successful execution."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            else:
                self.failure_count = 0

    def _on_failure(self):
        """Handle failed execution."""
        with self._lock:
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            else:
                self.failure_count += 1
                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.half_open_calls = 0
        logger.warning(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to OPEN "
            f"(failures: {self.failure_count})"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.half_open_calls = 0
        logger.info(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to HALF_OPEN"
        )

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        logger.info(
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to CLOSED"
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }
        }

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._transition_to_closed()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Example:
        limiter = RateLimiter(max_calls=10, period=60.0)  # 10 calls per minute

        @limiter
        def api_call():
            return requests.get('https://api.example.com/data')
    """

    def __init__(self, max_calls: int, period: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: deque = deque()
        self._lock = threading.Lock()

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with rate limiting."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._wait_if_needed()
            return func(*args, **kwargs)
        return wrapper

    def _wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self._lock:
            now = time.time()

            # Remove old calls outside the period window
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                sleep_time = self.calls[0] - (now - self.period)
                if sleep_time > 0:
                    logger.info(f"Rate limit reached. Waiting {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    # Recurse to re-check
                    self._wait_if_needed()
                    return

            self.calls.append(now)

    def get_remaining_calls(self) -> int:
        """Get number of remaining calls in current period."""
        with self._lock:
            now = time.time()
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            return max(0, self.max_calls - len(self.calls))


# =============================================================================
# SAFE JSON PARSING
# =============================================================================

def safe_json_parse(
    json_string: str,
    default: Any = None,
    raise_on_error: bool = False
) -> Any:
    """
    Safely parse JSON string with error handling.

    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        raise_on_error: If True, raise exception on error

    Returns:
        Parsed JSON or default value

    Example:
        data = safe_json_parse('{"key": "value"}', default={})
        headers = safe_json_parse(headers_str, default={})
    """
    if not json_string or json_string.strip() in ("", "{}", "[]", "null"):
        return default if default is not None else {}

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed: {e}. Input: {json_string[:100]}...")
        if raise_on_error:
            raise
        return default
    except TypeError as e:
        logger.warning(f"JSON parsing type error: {e}. Input type: {type(json_string)}")
        if raise_on_error:
            raise
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON string.

    Args:
        obj: Object to serialize
        default: Default string if serialization fails

    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"JSON serialization failed: {e}")
        return default


# =============================================================================
# HEALTH CHECK INFRASTRUCTURE
# =============================================================================

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    healthy: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class HealthChecker:
    """
    Health check coordinator for monitoring service dependencies.

    Example:
        checker = HealthChecker()

        @checker.register("database")
        def check_database():
            db.ping()
            return True, "Database connection OK"

        @checker.register("api")
        def check_api():
            response = requests.get('https://api.example.com/health')
            return response.ok, f"API status: {response.status_code}"

        results = checker.run_all()
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, HealthCheckResult] = {}

    def register(self, name: str):
        """
        Decorator to register a health check function.

        The function should return (bool, str) or just bool.
        """
        def decorator(func: Callable):
            self.checks[name] = func
            return func
        return decorator

    def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check by name."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Health check '{name}' not found"
            )

        try:
            result = self.checks[name]()

            if isinstance(result, tuple):
                healthy, message = result[0], result[1]
                details = result[2] if len(result) > 2 else {}
            elif isinstance(result, bool):
                healthy = result
                message = "OK" if result else "Failed"
                details = {}
            else:
                healthy = bool(result)
                message = str(result)
                details = {}

            check_result = HealthCheckResult(
                name=name,
                healthy=healthy,
                message=message,
                details=details
            )
        except Exception as e:
            check_result = HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Health check error: {str(e)}",
                details={"exception": type(e).__name__}
            )

        self.results[name] = check_result
        return check_result

    def run_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results

    def is_healthy(self) -> bool:
        """Check if all services are healthy."""
        if not self.results:
            self.run_all()
        return all(r.healthy for r in self.results.values())

    def get_summary(self) -> Dict[str, Any]:
        """Get health check summary."""
        if not self.results:
            self.run_all()

        return {
            "overall_healthy": self.is_healthy(),
            "total_checks": len(self.checks),
            "healthy_count": sum(1 for r in self.results.values() if r.healthy),
            "unhealthy_count": sum(1 for r in self.results.values() if not r.healthy),
            "checks": {name: result.to_dict() for name, result in self.results.items()},
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# GLOBAL CIRCUIT BREAKER REGISTRY
# =============================================================================

_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def get_all_circuit_breaker_states() -> Dict[str, Any]:
    """Get states of all circuit breakers."""
    return {
        name: cb.get_state() for name, cb in _circuit_breakers.items()
    }


# =============================================================================
# EXAMPLE USAGE AND TESTS
# =============================================================================

if __name__ == "__main__":
    import asyncio

    print("=" * 60)
    print("Skippy Resilience Library - Examples")
    print("=" * 60)

    # Example 1: Retry with backoff
    print("\n1. Retry with Exponential Backoff:")
    attempt_count = 0

    @retry_with_backoff(max_attempts=3, base_delay=0.1, retryable_exceptions=(ValueError,))
    def flaky_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")
        return "Success!"

    try:
        result = flaky_function()
        print(f"   Result: {result} (after {attempt_count} attempts)")
    except RetryError as e:
        print(f"   Failed: {e}")

    # Example 2: Circuit Breaker
    print("\n2. Circuit Breaker Pattern:")
    cb = CircuitBreaker("test-service", CircuitBreakerConfig(failure_threshold=2, timeout=1))

    @cb
    def unreliable_service():
        raise ConnectionError("Service unavailable")

    for i in range(4):
        try:
            unreliable_service()
        except CircuitBreakerOpenError as e:
            print(f"   Call {i+1}: Circuit OPEN - {e}")
        except ConnectionError:
            print(f"   Call {i+1}: Service error (circuit: {cb.state.value})")

    print(f"   Circuit state: {cb.get_state()}")

    # Example 3: Safe JSON parsing
    print("\n3. Safe JSON Parsing:")
    valid_json = '{"name": "test", "value": 123}'
    invalid_json = '{invalid json}'
    empty_json = '{}'

    print(f"   Valid JSON: {safe_json_parse(valid_json)}")
    print(f"   Invalid JSON: {safe_json_parse(invalid_json, default={'error': 'parse failed'})}")
    print(f"   Empty JSON: {safe_json_parse(empty_json)}")

    # Example 4: Rate Limiter
    print("\n4. Rate Limiter:")
    limiter = RateLimiter(max_calls=3, period=1.0)

    @limiter
    def limited_api_call():
        return "API response"

    print(f"   Remaining calls: {limiter.get_remaining_calls()}")
    for i in range(3):
        result = limited_api_call()
        print(f"   Call {i+1}: {result} (remaining: {limiter.get_remaining_calls()})")

    # Example 5: Health Checker
    print("\n5. Health Checker:")
    checker = HealthChecker()

    @checker.register("database")
    def check_db():
        return True, "Database OK", {"connections": 10}

    @checker.register("cache")
    def check_cache():
        return False, "Cache unavailable"

    @checker.register("api")
    def check_api():
        return True, "API responding"

    summary = checker.get_summary()
    print(f"   Overall healthy: {summary['overall_healthy']}")
    print(f"   Healthy: {summary['healthy_count']}/{summary['total_checks']}")
    for name, result in summary['checks'].items():
        status = "✓" if result['healthy'] else "✗"
        print(f"   {status} {name}: {result['message']}")

    print("\n" + "=" * 60)
    print("Examples completed successfully!")
