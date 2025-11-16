# Skippy System Manager - Resilience Architecture

## Overview

Version 2.5.0 introduces comprehensive resilience infrastructure to handle failures gracefully, prevent cascading issues, and provide observability into system behavior. This document details the architecture and usage of these features.

## Core Components

### 1. Circuit Breaker Pattern

**Location:** `lib/python/skippy_resilience.py`

Prevents repeated calls to failing services, allowing them time to recover.

```python
from skippy_resilience import CircuitBreaker, CircuitBreakerConfig

# Create circuit breaker
cb = CircuitBreaker(CircuitBreakerConfig(
    failure_threshold=5,    # Open after 5 failures
    success_threshold=3,    # Close after 3 successes
    timeout=120.0          # Try again after 120s
))

# States:
# - CLOSED: Normal operation, requests pass through
# - OPEN: Service failing, fail fast without calling
# - HALF_OPEN: Testing if service recovered
```

**Protected Services:**
- Google Drive API (60 req/min)
- Google Photos API (30 req/min)
- GitHub API (30 req/min)
- Pexels API (200 req/hour)
- HTTP Client (100 req/min)

### 2. Retry with Exponential Backoff

**Location:** `lib/python/skippy_resilience.py`

Automatically retries failed operations with increasing delays.

```python
from skippy_resilience import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)
def unstable_operation():
    # This will retry on ConnectionError or TimeoutError
    pass
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After 1s delay
- Attempt 3: After 2s delay
- Attempt 4: After 4s delay (exponential)

### 3. Rate Limiting

**Location:** `lib/python/skippy_resilience.py`

Token bucket algorithm prevents API quota exhaustion.

```python
from skippy_resilience import RateLimiter

limiter = RateLimiter(max_calls=60, period=60.0)  # 60 calls per minute

# Check before making calls
if limiter.acquire():
    make_api_call()
else:
    # Wait or handle rate limit
    pass
```

### 4. Request Tracing

**Location:** `lib/python/skippy_resilience_advanced.py`

Correlates requests across the system with unique IDs for debugging.

```python
from skippy_resilience_advanced import get_tracer

tracer = get_tracer()
trace = tracer.start_trace("Google Drive", "search_files")

try:
    result = perform_operation()
    tracer.end_trace(trace, success=True)
except Exception as e:
    tracer.end_trace(trace, success=False, error=str(e))
```

**Trace Data:**
- Request ID (unique per request)
- Service name and operation
- Start/end timestamps
- Duration in milliseconds
- Success/failure status
- Error messages
- Attempt count (for retries)

### 5. Graceful Cache

**Location:** `lib/python/skippy_resilience_advanced.py`

Returns stale cached data when services are unavailable.

```python
from skippy_resilience_advanced import get_cache

cache = get_cache()

# Store with TTL
cache.set("gdrive_files", files_list, ttl=3600)

# Normal fetch (only returns valid data)
data = cache.get("gdrive_files")

# Fallback fetch (returns stale data if service down)
data = cache.get("gdrive_files", allow_stale=True)
```

**Features:**
- Time-to-live (TTL) expiration
- Maximum cache size with LRU eviction
- Stale-while-revalidate pattern
- Automatic cleanup

### 6. Alert Manager

**Location:** `lib/python/skippy_resilience_advanced.py`

Centralized notification system for resilience events.

```python
from skippy_resilience_advanced import get_alert_manager, AlertLevel

manager = get_alert_manager()

# Add file handler
manager.add_handler("file", file_alert_handler)

# Send alert
manager.alert(
    AlertLevel.ERROR,
    "Service Failure",
    "Google Drive API failed after 3 retries",
    service="google-drive",
    attempts=3
)
```

**Alert Levels:**
- DEBUG: Detailed information for debugging
- INFO: Normal operation events
- WARNING: Potential issues requiring attention
- ERROR: Operation failures
- CRITICAL: System-level failures

### 7. Metrics Persistence

**Location:** `lib/python/skippy_resilience_advanced.py`

Saves operational metrics to disk for analysis.

```python
from skippy_resilience_advanced import init_metrics_persistence

persistence = init_metrics_persistence()

