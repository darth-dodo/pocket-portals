"""Game session service providing async API for FastAPI routes.

Simple service layer wrapping GameSessionFlow. State is auto-persisted
via @persist decorator on GameSessionFlow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from crewai.flow.flow import Flow

from src.engine.game_session import GameSessionFlow, _persistence
from src.state.models import (
    AdventureMoment,
    AdventurePhase,
    CombatState,
    GamePhase,
    GameState,
    Quest,
)

if TYPE_CHECKING:
    from src.state.character import CharacterSheet


class GameSessionService:
    """Async API for game session operations.

    Usage:
        state = await GameSessionService.create_session()
        state = await GameSessionService.get_session(session_id)
        await GameSessionService.set_phase(session_id, GamePhase.EXPLORATION)
    """

    @staticmethod
    async def create_session() -> GameState:
        """Create a new game session."""
        flow = GameSessionFlow()
        await flow.kickoff_async()
        return flow.state

    @staticmethod
    async def get_session(session_id: str) -> GameState | None:
        """Get existing session by ID."""
        state_dict = _persistence.load_state(session_id)
        if state_dict is None:
            return None
        return GameState(**state_dict)

    @staticmethod
    async def get_or_create_session(session_id: str | None) -> GameState:
        """Get existing session or create new one."""
        if session_id:
            state = await GameSessionService.get_session(session_id)
            if state:
                return state
        return await GameSessionService.create_session()

    @staticmethod
    async def _get_flow(session_id: str) -> GameSessionFlow:
        """Get flow for existing session, loading state from persistence."""
        state_dict = _persistence.load_state(session_id)
        if state_dict:
            # Reconstruct flow with existing state (no kickoff needed)
            state = GameState(**state_dict)
            flow = GameSessionFlow.__new__(GameSessionFlow)
            flow.initial_state = state
            # Initialize parent Flow class properly
            Flow.__init__(flow)
            return flow
        else:
            # New session - create and kickoff
            flow = GameSessionFlow(session_id=session_id)
            await flow.kickoff_async()
            return flow

    # =========================================================================
    # Conversation Operations
    # =========================================================================

    @staticmethod
    async def add_exchange(session_id: str, action: str, narrative: str) -> None:
        """Add conversation exchange."""
        flow = await GameSessionService._get_flow(session_id)
        flow.add_exchange(action, narrative)

    @staticmethod
    async def set_choices(session_id: str, choices: list[str]) -> None:
        """Set current choices."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_choices(choices)

    # =========================================================================
    # Character Operations
    # =========================================================================

    @staticmethod
    async def set_character_description(session_id: str, description: str) -> None:
        """Set character description."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_character_description(description)

    @staticmethod
    async def set_character_sheet(session_id: str, sheet: CharacterSheet) -> None:
        """Set character sheet."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_character_sheet(sheet)

    @staticmethod
    async def get_character_sheet(session_id: str) -> CharacterSheet | None:
        """Get character sheet."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.get_character_sheet()

    @staticmethod
    async def set_creation_turn(session_id: str, turn: int) -> None:
        """Set creation turn number."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_creation_turn(turn)

    @staticmethod
    async def increment_creation_turn(session_id: str) -> int:
        """Increment creation turn and return new value."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.increment_creation_turn()

    @staticmethod
    async def get_creation_turn(session_id: str) -> int:
        """Get current creation turn."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.get_creation_turn()

    # =========================================================================
    # Phase Management
    # =========================================================================

    @staticmethod
    async def set_phase(session_id: str, phase: GamePhase) -> None:
        """Set game phase."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_phase(phase)

    @staticmethod
    async def get_phase(session_id: str) -> GamePhase | None:
        """Get current game phase."""
        state = await GameSessionService.get_session(session_id)
        return state.phase if state else None

    @staticmethod
    async def update_game_phase(session_id: str, phase: GamePhase) -> None:
        """Update game phase (alias for set_phase)."""
        await GameSessionService.set_phase(session_id, phase)

    # =========================================================================
    # Health & Combat Operations
    # =========================================================================

    @staticmethod
    async def update_health(session_id: str, damage: int) -> int:
        """Apply damage and return remaining health."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.update_health(damage)

    @staticmethod
    async def set_combat_state(
        session_id: str, combat_state: CombatState | None
    ) -> None:
        """Set combat state."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_combat_state(combat_state)

    # =========================================================================
    # Quest Operations
    # =========================================================================

    @staticmethod
    async def set_active_quest(session_id: str, quest: Quest | None) -> None:
        """Set active quest."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_active_quest(quest)

    @staticmethod
    async def get_active_quest(session_id: str) -> Quest | None:
        """Get active quest."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.get_active_quest()

    @staticmethod
    async def complete_quest(session_id: str) -> None:
        """Complete the active quest."""
        flow = await GameSessionService._get_flow(session_id)
        flow.complete_quest()

    @staticmethod
    async def update_quest_objective(
        session_id: str, objective_id: str, completed: bool = True
    ) -> None:
        """Update quest objective completion status."""
        flow = await GameSessionService._get_flow(session_id)
        flow.update_quest_objective(objective_id, completed)

    @staticmethod
    async def set_pending_quest_options(session_id: str, quests: list[Quest]) -> None:
        """Set pending quest options."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_pending_quest_options(quests)

    @staticmethod
    async def clear_pending_quest_options(session_id: str) -> None:
        """Clear pending quest options."""
        flow = await GameSessionService._get_flow(session_id)
        flow.clear_pending_quest_options()

    # =========================================================================
    # Adventure Pacing Operations
    # =========================================================================

    @staticmethod
    async def increment_adventure_turn(session_id: str) -> int:
        """Increment adventure turn and return new value."""
        flow = await GameSessionService._get_flow(session_id)
        return flow.increment_adventure_turn()

    @staticmethod
    async def set_adventure_phase(session_id: str, phase: AdventurePhase) -> None:
        """Set adventure phase."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_adventure_phase(phase)

    @staticmethod
    async def set_adventure_completed(session_id: str, completed: bool) -> None:
        """Set adventure completion status."""
        flow = await GameSessionService._get_flow(session_id)
        flow.set_adventure_completed(completed)

    @staticmethod
    async def add_adventure_moment(session_id: str, moment: AdventureMoment) -> None:
        """Add adventure moment."""
        flow = await GameSessionService._get_flow(session_id)
        flow.add_adventure_moment(moment)

    @staticmethod
    async def trigger_epilogue(session_id: str, reason: str) -> GameState | None:
        """Trigger adventure epilogue."""
        state = await GameSessionService.get_session(session_id)
        if state is None:
            return None
        flow = await GameSessionService._get_flow(session_id)
        return flow.trigger_epilogue(reason)

    # =========================================================================
    # Agent Tracking Operations
    # =========================================================================

    @staticmethod
    async def update_recent_agents(session_id: str, agents: list[str]) -> None:
        """Update recent agents list."""
        flow = await GameSessionService._get_flow(session_id)
        flow.update_recent_agents(agents)

    # =========================================================================
    # Testing Utilities
    # =========================================================================

    @staticmethod
    def _reset_persistence() -> None:
        """Reset persistence storage (for testing only)."""
        _persistence.clear()
