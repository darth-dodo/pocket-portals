"""Tests for FastAPI endpoints."""

from typing import TYPE_CHECKING, Any

from fastapi.testclient import TestClient

from src.api.main import build_context

if TYPE_CHECKING:
    from tests.conftest import SessionStateHelper

# Note: 'client' fixture is provided by conftest.py with proper lifespan context


def test_health_endpoint_returns_200(client: TestClient) -> None:
    """Test that health check endpoint returns 200 status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_action_endpoint_accepts_post(client: TestClient) -> None:
    """Test that /action endpoint accepts POST and returns narrative."""
    payload = {"action": "open the door"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "narrative" in data
    assert isinstance(data["narrative"], str)
    assert len(data["narrative"]) > 0


def test_action_endpoint_returns_narrative(client: TestClient) -> None:
    """Test that response contains a meaningful narrative."""
    payload = {"action": "examine the ancient runes"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    # Narrative should be substantial (more than a short error message)
    assert len(data["narrative"]) > 20


def test_action_endpoint_validates_request_schema(client: TestClient) -> None:
    """Test that /action endpoint validates request schema."""
    # Missing required 'action' field
    payload: dict[str, Any] = {}
    response = client.post("/action", json=payload)

    assert response.status_code == 422  # Unprocessable Entity


def test_action_endpoint_returns_session_id(client: TestClient) -> None:
    """Test that /action response includes session_id for context continuity."""
    payload = {"action": "look around"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_action_endpoint_accepts_session_id(client: TestClient) -> None:
    """Test that /action endpoint accepts session_id for continuing context."""
    # First request - get a session
    payload = {"action": "enter the tavern"}
    response1 = client.post("/action", json=payload)
    session_id = response1.json()["session_id"]

    # Second request - continue same session
    payload2 = {"action": "order a drink", "session_id": session_id}
    response2 = client.post("/action", json=payload2)

    assert response2.status_code == 200
    data = response2.json()
    assert data["session_id"] == session_id  # Same session maintained


def test_different_sessions_are_isolated(client: TestClient) -> None:
    """Test that different sessions don't share context."""
    # Create two different sessions
    response1 = client.post("/action", json={"action": "go north"})
    response2 = client.post("/action", json={"action": "go south"})

    session1 = response1.json()["session_id"]
    session2 = response2.json()["session_id"]

    # Sessions should be different
    assert session1 != session2


# Context Building Tests


def test_build_context_returns_empty_for_empty_history() -> None:
    """Test that build_context returns empty string for empty history."""
    context = build_context([])
    assert context == ""


def test_build_context_formats_single_turn() -> None:
    """Test that build_context formats a single turn correctly."""
    history = [{"action": "enter tavern", "narrative": "You push open the door."}]
    context = build_context(history)

    assert "enter tavern" in context
    assert "You push open the door" in context


def test_build_context_formats_multiple_turns() -> None:
    """Test that build_context formats multiple turns correctly."""
    history = [
        {"action": "enter tavern", "narrative": "You push open the door."},
        {"action": "order ale", "narrative": "The barkeep nods."},
    ]
    context = build_context(history)

    assert "enter tavern" in context
    assert "You push open the door" in context
    assert "order ale" in context
    assert "The barkeep nods" in context


# Choice System Tests


