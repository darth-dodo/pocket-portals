"""Tests for GameSessionFlow class."""

import pytest

from src.engine.game_session import GameSessionFlow, _persistence
from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import (
    AdventureMoment,
    AdventurePhase,
    CombatState,
    GamePhase,
    Quest,
    QuestObjective,
    QuestStatus,
)


@pytest.fixture(autouse=True)
def reset_persistence() -> None:
    """Reset persistence before each test."""
    _persistence.clear()


@pytest.fixture
def flow() -> GameSessionFlow:
    """Create GameSessionFlow for tests."""
    flow = GameSessionFlow()
    flow.kickoff()
    return flow


class TestSessionCreation:
    """Test session creation and ID generation."""

    def test_creates_session_with_id(self) -> None:
        flow = GameSessionFlow()
        flow.kickoff()
        assert flow.state.session_id != ""
        assert len(flow.state.session_id) == 36  # UUID format

    def test_multiple_sessions_unique_ids(self) -> None:
        flow1 = GameSessionFlow()
        flow1.kickoff()
        flow2 = GameSessionFlow()
        flow2.kickoff()
        assert flow1.state.session_id != flow2.state.session_id

    def test_new_session_has_defaults(self) -> None:
        flow = GameSessionFlow()
        flow.kickoff()
        assert flow.state.phase == GamePhase.CHARACTER_CREATION
        assert flow.state.health_current == 20
        assert flow.state.creation_turn == 0


class TestPhaseManagement:
    """Test phase management."""

    def test_set_phase(self, flow: GameSessionFlow) -> None:
        flow.set_phase(GamePhase.EXPLORATION)
        assert flow.state.phase == GamePhase.EXPLORATION

    def test_get_phase(self, flow: GameSessionFlow) -> None:
        assert flow.get_phase() == GamePhase.CHARACTER_CREATION
        flow.set_phase(GamePhase.COMBAT)
        assert flow.get_phase() == GamePhase.COMBAT


class TestCharacterOperations:
    """Test character operations."""

    def test_set_character_sheet(self, flow: GameSessionFlow) -> None:
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        flow.set_character_sheet(sheet)
        assert flow.state.character_sheet is not None
        assert flow.state.character_sheet.name == "Thorin"

    def test_get_character_sheet(self, flow: GameSessionFlow) -> None:
        assert flow.get_character_sheet() is None
        sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
        )
        flow.set_character_sheet(sheet)
        result = flow.get_character_sheet()
        assert result is not None
        assert result.name == "Elara"

    def test_set_character_description(self, flow: GameSessionFlow) -> None:
        flow.set_character_description("A brave warrior")
        assert flow.state.character_description == "A brave warrior"


class TestCreationTurns:
    """Test creation turn management."""

    def test_set_creation_turn(self, flow: GameSessionFlow) -> None:
        flow.set_creation_turn(3)
        assert flow.state.creation_turn == 3

    def test_creation_turn_caps_at_5(self, flow: GameSessionFlow) -> None:
        flow.set_creation_turn(10)
        assert flow.state.creation_turn == 5

    def test_increment_creation_turn(self, flow: GameSessionFlow) -> None:
        assert flow.increment_creation_turn() == 1
        assert flow.increment_creation_turn() == 2

    def test_increment_caps_at_5(self, flow: GameSessionFlow) -> None:
        flow.set_creation_turn(4)
        assert flow.increment_creation_turn() == 5
        assert flow.increment_creation_turn() == 5


class TestQuestOperations:
    """Test quest operations."""

    def test_set_active_quest(self, flow: GameSessionFlow) -> None:
        quest = Quest(
            id="quest-1",
            title="The Lost Artifact",
            description="Find it.",
            objectives=[QuestObjective(id="obj-1", description="Enter dungeon")],
            status=QuestStatus.ACTIVE,
        )
        flow.set_active_quest(quest)
        assert flow.state.active_quest is not None
        assert flow.state.active_quest.title == "The Lost Artifact"

    def test_complete_quest(self, flow: GameSessionFlow) -> None:
        quest = Quest(
            id="quest-1",
            title="Slay Dragon",
            description="Defeat it.",
            objectives=[],
            status=QuestStatus.ACTIVE,
        )
        flow.set_active_quest(quest)
        flow.complete_quest()
        assert flow.state.active_quest is None
        assert len(flow.state.completed_quests) == 1
        assert flow.state.completed_quests[0].status == QuestStatus.COMPLETED

    def test_update_quest_objective(self, flow: GameSessionFlow) -> None:
        quest = Quest(
            id="quest-1",
            title="Test",
            description="Test.",
            objectives=[
                QuestObjective(id="obj-1", description="Task 1", is_completed=False),
                QuestObjective(id="obj-2", description="Task 2", is_completed=False),
            ],
            status=QuestStatus.ACTIVE,
        )
        flow.set_active_quest(quest)
        flow.update_quest_objective("obj-1", completed=True)
        assert flow.state.active_quest.objectives[0].is_completed is True
        assert flow.state.active_quest.objectives[1].is_completed is False


