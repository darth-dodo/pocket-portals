"""In-memory session backend."""

from src.state.models import GameState


class InMemoryBackend:
    """In-memory session storage for development and testing.

    This backend stores all sessions in a Python dictionary, providing
    fast access but no persistence across process restarts.

    Suitable for:
        - Local development
        - Unit and integration testing
        - Single-process deployments where persistence is not required

    Not suitable for:
        - Production deployments requiring persistence
        - Multi-process or distributed deployments
        - Deployments requiring session recovery after crashes
    """

    def __init__(self) -> None:
        """Initialize empty session storage."""
        self._sessions: dict[str, GameState] = {}

    async def create(self, session_id: str, state: GameState) -> None:
        """Create a new session.

        Args:
            session_id: Unique identifier for the session.
            state: Initial game state for the session.
        """
        self._sessions[session_id] = state

    async def get(self, session_id: str) -> GameState | None:
        """Get session by ID.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            The GameState if the session exists, None otherwise.
        """
        return self._sessions.get(session_id)

    async def update(self, session_id: str, state: GameState) -> None:
        """Update existing session.

        Args:
            session_id: Unique identifier for the session.
            state: New game state to store.
        """
        self._sessions[session_id] = state

    async def delete(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session existed and was deleted, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        """Check if session exists.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            True if the session exists, False otherwise.
        """
        return session_id in self._sessions

    def clear(self) -> None:
        """Clear all sessions (utility for testing)."""
        self._sessions.clear()

    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)
