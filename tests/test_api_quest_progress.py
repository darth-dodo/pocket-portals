"""Tests for quest progress integration in process_action().

These tests verify that quest progress is checked and updated during normal
gameplay actions. They are designed to FAIL until the integration is implemented.

Integration requirement: process_action() should call quest_designer.check_quest_progress()
when an active quest exists, and update completed objectives via session manager.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import GamePhase, GameState, Quest, QuestObjective, QuestStatus

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


@pytest.fixture
def mock_quest() -> Quest:
    """Create a test quest with active status."""
    return Quest(
        id="quest-1",
        title="Find the Lost Artifact",
        description="Recover the ancient artifact from the ruins.",
        objectives=[
            QuestObjective(
                id="obj-1",
                description="Find the ancient artifact in the ruins",
                is_completed=False,
            ),
            QuestObjective(
                id="obj-2",
                description="Return the artifact to the village elder",
                is_completed=False,
            ),
        ],
        rewards="100 gold pieces",
        status=QuestStatus.ACTIVE,
        given_by="Village Elder",
        location_hint="The old ruins north of town",
    )


@pytest.fixture
def mock_character_sheet() -> CharacterSheet:
    """Create a test character sheet."""
    return CharacterSheet(
        name="TestHero",
        race=CharacterRace.HUMAN,
        character_class=CharacterClass.FIGHTER,
        level=1,
    )


@pytest.fixture
def mock_state_with_quest(
    mock_quest: Quest, mock_character_sheet: CharacterSheet
) -> GameState:
    """Create mock game state with active quest in EXPLORATION phase."""
    return GameState(
        session_id="session-123",
        phase=GamePhase.EXPLORATION,
        active_quest=mock_quest,
        character_sheet=mock_character_sheet,
        current_choices=["Look around", "Wait", "Leave"],
    )


@pytest.fixture
def mock_state_without_quest(mock_character_sheet: CharacterSheet) -> GameState:
    """Create mock game state without active quest."""
    return GameState(
        session_id="session-456",
        phase=GamePhase.EXPLORATION,
        active_quest=None,
        character_sheet=mock_character_sheet,
        current_choices=["Look around", "Wait", "Leave"],
    )


class TestProcessActionQuestProgress:
    """Tests for quest progress integration in process_action().

    These tests verify that:
    1. check_quest_progress is called when an active quest exists
    2. Completed objectives are updated via session manager
    3. Quest completion triggers completion narrative
    4. No progress check occurs when no quest is active
    """

    @pytest.mark.asyncio
    async def test_process_action_checks_quest_progress(
        self, mock_state_with_quest: GameState, mock_quest: Quest
    ) -> None:
        """When active quest exists, check_quest_progress should be called.

        This test verifies that process_action() calls the quest_designer's
        check_quest_progress method with the active quest, player action,
        and narrative response.

        Expected behavior after integration:
        - quest_designer.check_quest_progress() is called once per action
        - It receives (active_quest, action, narrative) parameters
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        # Create mock session manager
        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_with_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)

        # Create mock quest designer with check_quest_progress
        mock_quest_designer = MagicMock()
        mock_quest_designer.check_quest_progress.return_value = {
            "objectives_completed": [],
            "quest_completed": False,
            "completion_narrative": None,
        }

        # Create mock turn executor
        mock_turn_executor = MagicMock()

        # Create mock request with agents on app.state
        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm
        mock_request.app.state.quest_designer = mock_quest_designer
        mock_request.app.state.turn_executor = mock_turn_executor

        action_request = ActionRequest(
            action="I search for the artifact in the ruins",
            session_id="session-123",
        )

        # Patch check_closure_triggers (imported from src.engine.pacing)
        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            # Setup mock turn executor
            mock_result = MagicMock()
            mock_result.narrative = "You search through the ancient ruins..."
            mock_result.choices = ["Look deeper", "Return", "Rest"]
            mock_turn_executor.execute_async = AsyncMock(return_value=mock_result)

            # Setup closure check to not trigger epilogue
            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            # Call process_action
            await process_action(mock_request, action_request)

            # Assert check_quest_progress was called
            mock_quest_designer.check_quest_progress.assert_called_once()

            # Verify it was called with correct arguments (using kwargs)
            call_args = mock_quest_designer.check_quest_progress.call_args
            assert call_args.kwargs["active_quest"] == mock_quest
            action_arg = call_args.kwargs["action"].lower()
            assert "artifact" in action_arg or "ruins" in action_arg
            assert isinstance(call_args.kwargs["narrative"], str)

    @pytest.mark.asyncio
    async def test_process_action_updates_completed_objectives(
        self, mock_state_with_quest: GameState
    ) -> None:
        """When progress check returns completed objectives, they should be updated.

        This test verifies that when check_quest_progress returns objective IDs
        in the objectives_completed list, the session manager's update_quest_objective
        method is called for each completed objective.

        Expected behavior after integration:
        - For each objective_id in objectives_completed, call sm.update_quest_objective()
        - Objectives are marked as completed in the session state
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        # Create mock session manager
        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_with_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)
        mock_sm.update_quest_objective = AsyncMock()  # This should be called

        # Create mock quest designer that returns completed objective
        mock_quest_designer = MagicMock()
        mock_quest_designer.check_quest_progress.return_value = {
            "objectives_completed": ["obj-1"],  # First objective completed
            "quest_completed": False,
            "completion_narrative": None,
        }

        # Create mock request
        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I found the ancient artifact!",
            session_id="session-123",
        )

        # Set agents on mock_request.app.state

        mock_request.app.state.quest_designer = mock_quest_designer

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = (
                "You found the ancient artifact hidden in the ruins!"
            )
            mock_result.choices = ["Examine it", "Leave", "Continue"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            await process_action(mock_request, action_request)

            # Assert update_quest_objective was called for the completed objective
            mock_sm.update_quest_objective.assert_called_once_with(
                "session-123", "obj-1", True
            )

    @pytest.mark.asyncio
    async def test_process_action_handles_quest_completion(
        self, mock_state_with_quest: GameState
    ) -> None:
        """When quest is fully completed, completion narrative should be appended.

        This test verifies that when check_quest_progress returns quest_completed=True
        with a completion_narrative, that narrative is appended to the response
        and the session manager's complete_quest method is called.

        Expected behavior after integration:
        - completion_narrative is appended to the response narrative
        - sm.complete_quest() is called to finalize the quest
        - Quest moves to completed_quests list
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        completion_narrative = (
            "Quest Completed: Find the Lost Artifact!\n"
            "The Village Elder is pleased with your work.\n"
            "Reward: 100 gold pieces"
        )

        # Create mock session manager
        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_with_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)
        mock_sm.update_quest_objective = AsyncMock()
        mock_sm.complete_quest = AsyncMock()  # This should be called

        # Create mock quest designer that returns quest completed
        mock_quest_designer = MagicMock()
        mock_quest_designer.check_quest_progress.return_value = {
            "objectives_completed": ["obj-1", "obj-2"],  # All objectives completed
            "quest_completed": True,
            "completion_narrative": completion_narrative,
        }

        # Create mock request
        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I return the artifact to the elder",
            session_id="session-123",
        )

        # Set agents on mock_request.app.state

        mock_request.app.state.quest_designer = mock_quest_designer

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = "You hand the artifact to the grateful elder."
            mock_result.choices = ["Continue", "Rest", "Explore"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            response = await process_action(mock_request, action_request)

            # Assert complete_quest was called
            mock_sm.complete_quest.assert_called_once_with("session-123")

            # Assert completion narrative was included in response
            assert (
                completion_narrative in response.narrative
                or "Quest Completed" in response.narrative
            )

    @pytest.mark.asyncio
    async def test_process_action_skips_check_when_no_quest(
        self, mock_state_without_quest: GameState
    ) -> None:
        """When no active quest, no progress check should happen.

        This test verifies that process_action() does not call check_quest_progress
        when the game state has no active quest (active_quest is None).

        Expected behavior after integration:
        - quest_designer.check_quest_progress() is NOT called
        - Normal action processing continues without quest logic
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        # Create mock session manager
        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_without_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)

        # Create mock quest designer
        mock_quest_designer = MagicMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I look around the area",
            session_id="session-456",
        )

        # Set agents on mock_request.app.state

        mock_request.app.state.quest_designer = mock_quest_designer

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = "You survey your surroundings carefully."
            mock_result.choices = ["Continue", "Wait", "Leave"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            await process_action(mock_request, action_request)

            # Assert check_quest_progress was NOT called
            mock_quest_designer.check_quest_progress.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_action_skips_check_during_character_creation(
        self, mock_quest: Quest, mock_character_sheet: CharacterSheet
    ) -> None:
        """Quest progress should not be checked during CHARACTER_CREATION phase.

        This test verifies that even if a quest somehow exists during character
        creation phase, the progress check is skipped since the player is not
        yet engaged in gameplay actions.
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        # Create state in CHARACTER_CREATION phase with quest (edge case)
        state = GameState(
            session_id="session-789",
            phase=GamePhase.CHARACTER_CREATION,
            active_quest=mock_quest,
            character_sheet=None,  # No character yet
            current_choices=["I am a warrior", "I am a mage", "I am a rogue"],
            creation_turn=1,
        )

        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = state
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.increment_creation_turn = AsyncMock(return_value=2)

        mock_quest_designer = MagicMock()

        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I am a brave warrior",
            session_id="session-789",
        )

        # Set agents on mock_request.app.state
        mock_request.app.state.quest_designer = mock_quest_designer
        mock_interviewer = MagicMock()
        mock_request.app.state.character_interviewer = mock_interviewer
        mock_interviewer.interview_turn.return_value = {
            "narrative": "The innkeeper nods...",
            "choices": ["Continue", "Skip", "Tell more"],
        }

        await process_action(mock_request, action_request)

        # Quest progress should NOT be checked during character creation
        mock_quest_designer.check_quest_progress.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_action_skips_check_during_combat(
        self, mock_quest: Quest, mock_character_sheet: CharacterSheet
    ) -> None:
        """Quest progress should not be checked during COMBAT phase.

        This test verifies that quest progress checking is skipped when the
        player is in combat, since combat has its own resolution logic.
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action
        from src.state.models import (
            Combatant,
            CombatantType,
            CombatPhaseEnum,
            CombatState,
            Enemy,
        )

        # Create combat state
        combat_state = CombatState(
            is_active=True,
            phase=CombatPhaseEnum.PLAYER_TURN,
            round_number=1,
            combatants=[
                Combatant(
                    id="player",
                    name="TestHero",
                    type=CombatantType.PLAYER,
                    initiative=15,
                    current_hp=20,
                    max_hp=20,
                    armor_class=15,
                ),
                Combatant(
                    id="enemy-1",
                    name="Goblin",
                    type=CombatantType.ENEMY,
                    initiative=10,
                    current_hp=7,
                    max_hp=7,
                    armor_class=12,
                ),
            ],
            turn_order=["player", "enemy-1"],
            enemy_template=Enemy(
                name="Goblin",
                description="A small green creature",
                max_hp=7,
                armor_class=12,
                attack_bonus=4,
                damage_dice="1d6+2",
            ),
        )

        # Create state in COMBAT phase with active quest
        state = GameState(
            session_id="session-combat",
            phase=GamePhase.COMBAT,
            active_quest=mock_quest,
            character_sheet=mock_character_sheet,
            combat_state=combat_state,
            current_choices=["Attack", "Defend", "Flee"],
        )

        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = state
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.set_combat_state = AsyncMock()
        mock_sm.set_phase = AsyncMock()

        mock_quest_designer = MagicMock()

        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I attack the goblin",
            session_id="session-combat",
        )

        # Set agents on mock_request.app.state
        mock_request.app.state.quest_designer = mock_quest_designer
        mock_keeper = MagicMock()
        mock_request.app.state.keeper = mock_keeper
        # Note: combat_manager is created fresh per request in _get_agents, no need to set

        # Setup mock keeper for combat resolution
        # Player attack defeats enemy to end combat cleanly
        mock_keeper.resolve_player_attack.return_value = {
            "success": True,
            "damage": 10,
            "enemy_hp": 0,  # Enemy defeated
            "log_entry": "You hit the goblin for 10 damage!",
        }

        await process_action(mock_request, action_request)

        # Quest progress should NOT be checked during combat
        mock_quest_designer.check_quest_progress.assert_not_called()


class TestProcessActionQuestProgressIntegration:
    """Integration-style tests using the test client.

    These tests verify the complete flow through the API endpoint.
    """

    def test_action_with_active_quest_checks_progress(self, client: TestClient) -> None:
        """Test that action with active quest triggers progress check.

        This integration test creates a session with an active quest and
        verifies that progress checking is wired up correctly.
        """
        from src.state.models import GamePhase
        from tests.conftest import run_async

        # Start with character creation skipped (goes to QUEST_SELECTION)
        start_response = client.get("/start?skip_creation=true")
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Get the session manager and set up the quest and exploration phase
        sm = client.app.state.session_manager

        quest = Quest(
            id="test-quest-1",
            title="Test Quest",
            description="A test quest for integration testing.",
            objectives=[
                QuestObjective(
                    id="test-obj-1",
                    description="Find the treasure in the dungeon",
                    is_completed=False,
                ),
            ],
            status=QuestStatus.ACTIVE,
            rewards="Test reward",
        )

        # Set up the active quest and transition to EXPLORATION phase
        run_async(sm.set_active_quest(session_id, quest))
        run_async(sm.clear_pending_quest_options(session_id))
        run_async(sm.set_phase(session_id, GamePhase.EXPLORATION))

        # Perform an action that should trigger quest progress check
        # Note: This test will FAIL until integration is implemented because
        # check_quest_progress is not called in process_action
        # Patch the quest_designer on the app state
        mock_qd = MagicMock()
        mock_qd.check_quest_progress.return_value = {
            "objectives_completed": [],
            "quest_completed": False,
            "completion_narrative": None,
        }
        original_qd = client.app.state.quest_designer
        client.app.state.quest_designer = mock_qd

        try:
            action_response = client.post(
                "/action",
                json={
                    "action": "I search for the treasure in the dungeon",
                    "session_id": session_id,
                },
            )

            assert action_response.status_code == 200

            # This assertion will FAIL until integration is implemented
            mock_qd.check_quest_progress.assert_called_once()
        finally:
            client.app.state.quest_designer = original_qd

    def test_objective_completion_updates_quest_state(self, client: TestClient) -> None:
        """Test that completed objectives are persisted in quest state.

        This test verifies that when an objective is completed, the quest
        state is properly updated in the session.
        """
        from src.state.models import GamePhase
        from tests.conftest import run_async

        # Setup session with quest
        start_response = client.get("/start?skip_creation=true")
        session_id = start_response.json()["session_id"]

        sm = client.app.state.session_manager

        quest = Quest(
            id="completion-test-quest",
            title="Completion Test Quest",
            description="Testing objective completion.",
            objectives=[
                QuestObjective(
                    id="completion-obj-1",
                    description="Find the ancient artifact in the ruins",
                    is_completed=False,
                ),
            ],
            status=QuestStatus.ACTIVE,
        )

        # Set up the active quest and transition to EXPLORATION phase
        run_async(sm.set_active_quest(session_id, quest))
        run_async(sm.clear_pending_quest_options(session_id))
        run_async(sm.set_phase(session_id, GamePhase.EXPLORATION))

        # Mock quest designer to return completed objective
        mock_qd = MagicMock()
        mock_qd.check_quest_progress.return_value = {
            "objectives_completed": ["completion-obj-1"],
            "quest_completed": True,
            "completion_narrative": "Quest Complete!",
        }
        # Also mock generate_quest_options for the post-completion flow
        mock_qd.generate_quest_options.return_value = []
        original_qd = client.app.state.quest_designer
        client.app.state.quest_designer = mock_qd

        try:
            action_response = client.post(
                "/action",
                json={
                    "action": "I found the ancient artifact!",
                    "session_id": session_id,
                },
            )

            assert action_response.status_code == 200

            # Check quest state was updated - this will FAIL until integration
            # After integration, the quest should be moved to completed_quests
            state = run_async(sm.get_session(session_id))

            # These assertions will FAIL until integration is implemented
            assert state is not None
            # Quest should be completed and moved
            assert (
                state.active_quest is None
                or state.active_quest.status == QuestStatus.COMPLETED
            )
        finally:
            client.app.state.quest_designer = original_qd


class TestQuestProgressEdgeCases:
    """Tests for edge cases in quest progress checking."""

    @pytest.mark.asyncio
    async def test_handles_quest_designer_none_gracefully(
        self, mock_state_with_quest: GameState
    ) -> None:
        """When quest_designer is None, should skip progress check gracefully.

        This handles the case where ANTHROPIC_API_KEY is not set and agents
        are not initialized.
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_with_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)

        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I explore the area",
            session_id="session-123",
        )

        # Patch quest_designer to be None (simulating no API key)
        # Set agents on mock_request.app.state (quest_designer is None)

        mock_request.app.state.quest_designer = None

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = "You explore carefully."
            mock_result.choices = ["Continue", "Wait", "Leave"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            # Should not raise an exception
            response = await process_action(mock_request, action_request)

            assert response is not None
            assert response.narrative is not None

    @pytest.mark.asyncio
    async def test_handles_check_quest_progress_exception(
        self, mock_state_with_quest: GameState
    ) -> None:
        """When check_quest_progress raises an exception, should handle gracefully.

        The action processing should continue even if quest progress check fails.
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = mock_state_with_quest
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)

        mock_quest_designer = MagicMock()
        mock_quest_designer.check_quest_progress.side_effect = Exception("LLM error")

        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I continue my adventure",
            session_id="session-123",
        )

        # Set agents on mock_request.app.state

        mock_request.app.state.quest_designer = mock_quest_designer

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = "The adventure continues..."
            mock_result.choices = ["Go on", "Rest", "Return"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            # Should not raise an exception - graceful degradation
            response = await process_action(mock_request, action_request)

            assert response is not None
            assert response.narrative is not None

    @pytest.mark.asyncio
    async def test_multiple_objectives_completed_in_single_action(
        self, mock_character_sheet: CharacterSheet
    ) -> None:
        """When multiple objectives are completed at once, all should be updated.

        A single player action might complete multiple quest objectives.
        """
        from src.api.models import ActionRequest
        from src.api.routes.adventure import process_action

        quest = Quest(
            id="multi-obj-quest",
            title="Multi-Objective Quest",
            description="Complete multiple objectives.",
            objectives=[
                QuestObjective(
                    id="mo-1", description="Find the sword", is_completed=False
                ),
                QuestObjective(
                    id="mo-2", description="Find the shield", is_completed=False
                ),
                QuestObjective(
                    id="mo-3", description="Find the helm", is_completed=False
                ),
            ],
            status=QuestStatus.ACTIVE,
        )

        state = GameState(
            session_id="multi-obj-session",
            phase=GamePhase.EXPLORATION,
            active_quest=quest,
            character_sheet=mock_character_sheet,
            current_choices=["Look", "Wait", "Leave"],
        )

        mock_sm = AsyncMock()
        mock_sm.get_or_create_session.return_value = state
        mock_sm.set_choices = AsyncMock()
        mock_sm.add_exchange = AsyncMock()
        mock_sm.update_recent_agents = AsyncMock()
        mock_sm.increment_adventure_turn = AsyncMock(return_value=1)
        mock_sm.update_quest_objective = AsyncMock()

        mock_quest_designer = MagicMock()
        mock_quest_designer.check_quest_progress.return_value = {
            "objectives_completed": [
                "mo-1",
                "mo-2",
            ],  # Two objectives completed at once
            "quest_completed": False,
            "completion_narrative": None,
        }

        mock_request = MagicMock()
        mock_request.app.state.session_manager = mock_sm

        action_request = ActionRequest(
            action="I found the sword and shield in the armory!",
            session_id="multi-obj-session",
        )

        # Set agents on mock_request.app.state

        mock_request.app.state.quest_designer = mock_quest_designer

        mock_executor = MagicMock()

        mock_request.app.state.turn_executor = mock_executor

        with patch("src.api.routes.adventure.check_closure_triggers") as mock_closure:
            mock_result = MagicMock()
            mock_result.narrative = "You found the legendary equipment!"
            mock_result.choices = ["Equip items", "Continue", "Search more"]
            mock_executor.execute_async = AsyncMock(return_value=mock_result)

            mock_closure_status = MagicMock()
            mock_closure_status.should_trigger_epilogue = False
            mock_closure.return_value = mock_closure_status

            await process_action(mock_request, action_request)

            # Both objectives should be updated - WILL FAIL until integration
            assert mock_sm.update_quest_objective.call_count == 2

            # Verify both objective IDs were updated
            call_args_list = mock_sm.update_quest_objective.call_args_list
            updated_ids = [call[0][1] for call in call_args_list]
            assert "mo-1" in updated_ids
            assert "mo-2" in updated_ids
