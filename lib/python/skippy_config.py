#!/usr/bin/env python3
"""
Skippy System Manager - Configuration Validation Library
Version: 1.0.0
Author: Skippy Development Team
Created: 2025-11-16

Provides configuration validation, schema enforcement, and environment setup.

Features:
- Configuration schema validation
- Environment variable validation
- Path existence checks
- Required field enforcement
- Type checking
- Default value management
"""

import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)

    def __str__(self):
        if self.errors:
            error_list = "\n".join(f"  - {e}" for e in self.errors)
            return f"{self.message}\nValidation errors:\n{error_list}"
        return self.message


@dataclass
class PathConfig:
    """Configuration for a path that needs validation."""
    env_var: str
    default: str
    must_exist: bool = False
    create_if_missing: bool = False
    is_file: bool = False
    description: str = ""


@dataclass
class EnvVarConfig:
    """Configuration for an environment variable."""
    name: str
    required: bool = True
    default: Optional[str] = None
    pattern: Optional[str] = None  # Regex pattern for validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    description: str = ""


@dataclass
class SkippyConfig:
    """
    Main configuration class for Skippy System Manager.

    This validates and manages all configuration settings.
    """
    # Core paths
    skippy_base_path: str = ""
    wordpress_base_path: str = ""
    conversations_path: str = ""
    scripts_path: str = ""
    backup_path: str = ""
    logs_path: str = ""

    # Remote server settings
    ebon_host: str = ""
    ssh_opts: str = ""

    # Feature flags
    enable_google_drive: bool = True
    enable_google_photos: bool = True
    enable_github: bool = True
    enable_slack: bool = False
    enable_browser_automation: bool = False

    # Performance settings
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0

    # Security settings
    validate_paths: bool = True
    validate_commands: bool = True
    validate_urls: bool = True
    audit_logging: bool = True

    # Monitoring
    health_check_interval: int = 300  # seconds
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

    @classmethod
    def from_env(cls) -> 'SkippyConfig':
        """
        Create configuration from environment variables.

        Returns:
            SkippyConfig instance with values from environment
        """
        skippy_base = os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")
        wordpress_base = os.getenv("WORDPRESS_BASE_PATH", "/home/dave/RunDaveRun")

        return cls(
            skippy_base_path=skippy_base,
            wordpress_base_path=wordpress_base,
            conversations_path=os.getenv("SKIPPY_CONVERSATIONS_PATH", f"{skippy_base}/conversations"),
            scripts_path=os.getenv("SKIPPY_SCRIPTS_PATH", f"{skippy_base}/scripts"),
            backup_path=os.getenv("WORDPRESS_BACKUP_PATH", f"{wordpress_base}/backups"),
            logs_path=os.getenv("SKIPPY_LOGS_PATH", f"{skippy_base}/logs"),

            ebon_host=os.getenv("EBON_HOST", "ebon@10.0.0.29"),
            ssh_opts=os.getenv("SSH_OPTS", "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"),

            enable_google_drive=os.getenv("ENABLE_GOOGLE_DRIVE", "true").lower() == "true",
            enable_google_photos=os.getenv("ENABLE_GOOGLE_PHOTOS", "true").lower() == "true",
            enable_github=os.getenv("ENABLE_GITHUB", "true").lower() == "true",
            enable_slack=os.getenv("ENABLE_SLACK", "false").lower() == "true",
            enable_browser_automation=os.getenv("ENABLE_BROWSER_AUTOMATION", "false").lower() == "true",

            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30.0")),
            retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            retry_base_delay=float(os.getenv("RETRY_BASE_DELAY", "1.0")),

            validate_paths=os.getenv("VALIDATE_PATHS", "true").lower() == "true",
            validate_commands=os.getenv("VALIDATE_COMMANDS", "true").lower() == "true",
            validate_urls=os.getenv("VALIDATE_URLS", "true").lower() == "true",
            audit_logging=os.getenv("AUDIT_LOGGING", "true").lower() == "true",

            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
            circuit_breaker_failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            circuit_breaker_timeout=float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkippyConfig':
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, json_str: str) -> 'SkippyConfig':
        """Create configuration from JSON string."""
        return cls.from_dict(json.loads(json_str))


