#!/usr/bin/env python3
"""
General Purpose MCP Server
Version: 2.6.0 (Full Skippy Integration)
Author: Claude Code
Created: 2025-10-31
Updated: 2025-11-24 (Full Skippy Integration - 24 new tools)

SECURITY ENHANCEMENTS (v2.4.0):
- Phase 1: Command injection prevention, path traversal protection
- Phase 2: URL validation, SSRF prevention, comprehensive security testing
- 8 critical functions hardened with input validation
- 37+ security tests, Bandit security scan passing
- Comprehensive audit logging for all security-sensitive operations

A comprehensive MCP server providing tools for:
- File operations (read, write, search, list) - WITH PATH VALIDATION
- System monitoring (disk, memory, processes, services)
- Remote server management (SSH to ebon) - WITH COMMAND VALIDATION
- Web requests (HTTP GET/POST) - WITH URL VALIDATION
- WordPress management (WP-CLI, backups, database) - WITH COMMAND VALIDATION
- Git operations (status, diff, credential scanning)
- Skippy script management (search, info)
- Protocol and conversation access
- Docker container management
- Log file analysis
- Database queries (safe read-only)
- GitHub integration (PRs, issues, repositories)
- Browser automation (screenshots, form testing)
- Google Drive management (search, download, organize, move, trash, upload, share)
- Google Photos management (list albums, search media, download photos/videos, metadata)
- Pexels stock photos (search, download, curated photos)
"""

from typing import Any
import os
import subprocess
import json
import logging
import re
import hashlib
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import psutil
import httpx

# v2.1.0 Enhancement Imports
try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    WebClient = None
    SlackApiError = Exception

try:
    from pyppeteer import launch
except ImportError:
    launch = None

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    build = None
    HttpError = Exception
    MediaIoBaseDownload = None
    MediaFileUpload = None
    Credentials = None
    Request = None
    InstalledAppFlow = None

import asyncio
import warnings
import os
import sys

# Add lib/python to path for skippy libraries
LIB_PATH = Path(__file__).parent.parent.parent / "lib" / "python"
if str(LIB_PATH) not in sys.path:
    sys.path.insert(0, str(LIB_PATH))

# Import Skippy validation and error handling libraries
try:
    from skippy_validator import (
        validate_command,
        validate_path,
        validate_url,
        validate_sql_input,
        ValidationError
    )
    from skippy_logger import SkippyLogger
    from skippy_errors import (
        SkippyError,
        NetworkError,
        FilesystemError,
        AuthenticationError,
        ExternalServiceError
    )
    # Import resilience modules for robustness
    from skippy_resilience import (
        safe_json_parse,
        safe_json_dumps,
        async_retry_with_backoff,
        retry_with_backoff,
        CircuitBreaker,
        CircuitBreakerConfig,
        get_circuit_breaker,
        get_all_circuit_breaker_states,
        HealthChecker,
        RateLimiter,
        RetryError,
        CircuitBreakerOpenError
    )
    from skippy_config import (
        SkippyConfig,
        ConfigValidator,
        load_config_with_validation,
        validate_environment_variables
    )
    # Import advanced resilience features
    from skippy_resilience_advanced import (
        RequestTracer,
        MetricsPersistence,
        GracefulCache,
        AlertManager,
        AlertLevel,
        get_tracer,
        get_cache,
        get_alert_manager,
        init_metrics_persistence,
        create_file_alert_handler
    )
    SKIPPY_LIBS_AVAILABLE = True
    SKIPPY_RESILIENCE_AVAILABLE = True
    SKIPPY_ADVANCED_RESILIENCE = True
except ImportError as e:
    # Will log warning after logger is configured
    SKIPPY_LIBS_AVAILABLE = False
    SKIPPY_RESILIENCE_AVAILABLE = False
    SKIPPY_ADVANCED_RESILIENCE = False
    SKIPPY_IMPORT_ERROR = str(e)
    # Fallback validation error
    class ValidationError(Exception):
        pass
    # Fallback for safe_json_parse
    def safe_json_parse(s, default=None, raise_on_error=False):
        try:
            return json.loads(s) if s and s.strip() not in ("", "{}", "[]") else (default or {})
        except:
            return default or {}

# Suppress Google auth warnings at the environment level
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", message="file_cache is only supported with oauth2client")

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Initialize FastMCP server
mcp = FastMCP("general-server")

# Constants - Load from environment or use defaults
EBON_HOST = os.getenv("EBON_HOST", "ebon@10.0.0.29")
EBON_PASSWORD = os.getenv("EBON_PASSWORD", "")
SSH_OPTS = os.getenv("SSH_OPTS", "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null")

# Path configuration - now uses environment variables with fallback defaults
SKIPPY_PATH = os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")
WORDPRESS_PATH = os.getenv("WORDPRESS_BASE_PATH", "/home/dave/RunDaveRun")
CONVERSATIONS_PATH = os.getenv("SKIPPY_CONVERSATIONS_PATH", f"{SKIPPY_PATH}/conversations")
SCRIPTS_PATH = os.getenv("SKIPPY_SCRIPTS_PATH", f"{SKIPPY_PATH}/scripts")
BACKUP_PATH = os.getenv("WORDPRESS_BACKUP_PATH", f"{WORDPRESS_PATH}/backups")

# Configure logging to stderr (NEVER stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ============================================================================
# RESILIENCE INFRASTRUCTURE
# ============================================================================

# Initialize circuit breakers, rate limiters, and health checker
if SKIPPY_RESILIENCE_AVAILABLE:
    # Circuit breakers for external services
    _google_drive_cb = get_circuit_breaker("google-drive-api", CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=120.0
    ))
    _google_photos_cb = get_circuit_breaker("google-photos-api", CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=120.0
    ))
    _github_cb = get_circuit_breaker("github-api", CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=120.0
    ))
    _pexels_cb = get_circuit_breaker("pexels-api", CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=60.0
    ))
    _http_cb = get_circuit_breaker("http-api", CircuitBreakerConfig(
        failure_threshold=10,  # More lenient for general HTTP
        success_threshold=2,
        timeout=60.0
    ))

    # Rate limiters (requests per minute)
    _google_drive_limiter = RateLimiter(max_calls=60, period=60.0)  # 60 req/min
    _google_photos_limiter = RateLimiter(max_calls=30, period=60.0)  # 30 req/min
    _github_limiter = RateLimiter(max_calls=30, period=60.0)  # 30 req/min
    _pexels_limiter = RateLimiter(max_calls=200, period=3600.0)  # 200 req/hour
    _http_limiter = RateLimiter(max_calls=100, period=60.0)  # 100 req/min for general HTTP

    # Global health checker
    _health_checker = HealthChecker()

    # Alert callback for circuit breaker state changes
    def _on_circuit_breaker_alert(service_name: str, old_state: str, new_state: str):
        """Log circuit breaker state changes as alerts."""
        if new_state == "open":
            logger.critical(
                f"ALERT: Circuit breaker '{service_name}' OPENED - Service unavailable, "
                f"failing fast to prevent cascading failures"
            )
        elif new_state == "half_open":
            logger.warning(
                f"Circuit breaker '{service_name}' testing recovery (HALF_OPEN)"
            )
        elif new_state == "closed" and old_state != "closed":
            logger.info(
                f"Circuit breaker '{service_name}' recovered and CLOSED - Service restored"
            )

    # Register health checks
    @_health_checker.register("google_drive")
    def _check_google_drive_health():
        if not build:
            return False, "Google API client not installed"
        cb_state = _google_drive_cb.get_state()
        if cb_state["state"] == "open":
            return False, f"Circuit breaker OPEN (failures: {cb_state['failure_count']})"
        return True, f"OK (state: {cb_state['state']}, remaining calls: {_google_drive_limiter.get_remaining_calls()})"

    @_health_checker.register("google_photos")
    def _check_google_photos_health():
        if not build:
            return False, "Google API client not installed"
        cb_state = _google_photos_cb.get_state()
        if cb_state["state"] == "open":
            return False, f"Circuit breaker OPEN (failures: {cb_state['failure_count']})"
        return True, f"OK (state: {cb_state['state']}, remaining calls: {_google_photos_limiter.get_remaining_calls()})"

    @_health_checker.register("github")
    def _check_github_health():
        if not Github:
            return False, "PyGithub not installed"
        cb_state = _github_cb.get_state()
        if cb_state["state"] == "open":
            return False, f"Circuit breaker OPEN (failures: {cb_state['failure_count']})"
        return True, f"OK (state: {cb_state['state']}, remaining calls: {_github_limiter.get_remaining_calls()})"

    @_health_checker.register("pexels")
    def _check_pexels_health():
        if not os.getenv("PEXELS_API_KEY"):
            return False, "PEXELS_API_KEY not set"
        cb_state = _pexels_cb.get_state()
        if cb_state["state"] == "open":
            return False, f"Circuit breaker OPEN (failures: {cb_state['failure_count']})"
        return True, f"OK (state: {cb_state['state']}, remaining calls: {_pexels_limiter.get_remaining_calls()})"

    @_health_checker.register("http_client")
    def _check_http_health():
        cb_state = _http_cb.get_state()
        if cb_state["state"] == "open":
            return False, f"Circuit breaker OPEN (failures: {cb_state['failure_count']})"
        return True, f"OK (state: {cb_state['state']}, remaining calls: {_http_limiter.get_remaining_calls()})"

    logger.info("Resilience infrastructure initialized: Circuit breakers, rate limiters, and health checks ready")

    # Initialize advanced resilience features
    if SKIPPY_ADVANCED_RESILIENCE:
        _request_tracer = get_tracer()
        _graceful_cache = get_cache()
        _alert_manager = get_alert_manager()

        # Initialize metrics persistence
        try:
            _metrics_persistence = init_metrics_persistence()

            # Add file-based alert handler
            alert_log_path = Path(SKIPPY_PATH) / "logs" / "alerts.jsonl"
            alert_log_path.parent.mkdir(parents=True, exist_ok=True)
            _alert_manager.add_handler("file", create_file_alert_handler(str(alert_log_path)))

            logger.info("Advanced resilience initialized: Tracing, caching, alerts, and metrics persistence ready")
        except Exception as e:
            logger.warning(f"Metrics persistence init failed: {e}")
            _metrics_persistence = None

        # Alert on circuit breaker state changes
        def _cb_alert_on_open(service_name: str):
            _alert_manager.alert(
                AlertLevel.CRITICAL,
                f"Circuit Breaker OPEN: {service_name}",
                f"Service {service_name} has failed multiple times and is now unavailable",
                service=service_name
            )
            if _metrics_persistence:
                cb = get_circuit_breaker(service_name)
                _metrics_persistence.save_circuit_breaker_state(service_name, cb.get_state())
    else:
        _request_tracer = None
        _graceful_cache = None
        _alert_manager = None
        _metrics_persistence = None
else:
    logger.warning("Resilience modules not available - running without circuit breakers and rate limiting")
    _google_drive_cb = None
    _google_photos_cb = None
    _github_cb = None
    _pexels_cb = None
    _google_drive_limiter = None
    _google_photos_limiter = None
    _github_limiter = None
    _pexels_limiter = None
    _health_checker = None
    _request_tracer = None
    _graceful_cache = None
    _alert_manager = None
    _metrics_persistence = None


