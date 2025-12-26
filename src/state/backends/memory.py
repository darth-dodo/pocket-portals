"""In-memory session backend."""

from src.state.models import GameState


class InMemoryBackend:
    """In-memory session storage for development and testing.

    This backend stores all sessions in a Python dictionary, providing
    fast access but no persistence across process restarts.
    """

    def __init__(self) -> None:
        """Initialize empty session storage."""
        self._sessions: dict[str, GameState] = {}

    async def create(self, session_id: str, state: GameState) -> None:
        """Create a new session."""
        self._sessions[session_id] = state

    async def get(self, session_id: str) -> GameState | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    async def update(self, session_id: str, state: GameState) -> None:
        """Update existing session."""
        self._sessions[session_id] = state

    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._sessions

    def clear(self) -> None:
        """Clear all sessions (utility for testing)."""
        self._sessions.clear()

    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)
