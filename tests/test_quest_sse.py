"""Tests for quest SSE game_state event functionality.

These tests verify that the /action/stream endpoint correctly emits
game_state SSE events with active_quest data when a player selects a quest.

The QUEST_SELECTION handling in src/api/routes/adventure.py (lines 623-692)
emits a game_state SSE event after successful quest selection.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.state.models import GamePhase, Quest
from tests.conftest import SessionStateHelper


def parse_sse_events(content: str) -> list[dict[str, Any]]:
    """Parse SSE events from response content.

    Args:
        content: Raw SSE response content with event: and data: lines

    Returns:
        List of dicts with 'event' and 'data' keys
    """
    events = []
    current_event = ""
    for line in content.split("\n"):
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:") and current_event:
            try:
                data = json.loads(line[5:].strip())
                events.append({"event": current_event, "data": data})
            except json.JSONDecodeError:
                # Skip malformed JSON data
                pass
            current_event = ""
    return events


def collect_sse_events(
    client: TestClient, session_id: str, action: str
) -> list[dict[str, Any]]:
    """Helper to make streaming request and collect all SSE events.

    Args:
        client: FastAPI TestClient
        session_id: Session ID to use
        action: Action to send

    Returns:
        List of parsed SSE events
    """
    events = []
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": action, "session_id": session_id},
    ) as response:
        current_event = ""
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:") and current_event:
                try:
                    data = json.loads(line[5:].strip())
                    events.append({"event": current_event, "data": data})
                except json.JSONDecodeError:
                    pass
                current_event = ""
    return events


@pytest.fixture
def session_with_quest_selection(
    client: TestClient, session_state: SessionStateHelper
) -> tuple[str, list[Quest]]:
    """Create a session in QUEST_SELECTION phase with pending quest options.

    Returns:
        Tuple of (session_id, pending_quest_options)
    """
    # Start with character creation skipped (goes to QUEST_SELECTION)
    start_response = client.get("/start?skip_creation=true")
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    # Verify we're in QUEST_SELECTION phase
    phase = session_state.get_phase(session_id)
    assert phase == GamePhase.QUEST_SELECTION

    # Get the pending quest options
    session = session_state.get_session(session_id)
    assert session is not None
    assert len(session.pending_quest_options) == 3

    return session_id, session.pending_quest_options


class TestQuestSelectionStreamEmitsGameStateEvent:
    """Test that quest selection streaming emits game_state SSE event."""

    def test_quest_selection_stream_emits_game_state_event(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """When a quest is selected via stream, a game_state event is emitted."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        # Select the first quest
        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        # Find game_state event
        game_state_events = [e for e in events if e["event"] == "game_state"]

        assert len(game_state_events) >= 1, (
            f"Expected at least one game_state event, got none. "
            f"Events received: {[e['event'] for e in events]}"
        )

        # Check that the game_state event has active_quest
        game_state_data = game_state_events[0]["data"]
        assert "active_quest" in game_state_data, (
            f"Expected active_quest in game_state data, got: {game_state_data.keys()}"
        )

    def test_quest_selection_game_state_has_correct_structure(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """Verify active_quest structure has all required fields."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        # Select the first quest
        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        # Find game_state event
        game_state_events = [e for e in events if e["event"] == "game_state"]
        assert len(game_state_events) >= 1, "Expected game_state event"

        active_quest = game_state_events[0]["data"]["active_quest"]

        # Verify top-level fields
        assert "title" in active_quest, "active_quest should have title"
        assert "description" in active_quest, "active_quest should have description"
        assert "objectives" in active_quest, "active_quest should have objectives"
        assert "rewards" in active_quest, "active_quest should have rewards"
        assert "given_by" in active_quest, "active_quest should have given_by"
        assert "location_hint" in active_quest, "active_quest should have location_hint"

        # Verify title matches selected quest
        assert active_quest["title"] == quest_to_select.title

        # Verify objectives structure
        assert isinstance(active_quest["objectives"], list), (
            "objectives should be a list"
        )
        if active_quest["objectives"]:
            first_objective = active_quest["objectives"][0]
            assert "id" in first_objective, "objective should have id"
            assert "description" in first_objective, "objective should have description"
            assert "completed" in first_objective, "objective should have completed"

    def test_quest_selection_stream_emits_all_events_in_order(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """Verify event order for quest selection streaming."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        # Select the first quest
        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        # Extract event types in order
        event_types = [e["event"] for e in events]

        # Verify key events are present
        assert "agent_start" in event_types, "agent_start should be emitted"
        assert "agent_response" in event_types, "agent_response should be emitted"
        assert "game_state" in event_types, "game_state should be emitted"
        assert "choices" in event_types, "choices should be emitted"
        assert "complete" in event_types, "complete should be emitted"

        # Verify ordering relationships
        agent_start_idx = event_types.index("agent_start")
        agent_response_idx = event_types.index("agent_response")
        game_state_idx = event_types.index("game_state")
        choices_idx = event_types.index("choices")
        complete_idx = event_types.index("complete")

        # agent_start must come first
        assert agent_start_idx == 0, (
            f"agent_start should be first, got index {agent_start_idx}"
        )

        # agent_response must come after agent_start
        assert agent_response_idx > agent_start_idx, (
            "agent_response should come after agent_start"
        )

        # game_state must come after agent_response
        assert game_state_idx > agent_response_idx, (
            "game_state should come after agent_response"
        )

        # choices must come after game_state
        assert choices_idx > game_state_idx, "choices should come after game_state"

        # complete must be last
        assert complete_idx == len(event_types) - 1, "complete should be the last event"

    def test_invalid_quest_selection_no_game_state_event(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
        session_state: SessionStateHelper,
    ) -> None:
        """When an invalid quest is selected, NO game_state event is emitted."""
        session_id, pending_quests = session_with_quest_selection

        # Try to select an invalid quest
        action = "Accept: Nonexistent Quest Title"
        events = collect_sse_events(client, session_id, action)

        # Extract event types
        event_types = [e["event"] for e in events]

        # game_state should NOT be emitted for invalid selection
        assert "game_state" not in event_types, (
            f"game_state should NOT be emitted for invalid quest selection. "
            f"Events received: {event_types}"
        )

        # Verify session is still in QUEST_SELECTION phase
        phase = session_state.get_phase(session_id)
        assert phase == GamePhase.QUEST_SELECTION, (
            f"Session should remain in QUEST_SELECTION, got {phase}"
        )


class TestQuestSelectionStreamEdgeCases:
    """Edge case tests for quest selection SSE streaming."""

    def test_quest_selection_by_number_emits_game_state(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """Quest can be selected by number (1, 2, 3) and should emit game_state."""
        session_id, pending_quests = session_with_quest_selection

        # Select quest by number
        events = collect_sse_events(client, session_id, "1")

        # Find game_state event
        game_state_events = [e for e in events if e["event"] == "game_state"]

        assert len(game_state_events) >= 1, (
            "game_state should be emitted when selecting quest by number"
        )

        # Verify correct quest was selected
        active_quest = game_state_events[0]["data"]["active_quest"]
        assert active_quest["title"] == pending_quests[0].title

    def test_quest_selection_by_second_quest(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """Selecting second quest should emit correct quest in game_state."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[1]

        # Select the second quest
        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        # Find game_state event
        game_state_events = [e for e in events if e["event"] == "game_state"]
        assert len(game_state_events) >= 1

        # Verify correct quest was selected
        active_quest = game_state_events[0]["data"]["active_quest"]
        assert active_quest["title"] == quest_to_select.title

    def test_agent_chunks_are_emitted_before_game_state(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """Agent chunks should be streamed before game_state for typewriter effect."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        event_types = [e["event"] for e in events]

        # Should have agent_chunk events
        chunk_indices = [i for i, t in enumerate(event_types) if t == "agent_chunk"]
        assert len(chunk_indices) > 0, "Should have agent_chunk events"

        # game_state should come after all chunks
        game_state_idx = event_types.index("game_state")
        last_chunk_idx = max(chunk_indices)
        assert game_state_idx > last_chunk_idx, (
            "game_state should come after all agent_chunk events"
        )

    def test_game_state_active_quest_objectives_match_original(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """The objectives in game_state should match the selected quest's objectives."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        action = f"Accept: {quest_to_select.title}"
        events = collect_sse_events(client, session_id, action)

        game_state_events = [e for e in events if e["event"] == "game_state"]
        active_quest = game_state_events[0]["data"]["active_quest"]

        # Verify objectives count matches
        assert len(active_quest["objectives"]) == len(quest_to_select.objectives)

        # Verify objective descriptions match
        for i, obj in enumerate(quest_to_select.objectives):
            assert active_quest["objectives"][i]["description"] == obj.description

    def test_complete_event_contains_session_id(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
    ) -> None:
        """The complete event should contain the session_id."""
        session_id, pending_quests = session_with_quest_selection

        action = f"Accept: {pending_quests[0].title}"
        events = collect_sse_events(client, session_id, action)

        complete_events = [e for e in events if e["event"] == "complete"]
        assert len(complete_events) == 1, "Should have exactly one complete event"

        complete_data = complete_events[0]["data"]
        assert "session_id" in complete_data
        assert complete_data["session_id"] == session_id


class TestQuestSelectionPhaseTransition:
    """Tests for phase transition after quest selection via streaming."""

    def test_phase_transitions_to_exploration_after_selection(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
        session_state: SessionStateHelper,
    ) -> None:
        """After successful quest selection, phase should be EXPLORATION."""
        session_id, pending_quests = session_with_quest_selection

        # Before selection - verify in QUEST_SELECTION
        assert session_state.get_phase(session_id) == GamePhase.QUEST_SELECTION

        # Select a quest via streaming
        action = f"Accept: {pending_quests[0].title}"
        _ = collect_sse_events(client, session_id, action)

        # After selection - verify in EXPLORATION
        assert session_state.get_phase(session_id) == GamePhase.EXPLORATION

    def test_active_quest_is_set_after_selection(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
        session_state: SessionStateHelper,
    ) -> None:
        """After quest selection, the active_quest should be set in session."""
        session_id, pending_quests = session_with_quest_selection
        quest_to_select = pending_quests[0]

        # Select a quest
        action = f"Accept: {quest_to_select.title}"
        _ = collect_sse_events(client, session_id, action)

        # Verify active quest is set
        session = session_state.get_session(session_id)
        assert session is not None
        assert session.active_quest is not None
        assert session.active_quest.title == quest_to_select.title

    def test_pending_quest_options_cleared_after_selection(
        self,
        client: TestClient,
        session_with_quest_selection: tuple[str, list[Quest]],
        session_state: SessionStateHelper,
    ) -> None:
        """After quest selection, pending_quest_options should be cleared."""
        session_id, pending_quests = session_with_quest_selection

        # Before selection - verify pending options exist
        session = session_state.get_session(session_id)
        assert session is not None
        assert len(session.pending_quest_options) == 3

        # Select a quest
        action = f"Accept: {pending_quests[0].title}"
        _ = collect_sse_events(client, session_id, action)

        # After selection - verify pending options cleared
        session = session_state.get_session(session_id)
        assert session is not None
        assert len(session.pending_quest_options) == 0
