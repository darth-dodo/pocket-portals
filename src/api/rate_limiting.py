"""Rate limiting module for Pocket Portals API.

Privacy-first rate limiting using session_id only - no IP tracking.
Uses in-memory tracking per process with configurable limits.
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request

from src.config.settings import get_settings


@dataclass
class RateLimitBucket:
    """Track request counts for rate limiting."""

    calls: list[float] = field(default_factory=list)

    def clean_old_calls(self, window_seconds: int = 60) -> None:
        """Remove calls outside the time window."""
        cutoff = time.time() - window_seconds
        self.calls = [t for t in self.calls if t > cutoff]

    def add_call(self) -> None:
        """Record a new call."""
        self.calls.append(time.time())

    def count(self, window_seconds: int = 60) -> int:
        """Count calls within the time window."""
        self.clean_old_calls(window_seconds)
        return len(self.calls)


class RateLimiter:
    """In-memory rate limiter using session_id for tracking.

    Privacy-first design: only uses session_id, never tracks IP addresses.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, RateLimitBucket] = defaultdict(RateLimitBucket)
        self._settings = get_settings()

    def _get_session_id(self, request: Request) -> str:
        """Extract session_id from request.

        Looks in headers, query params, and form data.
        Returns a default key for anonymous requests.
        """
        # Check header first (preferred)
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id

        # Check query params
        session_id = request.query_params.get("session_id")
        if session_id:
            return session_id

        # For anonymous requests, use a general bucket
        # This is still privacy-preserving as we don't track IP
        return "anonymous"

    def check_rate_limit(
        self,
        request: Request,
        limit: int,
        window_seconds: int = 60,
    ) -> None:
        """Check rate limit and raise HTTPException if exceeded.

        Args:
            request: The FastAPI request object
            limit: Maximum calls allowed in window
            window_seconds: Time window in seconds (default 60)

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if not self._settings.rate_limit_enabled:
            return

        # Skip rate limiting in test environment
        if self._settings.environment == "test":
            return

        session_id = self._get_session_id(request)
        bucket_key = f"{session_id}:{limit}"  # Separate buckets per limit tier

        bucket = self._buckets[bucket_key]
        current_count = bucket.count(window_seconds)

        if current_count >= limit:
            retry_after = window_seconds
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {limit} requests per minute",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        bucket.add_call()

    def check_llm_rate_limit(self, request: Request) -> None:
        """Check rate limit for LLM-heavy endpoints (20/min)."""
        self.check_rate_limit(request, self._settings.rate_limit_llm_calls)

    def check_combat_rate_limit(self, request: Request) -> None:
        """Check rate limit for combat endpoints (60/min)."""
        self.check_rate_limit(request, self._settings.rate_limit_combat_calls)

    def check_default_rate_limit(self, request: Request) -> None:
        """Check rate limit for general endpoints (100/min)."""
        self.check_rate_limit(request, self._settings.rate_limit_default_calls)


# Global rate limiter instance
rate_limiter = RateLimiter()


def require_rate_limit(
    limit_type: str = "default",
) -> Callable[[Request], None]:
    """Dependency factory for rate limiting.

    Usage:
        @app.get("/endpoint")
        async def endpoint(request: Request, _: None = Depends(require_rate_limit("llm"))):
            ...

    Args:
        limit_type: One of "llm", "combat", or "default"

    Returns:
        A dependency function that checks rate limits
    """

    def rate_limit_dependency(request: Request) -> None:
        if limit_type == "llm":
            rate_limiter.check_llm_rate_limit(request)
        elif limit_type == "combat":
            rate_limiter.check_combat_rate_limit(request)
        else:
            rate_limiter.check_default_rate_limit(request)

    return rate_limit_dependency
