"""
Unit tests for skippy_logger module
"""
import pytest
import sys
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(lib_path))

from skippy_logger import SkippyLogger


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
        log_file = tmp_path / "test.log"
        logger = SkippyLogger("test", log_file=str(log_file))

        logger.info("Test info message")

        # Check log file was created and contains message
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Test info message" in log_content
        assert "INFO" in log_content

    def test_log_error(self, tmp_path):
        """Test error logging"""
        log_file = tmp_path / "test.log"
        logger = SkippyLogger("test", log_file=str(log_file))

        logger.error("Test error message")

        log_content = log_file.read_text()
        assert "Test error message" in log_content
        assert "ERROR" in log_content

    def test_log_warning(self, tmp_path):
        """Test warning logging"""
        log_file = tmp_path / "test.log"
        logger = SkippyLogger("test", log_file=str(log_file))

        logger.warning("Test warning message")

        log_content = log_file.read_text()
        assert "Test warning message" in log_content
        assert "WARNING" in log_content

    def test_log_debug(self, tmp_path):
        """Test debug logging"""
        log_file = tmp_path / "test.log"
        logger = SkippyLogger("test", log_file=str(log_file), log_level="DEBUG")

        logger.debug("Test debug message")

        log_content = log_file.read_text()
        assert "Test debug message" in log_content
        assert "DEBUG" in log_content

    def test_multiple_loggers(self, tmp_path):
        """Test multiple logger instances don't interfere"""
        log_file1 = tmp_path / "test1.log"
        log_file2 = tmp_path / "test2.log"

        logger1 = SkippyLogger("test1", log_file=str(log_file1))
        logger2 = SkippyLogger("test2", log_file=str(log_file2))

        logger1.info("Logger 1 message")
        logger2.info("Logger 2 message")

        assert "Logger 1 message" in log_file1.read_text()
        assert "Logger 2 message" in log_file2.read_text()
        assert "Logger 2 message" not in log_file1.read_text()
        assert "Logger 1 message" not in log_file2.read_text()
