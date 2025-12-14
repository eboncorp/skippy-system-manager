"""
Unit tests for skippy_errors module.

Tests cover:
- ErrorSeverity and ErrorCategory enums
- SkippyError base exception class
- Specialized exception classes
- ErrorHandler class
- Global convenience functions
- handle_errors decorator
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from skippy_errors import (
    ErrorSeverity,
    ErrorCategory,
    SkippyError,
    ConfigurationError,
    NetworkError,
    FilesystemError,
    AuthenticationError,
    PermissionError as SkippyPermissionError,
    ValidationError,
    ExternalServiceError,
    ResourceError,
    ErrorHandler,
    handle_error,
    wrap_exception,
    get_error_summary,
    handle_errors,
)


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_severity_values(self):
        """Test all severity levels exist with correct values."""
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_severity_count(self):
        """Test we have exactly 4 severity levels."""
        assert len(ErrorSeverity) == 4


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_category_values(self):
        """Test all category values exist."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.FILESYSTEM.value == "filesystem"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.PERMISSION.value == "permission"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.EXTERNAL_SERVICE.value == "external_service"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.UNKNOWN.value == "unknown"

    def test_category_count(self):
        """Test we have exactly 9 categories."""
        assert len(ErrorCategory) == 9


# =============================================================================
# BASE EXCEPTION TESTS
# =============================================================================

class TestSkippyError:
    """Tests for SkippyError base exception class."""

    def test_basic_creation(self):
        """Test creating error with just a message."""
        error = SkippyError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.ERROR
        assert error.recovery_suggestions == []
        assert error.context == {}
        assert error.original_exception is None

    def test_full_creation(self):
        """Test creating error with all parameters."""
        original = ValueError("Original error")
        error = SkippyError(
            message="Full error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.CRITICAL,
            recovery_suggestions=["Try again", "Check connection"],
            context={"host": "example.com", "port": 80},
            original_exception=original
        )
        assert error.message == "Full error"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recovery_suggestions == ["Try again", "Check connection"]
        assert error.context == {"host": "example.com", "port": 80}
        assert error.original_exception is original

    def test_str_basic(self):
        """Test string representation with basic error."""
        error = SkippyError("Test error")
        result = str(error)
        assert "[ERROR] Test error" in result

    def test_str_with_context(self):
        """Test string representation includes context."""
        error = SkippyError(
            "Test error",
            context={"key1": "value1", "key2": "value2"}
        )
        result = str(error)
        assert "Context:" in result
        assert "key1: value1" in result
        assert "key2: value2" in result

    def test_str_with_suggestions(self):
        """Test string representation includes recovery suggestions."""
        error = SkippyError(
            "Test error",
            recovery_suggestions=["First suggestion", "Second suggestion"]
        )
        result = str(error)
        assert "Recovery Suggestions:" in result
        assert "1. First suggestion" in result
        assert "2. Second suggestion" in result

    def test_str_severity_levels(self):
        """Test string representation shows correct severity."""
        for severity in ErrorSeverity:
            error = SkippyError("Test", severity=severity)
            assert f"[{severity.value.upper()}]" in str(error)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        original = ValueError("Original")
        error = SkippyError(
            message="Dict test",
            category=ErrorCategory.FILESYSTEM,
            severity=ErrorSeverity.WARNING,
            recovery_suggestions=["Suggestion 1"],
            context={"path": "/tmp/file"},
            original_exception=original
        )
        result = error.to_dict()

        assert result["message"] == "Dict test"
        assert result["category"] == "filesystem"
        assert result["severity"] == "warning"
        assert result["recovery_suggestions"] == ["Suggestion 1"]
        assert result["context"] == {"path": "/tmp/file"}
        assert result["original_exception"] == "Original"

    def test_to_dict_no_original_exception(self):
        """Test to_dict when no original exception."""
        error = SkippyError("Test")
        result = error.to_dict()
        assert result["original_exception"] is None

    def test_is_exception(self):
        """Test that SkippyError can be raised and caught as Exception."""
        with pytest.raises(Exception):
            raise SkippyError("Test")

    def test_exception_args(self):
        """Test that message is accessible via args."""
        error = SkippyError("Test message")
        assert error.args[0] == "Test message"


# =============================================================================
# SPECIALIZED EXCEPTION TESTS
# =============================================================================

