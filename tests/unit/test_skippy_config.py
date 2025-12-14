"""
Unit tests for skippy_config module.

Tests cover:
- ConfigValidationError exception
- PathConfig and EnvVarConfig dataclasses
- SkippyConfig dataclass and methods
- ConfigValidator class
- validate_environment_variables function
- load_config_with_validation function
- generate_config_template function
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from skippy_config import (
    ConfigValidationError,
    PathConfig,
    EnvVarConfig,
    SkippyConfig,
    ConfigValidator,
    validate_environment_variables,
    load_config_with_validation,
    generate_config_template,
)


# =============================================================================
# CONFIG VALIDATION ERROR TESTS
# =============================================================================

class TestConfigValidationError:
    """Tests for ConfigValidationError exception."""

    def test_basic_error(self):
        """Test creating basic error."""
        error = ConfigValidationError("Test error")
        assert str(error) == "Test error"
        assert error.errors == []

    def test_error_with_errors_list(self):
        """Test error with list of validation errors."""
        errors = ["Error 1", "Error 2", "Error 3"]
        error = ConfigValidationError("Validation failed", errors=errors)

        assert error.message == "Validation failed"
        assert error.errors == errors

        error_str = str(error)
        assert "Validation failed" in error_str
        assert "Validation errors:" in error_str
        assert "Error 1" in error_str
        assert "Error 2" in error_str
        assert "Error 3" in error_str

    def test_error_can_be_raised(self):
        """Test that error can be raised and caught."""
        with pytest.raises(ConfigValidationError) as exc_info:
            raise ConfigValidationError("Test", errors=["e1"])

        assert exc_info.value.errors == ["e1"]


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestPathConfig:
    """Tests for PathConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating PathConfig with minimal params."""
        config = PathConfig(env_var="MY_PATH", default="/tmp/test")
        assert config.env_var == "MY_PATH"
        assert config.default == "/tmp/test"
        assert config.must_exist is False
        assert config.create_if_missing is False
        assert config.is_file is False
        assert config.description == ""

    def test_creation_full(self):
        """Test creating PathConfig with all params."""
        config = PathConfig(
            env_var="DATA_DIR",
            default="/data",
            must_exist=True,
            create_if_missing=True,
            is_file=False,
            description="Data directory"
        )
        assert config.must_exist is True
        assert config.create_if_missing is True
        assert config.description == "Data directory"


class TestEnvVarConfig:
    """Tests for EnvVarConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating EnvVarConfig with minimal params."""
        config = EnvVarConfig(name="MY_VAR")
        assert config.name == "MY_VAR"
        assert config.required is True
        assert config.default is None
        assert config.pattern is None
        assert config.min_length is None
        assert config.max_length is None
        assert config.description == ""

    def test_creation_full(self):
        """Test creating EnvVarConfig with all params."""
        config = EnvVarConfig(
            name="API_KEY",
            required=False,
            default="default_key",
            pattern=r'^[A-Za-z0-9]+$',
            min_length=10,
            max_length=100,
            description="API authentication key"
        )
        assert config.required is False
        assert config.default == "default_key"
        assert config.pattern == r'^[A-Za-z0-9]+$'
        assert config.min_length == 10
        assert config.max_length == 100


# =============================================================================
# SKIPPY CONFIG TESTS
# =============================================================================

class TestSkippyConfig:
    """Tests for SkippyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SkippyConfig()
        assert config.skippy_base_path == ""
        assert config.enable_google_drive is True
        assert config.enable_slack is False
        assert config.max_concurrent_requests == 10
        assert config.request_timeout == 30.0
        assert config.validate_paths is True

    def test_from_env_defaults(self, monkeypatch):
        """Test from_env with default values."""
        # Clear all env vars
        for key in ["SKIPPY_BASE_PATH", "WORDPRESS_BASE_PATH", "ENABLE_GOOGLE_DRIVE",
                    "ENABLE_SLACK", "MAX_CONCURRENT_REQUESTS"]:
            monkeypatch.delenv(key, raising=False)

        config = SkippyConfig.from_env()

        assert config.skippy_base_path == "/home/dave/skippy"
        assert config.wordpress_base_path == "/home/dave/RunDaveRun"
        assert config.enable_google_drive is True
        assert config.enable_slack is False

    def test_from_env_custom_values(self, monkeypatch):
        """Test from_env with custom environment values."""
        monkeypatch.setenv("SKIPPY_BASE_PATH", "/custom/skippy")
        monkeypatch.setenv("WORDPRESS_BASE_PATH", "/custom/wordpress")
        monkeypatch.setenv("ENABLE_GOOGLE_DRIVE", "false")
        monkeypatch.setenv("ENABLE_SLACK", "true")
        monkeypatch.setenv("MAX_CONCURRENT_REQUESTS", "50")
        monkeypatch.setenv("REQUEST_TIMEOUT", "60.0")

        config = SkippyConfig.from_env()

        assert config.skippy_base_path == "/custom/skippy"
        assert config.wordpress_base_path == "/custom/wordpress"
        assert config.enable_google_drive is False
        assert config.enable_slack is True
        assert config.max_concurrent_requests == 50
        assert config.request_timeout == 60.0

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = SkippyConfig(
            skippy_base_path="/test/path",
            max_concurrent_requests=20
        )
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["skippy_base_path"] == "/test/path"
        assert result["max_concurrent_requests"] == 20

    def test_to_json(self):
        """Test converting config to JSON."""
        config = SkippyConfig(skippy_base_path="/test")
        result = config.to_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["skippy_base_path"] == "/test"

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "skippy_base_path": "/dict/path",
            "enable_slack": True,
            "max_concurrent_requests": 30
        }
        config = SkippyConfig.from_dict(data)

        assert config.skippy_base_path == "/dict/path"
        assert config.enable_slack is True
        assert config.max_concurrent_requests == 30

    def test_from_dict_ignores_unknown_keys(self):
        """Test that from_dict ignores unknown keys."""
        data = {
            "skippy_base_path": "/path",
            "unknown_key": "ignored",
            "another_unknown": 123
        }
        config = SkippyConfig.from_dict(data)
        assert config.skippy_base_path == "/path"

    def test_from_json(self):
        """Test creating config from JSON string."""
        json_str = '{"skippy_base_path": "/json/path", "enable_github": false}'
        config = SkippyConfig.from_json(json_str)

        assert config.skippy_base_path == "/json/path"
        assert config.enable_github is False