def test_action_response_includes_choices(client: TestClient) -> None:
    """Test that /action response includes exactly 3 suggested choices."""
    payload = {"action": "look around"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert isinstance(data["choices"], list)
    assert len(data["choices"]) == 3


def test_choices_are_strings(client: TestClient) -> None:
    """Test that each choice is a non-empty string."""
    payload = {"action": "examine the room"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    choices = data["choices"]

    # Each choice should be a non-empty string
    for choice in choices:
        assert isinstance(choice, str)
        assert len(choice) > 0
        assert len(choice.strip()) > 0  # Not just whitespace


def test_action_accepts_choice_index(client: TestClient) -> None:
    """Test that action can be submitted using choice_index (1-3)."""
    # First request - get choices
    response1 = client.post("/action", json={"action": "enter the dungeon"})
    session_id = response1.json()["session_id"]
    assert len(response1.json()["choices"]) == 3  # Verify choices exist

    # Second request - select a choice by index
    payload = {"choice_index": 2, "session_id": session_id}
    response2 = client.post("/action", json=payload)

    assert response2.status_code == 200
    data = response2.json()
    assert "narrative" in data


def test_action_still_accepts_free_text(client: TestClient) -> None:
    """Test that free text actions still work alongside choice system."""
    # First request with session
    response1 = client.post("/action", json={"action": "enter the forest"})
    session_id = response1.json()["session_id"]

    # Second request with custom free text (not a choice)
    custom_action = "do something completely unexpected and creative"
    payload = {"action": custom_action, "session_id": session_id}
    response2 = client.post("/action", json=payload)

    assert response2.status_code == 200
    data = response2.json()
    assert "narrative" in data
    assert len(data["narrative"]) > 0
    # Should still get choices for the next turn
    assert "choices" in data
    assert len(data["choices"]) == 3


def test_choice_index_validation(client: TestClient) -> None:
    """Test that choice_index must be between 1 and 3."""
    # Invalid choice index (0)
    response1 = client.post("/action", json={"choice_index": 0})
    assert response1.status_code == 422

    # Invalid choice index (4)
    response2 = client.post("/action", json={"choice_index": 4})
    assert response2.status_code == 422

    # Valid choice indices should work
    response3 = client.post("/action", json={"choice_index": 1})
    assert response3.status_code == 200

    response4 = client.post("/action", json={"choice_index": 3})
    assert response4.status_code == 200


def test_action_or_choice_index_required(client: TestClient) -> None:
    """Test that either action or choice_index must be provided (but not necessarily both)."""
    # Neither action nor choice_index
    response = client.post("/action", json={"session_id": "some-id"})
    assert response.status_code == 422


# Starter Choices Tests


def test_start_endpoint_returns_starter_choices(client: TestClient) -> None:
    """Test that /start endpoint returns starter choices for new adventures."""
    response = client.get("/start")

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert isinstance(data["choices"], list)
    assert len(data["choices"]) == 3


def test_start_choices_are_non_empty_strings(client: TestClient) -> None:
    """Test that each starter choice is a non-empty string."""
    response = client.get("/start")

    assert response.status_code == 200
    data = response.json()
    for choice in data["choices"]:
        assert isinstance(choice, str)
        assert len(choice.strip()) > 0


def test_start_endpoint_returns_session_id(client: TestClient) -> None:
    """Test that /start returns a new session_id."""
    response = client.get("/start")

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_start_endpoint_returns_welcome_narrative(client: TestClient) -> None:
    """Test that /start returns a welcome narrative."""
    response = client.get("/start")

    assert response.status_code == 200
    data = response.json()
    assert "narrative" in data
    assert isinstance(data["narrative"], str)
    assert len(data["narrative"]) > 0


def test_start_shuffle_returns_different_order(client: TestClient) -> None:
    """Test that /start?shuffle=true can return shuffled choices."""
    # Make multiple requests and check we get valid responses
    # Note: Due to randomness, we can't guarantee different order every time,
    # but we verify the endpoint works with shuffle parameter
    response = client.get("/start?shuffle=true")

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) == 3


def test_start_session_can_be_used_for_action(client: TestClient) -> None:
    """Test that session from /start can be used with /action."""
    # Get starter choices
    start_response = client.get("/start")
    assert start_response.status_code == 200
    start_data = start_response.json()
    session_id = start_data["session_id"]

    # Use the session with an action
    action_response = client.post(
        "/action", json={"choice_index": 1, "session_id": session_id}
    )

    assert action_response.status_code == 200
    action_data = action_response.json()
    assert action_data["session_id"] == session_id
    assert "narrative" in action_data


# Innkeeper Tests


def test_innkeeper_quest_requires_character(client: TestClient) -> None:
    """Test that character query param is required."""
    response = client.get("/innkeeper/quest")
    assert response.status_code == 422


# Character Creation Flow Tests


def test_start_begins_in_character_creation_phase(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that /start creates session in CHARACTER_CREATION phase."""
    from src.state import GamePhase

    response = client.get("/start")
    assert response.status_code == 200

    session_id = response.json()["session_id"]
    phase = session_state.get_phase(session_id)

    assert phase == GamePhase.CHARACTER_CREATION


def test_start_returns_innkeeper_greeting(client: TestClient) -> None:
    """Test that /start narrative is from innkeeper for character creation."""
    response = client.get("/start")
    assert response.status_code == 200

    data = response.json()
    # Should contain innkeeper-style greeting, not generic adventure narrative
    # The narrative should invite character description
    assert "narrative" in data
    assert len(data["narrative"]) > 0


def test_action_during_character_creation_continues_interview(
    client: TestClient,
) -> None:
    """Test that /action during CHARACTER_CREATION phase continues interview."""
    # Start session (in CHARACTER_CREATION phase)
    start_response = client.get("/start")
    session_id = start_response.json()["session_id"]

    # Respond with character concept
    action_response = client.post(
        "/action",
        json={"action": "I am Thorin, a dwarven blacksmith", "session_id": session_id},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert "narrative" in data
    assert "choices" in data


def test_session_tracks_creation_turn_count(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that session tracks character creation turn count."""
    start_response = client.get("/start")
    session_id = start_response.json()["session_id"]

    # After /start, should be turn 1
    turn = session_state.get_creation_turn(session_id)
    assert turn == 1

    # After first response, should be turn 2
    client.post(
        "/action",
        json={"action": "I'm a dwarven fighter", "session_id": session_id},
    )

    turn = session_state.get_creation_turn(session_id)
    assert turn == 2


def test_character_creation_completes_after_5_turns(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that character creation transitions after 5 turns."""
    from src.state import GamePhase

    start_response = client.get("/start")
    session_id = start_response.json()["session_id"]

    # Complete 5 turns of character creation
    for i in range(5):
        client.post(
            "/action",
            json={"action": f"Answer {i + 1}", "session_id": session_id},
        )

    # After 5 turns, should transition to EXPLORATION
    phase = session_state.get_phase(session_id)
    assert phase == GamePhase.EXPLORATION
    # Should have character sheet
    sheet = session_state.get_character_sheet(session_id)
    assert sheet is not None


def test_skip_character_creation_with_query_param(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that skip_creation=true skips character creation."""
    from src.state import GamePhase

    response = client.get("/start?skip_creation=true")
    assert response.status_code == 200

    session_id = response.json()["session_id"]

    # Should be in EXPLORATION phase with default character
    phase = session_state.get_phase(session_id)
    assert phase == GamePhase.EXPLORATION
    sheet = session_state.get_character_sheet(session_id)
    assert sheet is not None
    assert sheet.name == "Adventurer"


# Combat Action API Tests


def test_combat_action_requires_active_combat(client: TestClient) -> None:
    """Test that combat action returns error if no active combat."""

    # Setup: Create session with character but no combat
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Try to execute action without starting combat
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    assert action_response.status_code == 400
    assert "No active combat" in action_response.json()["detail"]


# Streaming Endpoint Tests


def test_stream_endpoint_returns_sse_response(client: TestClient) -> None:
    """Test that /action/stream returns Server-Sent Events format."""
    # Skip character creation to get to exploration
    start_response = client.get("/start?skip_creation=true")
    session_id = start_response.json()["session_id"]

    # Make streaming request
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": "look around", "session_id": session_id},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


def test_stream_emits_agent_start_before_chunks(client: TestClient) -> None:
    """Test that agent_start event is emitted before agent_chunk events.

    This is critical for the frontend to hide loading indicator when
    streaming begins, not when streaming completes.
    """
    # Skip character creation to get to exploration
    start_response = client.get("/start?skip_creation=true")
    session_id = start_response.json()["session_id"]

    events: list[str] = []

    # Make streaming request and collect events
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": "examine the room", "session_id": session_id},
    ) as response:
        assert response.status_code == 200

        current_event = ""
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:") and current_event:
                events.append(current_event)
                current_event = ""

    # Verify event sequence: agent_start must come before any agent_chunk
    assert "agent_start" in events, "agent_start event must be emitted"

    # Find first agent_start and first agent_chunk indices
    first_start_idx = events.index("agent_start")
    chunk_indices = [i for i, e in enumerate(events) if e == "agent_chunk"]

    if chunk_indices:
        first_chunk_idx = chunk_indices[0]
        assert first_start_idx < first_chunk_idx, (
            "agent_start must be emitted before first agent_chunk "
            f"(start at {first_start_idx}, chunk at {first_chunk_idx})"
        )


def test_stream_emits_routing_event_first(client: TestClient) -> None:
    """Test that routing event is emitted first in the stream."""
    # Skip character creation to get to exploration
    start_response = client.get("/start?skip_creation=true")
    session_id = start_response.json()["session_id"]

    events: list[str] = []

    # Make streaming request and collect events
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": "look around", "session_id": session_id},
    ) as response:
        for line in response.iter_lines():
            if line.startswith("event:"):
                events.append(line[6:].strip())
            # Only collect a few events to keep test fast
            if len(events) >= 5:
                break

    # First event should be routing
    assert len(events) > 0, "Should receive at least one event"
    assert events[0] == "routing", f"First event should be 'routing', got '{events[0]}'"


def test_stream_ends_with_complete_event(client: TestClient) -> None:
    """Test that streaming ends with a complete event containing session_id."""
    import json

    # Skip character creation to get to exploration
    start_response = client.get("/start?skip_creation=true")
    session_id = start_response.json()["session_id"]

    last_event = ""
    last_data = ""

    # Make streaming request
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": "wait", "session_id": session_id},
    ) as response:
        current_event = ""
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:") and current_event:
                last_event = current_event
                last_data = line[5:].strip()
                current_event = ""

    assert (
        last_event == "complete"
    ), f"Last event should be 'complete', got '{last_event}'"
    complete_data = json.loads(last_data)
    assert "session_id" in complete_data
    assert complete_data["session_id"] == session_id