class ConfigValidator:
    """
    Validates Skippy configuration for correctness and security.

    Example:
        config = SkippyConfig.from_env()
        validator = ConfigValidator(config)

        if not validator.validate():
            print(f"Configuration errors: {validator.errors}")
        else:
            print("Configuration is valid!")
    """

    def __init__(self, config: SkippyConfig):
        """
        Initialize validator with configuration.

        Args:
            config: SkippyConfig instance to validate
        """
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Perform full configuration validation.

        Returns:
            True if configuration is valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Validate paths
        self._validate_paths()

        # Validate remote server settings
        self._validate_remote_settings()

        # Validate performance settings
        self._validate_performance_settings()

        # Validate security settings
        self._validate_security_settings()

        # Validate monitoring settings
        self._validate_monitoring_settings()

        if self.errors:
            logger.error(f"Configuration validation failed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")

        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        return len(self.errors) == 0

    def _validate_paths(self):
        """Validate all path configurations."""
        paths_to_check = [
            ("skippy_base_path", self.config.skippy_base_path, True),
            ("scripts_path", self.config.scripts_path, True),
            ("logs_path", self.config.logs_path, False),  # Can be created
        ]

        for name, path, must_exist in paths_to_check:
            if not path:
                self.errors.append(f"Path '{name}' is empty or not set")
                continue

            path_obj = Path(path)

            # Check for dangerous patterns
            if ".." in path:
                self.errors.append(f"Path '{name}' contains directory traversal pattern (..)")

            # Check existence if required
            if must_exist and not path_obj.exists():
                self.errors.append(f"Path '{name}' ({path}) does not exist")
            elif not must_exist and not path_obj.exists():
                self.warnings.append(f"Path '{name}' ({path}) does not exist (will be created if needed)")

        # Validate conversations path is under skippy base
        if self.config.conversations_path and self.config.skippy_base_path:
            conv_path = Path(self.config.conversations_path).resolve()
            base_path = Path(self.config.skippy_base_path).resolve()
            try:
                conv_path.relative_to(base_path)
            except ValueError:
                self.warnings.append(
                    f"conversations_path ({conv_path}) is outside skippy_base_path ({base_path})"
                )

    def _validate_remote_settings(self):
        """Validate remote server configuration."""
        # Validate EBON_HOST format (user@ip or user@hostname)
        if self.config.ebon_host:
            pattern = r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+$'
            if not re.match(pattern, self.config.ebon_host):
                self.errors.append(
                    f"ebon_host '{self.config.ebon_host}' is not in valid format (user@host)"
                )

            # Check for potentially dangerous SSH options
            dangerous_opts = ["--no-host-checking", "ProxyCommand"]
            for opt in dangerous_opts:
                if opt in self.config.ssh_opts:
                    self.warnings.append(
                        f"SSH options contain potentially risky option: {opt}"
                    )

    def _validate_performance_settings(self):
        """Validate performance configuration."""
        if self.config.max_concurrent_requests < 1:
            self.errors.append("max_concurrent_requests must be at least 1")
        elif self.config.max_concurrent_requests > 100:
            self.warnings.append("max_concurrent_requests is very high (>100), may cause resource issues")

        if self.config.request_timeout <= 0:
            self.errors.append("request_timeout must be positive")
        elif self.config.request_timeout > 300:
            self.warnings.append("request_timeout is very long (>5 minutes)")

        if self.config.retry_max_attempts < 1:
            self.errors.append("retry_max_attempts must be at least 1")
        elif self.config.retry_max_attempts > 10:
            self.warnings.append("retry_max_attempts is high (>10), may cause long delays")

        if self.config.retry_base_delay <= 0:
            self.errors.append("retry_base_delay must be positive")

    def _validate_security_settings(self):
        """Validate security configuration."""
        # Recommend enabling security features
        if not self.config.validate_paths:
            self.warnings.append("Path validation is disabled - this is a security risk")

        if not self.config.validate_commands:
            self.warnings.append("Command validation is disabled - this is a security risk")

        if not self.config.validate_urls:
            self.warnings.append("URL validation is disabled - this is a security risk")

        if not self.config.audit_logging:
            self.warnings.append("Audit logging is disabled - recommended for security monitoring")

    def _validate_monitoring_settings(self):
        """Validate monitoring configuration."""
        if self.config.health_check_interval < 10:
            self.warnings.append("health_check_interval is very short (<10s), may impact performance")

        if self.config.circuit_breaker_failure_threshold < 1:
            self.errors.append("circuit_breaker_failure_threshold must be at least 1")

        if self.config.circuit_breaker_timeout <= 0:
            self.errors.append("circuit_breaker_timeout must be positive")

    def get_validation_report(self) -> Dict[str, Any]:
        """Get a detailed validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "config": self.config.to_dict(),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }


def validate_environment_variables() -> Dict[str, Any]:
    """
    Validate required environment variables are set.

    Returns:
        Dictionary with validation results
    """
    required_vars = [
        EnvVarConfig(
            name="SKIPPY_BASE_PATH",
            required=False,
            default="/home/dave/skippy",
            description="Base path for Skippy installation"
        ),
        EnvVarConfig(
            name="EBON_HOST",
            required=False,
            default="ebon@10.0.0.29",
            pattern=r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+$',
            description="Remote server in user@host format"
        ),
    ]

    optional_vars = [
        EnvVarConfig(
            name="GOOGLE_APPLICATION_CREDENTIALS",
            required=False,
            description="Path to Google service account credentials"
        ),
        EnvVarConfig(
            name="GITHUB_TOKEN",
            required=False,
            min_length=40,
            description="GitHub personal access token"
        ),
        EnvVarConfig(
            name="SLACK_TOKEN",
            required=False,
            pattern=r'^xox[bp]-.*$',
            description="Slack bot or user token"
        ),
    ]

    errors = []
    warnings = []
    env_status = {}

    # Check required variables
    for var_config in required_vars:
        value = os.getenv(var_config.name, var_config.default)

        if var_config.required and not value:
            errors.append(f"Required environment variable '{var_config.name}' is not set")
            env_status[var_config.name] = {"set": False, "valid": False}
        else:
            valid = True

            if var_config.pattern and value:
                if not re.match(var_config.pattern, value):
                    errors.append(
                        f"Environment variable '{var_config.name}' does not match required pattern"
                    )
                    valid = False

            if var_config.min_length and value and len(value) < var_config.min_length:
                errors.append(
                    f"Environment variable '{var_config.name}' is too short (min {var_config.min_length})"
                )
                valid = False

            env_status[var_config.name] = {"set": bool(value), "valid": valid}

    # Check optional variables
    for var_config in optional_vars:
        value = os.getenv(var_config.name)

        if value:
            valid = True

            if var_config.pattern:
                if not re.match(var_config.pattern, value):
                    warnings.append(
                        f"Optional variable '{var_config.name}' does not match expected pattern"
                    )
                    valid = False

            if var_config.min_length and len(value) < var_config.min_length:
                warnings.append(
                    f"Optional variable '{var_config.name}' seems too short (expected min {var_config.min_length})"
                )
                valid = False

            env_status[var_config.name] = {"set": True, "valid": valid}
        else:
            env_status[var_config.name] = {"set": False, "valid": True}  # Optional, so not invalid

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "variables": env_status
    }


def load_config_with_validation() -> SkippyConfig:
    """
    Load and validate configuration, raising an error if invalid.

    Returns:
        Validated SkippyConfig instance

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    config = SkippyConfig.from_env()
    validator = ConfigValidator(config)

    if not validator.validate():
        raise ConfigValidationError(
            "Configuration validation failed",
            errors=validator.errors
        )

    # Log warnings even if validation passes
    for warning in validator.warnings:
        logger.warning(f"Configuration warning: {warning}")

    logger.info("Configuration loaded and validated successfully")
    return config