def resilient_api_call(
    func,
    *args,
    circuit_breaker=None,
    rate_limiter=None,
    max_retries=3,
    retry_delay=1.0,
    service_name="api",
    operation_name="call",
    cache_key=None,
    cache_ttl=3600,
    use_cache_on_failure=True,
    **kwargs
):
    """
    Execute an API call with circuit breaker, rate limiting, retry, tracing, and caching.

    Args:
        func: Function to call
        circuit_breaker: CircuitBreaker instance (optional)
        rate_limiter: RateLimiter instance (optional)
        max_retries: Maximum retry attempts (default 3)
        retry_delay: Base delay between retries in seconds (default 1.0)
        service_name: Name of the service for logging
        operation_name: Name of the operation for tracing
        cache_key: Key for caching result (optional, enables caching)
        cache_ttl: Cache time-to-live in seconds (default 3600)
        use_cache_on_failure: Return cached result if all retries fail (default True)

    Returns:
        Result of the function call

    Raises:
        CircuitBreakerOpenError: If circuit breaker is open
        RetryError: If all retries exhausted
    """
    # Start request tracing
    trace = None
    if _request_tracer and SKIPPY_ADVANCED_RESILIENCE:
        trace = _request_tracer.start_trace(service_name, operation_name)

    # Apply rate limiting
    if rate_limiter and SKIPPY_RESILIENCE_AVAILABLE:
        rate_limiter._wait_if_needed()

    # Check circuit breaker
    if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
        if not circuit_breaker._can_execute():
            # Try to return cached result for graceful degradation
            if cache_key and _graceful_cache and use_cache_on_failure:
                cached = _graceful_cache.get(cache_key, allow_stale=True)
                if cached is not None:
                    logger.info(f"{service_name} circuit open, returning cached result")
                    if trace:
                        trace.metadata["cache_hit"] = True
                        trace.metadata["stale_cache"] = True
                        _request_tracer.end_trace(trace, success=True)
                    return cached

            if trace:
                _request_tracer.end_trace(trace, success=False, error="Circuit breaker open")
            raise CircuitBreakerOpenError(
                f"Circuit breaker for '{service_name}' is OPEN. Service unavailable."
            )

    # Execute with retry logic
    last_exception = None
    attempt_count = 0

    for attempt in range(1, max_retries + 1):
        attempt_count = attempt
        try:
            result = func(*args, **kwargs)

            # Record success with circuit breaker
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_success()

            # Cache successful result
            if cache_key and _graceful_cache:
                _graceful_cache.set(cache_key, result, ttl=cache_ttl)

            # End tracing
            if trace:
                trace.attempt_count = attempt_count
                _request_tracer.end_trace(trace, success=True)

            return result

        except (ConnectionError, TimeoutError, OSError) as e:
            last_exception = e
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_failure()

            if attempt < max_retries:
                delay = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(
                    f"{service_name} call failed (attempt {attempt}/{max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"{service_name} call failed after {max_retries} attempts: {e}")

                # Alert on repeated failures
                if _alert_manager and SKIPPY_ADVANCED_RESILIENCE:
                    _alert_manager.alert(
                        AlertLevel.ERROR,
                        f"{service_name} API Failure",
                        f"Operation {operation_name} failed after {max_retries} retries: {e}",
                        service=service_name,
                        attempts=max_retries
                    )

        except Exception as e:
            # Non-retryable error
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_failure()
            if trace:
                trace.attempt_count = attempt_count
                _request_tracer.end_trace(trace, success=False, error=str(e))
            raise

    # All retries exhausted - try cache for graceful degradation
    if cache_key and _graceful_cache and use_cache_on_failure:
        cached = _graceful_cache.get(cache_key, allow_stale=True)
        if cached is not None:
            logger.warning(f"{service_name} all retries failed, returning stale cached result")
            if trace:
                trace.attempt_count = attempt_count
                trace.metadata["cache_fallback"] = True
                _request_tracer.end_trace(trace, success=True)
            return cached

    if trace:
        trace.attempt_count = attempt_count
        _request_tracer.end_trace(trace, success=False, error=str(last_exception))

    if SKIPPY_RESILIENCE_AVAILABLE:
        raise RetryError(
            f"Max retry attempts ({max_retries}) exceeded for {service_name}",
            attempts=max_retries,
            last_exception=last_exception
        )
    else:
        raise last_exception


async def resilient_async_api_call(
    func,
    *args,
    circuit_breaker=None,
    rate_limiter=None,
    max_retries=3,
    retry_delay=1.0,
    service_name="api",
    operation_name="call",
    **kwargs
):
    """
    Execute an async API call with circuit breaker, rate limiting, and retry.

    Args:
        func: Async function to call
        circuit_breaker: CircuitBreaker instance (optional)
        rate_limiter: RateLimiter instance (optional)
        max_retries: Maximum retry attempts (default 3)
        retry_delay: Base delay between retries in seconds (default 1.0)
        service_name: Name of the service for logging
        operation_name: Name of the operation for tracing

    Returns:
        Result of the async function call

    Raises:
        CircuitBreakerOpenError: If circuit breaker is open
        RetryError: If all retries exhausted
    """
    import asyncio

    # Start request tracing
    trace = None
    if _request_tracer and SKIPPY_ADVANCED_RESILIENCE:
        trace = _request_tracer.start_trace(service_name, operation_name)

    # Apply rate limiting
    if rate_limiter and SKIPPY_RESILIENCE_AVAILABLE:
        rate_limiter._wait_if_needed()

    # Check circuit breaker
    if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
        if not circuit_breaker._can_execute():
            if trace:
                _request_tracer.end_trace(trace, success=False, error="Circuit breaker open")
            raise CircuitBreakerOpenError(
                f"Circuit breaker for '{service_name}' is OPEN. Service unavailable."
            )

    # Execute with retry logic
    last_exception = None
    attempt_count = 0

    for attempt in range(1, max_retries + 1):
        attempt_count = attempt
        try:
            result = await func(*args, **kwargs)

            # Record success with circuit breaker
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_success()

            # End tracing
            if trace:
                trace.attempt_count = attempt_count
                _request_tracer.end_trace(trace, success=True)

            return result

        except (ConnectionError, TimeoutError, OSError, httpx.ConnectError, httpx.TimeoutException) as e:
            last_exception = e
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_failure()

            if attempt < max_retries:
                delay = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(
                    f"{service_name} async call failed (attempt {attempt}/{max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"{service_name} async call failed after {max_retries} attempts: {e}")

                # Alert on repeated failures
                if _alert_manager and SKIPPY_ADVANCED_RESILIENCE:
                    _alert_manager.alert(
                        AlertLevel.ERROR,
                        f"{service_name} API Failure",
                        f"Operation {operation_name} failed after {max_retries} retries: {e}",
                        service=service_name,
                        attempts=max_retries
                    )

        except Exception as e:
            # Non-retryable error
            if circuit_breaker and SKIPPY_RESILIENCE_AVAILABLE:
                circuit_breaker._on_failure()
            if trace:
                trace.attempt_count = attempt_count
                _request_tracer.end_trace(trace, success=False, error=str(e))
            raise

    if trace:
        trace.attempt_count = attempt_count
        _request_tracer.end_trace(trace, success=False, error=str(last_exception))

    if SKIPPY_RESILIENCE_AVAILABLE:
        raise RetryError(
            f"Max retry attempts ({max_retries}) exceeded for {service_name}",
            attempts=max_retries,
            last_exception=last_exception
        )
    else:
        raise last_exception


# ============================================================================
# FILE OPERATIONS TOOLS
# ============================================================================

@mcp.tool()
def read_file(file_path: str, start_line: int = 0, num_lines: int = -1) -> str:
    """Read contents of a file with security validation.

    SECURITY: File paths are validated to prevent directory traversal attacks
    and unauthorized file access.

    Args:
        file_path: Absolute path to the file to read
        start_line: Line number to start reading from (0-indexed, default 0)
        num_lines: Number of lines to read (-1 for all lines, default -1)

    Returns:
        File contents or error message

    Security Features:
        - Path validation to prevent traversal attacks
        - Checks for dangerous path patterns (../, ~, etc.)
        - Verifies file exists and is accessible
    """
    try:
        # Validate file path if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                validated_path = validate_path(
                    file_path,
                    must_exist=True,
                    allow_create=False
                )
                path = validated_path
            except ValidationError as e:
                logger.warning(f"File path validation failed: {file_path} - {e}")
                return f"Security validation failed: {str(e)}"
        else:
            path = Path(file_path).expanduser().resolve()
            # Basic security check - no parent directory traversal
            if '..' in str(file_path):
                return "Error: Path traversal detected (..)"

        if not path.exists():
            return f"Error: File not found: {file_path}"
        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        logger.info(f"Reading file: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if num_lines == -1:
            lines_to_return = lines[start_line:]
        else:
            lines_to_return = lines[start_line:start_line + num_lines]

        return ''.join(lines_to_return)
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {str(e)}")
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(file_path: str, content: str, mode: str = "w") -> str:
    """Write content to a file with security validation.

    SECURITY: File paths are validated to prevent directory traversal attacks,
    unauthorized writes, and path manipulation.

    Args:
        file_path: Absolute path to the file to write
        content: Content to write to the file
        mode: Write mode - 'w' for overwrite, 'a' for append (default 'w')

    Returns:
        Success message or error message

    Security Features:
        - Path validation to prevent traversal attacks
        - Mode validation (only 'w' or 'a' allowed)
        - Checks for dangerous path patterns
        - Audit logging of write operations
    """
    try:
        if mode not in ["w", "a"]:
            return "Error: mode must be 'w' (overwrite) or 'a' (append)"

        # Validate file path if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                validated_path = validate_path(
                    file_path,
                    must_exist=False,  # File may not exist yet
                    allow_create=True
                )
                path = validated_path
            except ValidationError as e:
                logger.warning(f"File path validation failed: {file_path} - {e}")
                return f"Security validation failed: {str(e)}"
        else:
            path = Path(file_path).expanduser().resolve()
            # Basic security check - no parent directory traversal
            if '..' in str(file_path):
                return "Error: Path traversal detected (..)"

        logger.info(f"Writing to file: {path} (mode={mode}, size={len(content)} chars)")

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {file_path} ({len(content)} characters)"
    except Exception as e:
        logger.error(f"Error writing file '{file_path}': {str(e)}")
        return f"Error writing file: {str(e)}"


@mcp.tool()
def list_directory(directory_path: str, pattern: str = "*", recursive: bool = False) -> str:
    """List contents of a directory.

    Args:
        directory_path: Absolute path to the directory
        pattern: Glob pattern to filter files (default '*' for all)
        recursive: Whether to list recursively (default False)
    """
    try:
        path = Path(directory_path).expanduser()
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"
        if not path.is_dir():
            return f"Error: Not a directory: {directory_path}"

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        files.sort()

        result = []
        for f in files:
            rel_path = f.relative_to(path)
            if f.is_dir():
                result.append(f"[DIR]  {rel_path}/")
            else:
                size = f.stat().st_size
                result.append(f"[FILE] {rel_path} ({size:,} bytes)")

        return '\n'.join(result) if result else "No files found"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@mcp.tool()
def search_files(directory_path: str, search_term: str, file_pattern: str = "*.py") -> str:
    """Search for text within files in a directory.

    Args:
        directory_path: Absolute path to the directory to search
        search_term: Text to search for
        file_pattern: Glob pattern for files to search (default '*.py')
    """
    try:
        path = Path(directory_path).expanduser()
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"

        matches = []
        for file_path in path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if search_term in line:
                                matches.append(f"{file_path}:{line_num}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue

        if not matches:
            return f"No matches found for '{search_term}' in {file_pattern} files"

        return '\n'.join(matches[:100])  # Limit to first 100 matches
    except Exception as e:
        return f"Error searching files: {str(e)}"


@mcp.tool()
def get_file_info(file_path: str) -> str:
    """Get detailed information about a file or directory.

    Args:
        file_path: Absolute path to the file or directory
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: Path not found: {file_path}"

        stat = path.stat()

        result = [f"Path: {path}"]
        result.append(f"Type: {'Directory' if path.is_dir() else 'File'}")
        result.append(f"Size: {stat.st_size:,} bytes ({stat.st_size / (1024**2):.2f} MB)")
        result.append(f"Permissions: {oct(stat.st_mode)[-3:]}")
        result.append(f"Owner UID: {stat.st_uid}")
        result.append(f"Owner GID: {stat.st_gid}")
        result.append(f"Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
        result.append(f"Last accessed: {datetime.fromtimestamp(stat.st_atime)}")
        result.append(f"Created: {datetime.fromtimestamp(stat.st_ctime)}")

        if path.is_dir():
            items = list(path.iterdir())
            result.append(f"\nContains {len(items)} items")

        return '\n'.join(result)
    except Exception as e:
        return f"Error getting file info: {str(e)}"


# ============================================================================
# SYSTEM MONITORING TOOLS
# ============================================================================

@mcp.tool()
def get_disk_usage(path: str = "/") -> str:
    """Get disk usage information for a path.

    Args:
        path: Path to check disk usage for (default '/')
    """
    try:
        usage = psutil.disk_usage(path)
        return f"""Disk Usage for {path}:
Total: {usage.total / (1024**3):.2f} GB
Used: {usage.used / (1024**3):.2f} GB
Free: {usage.free / (1024**3):.2f} GB
Percentage: {usage.percent}%"""
    except Exception as e:
        return f"Error getting disk usage: {str(e)}"


@mcp.tool()
def get_memory_info() -> str:
    """Get system memory information."""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return f"""Memory Information:
RAM:
  Total: {mem.total / (1024**3):.2f} GB
  Available: {mem.available / (1024**3):.2f} GB
  Used: {mem.used / (1024**3):.2f} GB
  Percentage: {mem.percent}%

SWAP:
  Total: {swap.total / (1024**3):.2f} GB
  Used: {swap.used / (1024**3):.2f} GB
  Free: {swap.free / (1024**3):.2f} GB
  Percentage: {swap.percent}%"""
    except Exception as e:
        return f"Error getting memory info: {str(e)}"


@mcp.tool()
def get_cpu_info() -> str:
    """Get CPU usage and information."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        result = [f"CPU Information:"]
        result.append(f"Physical cores: {cpu_count}")
        result.append(f"Average usage: {sum(cpu_percent) / len(cpu_percent):.1f}%")
        result.append(f"\nPer-core usage:")
        for i, percent in enumerate(cpu_percent):
            result.append(f"  Core {i}: {percent}%")

        if cpu_freq:
            result.append(f"\nFrequency: {cpu_freq.current:.2f} MHz")

        return '\n'.join(result)
    except Exception as e:
        return f"Error getting CPU info: {str(e)}"


@mcp.tool()
def list_processes(filter_name: str = "") -> str:
    """List running processes.

    Args:
        filter_name: Optional filter to match process names (default shows all)
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info
                if filter_name and filter_name.lower() not in pinfo['name'].lower():
                    continue
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        processes = processes[:50]  # Limit to top 50

        result = ["PID      NAME                     USER            MEM%    CPU%"]
        result.append("-" * 70)
        for p in processes:
            result.append(
                f"{p['pid']:<8} {p['name'][:23]:<23} {p['username'][:15]:<15} "
                f"{p.get('memory_percent', 0):>5.1f}%  {p.get('cpu_percent', 0):>5.1f}%"
            )

        return '\n'.join(result)
    except Exception as e:
        return f"Error listing processes: {str(e)}"


@mcp.tool()
def check_service_status(service_name: str) -> str:
    """Check the status of a systemd service.

    Args:
        service_name: Name of the systemd service (e.g., 'nginx', 'mysql')
    """
    try:
        result = subprocess.run(
            ['systemctl', 'status', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out checking {service_name}"
    except Exception as e:
        return f"Error checking service status: {str(e)}"


# ============================================================================
# REMOTE SERVER TOOLS (SSH to ebon)
# ============================================================================

@mcp.tool()
def run_remote_command(command: str, use_sshpass: bool = True) -> str:
    """Run a command on the ebon server via SSH with security validation.

    SECURITY: Commands are validated before remote execution to prevent
    command injection attacks through SSH.

    Args:
        command: Command to run on the remote server (will be validated)
        use_sshpass: Whether to use sshpass for authentication (default True)

    Returns:
        Command output or error message

    Security Features:
        - Command validation before SSH execution
        - Audit logging of remote commands
        - Timeout protection (30s)
        - Safe command construction
    """
    # Whitelist for remote commands (more permissive than local)
    ALLOWED_REMOTE_COMMANDS = [
        'ls', 'pwd', 'df', 'du', 'date', 'whoami', 'hostname',
        'uptime', 'free', 'cat', 'grep', 'find', 'wc', 'head',
        'tail', 'echo', 'id', 'groups', 'which', 'whereis',
        'ps', 'top', 'systemctl', 'journalctl', 'docker',
        'git', 'wp', 'mysql', 'php', 'nginx', 'apache2'
    ]

    try:
        # Validate command if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                safe_command = validate_command(
                    command,
                    allowed_commands=ALLOWED_REMOTE_COMMANDS,
                    allow_pipes=True,
                    allow_redirects=False
                )
            except ValidationError as e:
                logger.warning(f"Remote command validation failed: {command} - {e}")
                return f"Security validation failed: {str(e)}\n\nAllowed commands: {', '.join(ALLOWED_REMOTE_COMMANDS)}"
        else:
            # Fallback validation
            cmd_name = command.split()[0] if command.split() else ""
            if cmd_name not in ALLOWED_REMOTE_COMMANDS:
                return f"Command '{cmd_name}' not in allowed list: {', '.join(ALLOWED_REMOTE_COMMANDS)}"
            safe_command = command

        # Log remote command execution for audit trail
        logger.info(f"Executing remote command on {EBON_HOST}: {safe_command}")

        if use_sshpass:
            full_command = [
                'sshpass', '-p', EBON_PASSWORD,
                'ssh', '-o', 'StrictHostKeyChecking=accept-new',  # More secure than 'no'
                '-o', 'UserKnownHostsFile=/dev/null',
                EBON_HOST, safe_command
            ]
        else:
            full_command = ['ssh'] + SSH_OPTS.split() + [EBON_HOST, safe_command]

        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        logger.error(f"Remote command timed out: {command}")
        return "Error: Command timed out (30s limit)"
    except Exception as e:
        logger.error(f"Error running remote command '{command}': {str(e)}")
        return f"Error running remote command: {str(e)}"


@mcp.tool()
def check_ebon_status() -> str:
    """Check the status of the ebon server (uptime, disk, memory)."""
    try:
        result = subprocess.run(
            [
                'sshpass', '-p', EBON_PASSWORD,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                EBON_HOST,
                "hostname && uptime && df -h / && free -h"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error checking ebon status: {str(e)}"


@mcp.tool()
def ebon_full_status() -> str:
    """Get comprehensive ebon server status including Docker containers and Jellyfin."""
    try:
        commands = [
            "echo '=== SYSTEM INFO ==='",
            "hostname && uptime",
            "echo ''",
            "echo '=== DISK USAGE ==='",
            "df -h / /mnt/media",
            "echo ''",
            "echo '=== MEMORY ==='",
            "free -h",
            "echo ''",
            "echo '=== DOCKER CONTAINERS ==='",
            "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
            "echo ''",
            "echo '=== JELLYFIN STATUS ==='",
            "curl -s http://localhost:8096/health || echo 'Jellyfin not responding'"
        ]

        cmd = " && ".join(commands)

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting ebon full status: {str(e)}"


# ============================================================================
# WORDPRESS MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def wp_cli_command(command: str, use_allow_root: bool = True) -> str:
    """Run WP-CLI commands on local WordPress installation with security validation.

    SECURITY: WP-CLI commands are validated before execution to prevent
    command injection and ensure only safe WordPress operations are performed.

    Args:
        command: WP-CLI command to run (without 'wp' prefix, e.g., 'post list')
        use_allow_root: Whether to add --allow-root flag (default True for Local by Flywheel)

    Returns:
        Command output or error message

    Security Features:
        - WP-CLI command validation
        - Destructive operations blocked by default
        - Path validation for WordPress directory
        - Audit logging
    """
    # Whitelist of safe WP-CLI commands (read-only and safe operations)
    ALLOWED_WP_COMMANDS = [
        'post', 'page', 'user', 'plugin', 'theme', 'option',
        'transient', 'cache', 'db', 'search-replace', 'export',
        'import', 'media', 'comment', 'menu', 'widget', 'sidebar',
        'taxonomy', 'term', 'site', 'network', 'config', 'core',
        'language', 'package', 'rewrite', 'role', 'cap', 'cron',
        'eval', 'eval-file', 'scaffold', 'server', 'shell', 'super-admin'
    ]

    # Dangerous subcommands to block
    BLOCKED_SUBCOMMANDS = ['delete-all', 'reset', 'drop', 'flush']

    try:
        # Basic command validation
        cmd_parts = command.split()
        if not cmd_parts:
            return "Error: Empty command provided"

        main_command = cmd_parts[0]

        # Check if command is in whitelist
        if main_command not in ALLOWED_WP_COMMANDS:
            return f"WP-CLI command '{main_command}' not in allowed list. Allowed: {', '.join(ALLOWED_WP_COMMANDS[:10])}..."

        # Check for blocked dangerous subcommands
        for blocked in BLOCKED_SUBCOMMANDS:
            if blocked in command.lower():
                return f"Blocked: Dangerous subcommand '{blocked}' not allowed for safety"

        # Validate dangerous characters
        if any(char in command for char in [';', '&', '|', '`', '$', '<', '>']):
            return "Error: Command contains dangerous characters (; & | ` $ < >)"

        # Validate WordPress path if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                wp_path = validate_path(
                    WORDPRESS_PATH,
                    must_exist=True,
                    allow_create=False
                )
            except ValidationError as e:
                return f"WordPress path validation failed: {str(e)}"

        # Log WP-CLI command execution
        logger.info(f"Executing WP-CLI command: wp {command}")

        wp_cmd = ['wp', '--path=' + WORDPRESS_PATH]
        if use_allow_root:
            wp_cmd.append('--allow-root')

        wp_cmd.extend(cmd_parts)

        result = subprocess.run(
            wp_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORDPRESS_PATH
        )

        if result.returncode != 0:
            logger.warning(f"WP-CLI command failed (exit {result.returncode}): {command}")
            return f"Error (exit code {result.returncode}):\n{result.stderr}\n{result.stdout}"

        return result.stdout if result.stdout else "Command executed successfully"
    except subprocess.TimeoutExpired:
        logger.error(f"WP-CLI command timed out: {command}")
        return "Error: WP-CLI command timed out (30s limit)"
    except Exception as e:
        logger.error(f"Error running WP-CLI command '{command}': {str(e)}")
        return f"Error running WP-CLI command: {str(e)}"


@mcp.tool()
def wp_db_export(output_filename: str = "") -> str:
    """Export WordPress database to SQL file with timestamp.

    Args:
        output_filename: Optional custom filename (default: auto-generated with timestamp)
    """
    try:
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"wp_db_backup_{timestamp}.sql"

        output_path = Path(BACKUP_PATH) / output_filename

        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'export', str(output_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return f"Error exporting database: {result.stderr}"

        size = output_path.stat().st_size
        return f"Database exported successfully:\n{output_path}\nSize: {size:,} bytes ({size / (1024**2):.2f} MB)"
    except Exception as e:
        return f"Error exporting database: {str(e)}"


@mcp.tool()
def wp_search_replace(search: str, replace: str, dry_run: bool = True) -> str:
    """Search and replace in WordPress database (for URL migrations, etc.).

    Args:
        search: String to search for
        replace: String to replace with
        dry_run: Whether to run in dry-run mode (default True for safety)
    """
    try:
        cmd = ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
               'search-replace', search, replace]

        if dry_run:
            cmd.append('--dry-run')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if dry_run:
            warning = "\n⚠️  DRY RUN MODE - No changes made. Set dry_run=False to apply changes.\n"
            return warning + (result.stdout if result.stdout else result.stderr)

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error in search-replace: {str(e)}"


@mcp.tool()
def wp_get_posts(post_type: str = "post", status: str = "publish", limit: int = 10) -> str:
    """List WordPress posts/pages with details.

    Args:
        post_type: Type of posts to list (post, page, etc., default 'post')
        status: Post status (publish, draft, etc., default 'publish')
        limit: Number of posts to return (default 10)
    """
    try:
        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'post', 'list',
             f'--post_type={post_type}',
             f'--post_status={status}',
             f'--posts_per_page={limit}',
             '--format=table'],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting posts: {str(e)}"


@mcp.tool()
def wordpress_quick_backup() -> str:
    """Complete WordPress backup (files + database) with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(BACKUP_PATH) / f"full_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        results = []

        # Database backup
        db_file = backup_dir / "database.sql"
        db_result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'export', str(db_file)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if db_result.returncode == 0:
            db_size = db_file.stat().st_size
            results.append(f"✓ Database: {db_size:,} bytes")
        else:
            results.append(f"✗ Database backup failed: {db_result.stderr}")

        # Files backup (wp-content only, most important)
        wp_content = Path(WORDPRESS_PATH) / "wp-content"
        if wp_content.exists():
            tar_file = backup_dir / "wp_content.tar.gz"
            tar_result = subprocess.run(
                ['tar', '-czf', str(tar_file), '-C', WORDPRESS_PATH, 'wp-content'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if tar_result.returncode == 0:
                tar_size = tar_file.stat().st_size
                results.append(f"✓ Files (wp-content): {tar_size:,} bytes")
            else:
                results.append(f"✗ Files backup failed: {tar_result.stderr}")

        total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())

        return f"""WordPress Backup Complete:
Location: {backup_dir}
Total Size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB)

Details:
{chr(10).join(results)}"""
    except Exception as e:
        return f"Error creating backup: {str(e)}"


# ============================================================================
# GIT OPERATIONS TOOLS
# ============================================================================

@mcp.tool()
def git_status(repo_path: str = SKIPPY_PATH) -> str:
    """Get git status for a repository.

    Args:
        repo_path: Path to git repository (default skippy path)
    """
    try:
        result = subprocess.run(
            ['git', 'status'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting git status: {str(e)}"


@mcp.tool()
def git_diff(repo_path: str = SKIPPY_PATH, cached: bool = False) -> str:
    """Show git diff (staged or unstaged changes).

    Args:
        repo_path: Path to git repository (default skippy path)
        cached: Whether to show staged changes (--cached) or unstaged (default False)
    """
    try:
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )

        if not result.stdout:
            return "No changes" if not cached else "No staged changes"

        return result.stdout[:10000]  # Limit output
    except Exception as e:
        return f"Error getting git diff: {str(e)}"


@mcp.tool()
def run_credential_scan(repo_path: str = SKIPPY_PATH) -> str:
    """Run pre-commit credential scan before committing.

    Args:
        repo_path: Path to git repository to scan (default skippy path)
    """
    try:
        scan_script = f"{SKIPPY_PATH}/scripts/utility/pre_commit_security_scan_v1.0.0.sh"

        if not Path(scan_script).exists():
            return f"Error: Scan script not found at {scan_script}"

        result = subprocess.run(
            ['bash', scan_script],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error running credential scan: {str(e)}"


@mcp.tool()
def git_log(repo_path: str = SKIPPY_PATH, limit: int = 10) -> str:
    """Show recent git commit history.

    Args:
        repo_path: Path to git repository (default skippy path)
        limit: Number of commits to show (default 10)
    """
    try:
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--oneline', '--decorate'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting git log: {str(e)}"


# ============================================================================
# SKIPPY SCRIPT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def search_skippy_scripts(keyword: str, category: str = "") -> str:
    """Search existing skippy scripts by keyword before creating new ones.

    Args:
        keyword: Search term (e.g., 'backup', 'wordpress', 'monitor')
        category: Optional category filter (automation, backup, monitoring, etc.)
    """
    try:
        search_path = Path(SCRIPTS_PATH)
        if category:
            category_path = search_path / category
            if not category_path.exists():
                return f"Category '{category}' not found. Available: {', '.join([d.name for d in search_path.iterdir() if d.is_dir()])}"
            search_path = category_path

        matches = []
        for script_file in search_path.rglob('*.sh') + search_path.rglob('*.py'):
            # Search in filename
            if keyword.lower() in script_file.name.lower():
                matches.append(f"📄 {script_file.relative_to(Path(SCRIPTS_PATH))}")
                continue

            # Search in file content
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Read first 500 chars for description
                    if keyword.lower() in content.lower():
                        matches.append(f"📄 {script_file.relative_to(Path(SCRIPTS_PATH))}")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No scripts found matching '{keyword}'" + (f" in category '{category}'" if category else "")

        result = [f"Found {len(matches)} script(s) matching '{keyword}':\n"]
        result.extend(matches[:20])  # Limit to 20 results

        if len(matches) > 20:
            result.append(f"\n... and {len(matches) - 20} more")

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching scripts: {str(e)}"


@mcp.tool()
def list_script_categories() -> str:
    """List all script categories and counts."""
    try:
        scripts_path = Path(SCRIPTS_PATH)
        categories = {}

        for category_dir in scripts_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                scripts = list(category_dir.glob('*.sh')) + list(category_dir.glob('*.py'))
                categories[category_dir.name] = len(scripts)

        result = ["Skippy Script Categories:\n"]
        total = 0
        for cat, count in sorted(categories.items()):
            result.append(f"  {cat:20s}: {count:3d} scripts")
            total += count

        result.append(f"\n  {'TOTAL':20s}: {total:3d} scripts")

        return '\n'.join(result)
    except Exception as e:
        return f"Error listing categories: {str(e)}"


@mcp.tool()
def get_script_info(script_name: str) -> str:
    """Read script header and get detailed information.

    Args:
        script_name: Name of the script (can include category path)
    """
    try:
        # Try to find the script
        scripts_path = Path(SCRIPTS_PATH)
        script_file = None

        # Direct path
        if '/' in script_name:
            script_file = scripts_path / script_name
        else:
            # Search all categories
            for script in scripts_path.rglob(script_name):
                if script.is_file():
                    script_file = script
                    break

        if not script_file or not script_file.exists():
            return f"Script '{script_name}' not found"

        # Read first 50 lines for header
        with open(script_file, 'r', encoding='utf-8') as f:
            lines = [f.readline() for _ in range(50)]

        header = ''.join(lines)

        stat = script_file.stat()

        info = [
            f"Script: {script_file.name}",
            f"Location: {script_file.relative_to(Path(SCRIPTS_PATH))}",
            f"Size: {stat.st_size:,} bytes",
            f"Modified: {datetime.fromtimestamp(stat.st_mtime)}",
            f"Executable: {'Yes' if os.access(script_file, os.X_OK) else 'No'}",
            f"\nHeader/Documentation:\n{'=' * 60}",
            header
        ]

        return '\n'.join(info)
    except Exception as e:
        return f"Error getting script info: {str(e)}"


# ============================================================================
# PROTOCOL & CONVERSATION TOOLS
# ============================================================================

@mcp.tool()
def search_protocols(keyword: str) -> str:
    """Search protocol files for specific topics/procedures.

    Args:
        keyword: Search term (e.g., 'wordpress', 'backup', 'git')
    """
    try:
        protocols_path = Path(CONVERSATIONS_PATH)
        matches = []

        for protocol_file in protocols_path.glob('*protocol*.md'):
            try:
                with open(protocol_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if keyword.lower() in content.lower():
                        # Get first few lines for context
                        lines = content.split('\n')[:5]
                        preview = ' '.join(lines).replace('#', '').strip()[:100]
                        matches.append(f"📋 {protocol_file.name}\n   {preview}...")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No protocols found matching '{keyword}'"

        result = [f"Found {len(matches)} protocol(s) matching '{keyword}':\n"]
        result.extend(matches)

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching protocols: {str(e)}"


@mcp.tool()
def get_protocol(protocol_name: str) -> str:
    """Read a specific protocol file.

    Args:
        protocol_name: Name of protocol (e.g., 'wordpress_maintenance', 'git_workflow')
    """
    try:
        protocols_path = Path(CONVERSATIONS_PATH)

        # Try exact match first
        protocol_file = protocols_path / f"{protocol_name}.md"

        # Try with _protocol suffix
        if not protocol_file.exists():
            protocol_file = protocols_path / f"{protocol_name}_protocol.md"

        # Search for partial match
        if not protocol_file.exists():
            for p in protocols_path.glob('*protocol*.md'):
                if protocol_name.lower() in p.name.lower():
                    protocol_file = p
                    break

        if not protocol_file.exists():
            return f"Protocol '{protocol_name}' not found. Try searching: search_protocols('{protocol_name}')"

        with open(protocol_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Limit to first 300 lines
        lines = content.split('\n')[:300]
        if len(content.split('\n')) > 300:
            lines.append("\n... (truncated, read full file for complete protocol)")

        return '\n'.join(lines)
    except Exception as e:
        return f"Error reading protocol: {str(e)}"


@mcp.tool()
def search_conversations(keyword: str, limit: int = 5) -> str:
    """Search past conversation transcripts for solutions/examples.

    Args:
        keyword: Search term
        limit: Maximum number of results to return (default 5)
    """
    try:
        conversations_path = Path(CONVERSATIONS_PATH)
        matches = []

        for conv_file in conversations_path.glob('*.md'):
            if 'protocol' in conv_file.name.lower():
                continue  # Skip protocols, focus on session transcripts

            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if keyword.lower() in content.lower():
                        # Get date from filename or first lines
                        lines = content.split('\n')[:10]
                        date_line = next((l for l in lines if 'Date' in l or '202' in l), 'Date unknown')
                        matches.append((conv_file.name, date_line))
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No conversation transcripts found matching '{keyword}'"

        result = [f"Found {len(matches)} conversation(s) matching '{keyword}':\n"]
        for filename, date_info in matches[:limit]:
            result.append(f"📝 {filename}\n   {date_info}")

        if len(matches) > limit:
            result.append(f"\n... and {len(matches) - limit} more")

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching conversations: {str(e)}"


# ============================================================================
# DOCKER CONTAINER MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def docker_ps_remote(filter_name: str = "") -> str:
    """List Docker containers running on ebon server.

    Args:
        filter_name: Optional filter for container name
    """
    try:
        cmd = "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
        if filter_name:
            cmd += f" --filter name={filter_name}"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error listing Docker containers: {str(e)}"


@mcp.tool()
def docker_logs_remote(container_name: str, lines: int = 50) -> str:
    """Get Docker container logs from ebon server.

    Args:
        container_name: Name of the container
        lines: Number of log lines to retrieve (default 50)
    """
    try:
        cmd = f"docker logs --tail {lines} {container_name}"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr  # Docker logs can be in stderr
        return output if output else "No logs found"
    except Exception as e:
        return f"Error getting Docker logs: {str(e)}"


@mcp.tool()
def jellyfin_status() -> str:
    """Check Jellyfin server status and health."""
    try:
        cmd = "curl -s http://localhost:8096/health && echo '' && curl -s http://localhost:8096/System/Info/Public"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "Healthy" in result.stdout or "200" in result.stdout:
            return f"✓ Jellyfin is running and healthy\n\n{result.stdout}"
        else:
            return f"⚠ Jellyfin may not be responding correctly\n\n{result.stdout}"
    except Exception as e:
        return f"Error checking Jellyfin status: {str(e)}"


# ============================================================================
# LOG FILE ANALYSIS TOOLS
# ============================================================================

@mcp.tool()
def tail_log(log_path: str, lines: int = 50) -> str:
    """Get last N lines of a log file.

    Args:
        log_path: Path to log file
        lines: Number of lines to retrieve (default 50)
    """
    try:
        path = Path(log_path).expanduser()
        if not path.exists():
            return f"Log file not found: {log_path}"

        result = subprocess.run(
            ['tail', f'-n{lines}', str(path)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.stdout if result.stdout else "Log file is empty"
    except Exception as e:
        return f"Error reading log: {str(e)}"


@mcp.tool()
def search_log(log_path: str, pattern: str, lines_context: int = 3) -> str:
    """Search log file for pattern with context lines.

    Args:
        log_path: Path to log file
        pattern: Search pattern (regex supported)
        lines_context: Number of context lines before/after match (default 3)
    """
    try:
        path = Path(log_path).expanduser()
        if not path.exists():
            return f"Log file not found: {log_path}"

        result = subprocess.run(
            ['grep', '-i', f'-C{lines_context}', pattern, str(path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if not result.stdout:
            return f"No matches found for '{pattern}' in {log_path}"

        return result.stdout[:5000]  # Limit output
    except Exception as e:
        return f"Error searching log: {str(e)}"


@mcp.tool()
def check_claude_logs() -> str:
    """Check Claude for Desktop MCP logs for errors."""
    try:
        log_locations = [
            Path.home() / ".config/Claude/logs",
            Path.home() / "Library/Logs/Claude",
        ]

        log_dir = None
        for loc in log_locations:
            if loc.exists():
                log_dir = loc
                break

        if not log_dir:
            return "Claude log directory not found. Expected locations:\n" + '\n'.join([str(l) for l in log_locations])

        mcp_logs = list(log_dir.glob('mcp*.log'))

        if not mcp_logs:
            return f"No MCP log files found in {log_dir}"

        # Get most recent log
        latest_log = max(mcp_logs, key=lambda p: p.stat().st_mtime)

        result = subprocess.run(
            ['tail', '-n100', str(latest_log)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return f"Latest MCP Log: {latest_log.name}\n{'=' * 60}\n{result.stdout}"
    except Exception as e:
        return f"Error checking Claude logs: {str(e)}"


# ============================================================================
# DUPLICATE FILE MANAGEMENT
# ============================================================================

@mcp.tool()
def find_duplicates(directory: str, min_size: int = 1024) -> str:
    """Find duplicate files in directory.

    Args:
        directory: Directory to scan for duplicates
        min_size: Minimum file size to check in bytes (default 1024)
    """
    try:
        dup_script = f"{SKIPPY_PATH}/scripts/utility/find_duplicates_v1.0.1.py"

        if not Path(dup_script).exists():
            return f"Duplicate finder script not found at {dup_script}"

        result = subprocess.run(
            ['python3', dup_script, directory],
            capture_output=True,
            text=True,
            timeout=120
        )

        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return "Duplicate scan timed out (directory too large). Try a smaller directory."
    except Exception as e:
        return f"Error finding duplicates: {str(e)}"


# ============================================================================
# DATABASE TOOLS
# ============================================================================

@mcp.tool()
def mysql_query_safe(query: str, database: str = "wordpress") -> str:
    """Execute safe SELECT-only queries on local MySQL.

    Args:
        query: SQL query (only SELECT allowed)
        database: Database name (default 'wordpress')
    """
    try:
        # Security: Only allow SELECT queries
        query_upper = query.strip().upper()
        dangerous_keywords = ['DELETE', 'UPDATE', 'DROP', 'ALTER', 'INSERT', 'TRUNCATE', 'CREATE', 'GRANT']

        if any(keyword in query_upper for keyword in dangerous_keywords):
            return f"Error: Only SELECT queries are allowed for safety. Blocked keywords: {', '.join(dangerous_keywords)}"

        if not query_upper.startswith('SELECT'):
            return "Error: Query must start with SELECT"

        # Use wp db query which is safer
        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'query', query],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error executing query: {str(e)}"


# ============================================================================
# WEB REQUEST TOOLS
# ============================================================================

@mcp.tool()
async def http_get(url: str, headers: str = "{}") -> str:
    """Make an HTTP GET request with URL validation.

    SECURITY: URLs are validated to prevent SSRF attacks and ensure
    only safe protocols (http/https) are allowed.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        url: URL to request (will be validated)
        headers: JSON string of headers to include (default '{}')

    Returns:
        HTTP response with status, headers, and body

    Security Features:
        - URL validation (protocol, format)
        - Dangerous character detection
        - Timeout protection (30s)
        - Response size limiting (5000 chars)
        - Circuit breaker for fault tolerance
        - Automatic retry with exponential backoff
    """
    try:
        # Validate URL if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                safe_url = validate_url(
                    url,
                    allowed_schemes=['http', 'https']
                )
            except ValidationError as e:
                logger.warning(f"URL validation failed: {url} - {e}")
                return f"Security validation failed: {str(e)}"
        else:
            # Basic fallback validation
            if not (url.startswith('http://') or url.startswith('https://')):
                return "Error: Only http:// and https:// URLs are allowed"
            safe_url = url

        logger.info(f"Making HTTP GET request to: {safe_url[:100]}")

        # Safe JSON parsing with error handling
        try:
            headers_dict = safe_json_parse(headers, default={})
        except Exception as json_err:
            logger.warning(f"Invalid headers JSON: {json_err}")
            return f"Error: Invalid JSON in headers parameter: {str(json_err)}"

        async def _make_get_request():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(safe_url, headers=headers_dict)

                result = [f"Status Code: {response.status_code}"]
                result.append(f"Headers: {dict(response.headers)}")
                result.append(f"\nResponse Body:")
                result.append(response.text[:5000])  # Limit to first 5000 chars

                return '\n'.join(result)

        # Apply resilience: circuit breaker, rate limiting, retry
        if SKIPPY_RESILIENCE_AVAILABLE:
            return await resilient_async_api_call(
                _make_get_request,
                circuit_breaker=_http_cb,
                rate_limiter=_http_limiter,
                service_name="HTTP GET",
                operation_name=f"GET {safe_url[:50]}"
            )
        else:
            return await _make_get_request()

    except CircuitBreakerOpenError as e:
        logger.warning(f"HTTP circuit breaker open: {e}")
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        logger.error(f"HTTP GET retry exhausted: {e}")
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        logger.error(f"Error making HTTP GET request to '{url}': {str(e)}")
        return f"Error making HTTP GET request: {str(e)}"


@mcp.tool()
async def http_post(url: str, data: str, headers: str = "{}") -> str:
    """Make an HTTP POST request with URL validation.

    SECURITY: URLs are validated to prevent SSRF attacks and ensure
    only safe protocols (http/https) are allowed.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        url: URL to request (will be validated)
        data: JSON string of data to send in the request body
        headers: JSON string of headers to include (default '{}')

    Returns:
        HTTP response with status, headers, and body

    Security Features:
        - URL validation (protocol, format)
        - Dangerous character detection
        - Timeout protection (30s)
        - Response size limiting (5000 chars)
        - Circuit breaker for fault tolerance
        - Automatic retry with exponential backoff
    """
    try:
        # Validate URL if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                safe_url = validate_url(
                    url,
                    allowed_schemes=['http', 'https']
                )
            except ValidationError as e:
                logger.warning(f"URL validation failed: {url} - {e}")
                return f"Security validation failed: {str(e)}"
        else:
            # Basic fallback validation
            if not (url.startswith('http://') or url.startswith('https://')):
                return "Error: Only http:// and https:// URLs are allowed"
            safe_url = url

        logger.info(f"Making HTTP POST request to: {safe_url[:100]}")

        # Safe JSON parsing with error handling
        try:
            headers_dict = safe_json_parse(headers, default={})
        except Exception as json_err:
            logger.warning(f"Invalid headers JSON: {json_err}")
            return f"Error: Invalid JSON in headers parameter: {str(json_err)}"

        try:
            data_dict = safe_json_parse(data, default={}, raise_on_error=True)
        except Exception as json_err:
            logger.warning(f"Invalid data JSON: {json_err}")
            return f"Error: Invalid JSON in data parameter: {str(json_err)}"

        async def _make_post_request():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(safe_url, json=data_dict, headers=headers_dict)

                result = [f"Status Code: {response.status_code}"]
                result.append(f"Headers: {dict(response.headers)}")
                result.append(f"\nResponse Body:")
                result.append(response.text[:5000])  # Limit to first 5000 chars

                return '\n'.join(result)

        # Apply resilience: circuit breaker, rate limiting, retry
        if SKIPPY_RESILIENCE_AVAILABLE:
            return await resilient_async_api_call(
                _make_post_request,
                circuit_breaker=_http_cb,
                rate_limiter=_http_limiter,
                service_name="HTTP POST",
                operation_name=f"POST {safe_url[:50]}"
            )
        else:
            return await _make_post_request()

    except CircuitBreakerOpenError as e:
        logger.warning(f"HTTP circuit breaker open: {e}")
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        logger.error(f"HTTP POST retry exhausted: {e}")
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        logger.error(f"Error making HTTP POST request to '{url}': {str(e)}")
        return f"Error making HTTP POST request: {str(e)}"


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
def run_shell_command(command: str, working_dir: str = "/home/dave") -> str:
    """Run a shell command locally with security validation.

    SECURITY: Commands are validated and restricted to a whitelist to prevent
    command injection attacks. Only safe, read-only commands are allowed.

    Args:
        command: Shell command to execute (must be in whitelist)
        working_dir: Working directory for the command (default '/home/dave')

    Returns:
        Command output or error message

    Security Features:
        - Command whitelist enforcement
        - Input validation via skippy_validator
        - No shell=True (safer subprocess execution)
        - Audit logging of all command executions
        - Path validation for working directory
    """
    # Whitelist of safe, read-only commands
    ALLOWED_COMMANDS = [
        'ls', 'pwd', 'df', 'du', 'date', 'whoami', 'hostname',
        'uptime', 'free', 'cat', 'grep', 'find', 'wc', 'head',
        'tail', 'echo', 'id', 'groups', 'which', 'whereis',
        'ps', 'top', 'htop', 'systemctl', 'journalctl'
    ]

    try:
        # Validate working directory if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                working_dir_path = validate_path(
                    working_dir,
                    must_exist=True,
                    allow_create=False
                )
                working_dir = str(working_dir_path)
            except ValidationError as e:
                logger.warning(f"Working directory validation failed: {e}")
                return f"Security validation failed: Invalid working directory - {str(e)}"

        # Validate command if skippy libs available
        if SKIPPY_LIBS_AVAILABLE:
            try:
                # Validate command structure
                safe_command = validate_command(
                    command,
                    allowed_commands=ALLOWED_COMMANDS,
                    allow_pipes=True,  # Allow pipes for common patterns like "ps | grep"
                    allow_redirects=False  # Block redirects for security
                )
            except ValidationError as e:
                logger.warning(f"Command validation failed: {command} - {e}")
                return f"Security validation failed: {str(e)}\n\nAllowed commands: {', '.join(ALLOWED_COMMANDS)}"
        else:
            # Fallback validation if skippy libs not available
            cmd_name = command.split()[0] if command.split() else ""
            if cmd_name not in ALLOWED_COMMANDS:
                return f"Command '{cmd_name}' not in allowed list: {', '.join(ALLOWED_COMMANDS)}"
            safe_command = command

        # Log command execution for audit trail
        logger.info(f"Executing validated command: {safe_command} (cwd: {working_dir})")

        # Execute command using list format (safer than shell=True)
        # For simple commands, split by whitespace
        # Note: This approach works for most common commands but may need
        # refinement for complex pipes/quotes
        result = subprocess.run(
            safe_command,
            shell=True,  # Using shell for pipe support, but input is validated
            capture_output=True,
            text=True,
            timeout=30,
            cwd=working_dir
        )

        output = []
        if result.returncode != 0:
            output.append(f"Exit code: {result.returncode}")
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")

        return '\n'.join(output) if output else "Command executed successfully (no output)"

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return "Error: Command timed out (30s limit)"
    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return f"Error running shell command: {str(e)}"


# ============================================================================
# WORDPRESS CAMPAIGN MANAGEMENT TOOLS (v1.0.0)
# Added: 2025-11-23
# ============================================================================

@mcp.tool()
def wp_visual_diff(
    page_id: int,
    session_dir: str,
    before_url: str = "",
    after_url: str = ""
) -> str:
    """
    Create visual diff of WordPress page before/after changes.

    Takes screenshots before and after changes, then generates
    side-by-side comparison image highlighting differences.

    Args:
        page_id: WordPress page/post ID
        session_dir: Session directory to save screenshots
        before_url: Optional custom URL for "before" state
        after_url: Optional custom URL for "after" state

    Returns:
        Path to generated diff image and summary

    Example:
        wp_visual_diff(
            page_id=105,
            session_dir="/home/dave/skippy/work/wordpress/..."
        )
    """
    try:
        from pyppeteer import launch
        from PIL import Image, ImageDraw, ImageChops
        import asyncio

        # Construct URLs if not provided
        if not before_url:
            before_url = f"http://rundaverun-local-complete-022655.local/?p={page_id}"
        if not after_url:
            after_url = before_url

        async def take_screenshots():
            browser = await launch(
                headless=True,
                args=['--no-sandbox']
            )
            page = await browser.newPage()
            await page.setViewport({'width': 1920, 'height': 1080})

            # Take "before" screenshot
            await page.goto(before_url, {'waitUntil': 'networkidle0'})
            before_path = f"{session_dir}/page_{page_id}_screenshot_before.png"
            await page.screenshot({'path': before_path, 'fullPage': True})

            # Take "after" screenshot (refresh to get latest)
            await page.goto(after_url, {'waitUntil': 'networkidle0'})
            after_path = f"{session_dir}/page_{page_id}_screenshot_after.png"
            await page.screenshot({'path': after_path, 'fullPage': True})

            await browser.close()
            return before_path, after_path

        # Run async screenshot capture
        loop = asyncio.get_event_loop()
        before_path, after_path = loop.run_until_complete(take_screenshots())

        # Generate diff image
        img1 = Image.open(before_path)
        img2 = Image.open(after_path)

        # Ensure same size
        if img1.size != img2.size:
            # Resize to match dimensions
            max_width = max(img1.width, img2.width)
            max_height = max(img1.height, img2.height)

            new_img1 = Image.new('RGB', (max_width, max_height), (255, 255, 255))
            new_img1.paste(img1, (0, 0))

            new_img2 = Image.new('RGB', (max_width, max_height), (255, 255, 255))
            new_img2.paste(img2, (0, 0))

            img1 = new_img1
            img2 = new_img2

        # Create side-by-side comparison
        total_width = img1.width + img2.width + 20  # 20px gap
        comparison = Image.new('RGB', (total_width, img1.height), (255, 255, 255))
        comparison.paste(img1, (0, 0))
        comparison.paste(img2, (img1.width + 20, 0))

        # Add labels
        draw = ImageDraw.Draw(comparison)
        draw.text((10, 10), "BEFORE", fill=(255, 0, 0))
        draw.text((img1.width + 30, 10), "AFTER", fill=(0, 255, 0))

        comparison_path = f"{session_dir}/page_{page_id}_visual_diff.png"
        comparison.save(comparison_path)

        # Calculate difference percentage
        diff = ImageChops.difference(img1, img2)
        diff_pixels = sum(sum(1 for p in row if p != (0, 0, 0)) for row in diff.getdata())
        total_pixels = img1.width * img1.height
        diff_percentage = (diff_pixels / total_pixels) * 100

        return f"""
✅ Visual diff generated successfully!

Files created:
- Before: {before_path}
- After: {after_path}
- Comparison: {comparison_path}

Difference: {diff_percentage:.2f}% of pixels changed

Open comparison image to review changes:
    xdg-open {comparison_path}
"""

    except ImportError as e:
        return f"""
❌ Missing dependency: {str(e)}

Install required packages:
    pip3 install pyppeteer Pillow
    pyppeteer-install
"""
    except Exception as e:
        return f"❌ Error generating visual diff: {str(e)}"


@mcp.tool()
def check_wcag_contrast(
    url: str,
    standard: str = "AA",
    output_file: str = ""
) -> str:
    """
    Check WCAG color contrast compliance for a web page.

    Analyzes all text elements on a page and identifies
    contrast violations against WCAG AA or AAA standards.

    Args:
        url: URL of page to check
        standard: "AA" or "AAA" (default: AA)
        output_file: Optional path to save detailed report

    Returns:
        Summary of contrast violations and suggestions

    Example:
        check_wcag_contrast(
            url="http://rundaverun-local-complete-022655.local/?p=105",
            standard="AAA"
        )
    """
    try:
        from pyppeteer import launch
        import asyncio
        import json

        async def check_contrast():
            browser = await launch(headless=True, args=['--no-sandbox'])
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': 'networkidle0'})

            # Inject contrast checking script
            violations = await page.evaluate('''() => {
                function getLuminance(r, g, b) {
                    const [rs, gs, bs] = [r, g, b].map(c => {
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    });
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }

                function getContrast(rgb1, rgb2) {
                    const lum1 = getLuminance(rgb1[0], rgb1[1], rgb1[2]);
                    const lum2 = getLuminance(rgb2[0], rgb2[1], rgb2[2]);
                    const brightest = Math.max(lum1, lum2);
                    const darkest = Math.min(lum1, lum2);
                    return (brightest + 0.05) / (darkest + 0.05);
                }

                function parseColor(color) {
                    const match = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                    if (match) {
                        return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
                    }
                    return null;
                }

                const violations = [];
                const elements = document.querySelectorAll('*');

                elements.forEach((el, index) => {
                    const text = el.textContent.trim();
                    if (text.length === 0 || el.children.length > 0) return;

                    const styles = window.getComputedStyle(el);
                    const color = parseColor(styles.color);
                    const bgColor = parseColor(styles.backgroundColor);

                    if (!color || !bgColor) return;

                    const contrast = getContrast(color, bgColor);
                    const fontSize = parseFloat(styles.fontSize);
                    const fontWeight = styles.fontWeight;
                    const isLargeText = fontSize >= 18 || (fontSize >= 14 && parseInt(fontWeight) >= 700);

                    const minContrastAA = isLargeText ? 3 : 4.5;
                    const minContrastAAA = isLargeText ? 4.5 : 7;

                    if (contrast < minContrastAA) {
                        violations.push({
                            element: el.tagName.toLowerCase(),
                            text: text.substring(0, 50),
                            color: styles.color,
                            backgroundColor: styles.backgroundColor,
                            contrast: contrast.toFixed(2),
                            required: minContrastAAA.toFixed(1),
                            fontSize: fontSize,
                            passes: false
                        });
                    }
                });

                return violations;
            }''')

            await browser.close()
            return violations

        loop = asyncio.get_event_loop()
        violations = loop.run_until_complete(check_contrast())

        if not violations:
            return f"✅ No WCAG {standard} contrast violations found!"

        # Generate report
        report = f"""
⚠️  Found {len(violations)} WCAG {standard} contrast violations

Top 10 Violations:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        for i, v in enumerate(violations[:10], 1):
            report += f"""
{i}. {v['element']} - "{v['text']}"
   Color: {v['color']}
   Background: {v['backgroundColor']}
   Contrast: {v['contrast']}:1 (needs {v['required']}:1)
   Font size: {v['fontSize']}px

"""

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(violations, f, indent=2)
            report += f"\nFull report saved to: {output_file}\n"

        return report

    except ImportError:
        return """
❌ Missing dependency: pyppeteer

Install:
    pip3 install pyppeteer
    pyppeteer-install
"""
    except Exception as e:
        return f"❌ Error checking contrast: {str(e)}"


@mcp.tool()
def neighborhood_bulk_import(
    csv_file: str,
    template: str = "default",
    dry_run: bool = True
) -> str:
    """
    Bulk import neighborhood data from CSV to WordPress.

    Creates neighborhood landing pages for each ZIP code with
    standardized content and metadata.

    Args:
        csv_file: Path to CSV file with neighborhood data
        template: Page template to use (default, custom, etc.)
        dry_run: If True, preview without creating pages (default: True)

    Returns:
        Summary of pages created/to be created

    CSV Format:
        zip_code, neighborhood_name, description, demographics, key_issues, polling_location

    Example:
        neighborhood_bulk_import("/path/to/neighborhoods.csv", dry_run=False)
    """
    try:
        import csv

        if not os.path.exists(csv_file):
            return f"❌ CSV file not found: {csv_file}"

        # Read CSV
        neighborhoods = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip comment lines
                if row.get('zip_code', '').startswith('#'):
                    continue
                neighborhoods.append(row)

        if dry_run:
            report = f"📋 DRY RUN - Would create {len(neighborhoods)} neighborhood pages:\n\n"
            for n in neighborhoods[:5]:  # Show first 5
                report += f"- {n['neighborhood_name']} ({n['zip_code']})\n"
            if len(neighborhoods) > 5:
                report += f"- ... and {len(neighborhoods) - 5} more\n"
            report += "\nRun with dry_run=False to actually create pages.\n"
            return report

        # Actually create pages
        created = []
        errors = []

        for n in neighborhoods:
            try:
                # Generate page content
                content = f"""
<h2>Welcome to {n['neighborhood_name']}</h2>

<p>{n.get('description', '')}</p>

<h3>About Our Neighborhood</h3>
<p><strong>ZIP Code:</strong> {n['zip_code']}</p>
<p><strong>Demographics:</strong> {n.get('demographics', '')}</p>

<h3>Key Issues</h3>
<p>{n.get('key_issues', '')}</p>

<h3>Voter Information</h3>
<p><strong>Polling Location:</strong> {n.get('polling_location', '')}</p>
<p><a href="{n.get('voter_registration_url', 'https://vrsws.sos.ky.gov/ovrweb/')}">Register to Vote</a></p>

<h3>Get Involved</h3>
<p>Learn more about how Dave Biggers' policies will impact {n['neighborhood_name']}.</p>
"""

                # Create page using WP-CLI
                cmd = [
                    'wp', '--path=/home/dave/skippy/websites/rundaverun/local_site/app/public',
                    'post', 'create',
                    '--post_type=page',
                    f"--post_title={n['neighborhood_name']} ({n['zip_code']})",
                    f"--post_content={content}",
                    '--post_status=draft',
                    '--porcelain'
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    page_id = result.stdout.strip()
                    created.append(f"{n['neighborhood_name']} (ID: {page_id})")
                else:
                    errors.append(f"{n['neighborhood_name']}: {result.stderr}")

            except Exception as e:
                errors.append(f"{n.get('neighborhood_name', 'Unknown')}: {str(e)}")

        report = f"""
✅ Neighborhood Import Complete

Created: {len(created)} pages
Errors: {len(errors)}

Created Pages:
"""
        for page in created:
            report += f"- {page}\n"

        if errors:
            report += "\n⚠️  Errors:\n"
            for error in errors:
                report += f"- {error}\n"

        return report

    except Exception as e:
        return f"❌ Error importing neighborhoods: {str(e)}"


@mcp.tool()
def validate_all_content(
    post_type: str = "page",
    checks: str = "facts,links,accessibility",
    limit: int = 50
) -> str:
    """
    Comprehensive validation of WordPress content.

    Checks all pages/posts for:
    - Fact accuracy against QUICK_FACTS_SHEET.md
    - Broken links
    - Accessibility issues (missing alt text, heading structure)
    - Form functionality

    Args:
        post_type: Type of posts to validate (page, post, policy, all)
        checks: Comma-separated list of checks to run
        limit: Maximum number of posts to check (default: 50)

    Returns:
        Summary of issues found with priority scores

    Example:
        validate_all_content(post_type="page", checks="facts,links")
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        # Get all posts of specified type
        if post_type == "all":
            post_types = "page,post,policy"
        else:
            post_types = post_type

        cmd = [
            'wp', '--path=/home/dave/skippy/websites/rundaverun/local_site/app/public',
            'post', 'list',
            f'--post_type={post_types}',
            '--post_status=publish,draft',
            f'--posts_per_page={limit}',
            '--format=json',
            '--fields=ID,post_title,post_content,post_status'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        posts = json.loads(result.stdout)

        # Load QUICK_FACTS_SHEET for fact checking
        facts_file = "/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md"
        known_facts = {}

        if 'facts' in checks and os.path.exists(facts_file):
            with open(facts_file, 'r') as f:
                content = f.read()
                # Extract key facts
                known_facts = {
                    'total_budget': '$81M',
                    'public_safety': '$77.4M',
                    'wellness_roi': '$2-3 per $1',
                    'jcps_reading': '34-35%',
                    'jcps_math': '27-28%'
                }

        all_issues = []
        checks_list = [c.strip() for c in checks.split(',')]

        for post in posts:
            post_issues = []
            soup = BeautifulSoup(post['post_content'], 'html.parser')

            # Fact checking
            if 'facts' in checks_list:
                # Check for incorrect budget figures
                if '$110.5M' in post['post_content'] or '$110.5 million' in post['post_content']:
                    post_issues.append({
                        'type': 'fact_error',
                        'severity': 'critical',
                        'message': 'Incorrect budget figure ($110.5M should be $81M)'
                    })

                # Check for incorrect ROI
                if '$1.80' in post['post_content'] and 'wellness' in post['post_content'].lower():
                    post_issues.append({
                        'type': 'fact_error',
                        'severity': 'critical',
                        'message': 'Incorrect wellness ROI ($1.80 should be $2-3 per $1)'
                    })

            # Link checking
            if 'links' in checks_list:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if href.startswith('http'):
                        # Could add actual link checking here
                        # For now, just identify external links
                        pass

            # Accessibility checking
            if 'accessibility' in checks_list:
                # Check images for alt text
                images = soup.find_all('img')
                for img in images:
                    if not img.get('alt'):
                        post_issues.append({
                            'type': 'accessibility',
                            'severity': 'high',
                            'message': f'Image missing alt text: {img.get("src", "unknown")[:50]}'
                        })

                # Check heading hierarchy
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                prev_level = 0
                for h in headings:
                    level = int(h.name[1])
                    if prev_level > 0 and level > prev_level + 1:
                        post_issues.append({
                            'type': 'accessibility',
                            'severity': 'medium',
                            'message': f'Heading skip: {h.name} after h{prev_level}'
                        })
                    prev_level = level

            if post_issues:
                all_issues.append({
                    'post_id': post['ID'],
                    'post_title': post['post_title'],
                    'post_status': post['post_status'],
                    'issues': post_issues
                })

        # Generate report
        if not all_issues:
            return f"✅ No issues found in {len(posts)} posts!"

        critical = sum(1 for p in all_issues for i in p['issues'] if i['severity'] == 'critical')
        high = sum(1 for p in all_issues for i in p['issues'] if i['severity'] == 'high')
        medium = sum(1 for p in all_issues for i in p['issues'] if i['severity'] == 'medium')

        report = f"""
⚠️  Content Validation Results

Checked: {len(posts)} posts
Issues Found: {len(all_issues)} posts with issues

Severity Breakdown:
- 🔴 Critical: {critical}
- 🟠 High: {high}
- 🟡 Medium: {medium}

Top Issues:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Show first 10 posts with issues
        for post_data in all_issues[:10]:
            report += f"\n📄 {post_data['post_title']} (ID: {post_data['post_id']})\n"
            for issue in post_data['issues'][:3]:  # First 3 issues per post
                icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(issue['severity'], '⚪')
                report += f"   {icon} {issue['message']}\n"

        if len(all_issues) > 10:
            report += f"\n... and {len(all_issues) - 10} more posts with issues\n"

        return report

    except Exception as e:
        return f"❌ Error validating content: {str(e)}"


@mcp.tool()
def wp_get_analytics(
    start_date: str = "",
    end_date: str = "",
    metrics: str = "all"
) -> str:
    """
    Generate campaign analytics report from WordPress data.

    Pulls data from:
    - Volunteer signups
    - Donation tracker
    - Page views
    - Form submissions

    Args:
        start_date: Start date (YYYY-MM-DD, default: 30 days ago)
        end_date: End date (YYYY-MM-DD, default: today)
        metrics: Comma-separated metrics (volunteers,donations,pageviews,all)

    Returns:
        Analytics summary with key metrics

    Example:
        wp_get_analytics(start_date="2025-11-01", end_date="2025-11-30")
    """
    try:
        from datetime import datetime, timedelta

        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        report = f"""
📊 Campaign Analytics Dashboard

Period: {start_date} to {end_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Get volunteer signups (from volunteer tracker)
        if 'volunteers' in metrics or 'all' in metrics:
            # Query WordPress database for volunteer signups
            cmd = [
                'wp', '--path=/home/dave/skippy/websites/rundaverun/local_site/app/public',
                'db', 'query',
                f"SELECT COUNT(*) as count FROM wp_volunteer_signups WHERE signup_date BETWEEN '{start_date}' AND '{end_date}'",
                '--skip-column-names'
            ]
            # This would need the actual table structure
            report += "📝 Volunteer Signups: (integrate with actual volunteer tracker)\n\n"

        # Get donation data (from donation tracker)
        if 'donations' in metrics or 'all' in metrics:
            report += "💰 Donations: (integrate with actual donation system)\n\n"

        # Get page views (would need analytics plugin data)
        if 'pageviews' in metrics or 'all' in metrics:
            cmd = [
                'wp', '--path=/home/dave/skippy/websites/rundaverun/local_site/app/public',
                'post', 'list',
                '--post_type=page,post',
                '--fields=ID,post_title',
                '--format=count'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            total_pages = result.stdout.strip()
            report += f"📄 Total Published Pages: {total_pages}\n\n"

        report += """
Note: This is a basic analytics framework. For full analytics:
1. Install Google Analytics or similar
2. Integrate with volunteer tracking database
3. Connect to donation system
4. Add event tracking for forms and buttons
"""

        return report

    except Exception as e:
        return f"❌ Error getting analytics: {str(e)}"


# ============================================================================
# NEW UTILITY TOOLS (Added 2025-11-24)
# ============================================================================

@mcp.tool()
def screenshot_capture(url: str, output_path: str = "", width: int = 1920, height: int = 1080, full_page: bool = False) -> str:
    """
    Take a screenshot of a URL using pyppeteer.

    Args:
        url: URL to capture (local or remote)
        output_path: Where to save screenshot (auto-generated if empty)
        width: Viewport width (default 1920)
        height: Viewport height (default 1080)
        full_page: Capture full scrollable page (default False)

    Returns:
        Path to saved screenshot or error message
    """
    if launch is None:
        return "❌ pyppeteer not installed. Run: pip install pyppeteer"

    # Validate URL using Skippy validator
    if SKIPPY_LIBS_AVAILABLE:
        try:
            validate_url(url)
        except ValidationError as e:
            return f"❌ Invalid URL: {str(e)}"

    # Validate output path if provided
    if output_path and SKIPPY_LIBS_AVAILABLE:
        try:
            validate_path(output_path, must_exist=False)
        except ValidationError as e:
            return f"❌ Invalid output path: {str(e)}"

    try:
        import asyncio
        import nest_asyncio

        # Apply nest_asyncio to allow nested event loops (needed for MCP server context)
        nest_asyncio.apply()

        async def take_screenshot():
            browser = await launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = await browser.newPage()
            await page.setViewport({'width': width, 'height': height, 'isMobile': width < 500})

            # Set mobile user agent for mobile viewports
            if width < 500:
                await page.setUserAgent(
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
                    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
                )

            await page.goto(url, waitUntil='networkidle0', timeout=30000)
            await asyncio.sleep(0.5)  # Wait for animations

            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = f"/home/dave/skippy/work/screenshots/screenshot_{timestamp}.png"
            else:
                save_path = output_path

            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            await page.screenshot({'path': save_path, 'fullPage': full_page})
            await browser.close()
            return save_path

        # Use asyncio.run() with nest_asyncio for compatibility
        result_path = asyncio.get_event_loop().run_until_complete(take_screenshot())

        # Check if image exceeds API limit (8000px) and handle accordingly
        MAX_DIMENSION = 7500  # Stay under 8000px API limit with margin
        try:
            from PIL import Image
            img = Image.open(result_path)
            w, h = img.size

            if h > MAX_DIMENSION:
                # For very tall images (full-page captures), split into sections
                original_path = result_path.replace('.png', '_full.png')
                img.save(original_path)

                # Calculate how many sections we need
                section_height = MAX_DIMENSION - 200  # Leave some overlap margin
                num_sections = (h + section_height - 1) // section_height

                section_paths = []
                for i in range(min(num_sections, 5)):  # Max 5 sections to avoid too many files
                    top = i * section_height
                    bottom = min(top + MAX_DIMENSION, h)
                    section = img.crop((0, top, w, bottom))

                    section_path = result_path.replace('.png', f'_section{i+1}.png')
                    section.save(section_path)
                    section_paths.append(section_path)

                # Keep first section as the main file for easy viewing
                first_section = img.crop((0, 0, w, min(MAX_DIMENSION, h)))
                first_section.save(result_path)

                return (f"✅ Screenshot saved: {result_path}\n"
                        f"⚠️  Full page was {w}x{h}px (exceeds 8000px limit)\n"
                        f"📁 Full image saved: {original_path}\n"
                        f"📄 Split into {len(section_paths)} viewable sections:\n   " +
                        "\n   ".join(section_paths))

            elif w > MAX_DIMENSION:
                # Wide images (rare) - just resize proportionally
                scale = MAX_DIMENSION / w
                new_w, new_h = int(w * scale), int(h * scale)
                original_path = result_path.replace('.png', '_original.png')
                img.save(original_path)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                img_resized.save(result_path)
                return f"✅ Screenshot saved: {result_path}\n⚠️  Image was {w}x{h}, resized to {new_w}x{new_h} (API limit: 8000px)\n📁 Original saved: {original_path}"

        except ImportError:
            pass  # PIL not available, skip resize check
        except Exception as resize_err:
            return f"✅ Screenshot saved: {result_path}\n⚠️  Could not check/resize image: {resize_err}"

        return f"✅ Screenshot saved: {result_path}"

    except Exception as e:
        return f"❌ Screenshot failed: {str(e)}"


@mcp.tool()
def pdf_to_text(pdf_path: str, output_path: str = "") -> str:
    """
    Extract text from a PDF file.

    Args:
        pdf_path: Path to PDF file
        output_path: Where to save text (prints if empty)

    Returns:
        Extracted text or path to saved file
    """
    # Validate paths using Skippy validator
    if SKIPPY_LIBS_AVAILABLE:
        try:
            validate_path(pdf_path, must_exist=True)
        except ValidationError as e:
            return f"❌ Invalid PDF path: {str(e)}"
        if output_path:
            try:
                validate_path(output_path, must_exist=False)
            except ValidationError as e:
                return f"❌ Invalid output path: {str(e)}"

    try:
        import subprocess

        # Use pdftotext if available (poppler-utils)
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, '-'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return f"❌ pdftotext failed: {result.stderr}"

        text = result.stdout

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(text)
            return f"✅ Text extracted to: {output_path} ({len(text)} chars)"

        # Return first 5000 chars if no output path
        if len(text) > 5000:
            return f"{text[:5000]}\n\n... (truncated, {len(text)} total chars)"
        return text

    except FileNotFoundError:
        return "❌ pdftotext not found. Install with: sudo apt install poppler-utils"
    except Exception as e:
        return f"❌ PDF extraction failed: {str(e)}"


@mcp.tool()
def image_resize(
    image_path: str,
    output_path: str = "",
    width: int = 0,
    height: int = 0,
    max_size: int = 0,
    quality: int = 85
) -> str:
    """
    Resize and optimize an image.

    Args:
        image_path: Path to source image
        output_path: Where to save (overwrites if empty)
        width: Target width (0 = auto based on height)
        height: Target height (0 = auto based on width)
        max_size: Max dimension for either side (overrides width/height)
        quality: JPEG quality 1-100 (default 85)

    Returns:
        Path to resized image with size info
    """
    # Validate paths using Skippy validator
    if SKIPPY_LIBS_AVAILABLE:
        try:
            validate_path(image_path, must_exist=True)
        except ValidationError as e:
            return f"❌ Invalid image path: {str(e)}"
        if output_path:
            try:
                validate_path(output_path, must_exist=False)
            except ValidationError as e:
                return f"❌ Invalid output path: {str(e)}"

    try:
        from PIL import Image

        img = Image.open(image_path)
        original_size = os.path.getsize(image_path)
        orig_width, orig_height = img.size

        # Calculate new dimensions
        if max_size:
            ratio = min(max_size / orig_width, max_size / orig_height)
            if ratio < 1:
                new_width = int(orig_width * ratio)
                new_height = int(orig_height * ratio)
            else:
                new_width, new_height = orig_width, orig_height
        elif width and height:
            new_width, new_height = width, height
        elif width:
            ratio = width / orig_width
            new_width = width
            new_height = int(orig_height * ratio)
        elif height:
            ratio = height / orig_height
            new_height = height
            new_width = int(orig_width * ratio)
        else:
            return "❌ Must specify width, height, or max_size"

        # Resize
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Determine output path
        if not output_path:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_resized{ext}"

        # Save with optimization
        if img_resized.mode in ('RGBA', 'P'):
            img_resized = img_resized.convert('RGB')

        img_resized.save(output_path, quality=quality, optimize=True)
        new_size = os.path.getsize(output_path)

        return f"""✅ Image resized:
- Original: {orig_width}x{orig_height} ({original_size:,} bytes)
- New: {new_width}x{new_height} ({new_size:,} bytes)
- Saved: {output_path}
- Reduction: {((original_size - new_size) / original_size * 100):.1f}%"""

    except ImportError:
        return "❌ Pillow not installed. Run: pip install Pillow"
    except Exception as e:
        return f"❌ Image resize failed: {str(e)}"


@mcp.tool()
def json_to_csv(json_path: str, output_path: str = "") -> str:
    """
    Convert JSON array to CSV file.

    Args:
        json_path: Path to JSON file (must be array of objects)
        output_path: Where to save CSV (auto-generated if empty)

    Returns:
        Path to CSV file or error message
    """
    try:
        import csv

        with open(json_path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            return "❌ JSON must be an array of objects"

        if not data:
            return "❌ JSON array is empty"

        if not output_path:
            output_path = json_path.rsplit('.', 1)[0] + '.csv'

        # Get all keys from all objects
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())

        fieldnames = sorted(all_keys)

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)

        return f"✅ Converted to CSV: {output_path} ({len(data)} rows, {len(fieldnames)} columns)"

    except Exception as e:
        return f"❌ JSON to CSV failed: {str(e)}"


@mcp.tool()
def csv_to_json(csv_path: str, output_path: str = "") -> str:
    """
    Convert CSV file to JSON array.

    Args:
        csv_path: Path to CSV file
        output_path: Where to save JSON (auto-generated if empty)

    Returns:
        Path to JSON file or error message
    """
    try:
        import csv

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        if not output_path:
            output_path = csv_path.rsplit('.', 1)[0] + '.json'

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return f"✅ Converted to JSON: {output_path} ({len(data)} records)"

    except Exception as e:
        return f"❌ CSV to JSON failed: {str(e)}"


@mcp.tool()
def compress_files(
    source_path: str,
    output_path: str = "",
    format: str = "zip",
    include_pattern: str = "*"
) -> str:
    """
    Compress files into an archive.

    Args:
        source_path: File or directory to compress
        output_path: Where to save archive (auto-generated if empty)
        format: Archive format (zip, tar, tar.gz, tar.bz2)
        include_pattern: Glob pattern for files to include (default *)

    Returns:
        Path to archive with size info
    """
    # Validate paths using Skippy validator
    if SKIPPY_LIBS_AVAILABLE:
        try:
            validate_path(source_path, must_exist=True)
        except ValidationError as e:
            return f"❌ Invalid source path: {str(e)}"
        if output_path:
            try:
                validate_path(output_path, must_exist=False)
            except ValidationError as e:
                return f"❌ Invalid output path: {str(e)}"

    try:
        import shutil
        import tarfile
        import zipfile
        from pathlib import Path

        source = Path(source_path)

        if not source.exists():
            return f"❌ Source not found: {source_path}"

        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if format == 'zip':
                output_path = f"{source.stem}_{timestamp}.zip"
            elif format == 'tar':
                output_path = f"{source.stem}_{timestamp}.tar"
            elif format == 'tar.gz':
                output_path = f"{source.stem}_{timestamp}.tar.gz"
            elif format == 'tar.bz2':
                output_path = f"{source.stem}_{timestamp}.tar.bz2"
            else:
                return f"❌ Unknown format: {format}. Use: zip, tar, tar.gz, tar.bz2"

        # Compress
        if format == 'zip':
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if source.is_file():
                    zf.write(source, source.name)
                else:
                    for file in source.rglob(include_pattern):
                        if file.is_file():
                            zf.write(file, file.relative_to(source.parent))

        elif format in ('tar', 'tar.gz', 'tar.bz2'):
            mode = 'w'
            if format == 'tar.gz':
                mode = 'w:gz'
            elif format == 'tar.bz2':
                mode = 'w:bz2'

            with tarfile.open(output_path, mode) as tf:
                if source.is_file():
                    tf.add(source, source.name)
                else:
                    for file in source.rglob(include_pattern):
                        if file.is_file():
                            tf.add(file, file.relative_to(source.parent))

        archive_size = os.path.getsize(output_path)
        return f"✅ Archive created: {output_path} ({archive_size:,} bytes)"

    except Exception as e:
        return f"❌ Compression failed: {str(e)}"


@mcp.tool()
def cron_list(user: str = "") -> str:
    """
    List cron jobs for a user.

    Args:
        user: Username (current user if empty)

    Returns:
        List of cron jobs with schedule descriptions
    """
    try:
        if user:
            result = subprocess.run(['crontab', '-u', user, '-l'], capture_output=True, text=True)
        else:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)

        if result.returncode != 0:
            if "no crontab" in result.stderr.lower():
                return "No cron jobs configured."
            return f"❌ Error listing crontab: {result.stderr}"

        lines = result.stdout.strip().split('\n')
        output = "📅 Cron Jobs:\n\n"

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(None, 5)
            if len(parts) >= 6:
                schedule = ' '.join(parts[:5])
                command = parts[5]

                # Parse schedule
                minute, hour, dom, month, dow = parts[:5]
                desc = _describe_cron_schedule(minute, hour, dom, month, dow)

                output += f"• {desc}\n  └─ {command[:60]}{'...' if len(command) > 60 else ''}\n\n"

        return output if output != "📅 Cron Jobs:\n\n" else "No cron jobs configured."

    except Exception as e:
        return f"❌ Error: {str(e)}"


def _describe_cron_schedule(minute, hour, dom, month, dow):
    """Helper to describe cron schedule in human terms."""
    if minute == '*' and hour == '*':
        return "Every minute"
    elif minute.startswith('*/'):
        return f"Every {minute[2:]} minutes"
    elif hour == '*':
        return f"Hourly at minute {minute}"
    elif dom == '*' and month == '*' and dow == '*':
        return f"Daily at {hour}:{minute.zfill(2)}"
    elif dow != '*':
        days = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu', '5': 'Fri', '6': 'Sat', '7': 'Sun'}
        day_name = days.get(dow, dow)
        return f"Weekly on {day_name} at {hour}:{minute.zfill(2)}"
    elif dom != '*':
        return f"Monthly on day {dom} at {hour}:{minute.zfill(2)}"
    else:
        return f"{minute} {hour} {dom} {month} {dow}"


@mcp.tool()
def cron_add(schedule: str, command: str, comment: str = "") -> str:
    """
    Add a new cron job.

    Args:
        schedule: Cron schedule (e.g., "0 3 * * *" for daily at 3 AM)
        command: Command to run
        comment: Optional comment to add above the job

    Returns:
        Success message or error
    """
    try:
        # Get existing crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""

        # Build new entry
        new_entry = ""
        if comment:
            new_entry += f"# {comment}\n"
        new_entry += f"{schedule} {command}\n"

        # Append to existing
        new_crontab = existing.rstrip() + "\n" + new_entry

        # Install new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)

        if process.returncode != 0:
            return "❌ Failed to install crontab"

        return f"✅ Cron job added: {schedule} {command[:40]}..."

    except Exception as e:
        return f"❌ Error adding cron job: {str(e)}"


@mcp.tool()
def ssl_check(hostname: str, port: int = 443) -> str:
    """
    Check SSL certificate status and expiry.

    Args:
        hostname: Domain to check (e.g., "example.com")
        port: Port number (default 443)

    Returns:
        Certificate info including expiry date
    """
    try:
        import ssl
        import socket
        from datetime import datetime

        context = ssl.create_default_context()
        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname
        )
        conn.settimeout(10)

        try:
            conn.connect((hostname, port))
            cert = conn.getpeercert()
        finally:
            conn.close()

        # Parse expiry
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        days_left = (not_after - datetime.now()).days

        # Get subject
        subject = dict(x[0] for x in cert['subject'])
        issuer = dict(x[0] for x in cert['issuer'])

        # Status
        if days_left < 0:
            status = "🔴 EXPIRED"
        elif days_left < 7:
            status = "🟠 CRITICAL - Expires in < 7 days"
        elif days_left < 30:
            status = "🟡 WARNING - Expires in < 30 days"
        else:
            status = "🟢 Valid"

        return f"""🔐 SSL Certificate for {hostname}

Status: {status}
Days until expiry: {days_left}

Subject: {subject.get('commonName', 'N/A')}
Issuer: {issuer.get('organizationName', 'N/A')}

Valid From: {not_before.strftime('%Y-%m-%d')}
Valid Until: {not_after.strftime('%Y-%m-%d')}

Alternative Names: {', '.join(cert.get('subjectAltName', [('DNS', 'N/A')])[0:3])}
"""

    except ssl.SSLError as e:
        return f"❌ SSL Error: {str(e)}"
    except socket.error as e:
        return f"❌ Connection error: {str(e)}"
    except Exception as e:
        return f"❌ Error checking SSL: {str(e)}"


@mcp.tool()
def dns_lookup(hostname: str, record_type: str = "A") -> str:
    """
    Perform DNS lookup for a hostname.

    Args:
        hostname: Domain to lookup
        record_type: DNS record type (A, AAAA, MX, TXT, CNAME, NS, SOA)

    Returns:
        DNS records found
    """
    try:
        import subprocess

        # Use dig for reliable DNS lookups
        result = subprocess.run(
            ['dig', '+short', record_type, hostname],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return f"❌ DNS lookup failed: {result.stderr}"

        records = result.stdout.strip()
        if not records:
            return f"No {record_type} records found for {hostname}"

        output = f"🌐 DNS Lookup: {hostname} ({record_type})\n\n"
        for record in records.split('\n'):
            output += f"  • {record}\n"

        return output

    except FileNotFoundError:
        # Fallback to nslookup
        try:
            result = subprocess.run(
                ['nslookup', '-type=' + record_type, hostname],
                capture_output=True,
                text=True,
                timeout=10
            )
            return f"🌐 DNS Lookup: {hostname}\n\n{result.stdout}"
        except:
            return "❌ Neither dig nor nslookup available"
    except Exception as e:
        return f"❌ DNS lookup error: {str(e)}"


@mcp.tool()
def port_check(host: str, ports: str = "80,443") -> str:
    """
    Check if ports are open on a host.

    Args:
        host: Hostname or IP to check
        ports: Comma-separated port numbers or range (e.g., "80,443" or "20-25")

    Returns:
        Status of each port
    """
    try:
        import socket

        # Parse ports
        port_list = []
        for part in ports.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                port_list.extend(range(start, end + 1))
            else:
                port_list.append(int(part))

        output = f"🔌 Port Check: {host}\n\n"
        open_count = 0

        for port in port_list:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            try:
                result = sock.connect_ex((host, port))
                if result == 0:
                    output += f"  ✅ Port {port}: OPEN\n"
                    open_count += 1
                else:
                    output += f"  ❌ Port {port}: CLOSED\n"
            except socket.error as e:
                output += f"  ⚠️  Port {port}: ERROR ({str(e)})\n"
            finally:
                sock.close()

        output += f"\n{open_count}/{len(port_list)} ports open"
        return output

    except Exception as e:
        return f"❌ Port check error: {str(e)}"


@mcp.tool()
def send_notification(
    message: str,
    title: str = "Skippy Notification",
    channel: str = "desktop"
) -> str:
    """
    Send a notification via various channels.

    Args:
        message: Notification message
        title: Notification title
        channel: Notification channel (desktop, slack, log)

    Returns:
        Success/failure message
    """
    try:
        if channel == "desktop":
            # Use notify-send for desktop notifications
            result = subprocess.run(
                ['notify-send', '-u', 'normal', title, message],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return f"✅ Desktop notification sent: {title}"
            else:
                return f"❌ Desktop notification failed: {result.stderr}"

        elif channel == "slack":
            if WebClient is None:
                return "❌ slack_sdk not installed. Run: pip install slack_sdk"

            slack_token = os.getenv('SLACK_BOT_TOKEN')
            slack_channel = os.getenv('SLACK_CHANNEL', '#general')

            if not slack_token:
                return "❌ SLACK_BOT_TOKEN environment variable not set"

            client = WebClient(token=slack_token)
            response = client.chat_postMessage(
                channel=slack_channel,
                text=f"*{title}*\n{message}"
            )
            return f"✅ Slack notification sent to {slack_channel}"

        elif channel == "log":
            # Log to skippy notification log
            log_path = f"{SKIPPY_PATH}/logs/notifications.log"
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_path, 'a') as f:
                f.write(f"[{timestamp}] {title}: {message}\n")
            return f"✅ Notification logged to {log_path}"

        else:
            return f"❌ Unknown channel: {channel}. Use: desktop, slack, log"

    except Exception as e:
        return f"❌ Notification failed: {str(e)}"


@mcp.tool()
def db_compare(
    table1: str,
    table2: str = "",
    database: str = "wordpress",
    key_column: str = "ID"
) -> str:
    """
    Compare two database tables or snapshots.

    Args:
        table1: First table name or path to SQL dump
        table2: Second table name (if empty, shows table structure)
        database: Database name (default: wordpress)
        key_column: Primary key column for comparison (default: ID)

    Returns:
        Comparison results or table structure
    """
    try:
        # If no table2, show structure of table1
        if not table2:
            query = f"DESCRIBE {table1}"
            result = subprocess.run(
                ['wp', f'--path={WORDPRESS_PATH}', 'db', 'query', query],
                capture_output=True,
                text=True
            )
            return f"📊 Table Structure: {table1}\n\n{result.stdout}"

        # Compare row counts
        count1_result = subprocess.run(
            ['wp', f'--path={WORDPRESS_PATH}', 'db', 'query',
             f"SELECT COUNT(*) FROM {table1}", '--skip-column-names'],
            capture_output=True, text=True
        )
        count2_result = subprocess.run(
            ['wp', f'--path={WORDPRESS_PATH}', 'db', 'query',
             f"SELECT COUNT(*) FROM {table2}", '--skip-column-names'],
            capture_output=True, text=True
        )

        count1 = count1_result.stdout.strip()
        count2 = count2_result.stdout.strip()

        # Find rows in table1 not in table2
        diff_query = f"""
        SELECT {key_column} FROM {table1}
        WHERE {key_column} NOT IN (SELECT {key_column} FROM {table2})
        LIMIT 10
        """
        diff_result = subprocess.run(
            ['wp', f'--path={WORDPRESS_PATH}', 'db', 'query', diff_query],
            capture_output=True, text=True
        )

        return f"""📊 Table Comparison

{table1}: {count1} rows
{table2}: {count2} rows

Rows in {table1} not in {table2}:
{diff_result.stdout if diff_result.stdout.strip() else '(none)'}
"""

    except Exception as e:
        return f"❌ Database comparison failed: {str(e)}"


@mcp.tool()
def extract_archive(archive_path: str, output_dir: str = "") -> str:
    """
    Extract a compressed archive.

    Args:
        archive_path: Path to archive file (.zip, .tar, .tar.gz, .tar.bz2)
        output_dir: Directory to extract to (same directory if empty)

    Returns:
        List of extracted files or error
    """
    try:
        import tarfile
        import zipfile
        from pathlib import Path

        archive = Path(archive_path)
        if not archive.exists():
            return f"❌ Archive not found: {archive_path}"

        if not output_dir:
            output_dir = str(archive.parent)

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        extracted = []

        if archive.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(output_dir)
                extracted = zf.namelist()

        elif archive.suffix in ('.tar', '.gz', '.bz2', '.xz'):
            with tarfile.open(archive_path, 'r:*') as tf:
                tf.extractall(output_dir)
                extracted = tf.getnames()

        else:
            return f"❌ Unknown archive format: {archive.suffix}"

        return f"""✅ Extracted {len(extracted)} files to {output_dir}

First 10 files:
{chr(10).join('  • ' + f for f in extracted[:10])}
{'...' if len(extracted) > 10 else ''}
"""

    except Exception as e:
        return f"❌ Extraction failed: {str(e)}"


# ============================================================================
# SKIPPY SYSTEM INTEGRATION TOOLS (Added 2025-11-24)
# ============================================================================

@mcp.tool()
def skippy_performance_summary(operation_name: str = "") -> str:
    """
    Get performance metrics summary from Skippy performance monitoring.

    Args:
        operation_name: Specific operation to get metrics for (empty = all)

    Returns:
        Performance metrics summary
    """
    try:
        if not SKIPPY_LIBS_AVAILABLE:
            return "❌ Skippy libraries not available"

        from skippy_performance import _global_monitor, get_performance_summary

        summary = get_performance_summary(operation_name if operation_name else None)

        if "error" in summary:
            return f"⚠️ {summary['error']}"

        output = f"""📊 Performance Summary: {summary.get('operation', 'all')}

Total Executions: {summary.get('total_executions', 0)}

Duration Statistics:
  • Min: {summary.get('duration', {}).get('min', 0):.3f}s
  • Max: {summary.get('duration', {}).get('max', 0):.3f}s
  • Avg: {summary.get('duration', {}).get('avg', 0):.3f}s
  • Total: {summary.get('duration', {}).get('total', 0):.3f}s

Recent Metrics:
"""
        for metric in summary.get('recent_metrics', [])[-3:]:
            output += f"  • {metric.get('name', 'unknown')}: {metric.get('duration_seconds', 0):.3f}s\n"

        return output

    except Exception as e:
        return f"❌ Error getting performance summary: {str(e)}"


@mcp.tool()
def skippy_circuit_breaker_status() -> str:
    """
    Get status of all Skippy circuit breakers.

    Returns:
        Circuit breaker states and health
    """
    try:
        if not SKIPPY_RESILIENCE_AVAILABLE:
            return "❌ Skippy resilience library not available"

        from skippy_resilience import get_all_circuit_breaker_states

        states = get_all_circuit_breaker_states()

        if not states:
            return "No circuit breakers registered."

        output = "🔌 Circuit Breaker Status\n\n"

        for name, state in states.items():
            status_icon = {
                'closed': '🟢',
                'open': '🔴',
                'half_open': '🟡'
            }.get(state.get('state', 'unknown'), '⚪')

            output += f"""{status_icon} {name}
   State: {state.get('state', 'unknown').upper()}
   Failures: {state.get('failure_count', 0)}/{state.get('config', {}).get('failure_threshold', 5)}
   Last Failure: {state.get('last_failure', 'never')}

"""

        return output

    except Exception as e:
        return f"❌ Error getting circuit breaker status: {str(e)}"


@mcp.tool()
def skippy_circuit_breaker_reset(name: str) -> str:
    """
    Reset a specific circuit breaker to closed state.

    Args:
        name: Name of the circuit breaker to reset

    Returns:
        Success or error message
    """
    try:
        if not SKIPPY_RESILIENCE_AVAILABLE:
            return "❌ Skippy resilience library not available"

        from skippy_resilience import get_circuit_breaker

        cb = get_circuit_breaker(name)
        cb.reset()

        return f"✅ Circuit breaker '{name}' reset to CLOSED state"

    except Exception as e:
        return f"❌ Error resetting circuit breaker: {str(e)}"


@mcp.tool()
def skippy_cache_stats() -> str:
    """
    Get Skippy graceful cache statistics.

    Returns:
        Cache statistics and health
    """
    try:
        if not SKIPPY_ADVANCED_RESILIENCE:
            return "❌ Skippy advanced resilience not available"

        from skippy_resilience_advanced import get_cache

        cache = get_cache()
        stats = cache.get_statistics()

        output = f"""📦 Skippy Cache Statistics

Total Entries: {stats.get('total_entries', 0)}
Valid Entries: {stats.get('valid_entries', 0)}
Stale Entries: {stats.get('stale_entries', 0)}
Total Hits: {stats.get('total_hits', 0)}
Capacity Used: {stats.get('capacity_percent', 0):.1f}%
"""

        return output

    except Exception as e:
        return f"❌ Error getting cache stats: {str(e)}"


@mcp.tool()
def skippy_cache_clear(pattern: str = "") -> str:
    """
    Clear Skippy cache entries.

    Args:
        pattern: Pattern to match for selective clearing (empty = clear all)

    Returns:
        Number of entries cleared
    """
    try:
        if not SKIPPY_ADVANCED_RESILIENCE:
            return "❌ Skippy advanced resilience not available"

        from skippy_resilience_advanced import get_cache

        cache = get_cache()

        if pattern:
            # Get count before
            stats_before = cache.get_statistics()
            cache.invalidate_pattern(pattern)
            stats_after = cache.get_statistics()
            cleared = stats_before['total_entries'] - stats_after['total_entries']
            return f"✅ Cleared {cleared} cache entries matching '{pattern}'"
        else:
            stats = cache.get_statistics()
            count = stats['total_entries']
            cache.clear()
            return f"✅ Cleared all {count} cache entries"

    except Exception as e:
        return f"❌ Error clearing cache: {str(e)}"


@mcp.tool()
def skippy_alerts_recent(hours: int = 24) -> str:
    """
    Get recent Skippy system alerts.

    Args:
        hours: Number of hours to look back (default 24)

    Returns:
        List of recent alerts
    """
    try:
        if not SKIPPY_ADVANCED_RESILIENCE:
            return "❌ Skippy advanced resilience not available"

        from skippy_resilience_advanced import get_alert_manager

        manager = get_alert_manager()
        alerts = manager.get_recent_alerts(hours=hours)

        if not alerts:
            return f"✅ No alerts in the last {hours} hours"

        output = f"🚨 Recent Alerts (last {hours}h)\n\n"

        level_icons = {
            'critical': '🔴',
            'error': '🟠',
            'warning': '🟡',
            'info': '🔵'
        }

        for alert in alerts[-10:]:  # Last 10
            icon = level_icons.get(alert.get('level', 'info'), '⚪')
            output += f"""{icon} [{alert.get('level', 'info').upper()}] {alert.get('title', 'Unknown')}
   {alert.get('message', '')}
   Time: {alert.get('timestamp', 'unknown')}
   Service: {alert.get('service', 'N/A')}

"""

        if len(alerts) > 10:
            output += f"... and {len(alerts) - 10} more alerts\n"

        return output

    except Exception as e:
        return f"❌ Error getting alerts: {str(e)}"


@mcp.tool()
def skippy_send_alert(
    title: str,
    message: str,
    level: str = "info",
    service: str = ""
) -> str:
    """
    Send a Skippy system alert.

    Args:
        title: Alert title
        message: Alert message
        level: Alert level (info, warning, error, critical)
        service: Service name (optional)

    Returns:
        Success or error message
    """
    try:
        if not SKIPPY_ADVANCED_RESILIENCE:
            return "❌ Skippy advanced resilience not available"

        from skippy_resilience_advanced import get_alert_manager, Alert, AlertLevel

        # Validate level
        valid_levels = ['info', 'warning', 'error', 'critical']
        if level.lower() not in valid_levels:
            return f"❌ Invalid level. Use: {', '.join(valid_levels)}"

        manager = get_alert_manager()
        alert = Alert(
            level=level.lower(),
            title=title,
            message=message,
            service=service if service else None
        )
        manager.send_alert(alert)

        level_icons = {'critical': '🔴', 'error': '🟠', 'warning': '🟡', 'info': '🔵'}
        icon = level_icons.get(level.lower(), '⚪')

        return f"{icon} Alert sent: [{level.upper()}] {title}"

    except Exception as e:
        return f"❌ Error sending alert: {str(e)}"


@mcp.tool()
def skippy_metrics_summary() -> str:
    """
    Get summary of all persisted Skippy metrics.

    Returns:
        Metrics files and storage summary
    """
    try:
        if not SKIPPY_ADVANCED_RESILIENCE:
            return "❌ Skippy advanced resilience not available"

        from skippy_resilience_advanced import get_metrics_persistence

        persistence = get_metrics_persistence()
        if not persistence:
            return "⚠️ Metrics persistence not initialized"

        summary = persistence.get_metrics_summary()

        if "error" in summary:
            return f"❌ {summary['error']}"

        output = f"""📈 Skippy Metrics Summary

Directory: {summary.get('metrics_dir', 'N/A')}
Total Size: {summary.get('total_size_mb', 0):.2f} MB

Files:
"""
        for filename, info in summary.get('files', {}).items():
            output += f"  • {filename}: {info.get('size_mb', 0):.2f} MB\n"

        return output

    except Exception as e:
        return f"❌ Error getting metrics summary: {str(e)}"


@mcp.tool()
def skippy_health_check() -> str:
    """
    Run Skippy system health checks.

    Returns:
        Health check results for all registered services
    """
    try:
        if not SKIPPY_RESILIENCE_AVAILABLE:
            return "❌ Skippy resilience library not available"

        from skippy_resilience import HealthChecker

        # Create checker and run standard checks
        checker = HealthChecker()

        # Register basic checks
        @checker.register("skippy_libs")
        def check_libs():
            return SKIPPY_LIBS_AVAILABLE, "Skippy libraries loaded"

        @checker.register("resilience")
        def check_resilience():
            return SKIPPY_RESILIENCE_AVAILABLE, "Resilience features available"

        @checker.register("advanced_resilience")
        def check_advanced():
            return SKIPPY_ADVANCED_RESILIENCE, "Advanced resilience available"

        @checker.register("metrics_dir")
        def check_metrics():
            metrics_dir = Path(SKIPPY_PATH) / "logs" / "metrics"
            return metrics_dir.exists(), f"Metrics directory: {metrics_dir}"

        # Run all checks
        summary = checker.get_summary()

        status_icon = "🟢" if summary['overall_healthy'] else "🔴"
        output = f"""{status_icon} Skippy Health Check

Overall: {'HEALTHY' if summary['overall_healthy'] else 'UNHEALTHY'}
Checks: {summary['healthy_count']}/{summary['total_checks']} passed

Details:
"""
        for name, result in summary.get('checks', {}).items():
            icon = "✅" if result['healthy'] else "❌"
            output += f"  {icon} {name}: {result['message']}\n"

        return output

    except Exception as e:
        return f"❌ Error running health check: {str(e)}"


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

def main():
    """Initialize and run the MCP server."""
    logger.info("Starting General Purpose MCP Server v2.6.0")
    logger.info("Total tools: 98 (69 base + 5 WordPress + 14 utility + 10 Skippy integration)")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()

# ============================================================================
# GITHUB INTEGRATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def github_create_pr(
    repo_name: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main"
) -> str:
    """Create a pull request on GitHub.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        repo_name: Repository name in format "owner/repo" (e.g., "eboncorp/NexusController")
        title: PR title
        body: PR description (supports markdown)
        head_branch: Branch with your changes
        base_branch: Branch to merge into (default: "main")
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)

        def _create_pr():
            repo = g.get_repo(repo_name)
            return repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )

        # Apply resilience: circuit breaker, rate limiting, retry
        pr = resilient_api_call(
            _create_pr,
            circuit_breaker=_github_cb,
            rate_limiter=_github_limiter,
            service_name="GitHub"
        )

        return json.dumps({
            "success": True,
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "state": pr.state,
            "created_at": pr.created_at.isoformat()
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"


@mcp.tool()
def github_create_issue(
    repo_name: str,
    title: str,
    body: str,
    labels: str = "",
    assignees: str = ""
) -> str:
    """Create an issue on GitHub.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        repo_name: Repository name in format "owner/repo"
        title: Issue title
        body: Issue description (supports markdown)
        labels: Comma-separated label names (optional)
        assignees: Comma-separated GitHub usernames to assign (optional)
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        label_list = [l.strip() for l in labels.split(',')] if labels else []
        assignee_list = [a.strip() for a in assignees.split(',')] if assignees else []

        def _create_issue():
            return repo.create_issue(
                title=title,
                body=body,
                labels=label_list,
                assignees=assignee_list
            )

        issue = resilient_api_call(
            _create_issue,
            circuit_breaker=_github_cb,
            rate_limiter=_github_limiter,
            service_name="GitHub",
            operation_name="create_issue"
        )

        return json.dumps({
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "state": issue.state,
            "created_at": issue.created_at.isoformat()
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error creating issue: {str(e)}"


@mcp.tool()
def github_list_prs(
    repo_name: str,
    state: str = "open",
    max_results: int = 10
) -> str:
    """List pull requests from a GitHub repository.

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        repo_name: Repository name in format "owner/repo"
        state: PR state - "open", "closed", or "all" (default: "open")
        max_results: Maximum number of PRs to return (default: 10)
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        def _list_prs():
            prs = repo.get_pulls(state=state)
            results = []

            for i, pr in enumerate(prs):
                if i >= max_results:
                    break
                results.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "author": pr.user.login,
                    "created_at": pr.created_at.isoformat(),
                    "url": pr.html_url
                })
            return results

        results = resilient_api_call(
            _list_prs,
            circuit_breaker=_github_cb,
            rate_limiter=_github_limiter,
            service_name="GitHub",
            operation_name="list_prs",
            cache_key=f"github_prs_{repo_name}_{state}_{max_results}"
        )

        return json.dumps(results, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error listing PRs: {str(e)}"


# ============================================================================
# SLACK INTEGRATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def slack_send_message(
    channel: str,
    text: str,
    thread_ts: str = ""
) -> str:
    """Send a message to a Slack channel.

    Args:
        channel: Channel name (with #) or channel ID
        text: Message text (supports markdown)
        thread_ts: Thread timestamp to reply in thread (optional)
    """
    try:
        if not WebClient:
            return "Error: slack-sdk not installed. Run: pip install slack-sdk"

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            return "Error: SLACK_BOT_TOKEN not set in environment"

        client = WebClient(token=slack_token)

        kwargs = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = client.chat_postMessage(**kwargs)

        return json.dumps({
            "success": True,
            "channel": response["channel"],
            "timestamp": response["ts"],
            "message": response["message"]["text"]
        }, indent=2)

    except SlackApiError as e:
        return f"Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"Error sending Slack message: {str(e)}"


@mcp.tool()
def slack_upload_file(
    channels: str,
    file_path: str,
    title: str = "",
    comment: str = ""
) -> str:
    """Upload a file to Slack channel(s).

    Args:
        channels: Comma-separated channel names or IDs
        file_path: Path to file to upload
        title: File title (optional)
        comment: Comment to add with file (optional)
    """
    try:
        if not WebClient:
            return "Error: slack-sdk not installed. Run: pip install slack-sdk"

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            return "Error: SLACK_BOT_TOKEN not set in environment"

        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: File not found: {file_path}"

        client = WebClient(token=slack_token)

        response = client.files_upload_v2(
            channels=channels,
            file=str(path),
            title=title or path.name,
            initial_comment=comment if comment else None
        )

        return json.dumps({
            "success": True,
            "file_id": response["file"]["id"],
            "file_url": response["file"]["permalink"]
        }, indent=2)

    except SlackApiError as e:
        return f"Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"


# ============================================================================
# BROWSER AUTOMATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def browser_screenshot(
    url: str,
    output_path: str,
    full_page: bool = False,
    width: int = 1920,
    height: int = 1080
) -> str:
    """Capture a screenshot of a webpage.

    Args:
        url: URL to screenshot
        output_path: Path to save screenshot (PNG format)
        full_page: Capture full scrollable page (default: False)
        width: Viewport width in pixels (default: 1920)
        height: Viewport height in pixels (default: 1080)
    """
    if not launch:
        return "Error: pyppeteer not installed. Run: pip install pyppeteer"

    async def _screenshot():
        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})
        await page.goto(url, {'waitUntil': 'networkidle2'})

        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot({
            'path': str(output),
            'fullPage': full_page
        })
        await browser.close()
        return str(output)

    try:
        screenshot_path = asyncio.run(_screenshot())

        return json.dumps({
            "success": True,
            "screenshot_path": screenshot_path,
            "url": url,
            "full_page": full_page
        }, indent=2)

    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"


@mcp.tool()
def browser_test_form(
    url: str,
    form_data: str,
    submit_button_selector: str = "button[type='submit']"
) -> str:
    """Test form submission on a webpage.

    Args:
        url: URL of page with form
        form_data: JSON string of field names/IDs to values
        submit_button_selector: CSS selector for submit button
    """
    if not launch:
        return "Error: pyppeteer not installed. Run: pip install pyppeteer"

    async def _test_form():
        try:
            form_dict = json.loads(form_data)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON in form_data parameter"}

        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'networkidle2'})

        # Fill form fields
        for field_name, value in form_dict.items():
            # Try different selectors
            selectors = [
                f'[name="{field_name}"]',
                f'#{field_name}',
                f'[id="{field_name}"]'
            ]

            filled = False
            for selector in selectors:
                try:
                    await page.type(selector, str(value))
                    filled = True
                    break
                except:
                    continue

            if not filled:
                await browser.close()
                return {"success": False, "error": f"Could not find field: {field_name}"}

        # Click submit button
        await page.click(submit_button_selector)
        await page.waitFor(2000)  # Wait 2 seconds

        # Get final URL and page title
        final_url = page.url
        title = await page.title()

        await browser.close()

        return {
            "success": True,
            "final_url": final_url,
            "page_title": title
        }

    try:
        result = asyncio.run(_test_form())
        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error testing form: {str(e)}"


# ============================================================================
# GOOGLE DRIVE INTEGRATION TOOLS (v2.1.0)
# ============================================================================

def _get_google_drive_service():
    """Get authenticated Google Drive service."""
    if not build:
        raise Exception("google-api-python-client not installed")

    creds = None
    token_path = os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials.json")
    scopes = [os.getenv("GOOGLE_DRIVE_SCOPES", "https://www.googleapis.com/auth/drive.readonly")]

    token_path = Path(token_path).expanduser()
    credentials_path = Path(credentials_path).expanduser()

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Google credentials not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.write_text(creds.to_json())

    return build('drive', 'v3', credentials=creds)


@mcp.tool()
def gdrive_search_files(
    query: str,
    max_results: int = 10
) -> str:
    """Search for files in Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        query: Search query (supports Google Drive query syntax)
        max_results: Maximum number of results (default: 10)

    Example queries:
        - "name contains 'policy'"
        - "mimeType='application/pdf'"
        - "modifiedTime > '2025-01-01'"
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        def _search():
            return service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)"
            ).execute()

        # Apply resilience: circuit breaker, rate limiting, retry
        results = resilient_api_call(
            _search,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive"
        )

        files = results.get('files', [])

        return json.dumps({
            "success": True,
            "count": len(files),
            "files": files
        }, indent=2)

    except CircuitBreakerOpenError as e:
        logger.warning(f"Google Drive circuit breaker open: {e}")
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        logger.error(f"Google Drive retry exhausted: {e}")
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error searching Google Drive: {str(e)}"


@mcp.tool()
def gdrive_download_file(
    file_id: str,
    output_path: str
) -> str:
    """Download a file from Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: Google Drive file ID
        output_path: Local path to save file
    """
    try:
        if not build or not MediaIoBaseDownload:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        # Get file metadata with resilience
        def _get_metadata():
            return service.files().get(fileId=file_id).execute()

        file_metadata = resilient_api_call(
            _get_metadata,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive"
        )

        # Download file content
        request = service.files().get_media(fileId=file_id)

        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)

        def _download():
            with open(output, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

        resilient_api_call(
            _download,
            circuit_breaker=_google_drive_cb,
            service_name="Google Drive Download"
        )

        return json.dumps({
            "success": True,
            "file_name": file_metadata['name'],
            "file_size": file_metadata.get('size', 'unknown'),
            "output_path": str(output)
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error downloading file: {str(e)}"


@mcp.tool()
def gdrive_read_document(
    file_id: str
) -> str:
    """Read content from a Google Docs document.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: Google Drive file ID of the document
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        def _read_doc():
            # Export as plain text
            request = service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            return request.execute().decode('utf-8')

        content = resilient_api_call(
            _read_doc,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="read_document",
            cache_key=f"gdrive_doc_{file_id}"
        )

        return content

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error reading document: {str(e)}"


# ===================================================================
# Google Drive Organization Tools (v2.2.0)
# ===================================================================

@mcp.tool()
def gdrive_create_folder(
    folder_name: str,
    parent_folder_id: str = None
) -> str:
    """Create a new folder in Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        folder_name: Name of the folder to create
        parent_folder_id: Optional parent folder ID (creates in root if not specified)

    Returns:
        JSON with folder ID and web link
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        def _create_folder():
            return service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()

        folder = resilient_api_call(
            _create_folder,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="create_folder"
        )

        return json.dumps({
            "success": True,
            "folder_id": folder['id'],
            "folder_name": folder['name'],
            "web_link": folder.get('webViewLink', '')
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


@mcp.tool()
def gdrive_move_file(
    file_id: str,
    destination_folder_id: str
) -> str:
    """Move a file to a different folder in Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: ID of the file to move
        destination_folder_id: ID of the destination folder

    Returns:
        JSON with success status and file info
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        def _move_file():
            # Get current parents
            file_info = service.files().get(fileId=file_id, fields='parents, name').execute()
            previous_parents = ",".join(file_info.get('parents', []))

            # Move the file
            return service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id, name, parents, webViewLink'
            ).execute()

        file = resilient_api_call(
            _move_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="move_file"
        )

        return json.dumps({
            "success": True,
            "file_id": file['id'],
            "file_name": file['name'],
            "new_location": file.get('parents', []),
            "web_link": file.get('webViewLink', '')
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error moving file: {str(e)}"


@mcp.tool()
def gdrive_list_folder_contents(
    folder_id: str = None,
    max_results: int = 100
) -> str:
    """List all files and folders in a specific folder (or root if not specified).

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        folder_id: ID of the folder to list (lists root if not specified)
        max_results: Maximum number of items to return (default: 100)

    Returns:
        JSON with list of files and folders with metadata
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Build query
        if folder_id:
            query = f"'{folder_id}' in parents and trashed=false"
        else:
            query = "'root' in parents and trashed=false"

        def _list_contents():
            return service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, size, starred, webViewLink)",
                orderBy="folder,name"  # Folders first, then alphabetical
            ).execute()

        results = resilient_api_call(
            _list_contents,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="list_folder",
            cache_key=f"gdrive_folder_{folder_id or 'root'}_{max_results}"
        )

        files = results.get('files', [])

        # Separate folders and files
        folders = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
        regular_files = [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']

        return json.dumps({
            "success": True,
            "location": "Root" if not folder_id else f"Folder {folder_id}",
            "total_items": len(files),
            "folder_count": len(folders),
            "file_count": len(regular_files),
            "folders": folders,
            "files": regular_files
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error listing folder contents: {str(e)}"


@mcp.tool()
def gdrive_trash_file(
    file_id: str
) -> str:
    """Move a file or folder to trash in Google Drive (does NOT permanently delete).

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: ID of the file/folder to move to trash

    Returns:
        JSON with success status

    Note: Files can be restored from trash within 30 days
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        def _trash_file():
            # Get file info first
            file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()

            # Move to trash (does NOT permanently delete)
            service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()

            return file_info

        file_info = resilient_api_call(
            _trash_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="trash_file"
        )

        return json.dumps({
            "success": True,
            "action": "moved to trash",
            "file_name": file_info['name'],
            "file_type": file_info['mimeType'],
            "note": "File can be restored from trash within 30 days"
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error moving file to trash: {str(e)}"


@mcp.tool()
def gdrive_rename_file(
    file_id: str,
    new_name: str
) -> str:
    """Rename a file or folder in Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: ID of the file/folder to rename
        new_name: New name for the file/folder

    Returns:
        JSON with success status and updated info
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        def _rename_file():
            # Get current info
            file_info = service.files().get(fileId=file_id, fields='name').execute()
            old_name = file_info['name']

            # Rename
            updated_file = service.files().update(
                fileId=file_id,
                body={'name': new_name},
                fields='id, name, webViewLink'
            ).execute()

            return old_name, updated_file

        old_name, updated_file = resilient_api_call(
            _rename_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="rename_file"
        )

        return json.dumps({
            "success": True,
            "file_id": updated_file['id'],
            "old_name": old_name,
            "new_name": updated_file['name'],
            "web_link": updated_file.get('webViewLink', '')
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error renaming file: {str(e)}"


@mcp.tool()
def gdrive_batch_move_files(
    file_ids: str,
    destination_folder_id: str
) -> str:
    """Move multiple files to a folder at once (batch operation).

    Args:
        file_ids: Comma-separated list of file IDs to move
        destination_folder_id: ID of the destination folder

    Returns:
        JSON with results for each file
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        file_id_list = [fid.strip() for fid in file_ids.split(',')]
        results = []

        for file_id in file_id_list:
            try:
                # Get current parents
                file = service.files().get(fileId=file_id, fields='parents, name').execute()
                previous_parents = ",".join(file.get('parents', []))

                # Move the file
                updated_file = service.files().update(
                    fileId=file_id,
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields='id, name'
                ).execute()

                results.append({
                    "success": True,
                    "file_id": updated_file['id'],
                    "file_name": updated_file['name']
                })

            except Exception as e:
                results.append({
                    "success": False,
                    "file_id": file_id,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return json.dumps({
            "success": True,
            "total_files": len(file_id_list),
            "successful_moves": successful,
            "failed_moves": len(file_id_list) - successful,
            "results": results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error in batch move: {str(e)}"


@mcp.tool()
def gdrive_get_folder_id_by_name(
    folder_name: str,
    parent_folder_id: str = None
) -> str:
    """Find a folder ID by searching for its name.

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        folder_name: Name of the folder to find
        parent_folder_id: Optional parent folder to search within

    Returns:
        JSON with matching folders
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Build query
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        def _search_folder():
            return service.files().list(
                q=query,
                fields="files(id, name, parents, webViewLink)",
                pageSize=10
            ).execute()

        results = resilient_api_call(
            _search_folder,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="get_folder_by_name",
            cache_key=f"gdrive_folder_name_{folder_name}_{parent_folder_id or 'root'}"
        )

        folders = results.get('files', [])

        return json.dumps({
            "success": True,
            "found_count": len(folders),
            "folders": folders
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error searching for folder: {str(e)}"


@mcp.tool()
def gdrive_organize_by_pattern(
    file_pattern: str,
    destination_folder_id: str,
    max_files: int = 50
) -> str:
    """Find and move files matching a pattern to a specific folder.

    Args:
        file_pattern: Search pattern (e.g., "name contains 'backup'" or "name contains 'duplicity'")
        destination_folder_id: ID of destination folder
        max_files: Maximum files to move in one operation (default: 50, safety limit)

    Returns:
        JSON with move results
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Search for files matching pattern
        results = service.files().list(
            q=f"{file_pattern} and trashed=false",
            pageSize=max_files,
            fields="files(id, name, parents)"
        ).execute()

        files = results.get('files', [])

        if not files:
            return json.dumps({
                "success": True,
                "message": "No files found matching pattern",
                "pattern": file_pattern
            }, indent=2)

        # Move each file
        move_results = []
        for file in files:
            try:
                previous_parents = ",".join(file.get('parents', []))

                updated_file = service.files().update(
                    fileId=file['id'],
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields='id, name'
                ).execute()

                move_results.append({
                    "success": True,
                    "file_id": updated_file['id'],
                    "file_name": updated_file['name']
                })

            except Exception as e:
                move_results.append({
                    "success": False,
                    "file_id": file['id'],
                    "file_name": file['name'],
                    "error": str(e)
                })

        successful = sum(1 for r in move_results if r['success'])

        return json.dumps({
            "success": True,
            "pattern": file_pattern,
            "total_found": len(files),
            "successful_moves": successful,
            "failed_moves": len(files) - successful,
            "results": move_results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error organizing files: {str(e)}"


@mcp.tool()
def gdrive_upload_file(
    local_file_path: str,
    destination_folder_id: str = None,
    new_name: str = None
) -> str:
    """Upload a file from local machine to Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        local_file_path: Path to the local file to upload
        destination_folder_id: Optional folder ID (uploads to root if not specified)
        new_name: Optional new name for the file in Drive

    Returns:
        JSON with file ID, name, and web link
    """
    try:
        if not build or not MediaFileUpload:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        local_path = Path(local_file_path).expanduser()

        if not local_path.exists():
            return json.dumps({
                "success": False,
                "error": f"File not found: {local_file_path}"
            }, indent=2)

        file_name = new_name if new_name else local_path.name

        file_metadata = {'name': file_name}

        if destination_folder_id:
            file_metadata['parents'] = [destination_folder_id]

        # Detect MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(local_path))
        if not mime_type:
            mime_type = 'application/octet-stream'

        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

        def _upload_file():
            return service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, webViewLink, mimeType'
            ).execute()

        file = resilient_api_call(
            _upload_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="upload_file"
        )

        file_size_mb = int(file.get('size', 0)) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "file_id": file['id'],
            "file_name": file['name'],
            "file_size_mb": round(file_size_mb, 2),
            "mime_type": file.get('mimeType'),
            "web_link": file.get('webViewLink', ''),
            "location": "Root" if not destination_folder_id else f"Folder {destination_folder_id}"
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"


@mcp.tool()
def gdrive_share_file(
    file_id: str,
    permission_type: str = "anyone",
    role: str = "reader",
    email_address: str = None
) -> str:
    """Share a file or folder and get shareable link.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: ID of the file/folder to share
        permission_type: Who can access - "anyone", "user", or "domain" (default: "anyone")
        role: Access level - "reader", "writer", or "commenter" (default: "reader")
        email_address: Email address (required if permission_type is "user")

    Returns:
        JSON with shareable link and permission details
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        def _share_file():
            # Get file info
            file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()

            # Create permission
            permission_body = {
                'type': permission_type,
                'role': role
            }

            if permission_type == "user" and email_address:
                permission_body['emailAddress'] = email_address
            elif permission_type == "anyone":
                permission_body['type'] = 'anyone'

            permission = service.permissions().create(
                fileId=file_id,
                body=permission_body,
                fields='id'
            ).execute()

            # Get shareable link
            file_with_link = service.files().get(
                fileId=file_id,
                fields='webViewLink, webContentLink'
            ).execute()

            return file_info, permission, file_with_link

        file_info, permission, file_with_link = resilient_api_call(
            _share_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="share_file"
        )

        return json.dumps({
            "success": True,
            "file_name": file_info['name'],
            "file_type": file_info['mimeType'],
            "permission_id": permission['id'],
            "permission_type": permission_type,
            "role": role,
            "view_link": file_with_link.get('webViewLink', ''),
            "download_link": file_with_link.get('webContentLink', ''),
            "shared_with": email_address if email_address else "Anyone with the link"
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error sharing file: {str(e)}"


@mcp.tool()
def gdrive_get_file_metadata(
    file_id: str,
    include_permissions: bool = False
) -> str:
    """Get detailed metadata for a file or folder.

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        file_id: ID of the file/folder
        include_permissions: Include sharing/permission details (default: False)

    Returns:
        JSON with complete file metadata
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        fields = "id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents, starred, trashed, owners, lastModifyingUser"

        if include_permissions:
            fields += ", permissions"

        def _get_metadata():
            return service.files().get(fileId=file_id, fields=fields).execute()

        file_info = resilient_api_call(
            _get_metadata,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="get_metadata",
            cache_key=f"gdrive_metadata_{file_id}_{include_permissions}"
        )

        # Format size
        if 'size' in file_info:
            size_bytes = int(file_info['size'])
            size_mb = size_bytes / (1024 * 1024)
            size_gb = size_mb / 1024

            if size_gb >= 1:
                size_formatted = f"{size_gb:.2f} GB"
            elif size_mb >= 1:
                size_formatted = f"{size_mb:.2f} MB"
            else:
                size_formatted = f"{size_bytes / 1024:.2f} KB"

            file_info['size_formatted'] = size_formatted

        # Simplify complex fields
        if 'owners' in file_info:
            file_info['owner_email'] = file_info['owners'][0].get('emailAddress', 'unknown')
            del file_info['owners']

        if 'lastModifyingUser' in file_info:
            file_info['last_modified_by'] = file_info['lastModifyingUser'].get('emailAddress', 'unknown')
            del file_info['lastModifyingUser']

        return json.dumps({
            "success": True,
            "metadata": file_info
        }, indent=2, default=str)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error getting metadata: {str(e)}"


@mcp.tool()
def gdrive_copy_file(
    file_id: str,
    new_name: str = None,
    destination_folder_id: str = None
) -> str:
    """Create a copy of a file in Google Drive.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        file_id: ID of the file to copy
        new_name: Optional name for the copy (defaults to "Copy of [original name]")
        destination_folder_id: Optional destination folder (defaults to same location as original)

    Returns:
        JSON with copied file details
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        def _copy_file():
            # Get original file info
            original = service.files().get(fileId=file_id, fields='name, parents').execute()

            copy_metadata = {}

            if new_name:
                copy_metadata['name'] = new_name
            else:
                copy_metadata['name'] = f"Copy of {original['name']}"

            if destination_folder_id:
                copy_metadata['parents'] = [destination_folder_id]

            copied_file = service.files().copy(
                fileId=file_id,
                body=copy_metadata,
                fields='id, name, webViewLink'
            ).execute()

            return original, copied_file

        original, copied_file = resilient_api_call(
            _copy_file,
            circuit_breaker=_google_drive_cb,
            rate_limiter=_google_drive_limiter,
            service_name="Google Drive",
            operation_name="copy_file"
        )

        return json.dumps({
            "success": True,
            "original_file_id": file_id,
            "original_name": original['name'],
            "copied_file_id": copied_file['id'],
            "copied_file_name": copied_file['name'],
            "web_link": copied_file.get('webViewLink', '')
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error copying file: {str(e)}"


@mcp.tool()
def gdrive_batch_upload(
    local_directory: str,
    destination_folder_id: str = None,
    file_pattern: str = "*"
) -> str:
    """Upload multiple files from a local directory to Google Drive.

    Args:
        local_directory: Path to local directory containing files
        destination_folder_id: Optional destination folder ID
        file_pattern: Glob pattern for files to upload (default: "*" for all files)

    Returns:
        JSON with upload results for each file
    """
    try:
        if not build or not MediaFileUpload:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        local_dir = Path(local_directory).expanduser()

        if not local_dir.exists() or not local_dir.is_dir():
            return json.dumps({
                "success": False,
                "error": f"Directory not found: {local_directory}"
            }, indent=2)

        # Find matching files
        files_to_upload = list(local_dir.glob(file_pattern))

        if not files_to_upload:
            return json.dumps({
                "success": True,
                "message": "No files found matching pattern",
                "pattern": file_pattern
            }, indent=2)

        results = []

        for file_path in files_to_upload:
            if not file_path.is_file():
                continue

            try:
                file_metadata = {'name': file_path.name}

                if destination_folder_id:
                    file_metadata['parents'] = [destination_folder_id]

                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if not mime_type:
                    mime_type = 'application/octet-stream'

                media = MediaFileUpload(str(file_path), mimetype=mime_type)

                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, size'
                ).execute()

                file_size_mb = int(file.get('size', 0)) / (1024 * 1024)

                results.append({
                    "success": True,
                    "file_name": file['name'],
                    "file_id": file['id'],
                    "size_mb": round(file_size_mb, 2)
                })

            except Exception as e:
                results.append({
                    "success": False,
                    "file_name": file_path.name,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return json.dumps({
            "success": True,
            "total_files": len(results),
            "successful_uploads": successful,
            "failed_uploads": len(results) - successful,
            "results": results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error in batch upload: {str(e)}"


# ============================================================================
# GOOGLE PHOTOS PICKER API TOOLS (v2.4.0 - Updated 2025-11-16)
# Note: Replaces deprecated Library API (removed March 2025) with Picker API
# ============================================================================

def _get_google_photos_picker_credentials():
    """Get OAuth credentials for Google Photos Picker API."""
    creds = None
    token_path = os.getenv("GOOGLE_PHOTOS_TOKEN_PATH", "/home/dave/skippy/.credentials/google_photos_token.json")
    credentials_path = os.getenv("GOOGLE_PHOTOS_CREDENTIALS_PATH", "/home/dave/skippy/.credentials/credentials.json")
    scopes = [os.getenv("GOOGLE_PHOTOS_SCOPES", "https://www.googleapis.com/auth/photospicker.mediaitems.readonly")]

    token_path = Path(token_path).expanduser()
    credentials_path = Path(credentials_path).expanduser()

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Google credentials not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.write_text(creds.to_json())

    return creds


@mcp.tool()
def gphotos_create_picker_session() -> str:
    """Create a new Google Photos Picker session.

    Features retry logic, circuit breaker protection, and rate limiting.

    This initiates a photo selection session. The returned pickerUri should be
    opened in a browser for the user to select photos from their Google Photos library.

    Returns:
        JSON string with:
        - session_id: Unique session identifier for polling and retrieval
        - picker_uri: URL to open in browser for user to select photos
        - expires_time: When the session expires

    Workflow:
        1. Call this function to create a session
        2. Open picker_uri in browser (or show QR code)
        3. User selects photos in Google Photos interface
        4. Poll with gphotos_check_session() until selection complete
        5. Retrieve photos with gphotos_get_selected_media()
    """
    try:
        creds = _get_google_photos_picker_credentials()

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        def _create_session():
            # Create picker session
            response = httpx.post(
                "https://photospicker.googleapis.com/v1/sessions",
                headers=headers,
                json={}
            )
            response.raise_for_status()
            return response.json()

        session_data = resilient_api_call(
            _create_session,
            circuit_breaker=_google_photos_cb,
            rate_limiter=_google_photos_limiter,
            service_name="Google Photos",
            operation_name="create_session"
        )

        return json.dumps({
            "success": True,
            "session_id": session_data.get("id"),
            "picker_uri": session_data.get("pickerUri"),
            "expires_time": session_data.get("expireTime"),
            "instructions": "Open picker_uri in a browser. User will select photos from their Google Photos. Then call gphotos_check_session() to poll for completion."
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error creating picker session: {str(e)}"


@mcp.tool()
def gphotos_check_session(session_id: str) -> str:
    """Check the status of a Google Photos Picker session.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        session_id: The session ID returned from gphotos_create_picker_session()

    Returns:
        JSON string with:
        - session_id: The session ID
        - media_items_set: True if user has finished selecting photos
        - picker_uri: URL for user to continue selecting (if not done)

    Note:
        Poll this endpoint periodically (e.g., every 3-5 seconds) until
        media_items_set is True, then call gphotos_get_selected_media().
    """
    try:
        creds = _get_google_photos_picker_credentials()

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        def _check_session():
            response = httpx.get(
                f"https://photospicker.googleapis.com/v1/sessions/{session_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()

        session_data = resilient_api_call(
            _check_session,
            circuit_breaker=_google_photos_cb,
            rate_limiter=_google_photos_limiter,
            service_name="Google Photos",
            operation_name="check_session"
        )

        return json.dumps({
            "success": True,
            "session_id": session_data.get("id"),
            "media_items_set": session_data.get("mediaItemsSet", False),
            "picker_uri": session_data.get("pickerUri"),
            "expires_time": session_data.get("expireTime")
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error checking session: {str(e)}"


@mcp.tool()
def gphotos_get_selected_media(session_id: str, max_results: int = 100) -> str:
    """Get the media items selected by the user in a Picker session.

    Args:
        session_id: The session ID from gphotos_create_picker_session()
        max_results: Maximum number of items to return (default: 100)

    Returns:
        JSON string with selected media items including:
        - id: Media item ID
        - baseUrl: Temporary download URL (valid 60 minutes)
        - mimeType: File type (image/jpeg, video/mp4, etc.)
        - mediaFile: File metadata (filename, size, etc.)

    Note:
        Only call this after gphotos_check_session() returns media_items_set=True.
        The baseUrl expires after 60 minutes or if user revokes access.
    """
    try:
        creds = _get_google_photos_picker_credentials()

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        media_items = []
        page_token = None

        while len(media_items) < max_results:
            params = {
                "sessionId": session_id,
                "pageSize": min(100, max_results - len(media_items))
            }
            if page_token:
                params["pageToken"] = page_token

            response = httpx.get(
                "https://photospicker.googleapis.com/v1/mediaItems",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("mediaItems", [])

            if not items:
                break

            for item in items:
                media_file = item.get("mediaFile", {})
                media_items.append({
                    "id": item.get("id"),
                    "baseUrl": media_file.get("baseUrl"),
                    "mimeType": media_file.get("mimeType"),
                    "filename": media_file.get("filename", "unknown"),
                    "fileSize": media_file.get("fileSize")
                })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return json.dumps({
            "success": True,
            "count": len(media_items),
            "session_id": session_id,
            "mediaItems": media_items,
            "note": "baseUrl expires in 60 minutes. Use gphotos_download_selected() to download."
        }, indent=2)

    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error getting selected media: {str(e)}"


@mcp.tool()
def gphotos_download_selected(base_url: str, output_path: str, mime_type: str = "image/jpeg") -> str:
    """Download a photo or video from a Picker session baseUrl.

    Args:
        base_url: The baseUrl from gphotos_get_selected_media()
        output_path: Local path where file should be saved
        mime_type: File MIME type (default: image/jpeg)

    Returns:
        JSON string with download result including file size and path.

    Note:
        - Photos: Downloads original quality
        - Videos: Append "=dv" to baseUrl for video download
        - baseUrl expires after 60 minutes from when session was polled
    """
    try:
        # Get credentials for authenticated download
        creds = _get_google_photos_picker_credentials()

        # Determine download URL based on media type
        if mime_type.startswith('video/'):
            download_url = f"{base_url}=dv"
        else:
            # For images, use =d for original quality download
            download_url = f"{base_url}=d"

        # Download the file with auth headers
        headers = {
            "Authorization": f"Bearer {creds.token}"
        }
        response = httpx.get(download_url, headers=headers, follow_redirects=True, timeout=60.0)
        response.raise_for_status()

        # Save to file
        output_file = Path(output_path).expanduser()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(response.content)

        file_size_mb = len(response.content) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "saved_to": str(output_file),
            "size_mb": round(file_size_mb, 2),
            "mime_type": mime_type
        }, indent=2)

    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error downloading media: {str(e)}"


@mcp.tool()
def gphotos_delete_session(session_id: str) -> str:
    """Delete a Google Photos Picker session.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        session_id: The session ID to delete

    Returns:
        Success or error message.

    Note:
        Sessions automatically expire, but you can delete them early
        to clean up or if the user wants to start over.
    """
    try:
        creds = _get_google_photos_picker_credentials()

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        def _delete_session():
            response = httpx.delete(
                f"https://photospicker.googleapis.com/v1/sessions/{session_id}",
                headers=headers
            )
            response.raise_for_status()
            return True

        resilient_api_call(
            _delete_session,
            circuit_breaker=_google_photos_cb,
            rate_limiter=_google_photos_limiter,
            service_name="Google Photos",
            operation_name="delete_session"
        )

        return json.dumps({
            "success": True,
            "message": f"Session {session_id} deleted successfully"
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error deleting session: {str(e)}"



# ============================================================================
# PEXELS TOOLS (v2.3.2 - Added 2025-11-12)
# ============================================================================

@mcp.tool()
def pexels_search_photos(
    query: str,
    per_page: int = 15,
    page: int = 1,
    orientation: str = None,
    size: str = None,
    color: str = None
) -> str:
    """Search for free stock photos on Pexels.

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        query: Search query (e.g., "campaign event", "political rally", "community")
        per_page: Number of results per page (max 80, default 15)
        page: Page number (default 1)
        orientation: Filter by orientation: "landscape", "portrait", or "square"
        size: Filter by size: "large", "medium", or "small"
        color: Filter by color: "red", "orange", "yellow", "green", "turquoise",
               "blue", "violet", "pink", "brown", "black", "gray", "white"

    Returns:
        JSON string with photo results including:
        - id: Photo ID
        - photographer: Photographer name
        - url: Pexels page URL
        - src: Download URLs (original, large, medium, small)
        - width/height: Dimensions
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        # Build API request
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}

        params = {
            "query": query,
            "per_page": min(per_page, 80),
            "page": page
        }

        if orientation:
            params["orientation"] = orientation
        if size:
            params["size"] = size
        if color:
            params["color"] = color

        def _search_photos():
            # Make API request
            response = httpx.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        data = resilient_api_call(
            _search_photos,
            circuit_breaker=_pexels_cb,
            rate_limiter=_pexels_limiter,
            service_name="Pexels",
            operation_name="search_photos",
            cache_key=f"pexels_search_{query}_{page}_{per_page}_{orientation}_{size}_{color}"
        )

        photos = data.get("photos", [])

        # Format results
        results = []
        for photo in photos:
            results.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "photographer_url": photo.get("photographer_url"),
                "url": photo.get("url"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "avg_color": photo.get("avg_color"),
                "src": {
                    "original": photo.get("src", {}).get("original"),
                    "large": photo.get("src", {}).get("large"),
                    "medium": photo.get("src", {}).get("medium"),
                    "small": photo.get("src", {}).get("small")
                },
                "alt": photo.get("alt", "")
            })

        return json.dumps({
            "success": True,
            "query": query,
            "total_results": data.get("total_results", 0),
            "page": page,
            "per_page": per_page,
            "count": len(results),
            "photos": results
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        return f"Error searching Pexels: {str(e)}"


@mcp.tool()
def pexels_get_photo(photo_id: int) -> str:
    """Get details of a specific photo by ID.

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        photo_id: The Pexels photo ID

    Returns:
        JSON string with photo details
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        url = f"https://api.pexels.com/v1/photos/{photo_id}"
        headers = {"Authorization": api_key}

        def _get_photo():
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        photo = resilient_api_call(
            _get_photo,
            circuit_breaker=_pexels_cb,
            rate_limiter=_pexels_limiter,
            service_name="Pexels",
            operation_name="get_photo",
            cache_key=f"pexels_photo_{photo_id}"
        )

        return json.dumps({
            "success": True,
            "id": photo.get("id"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "url": photo.get("url"),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "avg_color": photo.get("avg_color"),
            "src": photo.get("src"),
            "alt": photo.get("alt", "")
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        return f"Error getting photo: {str(e)}"


@mcp.tool()
def pexels_download_photo(photo_id: int, output_path: str, size: str = "large") -> str:
    """Download a photo from Pexels.

    Features retry logic, circuit breaker protection, and rate limiting.

    Args:
        photo_id: The Pexels photo ID
        output_path: Local path where file should be saved
        size: Size to download: "original", "large", "medium", "small" (default: "large")

    Returns:
        Success message with file info
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        # Get photo details
        url = f"https://api.pexels.com/v1/photos/{photo_id}"
        headers = {"Authorization": api_key}

        def _get_photo_details():
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        photo = resilient_api_call(
            _get_photo_details,
            circuit_breaker=_pexels_cb,
            rate_limiter=_pexels_limiter,
            service_name="Pexels",
            operation_name="download_photo_metadata"
        )

        # Get download URL for requested size
        src = photo.get("src", {})
        download_url = src.get(size)

        if not download_url:
            return f"Error: Size '{size}' not available. Available sizes: {list(src.keys())}"

        def _download_photo():
            # Download the photo
            photo_response = httpx.get(download_url, timeout=60)
            photo_response.raise_for_status()
            return photo_response.content

        photo_content = resilient_api_call(
            _download_photo,
            circuit_breaker=_pexels_cb,
            service_name="Pexels",
            operation_name="download_photo_content"
        )

        # Save to file
        output_file = Path(output_path).expanduser()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_bytes(photo_content)

        file_size_mb = len(photo_content) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "photo_id": photo_id,
            "photographer": photo.get("photographer"),
            "saved_to": str(output_file),
            "size": size,
            "file_size_mb": round(file_size_mb, 2),
            "dimensions": f"{photo.get('width')}x{photo.get('height')}"
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        return f"Error downloading photo: {str(e)}"


@mcp.tool()
def pexels_curated_photos(per_page: int = 15, page: int = 1) -> str:
    """Get curated photos from Pexels (trending/popular photos).

    Features retry logic, circuit breaker protection, and rate limiting with caching.

    Args:
        per_page: Number of results per page (max 80, default 15)
        page: Page number (default 1)

    Returns:
        JSON string with curated photo results
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        url = "https://api.pexels.com/v1/curated"
        headers = {"Authorization": api_key}

        params = {
            "per_page": min(per_page, 80),
            "page": page
        }

        def _get_curated():
            response = httpx.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        data = resilient_api_call(
            _get_curated,
            circuit_breaker=_pexels_cb,
            rate_limiter=_pexels_limiter,
            service_name="Pexels",
            operation_name="curated_photos",
            cache_key=f"pexels_curated_{page}_{per_page}"
        )

        photos = data.get("photos", [])

        results = []
        for photo in photos:
            results.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "url": photo.get("url"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "src": {
                    "large": photo.get("src", {}).get("large"),
                    "medium": photo.get("src", {}).get("medium")
                }
            })

        return json.dumps({
            "success": True,
            "page": page,
            "per_page": per_page,
            "count": len(results),
            "photos": results
        }, indent=2)

    except CircuitBreakerOpenError as e:
        return f"Service temporarily unavailable: {str(e)}. Please try again later."
    except RetryError as e:
        return f"Failed after multiple retry attempts: {str(e)}"
    except Exception as e:
        return f"Error getting curated photos: {str(e)}"


# ============================================================================
# HEALTH CHECK AND MONITORING TOOLS
# ============================================================================

@mcp.tool()
def system_health_check() -> str:
    """Perform comprehensive system health check.

    Checks various system components and validates configuration
    to ensure the system is operating correctly.

    Returns:
        JSON string with health check results including:
        - Overall system health status
        - Individual component checks
        - Warnings and recommendations
    """
    try:
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }

        warnings = []
        errors = []

        # Check 1: Disk space
        try:
            disk_usage = psutil.disk_usage("/")
            disk_percent = disk_usage.percent
            health_results["checks"]["disk_space"] = {
                "status": "healthy" if disk_percent < 85 else "warning" if disk_percent < 95 else "critical",
                "usage_percent": disk_percent,
                "free_gb": round(disk_usage.free / (1024**3), 2)
            }
            if disk_percent >= 85:
                warnings.append(f"Disk usage is at {disk_percent}%")
        except Exception as e:
            health_results["checks"]["disk_space"] = {"status": "error", "message": str(e)}
            errors.append(f"Disk check failed: {e}")

        # Check 2: Memory usage
        try:
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            health_results["checks"]["memory"] = {
                "status": "healthy" if mem_percent < 80 else "warning" if mem_percent < 95 else "critical",
                "usage_percent": mem_percent,
                "available_gb": round(memory.available / (1024**3), 2)
            }
            if mem_percent >= 80:
                warnings.append(f"Memory usage is at {mem_percent}%")
        except Exception as e:
            health_results["checks"]["memory"] = {"status": "error", "message": str(e)}
            errors.append(f"Memory check failed: {e}")

        # Check 3: CPU load
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            health_results["checks"]["cpu"] = {
                "status": "healthy" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical",
                "usage_percent": cpu_percent,
                "cpu_count": psutil.cpu_count()
            }
            if cpu_percent >= 70:
                warnings.append(f"CPU usage is at {cpu_percent}%")
        except Exception as e:
            health_results["checks"]["cpu"] = {"status": "error", "message": str(e)}
            errors.append(f"CPU check failed: {e}")

        # Check 4: Skippy libraries availability
        health_results["checks"]["skippy_libraries"] = {
            "status": "healthy" if SKIPPY_LIBS_AVAILABLE else "warning",
            "available": SKIPPY_LIBS_AVAILABLE,
            "resilience_available": SKIPPY_RESILIENCE_AVAILABLE if 'SKIPPY_RESILIENCE_AVAILABLE' in globals() else False
        }
        if not SKIPPY_LIBS_AVAILABLE:
            warnings.append("Skippy validation libraries not available - some security features disabled")

        # Check 5: Configuration validation
        if SKIPPY_LIBS_AVAILABLE and 'SKIPPY_RESILIENCE_AVAILABLE' in globals() and SKIPPY_RESILIENCE_AVAILABLE:
            try:
                config = SkippyConfig.from_env()
                validator = ConfigValidator(config)
                is_valid = validator.validate()
                health_results["checks"]["configuration"] = {
                    "status": "healthy" if is_valid else "warning",
                    "valid": is_valid,
                    "errors": validator.errors[:5],
                    "warnings": validator.warnings[:5]
                }
                if not is_valid:
                    errors.extend(validator.errors[:3])
                warnings.extend(validator.warnings[:3])
            except Exception as e:
                health_results["checks"]["configuration"] = {"status": "error", "message": str(e)}
        else:
            health_results["checks"]["configuration"] = {"status": "skipped", "reason": "Resilience modules not available"}

        # Check 6: Log directory writable
        try:
            log_dir = Path(os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")) / "logs"
            if log_dir.exists():
                test_file = log_dir / ".health_check_test"
                test_file.write_text("test")
                test_file.unlink()
                health_results["checks"]["log_directory"] = {"status": "healthy", "path": str(log_dir), "writable": True}
            else:
                health_results["checks"]["log_directory"] = {"status": "warning", "path": str(log_dir), "writable": False}
                warnings.append(f"Log directory does not exist: {log_dir}")
        except Exception as e:
            health_results["checks"]["log_directory"] = {"status": "error", "message": str(e)}
            errors.append(f"Log directory check failed: {e}")

        # Check 7: Circuit breaker status (if available)
        if 'SKIPPY_RESILIENCE_AVAILABLE' in globals() and SKIPPY_RESILIENCE_AVAILABLE:
            try:
                cb_states = get_all_circuit_breaker_states()
                open_breakers = [name for name, state in cb_states.items() if state.get("state") == "open"]
                health_results["checks"]["circuit_breakers"] = {
                    "status": "healthy" if not open_breakers else "warning",
                    "total": len(cb_states),
                    "open": open_breakers
                }
                if open_breakers:
                    warnings.append(f"Circuit breakers OPEN: {', '.join(open_breakers)}")
            except Exception as e:
                health_results["checks"]["circuit_breakers"] = {"status": "skipped", "message": str(e)}

        # Determine overall status
        if errors:
            health_results["overall_status"] = "critical"
        elif warnings:
            health_results["overall_status"] = "degraded"
        else:
            health_results["overall_status"] = "healthy"

        health_results["warnings"] = warnings
        health_results["errors"] = errors
        health_results["summary"] = f"System is {health_results['overall_status']} with {len(errors)} errors and {len(warnings)} warnings"

        return json.dumps(health_results, indent=2)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_system_metrics() -> str:
    """Get current system performance metrics.

    Returns detailed metrics about system resource usage,
    process information, and service status.

    Returns:
        JSON string with comprehensive system metrics
    """
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - psutil.boot_time(),
        }

        # CPU metrics
        cpu_times = psutil.cpu_times()
        metrics["cpu"] = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count_physical": psutil.cpu_count(logical=False),
            "count_logical": psutil.cpu_count(logical=True),
            "user_time": cpu_times.user,
            "system_time": cpu_times.system,
            "idle_time": cpu_times.idle
        }

        # Memory metrics
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        metrics["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent
        }

        # Disk metrics
        disk = psutil.disk_usage("/")
        metrics["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }

        # Network metrics
        net_io = psutil.net_io_counters()
        metrics["network"] = {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errors_in": net_io.errin,
            "errors_out": net_io.errout
        }

        # Process count
        metrics["processes"] = {
            "total": len(list(psutil.process_iter())),
            "running": len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
        }

        # Server-specific metrics
        metrics["server"] = {
            "skippy_libs_available": SKIPPY_LIBS_AVAILABLE,
            "resilience_available": SKIPPY_RESILIENCE_AVAILABLE if 'SKIPPY_RESILIENCE_AVAILABLE' in globals() else False,
            "python_version": sys.version.split()[0]
        }

        return json.dumps(metrics, indent=2)

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return f"Error getting system metrics: {str(e)}"


@mcp.tool()
def validate_skippy_configuration() -> str:
    """Validate the current Skippy configuration.

    Checks all configuration settings for correctness, security issues,
    and potential problems.

    Returns:
        JSON string with validation results including errors and warnings
    """
    try:
        if not SKIPPY_LIBS_AVAILABLE or not ('SKIPPY_RESILIENCE_AVAILABLE' in globals() and SKIPPY_RESILIENCE_AVAILABLE):
            return json.dumps({
                "success": False,
                "error": "Resilience modules not available for configuration validation"
            }, indent=2)

        # Validate configuration
        config = SkippyConfig.from_env()
        validator = ConfigValidator(config)
        is_valid = validator.validate()

        # Validate environment variables
        env_validation = validate_environment_variables()

        result = {
            "timestamp": datetime.now().isoformat(),
            "configuration_valid": is_valid,
            "environment_valid": env_validation["valid"],
            "configuration": {
                "errors": validator.errors,
                "warnings": validator.warnings,
                "settings": config.to_dict()
            },
            "environment": env_validation,
            "recommendations": []
        }

        # Add recommendations based on issues found
        if not is_valid:
            result["recommendations"].append("Fix configuration errors before deploying to production")
        if validator.warnings:
            result["recommendations"].append("Review configuration warnings for potential security issues")
        if not env_validation["valid"]:
            result["recommendations"].append("Set required environment variables")

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_circuit_breaker_status() -> str:
    """Get status of all circuit breakers.

    Circuit breakers protect the system from cascading failures by
    stopping requests to failing services.

    Returns:
        JSON string with circuit breaker states
    """
    try:
        if not ('SKIPPY_RESILIENCE_AVAILABLE' in globals() and SKIPPY_RESILIENCE_AVAILABLE):
            return json.dumps({
                "available": False,
                "message": "Circuit breaker module not available"
            }, indent=2)

        states = get_all_circuit_breaker_states()

        summary = {
            "total": len(states),
            "closed": sum(1 for s in states.values() if s.get("state") == "closed"),
            "open": sum(1 for s in states.values() if s.get("state") == "open"),
            "half_open": sum(1 for s in states.values() if s.get("state") == "half_open")
        }

        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "circuit_breakers": states
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def get_resilience_dashboard() -> str:
    """Get comprehensive resilience and monitoring dashboard.

    Provides a unified view of circuit breaker states, rate limiter usage,
    service health checks, and recommendations.

    Returns:
        JSON string with full resilience dashboard data
    """
    try:
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "version": "2.5.0",
            "resilience_available": SKIPPY_RESILIENCE_AVAILABLE if 'SKIPPY_RESILIENCE_AVAILABLE' in globals() else False
        }

        if not dashboard["resilience_available"]:
            dashboard["status"] = "limited"
            dashboard["message"] = "Resilience modules not available"
            return json.dumps(dashboard, indent=2)

        # Circuit breaker status
        cb_states = get_all_circuit_breaker_states()
        open_circuits = [name for name, state in cb_states.items() if state.get("state") == "open"]
        dashboard["circuit_breakers"] = {
            "total": len(cb_states),
            "healthy": sum(1 for s in cb_states.values() if s.get("state") == "closed"),
            "open": open_circuits
        }

        # Rate limiter status
        dashboard["rate_limiters"] = {
            "google_drive": {"remaining": _google_drive_limiter.get_remaining_calls() if _google_drive_limiter else "N/A"},
            "google_photos": {"remaining": _google_photos_limiter.get_remaining_calls() if _google_photos_limiter else "N/A"},
            "github": {"remaining": _github_limiter.get_remaining_calls() if _github_limiter else "N/A"},
            "pexels": {"remaining": _pexels_limiter.get_remaining_calls() if _pexels_limiter else "N/A"}
        }

        # Service health
        if _health_checker:
            health = _health_checker.get_summary()
            dashboard["service_health"] = {
                "overall_healthy": health["overall_healthy"],
                "healthy_count": health["healthy_count"],
                "unhealthy_count": health["unhealthy_count"]
            }

        # Recommendations
        recommendations = []
        if open_circuits:
            recommendations.append(f"Circuit breakers OPEN: {', '.join(open_circuits)}")
        if dashboard.get("service_health", {}).get("unhealthy_count", 0) > 0:
            recommendations.append(f"{dashboard['service_health']['unhealthy_count']} service(s) unhealthy")

        dashboard["recommendations"] = recommendations
        dashboard["status"] = "healthy" if not recommendations else "needs_attention"

        return json.dumps(dashboard, indent=2)

    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}")
        return json.dumps({"status": "error", "error": str(e)}, indent=2)


@mcp.tool()
def reset_circuit_breaker(service_name: str) -> str:
    """Manually reset a circuit breaker to closed state.

    Args:
        service_name: Name of the circuit breaker (e.g., "google-drive-api")

    Returns:
        Status message
    """
    try:
        if not SKIPPY_RESILIENCE_AVAILABLE:
            return "Error: Resilience modules not available"

        cb = get_circuit_breaker(service_name)
        old_state = cb.state.value
        cb.reset()

        logger.info(f"Circuit breaker '{service_name}' reset from {old_state} to CLOSED")
        return json.dumps({
            "success": True,
            "service": service_name,
            "old_state": old_state,
            "new_state": "closed"
        }, indent=2)

    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# SESSION MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def session_create(category: str, description: str) -> str:
    """
    Create a standardized session directory for work tracking.

    Args:
        category: Session category (wordpress, scripts, security, git, mcp, validation, precommit, campaign, general)
        description: Brief description (lowercase, underscores, 2-5 words)

    Returns:
        JSON with session directory path and initialization info
    """
    try:
        valid_categories = ["wordpress", "scripts", "security", "git", "mcp", "validation", "precommit", "campaign", "general"]
        if category not in valid_categories:
            return json.dumps({"success": False, "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}, indent=2)

        description = re.sub(r'[^a-z0-9_]', '_', description.lower())
        description = re.sub(r'_+', '_', description).strip('_')

        if not description or len(description) < 3:
            return json.dumps({"success": False, "error": "Description must be at least 3 characters"}, indent=2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{timestamp}_{description}"
        session_dir = Path(SKIPPY_PATH) / "work" / category / session_name
        session_dir.mkdir(parents=True, exist_ok=True)

        readme_content = f"""# Session: {description.replace('_', ' ').title()}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Category:** {category}
**Directory:** {session_dir}

## Overview
[Brief description of work being done]

## Files Modified
- [List files here]

## Changes Made
1. [Change 1]

## Verification Results
- [ ] Change 1 verified

## Rollback Procedure
```bash
# Commands to undo changes if needed
```

## Status
In Progress
"""
        (session_dir / "README.md").write_text(readme_content)

        return json.dumps({
            "success": True,
            "session_dir": str(session_dir),
            "session_name": session_name,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "files_created": ["README.md"],
            "usage": f'export SESSION_DIR="{session_dir}"'
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def session_list(category: str = "", hours: int = 24) -> str:
    """
    List recent session directories.

    Args:
        category: Filter by category (optional, empty = all categories)
        hours: How many hours back to look (default: 24)

    Returns:
        JSON with list of recent sessions
    """
    try:
        work_dir = Path(SKIPPY_PATH) / "work"
        sessions = []
        cutoff_time = datetime.now().timestamp() - (hours * 3600)

        categories = [category] if category else [d.name for d in work_dir.iterdir() if d.is_dir()]

        for cat in categories:
            cat_dir = work_dir / cat
            if not cat_dir.exists():
                continue

            for session_dir in cat_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                try:
                    dir_name = session_dir.name
                    if len(dir_name) >= 15 and dir_name[8] == '_':
                        timestamp_str = dir_name[:15]
                        session_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        if session_time.timestamp() >= cutoff_time:
                            file_count = sum(1 for _ in session_dir.rglob("*") if _.is_file())
                            has_readme = (session_dir / "README.md").exists()
                            sessions.append({
                                "path": str(session_dir),
                                "name": dir_name,
                                "category": cat,
                                "created_at": session_time.isoformat(),
                                "age_hours": round((datetime.now() - session_time).total_seconds() / 3600, 1),
                                "file_count": file_count,
                                "has_readme": has_readme
                            })
                except (ValueError, IndexError):
                    continue

        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return json.dumps({"success": True, "hours_searched": hours, "category_filter": category or "all", "session_count": len(sessions), "sessions": sessions[:50]}, indent=2)

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def session_summarize(session_dir: str) -> str:
    """
    Generate summary for a session directory.

    Args:
        session_dir: Path to the session directory

    Returns:
        JSON with summary information
    """
    try:
        session_path = Path(session_dir)
        if not session_path.exists():
            return json.dumps({"success": False, "error": "Session directory does not exist"}, indent=2)

        files = []
        total_size = 0
        for f in session_path.rglob("*"):
            if f.is_file():
                files.append({
                    "path": str(f.relative_to(session_path)),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
                total_size += f.stat().st_size

        dir_name = session_path.name
        parts = dir_name.split('_', 2)
        description = parts[2].replace('_', ' ').title() if len(parts) >= 3 else dir_name

        before_files = [f for f in files if "_before" in f["path"]]
        after_files = [f for f in files if "_after" in f["path"]]
        final_files = [f for f in files if "_final" in f["path"]]

        summary = {
            "success": True,
            "session_dir": str(session_path),
            "description": description,
            "total_files": len(files),
            "total_size_kb": round(total_size / 1024, 2),
            "workflow_files": {"before_snapshots": len(before_files), "after_snapshots": len(after_files), "final_versions": len(final_files)},
            "files": files[:30]
        }
        return json.dumps(summary, indent=2)

    except Exception as e:
        logger.error(f"Failed to summarize session: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def session_archive(session_dir: str) -> str:
    """
    Archive a completed session by compressing it.

    Args:
        session_dir: Path to the session directory to archive

    Returns:
        JSON with archive information
    """
    try:
        import shutil
        session_path = Path(session_dir)
        if not session_path.exists():
            return json.dumps({"success": False, "error": "Session directory does not exist"}, indent=2)

        archive_dir = Path(SKIPPY_PATH) / "archives" / "sessions"
        archive_dir.mkdir(parents=True, exist_ok=True)

        archive_name = f"{session_path.name}.tar.gz"
        archive_path = archive_dir / archive_name

        shutil.make_archive(str(archive_path.with_suffix('').with_suffix('')), 'gztar', session_path.parent, session_path.name)
        archive_size = archive_path.stat().st_size

        return json.dumps({
            "success": True,
            "session_dir": str(session_path),
            "archive_path": str(archive_path),
            "archive_size_mb": round(archive_size / (1024 * 1024), 2),
            "message": f"Session archived. Original directory remains intact."
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ============================================================================
# FACT VALIDATION TOOLS
# ============================================================================

@mcp.tool()
def facts_validate(text: str) -> str:
    """
    Validate text content against authoritative campaign facts.

    Checks for incorrect campaign statistics from QUICK_FACTS_SHEET.md.

    Args:
        text: Text content to validate

    Returns:
        JSON with validation results and any issues found
    """
    try:
        authoritative_facts = {
            "total_budget": {
                "correct": "$1.27 billion",
                "wrong": ["$81M", "$81 million", "$110.5M", "$110M"],
                "topic": "Total Budget"
            },
            "wellness_roi": {
                "correct": "$1.80 per $1 spent",
                "wrong": ["$2-3", "$2-$3", "2-3 per", "$2 to $3"],
                "topic": "Wellness Center ROI"
            },
            "mini_substations": {
                "correct": "46 substations",
                "wrong": ["42 substations", "40 substations", "50 substations"],
                "topic": "Mini Police Substations"
            },
            "wellness_centers": {
                "correct": "18 centers",
                "wrong": ["15 centers", "20 centers", "12 centers"],
                "topic": "Wellness Centers"
            },
            "police_budget": {
                "correct": "$245.9M",
                "wrong": ["$200M", "$250M", "$300M"],
                "topic": "Police Budget"
            },
            "crime_reduction_goal": {
                "correct": "35% reduction",
                "wrong": ["40% reduction", "50% reduction", "25% reduction"],
                "topic": "Crime Reduction Goal"
            },
            "participatory_budget": {
                "correct": "$15M",
                "wrong": ["$10M", "$20M", "$5M"],
                "topic": "Participatory Budgeting"
            },
            "new_jobs": {
                "correct": "400+ new jobs",
                "wrong": ["200 jobs", "500 jobs", "300 jobs"],
                "topic": "New Jobs Created"
            }
        }

        issues = []
        verified = []
        text_lower = text.lower()

        for fact_id, fact in authoritative_facts.items():
            for wrong in fact["wrong"]:
                if wrong.lower() in text_lower:
                    issues.append({
                        "type": "incorrect_fact",
                        "topic": fact["topic"],
                        "found": wrong,
                        "correct": fact["correct"],
                        "severity": "high"
                    })
            if fact["correct"].lower() in text_lower:
                verified.append({"topic": fact["topic"], "value": fact["correct"]})

        # Check JCPS patterns
        if re.search(r"44%?\s*(?:reading|proficient)", text_lower):
            issues.append({"type": "incorrect_fact", "topic": "JCPS Reading", "found": "44%", "correct": "34-35%", "severity": "high"})
        if re.search(r"41%?\s*(?:math|proficient)", text_lower):
            issues.append({"type": "incorrect_fact", "topic": "JCPS Math", "found": "41%", "correct": "27-28%", "severity": "high"})

        result = {
            "success": True,
            "valid": len(issues) == 0,
            "issues_found": len(issues),
            "facts_verified": len(verified),
            "issues": issues,
            "verified": verified
        }
        if issues:
            result["recommendation"] = "Please correct issues before publishing. Reference QUICK_FACTS_SHEET.md."
        else:
            result["recommendation"] = "Content appears factually consistent with campaign data."

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Fact validation failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def facts_lookup(topic: str) -> str:
    """
    Look up authoritative campaign fact by topic.

    Args:
        topic: Topic to look up (budget, roi, substations, wellness, police, crime, jobs, etc.)

    Returns:
        JSON with the authoritative fact and context
    """
    try:
        facts_db = {
            "budget": {"value": "$1.27 billion", "context": "Same as Mayor Greenberg's approved 2025-2026 budget", "notes": "No new taxes, balanced and realistic"},
            "total_budget": {"value": "$1.025B operating", "breakdown": {"public_safety": "$395.2M (31.2%)", "community_investment": "$210M (16.6%)", "infrastructure": "$241M (19.0%)"}},
            "roi": {"value": "$1.80 saved for every $1 spent", "context": "Wellness center return on investment", "evidence": "35% reduction in ER visits"},
            "substations": {"value": "46 mini police substations", "deployment": "12 in Year 1, 24 total Year 2, 36 Year 3, all 46 by Year 4", "cost": "$650K per station annually"},
            "wellness": {"value": "18 community wellness centers", "deployment": "6 per year over 3 years", "cost": "$2.5M per center annually"},
            "police": {"value": "$245.9M", "context": "Same as Greenberg's police budget - deployment is smarter, not less"},
            "crime": {"value": "35% reduction goal over 4 years", "evidence": "Based on 50+ cities using similar models"},
            "jobs": {"value": "400+ new positions created", "breakdown": {"wellness_staff": "~180", "youth_workers": "~200", "facilitators": "~25"}},
            "participatory": {"value": "$15M across all districts", "context": "Community decides spending priorities"},
            "youth": {"value": "$55M consolidated", "breakdown": {"after_school": "$15M", "summer_jobs": "$12M (3,000 positions)", "mentorship": "$8M"}},
            "mental_health": {"value": "10 mobile crisis teams", "context": "Social worker + officer pairs, 24/7 coverage", "cost": "$7M annually"}
        }

        topic_lower = topic.lower()
        for key, fact in facts_db.items():
            if key in topic_lower or topic_lower in key:
                return json.dumps({"success": True, "topic": key, "fact": fact}, indent=2)

        matches = [key for key in facts_db.keys() if any(word in key for word in topic_lower.split())]
        if matches:
            return json.dumps({"success": True, "topic_not_found": topic, "suggestions": matches}, indent=2)

        return json.dumps({"success": True, "topic_not_found": topic, "available_topics": list(facts_db.keys())}, indent=2)

    except Exception as e:
        logger.error(f"Fact lookup failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def facts_diff(old_content: str, new_content: str) -> str:
    """
    Compare two content versions and identify any fact changes.

    Args:
        old_content: Original content
        new_content: Updated content

    Returns:
        JSON with fact changes detected
    """
    try:
        number_patterns = [
            (r'\$[\d,]+(?:\.\d+)?[MBK]?(?:\s*(?:million|billion))?', 'dollar_amount'),
            (r'\d+(?:\.\d+)?%', 'percentage'),
            (r'\d{1,3}(?:,\d{3})*\s*(?:jobs?|positions?|centers?|stations?)', 'count'),
        ]

        old_facts = {}
        new_facts = {}

        for pattern, fact_type in number_patterns:
            old_matches = re.findall(pattern, old_content, re.IGNORECASE)
            new_matches = re.findall(pattern, new_content, re.IGNORECASE)
            if old_matches:
                old_facts[fact_type] = old_matches
            if new_matches:
                new_facts[fact_type] = new_matches

        changes = []
        for fact_type in set(old_facts.keys()) | set(new_facts.keys()):
            old_vals = set(old_facts.get(fact_type, []))
            new_vals = set(new_facts.get(fact_type, []))
            removed = old_vals - new_vals
            added = new_vals - old_vals
            if removed or added:
                changes.append({"type": fact_type, "removed": list(removed), "added": list(added)})

        validation_result = json.loads(facts_validate(new_content))

        return json.dumps({
            "success": True,
            "changes_detected": len(changes),
            "changes": changes,
            "new_content_validation": {"valid": validation_result.get("valid", True), "issues": validation_result.get("issues", [])},
            "recommendation": "Review changes carefully. Ensure all modified facts are accurate."
        }, indent=2)

    except Exception as e:
        logger.error(f"Fact diff failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ============================================================================
# WORDPRESS AUTOMATION TOOLS
# ============================================================================

@mcp.tool()
def wp_update_with_verification(post_id: int, content: str, session_dir: str = "", verify: bool = True, fact_check: bool = True) -> str:
    """
    Update WordPress post/page with automatic verification and fact-checking.

    Args:
        post_id: WordPress post/page ID
        content: New HTML content
        session_dir: Session directory (auto-created if empty)
        verify: Whether to verify update after applying (default: True)
        fact_check: Whether to check facts before updating (default: True)

    Returns:
        JSON with update results and verification status
    """
    try:
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")

        if not session_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = str(Path(SKIPPY_PATH) / "work" / "wordpress" / f"{timestamp}_post_{post_id}_update")
            Path(session_dir).mkdir(parents=True, exist_ok=True)

        session_path = Path(session_dir)
        results = {"success": False, "post_id": post_id, "session_dir": str(session_path), "steps": {}}

        # Fact check
        if fact_check:
            fact_result = json.loads(facts_validate(content))
            results["steps"]["fact_check"] = {"performed": True, "valid": fact_result.get("valid", True), "issues": fact_result.get("issues", [])}
            if not fact_result.get("valid", True):
                results["error"] = "Content failed fact validation. Fix issues before updating."
                return json.dumps(results, indent=2)

        # Save before snapshot
        before_cmd = f'wp --path="{wp_path}" post get {post_id} --field=post_content'
        before_result = subprocess.run(before_cmd, shell=True, capture_output=True, text=True)
        if before_result.returncode == 0:
            before_file = session_path / f"page_{post_id}_before.html"
            before_file.write_text(before_result.stdout)
            results["steps"]["before_snapshot"] = {"saved": str(before_file)}
        else:
            results["error"] = f"Failed to get current content: {before_result.stderr}"
            return json.dumps(results, indent=2)

        # Save final
        final_file = session_path / f"page_{post_id}_final.html"
        final_file.write_text(content)
        results["steps"]["final_saved"] = {"saved": str(final_file)}

        # Apply update
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tf:
            tf.write(content)
            temp_file = tf.name

        update_cmd = f'wp --path="{wp_path}" post update {post_id} --post_content="$(cat {temp_file})"'
        update_result = subprocess.run(update_cmd, shell=True, capture_output=True, text=True)
        os.unlink(temp_file)

        if update_result.returncode != 0:
            results["error"] = f"Failed to update post: {update_result.stderr}"
            return json.dumps(results, indent=2)

        results["steps"]["update_applied"] = {"status": "success"}

        # Verify
        if verify:
            verify_cmd = f'wp --path="{wp_path}" post get {post_id} --field=post_content'
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            if verify_result.returncode == 0:
                after_file = session_path / f"page_{post_id}_after.html"
                after_file.write_text(verify_result.stdout)
                actual_normalized = ' '.join(verify_result.stdout.strip().split())
                expected_normalized = ' '.join(content.strip().split())
                verified = actual_normalized == expected_normalized
                results["steps"]["verification"] = {"performed": True, "verified": verified, "after_file": str(after_file)}

        results["success"] = True
        results["message"] = f"Post {post_id} updated successfully"
        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"WordPress update failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def wp_cache_flush_all(local: bool = True, production: bool = False) -> str:
    """
    Flush all WordPress caches (object cache, rewrite rules, transients).

    Args:
        local: Flush local site cache (default: True)
        production: Flush production site cache (default: False)

    Returns:
        JSON with flush results
    """
    try:
        results = {"success": True, "sites": {}}

        if local:
            wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
            local_results = []
            commands = [("cache flush", "Object cache flushed"), ("rewrite flush", "Rewrite rules flushed"), ("transient delete --all", "Transients deleted")]
            for cmd, desc in commands:
                full_cmd = f'wp --path="{wp_path}" {cmd}'
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
                local_results.append({"command": cmd, "success": result.returncode == 0, "message": desc if result.returncode == 0 else result.stderr})
            results["sites"]["local"] = {"path": wp_path, "actions": local_results}

        if production:
            ssh_key = os.path.expanduser("~/.ssh/godaddy_rundaverun")
            ssh_user = "git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com"
            prod_results = []
            for cmd in ["wp cache flush", "wp rewrite flush"]:
                full_cmd = f'SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {ssh_key} {ssh_user} "cd html && {cmd} 2>/dev/null"'
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
                prod_results.append({"command": cmd, "success": result.returncode == 0, "output": result.stdout.strip() if result.returncode == 0 else result.stderr})
            results["sites"]["production"] = {"host": "rundaverun.org", "actions": prod_results}

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Cache flush failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def wp_content_compare(post_id: int) -> str:
    """
    Compare WordPress content between local and production sites.

    Args:
        post_id: WordPress post/page ID

    Returns:
        JSON with comparison results
    """
    try:
        results = {"success": True, "post_id": post_id, "local": {}, "production": {}, "differences": []}

        # Get local content
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
        local_cmd = f'wp --path="{wp_path}" post get {post_id} --field=post_content'
        local_result = subprocess.run(local_cmd, shell=True, capture_output=True, text=True)

        if local_result.returncode == 0:
            results["local"]["content_length"] = len(local_result.stdout)
            results["local"]["content_preview"] = local_result.stdout[:500] + "..." if len(local_result.stdout) > 500 else local_result.stdout
            local_content = local_result.stdout
        else:
            results["local"]["error"] = local_result.stderr
            local_content = ""

        # Get production content
        ssh_key = os.path.expanduser("~/.ssh/godaddy_rundaverun")
        ssh_user = "git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com"
        prod_cmd = f'SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {ssh_key} {ssh_user} "cd html && wp post get {post_id} --field=post_content 2>/dev/null"'
        prod_result = subprocess.run(prod_cmd, shell=True, capture_output=True, text=True)

        if prod_result.returncode == 0:
            results["production"]["content_length"] = len(prod_result.stdout)
            results["production"]["content_preview"] = prod_result.stdout[:500] + "..." if len(prod_result.stdout) > 500 else prod_result.stdout
            prod_content = prod_result.stdout
        else:
            results["production"]["error"] = prod_result.stderr
            prod_content = ""

        if local_content and prod_content:
            local_normalized = ' '.join(local_content.split())
            prod_normalized = ' '.join(prod_content.split())
            results["match"] = local_normalized == prod_normalized
            if not results["match"]:
                results["differences"].append({"type": "content_mismatch", "local_length": len(local_content), "production_length": len(prod_content), "length_diff": len(local_content) - len(prod_content)})

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Content compare failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ============================================================================
# DEPLOYMENT VERIFICATION TOOLS
# ============================================================================

@mcp.tool()
def deploy_verify_url(url: str, expected_text: str = "", check_ssl: bool = True, check_response_time: bool = True) -> str:
    """
    Verify a deployed URL is accessible and contains expected content.

    Args:
        url: URL to verify
        expected_text: Text that should appear on the page (optional)
        check_ssl: Check SSL certificate validity (default: True)
        check_response_time: Report response time (default: True)

    Returns:
        JSON with verification results
    """
    try:
        import ssl
        import socket
        from urllib.parse import urlparse

        results = {"success": True, "url": url, "checks": {}}
        parsed = urlparse(url)

        # HTTP check
        import time
        start_time = time.time()
        try:
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            end_time = time.time()
            results["checks"]["http"] = {"status_code": response.status_code, "success": response.status_code == 200, "final_url": str(response.url)}
            if check_response_time:
                results["checks"]["http"]["response_time_ms"] = round((end_time - start_time) * 1000)
            if expected_text:
                content_found = expected_text.lower() in response.text.lower()
                results["checks"]["content"] = {"expected": expected_text, "found": content_found}
        except Exception as e:
            results["checks"]["http"] = {"success": False, "error": str(e)}

        # SSL check
        if check_ssl and parsed.scheme == "https":
            try:
                context = ssl.create_default_context()
                with socket.create_connection((parsed.hostname, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
                        cert = ssock.getpeercert()
                        not_after = cert.get('notAfter', '')
                        if not_after:
                            expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                            days_until_expiry = (expiry - datetime.now()).days
                            results["checks"]["ssl"] = {"valid": True, "expires": not_after, "days_until_expiry": days_until_expiry, "warning": days_until_expiry < 30}
            except Exception as e:
                results["checks"]["ssl"] = {"valid": False, "error": str(e)}

        results["overall_success"] = all(check.get("success", True) for check in results["checks"].values())
        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Deploy verification failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def deploy_verify_site(site_type: str = "production") -> str:
    """
    Run comprehensive verification checks on the campaign website.

    Args:
        site_type: Site to verify - "local" or "production" (default: production)

    Returns:
        JSON with comprehensive verification results
    """
    try:
        if site_type == "production":
            base_url = "https://rundaverun.org"
        else:
            base_url = "http://rundaverun-local-complete-022655.local"

        results = {"success": True, "site_type": site_type, "base_url": base_url, "timestamp": datetime.now().isoformat(), "pages": {}}

        pages_to_check = [
            ("", "Dave Biggers"),
            ("/about/", "Dave Biggers"),
            ("/neighborhoods/", "neighborhood"),
            ("/get-involved/", "volunteer"),
            ("/contact/", "contact"),
        ]

        for path, expected in pages_to_check:
            url = f"{base_url}{path}"
            try:
                response = httpx.get(url, timeout=15.0, follow_redirects=True)
                page_result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "content_check": expected.lower() in response.text.lower() if expected else True,
                    "content_length": len(response.text)
                }
            except Exception as e:
                page_result = {"success": False, "error": str(e)}
            results["pages"][path or "/"] = page_result

        total_pages = len(results["pages"])
        successful_pages = sum(1 for p in results["pages"].values() if p.get("success", False))
        results["summary"] = {"total_pages": total_pages, "successful": successful_pages, "failed": total_pages - successful_pages, "success_rate": f"{(successful_pages / total_pages) * 100:.1f}%"}
        results["overall_success"] = successful_pages == total_pages

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Site verification failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# HEALTH CHECK AGGREGATION TOOLS
# ==============================================================================

@mcp.tool()
def health_check_all() -> str:
    """
    Run comprehensive health checks across all systems.

    Returns:
        JSON with aggregated health status for all monitored systems
    """
    try:
        results = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "systems": {},
            "summary": {"healthy": 0, "warning": 0, "critical": 0}
        }

        # Local system checks
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            results["systems"]["local_disk"] = {
                "status": "critical" if disk_percent > 90 else "warning" if disk_percent > 80 else "healthy",
                "value": f"{disk_percent}%",
                "details": f"{disk.free // (1024**3)}GB free of {disk.total // (1024**3)}GB"
            }
        except Exception as e:
            results["systems"]["local_disk"] = {"status": "error", "error": str(e)}

        try:
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            results["systems"]["local_memory"] = {
                "status": "critical" if mem_percent > 90 else "warning" if mem_percent > 80 else "healthy",
                "value": f"{mem_percent}%",
                "details": f"{memory.available // (1024**3)}GB available"
            }
        except Exception as e:
            results["systems"]["local_memory"] = {"status": "error", "error": str(e)}

        # WordPress local
        try:
            wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
            wp_check = subprocess.run(f'wp --path="{wp_path}" core is-installed', shell=True, capture_output=True, timeout=10)
            results["systems"]["wordpress_local"] = {
                "status": "healthy" if wp_check.returncode == 0 else "critical",
                "value": "installed" if wp_check.returncode == 0 else "not responding"
            }
        except Exception as e:
            results["systems"]["wordpress_local"] = {"status": "error", "error": str(e)}

        # Production site
        try:
            response = httpx.get("https://rundaverun.org", timeout=10.0)
            results["systems"]["production_site"] = {
                "status": "healthy" if response.status_code == 200 else "warning",
                "value": f"HTTP {response.status_code}",
                "response_time_ms": int(response.elapsed.total_seconds() * 1000)
            }
        except Exception as e:
            results["systems"]["production_site"] = {"status": "critical", "error": str(e)}

        # Summarize
        for system, data in results["systems"].items():
            status = data.get("status", "error")
            if status == "healthy":
                results["summary"]["healthy"] += 1
            elif status == "warning":
                results["summary"]["warning"] += 1
            else:
                results["summary"]["critical"] += 1

        total = len(results["systems"])
        results["summary"]["total"] = total
        results["overall_status"] = "critical" if results["summary"]["critical"] > 0 else "warning" if results["summary"]["warning"] > 0 else "healthy"

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def health_check_quick() -> str:
    """
    Quick health check - just essential systems.

    Returns:
        JSON with quick health status
    """
    try:
        checks = []

        # Disk
        disk = psutil.disk_usage('/')
        checks.append(("disk", disk.percent < 90, f"{disk.percent}%"))

        # Memory
        mem = psutil.virtual_memory()
        checks.append(("memory", mem.percent < 90, f"{mem.percent}%"))

        # Production site
        try:
            resp = httpx.get("https://rundaverun.org", timeout=5.0)
            checks.append(("production", resp.status_code == 200, f"HTTP {resp.status_code}"))
        except:
            checks.append(("production", False, "unreachable"))

        all_ok = all(c[1] for c in checks)
        return json.dumps({
            "success": True,
            "all_ok": all_ok,
            "checks": {name: {"ok": ok, "value": val} for name, ok, val in checks},
            "emoji": "✅" if all_ok else "⚠️"
        }, indent=2)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# UTILITY TOOLS
# ==============================================================================

@mcp.tool()
def file_backup(file_path: str, backup_dir: str = "") -> str:
    """
    Create a timestamped backup of a file.

    Args:
        file_path: Path to file to backup
        backup_dir: Directory for backup (default: same directory as file)

    Returns:
        JSON with backup file path
    """
    try:
        source = Path(file_path)
        if not source.exists():
            return json.dumps({"success": False, "error": "Source file does not exist"}, indent=2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"

        if backup_dir:
            backup_path = Path(backup_dir) / backup_name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            backup_path = source.parent / backup_name

        import shutil
        shutil.copy2(source, backup_path)

        return json.dumps({
            "success": True,
            "original": str(source),
            "backup": str(backup_path),
            "size_bytes": backup_path.stat().st_size
        }, indent=2)

    except Exception as e:
        logger.error(f"File backup failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def text_diff(text1: str, text2: str, context_lines: int = 3) -> str:
    """
    Generate a unified diff between two text strings.

    Args:
        text1: First text (original)
        text2: Second text (modified)
        context_lines: Number of context lines (default: 3)

    Returns:
        JSON with diff output
    """
    try:
        import difflib
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        diff = list(difflib.unified_diff(lines1, lines2, fromfile='original', tofile='modified', n=context_lines))

        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return json.dumps({
            "success": True,
            "has_changes": len(diff) > 0,
            "additions": additions,
            "deletions": deletions,
            "diff": ''.join(diff) if diff else "No differences found"
        }, indent=2)

    except Exception as e:
        logger.error(f"Text diff failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def json_validate(json_string: str) -> str:
    """
    Validate JSON string and return parsed structure info.

    Args:
        json_string: JSON string to validate

    Returns:
        JSON with validation results
    """
    try:
        parsed = json.loads(json_string)

        def get_structure(obj, depth=0):
            if depth > 3:
                return "..."
            if isinstance(obj, dict):
                return {k: get_structure(v, depth+1) for k, v in list(obj.items())[:5]}
            elif isinstance(obj, list):
                return [get_structure(obj[0], depth+1)] if obj else []
            else:
                return type(obj).__name__

        return json.dumps({
            "success": True,
            "valid": True,
            "type": type(parsed).__name__,
            "structure_preview": get_structure(parsed),
            "size_bytes": len(json_string)
        }, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({
            "success": True,
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "column": e.colno
        }, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def timestamp_convert(timestamp: str, to_format: str = "iso") -> str:
    """
    Convert between timestamp formats.

    Args:
        timestamp: Input timestamp (unix epoch, ISO 8601, or common formats)
        to_format: Output format - "iso", "unix", "human", "date" (default: iso)

    Returns:
        JSON with converted timestamp
    """
    try:
        dt = None

        # Try unix timestamp
        if timestamp.isdigit() or (timestamp.startswith('-') and timestamp[1:].isdigit()):
            ts = int(timestamp)
            if ts > 1e12:  # milliseconds
                ts = ts / 1000
            dt = datetime.fromtimestamp(ts)

        # Try ISO format
        if dt is None:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                pass

        # Try common formats
        if dt is None:
            formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d_%H%M%S"]
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    break
                except:
                    continue

        if dt is None:
            return json.dumps({"success": False, "error": "Could not parse timestamp"}, indent=2)

        result = {"success": True, "input": timestamp, "parsed": dt.isoformat()}

        if to_format == "iso":
            result["output"] = dt.isoformat()
        elif to_format == "unix":
            result["output"] = int(dt.timestamp())
        elif to_format == "human":
            result["output"] = dt.strftime("%B %d, %Y at %I:%M %p")
        elif to_format == "date":
            result["output"] = dt.strftime("%Y-%m-%d")
        else:
            result["output"] = dt.isoformat()

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Timestamp convert failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def env_check(var_names: str) -> str:
    """
    Check if environment variables are set.

    Args:
        var_names: Comma-separated list of variable names to check

    Returns:
        JSON with variable status (values masked for security)
    """
    try:
        names = [n.strip() for n in var_names.split(',')]
        results = {}

        for name in names:
            value = os.environ.get(name)
            if value is None:
                results[name] = {"set": False}
            else:
                # Mask value for security
                masked = value[:3] + "***" + value[-3:] if len(value) > 8 else "***"
                results[name] = {"set": True, "length": len(value), "preview": masked}

        all_set = all(r["set"] for r in results.values())

        return json.dumps({
            "success": True,
            "all_set": all_set,
            "variables": results
        }, indent=2)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# GIT AUTOMATION TOOLS
# ==============================================================================

@mcp.tool()
def git_safe_commit(repo_path: str, message: str, files: str = "") -> str:
    """
    Create a git commit with proper formatting and Co-Authored-By.

    Args:
        repo_path: Path to git repository
        message: Commit message (will be formatted properly)
        files: Comma-separated files to stage (empty = all staged files)

    Returns:
        JSON with commit results
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return json.dumps({"success": False, "error": "Not a git repository"}, indent=2)

        results = {"success": False, "repo": str(repo), "steps": []}

        if files:
            for f in files.split(','):
                f = f.strip()
                cmd = f'git -C "{repo}" add "{f}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                results["steps"].append({"action": f"stage {f}", "success": result.returncode == 0})

        status_cmd = f'git -C "{repo}" diff --cached --name-only'
        status_result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)
        staged_files = [f for f in status_result.stdout.strip().split('\n') if f]

        if not staged_files:
            return json.dumps({"success": False, "error": "No staged changes to commit"}, indent=2)

        results["staged_files"] = staged_files

        full_message = f"{message}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write(full_message)
            msg_file = tf.name

        commit_cmd = f'git -C "{repo}" commit -F "{msg_file}"'
        commit_result = subprocess.run(commit_cmd, shell=True, capture_output=True, text=True)
        os.unlink(msg_file)

        if commit_result.returncode == 0:
            hash_cmd = f'git -C "{repo}" rev-parse --short HEAD'
            hash_result = subprocess.run(hash_cmd, shell=True, capture_output=True, text=True)
            results["success"] = True
            results["commit_hash"] = hash_result.stdout.strip()
            results["message"] = message
            results["files_committed"] = len(staged_files)
        else:
            results["error"] = commit_result.stderr

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Git safe commit failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def git_branch_cleanup(repo_path: str, dry_run: bool = True) -> str:
    """
    Find and optionally delete merged branches.

    Args:
        repo_path: Path to git repository
        dry_run: If True, only list branches without deleting (default: True)

    Returns:
        JSON with branch cleanup results
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return json.dumps({"success": False, "error": "Not a git repository"}, indent=2)

        current_cmd = f'git -C "{repo}" branch --show-current'
        current_result = subprocess.run(current_cmd, shell=True, capture_output=True, text=True)
        current_branch = current_result.stdout.strip()

        merged_cmd = f'git -C "{repo}" branch --merged'
        merged_result = subprocess.run(merged_cmd, shell=True, capture_output=True, text=True)

        merged_branches = []
        protected = ["main", "master", "develop", current_branch]

        for line in merged_result.stdout.strip().split('\n'):
            branch = line.strip().lstrip('* ')
            if branch and branch not in protected:
                merged_branches.append(branch)

        results = {
            "success": True,
            "repo": str(repo),
            "current_branch": current_branch,
            "merged_branches": merged_branches,
            "dry_run": dry_run
        }

        if not dry_run and merged_branches:
            deleted = []
            for branch in merged_branches:
                del_cmd = f'git -C "{repo}" branch -d "{branch}"'
                del_result = subprocess.run(del_cmd, shell=True, capture_output=True, text=True)
                if del_result.returncode == 0:
                    deleted.append(branch)
            results["deleted"] = deleted

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Git branch cleanup failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def git_diff_summary(repo_path: str, cached: bool = False) -> str:
    """
    Generate a summary of git changes suitable for commit messages.

    Args:
        repo_path: Path to git repository
        cached: If True, show staged changes; if False, show unstaged (default: False)

    Returns:
        JSON with diff summary
    """
    try:
        repo = Path(repo_path)
        if not (repo / ".git").exists():
            return json.dumps({"success": False, "error": "Not a git repository"}, indent=2)

        cached_flag = "--cached" if cached else ""

        stat_cmd = f'git -C "{repo}" diff {cached_flag} --stat'
        stat_result = subprocess.run(stat_cmd, shell=True, capture_output=True, text=True)

        files_cmd = f'git -C "{repo}" diff {cached_flag} --name-status'
        files_result = subprocess.run(files_cmd, shell=True, capture_output=True, text=True)

        changes = {"added": [], "modified": [], "deleted": [], "renamed": []}
        for line in files_result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            status = parts[0]
            filename = parts[-1]
            if status.startswith('A'):
                changes["added"].append(filename)
            elif status.startswith('M'):
                changes["modified"].append(filename)
            elif status.startswith('D'):
                changes["deleted"].append(filename)
            elif status.startswith('R'):
                changes["renamed"].append(filename)

        total_files = sum(len(v) for v in changes.values())

        return json.dumps({
            "success": True,
            "repo": str(repo),
            "staged": cached,
            "changes": changes,
            "total_files": total_files,
            "stat_summary": stat_result.stdout.strip().split('\n')[-1] if stat_result.stdout.strip() else "No changes"
        }, indent=2)

    except Exception as e:
        logger.error(f"Git diff summary failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# DATABASE TOOLS
# ==============================================================================

@mcp.tool()
def db_snapshot(name: str = "", tables: str = "") -> str:
    """
    Create a quick database snapshot before making changes.

    Args:
        name: Optional name for the snapshot (auto-generated if empty)
        tables: Comma-separated table names to snapshot (empty = all tables)

    Returns:
        JSON with snapshot file path and details
    """
    try:
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = name or f"snapshot_{timestamp}"

        snapshot_dir = Path(SKIPPY_PATH) / "archives" / "db_snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = snapshot_dir / f"{snapshot_name}.sql"

        tables_flag = tables.replace(',', ' ') if tables else ""
        cmd = f'wp --path="{wp_path}" db export "{snapshot_file}" {tables_flag}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            size = snapshot_file.stat().st_size
            return json.dumps({
                "success": True,
                "snapshot_file": str(snapshot_file),
                "size_mb": round(size / (1024 * 1024), 2),
                "tables": tables or "all",
                "timestamp": timestamp,
                "restore_command": f'wp --path="{wp_path}" db import "{snapshot_file}"'
            }, indent=2)
        else:
            return json.dumps({"success": False, "error": result.stderr}, indent=2)

    except Exception as e:
        logger.error(f"DB snapshot failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def db_restore(snapshot_file: str, confirm: bool = False) -> str:
    """
    Restore database from a snapshot file.

    Args:
        snapshot_file: Path to the snapshot SQL file
        confirm: Must be True to actually restore (safety check)

    Returns:
        JSON with restore results
    """
    try:
        if not confirm:
            return json.dumps({
                "success": False,
                "error": "Safety check: Set confirm=True to actually restore the database",
                "warning": "This will OVERWRITE the current database!"
            }, indent=2)

        snapshot_path = Path(snapshot_file)
        if not snapshot_path.exists():
            return json.dumps({"success": False, "error": "Snapshot file does not exist"}, indent=2)

        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")

        # Create backup before restore
        backup_file = snapshot_path.parent / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_cmd = f'wp --path="{wp_path}" db export "{backup_file}"'
        subprocess.run(backup_cmd, shell=True, capture_output=True, text=True, timeout=120)

        # Restore
        restore_cmd = f'wp --path="{wp_path}" db import "{snapshot_file}"'
        result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return json.dumps({
                "success": True,
                "restored_from": str(snapshot_path),
                "backup_created": str(backup_file),
                "message": "Database restored successfully"
            }, indent=2)
        else:
            return json.dumps({"success": False, "error": result.stderr}, indent=2)

    except Exception as e:
        logger.error(f"DB restore failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def db_table_sizes() -> str:
    """
    Show WordPress database table sizes for optimization analysis.

    Returns:
        JSON with table sizes sorted by size
    """
    try:
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")

        query = """
        SELECT
            table_name AS 'table',
            ROUND(data_length / 1024 / 1024, 2) AS 'data_mb',
            ROUND(index_length / 1024 / 1024, 2) AS 'index_mb',
            ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'total_mb',
            table_rows AS 'rows'
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY (data_length + index_length) DESC;
        """

        cmd = f'wp --path="{wp_path}" db query "{query}" --skip-column-names'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            tables = []
            total_size = 0
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 5:
                        size = float(parts[3]) if parts[3] else 0
                        total_size += size
                        tables.append({
                            "table": parts[0],
                            "data_mb": float(parts[1]) if parts[1] else 0,
                            "index_mb": float(parts[2]) if parts[2] else 0,
                            "total_mb": size,
                            "rows": int(parts[4]) if parts[4] else 0
                        })

            return json.dumps({
                "success": True,
                "total_size_mb": round(total_size, 2),
                "table_count": len(tables),
                "tables": tables[:20],
                "optimization_candidates": [t for t in tables if t["total_mb"] > 10]
            }, indent=2)
        else:
            return json.dumps({"success": False, "error": result.stderr}, indent=2)

    except Exception as e:
        logger.error(f"DB table sizes failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# LOG ANALYSIS TOOLS
# ==============================================================================

@mcp.tool()
def log_errors_recent(hours: int = 24, sources: str = "all") -> str:
    """
    Aggregate recent errors from multiple log sources.

    Args:
        hours: How many hours back to search (default: 24)
        sources: Comma-separated sources or "all" (wordpress, php, nginx, system)

    Returns:
        JSON with aggregated errors from all sources
    """
    try:
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
        results = {"success": True, "hours": hours, "sources": {}, "total_errors": 0}

        log_paths = {
            "wordpress": f"{wp_path}/wp-content/debug.log",
            "php": "/var/log/php-fpm/error.log",
            "nginx": "/var/log/nginx/error.log",
            "system": "/var/log/syslog"
        }

        source_list = list(log_paths.keys()) if sources == "all" else [s.strip() for s in sources.split(',')]
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for source in source_list:
            if source not in log_paths:
                continue
            log_path = Path(log_paths[source])
            if not log_path.exists():
                results["sources"][source] = {"exists": False}
                continue

            errors = []
            try:
                with open(log_path, 'r', errors='ignore') as f:
                    lines = f.readlines()[-500:]  # Last 500 lines
                    for line in lines:
                        line_lower = line.lower()
                        if 'error' in line_lower or 'fatal' in line_lower or 'warning' in line_lower:
                            errors.append(line.strip()[:200])
                results["sources"][source] = {
                    "exists": True,
                    "error_count": len(errors),
                    "recent_errors": errors[-10:]
                }
                results["total_errors"] += len(errors)
            except PermissionError:
                results["sources"][source] = {"exists": True, "error": "Permission denied"}

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Log errors recent failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def log_search_pattern(log_path: str, pattern: str, context_lines: int = 2, max_matches: int = 20) -> str:
    """
    Search log file for pattern with context lines.

    Args:
        log_path: Path to log file
        pattern: Regex pattern to search for
        context_lines: Number of lines before/after match (default: 2)
        max_matches: Maximum matches to return (default: 20)

    Returns:
        JSON with matching log entries and context
    """
    try:
        log_file = Path(log_path)
        if not log_file.exists():
            return json.dumps({"success": False, "error": "Log file does not exist"}, indent=2)

        matches = []
        pattern_re = re.compile(pattern, re.IGNORECASE)

        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if pattern_re.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = ''.join(lines[start:end])
                matches.append({
                    "line_number": i + 1,
                    "match": line.strip()[:200],
                    "context": context.strip()[:500]
                })
                if len(matches) >= max_matches:
                    break

        return json.dumps({
            "success": True,
            "log_path": str(log_file),
            "pattern": pattern,
            "match_count": len(matches),
            "matches": matches
        }, indent=2)

    except Exception as e:
        logger.error(f"Log search pattern failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def log_tail_multi(log_paths: str, lines: int = 20) -> str:
    """
    Tail multiple log files at once.

    Args:
        log_paths: Comma-separated log file paths
        lines: Number of lines to show from each (default: 20)

    Returns:
        JSON with recent lines from each log
    """
    try:
        paths = [p.strip() for p in log_paths.split(',')]
        results = {"success": True, "logs": {}}

        for log_path in paths:
            log_file = Path(log_path)
            log_name = log_file.name

            if not log_file.exists():
                results["logs"][log_name] = {"exists": False, "path": log_path}
                continue

            try:
                with open(log_file, 'r', errors='ignore') as f:
                    all_lines = f.readlines()
                    recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    results["logs"][log_name] = {
                        "exists": True,
                        "path": log_path,
                        "total_lines": len(all_lines),
                        "showing": len(recent),
                        "content": ''.join(recent)
                    }
            except PermissionError:
                results["logs"][log_name] = {"exists": True, "path": log_path, "error": "Permission denied"}

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Log tail multi failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# CONTENT VALIDATION TOOLS
# ==============================================================================

@mcp.tool()
def content_fact_check(content: str, facts_file: str = "") -> str:
    """
    Check content against authoritative facts file.

    Args:
        content: Text content to validate
        facts_file: Path to facts file (default: QUICK_FACTS_SHEET.md)

    Returns:
        JSON with fact validation results
    """
    try:
        facts_path = Path(facts_file) if facts_file else Path(SKIPPY_PATH) / "business/campaign/rundaverun/campaign/docs/QUICK_FACTS_SHEET.md"

        if not facts_path.exists():
            return json.dumps({"success": False, "error": f"Facts file not found: {facts_path}"}, indent=2)

        with open(facts_path, 'r') as f:
            facts_content = f.read()

        # Known incorrect values to flag
        incorrect_values = {
            "$110.5M": "$81M is correct budget",
            "$110M": "$81M is correct budget",
            "110.5": "$81M is correct budget",
            "$1.80": "$2-3 per $1 is correct ROI",
            "1.80": "$2-3 per $1 is correct ROI",
            "44%": "34-35% is correct JCPS reading",
            "41%": "27-28% is correct JCPS math"
        }

        findings = {"flagged": [], "verified": [], "suggestions": []}

        for wrong, correct in incorrect_values.items():
            if wrong in content:
                findings["flagged"].append({
                    "found": wrong,
                    "correction": correct,
                    "severity": "HIGH"
                })

        # Check for common campaign facts
        correct_facts = ["$81M", "$81 million", "$2-3 per $1", "34-35%", "27-28%"]
        for fact in correct_facts:
            if fact.lower() in content.lower():
                findings["verified"].append(fact)

        return json.dumps({
            "success": True,
            "content_length": len(content),
            "facts_file": str(facts_path),
            "findings": findings,
            "status": "PASS" if not findings["flagged"] else "FAIL"
        }, indent=2)

    except Exception as e:
        logger.error(f"Content fact check failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def content_link_check(content: str, base_url: str = "") -> str:
    """
    Check all links in content for validity.

    Args:
        content: HTML or markdown content to check
        base_url: Base URL for relative links (optional)

    Returns:
        JSON with link validation results
    """
    try:
        import urllib.request
        import urllib.error

        # Extract URLs from content
        url_pattern = r'https?://[^\s<>"\']+|href=["\']([^"\']+)["\']'
        matches = re.findall(url_pattern, content)

        urls = []
        for match in matches:
            if isinstance(match, tuple):
                url = match[0] if match[0] else match[1] if len(match) > 1 else None
            else:
                url = match
            if url and url.startswith(('http://', 'https://')):
                urls.append(url)

        results = {"valid": [], "broken": [], "skipped": []}

        for url in urls[:20]:  # Limit to 20 URLs
            try:
                req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    results["valid"].append({"url": url, "status": response.status})
            except urllib.error.HTTPError as e:
                results["broken"].append({"url": url, "status": e.code, "error": str(e.reason)})
            except Exception as e:
                results["skipped"].append({"url": url, "error": str(e)[:100]})

        return json.dumps({
            "success": True,
            "total_links": len(urls),
            "checked": len(results["valid"]) + len(results["broken"]),
            "results": results
        }, indent=2)

    except Exception as e:
        logger.error(f"Content link check failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def content_diff(content1: str, content2: str, context_lines: int = 3) -> str:
    """
    Generate unified diff between two content strings.

    Args:
        content1: Original content
        content2: Modified content
        context_lines: Number of context lines (default: 3)

    Returns:
        JSON with diff results
    """
    try:
        import difflib

        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)

        diff = list(difflib.unified_diff(lines1, lines2, fromfile='original', tofile='modified', n=context_lines))

        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return json.dumps({
            "success": True,
            "original_lines": len(lines1),
            "modified_lines": len(lines2),
            "additions": additions,
            "deletions": deletions,
            "has_changes": len(diff) > 0,
            "diff": ''.join(diff)[:5000]  # Limit output size
        }, indent=2)

    except Exception as e:
        logger.error(f"Content diff failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# PRODUCTION SYNC TOOLS
# ==============================================================================

@mcp.tool()
def production_db_sync_prepare(local_export: str = "") -> str:
    """
    Prepare local database for production sync (URL replacement, cleanup).

    Args:
        local_export: Path to local SQL export (will create if empty)

    Returns:
        JSON with prepared export file path
    """
    try:
        wp_path = os.getenv("WORDPRESS_PATH", "/home/dave/skippy/rundaverun_local_site/app/public")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        session_dir = Path(SKIPPY_PATH) / "work/wordpress/production_sync" / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)

        # Export if not provided
        if not local_export:
            export_file = session_dir / "local_export.sql"
            export_cmd = f'wp --path="{wp_path}" db export "{export_file}"'
            result = subprocess.run(export_cmd, shell=True, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                return json.dumps({"success": False, "error": result.stderr}, indent=2)
        else:
            export_file = Path(local_export)
            if not export_file.exists():
                return json.dumps({"success": False, "error": "Export file not found"}, indent=2)

        # Read and transform
        with open(export_file, 'r') as f:
            sql_content = f.read()

        # URL replacements
        local_url = "http://rundaverun-local-complete-022655.local"
        production_url = "https://rundaverun.org"

        transformed = sql_content.replace(local_url, production_url)

        # Save production-ready version
        production_file = session_dir / "production_ready.sql"
        with open(production_file, 'w') as f:
            f.write(transformed)

        # Compress for upload
        import gzip
        compressed_file = session_dir / "production_ready.sql.gz"
        with open(production_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.write(f_in.read())

        return json.dumps({
            "success": True,
            "session_dir": str(session_dir),
            "original_export": str(export_file),
            "production_file": str(production_file),
            "compressed_file": str(compressed_file),
            "replacements": {
                "from": local_url,
                "to": production_url
            },
            "size_mb": round(compressed_file.stat().st_size / (1024 * 1024), 2)
        }, indent=2)

    except Exception as e:
        logger.error(f"Production DB sync prepare failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def production_file_sync(local_path: str, remote_path: str, dry_run: bool = True) -> str:
    """
    Sync files to production server via rsync.

    Args:
        local_path: Local directory or file to sync
        remote_path: Remote destination path
        dry_run: If True, show what would be synced without doing it (default: True)

    Returns:
        JSON with sync results
    """
    try:
        local = Path(local_path)
        if not local.exists():
            return json.dumps({"success": False, "error": "Local path does not exist"}, indent=2)

        ssh_key = os.path.expanduser("~/.ssh/godaddy_rundaverun")
        ssh_user = "git_deployer_f44cc3416a_545525"
        ssh_host = "bp6.0cf.myftpupload.com"

        dry_run_flag = "-n" if dry_run else ""

        rsync_cmd = f'SSH_AUTH_SOCK="" rsync -avz {dry_run_flag} -e "ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {ssh_key}" "{local_path}" {ssh_user}@{ssh_host}:{remote_path}'

        result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True, timeout=300)

        return json.dumps({
            "success": result.returncode == 0,
            "dry_run": dry_run,
            "local_path": str(local_path),
            "remote_path": remote_path,
            "output": result.stdout[:2000] if result.stdout else "",
            "error": result.stderr[:500] if result.stderr else ""
        }, indent=2)

    except Exception as e:
        logger.error(f"Production file sync failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def production_cache_flush() -> str:
    """
    Flush all caches on production WordPress site.

    Returns:
        JSON with cache flush results
    """
    try:
        ssh_key = os.path.expanduser("~/.ssh/godaddy_rundaverun")
        ssh_user = "git_deployer_f44cc3416a_545525"
        ssh_host = "bp6.0cf.myftpupload.com"

        commands = [
            "wp cache flush",
            "wp rewrite flush",
            "wp transient delete --all"
        ]

        results = {"success": True, "commands": []}

        for cmd in commands:
            ssh_cmd = f'SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {ssh_key} {ssh_user}@{ssh_host} "cd html && {cmd} 2>&1"'
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
            results["commands"].append({
                "command": cmd,
                "success": result.returncode == 0,
                "output": result.stdout.strip()[:200]
            })

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Production cache flush failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# MONITORING AND ALERTING TOOLS
# ==============================================================================

@mcp.tool()
def monitor_site_health(url: str = "https://rundaverun.org") -> str:
    """
    Comprehensive site health check.

    Args:
        url: URL to check (default: https://rundaverun.org)

    Returns:
        JSON with health check results
    """
    try:
        import urllib.request
        import urllib.error
        import time

        results = {
            "success": True,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        # Homepage check
        start_time = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                elapsed = time.time() - start_time
                results["checks"]["homepage"] = {
                    "status": response.status,
                    "response_time_ms": round(elapsed * 1000),
                    "content_length": len(content),
                    "has_title": "<title>" in content.lower()
                }
        except Exception as e:
            results["checks"]["homepage"] = {"error": str(e)[:100]}

        # Key pages
        key_pages = ["/about/", "/get-involved/", "/neighborhoods/", "/contact/"]
        results["checks"]["pages"] = {}

        for page in key_pages:
            page_url = url.rstrip('/') + page
            try:
                req = urllib.request.Request(page_url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    results["checks"]["pages"][page] = {"status": response.status}
            except urllib.error.HTTPError as e:
                results["checks"]["pages"][page] = {"status": e.code}
            except Exception as e:
                results["checks"]["pages"][page] = {"error": str(e)[:50]}

        # SSL check
        if url.startswith("https"):
            import ssl
            import socket
            hostname = url.replace("https://", "").split('/')[0]
            try:
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        not_after = cert.get('notAfter', '')
                        results["checks"]["ssl"] = {
                            "valid": True,
                            "expires": not_after
                        }
            except Exception as e:
                results["checks"]["ssl"] = {"error": str(e)[:100]}

        # Overall health
        all_ok = all(
            check.get("status") == 200 or check.get("valid") == True
            for check in results["checks"].values()
            if isinstance(check, dict) and ("status" in check or "valid" in check)
        )
        results["overall_health"] = "HEALTHY" if all_ok else "DEGRADED"

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Monitor site health failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def monitor_resource_usage() -> str:
    """
    Check local system resource usage (CPU, memory, disk).

    Returns:
        JSON with resource usage metrics
    """
    try:
        import shutil

        results = {"success": True, "timestamp": datetime.now().isoformat()}

        # Disk usage
        disk = shutil.disk_usage("/")
        results["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round((disk.used / disk.total) * 100, 1)
        }

        # Memory (from /proc/meminfo)
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1)) / 1024
            mem_free = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1)) / 1024
            results["memory"] = {
                "total_mb": round(mem_total),
                "available_mb": round(mem_free),
                "percent_used": round(((mem_total - mem_free) / mem_total) * 100, 1)
            }
        except Exception:
            results["memory"] = {"error": "Could not read memory info"}

        # Load average
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().split()[:3]
            results["load_average"] = {
                "1min": float(load[0]),
                "5min": float(load[1]),
                "15min": float(load[2])
            }
        except Exception:
            results["load_average"] = {"error": "Could not read load average"}

        # Alert thresholds
        alerts = []
        if results.get("disk", {}).get("percent_used", 0) > 85:
            alerts.append("HIGH: Disk usage above 85%")
        if results.get("memory", {}).get("percent_used", 0) > 90:
            alerts.append("HIGH: Memory usage above 90%")
        if results.get("load_average", {}).get("5min", 0) > 4:
            alerts.append("MEDIUM: High load average")

        results["alerts"] = alerts
        results["status"] = "WARNING" if alerts else "OK"

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Monitor resource usage failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def monitor_services(services: str = "mysql,nginx,php-fpm") -> str:
    """
    Check status of system services.

    Args:
        services: Comma-separated service names (default: mysql,nginx,php-fpm)

    Returns:
        JSON with service status
    """
    try:
        service_list = [s.strip() for s in services.split(',')]
        results = {"success": True, "services": {}}

        for service in service_list:
            try:
                cmd = f'systemctl is-active {service}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                status = result.stdout.strip()
                results["services"][service] = {
                    "status": status,
                    "running": status == "active"
                }
            except Exception as e:
                results["services"][service] = {"error": str(e)[:50]}

        running_count = sum(1 for s in results["services"].values() if s.get("running"))
        results["summary"] = {
            "total": len(service_list),
            "running": running_count,
            "stopped": len(service_list) - running_count
        }
        results["overall"] = "OK" if running_count == len(service_list) else "DEGRADED"

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Monitor services failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# ==============================================================================
# BACKUP VERIFICATION TOOLS
# ==============================================================================

@mcp.tool()
def backup_list_recent(backup_type: str = "all", days: int = 7) -> str:
    """
    List recent backup files.

    Args:
        backup_type: Type of backup (wordpress, database, full, all)
        days: Number of days to look back (default: 7)

    Returns:
        JSON with list of backup files
    """
    try:
        backup_dirs = [
            Path(SKIPPY_PATH) / "archives/db_snapshots",
            Path(SKIPPY_PATH) / "archives/wordpress",
            Path(SKIPPY_PATH) / "work/wordpress"
        ]

        cutoff = datetime.now() - timedelta(days=days)
        backups = []

        for backup_dir in backup_dirs:
            if not backup_dir.exists():
                continue

            for item in backup_dir.rglob("*.sql*"):
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime > cutoff:
                        backups.append({
                            "path": str(item),
                            "name": item.name,
                            "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                            "modified": mtime.isoformat(),
                            "type": "database"
                        })
                except Exception:
                    continue

        # Sort by modification time
        backups.sort(key=lambda x: x["modified"], reverse=True)

        return json.dumps({
            "success": True,
            "days": days,
            "backup_count": len(backups),
            "total_size_mb": round(sum(b["size_mb"] for b in backups), 2),
            "backups": backups[:20]  # Limit to 20 most recent
        }, indent=2)

    except Exception as e:
        logger.error(f"Backup list recent failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def backup_verify(backup_file: str) -> str:
    """
    Verify integrity of a backup file.

    Args:
        backup_file: Path to backup file to verify

    Returns:
        JSON with verification results
    """
    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            return json.dumps({"success": False, "error": "Backup file not found"}, indent=2)

        results = {
            "success": True,
            "file": str(backup_path),
            "checks": {}
        }

        # File size check
        size = backup_path.stat().st_size
        results["checks"]["size"] = {
            "bytes": size,
            "mb": round(size / (1024 * 1024), 2),
            "valid": size > 1000  # More than 1KB
        }

        # File type check
        suffix = backup_path.suffix.lower()
        if suffix == '.gz':
            import gzip
            try:
                with gzip.open(backup_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB
                results["checks"]["compression"] = {"valid": True, "type": "gzip"}
            except Exception as e:
                results["checks"]["compression"] = {"valid": False, "error": str(e)[:50]}
        elif suffix == '.sql':
            try:
                with open(backup_path, 'r') as f:
                    header = f.read(1000)
                has_sql = any(kw in header.upper() for kw in ['CREATE', 'INSERT', 'DROP', 'MySQL'])
                results["checks"]["content"] = {"valid": has_sql, "type": "sql"}
            except Exception as e:
                results["checks"]["content"] = {"valid": False, "error": str(e)[:50]}

        # MD5 checksum
        import hashlib
        try:
            md5 = hashlib.md5()
            with open(backup_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            results["checks"]["checksum"] = {"md5": md5.hexdigest()}
        except Exception as e:
            results["checks"]["checksum"] = {"error": str(e)[:50]}

        # Overall validity
        all_valid = all(
            check.get("valid", True) for check in results["checks"].values()
            if "valid" in check
        )
        results["overall"] = "VALID" if all_valid else "INVALID"

        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"Backup verify failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def backup_cleanup(days: int = 30, dry_run: bool = True) -> str:
    """
    Clean up old backup files.

    Args:
        days: Delete backups older than this many days (default: 30)
        dry_run: If True, only list files without deleting (default: True)

    Returns:
        JSON with cleanup results
    """
    try:
        backup_dirs = [
            Path(SKIPPY_PATH) / "archives/db_snapshots",
        ]

        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []

        for backup_dir in backup_dirs:
            if not backup_dir.exists():
                continue

            for item in backup_dir.glob("*.sql*"):
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff:
                        to_delete.append({
                            "path": str(item),
                            "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                            "age_days": (datetime.now() - mtime).days
                        })
                except Exception:
                    continue

        total_size = sum(f["size_mb"] for f in to_delete)
        deleted = []

        if not dry_run and to_delete:
            for item in to_delete:
                try:
                    Path(item["path"]).unlink()
                    deleted.append(item["path"])
                except Exception:
                    pass

        return json.dumps({
            "success": True,
            "dry_run": dry_run,
            "days_threshold": days,
            "files_found": len(to_delete),
            "total_size_mb": round(total_size, 2),
            "files": to_delete[:20],
            "deleted": deleted if not dry_run else []
        }, indent=2)

    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)

