"""Tests for ConversationFlow class."""

from unittest.mock import MagicMock

import pytest

from src.engine.flow import ConversationFlow
from src.engine.flow_state import ConversationFlowState


@pytest.fixture
def mock_agents() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create mock agent instances."""
    narrator = MagicMock()
    keeper = MagicMock()
    jester = MagicMock()
    return narrator, keeper, jester


@pytest.fixture
def flow(mock_agents: tuple[MagicMock, MagicMock, MagicMock]) -> ConversationFlow:
    """Create ConversationFlow with mock agents."""
    narrator, keeper, jester = mock_agents
    return ConversationFlow(narrator, keeper, jester)


def test_flow_routes_to_narrator_in_exploration(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow routes correctly in exploration phase."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "You look around the room."
    keeper.respond.return_value = "The keeper speaks."
    jester.respond.return_value = "Jester jokes."

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I look around",
        phase="exploration",
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    assert "narrator" in final_state.agents_to_invoke
    assert final_state.narrative


def test_flow_handles_error_gracefully(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow error handling path."""
    narrator, keeper, jester = mock_agents
    narrator.respond.side_effect = Exception("Agent failed")

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I do something",
        phase="exploration",
        agents_to_invoke=["narrator"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    assert "went wrong" in final_state.narrative or "Error" in final_state.narrative
    assert final_state.choices  # Should have default choices


def test_flow_executes_specified_agents(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow executes agents specified in state."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Narrator speaks."
    keeper.respond.return_value = "Keeper speaks."

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I examine the artifact",
        context="You are in a temple.",
        phase="exploration",
        agents_to_invoke=["narrator", "keeper"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    narrator.respond.assert_called_once_with(
        action="I examine the artifact",
        context="You are in a temple.",
    )
    keeper.respond.assert_called_once_with(
        action="I examine the artifact",
        context="You are in a temple.",
    )
    assert "Narrator speaks." in final_state.narrative
    assert "Keeper speaks." in final_state.narrative


def test_flow_includes_jester_when_flagged(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow includes jester when include_jester is true."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Main story."
    jester.respond.return_value = "Witty comment!"

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I slip on a banana",
        phase="exploration",
        agents_to_invoke=["narrator"],
        include_jester=True,
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    jester.respond.assert_called_once()
    assert "Witty comment!" in final_state.narrative


def test_flow_generates_default_choices(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow generates default choices on success."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Story content."

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I explore",
        phase="exploration",
        agents_to_invoke=["narrator"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    assert len(final_state.choices) == 3
    assert "Investigate further" in final_state.choices
    assert "Talk to someone nearby" in final_state.choices
    assert "Move to a new location" in final_state.choices


def test_flow_aggregates_responses_in_order(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow aggregates responses in execution order."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "First."
    keeper.respond.return_value = "Second."
    jester.respond.return_value = "Third."

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I act",
        phase="exploration",
        agents_to_invoke=["narrator", "keeper"],
        include_jester=True,
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    # Verify order in narrative
    narrative = final_state.narrative
    assert narrative.index("First.") < narrative.index("Second.")
    assert narrative.index("Second.") < narrative.index("Third.")


def test_flow_state_contains_all_responses(
    flow: ConversationFlow, mock_agents: tuple[MagicMock, MagicMock, MagicMock]
) -> None:
    """Test flow state responses dict contains all agent responses."""
    narrator, keeper, jester = mock_agents
    narrator.respond.return_value = "Narrator response."
    keeper.respond.return_value = "Keeper response."

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I investigate",
        phase="exploration",
        agents_to_invoke=["narrator", "keeper"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    assert "narrator" in final_state.responses
    assert "keeper" in final_state.responses
    assert final_state.responses["narrator"] == "Narrator response."
    assert final_state.responses["keeper"] == "Keeper response."