def generate_config_template() -> str:
    """
    Generate a template .env file with all configuration options.

    Returns:
        String containing .env template with documentation
    """
    template = """# Skippy System Manager Configuration
# Generated template - customize for your environment
# Copy to .env and modify values as needed

# =============================================================================
# CORE PATHS
# =============================================================================
# Base installation path for Skippy
SKIPPY_BASE_PATH=/home/dave/skippy

# WordPress installation path
WORDPRESS_BASE_PATH=/home/dave/RunDaveRun

# Conversations storage path
SKIPPY_CONVERSATIONS_PATH=${SKIPPY_BASE_PATH}/conversations

# Scripts directory path
SKIPPY_SCRIPTS_PATH=${SKIPPY_BASE_PATH}/scripts

# Backup storage path
WORDPRESS_BACKUP_PATH=${WORDPRESS_BASE_PATH}/backups

# Logs directory path
SKIPPY_LOGS_PATH=${SKIPPY_BASE_PATH}/logs

# =============================================================================
# REMOTE SERVER SETTINGS
# =============================================================================
# Remote server connection (user@hostname format)
EBON_HOST=ebon@10.0.0.29

# SSH connection options
SSH_OPTS=-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null

# =============================================================================
# FEATURE FLAGS
# =============================================================================
# Enable/disable specific features
ENABLE_GOOGLE_DRIVE=true
ENABLE_GOOGLE_PHOTOS=true
ENABLE_GITHUB=true
ENABLE_SLACK=false
ENABLE_BROWSER_AUTOMATION=false

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================
# Maximum concurrent HTTP requests
MAX_CONCURRENT_REQUESTS=10

# Request timeout in seconds
REQUEST_TIMEOUT=30.0

# Retry configuration
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
# Enable input validation (recommended: true)
VALIDATE_PATHS=true
VALIDATE_COMMANDS=true
VALIDATE_URLS=true

# Enable audit logging (recommended: true)
AUDIT_LOGGING=true

# =============================================================================
# MONITORING SETTINGS
# =============================================================================
# Health check interval in seconds
HEALTH_CHECK_INTERVAL=300

# Circuit breaker settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60.0

# =============================================================================
# EXTERNAL SERVICE CREDENTIALS (Optional)
# =============================================================================
# Google API credentials (path to JSON file)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# GitHub personal access token
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Slack bot token
# SLACK_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx

# Pexels API key
# PEXELS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# =============================================================================
# LOGGING
# =============================================================================
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
SKIPPY_LOG_LEVEL=INFO
"""
    return template


