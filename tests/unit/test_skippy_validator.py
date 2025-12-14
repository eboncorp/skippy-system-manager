"""
Unit tests for skippy_validator.py

Tests cover:
- Path validation (directory traversal prevention)
- Command validation (injection prevention)
- SQL input validation (injection prevention)
- File type validation
- File size validation
- IP address validation
- URL validation
- Email validation
- String sanitization
- Convenience wrapper functions
"""
import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add lib/python to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib" / "python"))
from skippy_validator import (
    SkippyValidator,
    ValidationError,
    validate_path,
    validate_command,
    validate_sql_input,
    validate_file_type,
    validate_ip_address,
    validate_url,
    validate_email,
)


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
        assert "not in allowed" in str(exc_info.value).lower()


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

    def test_validate_sql_input_safe(self):
        """Test validate_sql_input with safe input."""
        result = SkippyValidator.validate_sql_input("normal_username")
        assert result == "normal_username"

    def test_validate_sql_input_with_sql_injection(self):
        """Test validate_sql_input rejects SQL injection."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_sql_input("admin' OR '1'='1")

    def test_validate_sql_input_excessive_special_chars(self):
        """Test validate_sql_input rejects excessive special characters.

        Uses chars that don't match SQL patterns but exceed 30% special chars.
        Excluded from special count: space, _, -, @, .
        """
        # abc^^^ = 3 special out of 6 chars = 50% > 30%
        # ^ doesn't match any SQL pattern
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_sql_input("abc^^^")
        assert "excessive special characters" in str(exc_info.value).lower()

    def test_validate_sql_input_sql_comment_pattern(self):
        """Test validate_sql_input catches SQL comment patterns."""
        # -- and # are SQL comment patterns
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_sql_input("value--comment")
        assert "sql injection" in str(exc_info.value).lower()


@pytest.mark.unit
class TestFileTypeValidation:
    """Test file type validation."""

    def test_validate_file_type_allowed(self):
        """Test validation of allowed file types."""
        result = SkippyValidator.validate_file_type("document.pdf", [".pdf", ".txt"])
        assert result.suffix == ".pdf"

    def test_validate_file_type_allowed_without_dot(self):
        """Test validation handles extensions without leading dot."""
        result = SkippyValidator.validate_file_type("document.txt", ["pdf", "txt"])
        assert result.suffix == ".txt"

    def test_validate_file_type_case_insensitive(self):
        """Test validation is case-insensitive."""
        result = SkippyValidator.validate_file_type("Document.PDF", [".pdf"])
        assert result.suffix == ".PDF"

    def test_validate_file_type_rejected(self):
        """Test rejection of disallowed file types."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_file_type("script.sh", [".pdf", ".txt"])
        assert "not allowed" in str(exc_info.value).lower()


@pytest.mark.unit
class TestFileSizeValidation:
    """Test file size validation."""

    def test_validate_file_size_under_limit(self, tmp_path):
        """Test validation of file under size limit."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("Small content")

        result = SkippyValidator.validate_file_size(str(test_file), max_size_mb=1)
        assert result.exists()

    def test_validate_file_size_over_limit(self, tmp_path):
        """Test rejection of file over size limit."""
        test_file = tmp_path / "large.txt"
        # Create file larger than limit (0.001 MB = 1KB limit)
        test_file.write_bytes(b"x" * 2000)

        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_file_size(str(test_file), max_size_mb=0.001)
        assert "exceeds maximum" in str(exc_info.value).lower()

    def test_validate_file_size_nonexistent(self, tmp_path):
        """Test rejection of nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_file_size(str(nonexistent), max_size_mb=10)
        assert "does not exist" in str(exc_info.value).lower()


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

    def test_email_with_dangerous_chars(self):
        """Test rejection of emails with dangerous characters."""
        dangerous_emails = [
            "user<script>@example.com",
            "user>@example.com",
            "user\"@example.com",
            "user'@example.com",
            "user;@example.com",
        ]
        for email in dangerous_emails:
            with pytest.raises(ValidationError):
                SkippyValidator.validate_email(email)


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
            result = SkippyValidator.validate_ip_address(ip)
            assert result == ip

    def test_invalid_ipv4_out_of_range(self):
        """Test rejection of IPv4 with octets > 255."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_ip_address("192.168.1.256")

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
                SkippyValidator.validate_ip_address(ip)

    def test_reject_private_ip_10_range(self):
        """Test rejection of 10.x.x.x private IPs when not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_ip_address("10.0.0.1", allow_private=False)
        assert "private" in str(exc_info.value).lower()

    def test_reject_private_ip_172_range(self):
        """Test rejection of 172.16-31.x.x private IPs when not allowed."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_ip_address("172.16.0.1", allow_private=False)
        # 172.15 should be allowed
        result = SkippyValidator.validate_ip_address("172.15.0.1", allow_private=False)
        assert result == "172.15.0.1"

    def test_reject_private_ip_192_168_range(self):
        """Test rejection of 192.168.x.x private IPs when not allowed."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_ip_address("192.168.1.1", allow_private=False)

    def test_allow_public_ip(self):
        """Test public IPs are allowed even with allow_private=False."""
        public_ips = ["8.8.8.8", "1.1.1.1", "93.184.216.34"]
        for ip in public_ips:
            result = SkippyValidator.validate_ip_address(ip, allow_private=False)
            assert result == ip


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
        assert "not allowed" in str(exc_info.value).lower()

    def test_reject_data_url(self):
        """Test rejection of data: URLs."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url("data:text/html,<script>alert('XSS')</script>")

    def test_reject_file_url(self):
        """Test rejection of file: URLs by default."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url("file:///etc/passwd")

    def test_reject_empty_url(self):
        """Test rejection of empty URL."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_url("")
        assert "empty" in str(exc_info.value).lower()

    def test_reject_whitespace_url(self):
        """Test rejection of whitespace-only URL."""
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url("   ")

    def test_reject_url_without_scheme(self):
        """Test rejection of URL without scheme."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_url("example.com/path")
        assert "scheme" in str(exc_info.value).lower()

    def test_reject_url_without_netloc(self):
        """Test rejection of URL without domain/host."""
        with pytest.raises(ValidationError) as exc_info:
            SkippyValidator.validate_url("http:///path")
        assert "missing domain" in str(exc_info.value).lower() or "structure" in str(exc_info.value).lower()

    def test_reject_url_with_dangerous_chars(self):
        """Test rejection of URL with dangerous characters."""
        dangerous_urls = [
            "https://example.com/<script>",
            "https://example.com/path?query=\"",
            "https://example.com/'injection",
        ]
        for url in dangerous_urls:
            with pytest.raises(ValidationError):
                SkippyValidator.validate_url(url)

    def test_custom_allowed_schemes(self):
        """Test URL validation with custom allowed schemes."""
        # ftp should be allowed by default
        result = SkippyValidator.validate_url("ftp://ftp.example.com/file.txt")
        assert result == "ftp://ftp.example.com/file.txt"

        # Custom schemes
        result = SkippyValidator.validate_url(
            "https://secure.example.com",
            allowed_schemes=["https"]
        )
        assert result == "https://secure.example.com"

        # http should be rejected if only https allowed
        with pytest.raises(ValidationError):
            SkippyValidator.validate_url(
                "http://example.com",
                allowed_schemes=["https"]
            )

    def test_url_parse_exception(self):
        """Test URL validation handles urlparse exceptions."""
        from unittest.mock import patch

        # Mock urlparse to raise an exception
        with patch('skippy_validator.urlparse') as mock_urlparse:
            mock_urlparse.side_effect = ValueError("Mock parse error")
            with pytest.raises(ValidationError) as exc_info:
                SkippyValidator.validate_url("http://example.com")
            assert "invalid url format" in str(exc_info.value).lower()


