"""
Rate Limiting for MCP Tools
============================

Provides rate limiting functionality to prevent abuse of MCP tools.
Uses in-memory storage for simple deployments, with optional Redis support.

SECURITY: Rate limiting is critical to prevent:
- DoS attacks through excessive API calls
- Exchange API rate limit exhaustion
- Resource exhaustion on the server

Usage:
    from rate_limiter import RateLimiter, rate_limited

    limiter = RateLimiter()

    # Check rate limit manually
    if not await limiter.check("user_123", "crypto_portfolio_summary", limit=10, window=60):
        return "Rate limit exceeded. Please wait before retrying."

    # Or use decorator (for async functions)
    @rate_limited(limit=10, window=60)
    async def my_tool():
        ...
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Default limits per tool category
    default_limit: int = 30  # requests per window
    default_window: int = 60  # seconds

    # Stricter limits for expensive operations
    expensive_limit: int = 5
    expensive_window: int = 60

    # Trading operations (extra cautious)
    trading_limit: int = 10
    trading_window: int = 300  # 5 minutes

    # Analysis operations
    analysis_limit: int = 10
    analysis_window: int = 60

    # Enable/disable rate limiting globally
    enabled: bool = True


@dataclass
class RateLimitEntry:
    """Tracks rate limit state for a key."""
    count: int = 0
    window_start: float = 0.0


class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm.

    Thread-safe for use in async context.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = asyncio.Lock()

    def _make_key(self, identifier: str, resource: str) -> str:
        """Create rate limit key."""
        return f"ratelimit:{identifier}:{resource}"

    async def check(
        self,
        identifier: str,
        resource: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> bool:
        """
        Check if request is within rate limits.

        Args:
            identifier: User/session identifier
            resource: Resource being accessed (tool name)
            limit: Max requests per window (uses default if None)
            window: Window size in seconds (uses default if None)

        Returns:
            True if request is allowed, False if rate limited
        """
        if not self.config.enabled:
            return True

        limit = limit or self.config.default_limit
        window = window or self.config.default_window
        key = self._make_key(identifier, resource)
        current_time = time.time()

        async with self._lock:
            entry = self._limits[key]

            # Reset window if expired
            if current_time - entry.window_start >= window:
                entry.count = 0
                entry.window_start = current_time

            # Check limit
            if entry.count >= limit:
                logger.warning(
                    f"Rate limit exceeded for {key}: {entry.count}/{limit} in {window}s"
                )
                return False

            # Increment counter
            entry.count += 1
            return True

    async def get_remaining(
        self,
        identifier: str,
        resource: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> Tuple[int, float]:
        """
        Get remaining requests and time until reset.

        Returns:
            Tuple of (remaining_requests, seconds_until_reset)
        """
        limit = limit or self.config.default_limit
        window = window or self.config.default_window
        key = self._make_key(identifier, resource)
        current_time = time.time()

        async with self._lock:
            entry = self._limits[key]

            # Check if window expired
            elapsed = current_time - entry.window_start
            if elapsed >= window:
                return limit, 0.0

            remaining = max(0, limit - entry.count)
            reset_in = window - elapsed
            return remaining, reset_in

    async def reset(self, identifier: str, resource: str) -> None:
        """Reset rate limit for a specific key."""
        key = self._make_key(identifier, resource)
        async with self._lock:
            if key in self._limits:
                del self._limits[key]

    def get_tool_limits(self, tool_name: str) -> Tuple[int, int]:
        """
        Get appropriate limits for a tool based on its name.

        Returns:
            Tuple of (limit, window)
        """
        # Trading operations - extra cautious
        if any(x in tool_name.lower() for x in ["trade", "order", "buy", "sell", "rebalance"]):
            return self.config.trading_limit, self.config.trading_window

        # Expensive analysis operations
        if any(x in tool_name.lower() for x in ["analysis", "backtest", "optimize", "ai_"]):
            return self.config.analysis_limit, self.config.analysis_window

        # Data-heavy operations
        if any(x in tool_name.lower() for x in ["history", "export", "report"]):
            return self.config.expensive_limit, self.config.expensive_window

        # Default for most read operations
        return self.config.default_limit, self.config.default_window


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limited(
    limit: Optional[int] = None,
    window: Optional[int] = None,
    identifier_param: str = "session_id",
):
    """
    Decorator to apply rate limiting to async functions.

    Args:
        limit: Max requests per window
        window: Window size in seconds
        identifier_param: Parameter name to use as identifier (or "default")

    Usage:
        @rate_limited(limit=10, window=60)
        async def my_tool(params):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Get identifier from kwargs or use default
            identifier = kwargs.get(identifier_param, "default")
            if identifier == "default" or identifier is None:
                # Try to get from params if it's a Pydantic model
                if args and hasattr(args[0], "session_id"):
                    identifier = getattr(args[0], "session_id", "default")
                else:
                    identifier = "default"

            # Get tool-specific limits
            tool_limit, tool_window = limiter.get_tool_limits(func.__name__)
            final_limit = limit or tool_limit
            final_window = window or tool_window

            # Check rate limit
            if not await limiter.check(identifier, func.__name__, final_limit, final_window):
                remaining, reset_in = await limiter.get_remaining(
                    identifier, func.__name__, final_limit, final_window
                )
                return (
                    f"Rate limit exceeded for {func.__name__}. "
                    f"Please wait {reset_in:.0f} seconds before retrying. "
                    f"Limit: {final_limit} requests per {final_window} seconds."
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def check_mcp_rate_limit(
    tool_name: str,
    session_id: str = "default",
) -> Optional[str]:
    """
    Check rate limit for an MCP tool call.

    Returns None if allowed, or an error message if rate limited.
    """
    limiter = get_rate_limiter()
    limit, window = limiter.get_tool_limits(tool_name)

    if not await limiter.check(session_id, tool_name, limit, window):
        remaining, reset_in = await limiter.get_remaining(
            session_id, tool_name, limit, window
        )
        return (
            f"Rate limit exceeded for {tool_name}. "
            f"Please wait {reset_in:.0f} seconds before retrying. "
            f"Limit: {limit} requests per {window} seconds."
        )

    return None
