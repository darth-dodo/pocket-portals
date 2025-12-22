"""Tests for the Jester agent."""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.jester import JesterAgent


@pytest.fixture
def jester() -> JesterAgent:
    """Create a JesterAgent instance for testing."""
    return JesterAgent()


def test_jester_initializes(jester: JesterAgent) -> None:
    """Test that JesterAgent initializes correctly when API key is present."""
    assert jester is not None
    assert jester.agent is not None
    assert jester.llm is not None
    assert jester.agent.role == "The Jester"


@patch("src.agents.jester.Task")
def test_jester_add_complication_returns_string(mock_task: MagicMock) -> None:
    """Test that add_complication returns a non-empty string."""
    # Mock the task execution
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = (
        "Did anyone check if the parrot speaks Common?"
    )
    mock_task.return_value = mock_task_instance

    jester = JesterAgent()
    situation = "You're sneaking past six armed guards with a loud pet parrot."
    result = jester.add_complication(situation)

    assert isinstance(result, str)
    assert len(result) > 0
