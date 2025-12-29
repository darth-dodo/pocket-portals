"""Tests for EpilogueAgent."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.agents.epilogue import EpilogueAgent, generate_fallback_epilogue
from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import (
    AdventureMoment,
    AdventurePhase,
    GameState,
    Quest,
    QuestObjective,
)


class TestEpilogueAgentUnit:
    """Unit tests for EpilogueAgent without requiring API key."""

    def test_fallback_epilogue_quest_complete(self) -> None:
        """Fallback epilogue for quest completion is appropriate."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )

        result = generate_fallback_epilogue("quest_complete", state)

        assert isinstance(result, str)
        assert "Thorin" in result
        assert "triumph" in result.lower() or "deeds" in result.lower()
        assert len(result) > 50

    def test_fallback_epilogue_hard_cap(self) -> None:
        """Fallback epilogue for hard cap is reflective."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
        )

        result = generate_fallback_epilogue("hard_cap", state)

        assert isinstance(result, str)
        assert "Elara" in result
        assert "journey" in result.lower() or "chapter" in result.lower()
        assert len(result) > 50

    def test_fallback_epilogue_no_character_sheet(self) -> None:
        """Fallback epilogue works without character sheet."""
        state = GameState(session_id="test-123")

        result = generate_fallback_epilogue("quest_complete", state)

        assert isinstance(result, str)
        assert "Adventurer" in result
        assert len(result) > 50


class TestEpilogueAgent:
    """Test suite for EpilogueAgent methods."""

    @pytest.fixture
    def epilogue_agent(self) -> EpilogueAgent:
        """Create an EpilogueAgent instance for testing."""
        try:
            agent = EpilogueAgent()
            return agent
        except Exception:
            pytest.skip("EpilogueAgent requires valid API key")
            raise

    @pytest.fixture
    def mock_state(self) -> GameState:
        """Create a mock game state for testing."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            backstory="A wandering warrior seeking redemption",
        )
        state.adventure_turn = 30
        state.adventure_phase = AdventurePhase.DENOUEMENT
        state.adventure_moments = [
            AdventureMoment(
                turn=5,
                type="combat_victory",
                summary="Defeated the goblin raiders at dawn",
                significance=0.8,
            ),
            AdventureMoment(
                turn=15,
                type="discovery",
                summary="Found the ancient map in the ruins",
                significance=0.9,
            ),
            AdventureMoment(
                turn=25,
                type="npc_interaction",
                summary="Earned the trust of the village elder",
                significance=0.7,
            ),
        ]
        state.conversation_history = [
            {"action": "Enter the cave", "narrative": "You descend into darkness."},
            {"action": "Light torch", "narrative": "Flames illuminate ancient runes."},
        ]
        return state

    @pytest.fixture
    def mock_state_with_quest(self, mock_state: GameState) -> GameState:
        """Create a mock game state with an active quest."""
        mock_state.active_quest = Quest(
            id="quest-123",
            title="The Lost Relic",
            description="Find the ancient relic in the mountains",
            objectives=[
                QuestObjective(
                    id="obj-1",
                    description="Find the mountain pass",
                    is_completed=True,
                ),
                QuestObjective(
                    id="obj-2",
                    description="Retrieve the relic",
                    is_completed=True,
                ),
            ],
            rewards="100 gold pieces",
        )
        return mock_state

    @patch("src.agents.epilogue.Task")
    def test_generate_epilogue_quest_complete(
        self,
        mock_task_class: Any,
        epilogue_agent: EpilogueAgent,
        mock_state_with_quest: GameState,
    ) -> None:
        """Generate epilogue for quest completion."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            "The dwarf warrior stood at the mountain's peak, the ancient relic "
            "clutched in his calloused hands. From the desperate dawn battle "
            "against goblin raiders to discovering the map that changed everything, "
            "Thorin's journey had been one of transformation. The village elder's "
            "words echoed in his memory as he gazed at the horizon. His quest was "
            "complete, but somehow, he knew this was just the beginning."
        )
        mock_task_class.return_value = mock_task_instance

        result = epilogue_agent.generate_epilogue(
            state=mock_state_with_quest,
            reason="quest_complete",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        mock_task_class.assert_called_once()

    @patch("src.agents.epilogue.Task")
    def test_generate_epilogue_hard_cap(
        self, mock_task_class: Any, epilogue_agent: EpilogueAgent, mock_state: GameState
    ) -> None:
        """Generate epilogue for hard cap ending."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            "As twilight settled over the mountains, Thorin paused to reflect. "
            "Fifty turns of adventure had shaped him in ways he never imagined."
        )
        mock_task_class.return_value = mock_task_instance

        result = epilogue_agent.generate_epilogue(
            state=mock_state,
            reason="hard_cap",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        mock_task_class.assert_called_once()

    @patch("src.agents.epilogue.Task")
    def test_generate_epilogue_includes_character_info(
        self, mock_task_class: Any, epilogue_agent: EpilogueAgent, mock_state: GameState
    ) -> None:
        """Epilogue task description includes character information."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Epic epilogue narrative"
        mock_task_class.return_value = mock_task_instance

        epilogue_agent.generate_epilogue(
            state=mock_state,
            reason="quest_complete",
        )

        task_args = mock_task_class.call_args
        description = task_args.kwargs["description"]

        assert "Thorin" in description
        assert "dwarf" in description.lower() or "Dwarf" in description

    @patch("src.agents.epilogue.Task")
    def test_generate_epilogue_includes_moments(
        self, mock_task_class: Any, epilogue_agent: EpilogueAgent, mock_state: GameState
    ) -> None:
        """Epilogue task description includes adventure moments."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Epic epilogue narrative"
        mock_task_class.return_value = mock_task_instance

        epilogue_agent.generate_epilogue(
            state=mock_state,
            reason="quest_complete",
        )

        task_args = mock_task_class.call_args
        description = task_args.kwargs["description"]

        # Should include moments sorted by significance
        assert "ancient map" in description.lower() or "map" in description
        assert "goblin" in description.lower()


class TestBuildCharacterSummary:
    """Test character summary building."""

    @pytest.fixture
    def epilogue_agent(self) -> EpilogueAgent:
        """Create an EpilogueAgent instance for testing."""
        try:
            agent = EpilogueAgent()
            return agent
        except Exception:
            pytest.skip("EpilogueAgent requires valid API key")
            raise

    def test_build_character_summary_complete(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Character summary includes all character details."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
            backstory="A scholar from the Silver Tower",
        )

        summary = epilogue_agent._build_character_summary(state)

        assert "Elara" in summary
        assert "elf" in summary.lower() or "Elf" in summary
        assert "wizard" in summary.lower() or "Wizard" in summary
        assert "Silver Tower" in summary

    def test_build_character_summary_default_backstory(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Character summary includes default backstory when not explicitly set."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )

        summary = epilogue_agent._build_character_summary(state)

        assert "Thorin" in summary
        assert "dwarf" in summary.lower() or "Dwarf" in summary
        # CharacterSheet has a default backstory, so it should be included
        assert "Backstory" in summary

    def test_build_character_summary_no_character(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Character summary handles missing character sheet."""
        state = GameState(session_id="test-123")

        summary = epilogue_agent._build_character_summary(state)

        assert "adventurer" in summary.lower()

    def test_build_character_summary_with_quest(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Character summary includes quest information."""
        state = GameState(session_id="test-123")
        state.character_sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        state.active_quest = Quest(
            id="quest-123",
            title="The Lost Relic",
            description="Find the ancient relic",
            objectives=[
                QuestObjective(id="obj-1", description="Find it", is_completed=True),
                QuestObjective(id="obj-2", description="Return it", is_completed=False),
            ],
        )

        summary = epilogue_agent._build_character_summary(state)

        assert "Lost Relic" in summary
        assert "1/2" in summary


class TestFormatAdventureMoments:
    """Test adventure moments formatting."""

    @pytest.fixture
    def epilogue_agent(self) -> EpilogueAgent:
        """Create an EpilogueAgent instance for testing."""
        try:
            agent = EpilogueAgent()
            return agent
        except Exception:
            pytest.skip("EpilogueAgent requires valid API key")
            raise

    def test_format_adventure_moments_sorted_by_significance(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Moments are sorted by significance, highest first."""
        state = GameState(session_id="test-123")
        state.adventure_moments = [
            AdventureMoment(
                turn=5, type="combat", summary="Low priority fight", significance=0.3
            ),
            AdventureMoment(
                turn=10, type="discovery", summary="Major discovery", significance=0.9
            ),
            AdventureMoment(
                turn=15, type="choice", summary="Medium choice", significance=0.6
            ),
        ]

        result = epilogue_agent._format_adventure_moments(state)

        # Should be in order of significance
        lines = result.split("\n")
        assert "Major discovery" in lines[0]

    def test_format_adventure_moments_limit_to_five(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Only top 5 moments are included."""
        state = GameState(session_id="test-123")
        state.adventure_moments = [
            AdventureMoment(
                turn=i, type="event", summary=f"Event {i}", significance=0.5 + i * 0.05
            )
            for i in range(10)
        ]

        result = epilogue_agent._format_adventure_moments(state)

        # Count lines (moments)
        lines = [line for line in result.split("\n") if line.strip().startswith("-")]
        assert len(lines) <= 5

    def test_format_adventure_moments_empty(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Empty moments falls back to history extraction."""
        state = GameState(session_id="test-123")
        state.adventure_moments = []
        state.conversation_history = [
            {"action": "Enter cave", "narrative": "You enter the dark cave."},
        ]

        result = epilogue_agent._format_adventure_moments(state)

        # Should fall back to extracting from history
        assert "dark cave" in result.lower() or "Beginning" in result


class TestExtractMomentsFromHistory:
    """Test fallback moment extraction from conversation history."""

    @pytest.fixture
    def epilogue_agent(self) -> EpilogueAgent:
        """Create an EpilogueAgent instance for testing."""
        try:
            agent = EpilogueAgent()
            return agent
        except Exception:
            pytest.skip("EpilogueAgent requires valid API key")
            raise

    def test_extract_moments_from_history_full(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Extract moments from full conversation history."""
        state = GameState(session_id="test-123")
        state.conversation_history = [
            {"action": "Start journey", "narrative": "The adventure begins at dawn."},
            {
                "action": "Find clue",
                "narrative": "A mysterious scroll reveals secrets.",
            },
            {"action": "Fight dragon", "narrative": "The dragon falls before you."},
            {
                "action": "Return home",
                "narrative": "The village celebrates your return.",
            },
        ]

        result = epilogue_agent._extract_moments_from_history(state)

        # Should include early, middle, and recent
        assert "Beginning" in result or "Journey" in result or "Recent" in result

    def test_extract_moments_from_history_empty(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Handle empty conversation history."""
        state = GameState(session_id="test-123")
        state.conversation_history = []

        result = epilogue_agent._extract_moments_from_history(state)

        assert isinstance(result, str)
        assert "journey" in result.lower() or "tale" in result.lower()

    def test_extract_moments_from_history_single(
        self, epilogue_agent: EpilogueAgent
    ) -> None:
        """Handle single conversation entry."""
        state = GameState(session_id="test-123")
        state.conversation_history = [
            {"action": "Look around", "narrative": "You see a vast landscape."},
        ]

        result = epilogue_agent._extract_moments_from_history(state)

        assert "vast landscape" in result.lower() or "Beginning" in result
