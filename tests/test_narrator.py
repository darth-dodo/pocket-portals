"""Tests for NarratorAgent."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.agents.narrator import NarratorAgent


class TestNarratorCombat:
    """Test suite for narrator combat summarization."""

    @pytest.fixture
    def narrator(self) -> NarratorAgent:
        """Create a NarratorAgent instance for testing."""
        # We can't easily mock NarratorAgent initialization, so we skip this test
        # if no API key is available
        try:
            narrator = NarratorAgent()
            return narrator
        except Exception:
            pytest.skip("NarratorAgent requires valid API key")
            raise  # This will never be reached but satisfies mypy

    @patch("src.agents.narrator.Task")
    def test_summarize_combat_victory(
        self, mock_task_class: Any, narrator: NarratorAgent
    ) -> None:
        """Summarize generates narrative for victory."""
        # Mock the task execution
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            "The dwarf warrior struck with fierce determination, "
            "his axe cleaving through the goblin's defenses. "
            "Victory was swift and decisive."
        )
        mock_task_class.return_value = mock_task_instance

        combat_log = [
            "Round 1: Thorin attacks Goblin. 1d20+3=18 vs AC 13. Hit! 1d8+3=7 damage. Goblin HP: 0/7"
        ]

        result = narrator.summarize_combat(
            combat_log=combat_log,
            victory=True,
            enemy_name="Goblin Raider",
            player_name="Thorin",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify Task was created with correct parameters
        mock_task_class.assert_called_once()
        task_args = mock_task_class.call_args
        assert task_args.kwargs["agent"] == narrator.agent

    @patch("src.agents.narrator.Task")
    def test_summarize_combat_defeat(
        self, mock_task_class: Any, narrator: NarratorAgent
    ) -> None:
        """Summarize generates narrative for defeat."""
        # Mock the task execution
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            "The goblin's blade found its mark, and the warrior fell. "
            "Darkness closed in as defeat took hold."
        )
        mock_task_class.return_value = mock_task_instance

        combat_log = [
            "Round 1: Goblin attacks Thorin. 1d20+4=19 vs AC 15. Hit! 1d6+2=6 damage. Thorin HP: 0/10"
        ]

        result = narrator.summarize_combat(
            combat_log=combat_log,
            victory=False,
            enemy_name="Goblin Raider",
            player_name="Thorin",
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify task was created
        mock_task_class.assert_called_once()

    @patch("src.agents.narrator.Task")
    def test_summarize_combat_includes_context(
        self, mock_task_class: Any, narrator: NarratorAgent
    ) -> None:
        """Summarize includes all combat context in task description."""
        # Mock the task execution
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Epic battle summary"
        mock_task_class.return_value = mock_task_instance

        combat_log = [
            "Round 1: Hero attacks Dragon. Hit!",
            "Round 2: Dragon attacks Hero. Miss!",
            "Round 3: Hero attacks Dragon. Hit! Dragon HP: 0/50",
        ]

        narrator.summarize_combat(
            combat_log=combat_log,
            victory=True,
            enemy_name="Ancient Dragon",
            player_name="Hero Supreme",
        )

        # Verify the task description includes all context
        task_args = mock_task_class.call_args
        description = task_args.kwargs["description"]

        assert "Hero Supreme" in description
        assert "Ancient Dragon" in description
        assert "victory" in description.lower() or "won" in description.lower()
        # Combat log should be included
        assert any(log_entry in description for log_entry in combat_log)
