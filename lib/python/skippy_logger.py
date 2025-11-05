#!/usr/bin/env python3
"""
Skippy System Manager - Centralized Logging Library
Version: 1.0.0
Author: Skippy Development Team
Created: 2025-11-05

A centralized logging library providing consistent logging across all Skippy scripts.

Features:
- Structured logging with consistent format
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output
- Log rotation
- Contextual information (script name, timestamp, etc.)
- Integration with conversation logs
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class SkippyLogger:
    """
    Centralized logger for Skippy System Manager.

    Usage:
        from lib.python.skippy_logger import get_logger

        logger = get_logger(__name__)
        logger.info("Script started")
        logger.error("An error occurred")
    """

    _instances = {}

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_dir: Optional[str] = None,
        conversation_log: bool = False,
    ):
        """
        Initialize the Skippy logger.

        Args:
            name: Logger name (usually __name__ or script name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
            log_dir: Custom log directory (defaults to SKIPPY_BASE_PATH/logs)
            conversation_log: Whether to also log to conversation logs
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.conversation_log = conversation_log

        # Determine log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            skippy_base = os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")
            self.log_dir = Path(skippy_base) / "logs"

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up and configure the logger."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        simple_formatter = logging.Formatter(
            fmt="%(levelname)s: %(message)s"
        )

        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        if self.log_to_file:
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

            # Also log to a combined log file
            combined_log = self.log_dir / "skippy_combined.log"
            combined_handler = RotatingFileHandler(
                combined_log,
                maxBytes=50 * 1024 * 1024,  # 50MB
                backupCount=10,
            )
            combined_handler.setLevel(self.log_level)
            combined_handler.setFormatter(detailed_formatter)
            logger.addHandler(combined_handler)

        # Conversation log handler
        if self.conversation_log:
            self._add_conversation_handler(logger, detailed_formatter)

        return logger

    def _add_conversation_handler(self, logger: logging.Logger, formatter: logging.Formatter):
        """Add handler for conversation logs."""
        conversations_path = os.getenv(
            "SKIPPY_CONVERSATIONS_PATH",
            os.path.join(os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy"), "conversations")
        )
        conversations_dir = Path(conversations_path) / "script_logs"
        conversations_dir.mkdir(parents=True, exist_ok=True)

        # Create daily conversation log
        today = datetime.now().strftime("%Y-%m-%d")
        conversation_file = conversations_dir / f"script_log_{today}.md"

        conversation_handler = logging.FileHandler(conversation_file)
        conversation_handler.setLevel(logging.INFO)
        conversation_handler.setFormatter(formatter)
        logger.addHandler(conversation_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger


def get_logger(
    name: str,
    log_level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    conversation_log: bool = False,
) -> logging.Logger:
    """
    Get or create a logger instance.

    This is the main entry point for using the Skippy logging system.

    Args:
        name: Logger name (usually __name__ or script name)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        conversation_log: Whether to also log to conversation logs

    Returns:
        Configured logger instance

    Example:
        >>> from lib.python.skippy_logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting script")
        >>> logger.error("An error occurred")
    """
    # Get log level from environment if not specified
    if log_level is None:
        log_level = os.getenv("SKIPPY_LOG_LEVEL", "INFO")

    # Create unique key for logger instance
    key = (name, log_level, log_to_file, log_to_console, conversation_log)

    # Return existing instance or create new one
    if key not in SkippyLogger._instances:
        skippy_logger = SkippyLogger(
            name=name,
            log_level=log_level,
            log_to_file=log_to_file,
            log_to_console=log_to_console,
            conversation_log=conversation_log,
        )
        SkippyLogger._instances[key] = skippy_logger.get_logger()

    return SkippyLogger._instances[key]


def log_script_execution(script_name: str, action: str, details: Optional[dict] = None):
    """
    Log script execution for audit trail.

    Args:
        script_name: Name of the script
        action: Action being performed (start, complete, error, etc.)
        details: Additional details to log (optional)

    Example:
        >>> log_script_execution("backup_script", "start")
        >>> log_script_execution("backup_script", "complete", {"files": 10, "size": "1.2GB"})
        >>> log_script_execution("backup_script", "error", {"error": "Connection timeout"})
    """
    logger = get_logger("skippy.audit", conversation_log=True)

    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "script": script_name,
        "action": action,
    }

    if details:
        log_entry.update(details)

    logger.info(f"Script execution: {log_entry}")


def log_error_with_context(error: Exception, context: Optional[dict] = None):
    """
    Log error with full context for debugging.

    Args:
        error: The exception that occurred
        context: Additional context information (optional)

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_error_with_context(e, {"operation": "backup", "file": "data.db"})
    """
    logger = get_logger("skippy.errors", conversation_log=True)

    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat(),
    }

    if context:
        error_details["context"] = context

    logger.error(f"Error occurred: {error_details}", exc_info=True)


# Convenience functions for common logging patterns
def log_info(message: str, script_name: Optional[str] = None):
    """Quick info log."""
    logger = get_logger(script_name or "skippy")
    logger.info(message)


def log_warning(message: str, script_name: Optional[str] = None):
    """Quick warning log."""
    logger = get_logger(script_name or "skippy")
    logger.warning(message)


def log_error(message: str, script_name: Optional[str] = None):
    """Quick error log."""
    logger = get_logger(script_name or "skippy")
    logger.error(message)


def log_debug(message: str, script_name: Optional[str] = None):
    """Quick debug log."""
    logger = get_logger(script_name or "skippy", log_level="DEBUG")
    logger.debug(message)


# Example usage
if __name__ == "__main__":
    # Example 1: Basic usage
    logger = get_logger(__name__)
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Example 2: Script execution logging
    log_script_execution("example_script", "start")
    log_script_execution("example_script", "complete", {"duration": "5.2s"})

    # Example 3: Error logging with context
    try:
        raise ValueError("Example error")
    except Exception as e:
        log_error_with_context(e, {"operation": "test", "user": "admin"})

    # Example 4: Convenience functions
    log_info("Quick info message")
    log_warning("Quick warning message")
    log_error("Quick error message")

    print("Logging examples completed. Check logs directory for output.")
