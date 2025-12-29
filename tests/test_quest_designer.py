"""Tests for QuestDesignerAgent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from src.state.character import CharacterClass, CharacterRace, CharacterSheet
from src.state.models import Quest, QuestObjective, QuestStatus

if TYPE_CHECKING:
    from src.agents.quest_designer import QuestDesignerAgent


class TestBuildCharacterContext:
    """Tests for _build_character_context method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    @pytest.fixture
    def character_sheet(self) -> CharacterSheet:
        """Create a test character sheet."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            level=3,
            backstory="A former blacksmith seeking adventure.",
        )

    @pytest.fixture
    def character_sheet_no_backstory(self) -> CharacterSheet:
        """Create a test character sheet without backstory."""
        return CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
            level=1,
            backstory="",
        )

    def test_build_character_context_with_backstory(
        self, mock_agent: QuestDesignerAgent, character_sheet: CharacterSheet
    ) -> None:
        """Test context building includes all character info with backstory."""
        context = mock_agent._build_character_context(character_sheet)

        assert "Thorin" in context
        assert "dwarf" in context
        assert "fighter" in context
        assert "3" in context
        assert "A former blacksmith" in context

    def test_build_character_context_without_backstory(
        self,
        mock_agent: QuestDesignerAgent,
        character_sheet_no_backstory: CharacterSheet,
    ) -> None:
        """Test context building when backstory is empty."""
        context = mock_agent._build_character_context(character_sheet_no_backstory)

        assert "Elara" in context
        assert "elf" in context
        assert "wizard" in context
        # Empty backstory should not be included
        assert "Backstory:" not in context


class TestParseQuestResult:
    """Tests for _parse_quest_result method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    def test_parse_plain_json(self, mock_agent: QuestDesignerAgent) -> None:
        """Test parsing plain JSON result."""
        json_data = {"title": "Test Quest", "description": "A test"}
        result = json.dumps(json_data)

        parsed = mock_agent._parse_quest_result(result)

        assert parsed == json_data

    def test_parse_json_with_markdown_code_block(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        json_data = {"title": "Test Quest", "description": "A test"}
        result = f"```json\n{json.dumps(json_data)}\n```"

        parsed = mock_agent._parse_quest_result(result)

        assert parsed == json_data

    def test_parse_json_with_generic_code_block(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test parsing JSON wrapped in generic code block."""
        json_data = {"title": "Test Quest", "description": "A test"}
        result = f"```\n{json.dumps(json_data)}\n```"

        parsed = mock_agent._parse_quest_result(result)

        assert parsed == json_data

    def test_parse_invalid_json_raises_error(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test that invalid JSON raises ValueError."""
        result = "not valid json {{"

        with pytest.raises(ValueError, match="Invalid quest JSON"):
            mock_agent._parse_quest_result(result)


class TestCreateQuestFromData:
    """Tests for _create_quest_from_data method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    def test_create_quest_with_full_data(self, mock_agent: QuestDesignerAgent) -> None:
        """Test creating quest with all fields provided."""
        quest_data = {
            "id": "quest-123",
            "title": "The Lost Artifact",
            "description": "Find the ancient artifact in the dungeon.",
            "objectives": [
                {"id": "obj-1", "description": "Enter the dungeon"},
                {
                    "id": "obj-2",
                    "description": "Find the artifact",
                    "is_completed": True,
                },
            ],
            "rewards": "100 gold pieces",
            "status": "active",
            "given_by": "Elder Mage",
            "location_hint": "North of the village",
        }

        quest = mock_agent._create_quest_from_data(quest_data)

        assert quest.id == "quest-123"
        assert quest.title == "The Lost Artifact"
        assert quest.description == "Find the ancient artifact in the dungeon."
        assert len(quest.objectives) == 2
        assert quest.objectives[0].id == "obj-1"
        assert quest.objectives[1].is_completed is True
        assert quest.rewards == "100 gold pieces"
        assert quest.given_by == "Elder Mage"
        assert quest.location_hint == "North of the village"

    def test_create_quest_with_minimal_data(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test creating quest with only required fields."""
        quest_data = {
            "title": "Simple Quest",
            "description": "A simple quest description.",
            "objectives": [{"description": "Do something"}],
        }

        quest = mock_agent._create_quest_from_data(quest_data)

        assert quest.title == "Simple Quest"
        assert quest.description == "A simple quest description."
        assert len(quest.objectives) == 1
        # Should generate UUIDs for missing IDs
        assert len(quest.id) > 0
        assert len(quest.objectives[0].id) > 0
        # Default values
        assert quest.status == QuestStatus.ACTIVE
        assert quest.given_by == "Innkeeper Theron"

    def test_create_quest_missing_required_fields(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test that missing required fields raise ValueError."""
        quest_data = {"title": "Missing Fields"}  # No description or objectives

        with pytest.raises(ValueError, match="Missing required quest fields"):
            mock_agent._create_quest_from_data(quest_data)

    def test_create_quest_objective_with_target_count(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test creating quest with quantity-based objectives."""
        quest_data = {
            "title": "Collect Items",
            "description": "Collect 5 gems.",
            "objectives": [
                {
                    "description": "Collect gems",
                    "target_count": 5,
                    "current_count": 2,
                }
            ],
        }

        quest = mock_agent._create_quest_from_data(quest_data)

        assert quest.objectives[0].target_count == 5
        assert quest.objectives[0].current_count == 2


class TestCreateFallbackQuest:
    """Tests for _create_fallback_quest method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    @pytest.fixture
    def character_sheet(self) -> CharacterSheet:
        """Create a test character sheet."""
        return CharacterSheet(
            name="Test Hero",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
            level=1,
        )

    def test_fallback_quest_has_required_fields(
        self, mock_agent: QuestDesignerAgent, character_sheet: CharacterSheet
    ) -> None:
        """Test that fallback quest has all required fields."""
        quest = mock_agent._create_fallback_quest(character_sheet)

        assert quest.id is not None
        assert quest.title == "The Missing Shipment"
        assert "Innkeeper Theron" in quest.description
        assert len(quest.objectives) == 1
        assert quest.status == QuestStatus.ACTIVE
        assert quest.given_by == "Innkeeper Theron"
        assert quest.location_hint is not None

    def test_fallback_quest_generates_unique_ids(
        self, mock_agent: QuestDesignerAgent, character_sheet: CharacterSheet
    ) -> None:
        """Test that each fallback quest has unique IDs."""
        quest1 = mock_agent._create_fallback_quest(character_sheet)
        quest2 = mock_agent._create_fallback_quest(character_sheet)

        assert quest1.id != quest2.id
        assert quest1.objectives[0].id != quest2.objectives[0].id


class TestMatchesObjective:
    """Tests for _matches_objective method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    def test_matches_when_completion_and_target_present(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test matching when both completion keyword and target are in narrative."""
        objective = QuestObjective(
            id="obj-1", description="Find the bandit camp and recover the stolen goods"
        )
        action = "I search for the bandits"
        narrative = "You found the bandit camp hidden in the forest and recovered the stolen goods."

        assert mock_agent._matches_objective(objective, action, narrative) is True

    def test_no_match_without_completion_keyword(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test no match when completion keyword is missing."""
        objective = QuestObjective(id="obj-1", description="Find the bandit camp")
        action = "I search for the bandits"
        narrative = "You see some tracks leading north toward the forest."

        assert mock_agent._matches_objective(objective, action, narrative) is False

    def test_no_match_without_objective_target(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test no match when objective target is not mentioned."""
        objective = QuestObjective(id="obj-1", description="Find the bandit camp")
        action = "I pick some flowers"
        narrative = "You found some beautiful wildflowers by the road."

        assert mock_agent._matches_objective(objective, action, narrative) is False

    def test_match_with_various_completion_keywords(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test matching with different completion keywords."""
        objective = QuestObjective(id="obj-1", description="Defeat the dragon")

        completion_narratives = [
            "You defeated the dragon in an epic battle!",
            "The dragon was killed after a fierce fight.",
            "You have destroyed the dragon's threat forever.",
        ]

        for narrative in completion_narratives:
            assert (
                mock_agent._matches_objective(objective, "attack dragon", narrative)
                is True
            )


class TestGenerateCompletionNarrative:
    """Tests for _generate_completion_narrative method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    def test_completion_narrative_includes_quest_title(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test that completion narrative includes quest title."""
        quest = Quest(
            id="quest-1",
            title="The Lost Treasure",
            description="Find the treasure.",
            objectives=[],
            rewards="500 gold",
            given_by="Captain Jack",
        )

        narrative = mock_agent._generate_completion_narrative(quest)

        assert "The Lost Treasure" in narrative
        assert "Captain Jack" in narrative
        assert "500 gold" in narrative

    def test_completion_narrative_without_rewards(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test completion narrative when no rewards specified."""
        quest = Quest(
            id="quest-1",
            title="Simple Task",
            description="Do something.",
            objectives=[],
            rewards=None,
            given_by="Villager",
        )

        narrative = mock_agent._generate_completion_narrative(quest)

        assert "Simple Task" in narrative
        assert "Experience and satisfaction" in narrative


class TestCheckQuestProgress:
    """Tests for check_quest_progress method."""

    @pytest.fixture
    def mock_agent(self) -> QuestDesignerAgent:
        """Create a mock QuestDesignerAgent without LLM initialization."""
        from src.agents.quest_designer import QuestDesignerAgent

        with (
            patch("src.agents.quest_designer.load_agent_config"),
            patch("src.agents.quest_designer.LLM"),
            patch("src.agents.quest_designer.Agent"),
        ):
            agent = QuestDesignerAgent()
            return agent

    def test_returns_empty_when_no_active_quest(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test returns empty result when quest is None."""
        result = mock_agent.check_quest_progress(None, "some action", "some narrative")  # type: ignore[arg-type]

        assert result["objectives_completed"] == []
        assert result["quest_completed"] is False
        assert result["completion_narrative"] is None

    def test_returns_empty_when_quest_not_active(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test returns empty result when quest status is not ACTIVE."""
        quest = Quest(
            id="quest-1",
            title="Completed Quest",
            description="Already done.",
            objectives=[],
            status=QuestStatus.COMPLETED,
        )

        result = mock_agent.check_quest_progress(quest, "action", "narrative")

        assert result["objectives_completed"] == []
        assert result["quest_completed"] is False

    def test_completes_matching_objective(self, mock_agent: QuestDesignerAgent) -> None:
        """Test that matching objectives are marked complete."""
        quest = Quest(
            id="quest-1",
            title="Find Items",
            description="Find the items.",
            objectives=[
                QuestObjective(
                    id="obj-1",
                    description="Find the ancient sword in the ruins",
                    is_completed=False,
                )
            ],
            status=QuestStatus.ACTIVE,
        )

        result = mock_agent.check_quest_progress(
            quest,
            "search for the sword",
            "You found the ancient sword hidden among the ruins!",
        )

        assert "obj-1" in result["objectives_completed"]
        assert quest.objectives[0].is_completed is True

    def test_quest_completed_when_all_objectives_done(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test quest is marked complete when all objectives are done."""
        quest = Quest(
            id="quest-1",
            title="Single Objective Quest",
            description="One thing to do.",
            objectives=[
                QuestObjective(
                    id="obj-1",
                    description="Defeat the monster in the cave",
                    is_completed=False,
                )
            ],
            status=QuestStatus.ACTIVE,
            rewards="100 gold",
        )

        result = mock_agent.check_quest_progress(
            quest,
            "attack the monster",
            "You defeated the monster in an epic battle!",
        )

        assert result["quest_completed"] is True
        assert quest.status == QuestStatus.COMPLETED
        assert result["completion_narrative"] is not None
        assert "Single Objective Quest" in result["completion_narrative"]

    def test_skips_already_completed_objectives(
        self, mock_agent: QuestDesignerAgent
    ) -> None:
        """Test that already completed objectives are skipped."""
        quest = Quest(
            id="quest-1",
            title="Multi Objective",
            description="Multiple things.",
            objectives=[
                QuestObjective(
                    id="obj-1",
                    description="Find the sword",
                    is_completed=True,  # Already completed
                ),
                QuestObjective(
                    id="obj-2",
                    description="Find the shield",
                    is_completed=False,
                ),
            ],
            status=QuestStatus.ACTIVE,
        )

        result = mock_agent.check_quest_progress(
            quest,
            "search for items",
            "You found the sword lying on the ground.",  # Matches obj-1 but it's done
        )

        # obj-1 should not be re-added to completed list
        assert "obj-1" not in result["objectives_completed"]
