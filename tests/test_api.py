"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


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
