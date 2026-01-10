"""Game session management using CrewAI Flow."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from crewai.flow.flow import Flow, start

from src.engine.flow_persistence import InMemoryFlowPersistence
from src.state.models import (
    AdventureMoment,
    AdventurePhase,
    CombatState,
    GamePhase,
    GameState,
    Quest,
    QuestStatus,
)

if TYPE_CHECKING:
    from src.state.character import CharacterSheet

MAX_ADVENTURE_MOMENTS = 15
MAX_CONVERSATION_HISTORY = 20
MAX_CREATION_TURNS = 5
MAX_RECENT_AGENTS = 5

# Shared persistence instance
_persistence = InMemoryFlowPersistence()


class GameSessionFlow(Flow[GameState]):
    """Game session state management with automatic persistence."""

    def __init__(self, session_id: str | None = None, **kwargs: Any) -> None:
        self.initial_state = GameState(session_id=session_id or str(uuid.uuid4()))
        super().__init__(**kwargs)

    def _save(self) -> None:
        """Save state to persistence."""
        _persistence.save_state(self.state.session_id, "update", self.state)

    @start()
    def initialize(self) -> GameState:
        """Initialize and persist state."""
        self._save()
        return self.state

    # Session Operations

    def get_session_id(self) -> str:
        return self.state.session_id

    def add_exchange(self, action: str, narrative: str) -> None:
        self.state.conversation_history.append(
            {"action": action, "narrative": narrative}
        )
        if len(self.state.conversation_history) > MAX_CONVERSATION_HISTORY:
            self.state.conversation_history = self.state.conversation_history[
                -MAX_CONVERSATION_HISTORY:
            ]
        self._save()

    def set_choices(self, choices: list[str]) -> None:
        self.state.current_choices = choices
        self._save()

    def get_choices(self) -> list[str]:
        return self.state.current_choices

    # Character Operations

    def set_character_description(self, description: str) -> None:
        self.state.character_description = description
        self._save()

    def get_character_description(self) -> str:
        return self.state.character_description

    def set_character_sheet(self, sheet: CharacterSheet) -> None:
        self.state.character_sheet = sheet
        self._save()

    def get_character_sheet(self) -> CharacterSheet | None:
        sheet = self.state.character_sheet
        if sheet is None:
            return None
        from src.state.character import CharacterSheet as CS

        return sheet if isinstance(sheet, CS) else None

    def set_creation_turn(self, turn: int) -> None:
        self.state.creation_turn = min(MAX_CREATION_TURNS, max(0, turn))
        self._save()

    def get_creation_turn(self) -> int:
        return self.state.creation_turn

    def increment_creation_turn(self) -> int:
        self.state.creation_turn = min(MAX_CREATION_TURNS, self.state.creation_turn + 1)
        self._save()
        return self.state.creation_turn

    # Phase Management

    def set_phase(self, phase: GamePhase) -> None:
        self.state.phase = phase
        self._save()

    def get_phase(self) -> GamePhase:
        return self.state.phase

    def update_game_phase(self, phase: GamePhase) -> None:
        self.set_phase(phase)

    # Health & Combat

    def update_health(self, damage: int) -> int:
        self.state.health_current = max(0, self.state.health_current - damage)
        self._save()
        return self.state.health_current

    def get_health(self) -> tuple[int, int]:
        return (self.state.health_current, self.state.health_max)

    def set_combat_state(self, combat_state: CombatState | None) -> None:
        self.state.combat_state = combat_state
        self._save()

    def get_combat_state(self) -> CombatState | None:
        return self.state.combat_state

    def is_in_combat(self) -> bool:
        return self.state.combat_state is not None and self.state.combat_state.is_active

    # Quest Operations

    def set_active_quest(self, quest: Quest | None) -> None:
        self.state.active_quest = quest
        self._save()

    def get_active_quest(self) -> Quest | None:
        return self.state.active_quest

    def complete_quest(self) -> None:
        if self.state.active_quest:
            self.state.active_quest.status = QuestStatus.COMPLETED
            self.state.completed_quests.append(self.state.active_quest)
            self.state.active_quest = None
            self._save()

    def update_quest_objective(self, objective_id: str, completed: bool = True) -> bool:
        if self.state.active_quest:
            for obj in self.state.active_quest.objectives:
                if obj.id == objective_id:
                    obj.is_completed = completed
                    self._save()
                    return True
        return False

    def set_pending_quest_options(self, quests: list[Quest]) -> None:
        self.state.pending_quest_options = quests
        self._save()

    def get_pending_quest_options(self) -> list[Quest]:
        return self.state.pending_quest_options

    def clear_pending_quest_options(self) -> None:
        self.state.pending_quest_options = []
        self._save()

    def get_completed_quests(self) -> list[Quest]:
        return self.state.completed_quests

    # Adventure Pacing

    def increment_adventure_turn(self) -> int:
        self.state.adventure_turn = min(
            self.state.max_turns, self.state.adventure_turn + 1
        )
        self.state.adventure_phase = self._calculate_turn_based_phase(
            self.state.adventure_turn
        )
        self._save()
        return self.state.adventure_turn

    def get_adventure_turn(self) -> int:
        return self.state.adventure_turn

    def _calculate_turn_based_phase(self, turn: int) -> AdventurePhase:
        if turn <= 5:
            return AdventurePhase.SETUP
        elif turn <= 20:
            return AdventurePhase.RISING_ACTION
        elif turn <= 30:
            return AdventurePhase.MID_POINT
        elif turn <= 42:
            return AdventurePhase.CLIMAX
        return AdventurePhase.DENOUEMENT

    def set_adventure_phase(self, phase: AdventurePhase) -> None:
        self.state.adventure_phase = phase
        self._save()

    def get_adventure_phase(self) -> AdventurePhase:
        return self.state.adventure_phase

    def set_adventure_completed(self, completed: bool) -> None:
        self.state.adventure_completed = completed
        self._save()

    def is_adventure_completed(self) -> bool:
        return self.state.adventure_completed

    def add_adventure_moment(self, moment: AdventureMoment) -> None:
        self.state.adventure_moments.append(moment)
        if len(self.state.adventure_moments) > MAX_ADVENTURE_MOMENTS:
            self.state.adventure_moments.sort(
                key=lambda m: m.significance, reverse=True
            )
            self.state.adventure_moments = self.state.adventure_moments[
                :MAX_ADVENTURE_MOMENTS
            ]
        self._save()

    def get_adventure_moments(self) -> list[AdventureMoment]:
        return self.state.adventure_moments

    def trigger_epilogue(self, reason: str) -> GameState:
        self.state.adventure_completed = True
        self.state.adventure_phase = AdventurePhase.DENOUEMENT
        self._save()
        return self.state

    def set_climax_reached(self, reached: bool) -> None:
        self.state.climax_reached = reached
        self._save()

    def is_climax_reached(self) -> bool:
        return self.state.climax_reached

    # Agent Tracking

    def update_recent_agents(self, agents: list[str]) -> None:
        self.state.recent_agents.extend(agents)
        if len(self.state.recent_agents) > MAX_RECENT_AGENTS:
            self.state.recent_agents = self.state.recent_agents[-MAX_RECENT_AGENTS:]
        if "jester" in agents:
            self.state.turns_since_jester = 0
        else:
            self.state.turns_since_jester += 1
        self._save()

    def get_recent_agents(self) -> list[str]:
        return self.state.recent_agents

    def get_turns_since_jester(self) -> int:
        return self.state.turns_since_jester

    # State Access

    def get_state(self) -> GameState:
        return self.state

    def has_character(self) -> bool:
        return self.state.character_sheet is not None
