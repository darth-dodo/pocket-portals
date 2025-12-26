"""Tests for combat API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client for API."""
    return TestClient(app)


@pytest.fixture
def session_with_character(client: TestClient) -> str:
    """Create a session with a character for testing."""
    # Start a new session with skip_creation to get a default character
    response = client.get("/start?skip_creation=true")
    assert response.status_code == 200
    data = response.json()
    return data["session_id"]


class TestCombatAPI:
    """Test suite for combat API endpoints."""

    def test_start_combat_endpoint_exists(self, client: TestClient) -> None:
        """POST /combat/start endpoint exists."""
        # This should return 404 for session not found, but endpoint itself exists
        # (not a 404 for route not found, which would have different detail message)
        response = client.post(
            "/combat/start", json={"session_id": "nonexistent", "enemy_type": "goblin"}
        )
        # 404 is expected for "session not found", but verify it's not a routing error
        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()

    def test_start_combat_returns_proper_response(
        self, client: TestClient, session_with_character: str
    ) -> None:
        """POST /combat/start returns proper response structure."""
        response = client.post(
            "/combat/start",
            json={"session_id": session_with_character, "enemy_type": "goblin"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "narrative" in data
        assert "combat_state" in data
        assert "initiative_results" in data

        # Narrative should be a non-empty string
        assert isinstance(data["narrative"], str)
        assert len(data["narrative"]) > 0

        # Combat state should have required fields
        combat_state = data["combat_state"]
        assert combat_state["is_active"] is True
        assert len(combat_state["combatants"]) == 2

        # Initiative results should be a list
        assert isinstance(data["initiative_results"], list)
        assert len(data["initiative_results"]) == 2

    def test_start_combat_requires_valid_session(self, client: TestClient) -> None:
        """Invalid session returns 404."""
        response = client.post(
            "/combat/start",
            json={"session_id": "invalid_session_id", "enemy_type": "goblin"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_start_combat_requires_character(self, client: TestClient) -> None:
        """Session without character returns error."""
        # Create a new session without character (don't skip creation)
        start_response = client.get("/start")
        session_id = start_response.json()["session_id"]

        # Try to start combat without completing character creation
        response = client.post(
            "/combat/start", json={"session_id": session_id, "enemy_type": "goblin"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "character" in data["detail"].lower()

    def test_start_combat_invalid_enemy_type(
        self, client: TestClient, session_with_character: str
    ) -> None:
        """Invalid enemy type returns 400."""
        response = client.post(
            "/combat/start",
            json={
                "session_id": session_with_character,
                "enemy_type": "nonexistent_enemy",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_start_combat_validates_request_schema(self, client: TestClient) -> None:
        """Request schema validation works."""
        # Missing required fields
        response = client.post("/combat/start", json={})

        assert response.status_code == 422  # Unprocessable Entity

    def test_start_combat_narrative_describes_initiative(
        self, client: TestClient, session_with_character: str
    ) -> None:
        """Combat start narrative includes initiative information."""
        response = client.post(
            "/combat/start",
            json={"session_id": session_with_character, "enemy_type": "goblin"},
        )

        assert response.status_code == 200
        data = response.json()

        narrative = data["narrative"].lower()
        # Should mention initiative or who goes first
        assert (
            "initiative" in narrative
            or "first" in narrative
            or "goes" in narrative
            or "turn" in narrative
        )

    def test_start_combat_with_different_enemies(
        self, client: TestClient, session_with_character: str
    ) -> None:
        """Can start combat with different enemy types."""
        enemy_types = ["goblin", "bandit", "skeleton", "wolf", "orc"]

        for enemy_type in enemy_types:
            response = client.post(
                "/combat/start",
                json={"session_id": session_with_character, "enemy_type": enemy_type},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["combat_state"]["is_active"] is True

    def test_start_combat_initiative_results_format(
        self, client: TestClient, session_with_character: str
    ) -> None:
        """Initiative results have correct format."""
        response = client.post(
            "/combat/start",
            json={"session_id": session_with_character, "enemy_type": "goblin"},
        )

        assert response.status_code == 200
        data = response.json()

        for result in data["initiative_results"]:
            assert "id" in result
            assert "roll" in result
            assert "modifier" in result
            assert "total" in result
            # Verify total = roll + modifier
            assert result["total"] == result["roll"] + result["modifier"]