# =============================================================================
# EXAMPLE USAGE AND TESTS
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Skippy Configuration Validation - Examples")
    print("=" * 60)

    # Example 1: Load configuration from environment
    print("\n1. Loading configuration from environment:")
    config = SkippyConfig.from_env()
    print(f"   Base path: {config.skippy_base_path}")
    print(f"   Remote host: {config.ebon_host}")
    print(f"   Max retries: {config.retry_max_attempts}")

    # Example 2: Validate configuration
    print("\n2. Validating configuration:")
    validator = ConfigValidator(config)
    is_valid = validator.validate()
    print(f"   Configuration valid: {is_valid}")

    if validator.errors:
        print("   Errors:")
        for error in validator.errors:
            print(f"     - {error}")

    if validator.warnings:
        print("   Warnings:")
        for warning in validator.warnings:
            print(f"     - {warning}")

    # Example 3: Environment variable validation
    print("\n3. Validating environment variables:")
    env_result = validate_environment_variables()
    print(f"   Environment valid: {env_result['valid']}")
    for var_name, status in env_result['variables'].items():
        set_status = "✓" if status['set'] else "✗"
        valid_status = "valid" if status['valid'] else "invalid"
        print(f"   {set_status} {var_name}: {valid_status}")

    # Example 4: Generate config template
    print("\n4. Configuration template preview (first 20 lines):")
    template = generate_config_template()
    for line in template.split('\n')[:20]:
        print(f"   {line}")
    print("   ...")

    # Example 5: Convert to JSON
    print("\n5. Configuration as JSON (partial):")
    config_json = config.to_json()
    print(f"   {config_json[:200]}...")

    print("\n" + "=" * 60)
    print("Configuration validation examples completed!")
