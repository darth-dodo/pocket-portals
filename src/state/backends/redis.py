"""Redis session backend."""

from typing import Any

import redis.asyncio as redis  # type: ignore[import-untyped]

from src.state.models import GameState


class RedisBackend:
    """Redis-backed session storage for production.

    Provides persistent session storage with automatic TTL-based expiration.
    Uses Redis for high-performance, distributed session management.

    Attributes:
        _redis: Async Redis client connection.
        _ttl: Time-to-live in seconds for session keys (default: 24 hours).
        _prefix: Key prefix for namespacing session keys.
    """

    def __init__(self, redis_url: str, ttl: int = 86400) -> None:
        """Initialize Redis backend.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379").
            ttl: Session time-to-live in seconds (default: 86400 = 24 hours).
        """
        self._redis: redis.Redis[Any] = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl
        self._prefix = "pocket_portals:session:"

    def _key(self, session_id: str) -> str:
        """Generate Redis key for a session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            Prefixed Redis key string.
        """
        return f"{self._prefix}{session_id}"

    async def create(self, session_id: str, state: GameState) -> None:
        """Create a new session with the given state.

        Args:
            session_id: Unique identifier for the session.
            state: Initial game state for the session.
        """
        await self._redis.setex(
            self._key(session_id),
            self._ttl,
            state.model_dump_json(),
        )

    async def get(self, session_id: str) -> GameState | None:
        """Retrieve a session by ID.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The game state if found, None otherwise.
        """
        data = await self._redis.get(self._key(session_id))
        if data:
            return GameState.model_validate_json(data)
        return None

    async def update(self, session_id: str, state: GameState) -> None:
        """Update an existing session with new state.

        This also refreshes the TTL for the session.

        Args:
            session_id: Unique identifier for the session.
            state: Updated game state.
        """
        await self.create(session_id, state)  # Same as create with TTL refresh

    async def delete(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session was deleted, False if not found.
        """
        result = await self._redis.delete(self._key(session_id))
        return result > 0

    async def exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session exists, False otherwise.
        """
        result = await self._redis.exists(self._key(session_id))
        return result > 0

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.aclose()
