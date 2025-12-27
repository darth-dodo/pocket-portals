"""Session manager for game state persistence."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.state.backends.base import SessionBackend
from src.state.models import CombatState, GamePhase, GameState, Quest, QuestStatus

if TYPE_CHECKING:
    from src.state.character import CharacterSheet


class SessionManager:
    """Manages game sessions using a pluggable async backend."""

    def __init__(self, backend: SessionBackend) -> None:
        """Initialize session manager with a storage backend.

        Args:
            backend: SessionBackend implementation for state persistence
        """
        self._backend = backend

    async def create_session(self) -> GameState:
        """Create a new session with default state.

        Returns:
            GameState: New game state with unique session ID
        """
        session_id = str(uuid.uuid4())
        state = GameState(session_id=session_id)
        await self._backend.create(session_id, state)
        return state

    async def get_session(self, session_id: str) -> GameState | None:
        """Get existing session or None.

        Args:
            session_id: Session identifier

        Returns:
            GameState if session exists, None otherwise
        """
        return await self._backend.get(session_id)

    async def get_or_create_session(self, session_id: str | None) -> GameState:
        """Get existing session or create new one.

        Args:
            session_id: Optional session identifier

        Returns:
            GameState: Existing or newly created game state
        """
        if session_id:
            existing = await self._backend.get(session_id)
            if existing:
                return existing
        return await self.create_session()

    async def add_exchange(self, session_id: str, action: str, narrative: str) -> None:
        """Add conversation exchange, maintaining history limit of 20.

        Args:
            session_id: Session identifier
            action: Player action text
            narrative: Game narrative response
        """
        state = await self._backend.get(session_id)
        if state:
            state.conversation_history.append(
                {"action": action, "narrative": narrative}
            )
            if len(state.conversation_history) > 20:
                state.conversation_history = state.conversation_history[-20:]
            await self._backend.update(session_id, state)

    async def update_health(self, session_id: str, damage: int) -> int:
        """Apply damage and return remaining health.

        Args:
            session_id: Session identifier
            damage: Amount of damage to apply

        Returns:
            int: Remaining health after damage (minimum 0)
        """
        state = await self._backend.get(session_id)
        if state:
            state.health_current = max(0, state.health_current - damage)
            await self._backend.update(session_id, state)
            return state.health_current
        return 0

    async def set_character_description(
        self, session_id: str, description: str
    ) -> None:
        """Set character description for personalization.

        Args:
            session_id: Session identifier
            description: Character description text
        """
        state = await self._backend.get(session_id)
        if state:
            state.character_description = description
            await self._backend.update(session_id, state)

    async def set_choices(self, session_id: str, choices: list[str]) -> None:
        """Set current choices for the session.

        Args:
            session_id: Session identifier
            choices: List of available choice texts
        """
        state = await self._backend.get(session_id)
        if state:
            state.current_choices = choices
            await self._backend.update(session_id, state)

    async def update_recent_agents(self, session_id: str, agents: list[str]) -> None:
        """Update recent agents list, keeping last 5.

        Args:
            session_id: Session identifier
            agents: List of agent names used in current turn
        """
        state = await self._backend.get(session_id)
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
            await self._backend.update(session_id, state)

    async def set_character_sheet(self, session_id: str, sheet: CharacterSheet) -> None:
        """Set the character sheet for a session.

        Args:
            session_id: Session identifier
            sheet: CharacterSheet instance to store
        """
        state = await self._backend.get(session_id)
        if state:
            state.character_sheet = sheet
            await self._backend.update(session_id, state)

    async def get_character_sheet(self, session_id: str) -> CharacterSheet | None:
        """Get the character sheet for a session.

        Args:
            session_id: Session identifier

        Returns:
            CharacterSheet if set, None otherwise
        """
        state = await self._backend.get(session_id)
        if state:
            return state.character_sheet
        return None

    async def set_phase(self, session_id: str, phase: GamePhase) -> None:
        """Set the game phase for a session.

        Args:
            session_id: Session identifier
            phase: GamePhase value to set
        """
        state = await self._backend.get(session_id)
        if state:
            state.phase = phase
            await self._backend.update(session_id, state)

    async def get_phase(self, session_id: str) -> GamePhase | None:
        """Get the current game phase for a session.

        Args:
            session_id: Session identifier

        Returns:
            GamePhase if session exists, None otherwise
        """
        state = await self._backend.get(session_id)
        if state:
            return state.phase
        return None

    async def set_creation_turn(self, session_id: str, turn: int) -> None:
        """Set the character creation turn number.

        Args:
            session_id: Session identifier
            turn: Turn number (0-5)
        """
        state = await self._backend.get(session_id)
        if state:
            state.creation_turn = min(5, max(0, turn))
            await self._backend.update(session_id, state)

    async def increment_creation_turn(self, session_id: str) -> int:
        """Increment the character creation turn and return new value.

        Args:
            session_id: Session identifier

        Returns:
            New turn number after incrementing (capped at 5)
        """
        state = await self._backend.get(session_id)
        if state:
            state.creation_turn = min(5, state.creation_turn + 1)
            await self._backend.update(session_id, state)
            return state.creation_turn
        return 0

    async def get_creation_turn(self, session_id: str) -> int:
        """Get the current character creation turn.

        Args:
            session_id: Session identifier

        Returns:
            Current turn number (0 if session doesn't exist)
        """
        state = await self._backend.get(session_id)
        if state:
            return state.creation_turn
        return 0

    async def set_combat_state(
        self, session_id: str, combat_state: CombatState | None
    ) -> None:
        """Set the combat state for a session.

        Args:
            session_id: Session identifier
            combat_state: CombatState instance or None to clear combat
        """
        state = await self._backend.get(session_id)
        if state:
            state.combat_state = combat_state
            await self._backend.update(session_id, state)

    async def set_active_quest(self, session_id: str, quest: Quest | None) -> None:
        """Set the active quest for a session.

        Args:
            session_id: Session identifier
            quest: Quest instance or None to clear active quest
        """
        state = await self._backend.get(session_id)
        if state:
            state.active_quest = quest
            await self._backend.update(session_id, state)

    async def get_active_quest(self, session_id: str) -> Quest | None:
        """Get the active quest for a session.

        Args:
            session_id: Session identifier

        Returns:
            Quest if active, None otherwise
        """
        state = await self._backend.get(session_id)
        if state:
            return state.active_quest
        return None

    async def complete_quest(self, session_id: str) -> None:
        """Complete the active quest and move it to completed quests.

        Args:
            session_id: Session identifier
        """
        state = await self._backend.get(session_id)
        if state and state.active_quest:
            state.active_quest.status = QuestStatus.COMPLETED
            state.completed_quests.append(state.active_quest)
            state.active_quest = None
            await self._backend.update(session_id, state)

    async def update_quest_objective(
        self, session_id: str, objective_id: str, completed: bool = True
    ) -> None:
        """Update quest objective completion status.

        Args:
            session_id: Session identifier
            objective_id: ID of the objective to update
            completed: Whether the objective is completed (default True)
        """
        state = await self._backend.get(session_id)
        if state and state.active_quest:
            for obj in state.active_quest.objectives:
                if obj.id == objective_id:
                    obj.is_completed = completed
                    break
            await self._backend.update(session_id, state)
