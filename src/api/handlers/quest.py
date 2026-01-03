"""Quest selection handlers for Pocket Portals API.

This module contains handler functions for quest selection flow,
including quest option parsing and quest activation.
"""

import logging
from typing import TYPE_CHECKING

from fastapi import Request

from src.api.models import NarrativeResponse
from src.state import GamePhase, GameState, SessionManager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state.

    Args:
        request: FastAPI Request object

    Returns:
        SessionManager: The session manager instance from app.state
    """
    return request.app.state.session_manager


async def handle_quest_selection(
    request: Request,
    state: GameState,
    action: str,
) -> NarrativeResponse:
    """Handle actions during quest selection phase.

    Args:
        request: FastAPI Request object (to access app.state)
        state: Current game state
        action: Player's action (quest selection)

    Returns:
        NarrativeResponse with quest acceptance narrative or reprompt
    """
    sm = get_session_manager(request)

    # Parse the action to find which quest was selected
    selected_quest = None

    # Check if action starts with "Accept: " (from clicking a choice)
    if action.startswith("Accept: "):
        quest_title = action[8:]  # Remove "Accept: " prefix
        for quest in state.pending_quest_options:
            if quest.title == quest_title:
                selected_quest = quest
                break

    # Check if action is a number (1, 2, or 3)
    elif action.strip() in ("1", "2", "3"):
        index = int(action.strip()) - 1
        if 0 <= index < len(state.pending_quest_options):
            selected_quest = state.pending_quest_options[index]

    # If no valid selection, stay in QUEST_SELECTION and reprompt
    if selected_quest is None:
        choices = [f"Accept: {quest.title}" for quest in state.pending_quest_options]
        narrative = (
            "The innkeeper raises an eyebrow. 'Those are the opportunities I know of. "
            "Which one interests you?'"
        )
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Valid selection - activate the quest
    await sm.set_active_quest(state.session_id, selected_quest)
    await sm.clear_pending_quest_options(state.session_id)
    await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

    # Build narrative about accepting the quest
    narrative = (
        f"You've accepted the quest: **{selected_quest.title}**\n\n"
        f"{selected_quest.description}\n\n"
        f"**Objective:** {selected_quest.objectives[0].description if selected_quest.objectives else 'Complete the quest'}\n\n"
        f"The innkeeper nods approvingly. 'Good choice. May fortune favor your journey.'"
    )

    # Generate exploration choices based on the quest
    if selected_quest.location_hint:
        choices = [
            f"Head toward {selected_quest.location_hint}",
            "Ask the innkeeper for more details",
            "Prepare supplies before leaving",
        ]
    else:
        choices = [
            "Begin the quest immediately",
            "Ask where to start",
            "Gather information first",
        ]

    await sm.set_choices(state.session_id, choices)
    await sm.add_exchange(state.session_id, action, narrative)

    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
    )
