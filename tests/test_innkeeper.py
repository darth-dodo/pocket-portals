"""Tests for InnkeeperAgent."""

import os
from unittest.mock import MagicMock, patch

from src.agents.innkeeper import InnkeeperAgent


class TestInnkeeperAgent:
    """Test suite for InnkeeperAgent."""

    def test_innkeeper_initializes(self) -> None:
        """Test that InnkeeperAgent initializes correctly when API key is present."""
        # Verify API key exists
        assert os.getenv("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY must be set"

        # Initialize agent
        innkeeper = InnkeeperAgent()

        # Verify agent components exist
        assert innkeeper.llm is not None
        assert innkeeper.agent is not None
        assert innkeeper.agent.role == "Innkeeper Theron"

    @patch("src.agents.innkeeper.Task")
    def test_innkeeper_introduce_quest_returns_string(self, mock_task: MagicMock) -> None:
        """Test that introduce_quest method returns a non-empty string."""
        # Mock the task execution
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Storm's breaking. Roads'll be mud by morning."
        mock_task.return_value = mock_task_instance

        innkeeper = InnkeeperAgent()

        # Test with basic character description
        character_desc = "A weary warrior with a notched sword"
        result = innkeeper.introduce_quest(character_desc)

        # Verify result is a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        assert result.strip() != ""

    @patch("src.agents.innkeeper.Task")
    def test_innkeeper_introduce_quest_with_context(self, mock_task: MagicMock) -> None:
        """Test that introduce_quest works with optional context parameter."""
        # Mock the task execution
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Quiet week. Could use some help with a problem."
        mock_task.return_value = mock_task_instance

        innkeeper = InnkeeperAgent()

        character_desc = "A skilled rogue looking for work"
        context = "It's been a quiet week at the tavern."
        result = innkeeper.introduce_quest(character_desc, context)

        # Verify result is valid
        assert isinstance(result, str)
        assert len(result) > 0
