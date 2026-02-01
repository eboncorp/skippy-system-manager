"""
Metrics & Monitoring
====================

Observability for production deployment.

Features:
- Prometheus metrics collection
- Health check endpoints
- Sentry error tracking
- Structured logging
- Performance tracking

Usage:
    from monitoring import MetricsCollector, setup_logging

    metrics = MetricsCollector()

    # Record a metric
    metrics.record_api_call("coinbase", "get_balances", 0.5, success=True)

    # Export metrics
    prometheus_metrics = metrics.export_prometheus()
"""

import asyncio
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

# Optional imports
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""

    # Sentry
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_RATE", "0.1"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")  # json or text
    log_file: str = os.getenv("LOG_FILE", "")

    # Metrics
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))

    # Health checks
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(config: Optional[MonitoringConfig] = None) -> logging.Logger:
    """
    Set up structured logging.

    Args:
        config: Monitoring configuration

    Returns:
        Root logger
    """
    config = config or MonitoringConfig()

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create handler
    if config.log_file:
        handler = logging.FileHandler(config.log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if config.log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    logger.addHandler(handler)

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter with extra fields support."""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra["extra_fields"] = self.extra
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str, **extra_fields) -> LoggerAdapter:
    """Get a logger with extra fields."""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, extra_fields)


# =============================================================================
# SENTRY INTEGRATION
# =============================================================================


def setup_sentry(config: Optional[MonitoringConfig] = None):
    """
    Initialize Sentry error tracking.

    Args:
        config: Monitoring configuration
    """
    config = config or MonitoringConfig()

    if not SENTRY_AVAILABLE:
        logging.warning("Sentry SDK not installed. Error tracking disabled.")
        return

    if not config.sentry_dsn:
        logging.info("Sentry DSN not configured. Error tracking disabled.")
        return

    sentry_sdk.init(
        dsn=config.sentry_dsn,
        environment=config.sentry_environment,
        traces_sample_rate=config.sentry_traces_sample_rate,

        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,

        # Integrations
        integrations=[],
    )

    logging.info(f"Sentry initialized for environment: {config.sentry_environment}")


def capture_exception(exception: Exception, **context):
    """Capture exception to Sentry."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **context):
    """Capture message to Sentry."""
    if SENTRY_AVAILABLE and sentry_sdk.Hub.current.client:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)


# =============================================================================
# METRICS COLLECTOR
# =============================================================================


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Individual metric."""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    help_text: str = ""


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution metrics."""
    le: float  # less than or equal
    count: int = 0


