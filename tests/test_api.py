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


def test_action_endpoint_includes_action_context(client: TestClient) -> None:
    """Test that response narrative includes context from the action."""
    payload = {"action": "examine the ancient runes"}
    response = client.post("/action", json=payload)

    assert response.status_code == 200
    data = response.json()
    # Placeholder response should include the action
    assert "examine the ancient runes" in data["narrative"]


def test_action_endpoint_validates_request_schema(client: TestClient) -> None:
    """Test that /action endpoint validates request schema."""
    # Missing required 'action' field
    payload = {}
    response = client.post("/action", json=payload)

    assert response.status_code == 422  # Unprocessable Entity
