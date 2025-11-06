#!/usr/bin/env python3
"""
Skippy System Manager - Enhanced Error Handling
Version: 1.0.0
Purpose: Centralized error handling with context, recovery suggestions, and user-friendly messages
"""

import sys
import traceback
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class SkippyError(Exception):
    """Base exception class for all Skippy errors"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recovery_suggestions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_suggestions = recovery_suggestions or []
        self.context = context or {}
        self.original_exception = original_exception

    def __str__(self):
        """User-friendly error message"""
        output = [f"[{self.severity.value.upper()}] {self.message}"]

        if self.context:
            output.append("\nContext:")
            for key, value in self.context.items():
                output.append(f"  {key}: {value}")

        if self.recovery_suggestions:
            output.append("\nRecovery Suggestions:")
            for i, suggestion in enumerate(self.recovery_suggestions, 1):
                output.append(f"  {i}. {suggestion}")

        return "\n".join(output)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_suggestions": self.recovery_suggestions,
            "context": self.context,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }


class ConfigurationError(SkippyError):
    """Configuration-related errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        kwargs.setdefault('recovery_suggestions', [
            "Check config.env file exists and is properly formatted",
            "Verify all required environment variables are set",
            "Run: ./scripts/utility/validate_config.sh"
        ])
        super().__init__(message, **kwargs)


class NetworkError(SkippyError):
    """Network-related errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        kwargs.setdefault('recovery_suggestions', [
            "Check network connectivity",
            "Verify firewall rules allow connections",
            "Test DNS resolution",
            "Try pinging the remote host"
        ])
        super().__init__(message, **kwargs)


class FilesystemError(SkippyError):
    """Filesystem-related errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.FILESYSTEM)
        kwargs.setdefault('recovery_suggestions', [
            "Check if path exists and is accessible",
            "Verify file permissions",
            "Ensure sufficient disk space",
            "Check filesystem is mounted correctly"
        ])
        super().__init__(message, **kwargs)


class AuthenticationError(SkippyError):
    """Authentication-related errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.AUTHENTICATION)
        kwargs.setdefault('recovery_suggestions', [
            "Verify credentials are correct",
            "Check SSH key is properly configured",
            "Ensure user has proper permissions",
            "Try: ./scripts/security/migrate_to_ssh_keys_v1.0.0.sh"
        ])
        super().__init__(message, **kwargs)


class PermissionError(SkippyError):
    """Permission-related errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.PERMISSION)
        kwargs.setdefault('recovery_suggestions', [
            "Check file/directory permissions",
            "Verify user has necessary privileges",
            "Consider using sudo if appropriate",
            "Review group memberships"
        ])
        super().__init__(message, **kwargs)


class ValidationError(SkippyError):
    """Input validation errors"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.VALIDATION)
        kwargs.setdefault('severity', ErrorSeverity.WARNING)
        kwargs.setdefault('recovery_suggestions', [
            "Check input format and values",
            "Refer to documentation for valid inputs",
            "Use --help flag for usage information"
        ])
        super().__init__(message, **kwargs)


class ExternalServiceError(SkippyError):
    """External service errors (WordPress, APIs, etc.)"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.EXTERNAL_SERVICE)
        kwargs.setdefault('recovery_suggestions', [
            "Check if service is running",
            "Verify service configuration",
            "Review service logs for errors",
            "Test service connectivity independently"
        ])
        super().__init__(message, **kwargs)


