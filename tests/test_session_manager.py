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


class TestSessionManagerQuests:
    """Test suite for SessionManager quest management."""

    @pytest.mark.asyncio
    async def test_set_active_quest_stores_quest(self, manager: SessionManager) -> None:
        """Test that set_active_quest stores the quest in session."""
        from src.state.models import Quest, QuestObjective, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        # Initially no active quest
        assert session.active_quest is None

        # Set active quest
        quest = Quest(
            id="quest-1",
            title="The Lost Artifact",
            description="Find the ancient artifact.",
            objectives=[QuestObjective(id="obj-1", description="Enter the dungeon")],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.active_quest is not None
        assert updated.active_quest.title == "The Lost Artifact"

    @pytest.mark.asyncio
    async def test_set_active_quest_can_clear_quest(
        self, manager: SessionManager
    ) -> None:
        """Test that set_active_quest can clear the active quest."""
        from src.state.models import Quest, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        # Set a quest first
        quest = Quest(
            id="quest-1",
            title="Test Quest",
            description="Test description.",
            objectives=[],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        # Clear the quest
        await manager.set_active_quest(session_id, None)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.active_quest is None

    @pytest.mark.asyncio
    async def test_get_active_quest_returns_quest_if_set(
        self, manager: SessionManager
    ) -> None:
        """Test that get_active_quest returns the quest if set."""
        from src.state.models import Quest, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        quest = Quest(
            id="quest-1",
            title="Find the Dragon",
            description="Locate the dragon's lair.",
            objectives=[],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        result = await manager.get_active_quest(session_id)

        assert result is not None
        assert result.title == "Find the Dragon"

    @pytest.mark.asyncio
    async def test_get_active_quest_returns_none_if_not_set(
        self, manager: SessionManager
    ) -> None:
        """Test that get_active_quest returns None if no quest is set."""
        session = await manager.create_session()
        session_id = session.session_id

        result = await manager.get_active_quest(session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_quest_returns_none_for_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that get_active_quest returns None for invalid session."""
        result = await manager.get_active_quest("invalid-session-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_quest_moves_to_completed_list(
        self, manager: SessionManager
    ) -> None:
        """Test that complete_quest moves quest to completed list."""
        from src.state.models import Quest, QuestObjective, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        # Set active quest
        quest = Quest(
            id="quest-1",
            title="Slay the Dragon",
            description="Defeat the dragon.",
            objectives=[
                QuestObjective(id="obj-1", description="Find dragon", is_completed=True)
            ],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        # Complete the quest
        await manager.complete_quest(session_id)

        updated = await manager.get_session(session_id)
        assert updated is not None

        # Active quest should be cleared
        assert updated.active_quest is None

        # Quest should be in completed list
        assert len(updated.completed_quests) == 1
        assert updated.completed_quests[0].title == "Slay the Dragon"
        assert updated.completed_quests[0].status == QuestStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_complete_quest_does_nothing_if_no_active_quest(
        self, manager: SessionManager
    ) -> None:
        """Test that complete_quest does nothing if no active quest."""
        session = await manager.create_session()
        session_id = session.session_id

        # No active quest
        await manager.complete_quest(session_id)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.completed_quests) == 0

    @pytest.mark.asyncio
    async def test_update_quest_objective_marks_complete(
        self, manager: SessionManager
    ) -> None:
        """Test that update_quest_objective marks objective as complete."""
        from src.state.models import Quest, QuestObjective, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        # Set quest with objectives
        quest = Quest(
            id="quest-1",
            title="Multi Objective Quest",
            description="Multiple things to do.",
            objectives=[
                QuestObjective(
                    id="obj-1", description="First task", is_completed=False
                ),
                QuestObjective(
                    id="obj-2", description="Second task", is_completed=False
                ),
            ],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        # Complete first objective
        await manager.update_quest_objective(session_id, "obj-1", completed=True)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.active_quest is not None
        assert updated.active_quest.objectives[0].is_completed is True
        assert updated.active_quest.objectives[1].is_completed is False

    @pytest.mark.asyncio
    async def test_update_quest_objective_does_nothing_for_nonexistent_objective(
        self, manager: SessionManager
    ) -> None:
        """Test that update_quest_objective handles nonexistent objective gracefully."""
        from src.state.models import Quest, QuestObjective, QuestStatus

        session = await manager.create_session()
        session_id = session.session_id

        quest = Quest(
            id="quest-1",
            title="Test Quest",
            description="Test.",
            objectives=[
                QuestObjective(id="obj-1", description="Task", is_completed=False),
            ],
            status=QuestStatus.ACTIVE,
        )
        await manager.set_active_quest(session_id, quest)

        # Try to update non-existent objective
        await manager.update_quest_objective(
            session_id, "nonexistent-obj", completed=True
        )

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.active_quest is not None
        # Original objective should still be incomplete
        assert updated.active_quest.objectives[0].is_completed is False


class TestSessionManagerCreationTurn:
    """Test suite for SessionManager character creation turn management."""

    @pytest.mark.asyncio
    async def test_set_creation_turn_updates_turn(
        self, manager: SessionManager
    ) -> None:
        """Test that set_creation_turn updates the turn number."""
        session = await manager.create_session()
        session_id = session.session_id

        # Initially at turn 0
        assert session.creation_turn == 0

        # Set to turn 3
        await manager.set_creation_turn(session_id, 3)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.creation_turn == 3

    @pytest.mark.asyncio
    async def test_set_creation_turn_caps_at_5(self, manager: SessionManager) -> None:
        """Test that set_creation_turn caps at 5."""
        session = await manager.create_session()
        session_id = session.session_id

        await manager.set_creation_turn(session_id, 10)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.creation_turn == 5

    @pytest.mark.asyncio
    async def test_set_creation_turn_floors_at_0(self, manager: SessionManager) -> None:
        """Test that set_creation_turn floors at 0."""
        session = await manager.create_session()
        session_id = session.session_id

        await manager.set_creation_turn(session_id, -5)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.creation_turn == 0

    @pytest.mark.asyncio
    async def test_increment_creation_turn_increases_by_one(
        self, manager: SessionManager
    ) -> None:
        """Test that increment_creation_turn increases by one."""
        session = await manager.create_session()
        session_id = session.session_id

        # Increment from 0
        result = await manager.increment_creation_turn(session_id)
        assert result == 1

        # Increment again
        result = await manager.increment_creation_turn(session_id)
        assert result == 2

    @pytest.mark.asyncio
    async def test_increment_creation_turn_caps_at_5(
        self, manager: SessionManager
    ) -> None:
        """Test that increment_creation_turn caps at 5."""
        session = await manager.create_session()
        session_id = session.session_id

        # Set to 4, then increment twice
        await manager.set_creation_turn(session_id, 4)

        result = await manager.increment_creation_turn(session_id)
        assert result == 5

        # Should stay at 5
        result = await manager.increment_creation_turn(session_id)
        assert result == 5

    @pytest.mark.asyncio
    async def test_increment_creation_turn_returns_zero_for_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that increment_creation_turn returns 0 for invalid session."""
        result = await manager.increment_creation_turn("invalid-session")
        assert result == 0


class TestSessionManagerChoicesAndAgents:
    """Test suite for SessionManager choices and recent agents management."""

    @pytest.mark.asyncio
    async def test_set_choices_updates_current_choices(
        self, manager: SessionManager
    ) -> None:
        """Test that set_choices updates current choices."""
        session = await manager.create_session()
        session_id = session.session_id

        choices = ["Go north", "Go south", "Stay here"]
        await manager.set_choices(session_id, choices)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.current_choices == choices

    @pytest.mark.asyncio
    async def test_set_choices_replaces_previous_choices(
        self, manager: SessionManager
    ) -> None:
        """Test that set_choices replaces previous choices."""
        session = await manager.create_session()
        session_id = session.session_id

        await manager.set_choices(session_id, ["Option A", "Option B"])
        await manager.set_choices(session_id, ["Option C", "Option D"])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.current_choices == ["Option C", "Option D"]

    @pytest.mark.asyncio
    async def test_update_recent_agents_adds_agents(
        self, manager: SessionManager
    ) -> None:
        """Test that update_recent_agents adds agents to list."""
        session = await manager.create_session()
        session_id = session.session_id

        await manager.update_recent_agents(session_id, ["narrator"])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert "narrator" in updated.recent_agents

    @pytest.mark.asyncio
    async def test_update_recent_agents_keeps_last_5(
        self, manager: SessionManager
    ) -> None:
        """Test that update_recent_agents keeps only last 5 agents."""
        session = await manager.create_session()
        session_id = session.session_id

        # Add 7 agents one by one
        agents = ["agent1", "agent2", "agent3", "agent4", "agent5", "agent6", "agent7"]
        for agent in agents:
            await manager.update_recent_agents(session_id, [agent])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.recent_agents) == 5
        # Should have the last 5 agents
        assert updated.recent_agents == [
            "agent3",
            "agent4",
            "agent5",
            "agent6",
            "agent7",
        ]

    @pytest.mark.asyncio
    async def test_update_recent_agents_tracks_jester_turns(
        self, manager: SessionManager
    ) -> None:
        """Test that update_recent_agents tracks turns since jester."""
        session = await manager.create_session()
        session_id = session.session_id

        # Add narrator (not jester)
        await manager.update_recent_agents(session_id, ["narrator"])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.turns_since_jester == 1  # Incremented

        # Add jester
        await manager.update_recent_agents(session_id, ["jester"])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.turns_since_jester == 0  # Reset

        # Add narrator again
        await manager.update_recent_agents(session_id, ["narrator"])

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert updated.turns_since_jester == 1  # Incremented again


class TestSessionManagerAdventureMoments:
    """Test suite for SessionManager adventure moment management."""

    @pytest.mark.asyncio
    async def test_add_adventure_moment_stores_moment(
        self, manager: SessionManager
    ) -> None:
        """Test that add_adventure_moment stores the moment in session."""
        from src.state.models import AdventureMoment

        session = await manager.create_session()
        session_id = session.session_id

        # Initially no moments
        assert len(session.adventure_moments) == 0

        # Add a moment
        moment = AdventureMoment(
            turn=5,
            type="combat_victory",
            summary="Defeated the cave goblin",
            significance=0.8,
        )
        await manager.add_adventure_moment(session_id, moment)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.adventure_moments) == 1
        assert updated.adventure_moments[0].turn == 5
        assert updated.adventure_moments[0].type == "combat_victory"

    @pytest.mark.asyncio
    async def test_add_adventure_moment_caps_at_max(
        self, manager: SessionManager
    ) -> None:
        """Test that add_adventure_moment caps at MAX_ADVENTURE_MOMENTS."""
        from src.state.models import AdventureMoment
        from src.state.session_manager import MAX_ADVENTURE_MOMENTS

        session = await manager.create_session()
        session_id = session.session_id

        # Add more moments than the max
        for i in range(MAX_ADVENTURE_MOMENTS + 5):
            moment = AdventureMoment(
                turn=i,
                type="discovery",
                summary=f"Moment {i}",
                significance=0.5,  # All same significance
            )
            await manager.add_adventure_moment(session_id, moment)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.adventure_moments) == MAX_ADVENTURE_MOMENTS

    @pytest.mark.asyncio
    async def test_add_adventure_moment_keeps_highest_significance(
        self, manager: SessionManager
    ) -> None:
        """Test that capping keeps moments with highest significance."""
        from src.state.models import AdventureMoment
        from src.state.session_manager import MAX_ADVENTURE_MOMENTS

        session = await manager.create_session()
        session_id = session.session_id

        # Add moments with varying significance
        # First add MAX moments with low significance
        for i in range(MAX_ADVENTURE_MOMENTS):
            moment = AdventureMoment(
                turn=i,
                type="discovery",
                summary=f"Low significance {i}",
                significance=0.3,
            )
            await manager.add_adventure_moment(session_id, moment)

        # Now add a high-significance moment
        high_moment = AdventureMoment(
            turn=100,
            type="combat_victory",
            summary="High significance event",
            significance=0.95,
        )
        await manager.add_adventure_moment(session_id, high_moment)

        updated = await manager.get_session(session_id)
        assert updated is not None
        assert len(updated.adventure_moments) == MAX_ADVENTURE_MOMENTS

        # The high significance moment should be kept
        summaries = [m.summary for m in updated.adventure_moments]
        assert "High significance event" in summaries

    @pytest.mark.asyncio
    async def test_add_adventure_moment_handles_invalid_session(
        self, manager: SessionManager
    ) -> None:
        """Test that add_adventure_moment handles invalid session gracefully."""
        from src.state.models import AdventureMoment

        moment = AdventureMoment(
            turn=1, type="discovery", summary="Test", significance=0.5
        )

        # Should not raise error for non-existent session
        await manager.add_adventure_moment("invalid-session-id", moment)

    @pytest.mark.asyncio
    async def test_add_multiple_moments_maintains_order_by_significance(
        self, manager: SessionManager
    ) -> None:
        """Test that moments are sorted by significance after capping."""
        from src.state.models import AdventureMoment
        from src.state.session_manager import MAX_ADVENTURE_MOMENTS

        session = await manager.create_session()
        session_id = session.session_id

        # Add many moments with varying significance
        for i in range(MAX_ADVENTURE_MOMENTS + 3):
            significance = 0.1 + (i * 0.05)  # Increasing significance
            moment = AdventureMoment(
                turn=i,
                type="achievement",
                summary=f"Moment sig={significance:.2f}",
                significance=min(significance, 1.0),
            )
            await manager.add_adventure_moment(session_id, moment)

        updated = await manager.get_session(session_id)
        assert updated is not None

        # After capping, moments should be the ones with highest significance
        # The first 3 moments (lowest significance) should have been removed
        assert len(updated.adventure_moments) == MAX_ADVENTURE_MOMENTS

        # Verify the lowest significance moments were removed
        significances = [m.significance for m in updated.adventure_moments]
        assert all(s >= 0.25 for s in significances)  # Low significance ones removed