class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_default_category(self):
        """Test default category is CONFIGURATION."""
        error = ConfigurationError("Config missing")
        assert error.category == ErrorCategory.CONFIGURATION

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = ConfigurationError("Config missing")
        assert len(error.recovery_suggestions) > 0
        assert any("config" in s.lower() for s in error.recovery_suggestions)

    def test_override_suggestions(self):
        """Test can override default suggestions."""
        error = ConfigurationError(
            "Config missing",
            recovery_suggestions=["Custom suggestion"]
        )
        assert error.recovery_suggestions == ["Custom suggestion"]


class TestNetworkError:
    """Tests for NetworkError."""

    def test_default_category(self):
        """Test default category is NETWORK."""
        error = NetworkError("Connection failed")
        assert error.category == ErrorCategory.NETWORK

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = NetworkError("Connection failed")
        assert len(error.recovery_suggestions) > 0
        assert any("network" in s.lower() or "connect" in s.lower()
                   for s in error.recovery_suggestions)


class TestFilesystemError:
    """Tests for FilesystemError."""

    def test_default_category(self):
        """Test default category is FILESYSTEM."""
        error = FilesystemError("File not found")
        assert error.category == ErrorCategory.FILESYSTEM

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = FilesystemError("File not found")
        assert len(error.recovery_suggestions) > 0
        assert any("path" in s.lower() or "file" in s.lower() or "disk" in s.lower()
                   for s in error.recovery_suggestions)


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_category(self):
        """Test default category is AUTHENTICATION."""
        error = AuthenticationError("Login failed")
        assert error.category == ErrorCategory.AUTHENTICATION

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = AuthenticationError("Login failed")
        assert len(error.recovery_suggestions) > 0
        assert any("credential" in s.lower() or "ssh" in s.lower() or "permission" in s.lower()
                   for s in error.recovery_suggestions)


class TestSkippyPermissionError:
    """Tests for PermissionError (Skippy version)."""

    def test_default_category(self):
        """Test default category is PERMISSION."""
        error = SkippyPermissionError("Access denied")
        assert error.category == ErrorCategory.PERMISSION

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = SkippyPermissionError("Access denied")
        assert len(error.recovery_suggestions) > 0
        assert any("permission" in s.lower() or "privilege" in s.lower()
                   for s in error.recovery_suggestions)


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_category(self):
        """Test default category is VALIDATION."""
        error = ValidationError("Invalid input")
        assert error.category == ErrorCategory.VALIDATION

    def test_default_severity(self):
        """Test default severity is WARNING."""
        error = ValidationError("Invalid input")
        assert error.severity == ErrorSeverity.WARNING

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = ValidationError("Invalid input")
        assert len(error.recovery_suggestions) > 0


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_default_category(self):
        """Test default category is EXTERNAL_SERVICE."""
        error = ExternalServiceError("API failed")
        assert error.category == ErrorCategory.EXTERNAL_SERVICE

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = ExternalServiceError("API failed")
        assert len(error.recovery_suggestions) > 0
        assert any("service" in s.lower() for s in error.recovery_suggestions)


class TestResourceError:
    """Tests for ResourceError."""

    def test_default_category(self):
        """Test default category is RESOURCE."""
        error = ResourceError("Disk full")
        assert error.category == ErrorCategory.RESOURCE

    def test_default_severity(self):
        """Test default severity is CRITICAL."""
        error = ResourceError("Disk full")
        assert error.severity == ErrorSeverity.CRITICAL

    def test_default_suggestions(self):
        """Test has default recovery suggestions."""
        error = ResourceError("Disk full")
        assert len(error.recovery_suggestions) > 0
        assert any("disk" in s.lower() or "memory" in s.lower()
                   for s in error.recovery_suggestions)


# =============================================================================
# ERROR HANDLER TESTS
# =============================================================================

