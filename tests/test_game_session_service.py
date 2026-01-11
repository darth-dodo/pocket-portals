"""Tests for GameSessionService class."""

import pytest

from src.engine.game_session_service import GameSessionService
from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import (
    AdventurePhase,
    CombatState,
    GamePhase,
    GameState,
    Quest,
    QuestStatus,
)


@pytest.fixture(autouse=True)
def reset_persistence() -> None:
    """Reset persistence before each test."""
    GameSessionService._reset_persistence()


class TestCreateSession:
    """Test session creation."""

    @pytest.mark.asyncio
    async def test_creates_game_state(self) -> None:
        state = await GameSessionService.create_session()
        assert isinstance(state, GameState)

    @pytest.mark.asyncio
    async def test_generates_unique_id(self) -> None:
        state = await GameSessionService.create_session()
        assert len(state.session_id) == 36

    @pytest.mark.asyncio
    async def test_has_default_phase(self) -> None:
        state = await GameSessionService.create_session()
        assert state.phase == GamePhase.CHARACTER_CREATION

    @pytest.mark.asyncio
    async def test_multiple_sessions_unique(self) -> None:
        state1 = await GameSessionService.create_session()
        state2 = await GameSessionService.create_session()
        assert state1.session_id != state2.session_id


class TestGetSession:
    """Test session retrieval."""

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown(self) -> None:
        state = await GameSessionService.get_session("nonexistent")
        assert state is None

    @pytest.mark.asyncio
    async def test_returns_existing_session(self) -> None:
        created = await GameSessionService.create_session()
        retrieved = await GameSessionService.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    @pytest.mark.asyncio
    async def test_returns_updated_state(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.set_phase(state.session_id, GamePhase.EXPLORATION)
        retrieved = await GameSessionService.get_session(state.session_id)
        assert retrieved is not None
        assert retrieved.phase == GamePhase.EXPLORATION


class TestGetOrCreateSession:
    """Test get or create logic."""

    @pytest.mark.asyncio
    async def test_creates_if_none(self) -> None:
        state = await GameSessionService.get_or_create_session(None)
        assert isinstance(state, GameState)

    @pytest.mark.asyncio
    async def test_returns_existing(self) -> None:
        created = await GameSessionService.create_session()
        retrieved = await GameSessionService.get_or_create_session(created.session_id)
        assert retrieved.session_id == created.session_id

    @pytest.mark.asyncio
    async def test_creates_if_not_found(self) -> None:
        state = await GameSessionService.get_or_create_session("nonexistent")
        assert state.session_id != "nonexistent"


class TestPhaseManagement:
    """Test phase management."""

    @pytest.mark.asyncio
    async def test_set_phase(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.set_phase(state.session_id, GamePhase.EXPLORATION)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.phase == GamePhase.EXPLORATION

    @pytest.mark.asyncio
    async def test_get_phase(self) -> None:
        state = await GameSessionService.create_session()
        phase = await GameSessionService.get_phase(state.session_id)
        assert phase == GamePhase.CHARACTER_CREATION


class TestCharacterOperations:
    """Test character operations."""

    @pytest.mark.asyncio
    async def test_set_character_sheet(self) -> None:
        state = await GameSessionService.create_session()
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        await GameSessionService.set_character_sheet(state.session_id, sheet)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.character_sheet is not None

    @pytest.mark.asyncio
    async def test_set_character_description(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.set_character_description(state.session_id, "A hero")
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.character_description == "A hero"


class TestCreationTurns:
    """Test creation turn management."""

    @pytest.mark.asyncio
    async def test_set_creation_turn(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.set_creation_turn(state.session_id, 3)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.creation_turn == 3

    @pytest.mark.asyncio
    async def test_increment_creation_turn(self) -> None:
        state = await GameSessionService.create_session()
        result = await GameSessionService.increment_creation_turn(state.session_id)
        assert result == 1


class TestQuestOperations:
    """Test quest operations."""

    @pytest.mark.asyncio
    async def test_set_active_quest(self) -> None:
        state = await GameSessionService.create_session()
        quest = Quest(
            id="quest-1",
            title="Test Quest",
            description="Test.",
            objectives=[],
            status=QuestStatus.ACTIVE,
        )
        await GameSessionService.set_active_quest(state.session_id, quest)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.active_quest is not None

    @pytest.mark.asyncio
    async def test_complete_quest(self) -> None:
        state = await GameSessionService.create_session()
        quest = Quest(
            id="quest-1",
            title="Test",
            description="Test.",
            objectives=[],
            status=QuestStatus.ACTIVE,
        )
        await GameSessionService.set_active_quest(state.session_id, quest)
        await GameSessionService.complete_quest(state.session_id)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.active_quest is None
        assert len(loaded.completed_quests) == 1


class TestConversationHistory:
    """Test conversation history."""

    @pytest.mark.asyncio
    async def test_add_exchange(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.add_exchange(state.session_id, "look", "You see...")
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert len(loaded.conversation_history) == 1


class TestHealthAndCombat:
    """Test health and combat."""

    @pytest.mark.asyncio
    async def test_update_health(self) -> None:
        state = await GameSessionService.create_session()
        remaining = await GameSessionService.update_health(state.session_id, 5)
        assert remaining == 15

    @pytest.mark.asyncio
    async def test_set_combat_state(self) -> None:
        state = await GameSessionService.create_session()
        combat = CombatState(is_active=True)
        await GameSessionService.set_combat_state(state.session_id, combat)
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.combat_state is not None


class TestAdventurePacing:
    """Test adventure pacing."""

    @pytest.mark.asyncio
    async def test_increment_adventure_turn(self) -> None:
        state = await GameSessionService.create_session()
        result = await GameSessionService.increment_adventure_turn(state.session_id)
        assert result == 1

    @pytest.mark.asyncio
    async def test_set_adventure_phase(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.set_adventure_phase(
            state.session_id, AdventurePhase.CLIMAX
        )
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert loaded.adventure_phase == AdventurePhase.CLIMAX


class TestAgentTracking:
    """Test agent tracking."""

    @pytest.mark.asyncio
    async def test_update_recent_agents(self) -> None:
        state = await GameSessionService.create_session()
        await GameSessionService.update_recent_agents(state.session_id, ["narrator"])
        loaded = await GameSessionService.get_session(state.session_id)
        assert loaded is not None
        assert "narrator" in loaded.recent_agents


class TestStatePersistence:
    """Test state persistence across operations."""

    @pytest.mark.asyncio
    async def test_multiple_operations_persist(self) -> None:
        state = await GameSessionService.create_session()
        sid = state.session_id

        await GameSessionService.set_phase(sid, GamePhase.EXPLORATION)
        await GameSessionService.set_character_description(sid, "A hero")
        await GameSessionService.add_exchange(sid, "look", "You see...")
        await GameSessionService.update_health(sid, 5)

        loaded = await GameSessionService.get_session(sid)
        assert loaded is not None
        assert loaded.phase == GamePhase.EXPLORATION
        assert loaded.character_description == "A hero"
        assert len(loaded.conversation_history) == 1
        assert loaded.health_current == 15

    @pytest.mark.asyncio
    async def test_session_isolation(self) -> None:
        state1 = await GameSessionService.create_session()
        state2 = await GameSessionService.create_session()

        await GameSessionService.set_phase(state1.session_id, GamePhase.COMBAT)
        await GameSessionService.set_phase(state2.session_id, GamePhase.EXPLORATION)

        loaded1 = await GameSessionService.get_session(state1.session_id)
        loaded2 = await GameSessionService.get_session(state2.session_id)

        assert loaded1 is not None
        assert loaded2 is not None
        assert loaded1.phase == GamePhase.COMBAT
        assert loaded2.phase == GamePhase.EXPLORATION