class ResourceError(SkippyError):
    """Resource exhaustion errors (disk, memory, etc.)"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.RESOURCE)
        kwargs.setdefault('severity', ErrorSeverity.CRITICAL)
        kwargs.setdefault('recovery_suggestions', [
            "Check available disk space",
            "Monitor system memory usage",
            "Clean up temporary files",
            "Review system resource limits"
        ])
        super().__init__(message, **kwargs)


class ErrorHandler:
    """Centralized error handling and reporting"""

    def __init__(self, log_errors: bool = True, raise_on_critical: bool = True):
        self.log_errors = log_errors
        self.raise_on_critical = raise_on_critical
        self.error_history: List[SkippyError] = []

    def handle(self, error: SkippyError, exit_on_critical: bool = False) -> None:
        """
        Handle an error with logging and optional exit

        Args:
            error: The SkippyError to handle
            exit_on_critical: Exit program if error is critical
        """
        self.error_history.append(error)

        # Log the error
        if self.log_errors:
            log_level = {
                ErrorSeverity.INFO: logging.INFO,
                ErrorSeverity.WARNING: logging.WARNING,
                ErrorSeverity.ERROR: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(error.severity, logging.ERROR)

            logger.log(log_level, str(error))

            if error.original_exception:
                logger.debug("Original exception traceback:", exc_info=error.original_exception)

        # Print to stderr for user visibility
        print(str(error), file=sys.stderr)

        # Exit on critical if configured
        if error.severity == ErrorSeverity.CRITICAL and (self.raise_on_critical or exit_on_critical):
            sys.exit(1)

    def wrap_exception(self, exc: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN) -> SkippyError:
        """
        Wrap a standard Python exception in a SkippyError

        Args:
            exc: The exception to wrap
            category: Error category to assign

        Returns:
            SkippyError wrapping the original exception
        """
        error_map = {
            FileNotFoundError: (FilesystemError, "File or directory not found"),
            PermissionError: (PermissionError, "Permission denied"),
            ConnectionError: (NetworkError, "Network connection failed"),
            TimeoutError: (NetworkError, "Operation timed out"),
            ValueError: (ValidationError, "Invalid value provided"),
            KeyError: (ConfigurationError, "Missing required configuration"),
        }

        error_class, default_message = error_map.get(type(exc), (SkippyError, str(exc)))

        return error_class(
            message=f"{default_message}: {str(exc)}",
            original_exception=exc,
            context={"exception_type": type(exc).__name__}
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        return {
            "total_errors": len(self.error_history),
            "by_severity": {
                severity.value: sum(1 for e in self.error_history if e.severity == severity)
                for severity in ErrorSeverity
            },
            "by_category": {
                category.value: sum(1 for e in self.error_history if e.category == category)
                for category in ErrorCategory
            },
            "recent_errors": [e.to_dict() for e in self.error_history[-5:]]
        }


# Global error handler instance
_global_handler = ErrorHandler()


def handle_error(error: SkippyError, exit_on_critical: bool = False) -> None:
    """Convenience function to handle errors using global handler"""
    _global_handler.handle(error, exit_on_critical)


def wrap_exception(exc: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN) -> SkippyError:
    """Convenience function to wrap exceptions using global handler"""
    return _global_handler.wrap_exception(exc, category)


def get_error_summary() -> Dict[str, Any]:
    """Convenience function to get error summary from global handler"""
    return _global_handler.get_error_summary()


# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN, exit_on_error: bool = False):
    """
    Decorator to automatically handle exceptions in functions

    Usage:
        @handle_errors(category=ErrorCategory.NETWORK)
        def connect_to_server():
            # function code
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SkippyError as e:
                handle_error(e, exit_on_critical=exit_on_error)
                raise
            except Exception as e:
                skippy_error = wrap_exception(e, category)
                handle_error(skippy_error, exit_on_critical=exit_on_error)
                raise skippy_error from e
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    print("Skippy Error Handling Library - Examples\n")

    # Example 1: Configuration error
    try:
        raise ConfigurationError(
            "Missing required environment variable: SKIPPY_BASE_PATH",
            context={"config_file": "config.env", "variable": "SKIPPY_BASE_PATH"}
        )
    except SkippyError as e:
        handle_error(e)

    print("\n" + "="*60 + "\n")

    # Example 2: Network error
    try:
        raise NetworkError(
            "Failed to connect to remote server",
            context={"host": "example.com", "port": 22, "timeout": 30},
            severity=ErrorSeverity.CRITICAL
        )
    except SkippyError as e:
        handle_error(e)

    print("\n" + "="*60 + "\n")

    # Example 3: Wrapping standard exception
    try:
        open("/nonexistent/file.txt")
    except Exception as e:
        skippy_error = wrap_exception(e)
        handle_error(skippy_error)

    print("\n" + "="*60 + "\n")

    # Show error summary
    print("Error Summary:")
    summary = get_error_summary()
    print(f"Total errors: {summary['total_errors']}")
    print(f"By severity: {summary['by_severity']}")
    print(f"By category: {summary['by_category']}")