class TestErrorHandler:
    """Tests for ErrorHandler class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        handler = ErrorHandler()
        assert handler.log_errors is True
        assert handler.raise_on_critical is True
        assert handler.error_history == []

    def test_initialization_custom(self):
        """Test custom initialization."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)
        assert handler.log_errors is False
        assert handler.raise_on_critical is False

    def test_handle_adds_to_history(self):
        """Test that handle adds error to history."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)
        error = SkippyError("Test error")

        with patch('sys.stderr', new_callable=StringIO):
            handler.handle(error)

        assert len(handler.error_history) == 1
        assert handler.error_history[0] is error

    def test_handle_prints_to_stderr(self):
        """Test that handle prints to stderr."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)
        error = SkippyError("Test error message")

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            handler.handle(error)
            assert "Test error message" in mock_stderr.getvalue()

    def test_handle_critical_exits(self):
        """Test that critical errors exit when configured."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=True)
        error = SkippyError("Critical error", severity=ErrorSeverity.CRITICAL)

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                handler.handle(error)
            assert exc_info.value.code == 1

    def test_handle_critical_no_exit(self):
        """Test that critical errors don't exit when not configured."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)
        error = SkippyError("Critical error", severity=ErrorSeverity.CRITICAL)

        with patch('sys.stderr', new_callable=StringIO):
            handler.handle(error)  # Should not raise

        assert len(handler.error_history) == 1

    def test_handle_exit_on_critical_param(self):
        """Test exit_on_critical parameter overrides config."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)
        error = SkippyError("Critical error", severity=ErrorSeverity.CRITICAL)

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SystemExit):
                handler.handle(error, exit_on_critical=True)

    def test_wrap_exception_file_not_found(self):
        """Test wrapping FileNotFoundError."""
        handler = ErrorHandler()
        exc = FileNotFoundError("No such file")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, FilesystemError)
        assert "not found" in wrapped.message.lower()
        assert wrapped.original_exception is exc

    def test_wrap_exception_connection_error(self):
        """Test wrapping ConnectionError."""
        handler = ErrorHandler()
        exc = ConnectionError("Connection refused")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, NetworkError)
        assert wrapped.original_exception is exc

    def test_wrap_exception_timeout_error(self):
        """Test wrapping TimeoutError."""
        handler = ErrorHandler()
        exc = TimeoutError("Timed out")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, NetworkError)
        assert "timed out" in wrapped.message.lower()

    def test_wrap_exception_value_error(self):
        """Test wrapping ValueError."""
        handler = ErrorHandler()
        exc = ValueError("Invalid value")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, ValidationError)

    def test_wrap_exception_key_error(self):
        """Test wrapping KeyError."""
        handler = ErrorHandler()
        exc = KeyError("missing_key")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, ConfigurationError)

    def test_wrap_exception_unknown(self):
        """Test wrapping unknown exception type."""
        handler = ErrorHandler()
        exc = RuntimeError("Unknown error")

        wrapped = handler.wrap_exception(exc)

        assert isinstance(wrapped, SkippyError)
        assert wrapped.original_exception is exc
        assert "RuntimeError" in wrapped.context.get("exception_type", "")

    def test_get_error_summary_empty(self):
        """Test error summary with no errors."""
        handler = ErrorHandler()

        summary = handler.get_error_summary()

        assert summary["total_errors"] == 0
        assert all(count == 0 for count in summary["by_severity"].values())
        assert all(count == 0 for count in summary["by_category"].values())
        assert summary["recent_errors"] == []

    def test_get_error_summary_with_errors(self):
        """Test error summary with multiple errors."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)

        with patch('sys.stderr', new_callable=StringIO):
            handler.handle(SkippyError("Error 1", severity=ErrorSeverity.WARNING))
            handler.handle(SkippyError("Error 2", severity=ErrorSeverity.ERROR))
            handler.handle(NetworkError("Error 3"))

        summary = handler.get_error_summary()

        assert summary["total_errors"] == 3
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["error"] == 2
        assert summary["by_category"]["network"] == 1
        assert len(summary["recent_errors"]) == 3

    def test_get_error_summary_limits_recent(self):
        """Test that recent_errors is limited to last 5."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)

        with patch('sys.stderr', new_callable=StringIO):
            for i in range(10):
                handler.handle(SkippyError(f"Error {i}"))

        summary = handler.get_error_summary()

        assert summary["total_errors"] == 10
        assert len(summary["recent_errors"]) == 5
        # Check it's the last 5 errors
        assert summary["recent_errors"][0]["message"] == "Error 5"
        assert summary["recent_errors"][4]["message"] == "Error 9"


# =============================================================================
# GLOBAL FUNCTION TESTS
# =============================================================================

class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_handle_error(self):
        """Test global handle_error function."""
        error = SkippyError("Global test", severity=ErrorSeverity.WARNING)

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            handle_error(error)
            assert "Global test" in mock_stderr.getvalue()

    def test_wrap_exception(self):
        """Test global wrap_exception function."""
        exc = ValueError("Test value error")

        wrapped = wrap_exception(exc)

        assert isinstance(wrapped, ValidationError)
        assert wrapped.original_exception is exc

    def test_wrap_exception_with_category(self):
        """Test global wrap_exception with specific category."""
        exc = RuntimeError("Custom error")

        wrapped = wrap_exception(exc, category=ErrorCategory.NETWORK)

        assert wrapped.context.get("exception_type") == "RuntimeError"

    def test_get_error_summary(self):
        """Test global get_error_summary function."""
        summary = get_error_summary()

        assert "total_errors" in summary
        assert "by_severity" in summary
        assert "by_category" in summary
        assert "recent_errors" in summary


# =============================================================================
# DECORATOR TESTS
# =============================================================================

class TestHandleErrorsDecorator:
    """Tests for handle_errors decorator."""

    def test_decorator_passes_through_success(self):
        """Test that decorator passes through successful function calls."""
        @handle_errors()
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_passes_arguments(self):
        """Test that decorator passes arguments correctly."""
        @handle_errors()
        def add_function(a, b):
            return a + b

        result = add_function(2, 3)
        assert result == 5

    def test_decorator_passes_kwargs(self):
        """Test that decorator passes keyword arguments correctly."""
        @handle_errors()
        def kwargs_function(a, b=10):
            return a + b

        result = kwargs_function(5, b=20)
        assert result == 25

    def test_decorator_handles_skippy_error(self):
        """Test that decorator handles SkippyError."""
        @handle_errors()
        def raise_skippy_error():
            raise ConfigurationError("Test config error")

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(ConfigurationError):
                raise_skippy_error()

    def test_decorator_wraps_standard_exception(self):
        """Test that decorator wraps standard exceptions."""
        @handle_errors(category=ErrorCategory.FILESYSTEM)
        def raise_value_error():
            raise ValueError("Invalid value")

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SkippyError) as exc_info:
                raise_value_error()

            # Should be wrapped as ValidationError (based on ValueError mapping)
            assert isinstance(exc_info.value, ValidationError)

    def test_decorator_uses_category(self):
        """Test that decorator uses specified category for context."""
        @handle_errors(category=ErrorCategory.NETWORK)
        def raise_runtime_error():
            raise RuntimeError("Network issue")

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SkippyError) as exc_info:
                raise_runtime_error()

            assert exc_info.value.context.get("exception_type") == "RuntimeError"

    def test_decorator_preserves_original_exception(self):
        """Test that decorator preserves original exception in chain."""
        @handle_errors()
        def raise_exception():
            raise KeyError("missing")

        with patch('sys.stderr', new_callable=StringIO):
            with pytest.raises(SkippyError) as exc_info:
                raise_exception()

            assert exc_info.value.__cause__ is not None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling workflow."""

    def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        handler = ErrorHandler(log_errors=False, raise_on_critical=False)

        with patch('sys.stderr', new_callable=StringIO):
            # Simulate various errors
            handler.handle(ConfigurationError("Missing config"))
            handler.handle(NetworkError("Connection failed",
                                        context={"host": "example.com"}))

            # Wrap and handle a standard exception
            try:
                raise FileNotFoundError("/path/to/file")
            except Exception as e:
                wrapped = handler.wrap_exception(e)
                handler.handle(wrapped)

        # Verify summary
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 3
        assert summary["by_category"]["configuration"] == 1
        assert summary["by_category"]["network"] == 1
        assert summary["by_category"]["filesystem"] == 1

    def test_error_chaining(self):
        """Test that error chaining works correctly."""
        original = ConnectionError("TCP connection refused")

        network_error = NetworkError(
            "Failed to reach server",
            original_exception=original,
            context={"retry_count": 3}
        )

        # Verify chain
        assert network_error.original_exception is original
        assert "TCP connection refused" in str(original)
        assert network_error.context["retry_count"] == 3

        # Verify to_dict includes original exception message
        error_dict = network_error.to_dict()
        assert error_dict["original_exception"] == "TCP connection refused"
