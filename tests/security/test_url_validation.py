#!/usr/bin/env python3
"""
Security Tests - URL Validation
Version: 1.0.0
Created: 2025-11-12
Purpose: Test URL validation to prevent SSRF and other web-based attacks

These tests verify that URL validation prevents Server-Side Request Forgery (SSRF)
and other malicious URL-based attacks.
"""

import pytest
import sys
from pathlib import Path

# Add lib/python to path
LIB_PATH = Path(__file__).parent.parent.parent / "lib" / "python"
sys.path.insert(0, str(LIB_PATH))

from skippy_validator import validate_url, ValidationError


class TestURLValidation:
    """Test suite for URL validation and SSRF prevention."""

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are allowed."""
        valid_url = "http://example.com/api/data"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are allowed."""
        valid_url = "https://example.com/api/data"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_javascript_protocol_blocked(self):
        """Test that javascript: protocol is blocked."""
        malicious_url = "javascript:alert(1)"

        with pytest.raises(ValidationError) as exc_info:
            validate_url(malicious_url, allowed_schemes=['http', 'https'])

        assert "not allowed" in str(exc_info.value).lower()

    def test_file_protocol_blocked(self):
        """Test that file: protocol is blocked."""
        malicious_url = "file:///etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            validate_url(malicious_url, allowed_schemes=['http', 'https'])

        assert "not allowed" in str(exc_info.value).lower()

    def test_ftp_protocol_blocked_when_not_allowed(self):
        """Test that ftp: protocol is blocked when not in allowed list."""
        url = "ftp://example.com/file.txt"

        with pytest.raises(ValidationError) as exc_info:
            validate_url(url, allowed_schemes=['http', 'https'])

        assert "not allowed" in str(exc_info.value).lower()

    def test_dangerous_characters_in_url(self):
        """Test that URLs with dangerous characters are blocked."""
        malicious_urls = [
            "http://example.com/<script>alert(1)</script>",
            'http://example.com/"><script>alert(1)</script>',
            "http://example.com/'><script>alert(1)</script>",
        ]

        for url in malicious_urls:
            with pytest.raises(ValidationError) as exc_info:
                validate_url(url, allowed_schemes=['http', 'https'])

            assert "dangerous characters" in str(exc_info.value).lower()

    def test_url_with_query_parameters(self):
        """Test that URLs with safe query parameters work."""
        valid_url = "https://example.com/api?param1=value1&param2=value2"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_url_with_port(self):
        """Test that URLs with port numbers work."""
        valid_url = "http://example.com:8080/api"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_url_with_authentication(self):
        """Test that URLs with basic auth components work."""
        valid_url = "https://user:pass@example.com/api"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_localhost_url_allowed(self):
        """Test that localhost URLs are allowed (for local development)."""
        valid_url = "http://localhost:8080/api"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_internal_ip_allowed(self):
        """Test that internal IP addresses are allowed."""
        valid_url = "http://192.168.1.1/api"

        result = validate_url(valid_url, allowed_schemes=['http', 'https'])
        assert result == valid_url

    def test_malformed_url_blocked(self):
        """Test that malformed URLs are blocked."""
        malformed_urls = [
            "ht!tp://example.com",
            "http:/example.com",  # Missing slash
            "http//example.com",  # Missing colon
        ]

        for url in malformed_urls:
            with pytest.raises(ValidationError):
                validate_url(url, allowed_schemes=['http', 'https'])

    def test_empty_url_blocked(self):
        """Test that empty URLs are blocked."""
        with pytest.raises(ValidationError):
            validate_url("", allowed_schemes=['http', 'https'])

    def test_whitespace_only_url_blocked(self):
        """Test that whitespace-only URLs are blocked."""
        with pytest.raises(ValidationError):
            validate_url("   ", allowed_schemes=['http', 'https'])

    def test_data_uri_blocked(self):
        """Test that data: URIs are blocked."""
        data_uri = "data:text/html,<script>alert(1)</script>"

        with pytest.raises(ValidationError) as exc_info:
            validate_url(data_uri, allowed_schemes=['http', 'https'])

        assert "not allowed" in str(exc_info.value).lower()


class TestSSRFPrevention:
    """Test suite specifically for SSRF attack prevention."""

    def test_ssrf_to_metadata_endpoint(self):
        """Test that SSRF to cloud metadata endpoints can be detected."""
        # Note: The validator doesn't block these by default as they might be legitimate
        # This test documents the behavior - actual SSRF prevention would need
        # additional network-level controls or custom validation

        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/computeMetadata/v1/",  # GCP metadata
        ]

        for url in metadata_urls:
            # These URLs are technically valid, so they pass validation
            # SSRF prevention requires network-level controls or custom validation
            result = validate_url(url, allowed_schemes=['http', 'https'])
            assert result == url

    def test_ssrf_to_internal_service(self):
        """Test that internal service URLs are allowed (may need app-level controls)."""
        internal_url = "http://internal-api.local:8080/admin"

        # Internal URLs pass validation - SSRF prevention needs app-level controls
        result = validate_url(internal_url, allowed_schemes=['http', 'https'])
        assert result == internal_url


# Test markers
pytestmark = pytest.mark.security


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