# Metrics saved to: {SKIPPY_PATH}/metrics/
# Files: performance.jsonl, resilience.jsonl, etc.
```

**Recorded Metrics:**
- Request traces (request ID, duration, success)
- Circuit breaker state changes
- Rate limiter statistics
- Cache hit/miss ratios
- Alert history

## Integration with MCP Tools

### Google Drive Functions (16 total)

All Google Drive operations now include:
- Circuit breaker protection
- Rate limiting (60 req/min)
- Automatic retry (3 attempts)
- Request tracing
- Graceful cache fallback for read operations

```python
@mcp.tool()
def gdrive_search_files(query: str, max_results: int = 10) -> str:
    """Features: retry logic, circuit breaker, rate limiting, caching"""

    def _search():
        return service.files().list(...).execute()

    # Apply all resilience patterns
    results = resilient_api_call(
        _search,
        circuit_breaker=_google_drive_cb,
        rate_limiter=_google_drive_limiter,
        service_name="Google Drive",
        operation_name="search_files",
        cache_key=f"gdrive_search_{query}"  # Enable caching
    )
```

### HTTP Operations

HTTP GET/POST now include:
- Circuit breaker (10 failures threshold)
- Rate limiting (100 req/min)
- Async retry with exponential backoff
- Request tracing

### Health Monitoring

New MCP tools for system observability:

- `system_health_check()` - Overall system health status
- `get_system_metrics()` - Performance and resilience metrics
- `validate_skippy_configuration()` - Configuration validation
- `get_circuit_breaker_status()` - Circuit breaker states
- `get_resilience_dashboard()` - Comprehensive resilience view
- `reset_circuit_breaker(service_name)` - Manual circuit reset

## Configuration

### Environment Variables

```bash
SKIPPY_PATH=/home/dave/skippy          # Base path for logs/metrics
SKIPPY_RETRY_MAX_ATTEMPTS=3            # Default retry count
SKIPPY_RETRY_BASE_DELAY=1.0            # Base retry delay
SKIPPY_CIRCUIT_BREAKER_TIMEOUT=120     # CB timeout in seconds
```

### Configuration Validation

```python
from skippy_config import load_configuration, ConfigValidator

config = load_configuration()
validator = ConfigValidator()
is_valid, errors = validator.validate(config)
```

## Bash Script Robustness

### Template Features

**Location:** `lib/bash/robust_template.sh`

```bash
# Strict mode
set -euo pipefail

# Lock file support (single instance)
acquire_lock

# Retry logic
retry some_command --with-args

# Graceful cleanup
trap cleanup EXIT
```

### Available Scripts

- `scripts/utility/health_check.sh` - System health monitoring
- `scripts/backup/robust_backup.sh` - Resilient backup operations

## Error Handling Hierarchy

1. **Input Validation**
   - JSON parsing with safe_json_parse()
   - Path validation with validate_path()
   - URL validation with validate_url()

2. **Rate Limiting**
   - Prevents API quota exhaustion
   - Automatic waiting when limits reached

3. **Circuit Breaker Check**
   - Fast-fail if service known to be down
   - Falls back to cached data if available

4. **Retry with Backoff**
   - Retries transient failures
   - Exponential delay between attempts

5. **Alerting**
   - Notifications on repeated failures
   - File-based alert logging

6. **Graceful Degradation**
   - Returns stale cache on complete failure
   - Provides informative error messages

## Monitoring and Debugging

### Log Files

- `{SKIPPY_PATH}/logs/alerts.jsonl` - Alert history
- `{SKIPPY_PATH}/logs/health_check.log` - Health check results
- `{SKIPPY_PATH}/metrics/*.jsonl` - Performance metrics

### Request Tracing

Each request gets a unique ID:
```
Request-ID: req_20251116_143025_abc123
```

Use this ID to trace requests across logs and metrics.

### Dashboard View

```python
# Get comprehensive resilience status
dashboard = get_resilience_dashboard()
# Returns: circuit breakers, rate limiters, cache stats, recent alerts
```

## Testing

Comprehensive test suite in `tests/test_resilience.py`:

- Circuit breaker state transitions
- Retry logic with backoff
- Rate limiter behavior
- Safe JSON parsing
- Health check functionality
- Configuration validation

## Best Practices

1. **Always use resilient_api_call()** for external API calls
2. **Set appropriate thresholds** for circuit breakers
3. **Enable caching** for read operations
4. **Monitor alert logs** for service issues
5. **Review metrics** periodically for performance trends
6. **Test recovery** by simulating failures
7. **Use request IDs** when investigating issues

## Future Enhancements

- Distributed tracing across services
- Prometheus/Grafana metrics export
- Slack/email alert notifications
- Automatic circuit breaker tuning
- Load shedding under high pressure
- Bulkhead pattern for isolation

## Version History

- **v2.5.0** (2025-11-16): Initial resilience infrastructure
  - Circuit breaker pattern
  - Retry with exponential backoff
  - Rate limiting
  - Request tracing
  - Graceful caching
  - Alert management
  - Metrics persistence
  - All Google Drive functions protected (16 functions)
  - HTTP GET/POST with resilience
  - Bash script robustness templates
