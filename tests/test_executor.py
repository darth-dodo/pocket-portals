"""Tests for TurnExecutor class."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.engine.executor import AgentResponse, TurnExecutor, TurnResult
from src.engine.router import RoutingDecision


@pytest.fixture
def mock_agents() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create mock agent instances.

    Note: We explicitly delete respond_with_choices from the narrator mock
    and resolve_action_with_moments from the keeper mock so the executor
    falls back to using respond() instead. This keeps tests simpler and
    focused on execution flow rather than structured output.
    """
    narrator = MagicMock()
    keeper = MagicMock()
    jester = MagicMock()
    # Delete respond_with_choices so hasattr returns False and executor uses respond()
    del narrator.respond_with_choices
    # Delete resolve_action_with_moments so hasattr returns False and executor uses respond()
    del keeper.resolve_action_with_moments
    return narrator, keeper, jester


@pytest.fixture
def executor(mock_agents: tuple[Any, Any, Any]) -> TurnExecutor:
    """Create TurnExecutor with mock agents."""
    narrator, keeper, jester = mock_agents
    return TurnExecutor(narrator, keeper, jester)


def test_executor_single_agent_narrator_only(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test executor with single agent (narrator only) returns response."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = (
        "You enter the dark cave, water dripping from stalactites above."
    )

    routing = RoutingDecision(
        agents=["narrator"],
        include_jester=False,
        reason="Simple narrative continuation",
    )

    result = executor.execute(
        action="I enter the cave",
        routing=routing,
        context="You are standing at the entrance of a mysterious cave.",
    )

    # Narrator is called once for narration (mock doesn't have respond_with_choices)
    narrator.respond.assert_called_once()

    # Call is for narration with original context
    call = narrator.respond.call_args
    assert call.kwargs["action"] == "I enter the cave"
    assert (
        call.kwargs["context"]
        == "You are standing at the entrance of a mysterious cave."
    )

    # Verify keeper and jester were not called
    keeper.respond.assert_not_called()
    jester.respond.assert_not_called()

    # Verify result structure
    assert isinstance(result, TurnResult)
    assert len(result.responses) == 1
    assert result.responses[0].agent == "narrator"
    assert (
        result.responses[0].content
        == "You enter the dark cave, water dripping from stalactites above."
    )
    assert (
        result.narrative
        == "You enter the dark cave, water dripping from stalactites above."
    )
    assert len(result.choices) == 3  # Default choices


def test_executor_multi_agent_narrator_and_keeper(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test executor with multi-agent (narrator + keeper) aggregates responses."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = (
        "You discover an ancient stone door with glowing runes."
    )
    keeper.respond.return_value = (
        "The runes match the pattern described in the Codex of Eldrath, page 47."
    )

    routing = RoutingDecision(
        agents=["narrator", "keeper"],
        include_jester=False,
        reason="Action requires lore knowledge",
    )

    result = executor.execute(
        action="I examine the door closely",
        routing=routing,
        context="You are in an ancient temple.",
    )

    # Narrator is called once for narration (mock doesn't have respond_with_choices)
    narrator.respond.assert_called_once()

    # Narrator call is for narration with original context
    narrator_call = narrator.respond.call_args
    assert narrator_call.kwargs["action"] == "I examine the door closely"
    assert narrator_call.kwargs["context"] == "You are in an ancient temple."

    # Keeper gets accumulated context including narrator's response
    keeper.respond.assert_called_once()
    keeper_call = keeper.respond.call_args
    assert keeper_call.kwargs["action"] == "I examine the door closely"
    assert "Narrator just said" in keeper_call.kwargs["context"]

    # Verify jester was not called
    jester.respond.assert_not_called()

    # Verify result structure
    assert len(result.responses) == 2
    assert result.responses[0].agent == "narrator"
    assert (
        result.responses[0].content
        == "You discover an ancient stone door with glowing runes."
    )
    assert result.responses[1].agent == "keeper"
    assert (
        result.responses[1].content
        == "The runes match the pattern described in the Codex of Eldrath, page 47."
    )

    # Verify narrative combines both responses
    assert "You discover an ancient stone door with glowing runes." in result.narrative
    assert (
        "The runes match the pattern described in the Codex of Eldrath, page 47."
        in result.narrative
    )


