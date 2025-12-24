"""Session manager for game state persistence."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.state.models import GamePhase, GameState

if TYPE_CHECKING:
    from src.state.character import CharacterSheet


class SessionManager:
    """Manages game sessions with in-memory storage."""

    def __init__(self) -> None:
        """Initialize session manager with empty session storage."""
        self._sessions: dict[str, GameState] = {}

    def create_session(self) -> GameState:
        """Create a new session with default state.

        Returns:
            GameState: New game state with unique session ID
        """
        session_id = str(uuid.uuid4())
        state = GameState(session_id=session_id)
        self._sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> GameState | None:
        """Get existing session or None.

        Args:
            session_id: Session identifier

        Returns:
            GameState if session exists, None otherwise
        """
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str | None) -> GameState:
        """Get existing session or create new one.

        Args:
            session_id: Optional session identifier

        Returns:
            GameState: Existing or newly created game state
        """
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session()

    def add_exchange(self, session_id: str, action: str, narrative: str) -> None:
        """Add conversation exchange, maintaining history limit of 20.

        Args:
            session_id: Session identifier
            action: Player action text
            narrative: Game narrative response
        """
        state = self._sessions.get(session_id)
        if state:
            state.conversation_history.append(
                {"action": action, "narrative": narrative}
            )
            if len(state.conversation_history) > 20:
                state.conversation_history = state.conversation_history[-20:]

    def update_health(self, session_id: str, damage: int) -> int:
        """Apply damage and return remaining health.

        Args:
            session_id: Session identifier
            damage: Amount of damage to apply

        Returns:
            int: Remaining health after damage (minimum 0)
        """
        state = self._sessions.get(session_id)
        if state:
            state.health_current = max(0, state.health_current - damage)
            return state.health_current
        return 0

    def set_character_description(self, session_id: str, description: str) -> None:
        """Set character description for personalization.

        Args:
            session_id: Session identifier
            description: Character description text
        """
        state = self._sessions.get(session_id)
        if state:
            state.character_description = description

    def set_choices(self, session_id: str, choices: list[str]) -> None:
        """Set current choices for the session.

        Args:
            session_id: Session identifier
            choices: List of available choice texts
        """
        state = self._sessions.get(session_id)
        if state:
            state.current_choices = choices

    def update_recent_agents(self, session_id: str, agents: list[str]) -> None:
        """Update recent agents list, keeping last 5.

        Args:
            session_id: Session identifier
            agents: List of agent names used in current turn
        """
        state = self._sessions.get(session_id)
        if state:
            state.recent_agents.extend(agents)
            # Keep only the last 5 agents for cooldown tracking
            if len(state.recent_agents) > 5:
                state.recent_agents = state.recent_agents[-5:]
            # Track Jester appearances
            if "jester" in agents:
                state.turns_since_jester = 0
            else:
                state.turns_since_jester += 1

    def set_character_sheet(self, session_id: str, sheet: CharacterSheet) -> None:
        """Set the character sheet for a session.

        Args:
            session_id: Session identifier
            sheet: CharacterSheet instance to store
        """
        state = self._sessions.get(session_id)
        if state:
            state.character_sheet = sheet

    def get_character_sheet(self, session_id: str) -> CharacterSheet | None:
        """Get the character sheet for a session.

        Args:
            session_id: Session identifier

        Returns:
            CharacterSheet if set, None otherwise
        """
        state = self._sessions.get(session_id)
        if state:
            return state.character_sheet
        return None

    def set_phase(self, session_id: str, phase: GamePhase) -> None:
        """Set the game phase for a session.

        Args:
            session_id: Session identifier
            phase: GamePhase value to set
        """
        state = self._sessions.get(session_id)
        if state:
            state.phase = phase

    def get_phase(self, session_id: str) -> GamePhase | None:
        """Get the current game phase for a session.

        Args:
            session_id: Session identifier

        Returns:
            GamePhase if session exists, None otherwise
        """
        state = self._sessions.get(session_id)
        if state:
            return state.phase
        return None
