"""Agent endpoints for Pocket Portals API.

Handles /innkeeper, /keeper, and /jester endpoints for direct agent access.
"""

from typing import Any

from fastapi import APIRouter, Query, Request

from src.api.dependencies import build_context, get_session
from src.api.models import (
    ComplicateRequest,
    ComplicateResponse,
    QuestResponse,
    ResolveRequest,
    ResolveResponse,
)

router = APIRouter(tags=["agents"])


def _get_agents(request: Request) -> dict[str, Any]:
    """Get agent instances from app.state.

    Args:
        request: FastAPI Request object with access to app.state

    Returns:
        Dict with innkeeper, keeper, jester agent instances.
    """
    return {
        "innkeeper": getattr(request.app.state, "innkeeper", None),
        "keeper": getattr(request.app.state, "keeper", None),
        "jester": getattr(request.app.state, "jester", None),
    }


@router.get("/innkeeper/quest", response_model=QuestResponse)
async def get_quest(
    request: Request,
    character: str = Query(
        ..., description="Character description for quest introduction"
    ),
) -> QuestResponse:
    """Get a quest introduction from the innkeeper.

    Args:
        request: FastAPI Request object
        character: Description of the adventurer receiving the quest
    """
    agents = _get_agents(request)
    innkeeper = agents["innkeeper"]

    if innkeeper is None:
        return QuestResponse(
            narrative="The innkeeper is not available. Check ANTHROPIC_API_KEY."
        )

    narrative = innkeeper.introduce_quest(character_description=character)
    return QuestResponse(narrative=narrative)


@router.post("/keeper/resolve", response_model=ResolveResponse)
async def resolve_action(
    request: Request,
    resolve_request: ResolveRequest,
) -> ResolveResponse:
    """Resolve game mechanics for a player action.

    Args:
        request: FastAPI Request object
        resolve_request: Action resolution request with action, difficulty, and optional session_id
    """
    agents = _get_agents(request)
    keeper = agents["keeper"]

    if keeper is None:
        return ResolveResponse(
            result="The keeper is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if resolve_request.session_id:
        state = await get_session(request, resolve_request.session_id)
        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
            character_description=state.character_description,
        )

    result = keeper.resolve_action(
        action=resolve_request.action,
        context=context,
        difficulty=resolve_request.difficulty,
    )
    return ResolveResponse(result=result)


@router.post("/jester/complicate", response_model=ComplicateResponse)
async def add_complication(
    request: Request,
    complicate_request: ComplicateRequest,
) -> ComplicateResponse:
    """Add a complication or meta-commentary to a situation.

    Args:
        request: FastAPI Request object
        complicate_request: Complication request with situation and optional session_id
    """
    agents = _get_agents(request)
    jester = agents["jester"]

    if jester is None:
        return ComplicateResponse(
            complication="The jester is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if complicate_request.session_id:
        state = await get_session(request, complicate_request.session_id)
        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
            character_description=state.character_description,
        )

    complication = jester.add_complication(
        situation=complicate_request.situation, context=context
    )
    return ComplicateResponse(complication=complication)
