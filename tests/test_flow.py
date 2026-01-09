"""Tests for ConversationFlow class."""

from unittest.mock import MagicMock

import pytest

from src.agents.keeper import KeeperResponse
from src.engine.flow import ConversationFlow
from src.engine.flow_state import ConversationFlowState


@pytest.fixture
def mock_agents() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create mock agent instances.

    Note: We explicitly delete respond_with_choices from the narrator mock
    and resolve_action_with_moments from the keeper mock so the flow falls
    back to using respond() instead. This keeps tests simpler and focused
    on flow orchestration rather than structured output.
    """
    narrator = MagicMock()
    keeper = MagicMock()
    jester = MagicMock()
    # Delete respond_with_choices so hasattr returns False and flow uses respond()
    del narrator.respond_with_choices
    # Delete resolve_action_with_moments so hasattr returns False and flow uses respond()
    del keeper.resolve_action_with_moments
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
    """Test flow executes agents specified in state with accumulated context."""
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

    # Narrator is called once for narration (without respond_with_choices, uses respond)
    narrator.respond.assert_called_once()

    # First call is for narration with original context
    first_call = narrator.respond.call_args
    assert first_call.kwargs["action"] == "I examine the artifact"
    assert first_call.kwargs["context"] == "You are in a temple."

    # Keeper gets accumulated context including narrator's response
    keeper.respond.assert_called_once()
    keeper_call = keeper.respond.call_args
    assert keeper_call.kwargs["action"] == "I examine the artifact"
    assert "Narrator just said" in keeper_call.kwargs["context"]

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


def test_flow_extracts_moment_from_keeper_response() -> None:
    """Test flow extracts moment data when keeper uses resolve_action_with_moments."""
    narrator = MagicMock()
    keeper = MagicMock()
    jester = MagicMock()

    # Delete respond_with_choices from narrator
    del narrator.respond_with_choices

    # Configure keeper to use resolve_action_with_moments
    keeper.resolve_action_with_moments.return_value = KeeperResponse(
        resolution="Natural 20! Critical hit for 12 damage.",
        moment_type="critical_success",
        moment_summary="Landed critical hit on the goblin chief",
        moment_significance=0.9,
    )

    narrator.respond.return_value = "You strike with precision!"

    flow = ConversationFlow(narrator, keeper, jester)

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I attack the goblin chief",
        context="Combat is underway.",
        phase="exploration",
        agents_to_invoke=["narrator", "keeper"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    # Verify resolve_action_with_moments was called
    keeper.resolve_action_with_moments.assert_called_once()

    # Verify moment was extracted
    assert final_state.detected_moment is not None
    assert final_state.detected_moment.type == "critical_success"
    assert (
        final_state.detected_moment.summary == "Landed critical hit on the goblin chief"
    )
    assert final_state.detected_moment.significance == 0.9

    # Verify resolution text is in responses
    assert final_state.responses["keeper"] == "Natural 20! Critical hit for 12 damage."


def test_flow_no_moment_when_keeper_returns_routine_action() -> None:
    """Test flow does not set detected_moment for routine actions."""
    narrator = MagicMock()
    keeper = MagicMock()
    jester = MagicMock()

    del narrator.respond_with_choices

    # Keeper returns routine action without significant moment
    keeper.resolve_action_with_moments.return_value = KeeperResponse(
        resolution="DC 12. Rolled 15. Success.",
        moment_type=None,
        moment_summary=None,
        moment_significance=0.3,
    )

    narrator.respond.return_value = "You search the room carefully."

    flow = ConversationFlow(narrator, keeper, jester)

    initial_state = ConversationFlowState(
        session_id="test-session",
        action="I search the room",
        phase="exploration",
        agents_to_invoke=["narrator", "keeper"],
    )

    final_state = flow.kickoff(inputs=initial_state.model_dump())

    # Verify no moment was detected
    assert final_state.detected_moment is None

    # Verify resolution is still in responses
    assert final_state.responses["keeper"] == "DC 12. Rolled 15. Success."
