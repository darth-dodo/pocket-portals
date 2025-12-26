"""Tests for SessionManager class."""

import pytest

from src.state.backends.memory import InMemoryBackend
from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import GamePhase, GameState
from src.state.session_manager import SessionManager


@pytest.fixture
def backend() -> InMemoryBackend:
    """Create in-memory backend for tests."""
    return InMemoryBackend()


@pytest.fixture
def manager(backend: InMemoryBackend) -> SessionManager:
    """Create session manager with in-memory backend."""
    return SessionManager(backend)


class TestSessionManager:
    """Test suite for SessionManager."""

    @pytest.mark.asyncio
    async def test_create_session_generates_unique_uuid_and_returns_game_state(
        self, manager: SessionManager
    ) -> None:
        """Test that create_session generates unique UUID and returns GameState."""
        session1 = await manager.create_session()
        session2 = await manager.create_session()

        # Both should be GameState instances
        assert isinstance(session1, GameState)
        assert isinstance(session2, GameState)

        # Session IDs should be unique
        assert session1.session_id != session2.session_id

        # Session IDs should be valid UUIDs (will raise ValueError if not)
        import uuid

        uuid.UUID(session1.session_id)
        uuid.UUID(session2.session_id)

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_nonexistent_session(
        self, manager: SessionManager
    ) -> None:
        """Test that get_session returns None for non-existent session."""
        result = await manager.get_session("nonexistent-session-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_returns_correct_game_state_for_existing_session(
        self, manager: SessionManager
    ) -> None:
        """Test that get_session returns correct GameState for existing session."""
        # Create a session
        created_session = await manager.create_session()
        session_id = created_session.session_id

        # Retrieve the session
        retrieved_session = await manager.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_or_create_session_creates_new_if_session_id_is_none(
        self, manager: SessionManager
    ) -> None:
        """Test that get_or_create_session creates new session if session_id is None."""
        session = await manager.get_or_create_session(None)

        assert isinstance(session, GameState)
        assert session.session_id is not None

    @pytest.mark.asyncio
    async def test_get_or_create_session_returns_existing_if_session_exists(
        self, manager: SessionManager
    ) -> None:
        """Test that get_or_create_session returns existing session if it exists."""
        # Create a session
        created_session = await manager.create_session()
        session_id = created_session.session_id

        # Get or create with existing ID
        retrieved_session = await manager.get_or_create_session(session_id)

        assert retrieved_session.session_id == session_id

    @pytest.mark.asyncio
    async def test_add_exchange_appends_to_conversation_history(
        self, manager: SessionManager
    ) -> None:
        """Test that add_exchange appends to conversation_history."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initial history should be empty
        assert len(session.conversation_history) == 0

        # Add an exchange
        await manager.add_exchange(
            session_id, "explore cave", "You enter a dark cave..."
        )

        # Retrieve updated session
        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.conversation_history) == 1
        assert updated.conversation_history[0]["action"] == "explore cave"
        assert (
            updated.conversation_history[0]["narrative"] == "You enter a dark cave..."
        )

        # Add another exchange
        await manager.add_exchange(
            session_id, "light torch", "The torch illuminates the cave."
        )

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.conversation_history) == 2
        assert updated.conversation_history[1]["action"] == "light torch"

    @pytest.mark.asyncio
    async def test_add_exchange_limits_history_to_20_entries(
        self, manager: SessionManager
    ) -> None:
        """Test that add_exchange limits history to 20 entries, removing oldest."""
        session = await manager.create_session()
        session_id = session.session_id

        # Add 25 exchanges
        for i in range(25):
            await manager.add_exchange(session_id, f"action_{i}", f"narrative_{i}")

        # Retrieve updated session
        updated = await manager.get_session(session_id)
        assert updated is not None

        # Should only keep the last 20
        assert len(updated.conversation_history) == 20

        # First entry should be action_5 (indices 0-4 were removed)
        assert updated.conversation_history[0]["action"] == "action_5"
        assert updated.conversation_history[0]["narrative"] == "narrative_5"

        # Last entry should be action_24
        assert updated.conversation_history[19]["action"] == "action_24"
        assert updated.conversation_history[19]["narrative"] == "narrative_24"

    @pytest.mark.asyncio
    async def test_update_health_reduces_health_current(
        self, manager: SessionManager
    ) -> None:
        """Test that update_health reduces health_current."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initial health should be 20
        assert session.health_current == 20

        # Apply 5 damage
        remaining = await manager.update_health(session_id, 5)

        assert remaining == 15
        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.health_current == 15

        # Apply 10 more damage
        remaining = await manager.update_health(session_id, 10)

        assert remaining == 5
        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.health_current == 5

    @pytest.mark.asyncio
    async def test_update_health_cannot_go_below_0(
        self, manager: SessionManager
    ) -> None:
        """Test that update_health cannot reduce health below 0."""
        session = await manager.create_session()
        session_id = session.session_id

        # Apply damage greater than current health
        remaining = await manager.update_health(session_id, 150)

        assert remaining == 0
        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.health_current == 0

        # Apply more damage when already at 0
        remaining = await manager.update_health(session_id, 50)

        assert remaining == 0

    @pytest.mark.asyncio
    async def test_set_character_description_updates_the_character(
        self, manager: SessionManager
    ) -> None:
        """Test that set_character_description updates the character."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initial description should be empty string
        assert session.character_description == ""

        # Set description
        description = "A brave warrior with a mysterious past"
        await manager.set_character_description(session_id, description)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.character_description == description

        # Update description
        new_description = "A cunning rogue skilled in stealth"
        await manager.set_character_description(session_id, new_description)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.character_description == new_description


class TestSessionManagerCharacterSheet:
    """Test suite for SessionManager character sheet management."""

    @pytest.mark.asyncio
    async def test_set_character_sheet_stores_sheet_in_session(
        self, manager: SessionManager
    ) -> None:
        """Test that set_character_sheet stores the sheet in session."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initially no character sheet
        assert session.character_sheet is None

        # Set character sheet
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        await manager.set_character_sheet(session_id, sheet)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.character_sheet is not None
        assert updated.character_sheet.name == "Thorin"
        assert updated.character_sheet.race == CharacterRace.DWARF

    @pytest.mark.asyncio
    async def test_get_character_sheet_returns_none_if_not_set(
        self, manager: SessionManager
    ) -> None:
        """Test that get_character_sheet returns None if not set."""
        session = await manager.create_session()
        session_id = session.session_id

        result = await manager.get_character_sheet(session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_character_sheet_returns_sheet_if_set(
        self, manager: SessionManager
    ) -> None:
        """Test that get_character_sheet returns the sheet if set."""
        session = await manager.create_session()
        session_id = session.session_id

        sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
        )
        await manager.set_character_sheet(session_id, sheet)

        result = await manager.get_character_sheet(session_id)

        assert result is not None
        assert result.name == "Elara"
        assert result.race == CharacterRace.ELF

    @pytest.mark.asyncio
    async def test_set_phase_updates_game_phase(self, manager: SessionManager) -> None:
        """Test that set_phase updates the game phase."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initial phase should be CHARACTER_CREATION
        assert session.phase == GamePhase.CHARACTER_CREATION

        # Set to EXPLORATION and verify via getter
        await manager.set_phase(session_id, GamePhase.EXPLORATION)
        result = await manager.get_phase(session_id)
        assert result == GamePhase.EXPLORATION

        # Set to COMBAT
        await manager.set_phase(session_id, GamePhase.COMBAT)
        result = await manager.get_phase(session_id)
        assert result == GamePhase.COMBAT

    @pytest.mark.asyncio
    async def test_get_phase_returns_current_phase(
        self, manager: SessionManager
    ) -> None:
        """Test that get_phase returns the current phase."""
        session = await manager.create_session()
        session_id = session.session_id

        # Get initial phase
        result = await manager.get_phase(session_id)
        assert result == GamePhase.CHARACTER_CREATION

        # Update and get again
        await manager.set_phase(session_id, GamePhase.DIALOGUE)
        result = await manager.get_phase(session_id)
        assert result == GamePhase.DIALOGUE

    @pytest.mark.asyncio
    async def test_set_character_sheet_ignores_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that set_character_sheet handles invalid session gracefully."""
        sheet = CharacterSheet(
            name="Test",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )

        # Should not raise error for non-existent session
        await manager.set_character_sheet("invalid-session-id", sheet)

    @pytest.mark.asyncio
    async def test_get_character_sheet_returns_none_for_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that get_character_sheet returns None for invalid session."""
        result = await manager.get_character_sheet("invalid-session-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_phase_returns_none_for_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that get_phase returns None for invalid session."""
        result = await manager.get_phase("invalid-session-id")

        assert result is None