# =============================================================================
# CONFIG VALIDATOR TESTS
# =============================================================================

class TestConfigValidator:
    """Tests for ConfigValidator class."""

    def test_initialization(self):
        """Test validator initialization."""
        config = SkippyConfig()
        validator = ConfigValidator(config)

        assert validator.config is config
        assert validator.errors == []
        assert validator.warnings == []

    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                conversations_path=tmpdir,
                ebon_host="user@10.0.0.1",
                max_concurrent_requests=10,
                request_timeout=30.0,
                retry_max_attempts=3,
                retry_base_delay=1.0,
                circuit_breaker_failure_threshold=5,
                circuit_breaker_timeout=60.0
            )
            validator = ConfigValidator(config)

            result = validator.validate()
            assert result is True
            assert len(validator.errors) == 0

    def test_validate_empty_path_error(self):
        """Test validation fails for empty paths."""
        config = SkippyConfig(skippy_base_path="")
        validator = ConfigValidator(config)

        result = validator.validate()
        assert result is False
        assert any("empty" in e.lower() for e in validator.errors)

    def test_validate_path_traversal_error(self):
        """Test validation fails for path traversal."""
        config = SkippyConfig(skippy_base_path="/home/../etc/passwd")
        validator = ConfigValidator(config)

        result = validator.validate()
        assert result is False
        assert any("traversal" in e.lower() for e in validator.errors)

    def test_validate_nonexistent_path_error(self):
        """Test validation fails for non-existent required paths."""
        config = SkippyConfig(
            skippy_base_path="/nonexistent/path/12345"
        )
        validator = ConfigValidator(config)

        result = validator.validate()
        assert result is False
        assert any("does not exist" in e for e in validator.errors)

    def test_validate_ebon_host_invalid_format(self):
        """Test validation fails for invalid ebon_host format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                ebon_host="invalid-host-format"
            )
            validator = ConfigValidator(config)

            result = validator.validate()
            assert result is False
            assert any("ebon_host" in e for e in validator.errors)

    def test_validate_performance_errors(self):
        """Test validation catches performance setting errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                max_concurrent_requests=0,  # Invalid
                request_timeout=-1,  # Invalid
                retry_max_attempts=0,  # Invalid
                retry_base_delay=-0.5  # Invalid
            )
            validator = ConfigValidator(config)

            result = validator.validate()
            assert result is False
            assert any("max_concurrent_requests" in e for e in validator.errors)
            assert any("request_timeout" in e for e in validator.errors)
            assert any("retry_max_attempts" in e for e in validator.errors)
            assert any("retry_base_delay" in e for e in validator.errors)

    def test_validate_performance_warnings(self):
        """Test validation generates performance warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                max_concurrent_requests=150,  # Very high
                request_timeout=400.0,  # Very long
                retry_max_attempts=15  # Many retries
            )
            validator = ConfigValidator(config)

            validator.validate()
            assert any("max_concurrent_requests" in w for w in validator.warnings)
            assert any("request_timeout" in w for w in validator.warnings)
            assert any("retry_max_attempts" in w for w in validator.warnings)

    def test_validate_security_warnings(self):
        """Test validation generates security warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                validate_paths=False,
                validate_commands=False,
                validate_urls=False,
                audit_logging=False
            )
            validator = ConfigValidator(config)

            validator.validate()
            assert any("Path validation" in w for w in validator.warnings)
            assert any("Command validation" in w for w in validator.warnings)
            assert any("URL validation" in w for w in validator.warnings)
            assert any("Audit logging" in w for w in validator.warnings)

    def test_validate_monitoring_errors(self):
        """Test validation catches monitoring setting errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                circuit_breaker_failure_threshold=0,  # Invalid
                circuit_breaker_timeout=-1  # Invalid
            )
            validator = ConfigValidator(config)

            result = validator.validate()
            assert result is False
            assert any("circuit_breaker_failure_threshold" in e for e in validator.errors)
            assert any("circuit_breaker_timeout" in e for e in validator.errors)

    def test_validate_monitoring_warnings(self):
        """Test validation generates monitoring warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                health_check_interval=5  # Very short
            )
            validator = ConfigValidator(config)

            validator.validate()
            assert any("health_check_interval" in w for w in validator.warnings)

    def test_validate_ssh_opts_warning(self):
        """Test validation warns about dangerous SSH options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                ebon_host="user@10.0.0.1",  # Need valid host for SSH opts check
                ssh_opts="ProxyCommand=/bin/bash"
            )
            validator = ConfigValidator(config)

            validator.validate()
            assert any("ProxyCommand" in w for w in validator.warnings)

    def test_validate_conversations_path_warning(self):
        """Test warning when conversations path is outside base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir,
                conversations_path="/some/other/path"
            )
            validator = ConfigValidator(config)

            validator.validate()
            assert any("outside" in w.lower() for w in validator.warnings)

    def test_get_validation_report(self):
        """Test getting validation report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SkippyConfig(
                skippy_base_path=tmpdir,
                scripts_path=tmpdir,
                logs_path=tmpdir
            )
            validator = ConfigValidator(config)
            validator.validate()

            report = validator.get_validation_report()

            assert "valid" in report
            assert "errors" in report
            assert "warnings" in report
            assert "config" in report
            assert "timestamp" in report


# =============================================================================
# VALIDATE ENVIRONMENT VARIABLES TESTS
# =============================================================================

class TestValidateEnvironmentVariables:
    """Tests for validate_environment_variables function."""

    def test_validate_with_defaults(self, monkeypatch):
        """Test validation with default values."""
        # Clear vars to use defaults
        for key in ["SKIPPY_BASE_PATH", "EBON_HOST", "GITHUB_TOKEN", "SLACK_TOKEN"]:
            monkeypatch.delenv(key, raising=False)

        result = validate_environment_variables()

        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "variables" in result

    def test_validate_ebon_host_invalid_pattern(self, monkeypatch):
        """Test validation catches invalid EBON_HOST pattern."""
        monkeypatch.setenv("EBON_HOST", "invalid-no-at-sign")

        result = validate_environment_variables()

        assert any("EBON_HOST" in e and "pattern" in e for e in result["errors"])

    def test_validate_github_token_too_short(self, monkeypatch):
        """Test validation warns about short GitHub token."""
        monkeypatch.setenv("GITHUB_TOKEN", "short")  # Less than 40 chars

        result = validate_environment_variables()

        assert any("GITHUB_TOKEN" in w and "short" in w for w in result["warnings"])

    def test_validate_slack_token_invalid_pattern(self, monkeypatch):
        """Test validation warns about invalid Slack token pattern."""
        monkeypatch.setenv("SLACK_TOKEN", "invalid-slack-token")

        result = validate_environment_variables()

        assert any("SLACK_TOKEN" in w and "pattern" in w for w in result["warnings"])

    def test_validate_valid_tokens(self, monkeypatch):
        """Test validation passes with valid tokens."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "x" * 40)
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-valid-token-here")

        result = validate_environment_variables()

        # Check these specific vars are valid
        assert result["variables"]["GITHUB_TOKEN"]["valid"] is True
        assert result["variables"]["SLACK_TOKEN"]["valid"] is True

    def test_validate_optional_not_set(self, monkeypatch):
        """Test that unset optional vars are still valid."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("SLACK_TOKEN", raising=False)

        result = validate_environment_variables()

        # Optional vars should be valid even when not set
        assert result["variables"]["GITHUB_TOKEN"]["set"] is False
        assert result["variables"]["GITHUB_TOKEN"]["valid"] is True


# =============================================================================
# LOAD CONFIG WITH VALIDATION TESTS
# =============================================================================

class TestLoadConfigWithValidation:
    """Tests for load_config_with_validation function."""

    def test_load_valid_config(self, monkeypatch):
        """Test loading valid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("SKIPPY_BASE_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_SCRIPTS_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_LOGS_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_CONVERSATIONS_PATH", tmpdir)

            config = load_config_with_validation()

            assert isinstance(config, SkippyConfig)
            assert config.skippy_base_path == tmpdir

    def test_load_invalid_config_raises(self, monkeypatch):
        """Test loading invalid configuration raises error."""
        monkeypatch.setenv("SKIPPY_BASE_PATH", "/nonexistent/path/12345")
        monkeypatch.setenv("SKIPPY_SCRIPTS_PATH", "/nonexistent/scripts/12345")

        with pytest.raises(ConfigValidationError) as exc_info:
            load_config_with_validation()

        assert len(exc_info.value.errors) > 0

    def test_load_config_logs_warnings(self, monkeypatch, tmp_path, caplog):
        """Test load_config_with_validation logs warnings."""
        import logging

        # Create valid paths
        scripts_path = tmp_path / "scripts"
        scripts_path.mkdir()
        logs_path = tmp_path / "logs"
        logs_path.mkdir()

        monkeypatch.setenv("SKIPPY_BASE_PATH", str(tmp_path))
        monkeypatch.setenv("SKIPPY_SCRIPTS_PATH", str(scripts_path))
        monkeypatch.setenv("SKIPPY_LOGS_PATH", str(logs_path))
        # Disable audit logging to trigger a warning
        monkeypatch.setenv("AUDIT_LOGGING", "false")

        with caplog.at_level(logging.WARNING, logger="lib.python.skippy_config"):
            config = load_config_with_validation()

        assert config is not None
        # Should have logged warning about audit logging being disabled
        assert any("audit logging" in record.message.lower()
                   for record in caplog.records)


