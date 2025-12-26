"""Tests for session backends."""

import pytest

from src.state.backends import InMemoryBackend, SessionBackend
from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)
from src.state.models import CombatState, GamePhase, GameState


@pytest.fixture
def backend() -> InMemoryBackend:
    """Provide a fresh InMemoryBackend for each test."""
    return InMemoryBackend()


@pytest.fixture
def sample_state() -> GameState:
    """Provide a sample GameState for testing."""
    return GameState(
        session_id="test-session-123",
        phase=GamePhase.CHARACTER_CREATION,
        health_current=20,
        health_max=20,
    )


class TestInMemoryBackend:
    """Tests for InMemoryBackend."""

    @pytest.mark.asyncio
    async def test_create_and_get(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test creating and retrieving a session."""
        await backend.create("session-1", sample_state)

        result = await backend.get("session-1")

        assert result is not None
        assert result.session_id == sample_state.session_id
        assert result.phase == GamePhase.CHARACTER_CREATION

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, backend: InMemoryBackend) -> None:
        """Test that getting a nonexistent session returns None."""
        result = await backend.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_exists(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test checking session existence."""
        assert await backend.exists("session-1") is False

        await backend.create("session-1", sample_state)

        assert await backend.exists("session-1") is True

    @pytest.mark.asyncio
    async def test_update(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test updating an existing session."""
        await backend.create("session-1", sample_state)

        updated_state = GameState(
            session_id="test-session-123",
            phase=GamePhase.EXPLORATION,
            health_current=15,
            health_max=20,
        )
        await backend.update("session-1", updated_state)

        result = await backend.get("session-1")
        assert result is not None
        assert result.phase == GamePhase.EXPLORATION
        assert result.health_current == 15

    @pytest.mark.asyncio
    async def test_delete_existing(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test deleting an existing session."""
        await backend.create("session-1", sample_state)

        result = await backend.delete("session-1")

        assert result is True
        assert await backend.exists("session-1") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, backend: InMemoryBackend) -> None:
        """Test deleting a nonexistent session returns False."""
        result = await backend.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test clearing all sessions."""
        await backend.create("session-1", sample_state)
        await backend.create("session-2", sample_state)

        assert backend.session_count == 2

        backend.clear()

        assert backend.session_count == 0
        assert await backend.exists("session-1") is False

    @pytest.mark.asyncio
    async def test_session_count(
        self, backend: InMemoryBackend, sample_state: GameState
    ) -> None:
        """Test session count property."""
        assert backend.session_count == 0

        await backend.create("session-1", sample_state)
        assert backend.session_count == 1

        await backend.create("session-2", sample_state)
        assert backend.session_count == 2

        await backend.delete("session-1")
        assert backend.session_count == 1


class TestSessionBackendProtocol:
    """Tests for SessionBackend protocol conformance."""

    def test_inmemory_backend_is_session_backend(self) -> None:
        """InMemoryBackend should be recognized as SessionBackend."""
        backend = InMemoryBackend()
        assert isinstance(backend, SessionBackend)

    def test_protocol_has_required_methods(self) -> None:
        """SessionBackend protocol should define all required methods."""
        # Verify the protocol has all expected method signatures
        assert hasattr(SessionBackend, "create")
        assert hasattr(SessionBackend, "get")
        assert hasattr(SessionBackend, "update")
        assert hasattr(SessionBackend, "delete")
        assert hasattr(SessionBackend, "exists")


class TestGameStateSerialization:
    """Tests for GameState JSON serialization round-trips."""

    def test_basic_state_round_trip(self) -> None:
        """Basic GameState should serialize and deserialize correctly."""
        original = GameState(
            session_id="test-123",
            phase=GamePhase.EXPLORATION,
            health_current=15,
            health_max=20,
        )

        json_str = original.to_json()
        restored = GameState.from_json(json_str)

        assert restored.session_id == original.session_id
        assert restored.phase == original.phase
        assert restored.health_current == original.health_current
        assert restored.health_max == original.health_max

    def test_state_with_character_sheet_round_trip(self) -> None:
        """GameState with CharacterSheet should serialize correctly."""
        sheet = CharacterSheet(
            name="Thorin Oakenshield",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            level=5,
            stats=CharacterStats(
                strength=16,
                dexterity=12,
                constitution=14,
                intelligence=10,
                wisdom=10,
                charisma=8,
            ),
            current_hp=45,
            max_hp=50,
            equipment=["Warhammer", "Shield", "Chain mail"],
            backstory="A warrior from the mountain clans.",
        )
        original = GameState(
            session_id="test-456",
            phase=GamePhase.COMBAT,
            character_sheet=sheet,
            health_current=45,
            health_max=50,
        )

        json_str = original.to_json()
        restored = GameState.from_json(json_str)

        assert restored.character_sheet is not None
        assert restored.character_sheet.name == "Thorin Oakenshield"
        assert restored.character_sheet.race == CharacterRace.DWARF
        assert restored.character_sheet.character_class == CharacterClass.FIGHTER
        assert restored.character_sheet.level == 5
        assert restored.character_sheet.stats.strength == 16
        assert restored.character_sheet.stats.dexterity == 12
        assert len(restored.character_sheet.equipment) == 3

    def test_state_with_conversation_history_round_trip(self) -> None:
        """GameState with conversation history should serialize correctly."""
        original = GameState(
            session_id="test-789",
            conversation_history=[
                {"action": "explore cave", "narrative": "You enter a dark cave..."},
                {"action": "light torch", "narrative": "The torch illuminates..."},
            ],
            current_choices=["Go deeper", "Turn back"],
        )

        json_str = original.to_json()
        restored = GameState.from_json(json_str)

        assert len(restored.conversation_history) == 2
        assert restored.conversation_history[0]["action"] == "explore cave"
        assert (
            restored.conversation_history[1]["narrative"] == "The torch illuminates..."
        )
        assert len(restored.current_choices) == 2
        assert "Go deeper" in restored.current_choices

    def test_state_with_combat_state_round_trip(self) -> None:
        """GameState with CombatState should serialize correctly."""
        combat = CombatState(
            is_active=True,
            round_number=2,
            combat_log=["Initiative rolled", "Player attacks"],
        )
        original = GameState(
            session_id="test-combat",
            phase=GamePhase.COMBAT,
            combat_state=combat,
        )

        json_str = original.to_json()
        restored = GameState.from_json(json_str)

        assert restored.combat_state is not None
        assert restored.combat_state.is_active is True
        assert restored.combat_state.round_number == 2
        assert len(restored.combat_state.combat_log) == 2

    def test_full_state_round_trip(self) -> None:
        """Full GameState with all fields should serialize correctly."""
        sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
        )
        combat = CombatState(is_active=True)
        original = GameState(
            session_id="full-test",
            conversation_history=[{"action": "cast spell", "narrative": "Magic!"}],
            current_choices=["Attack", "Defend", "Flee"],
            character_description="A wise elf wizard",
            character_sheet=sheet,
            health_current=18,
            health_max=20,
            phase=GamePhase.COMBAT,
            creation_turn=3,
            recent_agents=["narrator", "combat_master"],
            turns_since_jester=5,
            combat_state=combat,
        )

        json_str = original.to_json()
        restored = GameState.from_json(json_str)

        # Verify all fields preserved
        assert restored.session_id == original.session_id
        assert len(restored.conversation_history) == 1
        assert len(restored.current_choices) == 3
        assert restored.character_description == "A wise elf wizard"
        assert restored.character_sheet is not None
        assert restored.character_sheet.name == "Elara"
        assert restored.health_current == 18
        assert restored.health_max == 20
        assert restored.phase == GamePhase.COMBAT
        assert restored.creation_turn == 3
        assert len(restored.recent_agents) == 2
        assert restored.turns_since_jester == 5
        assert restored.combat_state is not None
        assert restored.combat_state.is_active is True


class TestBackendWithSerialization:
    """Tests for backend operations with serialized states."""

    @pytest.mark.asyncio
    async def test_backend_preserves_complex_state(self) -> None:
        """Backend should preserve all state data through storage cycle."""
        backend = InMemoryBackend()
        sheet = CharacterSheet(
            name="Test Hero",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.ROGUE,
            stats=CharacterStats(dexterity=18),
        )
        original = GameState(
            session_id="storage-test",
            character_sheet=sheet,
            phase=GamePhase.EXPLORATION,
            conversation_history=[
                {"action": "sneak", "narrative": "You move silently"}
            ],
        )

        await backend.create("session-key", original)
        retrieved = await backend.get("session-key")

        assert retrieved is not None
        assert retrieved.character_sheet is not None
        assert retrieved.character_sheet.name == "Test Hero"
        assert retrieved.character_sheet.stats.dexterity == 18
        assert len(retrieved.conversation_history) == 1

    @pytest.mark.asyncio
    async def test_backend_update_preserves_state(self) -> None:
        """Backend update should preserve all state changes."""
        backend = InMemoryBackend()
        initial = GameState(
            session_id="update-test", phase=GamePhase.CHARACTER_CREATION
        )
        await backend.create("session-key", initial)

        # Create updated state with more data
        sheet = CharacterSheet(
            name="Updated Hero",
            race=CharacterRace.DRAGONBORN,
            character_class=CharacterClass.CLERIC,
        )
        updated = GameState(
            session_id="update-test",
            phase=GamePhase.EXPLORATION,
            character_sheet=sheet,
            health_current=25,
            health_max=30,
        )
        await backend.update("session-key", updated)

        retrieved = await backend.get("session-key")
        assert retrieved is not None
        assert retrieved.phase == GamePhase.EXPLORATION
        assert retrieved.character_sheet is not None
        assert retrieved.character_sheet.name == "Updated Hero"
        assert retrieved.health_current == 25
