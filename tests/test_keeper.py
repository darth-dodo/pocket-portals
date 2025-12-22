"""Tests for KeeperAgent - game mechanics resolution."""

from src.agents.keeper import KeeperAgent


def test_keeper_initializes() -> None:
    """Test that KeeperAgent initializes when API key is present."""
    keeper = KeeperAgent()

    assert keeper is not None
    assert keeper.agent is not None
    assert keeper.llm is not None


def test_keeper_resolve_action_returns_string() -> None:
    """Test that resolve_action returns a non-empty string."""
    keeper = KeeperAgent()

    action = "swing sword at goblin"
    context = "You're in combat with a goblin guard"

    result = keeper.resolve_action(action=action, context=context)

    assert isinstance(result, str)
    assert len(result) > 0
