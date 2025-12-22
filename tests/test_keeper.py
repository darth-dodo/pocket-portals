"""Tests for KeeperAgent - game mechanics resolution."""

from unittest.mock import MagicMock, patch

from src.agents.keeper import KeeperAgent


def test_keeper_initializes() -> None:
    """Test that KeeperAgent initializes when API key is present."""
    keeper = KeeperAgent()

    assert keeper is not None
    assert keeper.agent is not None
    assert keeper.llm is not None


@patch("src.agents.keeper.Task")
def test_keeper_resolve_action_returns_string(mock_task: MagicMock) -> None:
    """Test that resolve_action returns a non-empty string."""
    # Mock the task execution
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "14. Hits. 6 damage."
    mock_task.return_value = mock_task_instance

    keeper = KeeperAgent()

    action = "swing sword at goblin"
    context = "You're in combat with a goblin guard"

    result = keeper.resolve_action(action=action, context=context)

    assert isinstance(result, str)
    assert len(result) > 0
