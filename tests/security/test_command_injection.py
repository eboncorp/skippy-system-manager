#!/usr/bin/env python3
"""
Security Tests - Command Injection Prevention
Version: 1.0.0
Created: 2025-11-12
Purpose: Test command injection prevention in MCP server tools

These tests verify that input validation prevents command injection attacks
across all command execution interfaces.
"""

import pytest
import sys
from pathlib import Path

# Add lib/python to path
LIB_PATH = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(LIB_PATH))

from skippy_validator import validate_command, ValidationError


class TestCommandInjectionPrevention:
    """Test suite for command injection attack prevention."""

    def test_semicolon_injection_blocked(self):
        """Test that semicolon command injection is blocked."""
        malicious_command = "ls; rm -rf /tmp/test"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_ampersand_injection_blocked(self):
        """Test that ampersand command injection is blocked."""
        malicious_command = "ls & cat /etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_pipe_injection_blocked_when_disabled(self):
        """Test that pipe injection is blocked when pipes are disabled."""
        malicious_command = "ls | grep password"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,  # Pipes disabled
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_pipe_allowed_when_enabled(self):
        """Test that pipes work when explicitly allowed."""
        safe_command = "ls | grep test"

        # Should not raise when pipes are allowed
        result = validate_command(
            safe_command,
            allowed_commands=['ls', 'grep', 'pwd'],
            allow_pipes=True,  # Pipes enabled
            allow_redirects=False
        )

        assert result == safe_command

    def test_redirect_injection_blocked(self):
        """Test that redirect injection is blocked."""
        malicious_command = "ls > /tmp/stolen_data.txt"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_subshell_injection_blocked(self):
        """Test that subshell injection is blocked."""
        malicious_command = "ls $(cat /etc/passwd)"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_backtick_injection_blocked(self):
        """Test that backtick command substitution is blocked."""
        malicious_command = "ls `whoami`"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_newline_injection_blocked(self):
        """Test that newline injection is blocked."""
        malicious_command = "ls\nrm -rf /"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                malicious_command,
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

        assert "dangerous character" in str(exc_info.value).lower()

    def test_command_whitelist_enforcement(self):
        """Test that only whitelisted commands are allowed."""
        dangerous_command = "rm -rf /tmp/test"

        with pytest.raises(ValidationError) as exc_info:
            validate_command(
                dangerous_command,
                allowed_commands=['ls', 'pwd', 'date'],  # rm not in whitelist
                allow_pipes=False,
                allow_redirects=False
            )

        assert "not in allowed list" in str(exc_info.value).lower()

    def test_safe_command_allowed(self):
        """Test that safe, whitelisted commands are allowed."""
        safe_command = "ls -la"

        result = validate_command(
            safe_command,
            allowed_commands=['ls', 'pwd', 'date'],
            allow_pipes=False,
            allow_redirects=False
        )

        assert result == safe_command

    def test_empty_command_blocked(self):
        """Test that empty commands are rejected."""
        with pytest.raises(ValidationError):
            validate_command(
                "",
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )

    def test_whitespace_only_command_blocked(self):
        """Test that whitespace-only commands are rejected."""
        with pytest.raises(ValidationError):
            validate_command(
                "   ",
                allowed_commands=['ls', 'pwd', 'date'],
                allow_pipes=False,
                allow_redirects=False
            )


class TestPathTraversalPrevention:
    """Test suite for path traversal attack prevention."""

    def test_parent_directory_traversal_blocked(self):
        """Test that ../ path traversal is blocked."""
        from skippy_validator import validate_path

        malicious_path = "../../../etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_path(malicious_path, must_exist=False)

        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_absolute_path_with_traversal_blocked(self):
        """Test that absolute paths with .. are blocked."""
        from skippy_validator import validate_path

        malicious_path = "/home/user/../../../etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_path(malicious_path, must_exist=False)

        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_tilde_expansion_detected(self):
        """Test that tilde expansion is detected."""
        from skippy_validator import validate_path

        # Tilde in original path should be flagged
        path_with_tilde = "~/../../etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_path(path_with_tilde, must_exist=False)

        # Should detect dangerous pattern
        assert "dangerous pattern" in str(exc_info.value).lower()

    def test_safe_absolute_path_allowed(self):
        """Test that safe absolute paths are allowed."""
        from skippy_validator import validate_path

        safe_path = "/tmp/test.txt"

        # Should not raise
        result = validate_path(safe_path, must_exist=False, allow_create=True)
        assert str(result) == "/tmp/test.txt"

    def test_base_directory_restriction(self):
        """Test that paths are restricted to base directory."""
        from skippy_validator import validate_path

        # Path outside base directory
        with pytest.raises(ValidationError) as exc_info:
            validate_path(
                "/etc/passwd",
                base_dir="/tmp",
                must_exist=False
            )

        assert "outside allowed directory" in str(exc_info.value).lower()


class TestSQLInjectionPrevention:
    """Test suite for SQL injection attack prevention."""

    def test_basic_sql_injection_blocked(self):
        """Test that basic SQL injection is blocked."""
        from skippy_validator import validate_sql_input

        malicious_input = "admin' OR '1'='1"

        with pytest.raises(ValidationError) as exc_info:
            validate_sql_input(malicious_input)

        assert "sql injection" in str(exc_info.value).lower()

    def test_union_injection_blocked(self):
        """Test that UNION injection is blocked."""
        from skippy_validator import validate_sql_input

        malicious_input = "1 UNION SELECT * FROM users"

        with pytest.raises(ValidationError) as exc_info:
            validate_sql_input(malicious_input)

        assert "sql injection" in str(exc_info.value).lower()

    def test_comment_injection_blocked(self):
        """Test that SQL comment injection is blocked."""
        from skippy_validator import validate_sql_input

        malicious_input = "admin'--"

        with pytest.raises(ValidationError) as exc_info:
            validate_sql_input(malicious_input)

        assert "sql injection" in str(exc_info.value).lower()

    def test_safe_sql_input_allowed(self):
        """Test that safe SQL input is allowed."""
        from skippy_validator import validate_sql_input

        safe_input = "john_doe_123"

        result = validate_sql_input(safe_input)
        assert result == safe_input


# Test markers
pytestmark = pytest.mark.security


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
