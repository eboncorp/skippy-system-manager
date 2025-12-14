#!/usr/bin/env python3
"""
Skippy System Manager - Input Validation Library
Version: 1.0.0
Author: Skippy Development Team
Created: 2025-11-05

A centralized input validation library for security hardening.

Features:
- Path validation (prevent directory traversal)
- Command injection prevention
- SQL injection prevention
- File type validation
- Size limit validation
- IP address validation
- URL validation
- Email validation
"""

import re
import os
from pathlib import Path
from typing import Optional, List, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SkippyValidator:
    """
    Centralized validator for Skippy System Manager.

    Usage:
        from lib.python.skippy_validator import validate_path, validate_command

        # Validate file path
        safe_path = validate_path("/path/to/file.txt")

        # Validate command
        safe_command = validate_command("ls -la")
    """

    # Dangerous characters and patterns
    DANGEROUS_PATH_CHARS = ["../", "..\\", "~", "$"]
    DANGEROUS_CMD_CHARS = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('|\")\s*(OR|AND)\s*\1",
    ]

    @staticmethod
    def validate_path(
        path: Union[str, Path],
        base_dir: Optional[Union[str, Path]] = None,
        must_exist: bool = False,
        allow_create: bool = True,
    ) -> Path:
        """
        Validate and sanitize file paths to prevent directory traversal attacks.

        Args:
            path: Path to validate
            base_dir: Base directory to restrict path to (optional)
            must_exist: Whether path must exist
            allow_create: Whether to allow creation of new paths

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid or dangerous

        Example:
            >>> validate_path("/safe/path/file.txt")
            PosixPath('/safe/path/file.txt')

            >>> validate_path("../../../etc/passwd")  # Raises ValidationError
        """
        # Convert to Path object
        path_obj = Path(path).expanduser().resolve()

        # Check for dangerous characters in original path
        for dangerous_char in SkippyValidator.DANGEROUS_PATH_CHARS:
            if dangerous_char in str(path):  # Check original path, not resolved
                raise ValidationError(f"Path contains dangerous pattern: {dangerous_char}")

        # If base_dir specified, ensure path is within it
        if base_dir:
            base_dir_obj = Path(base_dir).expanduser().resolve()
            try:
                path_obj.relative_to(base_dir_obj)
            except ValueError:
                raise ValidationError(
                    f"Path '{path_obj}' is outside allowed directory '{base_dir_obj}'"
                )

        # Check if path must exist
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path_obj}")

        # Check if creation is allowed
        if not allow_create and not path_obj.exists():
            raise ValidationError(f"Path does not exist and creation not allowed: {path_obj}")

        return path_obj

    @staticmethod
    def validate_command(
        command: str,
        allowed_commands: Optional[List[str]] = None,
        allow_pipes: bool = False,
        allow_redirects: bool = False,
    ) -> str:
        """
        Validate command to prevent command injection.

        Args:
            command: Command to validate
            allowed_commands: Whitelist of allowed commands (optional)
            allow_pipes: Whether to allow pipe operators
            allow_redirects: Whether to allow redirect operators

        Returns:
            Validated command string

        Raises:
            ValidationError: If command is dangerous

        Example:
            >>> validate_command("ls -la")
            'ls -la'

            >>> validate_command("rm -rf /; echo hacked")  # Raises ValidationError
        """
        # Check for dangerous characters
        dangerous_chars = list(SkippyValidator.DANGEROUS_CMD_CHARS)

        if allow_pipes:
            dangerous_chars.remove("|")

        if allow_redirects:
            dangerous_chars = [c for c in dangerous_chars if c not in ["<", ">"]]

        for char in dangerous_chars:
            if char in command:
                raise ValidationError(f"Command contains dangerous character: {char}")

        # If whitelist provided, check command
        if allowed_commands:
            cmd_name = command.split()[0] if command.split() else ""
            if cmd_name not in allowed_commands:
                raise ValidationError(
                    f"Command '{cmd_name}' not in allowed list: {allowed_commands}"
                )

        return command

    @staticmethod
    def validate_sql_input(input_str: str) -> str:
        """
        Validate input to prevent SQL injection.

        Args:
            input_str: Input string to validate

        Returns:
            Validated string

        Raises:
            ValidationError: If input contains SQL injection patterns

        Example:
            >>> validate_sql_input("normal_username")
            'normal_username'

            >>> validate_sql_input("admin' OR '1'='1")  # Raises ValidationError
        """
        # Check against SQL injection patterns
        for pattern in SkippyValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                raise ValidationError(f"Input contains potential SQL injection pattern")

        # Additional check for excessive special characters
        special_char_count = sum(1 for c in input_str if not c.isalnum() and c not in [" ", "_", "-", "@", "."])
        if special_char_count > len(input_str) * 0.3:  # More than 30% special chars
            raise ValidationError("Input contains excessive special characters")

        return input_str

    @staticmethod
    def validate_file_type(
        file_path: Union[str, Path],
        allowed_extensions: List[str],
    ) -> Path:
        """
        Validate file type by extension.

        Args:
            file_path: Path to file
            allowed_extensions: List of allowed extensions (e.g., ['.txt', '.pdf'])

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file type is not allowed

        Example:
            >>> validate_file_type("document.pdf", ['.pdf', '.txt'])
            PosixPath('document.pdf')

            >>> validate_file_type("script.sh", ['.pdf', '.txt'])  # Raises ValidationError
        """
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()

        # Normalize allowed extensions
        allowed_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                             for ext in allowed_extensions]

        if extension not in allowed_extensions:
            raise ValidationError(
                f"File type '{extension}' not allowed. Allowed types: {allowed_extensions}"
            )

        return path_obj

    @staticmethod
    def validate_file_size(
        file_path: Union[str, Path],
        max_size_mb: float,
    ) -> Path:
        """
        Validate file size.

        Args:
            file_path: Path to file
            max_size_mb: Maximum allowed size in megabytes

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file is too large

        Example:
            >>> validate_file_size("small_file.txt", max_size_mb=10)
            PosixPath('small_file.txt')
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise ValidationError(f"File does not exist: {path_obj}")

        file_size_mb = path_obj.stat().st_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            raise ValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum ({max_size_mb} MB)"
            )

        return path_obj

    @staticmethod
    def validate_ip_address(ip: str, allow_private: bool = True) -> str:
        """
        Validate IP address format.

        Args:
            ip: IP address to validate
            allow_private: Whether to allow private IP addresses

        Returns:
            Validated IP address string

        Raises:
            ValidationError: If IP address is invalid

        Example:
            >>> validate_ip_address("192.168.1.1")
            '192.168.1.1'

            >>> validate_ip_address("999.999.999.999")  # Raises ValidationError
        """
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ipv4_pattern, ip)

        if not match:
            raise ValidationError(f"Invalid IP address format: {ip}")

        # Validate each octet
        octets = [int(x) for x in match.groups()]
        for octet in octets:
            if octet > 255:
                raise ValidationError(f"Invalid IP address (octet > 255): {ip}")

        # Check for private IP ranges if not allowed
        if not allow_private:
            if (octets[0] == 10 or
                (octets[0] == 172 and 16 <= octets[1] <= 31) or
                (octets[0] == 192 and octets[1] == 168)):
                raise ValidationError(f"Private IP addresses not allowed: {ip}")

        return ip

    @staticmethod
    def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """
        Validate URL format and scheme.

        Args:
            url: URL to validate
            allowed_schemes: List of allowed schemes (e.g., ['http', 'https'])

        Returns:
            Validated URL string

        Raises:
            ValidationError: If URL is invalid

        Example:
            >>> validate_url("https://example.com")
            'https://example.com'

            >>> validate_url("javascript:alert(1)")  # Raises ValidationError
        """
        # Basic checks
        if not url or not url.strip():
            raise ValidationError("URL cannot be empty")

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {e}")

        # Check scheme
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https', 'ftp', 'ftps']

        if not parsed.scheme:
            raise ValidationError("URL must have a scheme (e.g., http://)")

        if parsed.scheme not in allowed_schemes:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}"
            )

        # Validate URL structure - must have netloc (domain/host)
        if not parsed.netloc:
            raise ValidationError(
                "Invalid URL structure: missing domain/host"
            )

        # Check for dangerous patterns
        if any(char in url for char in ['<', '>', '"', "'"]):
            raise ValidationError("URL contains dangerous characters")

        return url

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            Validated email string

        Raises:
            ValidationError: If email is invalid

        Example:
            >>> validate_email("user@example.com")
            'user@example.com'

            >>> validate_email("invalid.email")  # Raises ValidationError
        """
        # Basic email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValidationError(f"Invalid email format: {email}")

        # Check for dangerous characters (defense in depth - regex already blocks these)
        if any(char in email for char in ['<', '>', '"', "'", ';', '&']):  # pragma: no cover
            raise ValidationError("Email contains dangerous characters")

        return email

    @staticmethod
    def sanitize_string(
        input_str: str,
        max_length: Optional[int] = None,
        allow_special_chars: bool = True,
    ) -> str:
        """
        Sanitize string by removing/escaping dangerous characters.

        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length
            allow_special_chars: Whether to allow special characters

        Returns:
            Sanitized string

        Example:
            >>> sanitize_string("Hello World!", max_length=10)
            'Hello Worl'
        """
        # Remove control characters
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in ['\n', '\t'])

        # Remove special chars if not allowed
        if not allow_special_chars:
            sanitized = ''.join(char for char in sanitized if char.isalnum() or char in [' ', '_', '-'])

        # Truncate to max length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized


# Convenience functions
def validate_path(path: Union[str, Path], **kwargs) -> Path:
    """Convenience wrapper for path validation."""
    return SkippyValidator.validate_path(path, **kwargs)


def validate_command(command: str, **kwargs) -> str:
    """Convenience wrapper for command validation."""
    return SkippyValidator.validate_command(command, **kwargs)


def validate_sql_input(input_str: str) -> str:
    """Convenience wrapper for SQL input validation."""
    return SkippyValidator.validate_sql_input(input_str)


def validate_file_type(file_path: Union[str, Path], allowed_extensions: List[str]) -> Path:
    """Convenience wrapper for file type validation."""
    return SkippyValidator.validate_file_type(file_path, allowed_extensions)


def validate_ip_address(ip: str, **kwargs) -> str:
    """Convenience wrapper for IP address validation."""
    return SkippyValidator.validate_ip_address(ip, **kwargs)


def validate_url(url: str, **kwargs) -> str:
    """Convenience wrapper for URL validation."""
    return SkippyValidator.validate_url(url, **kwargs)


def validate_email(email: str) -> str:
    """Convenience wrapper for email validation."""
    return SkippyValidator.validate_email(email)


# Example usage
if __name__ == "__main__":
    print("=== Skippy Validator Examples ===\n")

    # Path validation
    try:
        safe_path = validate_path("/tmp/test.txt")
        print(f"✓ Valid path: {safe_path}")
    except ValidationError as e:
        print(f"✗ Invalid path: {e}")

    try:
        dangerous_path = validate_path("../../../etc/passwd")
        print(f"✓ Valid path: {dangerous_path}")
    except ValidationError as e:
        print(f"✗ Invalid path: {e}")

    # Command validation
    try:
        safe_cmd = validate_command("ls -la")
        print(f"✓ Valid command: {safe_cmd}")
    except ValidationError as e:
        print(f"✗ Invalid command: {e}")

    try:
        dangerous_cmd = validate_command("rm -rf /; echo hacked")
        print(f"✓ Valid command: {dangerous_cmd}")
    except ValidationError as e:
        print(f"✗ Invalid command: {e}")

    # SQL input validation
    try:
        safe_input = validate_sql_input("normal_user")
        print(f"✓ Valid SQL input: {safe_input}")
    except ValidationError as e:
        print(f"✗ Invalid SQL input: {e}")

    try:
        sql_injection = validate_sql_input("admin' OR '1'='1")
        print(f"✓ Valid SQL input: {sql_injection}")
    except ValidationError as e:
        print(f"✗ Invalid SQL input: {e}")

    # IP validation
    try:
        valid_ip = validate_ip_address("192.168.1.1")
        print(f"✓ Valid IP: {valid_ip}")
    except ValidationError as e:
        print(f"✗ Invalid IP: {e}")

    # Email validation
    try:
        valid_email = validate_email("user@example.com")
        print(f"✓ Valid email: {valid_email}")
    except ValidationError as e:
        print(f"✗ Invalid email: {e}")

    print("\nValidation examples completed.")
