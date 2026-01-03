"""Combat endpoints for Pocket Portals API.

Handles /combat/start and /combat/action endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.dependencies import build_context, get_session_manager
from src.api.models import (
    CombatActionRequest,
    CombatActionResponse,
    StartCombatRequest,
    StartCombatResponse,
)
from src.api.rate_limiting import require_rate_limit
from src.state import GamePhase
from src.state.models import CombatPhaseEnum

router = APIRouter(prefix="/combat", tags=["combat"])


def _get_agents(request: Request) -> dict[str, Any]:
    """Get agent instances from app.state.

    Args:
        request: FastAPI Request object with access to app.state

    Returns:
        Dict with narrator, keeper, and combat_manager instances.
    """
    from src.engine.combat_manager import CombatManager

    return {
        "narrator": getattr(request.app.state, "narrator", None),
        "keeper": getattr(request.app.state, "keeper", None),
        "combat_manager": CombatManager(),  # Stateless, can be created fresh
    }


@router.post("/start", response_model=StartCombatResponse)
async def start_combat(
    request: Request,
    combat_request: StartCombatRequest,
    _rate_limit: None = Depends(require_rate_limit("combat")),
) -> StartCombatResponse:
    """Start a new combat encounter.

    Args:
        request: FastAPI Request object
        combat_request: Combat start request with session_id and enemy_type

    Returns:
        StartCombatResponse with narrative, combat state, and initiative results

    Raises:
        HTTPException: 404 if session not found, 400 if no character or invalid enemy
    """
    agents = _get_agents(request)
    narrator = agents["narrator"]
    keeper = agents["keeper"]
    combat_manager = agents["combat_manager"]

    # Get session manager from app state
    sm = get_session_manager(request)

    # 1. Get session - validate that this specific session_id exists
    state = await sm.get_session(combat_request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate character exists
    if not state.character_sheet:
        raise HTTPException(
            status_code=400,
            detail="Character sheet required. Complete character creation first.",
        )

    # 3. Use Keeper to start combat (Keeper handles all combat mechanics)
    # Fallback to combat_manager if keeper not available (e.g., in tests without API key)
    try:
        if keeper:
            combat_state, initiative_results = keeper.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=combat_request.enemy_type,
            )
        else:
            # Fallback for testing/development without API key
            combat_state, initiative_results = combat_manager.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=combat_request.enemy_type,
            )
    except ValueError as e:
        # Invalid enemy type
        raise HTTPException(status_code=400, detail=str(e)) from e

    # 4. Get Keeper to format initiative results
    if keeper:
        initiative_narrative = keeper.format_initiative_result(initiative_results)
    else:
        # Fallback formatting
        initiative_narrative = "Initiative rolled. Combat begins!"

    # 5. Get Narrator to describe combat scene
    scene_narrative = ""
    if narrator and combat_state.enemy_template:
        enemy_desc = combat_state.enemy_template.description
        enemy_name = combat_state.enemy_template.name

        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
        )

        # Ask narrator to describe the encounter
        scene_prompt = (
            f"A {enemy_name} appears! {enemy_desc}. "
            f"Describe this combat encounter dramatically in 2-3 sentences."
        )

        scene_narrative = narrator.respond(action=scene_prompt, context=context)
    else:
        # Fallback if narrator not available
        enemy_name = (
            combat_state.enemy_template.name if combat_state.enemy_template else "enemy"
        )
        scene_narrative = f"A {enemy_name} appears before you!"

    # Combine narratives
    full_narrative = f"{scene_narrative}\n\n{initiative_narrative}"

    # 6. Store combat state in session
    state.combat_state = combat_state
    state.phase = GamePhase.COMBAT

    # 7. Return response
    return StartCombatResponse(
        narrative=full_narrative,
        combat_state=combat_state,
        initiative_results=initiative_results,
    )


@router.post("/action", response_model=CombatActionResponse)
async def combat_action(
    request: Request,
    combat_action_request: CombatActionRequest,
    _rate_limit: None = Depends(require_rate_limit("combat")),
) -> CombatActionResponse:
    """Execute a combat action.

    Args:
        request: FastAPI Request object
        combat_action_request: Combat action request with session_id and action

    Returns:
        CombatActionResponse with result, message, updated combat state, and end status

    Raises:
        HTTPException: 404 if session not found, 400 if no active combat or not player turn
    """
    agents = _get_agents(request)
    narrator = agents["narrator"]
    keeper = agents["keeper"]
    combat_manager = agents["combat_manager"]

    # Get session manager from app state
    sm = get_session_manager(request)

    # 1. Validate session and active combat
    state = await sm.get_session(combat_action_request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not state.combat_state or not state.combat_state.is_active:
        raise HTTPException(status_code=400, detail="No active combat")

    if not state.character_sheet:
        raise HTTPException(status_code=400, detail="No character sheet found")

    combat_state = state.combat_state

    # 2. Validate it's player's turn
    if combat_state.phase != CombatPhaseEnum.PLAYER_TURN:
        raise HTTPException(
            status_code=400,
            detail=f"Not player's turn. Current phase: {combat_state.phase}",
        )

    # 3. Execute player action via keeper
    action = combat_action_request.action.lower()
    fled = False

    if action == "attack":
        # Use keeper to resolve attack
        if keeper:
            player_result = keeper.resolve_player_attack(
                combat_state, state.character_sheet
            )
        else:
            # Fallback to combat_manager
            player_result = combat_manager.execute_player_attack(
                combat_state, state.character_sheet
            )

        # Format the message
        player_message = (
            combat_manager.format_attack_result(player_result)
            if combat_manager
            else player_result["log_entry"]
        )
    elif action == "defend":
        # Execute defend action
        player_result = combat_manager.execute_defend(
            combat_state, state.character_sheet
        )
        player_message = player_result["log_entry"]
    elif action == "flee":
        # Execute flee action
        player_result = combat_manager.execute_flee(combat_state, state.character_sheet)
        player_message = player_result["log_entry"]

        if player_result["success"]:
            # Successful flee - combat ends, player escaped
            fled = True
            combat_ended = True
            victory = None  # Neither victory nor defeat
            narrative = None  # No narrator summary for flee
        # If flee failed, free_attack is already logged in combat_log
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    # 4. Check if combat ended after player action (for attack/defend)
    if action != "flee" or not fled:
        combat_ended, result = combat_manager.check_combat_end(combat_state)
    else:
        # Fled successfully - already handled above
        combat_ended = True
        result = None

    victory = None
    narrative = None

    if combat_ended and not fled and result is not None:
        # Combat ended - clean up and get narrative
        victory = result == "victory"
        combat_manager.end_combat(combat_state, result)

        # Get narrator summary (ONE LLM call for entire combat)
        if narrator and combat_state.enemy_template:
            narrative = narrator.summarize_combat(
                combat_log=combat_state.combat_log,
                victory=victory,
                enemy_name=combat_state.enemy_template.name,
                player_name=state.character_sheet.name,
            )

    # 5. If combat continues, execute enemy turn
    enemy_message = ""
    if not combat_ended:
        # Execute enemy attack
        if keeper:
            enemy_result = keeper.resolve_enemy_attack(combat_state)
        else:
            enemy_result = combat_manager.execute_enemy_turn(combat_state)

        enemy_message = (
            combat_manager.format_attack_result(enemy_result)
            if combat_manager
            else enemy_result["log_entry"]
        )

        # Check if combat ended after enemy attack
        combat_ended, result = combat_manager.check_combat_end(combat_state)

        if combat_ended and result is not None:
            # Combat ended - clean up and get narrative
            victory = result == "victory"
            combat_manager.end_combat(combat_state, result)

            # Get narrator summary (ONE LLM call for entire combat)
            if narrator and combat_state.enemy_template:
                narrative = narrator.summarize_combat(
                    combat_log=combat_state.combat_log,
                    victory=victory,
                    enemy_name=combat_state.enemy_template.name,
                    player_name=state.character_sheet.name,
                )

    # 6. Combine messages
    full_message = player_message
    if enemy_message:
        full_message += f"\n\n{enemy_message}"

    # 7. Update session combat state
    await sm.set_combat_state(combat_action_request.session_id, combat_state)

    # If combat ended, also update phase back to EXPLORATION
    if combat_ended:
        await sm.set_phase(combat_action_request.session_id, GamePhase.EXPLORATION)

    # 8. Return response
    return CombatActionResponse(
        success=True,
        result=player_result,
        message=full_message,
        narrative=narrative,
        combat_state=combat_state,
        combat_ended=combat_ended,
        victory=victory,
        fled=fled,
    )