def test_executor_multi_agent_with_jester(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test executor with multi-agent (narrator + jester) includes jester commentary."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "You slip on a banana peel and tumble forward."
    jester.respond.return_value = (
        "Classic! I give that pratfall a solid 8/10. Could use more flailing."
    )

    routing = RoutingDecision(
        agents=["narrator"],
        include_jester=True,
        reason="Humorous action deserves commentary",
    )

    result = executor.execute(
        action="I try to sneak past the guards",
        routing=routing,
        context="Guards are patrolling the courtyard.",
    )

    # Narrator is called once for narration (mock doesn't have respond_with_choices)
    narrator.respond.assert_called_once()

    # Narrator call is for narration with original context
    narrator_call = narrator.respond.call_args
    assert narrator_call.kwargs["action"] == "I try to sneak past the guards"
    assert narrator_call.kwargs["context"] == "Guards are patrolling the courtyard."

    # Jester gets accumulated context including narrator's response
    jester.respond.assert_called_once()
    jester_call = jester.respond.call_args
    assert jester_call.kwargs["action"] == "I try to sneak past the guards"
    assert "Narrator just said" in jester_call.kwargs["context"]

    # Verify result structure
    assert len(result.responses) == 2
    assert result.responses[0].agent == "narrator"
    assert result.responses[1].agent == "jester"
    assert (
        result.responses[1].content
        == "Classic! I give that pratfall a solid 8/10. Could use more flailing."
    )

    # Verify narrative includes jester commentary
    assert "You slip on a banana peel and tumble forward." in result.narrative
    assert (
        "Classic! I give that pratfall a solid 8/10. Could use more flailing."
        in result.narrative
    )


def test_executor_context_accumulated_across_agents(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test that context is accumulated across agent calls."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Narrator response"
    keeper.respond.return_value = "Keeper response"
    jester.respond.return_value = "Jester response"

    routing = RoutingDecision(
        agents=["narrator", "keeper"], include_jester=True, reason="All agents needed"
    )

    context = "You are in a mystical library filled with ancient tomes."
    action = "I read the first book"

    executor.execute(
        action=action,
        routing=routing,
        context=context,
    )

    # Narrator is called once for narration (mock doesn't have respond_with_choices)
    narrator.respond.assert_called_once()

    # Narrator call gets original context
    narrator_call = narrator.respond.call_args
    assert narrator_call.kwargs["action"] == action
    assert narrator_call.kwargs["context"] == context

    # Keeper gets accumulated context including narrator's response
    keeper.respond.assert_called_once()
    keeper_call = keeper.respond.call_args
    assert keeper_call.kwargs["action"] == action
    assert context in keeper_call.kwargs["context"]  # Original context included
    assert "Narrator just said" in keeper_call.kwargs["context"]

    # Jester gets accumulated context including narrator and keeper responses
    jester.respond.assert_called_once()
    jester_call = jester.respond.call_args
    assert jester_call.kwargs["action"] == action
    assert "Narrator just said" in jester_call.kwargs["context"]
    assert "Keeper" in jester_call.kwargs["context"]


def test_turn_result_contains_all_agent_responses(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test that TurnResult contains all AgentResponse objects."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Response 1"
    keeper.respond.return_value = "Response 2"
    jester.respond.return_value = "Response 3"

    routing = RoutingDecision(
        agents=["narrator", "keeper"], include_jester=True, reason="All agents active"
    )

    result = executor.execute(
        action="I do something", routing=routing, context="Context"
    )

    # Verify all responses are included
    assert len(result.responses) == 3
    assert all(isinstance(r, AgentResponse) for r in result.responses)
    assert result.responses[0].agent == "narrator"
    assert result.responses[0].content == "Response 1"
    assert result.responses[1].agent == "keeper"
    assert result.responses[1].content == "Response 2"
    assert result.responses[2].agent == "jester"
    assert result.responses[2].content == "Response 3"


def test_combined_narrative_joins_all_responses(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test that combined narrative properly joins all responses."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "First part of the story."
    keeper.respond.return_value = "Important lore details."
    jester.respond.return_value = "Witty observation."

    routing = RoutingDecision(
        agents=["narrator", "keeper"], include_jester=True, reason="All agents active"
    )

    result = executor.execute(
        action="I investigate", routing=routing, context="Context"
    )

    # Verify narrative contains all parts
    assert "First part of the story." in result.narrative
    assert "Important lore details." in result.narrative
    assert "Witty observation." in result.narrative

    # Verify they're properly joined (with newlines)
    expected_narrative = (
        "First part of the story.\n\nImportant lore details.\n\nWitty observation."
    )
    assert result.narrative == expected_narrative


def test_executor_default_choices_always_present(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test that default choices are always included in TurnResult."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Response"

    routing = RoutingDecision(
        agents=["narrator"], include_jester=False, reason="Simple action"
    )

    result = executor.execute(
        action="I do something", routing=routing, context="Context"
    )

    # Verify default choices
    assert result.choices == [
        "Investigate further",
        "Talk to someone nearby",
        "Move to a new location",
    ]


def test_executor_agent_order_preserved(
    executor: TurnExecutor, mock_agents: tuple[Any, Any, Any]
) -> None:
    """Test that agent execution order matches routing.agents order."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Narrator"
    keeper.respond.return_value = "Keeper"
    jester.respond.return_value = "Jester"

    # Test different ordering - keeper before narrator
    routing = RoutingDecision(
        agents=["keeper", "narrator"], include_jester=True, reason="Custom order"
    )

    result = executor.execute(
        action="I do something", routing=routing, context="Context"
    )

    # Verify order in responses matches routing order (keeper, narrator, jester)
    assert result.responses[0].agent == "keeper"
    assert result.responses[1].agent == "narrator"
    assert result.responses[2].agent == "jester"

    # Verify narrative order matches
    expected_narrative = "Keeper\n\nNarrator\n\nJester"
    assert result.narrative == expected_narrative
