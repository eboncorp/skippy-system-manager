"""
Logging Configuration
Provides structured logging with proper formatting and log levels.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ("msg", "args", "exc_info", "exc_text", "stack_info",
                          "lineno", "funcName", "created", "msecs", "relativeCreated",
                          "thread", "threadName", "processName", "process", "name",
                          "levelname", "levelno", "pathname", "filename", "module",
                          "message"):
                log_data[key] = value
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for human-readable output."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    quiet: bool = False
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs
        json_format: Use JSON format for file logs
        quiet: Suppress console output
    
    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger("crypto_portfolio")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if sys.stdout.isatty():
            # Use colored output for terminal
            console_format = ColoredFormatter(
                "%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
                datefmt="%H:%M:%S"
            )
        else:
            console_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S"
            )
        
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        if json_format:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            ))
        
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the crypto_portfolio namespace."""
    return logging.getLogger(f"crypto_portfolio.{name}")


# Exchange-specific loggers
def get_exchange_logger(exchange: str) -> logging.Logger:
    """Get logger for a specific exchange."""
    return get_logger(f"exchange.{exchange.lower()}")


def get_wallet_logger(chain: str) -> logging.Logger:
    """Get logger for a specific blockchain."""
    return get_logger(f"wallet.{chain.lower()}")


# Default setup
_default_logger = None

def init_default_logging():
    """Initialize default logging configuration."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging(
            level="INFO",
            log_file="logs/portfolio.log",
            json_format=True
        )
    return _default_logger
