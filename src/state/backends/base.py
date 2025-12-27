"""Abstract base for session backends."""

from typing import Protocol, runtime_checkable

from src.state.models import GameState


@runtime_checkable
class SessionBackend(Protocol):
    """Protocol defining session storage operations.

    This protocol defines the interface that all session backends must implement.
    Using Protocol allows for structural subtyping (duck typing) without requiring
    explicit inheritance.

    All methods are async to support both in-memory and I/O-bound backends
    (e.g., Redis, database) with a consistent interface.
    """

    async def create(self, session_id: str, state: GameState) -> None:
        """Create a new session.

        Args:
            session_id: Unique identifier for the session.
            state: Initial game state for the session.
        """
        ...

    async def get(self, session_id: str) -> GameState | None:
        """Get session by ID.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The GameState if the session exists, None otherwise.
        """
        ...

    async def update(self, session_id: str, state: GameState) -> None:
        """Update existing session.

        Args:
            session_id: Unique identifier for the session.
            state: New game state to store.
        """
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session existed and was deleted, False otherwise.
        """
        ...

    async def exists(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session exists, False otherwise.
        """
        ...
