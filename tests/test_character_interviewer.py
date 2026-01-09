"""Tests for CharacterInterviewerAgent."""

import os
from unittest.mock import MagicMock, patch

from src.agents.character_interviewer import CharacterInterviewerAgent


class TestCharacterInterviewerAgent:
    """Test suite for CharacterInterviewerAgent."""

    def test_character_interviewer_initializes(self) -> None:
        """Test that CharacterInterviewerAgent initializes correctly."""
        # Verify API key exists
        assert os.getenv("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY must be set"

        # Initialize agent
        interviewer = CharacterInterviewerAgent()

        # Verify agent components exist
        assert interviewer.llm is not None
        assert interviewer.agent is not None
        assert interviewer.agent.role == "Character Interviewer"

    def test_default_starter_choices_exist(self) -> None:
        """Test that default starter choices are available as fallback."""
        interviewer = CharacterInterviewerAgent()

        assert len(interviewer.DEFAULT_STARTER_CHOICES) == 3
        for choice in interviewer.DEFAULT_STARTER_CHOICES:
            assert isinstance(choice, str)
            assert len(choice) > 0

    @patch("src.agents.character_interviewer.Task")
    def test_generate_starter_choices_returns_list(self, mock_task: MagicMock) -> None:
        """Test that generate_starter_choices returns a list of 3 choices."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            '{"choices": ["I am a warrior", "I am a mage", "I am a rogue"]}'
        )
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        choices = interviewer.generate_starter_choices()

        assert isinstance(choices, list)
        assert len(choices) == 3
        for choice in choices:
            assert isinstance(choice, str)

    @patch("src.agents.character_interviewer.Task")
    def test_generate_starter_choices_fallback_on_invalid_json(
        self, mock_task: MagicMock
    ) -> None:
        """Test that fallback choices are used when JSON parsing fails."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Invalid JSON response"
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        choices = interviewer.generate_starter_choices()

        # Should return default choices
        assert choices == interviewer.DEFAULT_STARTER_CHOICES

    @patch("src.agents.character_interviewer.Task")
    def test_generate_adventure_hooks_returns_list(self, mock_task: MagicMock) -> None:
        """Test that generate_adventure_hooks returns contextual choices."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            '{"choices": ["A hooded elf beckons you", '
            '"The innkeeper mentions a rogue problem", '
            '"A wizard seeks a thief for hire"]}'
        )
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        character_info = (
            "Name: Shadow\n"
            "Race: Elf\n"
            "Class: Rogue\n"
            "Backstory: A former thieves guild member seeking redemption"
        )
        choices = interviewer.generate_adventure_hooks(character_info)

        assert isinstance(choices, list)
        assert len(choices) == 3
        for choice in choices:
            assert isinstance(choice, str)
            assert len(choice) > 0

    @patch("src.agents.character_interviewer.Task")
    def test_generate_adventure_hooks_fallback_on_error(
        self, mock_task: MagicMock
    ) -> None:
        """Test that fallback hooks are used when LLM fails."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.side_effect = Exception("LLM error")
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        character_info = "Name: Test\nRace: Human\nClass: Fighter"
        choices = interviewer.generate_adventure_hooks(character_info)

        # Should return default hooks
        assert isinstance(choices, list)
        assert len(choices) == 3
        # Verify they're the fallback hooks
        assert (
            "hooded figure" in choices[0].lower() or "innkeeper" in choices[1].lower()
        )

    @patch("src.agents.character_interviewer.Task")
    def test_interview_turn_returns_narrative_and_choices(
        self, mock_task: MagicMock
    ) -> None:
        """Test that interview_turn returns expected structure."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = (
            '{"narrative": "The innkeeper nods slowly.", '
            '"choices": ["I am a fighter", "I am a wizard", "I am a ranger"]}'
        )
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        result = interviewer.interview_turn(
            turn_number=1, conversation_history="Player: Hello"
        )

        assert isinstance(result, dict)
        assert "narrative" in result
        assert "choices" in result
        assert isinstance(result["narrative"], str)
        assert isinstance(result["choices"], list)
        assert len(result["choices"]) == 3

    @patch("src.agents.character_interviewer.Task")
    def test_interview_turn_uses_fallback_on_parse_error(
        self, mock_task: MagicMock
    ) -> None:
        """Test that interview_turn uses fallbacks when parsing fails."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Just plain text, no JSON"
        mock_task.return_value = mock_task_instance

        interviewer = CharacterInterviewerAgent()
        result = interviewer.interview_turn(
            turn_number=2, conversation_history="Some history"
        )

        # Should have fallback structure
        assert "narrative" in result
        assert "choices" in result
        assert len(result["choices"]) == 3

    # Note: _parse_json_response tests removed - we now use Pydantic
    # structured output (output_pydantic) instead of manual JSON parsing.
    # See src/agents/schemas.py for the Pydantic models.
    # See tests/test_schemas.py for validation tests.

    def test_get_fallback_narrative_for_each_turn(self) -> None:
        """Test that fallback narratives exist for all turns."""
        interviewer = CharacterInterviewerAgent()

        for turn in range(1, 6):
            narrative = interviewer._get_fallback_narrative(turn)
            assert isinstance(narrative, str)
            assert len(narrative) > 0
            assert "innkeeper" in narrative.lower() or "he" in narrative.lower()

    def test_get_fallback_choices_for_each_turn(self) -> None:
        """Test that fallback choices exist for all turns."""
        interviewer = CharacterInterviewerAgent()

        for turn in range(1, 6):
            choices = interviewer._get_fallback_choices(turn)
            assert isinstance(choices, list)
            assert len(choices) == 3
            for choice in choices:
                assert isinstance(choice, str)
                assert len(choice) > 0