# =============================================================================
# GENERATE CONFIG TEMPLATE TESTS
# =============================================================================

class TestGenerateConfigTemplate:
    """Tests for generate_config_template function."""

    def test_template_is_string(self):
        """Test template returns a string."""
        result = generate_config_template()
        assert isinstance(result, str)

    def test_template_contains_core_sections(self):
        """Test template contains expected sections."""
        result = generate_config_template()

        assert "CORE PATHS" in result
        assert "REMOTE SERVER" in result
        assert "FEATURE FLAGS" in result
        assert "PERFORMANCE" in result
        assert "SECURITY" in result
        assert "MONITORING" in result

    def test_template_contains_key_variables(self):
        """Test template contains key environment variables."""
        result = generate_config_template()

        assert "SKIPPY_BASE_PATH" in result
        assert "WORDPRESS_BASE_PATH" in result
        assert "EBON_HOST" in result
        assert "ENABLE_GOOGLE_DRIVE" in result
        assert "MAX_CONCURRENT_REQUESTS" in result
        assert "VALIDATE_PATHS" in result

    def test_template_has_comments(self):
        """Test template has comments for documentation."""
        result = generate_config_template()

        # Should have comment lines
        assert result.count("#") > 10

    def test_template_can_be_parsed(self):
        """Test template can be parsed as env file."""
        result = generate_config_template()

        env_vars = {}
        for line in result.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value

        # Should have some parseable variables
        assert len(env_vars) > 0
        assert "SKIPPY_BASE_PATH" in env_vars


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestConfigIntegration:
    """Integration tests for configuration workflow."""

    def test_full_config_workflow(self, monkeypatch):
        """Test complete configuration workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up environment
            monkeypatch.setenv("SKIPPY_BASE_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_SCRIPTS_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_LOGS_PATH", tmpdir)
            monkeypatch.setenv("SKIPPY_CONVERSATIONS_PATH", tmpdir)
            monkeypatch.setenv("EBON_HOST", "test@192.168.1.1")

            # Load config
            config = SkippyConfig.from_env()

            # Validate
            validator = ConfigValidator(config)
            is_valid = validator.validate()

            # Get report
            report = validator.get_validation_report()

            # Convert to JSON and back
            json_str = config.to_json()
            restored = SkippyConfig.from_json(json_str)

            assert is_valid is True
            assert report["valid"] is True
            assert restored.skippy_base_path == tmpdir

    def test_config_roundtrip(self):
        """Test config serialization roundtrip."""
        original = SkippyConfig(
            skippy_base_path="/test/path",
            enable_slack=True,
            max_concurrent_requests=50,
            request_timeout=45.0
        )

        # Dict roundtrip
        as_dict = original.to_dict()
        from_dict = SkippyConfig.from_dict(as_dict)
        assert from_dict.skippy_base_path == original.skippy_base_path
        assert from_dict.enable_slack == original.enable_slack

        # JSON roundtrip
        as_json = original.to_json()
        from_json = SkippyConfig.from_json(as_json)
        assert from_json.max_concurrent_requests == original.max_concurrent_requests
        assert from_json.request_timeout == original.request_timeout