@pytest.mark.unit
class TestStringSanitization:
    """Test string sanitization."""

    def test_sanitize_basic_string(self):
        """Test sanitizing a basic string."""
        result = SkippyValidator.sanitize_string("Hello World!")
        assert result == "Hello World!"

    def test_sanitize_removes_control_chars(self):
        """Test removal of control characters."""
        # String with control characters (bell, backspace)
        input_str = "Hello\x07World\x08"
        result = SkippyValidator.sanitize_string(input_str)
        assert "\x07" not in result
        assert "\x08" not in result

    def test_sanitize_preserves_newlines_tabs(self):
        """Test that newlines and tabs are preserved."""
        input_str = "Line1\nLine2\tTabbed"
        result = SkippyValidator.sanitize_string(input_str)
        assert "\n" in result
        assert "\t" in result

    def test_sanitize_removes_special_chars(self):
        """Test removal of special chars when not allowed."""
        result = SkippyValidator.sanitize_string(
            "Hello@World#123!",
            allow_special_chars=False
        )
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_max_length(self):
        """Test truncation to max length."""
        result = SkippyValidator.sanitize_string(
            "Hello World!",
            max_length=5
        )
        assert len(result) == 5
        assert result == "Hello"

    def test_sanitize_combined_options(self):
        """Test sanitization with combined options."""
        result = SkippyValidator.sanitize_string(
            "Hello@World#123!!!",
            max_length=10,
            allow_special_chars=False
        )
        assert len(result) <= 10
        assert "@" not in result


@pytest.mark.unit
class TestConvenienceWrappers:
    """Test convenience wrapper functions."""

    def test_validate_path_wrapper(self, tmp_path):
        """Test validate_path convenience function."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = validate_path(str(test_file), must_exist=True)
        assert result.exists()

    def test_validate_command_wrapper(self):
        """Test validate_command convenience function."""
        result = validate_command("ls -la")
        assert result == "ls -la"

    def test_validate_sql_input_wrapper(self):
        """Test validate_sql_input convenience function."""
        result = validate_sql_input("safe_value")
        assert result == "safe_value"

    def test_validate_file_type_wrapper(self):
        """Test validate_file_type convenience function."""
        result = validate_file_type("document.pdf", [".pdf", ".txt"])
        assert result.suffix == ".pdf"

    def test_validate_ip_address_wrapper(self):
        """Test validate_ip_address convenience function."""
        result = validate_ip_address("8.8.8.8")
        assert result == "8.8.8.8"

    def test_validate_url_wrapper(self):
        """Test validate_url convenience function."""
        result = validate_url("https://example.com")
        assert result == "https://example.com"

    def test_validate_email_wrapper(self):
        """Test validate_email convenience function."""
        result = validate_email("user@example.com")
        assert result == "user@example.com"


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
