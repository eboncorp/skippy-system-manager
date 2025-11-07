"""
Unit tests for skippy_validator.py
"""
import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add lib/python to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib" / "python"))
from skippy_validator import SkippyValidator, ValidationError


@pytest.mark.unit
class TestPathValidation:
    """Test path validation to prevent directory traversal attacks."""

    def test_validate_simple_path(self, tmp_path):
        """Test validating a simple, safe path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = SkippyValidator.validate_path(str(test_file), must_exist=True)
        assert result == test_file
        assert result.exists()

    def test_reject_parent_directory_traversal(self):
        """Test rejection of ../ path traversal attempts."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path("../../../etc/passwd")
        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_reject_backslash_traversal(self):
        """Test rejection of ..\\ path traversal attempts."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path("..\\..\\windows\\system32")
        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_reject_tilde_expansion_attack(self):
        """Test rejection of ~ in paths (can expose user directories)."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path("~/../../etc/passwd")
        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_reject_dollar_sign_variable_expansion(self):
        """Test rejection of $ in paths (shell variable expansion)."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path("/tmp/$USER/malicious")
        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_base_dir_restriction(self, tmp_path):
        """Test that paths are restricted to base directory."""
        base_dir = tmp_path / "safe_zone"
        base_dir.mkdir()

        safe_file = base_dir / "safe.txt"
        safe_file.write_text("safe")

        # This should work - within base_dir
        result = SkippyValidator.validate_path(
            str(safe_file),
            base_dir=str(base_dir),
            must_exist=True
        )
        assert result == safe_file

        # This should fail - outside base_dir
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside")

        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path(
                str(outside_file),
                base_dir=str(base_dir),
                must_exist=True
            )
        assert "outside allowed directory" in str(exc_info.value).lower()

    def test_must_exist_validation(self, tmp_path):
        """Test must_exist parameter."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path(str(nonexistent), must_exist=True)
        assert "does not exist" in str(exc_info.value).lower()

    def test_allow_create_validation(self, tmp_path):
        """Test allow_create parameter."""
        new_file = tmp_path / "new.txt"

        # Should work with allow_create=True (default)
        result = SkippyValidator.validate_path(str(new_file), allow_create=True)
        assert result == new_file

        # Should fail with allow_create=False
        another_file = tmp_path / "another.txt"
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_path(str(another_file), allow_create=False)
        assert "creation not allowed" in str(exc_info.value).lower()


