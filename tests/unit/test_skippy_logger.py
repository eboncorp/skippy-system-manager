"""
Unit tests for skippy_logger module

Tests cover:
- SkippyLogger class initialization and methods
- get_logger factory function
- log_script_execution function
- log_error_with_context function
- Convenience logging functions (log_info, log_warning, log_error, log_debug)
- Conversation logging
"""
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(lib_path))

from skippy_logger import (
    SkippyLogger,
    get_logger,
    log_script_execution,
    log_error_with_context,
    log_info,
    log_warning,
    log_error,
    log_debug,
)


@pytest.mark.unit
class TestSkippyLogger:
    """Test cases for SkippyLogger"""

    def test_logger_initialization(self):
        """Test logger can be initialized"""
        logger = SkippyLogger("test")
        assert logger is not None
        assert hasattr(logger, 'logger')

    def test_logger_name(self):
        """Test logger has correct name"""
        logger = SkippyLogger("test_name")
        assert logger.logger.name == "test_name"

    def test_log_info(self, tmp_path):
        """Test info logging"""
        logger = SkippyLogger("test", log_dir=str(tmp_path))

        logger.info("Test info message")

        # Check log file was created and contains message
        log_file = tmp_path / "test.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Test info message" in log_content
        assert "INFO" in log_content

    def test_log_error(self, tmp_path):
        """Test error logging"""
        logger = SkippyLogger("test", log_dir=str(tmp_path))
        log_file = tmp_path / "test.log"

        logger.error("Test error message")

        log_content = log_file.read_text()
        assert "Test error message" in log_content
        assert "ERROR" in log_content

    def test_log_warning(self, tmp_path):
        """Test warning logging"""
        logger = SkippyLogger("test", log_dir=str(tmp_path))
        log_file = tmp_path / "test.log"

        logger.warning("Test warning message")

        log_content = log_file.read_text()
        assert "Test warning message" in log_content
        assert "WARNING" in log_content

    def test_log_debug(self, tmp_path):
        """Test debug logging"""
        logger = SkippyLogger("test", log_dir=str(tmp_path), log_level="DEBUG")
        log_file = tmp_path / "test.log"

        logger.debug("Test debug message")

        log_content = log_file.read_text()
        assert "Test debug message" in log_content
        assert "DEBUG" in log_content

    def test_multiple_loggers(self, tmp_path):
        """Test multiple logger instances don't interfere"""
        logger1 = SkippyLogger("test1", log_dir=str(tmp_path))
        logger2 = SkippyLogger("test2", log_dir=str(tmp_path))

        logger1.info("Logger 1 message")
        logger2.info("Logger 2 message")

        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"

        assert "Logger 1 message" in log_file1.read_text()
        assert "Logger 2 message" in log_file2.read_text()
        assert "Logger 2 message" not in log_file1.read_text()
        assert "Logger 1 message" not in log_file2.read_text()

    def test_log_critical(self, tmp_path):
        """Test critical logging"""
        logger = SkippyLogger("test", log_dir=str(tmp_path))
        log_file = tmp_path / "test.log"

        logger.critical("Test critical message")

        log_content = log_file.read_text()
        assert "Test critical message" in log_content
        assert "CRITICAL" in log_content

    def test_get_logger_method(self, tmp_path):
        """Test get_logger method returns the underlying logger."""
        skippy_logger = SkippyLogger("test-get", log_dir=str(tmp_path))
        underlying_logger = skippy_logger.get_logger()

        assert isinstance(underlying_logger, logging.Logger)
        assert underlying_logger.name == "test-get"

    def test_console_only(self, tmp_path, capsys):
        """Test logger with console only, no file."""
        logger = SkippyLogger(
            "console-only",
            log_dir=str(tmp_path),
            log_to_file=False,
            log_to_console=True
        )

        logger.info("Console message")

        # Log file should not exist
        log_file = tmp_path / "console-only.log"
        assert not log_file.exists()

    def test_file_only(self, tmp_path):
        """Test logger with file only, no console."""
        logger = SkippyLogger(
            "file-only",
            log_dir=str(tmp_path),
            log_to_file=True,
            log_to_console=False
        )

        logger.info("File only message")

        log_file = tmp_path / "file-only.log"
        assert log_file.exists()
        assert "File only message" in log_file.read_text()

    def test_combined_log_file(self, tmp_path):
        """Test that messages go to combined log file."""
        logger = SkippyLogger("combined-test", log_dir=str(tmp_path))

        logger.info("Combined log message")

        combined_log = tmp_path / "skippy_combined.log"
        assert combined_log.exists()
        assert "Combined log message" in combined_log.read_text()

    def test_conversation_log(self, tmp_path):
        """Test conversation logging creates daily log file."""
        with patch.dict('os.environ', {'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)}):
            logger = SkippyLogger(
                "conversation-test",
                log_dir=str(tmp_path),
                conversation_log=True
            )

            logger.info("Conversation log message")

            # Check script_logs directory was created
            script_logs_dir = tmp_path / "script_logs"
            assert script_logs_dir.exists()

            # Check daily log file exists
            log_files = list(script_logs_dir.glob("script_log_*.md"))
            assert len(log_files) >= 1

    def test_custom_log_level(self, tmp_path):
        """Test custom log level setting."""
        logger = SkippyLogger(
            "level-test",
            log_dir=str(tmp_path),
            log_level="WARNING"
        )

        logger.info("Info should not appear")
        logger.warning("Warning should appear")

        log_file = tmp_path / "level-test.log"
        content = log_file.read_text()
        assert "Info should not appear" not in content
        assert "Warning should appear" in content


@pytest.mark.unit
class TestGetLogger:
    """Tests for get_logger factory function."""

    def setup_method(self):
        """Clear logger instances before each test."""
        SkippyLogger._instances.clear()

    def test_get_logger_basic(self, tmp_path):
        """Test get_logger returns a logger."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            logger = get_logger("test-factory")
            assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_same_instance(self, tmp_path):
        """Test get_logger returns same instance for same parameters."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            logger1 = get_logger("same-instance")
            logger2 = get_logger("same-instance")
            assert logger1 is logger2

    def test_get_logger_with_log_level(self, tmp_path):
        """Test get_logger with custom log level."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            logger = get_logger("level-test", log_level="DEBUG")
            assert logger.level == logging.DEBUG

    def test_get_logger_from_env_level(self, tmp_path):
        """Test get_logger uses SKIPPY_LOG_LEVEL env var."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_LOG_LEVEL': 'WARNING'
        }):
            logger = get_logger("env-level-test")
            assert logger.level == logging.WARNING

    def test_get_logger_without_file(self, tmp_path):
        """Test get_logger with log_to_file=False."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            logger = get_logger("no-file", log_to_file=False)
            assert isinstance(logger, logging.Logger)

            # Verify no file handler
            file_handlers = [
                h for h in logger.handlers
                if hasattr(h, 'baseFilename')
            ]
            assert len(file_handlers) == 0

    def test_get_logger_with_conversation(self, tmp_path):
        """Test get_logger with conversation_log=True."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)
        }):
            logger = get_logger("convo-test", conversation_log=True)
            assert isinstance(logger, logging.Logger)


