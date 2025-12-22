"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, build_context


@pytest.fixture
def client() -> TestClient:
    """Create test client for API."""
    return TestClient(app)


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
    payload = {}
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


def test_innkeeper_quest_returns_narrative(client: TestClient) -> None:
    """Test GET /innkeeper/quest returns quest introduction."""
    response = client.get("/innkeeper/quest?character=A weary dwarf warrior")
    assert response.status_code == 200
    data = response.json()
    assert "narrative" in data
    assert isinstance(data["narrative"], str)
    assert len(data["narrative"]) > 0


def test_innkeeper_quest_requires_character(client: TestClient) -> None:
    """Test that character query param is required."""
    response = client.get("/innkeeper/quest")
    assert response.status_code == 422


# Keeper Tests


def test_keeper_resolve_returns_result(client: TestClient) -> None:
    """Test POST /keeper/resolve returns mechanical result."""
    response = client.post("/keeper/resolve", json={"action": "swing sword at goblin"})
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert isinstance(data["result"], str)


def test_keeper_resolve_accepts_difficulty(client: TestClient) -> None:
    """Test that difficulty parameter is accepted."""
    response = client.post(
        "/keeper/resolve", json={"action": "pick lock", "difficulty": 15}
    )
    assert response.status_code == 200


def test_keeper_resolve_accepts_session_id(client: TestClient) -> None:
    """Test that session_id provides context."""
    # First create a session
    start = client.get("/start")
    session_id = start.json()["session_id"]

    response = client.post(
        "/keeper/resolve", json={"action": "attack orc", "session_id": session_id}
    )
    assert response.status_code == 200


# Jester Tests


def test_jester_complicate_returns_complication(client: TestClient) -> None:
    """Test POST /jester/complicate returns meta-commentary."""
    response = client.post(
        "/jester/complicate", json={"situation": "The party is searching for treasure"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "complication" in data
    assert isinstance(data["complication"], str)


def test_jester_complicate_accepts_session_id(client: TestClient) -> None:
    """Test that session_id provides context."""
    start = client.get("/start")
    session_id = start.json()["session_id"]

    response = client.post(
        "/jester/complicate",
        json={"situation": "Everyone is standing around", "session_id": session_id},
    )
    assert response.status_code == 200
