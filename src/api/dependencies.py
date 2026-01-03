"""FastAPI dependencies for Pocket Portals API."""

from typing import Any

from fastapi import Request

from src.engine.pacing import build_pacing_context, format_pacing_hint
from src.state import GameState, SessionManager


def get_session_manager(request: Request) -> SessionManager:
    """FastAPI dependency to get session manager from app state.

    Args:
        request: FastAPI Request object

    Returns:
        SessionManager: The session manager instance from app.state
    """
    return request.app.state.session_manager


async def get_session(request: Request, session_id: str | None) -> GameState:
    """Get existing session or create new one.

    Args:
        request: FastAPI Request object (to access app.state)
        session_id: Optional existing session ID

    Returns:
        GameState: Existing or newly created game state
    """
    sm = get_session_manager(request)
    return await sm.get_or_create_session(session_id)


def build_context(
    history: list[dict[str, str]],
    character_sheet: Any = None,
    character_description: str = "",
    state: GameState | None = None,
    include_pacing: bool = True,
) -> str:
    """Format conversation history and character info for LLM context.

    Args:
        history: List of conversation exchanges
        character_sheet: Optional CharacterSheet with structured character data
        character_description: Optional text description of character
        state: Optional GameState for pacing context
        include_pacing: Whether to include pacing hints (default True)

    Returns:
        Formatted context string for LLM
    """
    lines = []

    # Prepend pacing hint if state is provided and pacing is enabled
    if include_pacing and state and state.adventure_turn > 0:
        pacing_context = build_pacing_context(state)
        pacing_hint = format_pacing_hint(pacing_context)
        lines.append(pacing_hint)
        lines.append("")

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