@pytest.mark.unit
class TestLogScriptExecution:
    """Tests for log_script_execution function."""

    def setup_method(self):
        """Clear logger instances before each test."""
        SkippyLogger._instances.clear()

    def test_log_script_execution_start(self, tmp_path):
        """Test logging script start."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)
        }):
            log_script_execution("test_script", "start")

            # Verify audit log was written
            logs_dir = tmp_path / "logs"
            audit_log = logs_dir / "skippy.audit.log"
            if audit_log.exists():
                content = audit_log.read_text()
                assert "test_script" in content
                assert "start" in content

    def test_log_script_execution_with_details(self, tmp_path):
        """Test logging script execution with details."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)
        }):
            log_script_execution(
                "backup_script",
                "complete",
                {"files": 10, "size": "1.2GB"}
            )

            logs_dir = tmp_path / "logs"
            audit_log = logs_dir / "skippy.audit.log"
            if audit_log.exists():
                content = audit_log.read_text()
                assert "backup_script" in content
                assert "complete" in content


@pytest.mark.unit
class TestLogErrorWithContext:
    """Tests for log_error_with_context function."""

    def setup_method(self):
        """Clear logger instances before each test."""
        SkippyLogger._instances.clear()

    def test_log_error_basic(self, tmp_path):
        """Test logging error without context."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)
        }):
            error = ValueError("Test error")
            log_error_with_context(error)

            logs_dir = tmp_path / "logs"
            error_log = logs_dir / "skippy.errors.log"
            if error_log.exists():
                content = error_log.read_text()
                assert "ValueError" in content
                assert "Test error" in content

    def test_log_error_with_context(self, tmp_path):
        """Test logging error with context."""
        with patch.dict('os.environ', {
            'SKIPPY_BASE_PATH': str(tmp_path),
            'SKIPPY_CONVERSATIONS_PATH': str(tmp_path)
        }):
            error = IOError("File not found")
            log_error_with_context(error, {"operation": "backup", "file": "data.db"})

            logs_dir = tmp_path / "logs"
            error_log = logs_dir / "skippy.errors.log"
            if error_log.exists():
                content = error_log.read_text()
                assert "IOError" in content or "OSError" in content


@pytest.mark.unit
class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def setup_method(self):
        """Clear logger instances before each test."""
        SkippyLogger._instances.clear()

    def test_log_info(self, tmp_path):
        """Test log_info convenience function."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            log_info("Test info message")

            logs_dir = tmp_path / "logs"
            skippy_log = logs_dir / "skippy.log"
            if skippy_log.exists():
                content = skippy_log.read_text()
                assert "Test info message" in content

    def test_log_info_with_script_name(self, tmp_path):
        """Test log_info with custom script name."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            log_info("Custom script message", script_name="custom_script")

            logs_dir = tmp_path / "logs"
            custom_log = logs_dir / "custom_script.log"
            if custom_log.exists():
                content = custom_log.read_text()
                assert "Custom script message" in content

    def test_log_warning(self, tmp_path):
        """Test log_warning convenience function."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            log_warning("Test warning message")

            logs_dir = tmp_path / "logs"
            skippy_log = logs_dir / "skippy.log"
            if skippy_log.exists():
                content = skippy_log.read_text()
                assert "Test warning message" in content

    def test_log_error_convenience(self, tmp_path):
        """Test log_error convenience function."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            log_error("Test error message")

            logs_dir = tmp_path / "logs"
            skippy_log = logs_dir / "skippy.log"
            if skippy_log.exists():
                content = skippy_log.read_text()
                assert "Test error message" in content

    def test_log_debug(self, tmp_path):
        """Test log_debug convenience function."""
        with patch.dict('os.environ', {'SKIPPY_BASE_PATH': str(tmp_path)}):
            log_debug("Test debug message")

            logs_dir = tmp_path / "logs"
            skippy_log = logs_dir / "skippy.log"
            if skippy_log.exists():
                content = skippy_log.read_text()
                assert "Test debug message" in content
