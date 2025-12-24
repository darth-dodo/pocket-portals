"""Tests for SessionManager class."""

from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import GamePhase, GameState
from src.state.session_manager import SessionManager


class TestSessionManager:
    """Test suite for SessionManager."""

    def test_create_session_generates_unique_uuid_and_returns_game_state(self) -> None:
        """Test that create_session generates unique UUID and returns GameState."""
        manager = SessionManager()

        session1 = manager.create_session()
        session2 = manager.create_session()

        # Both should be GameState instances
        assert isinstance(session1, GameState)
        assert isinstance(session2, GameState)

        # Session IDs should be unique
        assert session1.session_id != session2.session_id

        # Session IDs should be valid UUIDs (will raise ValueError if not)
        import uuid

        uuid.UUID(session1.session_id)
        uuid.UUID(session2.session_id)

    def test_get_session_returns_none_for_nonexistent_session(self) -> None:
        """Test that get_session returns None for non-existent session."""
        manager = SessionManager()

        result = manager.get_session("nonexistent-session-id")

        assert result is None

    def test_get_session_returns_correct_game_state_for_existing_session(self) -> None:
        """Test that get_session returns correct GameState for existing session."""
        manager = SessionManager()

        # Create a session
        created_session = manager.create_session()
        session_id = created_session.session_id

        # Retrieve the session
        retrieved_session = manager.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session is created_session  # Should be the same object

    def test_get_or_create_session_creates_new_if_session_id_is_none(self) -> None:
        """Test that get_or_create_session creates new session if session_id is None."""
        manager = SessionManager()

        session = manager.get_or_create_session(None)

        assert isinstance(session, GameState)
        assert session.session_id is not None

    def test_get_or_create_session_returns_existing_if_session_exists(self) -> None:
        """Test that get_or_create_session returns existing session if it exists."""
        manager = SessionManager()

        # Create a session
        created_session = manager.create_session()
        session_id = created_session.session_id

        # Get or create with existing ID
        retrieved_session = manager.get_or_create_session(session_id)

        assert retrieved_session is created_session
        assert retrieved_session.session_id == session_id

    def test_add_exchange_appends_to_conversation_history(self) -> None:
        """Test that add_exchange appends to conversation_history."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Initial history should be empty
        assert len(session.conversation_history) == 0

        # Add an exchange
        manager.add_exchange(session_id, "explore cave", "You enter a dark cave...")

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0]["action"] == "explore cave"
        assert (
            session.conversation_history[0]["narrative"] == "You enter a dark cave..."
        )

        # Add another exchange
        manager.add_exchange(
            session_id, "light torch", "The torch illuminates the cave."
        )

        assert len(session.conversation_history) == 2
        assert session.conversation_history[1]["action"] == "light torch"

    def test_add_exchange_limits_history_to_20_entries(self) -> None:
        """Test that add_exchange limits history to 20 entries, removing oldest."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Add 25 exchanges
        for i in range(25):
            manager.add_exchange(session_id, f"action_{i}", f"narrative_{i}")

        # Should only keep the last 20
        assert len(session.conversation_history) == 20

        # First entry should be action_5 (indices 0-4 were removed)
        assert session.conversation_history[0]["action"] == "action_5"
        assert session.conversation_history[0]["narrative"] == "narrative_5"

        # Last entry should be action_24
        assert session.conversation_history[19]["action"] == "action_24"
        assert session.conversation_history[19]["narrative"] == "narrative_24"

    def test_update_health_reduces_health_current(self) -> None:
        """Test that update_health reduces health_current."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Initial health should be 20
        assert session.health_current == 20

        # Apply 5 damage
        remaining = manager.update_health(session_id, 5)

        assert remaining == 15
        assert session.health_current == 15

        # Apply 10 more damage
        remaining = manager.update_health(session_id, 10)

        assert remaining == 5
        assert session.health_current == 5

    def test_update_health_cannot_go_below_0(self) -> None:
        """Test that update_health cannot reduce health below 0."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Apply damage greater than current health
        remaining = manager.update_health(session_id, 150)

        assert remaining == 0
        assert session.health_current == 0

        # Apply more damage when already at 0
        remaining = manager.update_health(session_id, 50)

        assert remaining == 0
        assert session.health_current == 0

    def test_set_character_description_updates_the_character(self) -> None:
        """Test that set_character_description updates the character."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Initial description should be empty string
        assert session.character_description == ""

        # Set description
        description = "A brave warrior with a mysterious past"
        manager.set_character_description(session_id, description)

        assert session.character_description == description

        # Update description
        new_description = "A cunning rogue skilled in stealth"
        manager.set_character_description(session_id, new_description)

        assert session.character_description == new_description


class TestSessionManagerCharacterSheet:
    """Test suite for SessionManager character sheet management."""

    def test_set_character_sheet_stores_sheet_in_session(self) -> None:
        """Test that set_character_sheet stores the sheet in session."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Initially no character sheet
        assert session.character_sheet is None

        # Set character sheet
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        manager.set_character_sheet(session_id, sheet)

        assert session.character_sheet is not None
        assert session.character_sheet.name == "Thorin"
        assert session.character_sheet.race == CharacterRace.DWARF

    def test_get_character_sheet_returns_none_if_not_set(self) -> None:
        """Test that get_character_sheet returns None if not set."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        result = manager.get_character_sheet(session_id)

        assert result is None

    def test_get_character_sheet_returns_sheet_if_set(self) -> None:
        """Test that get_character_sheet returns the sheet if set."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
        )
        manager.set_character_sheet(session_id, sheet)

        result = manager.get_character_sheet(session_id)

        assert result is not None
        assert result.name == "Elara"
        assert result.race == CharacterRace.ELF

    def test_set_phase_updates_game_phase(self) -> None:
        """Test that set_phase updates the game phase."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Initial phase should be CHARACTER_CREATION
        assert session.phase == GamePhase.CHARACTER_CREATION

        # Set to EXPLORATION and verify via getter to avoid mypy overlap warning
        manager.set_phase(session_id, GamePhase.EXPLORATION)
        assert manager.get_phase(session_id) == GamePhase.EXPLORATION

        # Set to COMBAT
        manager.set_phase(session_id, GamePhase.COMBAT)
        assert manager.get_phase(session_id) == GamePhase.COMBAT

    def test_get_phase_returns_current_phase(self) -> None:
        """Test that get_phase returns the current phase."""
        manager = SessionManager()
        session = manager.create_session()
        session_id = session.session_id

        # Get initial phase
        result = manager.get_phase(session_id)
        assert result == GamePhase.CHARACTER_CREATION

        # Update and get again
        manager.set_phase(session_id, GamePhase.DIALOGUE)
        result = manager.get_phase(session_id)
        assert result == GamePhase.DIALOGUE

    def test_set_character_sheet_ignores_invalid_session(self) -> None:
        """Test that set_character_sheet handles invalid session gracefully."""
        manager = SessionManager()
        sheet = CharacterSheet(
            name="Test",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )

        # Should not raise error for non-existent session
        manager.set_character_sheet("invalid-session-id", sheet)

    def test_get_character_sheet_returns_none_for_invalid_session(self) -> None:
        """Test that get_character_sheet returns None for invalid session."""
        manager = SessionManager()

        result = manager.get_character_sheet("invalid-session-id")

        assert result is None

    def test_get_phase_returns_none_for_invalid_session(self) -> None:
        """Test that get_phase returns None for invalid session."""
        manager = SessionManager()

        result = manager.get_phase("invalid-session-id")

        assert result is None