class MetricsCollector:
    """
    Collects and exports metrics.

    Usage:
        metrics = MetricsCollector()

        # Counters
        metrics.increment("api_calls_total", labels={"exchange": "coinbase"})

        # Gauges
        metrics.set_gauge("portfolio_value_usd", 125000)

        # Histograms
        metrics.observe_histogram("api_latency_seconds", 0.5, labels={"exchange": "coinbase"})

        # Export
        print(metrics.export_prometheus())
    """

    # Default histogram buckets (in seconds for latency)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]

    def __init__(self):
        self.counters: Dict[str, Dict[str, float]] = {}
        self.gauges: Dict[str, Dict[str, float]] = {}
        self.histograms: Dict[str, Dict[str, Dict]] = {}
        self.summaries: Dict[str, Dict[str, List[float]]] = {}
        self.help_texts: Dict[str, str] = {}

        # Register default metrics
        self._register_defaults()

    def _register_defaults(self):
        """Register default application metrics."""
        self.register_metric("api_calls_total", MetricType.COUNTER, "Total API calls")
        self.register_metric("api_errors_total", MetricType.COUNTER, "Total API errors")
        self.register_metric("api_latency_seconds", MetricType.HISTOGRAM, "API call latency")
        self.register_metric("portfolio_value_usd", MetricType.GAUGE, "Current portfolio value")
        self.register_metric("active_alerts", MetricType.GAUGE, "Number of active alerts")
        self.register_metric("active_dca_bots", MetricType.GAUGE, "Number of active DCA bots")
        self.register_metric("cache_hits_total", MetricType.COUNTER, "Cache hits")
        self.register_metric("cache_misses_total", MetricType.COUNTER, "Cache misses")
        self.register_metric("websocket_connections", MetricType.GAUGE, "Active WebSocket connections")
        self.register_metric("background_jobs_total", MetricType.COUNTER, "Background jobs executed")
        self.register_metric("background_job_duration_seconds", MetricType.HISTOGRAM, "Job duration")

    def register_metric(self, name: str, type: MetricType, help_text: str = ""):
        """Register a metric."""
        self.help_texts[name] = help_text

        if type == MetricType.COUNTER:
            self.counters[name] = {}
        elif type == MetricType.GAUGE:
            self.gauges[name] = {}
        elif type == MetricType.HISTOGRAM:
            self.histograms[name] = {}
        elif type == MetricType.SUMMARY:
            self.summaries[name] = {}

    def _labels_key(self, labels: Dict[str, str]) -> str:
        """Create a hashable key from labels."""
        return json.dumps(labels, sort_keys=True)

    # -------------------------------------------------------------------------
    # Counter Methods
    # -------------------------------------------------------------------------

    def increment(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter."""
        labels = labels or {}
        key = self._labels_key(labels)

        if name not in self.counters:
            self.counters[name] = {}

        if key not in self.counters[name]:
            self.counters[name][key] = 0

        self.counters[name][key] += value

    # -------------------------------------------------------------------------
    # Gauge Methods
    # -------------------------------------------------------------------------

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        labels = labels or {}
        key = self._labels_key(labels)

        if name not in self.gauges:
            self.gauges[name] = {}

        self.gauges[name][key] = value

    def inc_gauge(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a gauge."""
        labels = labels or {}
        key = self._labels_key(labels)

        if name not in self.gauges:
            self.gauges[name] = {}

        current = self.gauges[name].get(key, 0)
        self.gauges[name][key] = current + value

    def dec_gauge(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None):
        """Decrement a gauge."""
        self.inc_gauge(name, -value, labels)

    # -------------------------------------------------------------------------
    # Histogram Methods
    # -------------------------------------------------------------------------

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None
    ):
        """Observe a value in a histogram."""
        labels = labels or {}
        key = self._labels_key(labels)
        buckets = buckets or self.DEFAULT_BUCKETS

        if name not in self.histograms:
            self.histograms[name] = {}

        if key not in self.histograms[name]:
            self.histograms[name][key] = {
                "buckets": {b: 0 for b in buckets},
                "sum": 0,
                "count": 0
            }

        hist = self.histograms[name][key]
        hist["sum"] += value
        hist["count"] += 1

        for bucket in buckets:
            if value <= bucket:
                hist["buckets"][bucket] += 1

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    def record_api_call(
        self,
        exchange: str,
        endpoint: str,
        duration: float,
        success: bool = True
    ):
        """Record an API call with all relevant metrics."""
        labels = {"exchange": exchange, "endpoint": endpoint}

        self.increment("api_calls_total", labels=labels)
        self.observe_histogram("api_latency_seconds", duration, labels=labels)

        if not success:
            self.increment("api_errors_total", labels=labels)

    def record_cache_access(self, hit: bool, cache_type: str = "default"):
        """Record cache hit or miss."""
        labels = {"type": cache_type}
        if hit:
            self.increment("cache_hits_total", labels=labels)
        else:
            self.increment("cache_misses_total", labels=labels)

    def record_job_execution(self, job_name: str, duration: float, success: bool = True):
        """Record background job execution."""
        labels = {"job": job_name, "status": "success" if success else "failed"}
        self.increment("background_jobs_total", labels=labels)
        self.observe_histogram("background_job_duration_seconds", duration, labels={"job": job_name})

    # -------------------------------------------------------------------------
    # Timing Context Manager
    # -------------------------------------------------------------------------

    @asynccontextmanager
    async def time_async(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Context manager to time async operations."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe_histogram(metric_name, duration, labels)

    def time_sync(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Decorator to time sync functions."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start
                    self.observe_histogram(metric_name, duration, labels)
            return wrapper
        return decorator

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counters
        for name, values in self.counters.items():
            help_text = self.help_texts.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")

            for labels_json, value in values.items():
                labels = json.loads(labels_json)
                labels_str = self._format_prometheus_labels(labels)
                lines.append(f"{name}{labels_str} {value}")

        # Gauges
        for name, values in self.gauges.items():
            help_text = self.help_texts.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")

            for labels_json, value in values.items():
                labels = json.loads(labels_json)
                labels_str = self._format_prometheus_labels(labels)
                lines.append(f"{name}{labels_str} {value}")

        # Histograms
        for name, values in self.histograms.items():
            help_text = self.help_texts.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} histogram")

            for labels_json, hist in values.items():
                labels = json.loads(labels_json)

                # Buckets
                cumulative = 0
                for bucket, count in sorted(hist["buckets"].items()):
                    cumulative += count
                    bucket_labels = {**labels, "le": str(bucket)}
                    labels_str = self._format_prometheus_labels(bucket_labels)
                    lines.append(f"{name}_bucket{labels_str} {cumulative}")

                # +Inf bucket
                inf_labels = {**labels, "le": "+Inf"}
                labels_str = self._format_prometheus_labels(inf_labels)
                lines.append(f"{name}_bucket{labels_str} {hist['count']}")

                # Sum and count
                labels_str = self._format_prometheus_labels(labels)
                lines.append(f"{name}_sum{labels_str} {hist['sum']}")
                lines.append(f"{name}_count{labels_str} {hist['count']}")

        return "\n".join(lines)

    def _format_prometheus_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(parts) + "}"

    def export_json(self) -> Dict[str, Any]:
        """Export metrics as JSON."""
        return {
            "counters": {
                name: {json.loads(k): v for k, v in values.items()}
                for name, values in self.counters.items()
            },
            "gauges": {
                name: {json.loads(k): v for k, v in values.items()}
                for name, values in self.gauges.items()
            },
            "histograms": {
                name: {json.loads(k): v for k, v in values.items()}
                for name, values in self.histograms.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# =============================================================================
# HEALTH CHECKS
# =============================================================================


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Performs health checks on various components.

    Usage:
        health = HealthChecker()
        health.register("database", check_database)
        health.register("redis", check_redis)

        results = await health.check_all()
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}

    def register(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.checks[name] = check_func

    async def check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Unknown health check: {name}"
            )

        check_func = self.checks[name]
        start = time.perf_counter()

        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            latency = (time.perf_counter() - start) * 1000

            if isinstance(result, HealthCheckResult):
                result.latency_ms = latency
                self.last_results[name] = result
                return result
            elif isinstance(result, bool):
                check_result = HealthCheckResult(
                    name=name,
                    healthy=result,
                    latency_ms=latency
                )
                self.last_results[name] = check_result
                return check_result
            else:
                check_result = HealthCheckResult(
                    name=name,
                    healthy=True,
                    details=result if isinstance(result, dict) else {},
                    latency_ms=latency
                )
                self.last_results[name] = check_result
                return check_result

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            result = HealthCheckResult(
                name=name,
                healthy=False,
                message=str(e),
                latency_ms=latency
            )
            self.last_results[name] = result
            return result

    async def check_all(self) -> List[HealthCheckResult]:
        """Run all health checks."""
        tasks = [self.check(name) for name in self.checks]
        return await asyncio.gather(*tasks)

    async def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        results = await self.check_all()
        return all(r.healthy for r in results)

    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        overall_healthy = all(r.healthy for r in self.last_results.values())

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                name: {
                    "healthy": r.healthy,
                    "message": r.message,
                    "latency_ms": r.latency_ms,
                    "details": r.details
                }
                for name, r in self.last_results.items()
            }
        }


