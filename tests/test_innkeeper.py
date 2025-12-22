"""Tests for InnkeeperAgent."""

import os

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

    def test_innkeeper_introduce_quest_returns_string(self) -> None:
        """Test that introduce_quest method returns a non-empty string."""
        innkeeper = InnkeeperAgent()

        # Test with basic character description
        character_desc = "A weary warrior with a notched sword"
        result = innkeeper.introduce_quest(character_desc)

        # Verify result is a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        assert result.strip() != ""

    def test_innkeeper_introduce_quest_with_context(self) -> None:
        """Test that introduce_quest works with optional context parameter."""
        innkeeper = InnkeeperAgent()

        character_desc = "A skilled rogue looking for work"
        context = "It's been a quiet week at the tavern."
        result = innkeeper.introduce_quest(character_desc, context)

        # Verify result is valid
        assert isinstance(result, str)
        assert len(result) > 0
