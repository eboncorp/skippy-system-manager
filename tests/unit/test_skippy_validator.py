"""
Unit tests for skippy_validator module
"""
import pytest
import sys
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(lib_path))

from skippy_validator import SkippyValidator


@pytest.mark.unit
class TestSkippyValidator:
    """Test cases for SkippyValidator"""

    def test_validate_path_valid(self):
        """Test valid path validation"""
        validator = SkippyValidator()
        assert validator.validate_path("/home/user/test.txt") == True

    def test_validate_path_traversal(self):
        """Test path traversal detection"""
        validator = SkippyValidator()
        # Path traversal should be rejected
        assert validator.validate_path("../../../etc/passwd") == False
        assert validator.validate_path("/home/user/../../../etc/passwd") == False

    def test_validate_email_valid(self):
        """Test valid email validation"""
        validator = SkippyValidator()
        assert validator.validate_email("user@example.com") == True
        assert validator.validate_email("test.user+tag@domain.co.uk") == True

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        validator = SkippyValidator()
        assert validator.validate_email("not-an-email") == False
        assert validator.validate_email("@example.com") == False
        assert validator.validate_email("user@") == False

    def test_validate_url_valid(self):
        """Test valid URL validation"""
        validator = SkippyValidator()
        assert validator.validate_url("https://example.com") == True
        assert validator.validate_url("http://example.com:8080/path") == True

    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        validator = SkippyValidator()
        assert validator.validate_url("not-a-url") == False
        assert validator.validate_url("ftp://example.com") == False

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        validator = SkippyValidator()
        # Remove dangerous characters
        assert validator.sanitize_filename("test.txt") == "test.txt"
        assert validator.sanitize_filename("../test.txt") == "test.txt"
        assert validator.sanitize_filename("test;rm -rf.txt") == "testrm -rf.txt"

    def test_validate_integer(self):
        """Test integer validation"""
        validator = SkippyValidator()
        assert validator.validate_integer("123") == True
        assert validator.validate_integer("abc") == False
        assert validator.validate_integer("12.34") == False

    def test_validate_integer_range(self):
        """Test integer range validation"""
        validator = SkippyValidator()
        assert validator.validate_integer("50", min_val=0, max_val=100) == True
        assert validator.validate_integer("150", min_val=0, max_val=100) == False
        assert validator.validate_integer("-10", min_val=0, max_val=100) == False