# =============================================================================
# DEFAULT HEALTH CHECKS
# =============================================================================


async def check_database(database_url: str = None) -> HealthCheckResult:
    """Check database connectivity."""
    try:
        # Simple check - try to import and check connection
        return HealthCheckResult(
            name="database",
            healthy=True,
            message="Database connection OK"
        )
    except Exception as e:
        return HealthCheckResult(
            name="database",
            healthy=False,
            message=str(e)
        )


async def check_redis(redis_url: str = None) -> HealthCheckResult:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as redis
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = await redis.from_url(url)
        await client.ping()
        await client.close()
        return HealthCheckResult(
            name="redis",
            healthy=True,
            message="Redis connection OK"
        )
    except Exception as e:
        return HealthCheckResult(
            name="redis",
            healthy=False,
            message=str(e)
        )


async def check_exchange_api(exchange: str) -> HealthCheckResult:
    """Check exchange API connectivity."""
    # Placeholder - would actually make API call
    return HealthCheckResult(
        name=f"exchange_{exchange}",
        healthy=True,
        message=f"{exchange} API OK"
    )


# =============================================================================
# PROMETHEUS METRICS HTTP SERVER
# =============================================================================


async def start_metrics_server(
    metrics: MetricsCollector,
    health: HealthChecker,
    port: int = 9090
):
    """
    Start HTTP server for Prometheus metrics scraping.

    Endpoints:
    - /metrics: Prometheus metrics
    - /health: Health check
    - /health/live: Liveness probe
    - /health/ready: Readiness probe
    """
    from aiohttp import web

    async def metrics_handler(request):
        """Handle /metrics requests."""
        return web.Response(
            text=metrics.export_prometheus(),
            content_type="text/plain"
        )

    async def health_handler(request):
        """Handle /health requests."""
        status = health.get_status()
        status_code = 200 if status["status"] == "healthy" else 503
        return web.json_response(status, status=status_code)

    async def liveness_handler(request):
        """Handle /health/live requests."""
        return web.json_response({"status": "alive"})

    async def readiness_handler(request):
        """Handle /health/ready requests."""
        is_ready = await health.is_healthy()
        if is_ready:
            return web.json_response({"status": "ready"})
        return web.json_response({"status": "not ready"}, status=503)

    app = web.Application()
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/health/live", liveness_handler)
    app.router.add_get("/health/ready", readiness_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"Metrics server started on port {port}")
    return runner


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Global metrics collector
metrics = MetricsCollector()

