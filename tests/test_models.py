"""Tests for game state models."""

import pytest
from pydantic import ValidationError

from src.state.models import GameState


class TestGameState:
    """Test suite for GameState model."""

    def test_creates_with_default_values(self) -> None:
        """GameState should create with sensible defaults."""
        state = GameState(session_id="test-session-123")

        assert state.session_id == "test-session-123"
        assert state.conversation_history == []
        assert state.current_choices == []
        assert state.character_description == ""
        assert state.health_current == 20
        assert state.health_max == 20

    def test_validates_types_correctly(self) -> None:
        """GameState should enforce type validation."""
        # Valid state
        state = GameState(
            session_id="test-123",
            conversation_history=[{"role": "user", "content": "Hello"}],
            current_choices=["Go north", "Go south"],
            character_description="A brave warrior",
            health_current=15,
            health_max=25,
        )

        assert state.session_id == "test-123"
        assert len(state.conversation_history) == 1
        assert len(state.current_choices) == 2
        assert state.character_description == "A brave warrior"
        assert state.health_current == 15
        assert state.health_max == 25

    def test_rejects_invalid_session_id(self) -> None:
        """GameState should require a session_id."""
        with pytest.raises(ValidationError) as exc_info:
            GameState()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("session_id",) for error in errors)

    def test_rejects_negative_health_current(self) -> None:
        """GameState should reject negative current health."""
        with pytest.raises(ValidationError) as exc_info:
            GameState(session_id="test-123", health_current=-1)

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("health_current",) and "cannot be negative" in error["msg"]
            for error in errors
        )

    def test_rejects_health_current_greater_than_max(self) -> None:
        """GameState should reject current health > max health."""
        with pytest.raises(ValidationError) as exc_info:
            GameState(session_id="test-123", health_current=25, health_max=20)

        errors = exc_info.value.errors()
        # Model validators have empty loc tuple
        assert any("cannot exceed" in error["msg"] for error in errors)

    def test_serializes_to_dict_and_back(self) -> None:
        """GameState should serialize to dict and deserialize correctly."""
        original_state = GameState(
            session_id="test-456",
            conversation_history=[
                {"role": "user", "content": "I explore the cave"},
                {"role": "assistant", "content": "You enter the dark cave..."},
            ],
            current_choices=["Light a torch", "Feel your way forward"],
            character_description="An elven ranger",
            health_current=18,
            health_max=20,
        )

        # Serialize to dict
        state_dict = original_state.model_dump()

        assert isinstance(state_dict, dict)
        assert state_dict["session_id"] == "test-456"
        assert len(state_dict["conversation_history"]) == 2

        # Deserialize back to GameState
        restored_state = GameState(**state_dict)

        assert restored_state.session_id == original_state.session_id
        assert (
            restored_state.conversation_history == original_state.conversation_history
        )
        assert restored_state.current_choices == original_state.current_choices
        assert (
            restored_state.character_description == original_state.character_description
        )
        assert restored_state.health_current == original_state.health_current
        assert restored_state.health_max == original_state.health_max

    def test_serializes_to_json_and_back(self) -> None:
        """GameState should serialize to JSON and deserialize correctly."""
        original_state = GameState(
            session_id="test-789",
            character_description="A cunning rogue",
            health_current=12,
            health_max=15,
        )

        # Serialize to JSON
        json_str = original_state.model_dump_json()

        assert isinstance(json_str, str)
        assert "test-789" in json_str

        # Deserialize from JSON
        restored_state = GameState.model_validate_json(json_str)

        assert restored_state.session_id == original_state.session_id
        assert (
            restored_state.character_description == original_state.character_description
        )
        assert restored_state.health_current == original_state.health_current
        assert restored_state.health_max == original_state.health_max
