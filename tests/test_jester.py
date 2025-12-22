"""Tests for the Jester agent."""

import pytest

from src.agents.jester import JesterAgent
from src.settings import settings


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


def test_jester_add_complication_returns_string(jester: JesterAgent) -> None:
    """Test that add_complication returns a non-empty string."""
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    situation = "You're sneaking past six armed guards with a loud pet parrot."
    result = jester.add_complication(situation)

    assert isinstance(result, str)
    assert len(result) > 0
    assert len(result.split()) <= 50  # Brief commentary (roughly 1-2 sentences)