class TestAdventurePacing:
    """Test adventure pacing."""

    def test_increment_adventure_turn(self, flow: GameSessionFlow) -> None:
        assert flow.increment_adventure_turn() == 1
        assert flow.state.adventure_turn == 1

    def test_adventure_phase_transitions(self, flow: GameSessionFlow) -> None:
        # SETUP: turns 1-5
        for _ in range(5):
            flow.increment_adventure_turn()
        assert flow.state.adventure_phase == AdventurePhase.SETUP

        # RISING_ACTION: turns 6-20
        flow.increment_adventure_turn()
        assert flow.state.adventure_phase == AdventurePhase.RISING_ACTION

    def test_trigger_epilogue(self, flow: GameSessionFlow) -> None:
        flow.trigger_epilogue("Victory")
        assert flow.state.adventure_completed is True
        assert flow.state.adventure_phase == AdventurePhase.DENOUEMENT


class TestAdventureMoments:
    """Test adventure moment management."""

    def test_add_adventure_moment(self, flow: GameSessionFlow) -> None:
        moment = AdventureMoment(
            turn=5,
            type="combat_victory",
            summary="Defeated goblin",
            significance=0.8,
        )
        flow.add_adventure_moment(moment)
        assert len(flow.state.adventure_moments) == 1

    def test_caps_at_max_moments(self, flow: GameSessionFlow) -> None:
        from src.engine.game_session import MAX_ADVENTURE_MOMENTS

        for i in range(MAX_ADVENTURE_MOMENTS + 5):
            moment = AdventureMoment(
                turn=i,
                type="discovery",
                summary=f"Moment {i}",
                significance=0.5,
            )
            flow.add_adventure_moment(moment)
        assert len(flow.state.adventure_moments) == MAX_ADVENTURE_MOMENTS


class TestCombatAndHealth:
    """Test combat and health management."""

    def test_update_health(self, flow: GameSessionFlow) -> None:
        assert flow.update_health(5) == 15
        assert flow.state.health_current == 15

    def test_health_cannot_go_below_0(self, flow: GameSessionFlow) -> None:
        assert flow.update_health(150) == 0

    def test_set_combat_state(self, flow: GameSessionFlow) -> None:
        combat = CombatState(is_active=True, round_number=1)
        flow.set_combat_state(combat)
        assert flow.state.combat_state is not None
        assert flow.state.combat_state.is_active is True


class TestConversationHistory:
    """Test conversation history management."""

    def test_add_exchange(self, flow: GameSessionFlow) -> None:
        flow.add_exchange("explore cave", "You enter a dark cave...")
        assert len(flow.state.conversation_history) == 1
        assert flow.state.conversation_history[0]["action"] == "explore cave"

    def test_history_limit(self, flow: GameSessionFlow) -> None:
        for i in range(25):
            flow.add_exchange(f"action-{i}", f"narrative-{i}")
        assert len(flow.state.conversation_history) == 20
        assert flow.state.conversation_history[0]["action"] == "action-5"


class TestAgentTracking:
    """Test agent tracking."""

    def test_update_recent_agents(self, flow: GameSessionFlow) -> None:
        flow.update_recent_agents(["narrator"])
        assert "narrator" in flow.state.recent_agents

    def test_tracks_jester(self, flow: GameSessionFlow) -> None:
        flow.update_recent_agents(["narrator"])
        assert flow.state.turns_since_jester == 1
        flow.update_recent_agents(["jester"])
        assert flow.state.turns_since_jester == 0


class TestPersistence:
    """Test automatic persistence via @persist decorator."""

    def test_state_persists_after_method(self) -> None:
        flow = GameSessionFlow()
        flow.kickoff()
        session_id = flow.state.session_id

        flow.set_phase(GamePhase.EXPLORATION)

        # Load from persistence
        state_dict = _persistence.load_state(session_id)
        assert state_dict is not None
        assert state_dict["phase"] == GamePhase.EXPLORATION.value

    def test_state_persists_across_operations(self) -> None:
        flow = GameSessionFlow()
        flow.kickoff()
        session_id = flow.state.session_id

        flow.set_phase(GamePhase.COMBAT)
        flow.update_health(10)
        flow.add_exchange("attack", "You strike!")

        state_dict = _persistence.load_state(session_id)
        assert state_dict is not None
        assert state_dict["phase"] == GamePhase.COMBAT.value
        assert state_dict["health_current"] == 10
        assert len(state_dict["conversation_history"]) == 1