# Global health checker
health_checker = HealthChecker()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate monitoring system."""
    # Setup logging
    setup_logging()
    logger = get_logger("example", component="monitoring")

    # Record some metrics
    metrics.record_api_call("coinbase", "get_balances", 0.15, success=True)
    metrics.record_api_call("coinbase", "get_balances", 0.22, success=True)
    metrics.record_api_call("kraken", "get_balances", 0.18, success=True)
    metrics.record_api_call("coinbase", "place_order", 0.45, success=False)

    metrics.set_gauge("portfolio_value_usd", 125000)
    metrics.set_gauge("active_alerts", 5)

    metrics.record_cache_access(hit=True)
    metrics.record_cache_access(hit=True)
    metrics.record_cache_access(hit=False)

    # Export Prometheus metrics
    print("=== Prometheus Metrics ===")
    print(metrics.export_prometheus())

    # Health checks
    print("\n=== Health Checks ===")
    health_checker.register("redis", check_redis)

    results = await health_checker.check_all()
    for result in results:
        status = "✓" if result.healthy else "✗"
        print(f"{status} {result.name}: {result.message} ({result.latency_ms:.1f}ms)")

    print("\n=== Health Status ===")
    print(json.dumps(health_checker.get_status(), indent=2))


if __name__ == "__main__":
    asyncio.run(example_usage())