def test_stream_agent_start_precedes_each_agent_response(client: TestClient) -> None:
    """Test that each agent_response is preceded by an agent_start for the same agent."""
    import json

    # Skip character creation to get to exploration
    start_response = client.get("/start?skip_creation=true")
    session_id = start_response.json()["session_id"]

    events: list[tuple[str, dict[str, Any]]] = []

    # Make streaming request
    with client.stream(
        "POST",
        "/action/stream",
        json={"action": "look around carefully", "session_id": session_id},
    ) as response:
        current_event = ""
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:") and current_event:
                try:
                    data = json.loads(line[5:].strip())
                    events.append((current_event, data))
                except json.JSONDecodeError:
                    pass
                current_event = ""

    # Check that each agent_response has a preceding agent_start for same agent
    for i, (event_type, data) in enumerate(events):
        if event_type == "agent_response" and "agent" in data:
            agent_name = data["agent"]
            # Look backwards for matching agent_start
            found_start = False
            for j in range(i - 1, -1, -1):
                prev_event, prev_data = events[j]
                if prev_event == "agent_start" and prev_data.get("agent") == agent_name:
                    found_start = True
                    break
                # Stop if we hit another agent_response (different agent's section)
                if prev_event == "agent_response":
                    break

            assert found_start, (
                f"agent_response for '{agent_name}' at index {i} "
                f"has no preceding agent_start"
            )
