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


def test_combat_action_attack_success(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test POST /combat/action with attack returns result."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    combat_response = client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )
    assert combat_response.status_code == 200

    # Force player turn for deterministic testing
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        state.combat_state.turn_order = ["player", "enemy"]
        state.combat_state.current_turn_index = 0
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute attack action
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    assert action_response.status_code == 200
    data = action_response.json()

    assert data["success"] is True
    assert "result" in data
    assert "message" in data
    assert "combat_state" in data
    assert "combat_ended" in data
    assert isinstance(data["combat_ended"], bool)


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


def test_combat_action_requires_player_turn(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that combat action returns error if not player's turn."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Manually set combat phase to ENEMY_TURN
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        state.combat_state.phase = CombatPhaseEnum.ENEMY_TURN
        session_state.set_combat_state(session_id, state.combat_state)

    # Try to execute action during enemy turn
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    assert action_response.status_code == 400
    assert "Not player's turn" in action_response.json()["detail"]


def test_enemy_attacks_after_player(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that enemy turn executed after player action."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Force player turn for deterministic testing
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        state.combat_state.turn_order = ["player", "enemy"]
        state.combat_state.current_turn_index = 0
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute player attack
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    assert action_response.status_code == 200
    data = action_response.json()

    # If combat didn't end, message should contain both player and enemy attacks
    if not data["combat_ended"]:
        message = data["message"]
        # Should have multiple attack entries (player + enemy)
        assert "Round" in message
        # Should have returned to player turn
        assert data["combat_state"]["phase"] == "player_turn"


def test_combat_ends_on_enemy_death(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that combat ends when enemy HP reaches 0."""
    from unittest.mock import patch

    from src.state.models import CombatPhaseEnum
    from src.utils.dice import DiceRoll

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Get combat state and set enemy HP to 1
    state = session_state.get_session(session_id)
    assert state is not None, "Session should exist"
    assert state.combat_state is not None, "Combat state should exist"

    enemy = next((c for c in state.combat_state.combatants if c.id == "enemy"), None)
    assert enemy is not None, "Enemy combatant should exist"
    enemy.current_hp = 1
    enemy.armor_class = 5  # Low AC to guarantee hit

    # Force player turn for deterministic testing
    state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
    state.combat_state.turn_order = ["player", "enemy"]
    state.combat_state.current_turn_index = 0
    session_state.set_combat_state(session_id, state.combat_state)

    # Mock dice rolls to guarantee hit (roll 20) and damage (10)
    with patch("src.engine.combat_manager.DiceRoller.roll") as mock_roll:
        mock_roll.side_effect = [
            DiceRoll(notation="1d20", rolls=[20], modifier=0, total=20),  # Attack roll
            DiceRoll(notation="1d8+2", rolls=[8], modifier=2, total=10),  # Damage roll
        ]

        # Execute attack - should kill enemy
        action_response = client.post(
            "/combat/action",
            json={"session_id": session_id, "action": "attack"},
        )

    data = action_response.json()
    assert data["combat_ended"] is True
    assert data["victory"] is True
    # Combat should end when enemy HP reaches 0
    assert data["combat_state"]["is_active"] is False


def test_combat_ends_on_player_death(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that combat ends when player HP reaches 0."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Get combat state and set player HP to 1, enemy damage high
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        player = next(
            (c for c in state.combat_state.combatants if c.id == "player"), None
        )
        if player:
            player.current_hp = 1
            player.armor_class = 5  # Low AC so enemy will hit

        # Make player miss by setting enemy AC very high
        enemy = next(
            (c for c in state.combat_state.combatants if c.id == "enemy"), None
        )
        if enemy:
            enemy.armor_class = 30  # Player will miss

        # Force player turn for deterministic testing
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        state.combat_state.turn_order = ["player", "enemy"]
        state.combat_state.current_turn_index = 0
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute attack - player will miss, enemy will hit and kill
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    data = action_response.json()
    assert data["combat_ended"] is True
    assert data["victory"] is False
    # Combat should end when player HP reaches 0
    assert data["combat_state"]["is_active"] is False


def test_combat_end_includes_narrative(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that combat end response includes narrative summary."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Set enemy HP to 1 and low AC to guarantee kill
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        enemy = next(
            (c for c in state.combat_state.combatants if c.id == "enemy"), None
        )
        if enemy:
            enemy.current_hp = 1
            enemy.armor_class = 5  # Player will hit

        # Force player turn for deterministic testing
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        state.combat_state.turn_order = ["player", "enemy"]
        state.combat_state.current_turn_index = 0
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute attack - should end combat
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "attack"},
    )

    data = action_response.json()
    assert data["combat_ended"] is True
    assert data["victory"] is True

    # Check that narrative field exists and is populated
    assert "narrative" in data
    # If narrator is available, narrative should be a non-empty string
    # If not available (no API key), it can be None
    if data["narrative"] is not None:
        assert isinstance(data["narrative"], str)
        assert len(data["narrative"]) > 0


def test_defend_action_works(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that defend action causes enemy to attack with disadvantage."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Force player turn
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        state.combat_state.turn_order = ["player", "enemy"]
        state.combat_state.current_turn_index = 0
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute defend action
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "defend"},
    )

    data = action_response.json()
    assert data["success"] is True
    assert "defensive stance" in data["message"].lower()
    assert data["combat_ended"] is False
    # Enemy attack should mention disadvantage
    assert "disadvantage" in data["message"].lower()
    # After enemy attacks, defending flag should be reset
    assert data["combat_state"]["player_defending"] is False


def test_flee_action_success(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that flee action can succeed."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Try flee multiple times until we get a success
    for _ in range(100):
        # Reset combat state
        state = session_state.get_session(session_id)
        if state and state.combat_state:
            state.combat_state.is_active = True
            state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
            state.combat_state.turn_order = ["player", "enemy"]
            state.combat_state.current_turn_index = 0
            session_state.set_combat_state(session_id, state.combat_state)

        # Execute flee action
        action_response = client.post(
            "/combat/action",
            json={"session_id": session_id, "action": "flee"},
        )

        data = action_response.json()
        assert data["success"] is True

        if data["fled"]:
            # Successful flee
            assert "escaped" in data["message"].lower()
            assert data["combat_ended"] is True
            assert data["victory"] is None
            assert data["narrative"] is None
            assert data["combat_state"]["is_active"] is False
            break


def test_flee_action_failure(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that flee action can fail with free attack."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Try flee multiple times until we get a failure
    for _ in range(100):
        # Reset combat state
        state = session_state.get_session(session_id)
        if state and state.combat_state:
            state.combat_state.is_active = True
            state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
            state.combat_state.turn_order = ["player", "enemy"]
            state.combat_state.current_turn_index = 0
            session_state.set_combat_state(session_id, state.combat_state)

        # Execute flee action
        action_response = client.post(
            "/combat/action",
            json={"session_id": session_id, "action": "flee"},
        )

        data = action_response.json()
        assert data["success"] is True

        if not data["fled"]:
            # Failed flee
            assert "failed" in data["message"].lower()
            assert data["combat_ended"] is False
            assert data["combat_state"]["is_active"] is True
            # Should mention advantage attack
            assert "advantage" in data["message"].lower()
            break


def test_invalid_action_returns_error(
    client: TestClient, session_state: "SessionStateHelper"
) -> None:
    """Test that unknown action returns error."""
    from src.state.models import CombatPhaseEnum

    # Setup: Create session with character
    response = client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # Start combat
    client.post(
        "/combat/start",
        json={"session_id": session_id, "enemy_type": "goblin"},
    )

    # Force player turn
    state = session_state.get_session(session_id)
    if state and state.combat_state:
        state.combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        session_state.set_combat_state(session_id, state.combat_state)

    # Execute invalid action
    action_response = client.post(
        "/combat/action",
        json={"session_id": session_id, "action": "dance"},
    )

    assert action_response.status_code == 400
    data = action_response.json()
    assert "unknown action" in data["detail"].lower()
