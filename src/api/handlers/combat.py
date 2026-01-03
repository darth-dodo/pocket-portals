"""Combat handlers for Pocket Portals API.

This module contains handler functions for combat-related actions,
including combat initiation, player attacks, and combat resolution.
"""

import logging
from typing import TYPE_CHECKING, Any

from fastapi import Request

from src.api.content_safety import detect_combat_trigger, detect_enemy_type
from src.api.models import NarrativeResponse
from src.engine.combat_manager import CombatManager
from src.state import GamePhase, GameState, SessionManager
from src.state.models import CombatPhaseEnum

if TYPE_CHECKING:
    from src.agents.keeper import KeeperAgent
    from src.agents.narrator import NarratorAgent

logger = logging.getLogger(__name__)


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state.

    Args:
        request: FastAPI Request object

    Returns:
        SessionManager: The session manager instance from app.state
    """
    return request.app.state.session_manager


def build_context(
    history: list[dict[str, str]],
    character_sheet: Any = None,
    character_description: str = "",
) -> str:
    """Format conversation history and character info for LLM context.

    Args:
        history: List of conversation exchanges
        character_sheet: Optional CharacterSheet with structured character data
        character_description: Optional text description of character

    Returns:
        Formatted context string for LLM
    """
    lines = []

    # Include character information for continuity
    if character_sheet:
        lines.append("Character:")
        lines.append(f"- Name: {character_sheet.name}")
        lines.append(f"- Race: {character_sheet.race.value}")
        lines.append(f"- Class: {character_sheet.character_class.value}")
        if character_sheet.backstory:
            lines.append(f"- Backstory: {character_sheet.backstory}")
        lines.append("")

    # Include character description if no sheet but description exists
    elif character_description:
        lines.append(f"Character: {character_description}")
        lines.append("")

    # Include conversation history
    if history:
        lines.append("Previous conversation:")
        for turn in history:
            lines.append(f"- Player: {turn['action']}")
            lines.append(f"- Narrator: {turn['narrative']}")

    return "\n".join(lines)


async def handle_combat_action(
    request: Request,
    state: GameState,
    action: str,
    keeper: "KeeperAgent | None",
    narrator: "NarratorAgent | None",
    combat_manager: CombatManager,
) -> NarrativeResponse:
    """Handle combat-related actions in the main action flow.

    This function:
    1. Auto-starts combat if combat keywords detected and not in combat
    2. Routes to combat handler if already in combat
    3. Handles combat end transitions back to exploration

    Args:
        request: FastAPI Request object (to access app.state)
        state: Current game state
        action: Player's action text
        keeper: Keeper agent instance
        narrator: Narrator agent instance
        combat_manager: Combat manager instance

    Returns:
        NarrativeResponse with combat results
    """
    sm = get_session_manager(request)

    # Case 1: Already in combat - route to combat action handler
    if state.combat_state and state.combat_state.is_active:
        return await _handle_active_combat(
            request, state, action, sm, keeper, combat_manager
        )

    # Case 2: Combat keywords detected but not in combat - auto-start combat
    if detect_combat_trigger(action):
        return await _handle_combat_start(
            request, state, action, sm, keeper, narrator, combat_manager
        )

    # Case 3: No combat - this shouldn't be called, but return safe fallback
    narrative = "The adventure continues..."
    choices = ["Look around", "Wait", "Leave"]
    await sm.set_choices(state.session_id, choices)
    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
    )


async def _handle_active_combat(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
    keeper: "KeeperAgent | None",
    combat_manager: CombatManager,
) -> NarrativeResponse:
    """Handle actions when combat is already active.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action text
        sm: Session manager instance
        keeper: Keeper agent instance
        combat_manager: Combat manager instance

    Returns:
        NarrativeResponse with combat round results
    """
    action_lower = action.lower()

    # Handle flee action
    if "flee" in action_lower or "run" in action_lower or "escape" in action_lower:
        return await _handle_flee(request, state, action, sm)

    # Validate character sheet
    if not state.character_sheet:
        narrative = "You need a character to engage in combat!"
        choices = ["Look around", "Wait", "Leave"]
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    combat_state = state.combat_state
    if combat_state is None:
        # Safety check - should not happen
        narrative = "No active combat found."
        choices = ["Look around", "Wait", "Leave"]
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Validate it's player's turn
    if combat_state.phase != CombatPhaseEnum.PLAYER_TURN:
        narrative = "Wait for your turn in combat!"
        choices = ["Wait", "Assess the situation"]
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Execute player attack
    if keeper:
        player_result = keeper.resolve_player_attack(
            combat_state, state.character_sheet
        )
    else:
        player_result = combat_manager.execute_player_attack(
            combat_state, state.character_sheet
        )

    player_message = (
        combat_manager.format_attack_result(player_result)
        if combat_manager
        else player_result["log_entry"]
    )

    # Check if enemy defeated
    enemy_hp = player_result.get("enemy_hp", 0)
    if enemy_hp <= 0:
        return await _handle_victory(request, state, action, sm, player_message)

    # Enemy turn
    if keeper:
        enemy_result = keeper.resolve_enemy_attack(combat_state)
    else:
        enemy_result = combat_manager.execute_enemy_turn(combat_state)

    enemy_message = (
        combat_manager.format_attack_result(enemy_result)
        if combat_manager
        else enemy_result["log_entry"]
    )

    # Check if player defeated
    player_hp = enemy_result.get("player_hp", state.character_sheet.hit_points)
    if player_hp <= 0:
        return await _handle_defeat(
            request, state, action, sm, player_message, enemy_message
        )

    # Combat continues
    full_narrative = f"{player_message}\n\n{enemy_message}"
    choices = ["Attack again", "Defend", "Flee"]
    await sm.add_exchange(state.session_id, action, full_narrative)
    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=full_narrative,
        session_id=state.session_id,
        choices=choices,
    )


async def _handle_flee(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
) -> NarrativeResponse:
    """Handle player fleeing from combat.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action text
        sm: Session manager instance

    Returns:
        NarrativeResponse for successful flee
    """
    await sm.set_combat_state(state.session_id, None)
    await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

    narrative = (
        "You turn and flee from the battle! "
        "The enemy doesn't pursue as you make your escape."
    )
    choices = ["Look around", "Catch your breath", "Continue onward"]
    await sm.add_exchange(state.session_id, action, narrative)
    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
    )


async def _handle_victory(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
    player_message: str,
) -> NarrativeResponse:
    """Handle combat victory.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action text
        sm: Session manager instance
        player_message: Message describing player's winning attack

    Returns:
        NarrativeResponse for victory
    """
    await sm.set_combat_state(state.session_id, None)
    await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

    victory_narrative = (
        f"{player_message}\n\n"
        f"Victory! The enemy falls defeated. "
        f"You stand victorious and can continue your adventure."
    )
    choices = ["Search the area", "Rest briefly", "Continue onward"]
    await sm.add_exchange(state.session_id, action, victory_narrative)
    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=victory_narrative,
        session_id=state.session_id,
        choices=choices,
    )


async def _handle_defeat(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
    player_message: str,
    enemy_message: str,
) -> NarrativeResponse:
    """Handle combat defeat.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action text
        sm: Session manager instance
        player_message: Message describing player's last attack
        enemy_message: Message describing enemy's finishing blow

    Returns:
        NarrativeResponse for defeat
    """
    await sm.set_combat_state(state.session_id, None)
    await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

    defeat_narrative = (
        f"{player_message}\n\n{enemy_message}\n\n"
        f"Defeat! You fall unconscious. "
        f"When you awaken, you find yourself back at the tavern, bruised but alive."
    )
    choices = ["Recover", "Plan your next move", "Leave the tavern"]
    await sm.add_exchange(state.session_id, action, defeat_narrative)
    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=defeat_narrative,
        session_id=state.session_id,
        choices=choices,
    )


async def _handle_combat_start(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
    keeper: "KeeperAgent | None",
    narrator: "NarratorAgent | None",
    combat_manager: CombatManager,
) -> NarrativeResponse:
    """Handle starting a new combat encounter.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action that triggered combat
        sm: Session manager instance
        keeper: Keeper agent instance
        narrator: Narrator agent instance
        combat_manager: Combat manager instance

    Returns:
        NarrativeResponse with combat initiation narrative
    """
    # Validate character sheet
    if not state.character_sheet:
        narrative = "You need a character to engage in combat!"
        choices = ["Look around", "Wait", "Leave"]
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Detect enemy type from action
    enemy_type = detect_enemy_type(action)

    # Start combat using keeper
    try:
        if keeper:
            combat_state, initiative_results = keeper.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=enemy_type,
            )
        else:
            combat_state, initiative_results = combat_manager.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=enemy_type,
            )
    except ValueError:
        # Invalid enemy type, fall back to goblin
        if keeper:
            combat_state, initiative_results = keeper.start_combat(
                character_sheet=state.character_sheet,
                enemy_type="goblin",
            )
        else:
            combat_state, initiative_results = combat_manager.start_combat(
                character_sheet=state.character_sheet,
                enemy_type="goblin",
            )

    # Format initiative
    if keeper:
        initiative_narrative = keeper.format_initiative_result(initiative_results)
    else:
        initiative_narrative = "Initiative rolled. Combat begins!"

    # Get scene description
    scene_narrative = ""
    if narrator and combat_state.enemy_template:
        enemy_desc = combat_state.enemy_template.description
        enemy_name = combat_state.enemy_template.name

        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
        )

        scene_prompt = (
            f"A {enemy_name} appears! {enemy_desc}. "
            f"Describe this combat encounter dramatically in 2-3 sentences."
        )

        scene_narrative = narrator.respond(action=scene_prompt, context=context)
    else:
        enemy_name = (
            combat_state.enemy_template.name if combat_state.enemy_template else "enemy"
        )
        scene_narrative = f"A {enemy_name} appears before you!"

    # Combine narratives
    full_narrative = f"{scene_narrative}\n\n{initiative_narrative}"

    # Store combat state
    await sm.set_combat_state(state.session_id, combat_state)
    await sm.set_phase(state.session_id, GamePhase.COMBAT)

    choices = ["Attack", "Defend", "Flee"]
    await sm.add_exchange(state.session_id, action, full_narrative)
    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=full_narrative,
        session_id=state.session_id,
        choices=choices,
    )
