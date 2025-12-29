"""Backend factory for creating session backends based on configuration."""

import logging

from src.config.settings import get_settings
from src.state.backends.base import SessionBackend
from src.state.backends.memory import InMemoryBackend
from src.state.backends.redis import RedisBackend

logger = logging.getLogger(__name__)


async def create_backend() -> SessionBackend:
    """Create a session backend based on application settings.

    Reads the session_backend configuration from settings and returns
    the appropriate backend implementation:
        - "memory": Returns InMemoryBackend for development/testing
        - "redis": Returns RedisBackend for production use

    If Redis is configured but connection fails, gracefully falls back
    to InMemoryBackend with a warning.

    Returns:
        SessionBackend: The configured backend implementation.

    Example:
        >>> from src.state.backends import create_backend
        >>> backend = await create_backend()
        >>> await backend.create("session-123", game_state)
    """
    settings = get_settings()

    if settings.session_backend == "memory":
        logger.info("Using in-memory session backend")
        return InMemoryBackend()

    # Try Redis for production
    try:
        backend = RedisBackend(
            redis_url=settings.redis_url,
            ttl=settings.redis_session_ttl,
        )
        # Test connection by pinging Redis
        if backend._redis:
            await backend._redis.ping()
        logger.info("Using Redis session backend")
        return backend
    except Exception as e:
        logger.warning(
            f"Failed to connect to Redis: {e}. "
            "Falling back to in-memory session backend."
        )
        return InMemoryBackend()