@pytest.mark.unit
class TestCommandValidation:
    """Test command validation to prevent command injection."""

    def test_validate_simple_command(self):
        """Test validating a simple, safe command."""
        result = SkippyValidator.validate_command("ls -la")
        assert result == "ls -la"

    def test_reject_semicolon_command_chaining(self):
        """Test rejection of ; for command chaining."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("ls -la; rm -rf /")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_reject_ampersand_command_chaining(self):
        """Test rejection of & and && for command chaining."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("echo hello && rm -rf /")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_reject_pipe_by_default(self):
        """Test rejection of | pipe operator by default."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("cat /etc/passwd | grep root")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_allow_pipe_when_enabled(self):
        """Test that pipes work when explicitly allowed."""
        result = SkippyValidator.validate_command(
            "cat file.txt | grep pattern",
            allow_pipes=True
        )
        assert result == "cat file.txt | grep pattern"

    def test_reject_backtick_command_substitution(self):
        """Test rejection of backticks for command substitution."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("echo `whoami`")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_reject_dollar_command_substitution(self):
        """Test rejection of $() for command substitution."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("echo $(whoami)")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_reject_redirect_by_default(self):
        """Test rejection of > and < redirect operators by default."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("cat /etc/passwd > /tmp/stolen")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_allow_redirect_when_enabled(self):
        """Test that redirects work when explicitly allowed."""
        result = SkippyValidator.validate_command(
            "echo hello > output.txt",
            allow_redirects=True
        )
        assert result == "echo hello > output.txt"

    def test_reject_newline_injection(self):
        """Test rejection of newline characters for command injection."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command("echo hello\nrm -rf /")
        assert "dangerous character" in str(exc_info.value).lower()

    def test_allowed_commands_whitelist(self):
        """Test command whitelist functionality."""
        allowed = ["ls", "pwd", "echo"]

        # Should work for allowed commands
        result = SkippyValidator.validate_command(
            "ls -la",
            allowed_commands=allowed
        )
        assert result == "ls -la"

        # Should fail for disallowed commands
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_command(
                "rm -rf /",
                allowed_commands=allowed
            )
        assert "not in allowed commands" in str(exc_info.value).lower()


@pytest.mark.unit
class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_detect_select_statement(self):
        """Test detection of SELECT statements in input."""
        from skippy_validator import SkippyValidator

        # Access the SQL injection patterns
        dangerous_input = "admin' OR '1'='1' -- "

        # Check if any SQL pattern matches
        is_dangerous = any(
            __import__('re').search(pattern, dangerous_input, __import__('re').IGNORECASE)
            for pattern in SkippyValidator.SQL_INJECTION_PATTERNS
        )
        assert is_dangerous

    def test_detect_drop_statement(self):
        """Test detection of DROP statements."""
        dangerous_input = "'; DROP TABLE users; --"

        is_dangerous = any(
            __import__('re').search(pattern, dangerous_input, __import__('re').IGNORECASE)
            for pattern in SkippyValidator.SQL_INJECTION_PATTERNS
        )
        assert is_dangerous

    def test_detect_sql_comment(self):
        """Test detection of SQL comments."""
        dangerous_input = "admin'--"

        is_dangerous = any(
            __import__('re').search(pattern, dangerous_input, __import__('re').IGNORECASE)
            for pattern in SkippyValidator.SQL_INJECTION_PATTERNS
        )
        assert is_dangerous

    def test_detect_union_attack(self):
        """Test detection of UNION-based SQL injection."""
        dangerous_input = "1' UNION SELECT password FROM users--"

        is_dangerous = any(
            __import__('re').search(pattern, dangerous_input, __import__('re').IGNORECASE)
            for pattern in SkippyValidator.SQL_INJECTION_PATTERNS
        )
        assert is_dangerous


@pytest.mark.unit
class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Test validation of properly formatted emails."""
        from skippy_validator import SkippyValidator

        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@example-domain.com",
        ]

        for email in valid_emails:
            result = SkippyValidator.validate_email(email)
            assert result == email

    def test_invalid_email_no_at(self):
        """Test rejection of emails without @ symbol."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_email("userexample.com")

    def test_invalid_email_no_domain(self):
        """Test rejection of emails without domain."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_email("user@")

    def test_invalid_email_no_local_part(self):
        """Test rejection of emails without local part."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_email("@example.com")


@pytest.mark.unit
class TestIPValidation:
    """Test IP address validation."""

    def test_valid_ipv4(self):
        """Test validation of valid IPv4 addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
        ]

        for ip in valid_ips:
            result = SkippyValidator.validate_ip(ip)
            assert result == ip

    def test_invalid_ipv4_out_of_range(self):
        """Test rejection of IPv4 with octets > 255."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_ip("192.168.1.256")

    def test_invalid_ipv4_format(self):
        """Test rejection of malformed IPv4 addresses."""
        invalid_ips = [
            "192.168.1",
            "192.168.1.1.1",
            "abc.def.ghi.jkl",
            "192.168.-1.1",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValidationError):
                SkippyValidator.validate_ip(ip)


@pytest.mark.unit
class TestURLValidation:
    """Test URL validation."""

    def test_valid_http_url(self):
        """Test validation of valid HTTP URLs."""
        valid_urls = [
            "http://example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://subdomain.example.com:8080/path",
        ]

        for url in valid_urls:
            result = SkippyValidator.validate_url(url)
            assert result == url

    def test_reject_javascript_url(self):
        """Test rejection of javascript: URLs (XSS attack)."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_url("javascript:alert('XSS')")
        assert "invalid url scheme" in str(exc_info.value).lower()

    def test_reject_data_url(self):
        """Test rejection of data: URLs."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url("data:text/html,<script>alert('XSS')</script>")

    def test_reject_file_url(self):
        """Test rejection of file: URLs by default."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url("file:///etc/passwd")


# Pytest fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    test_file = temp_dir / "sample.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
    return test_file
