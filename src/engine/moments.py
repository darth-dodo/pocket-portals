"""Adventure moment utilities for story memory.

Provides functions to format adventure moments for LLM context
and convert Keeper responses to AdventureMoment instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.state.models import AdventureMoment

if TYPE_CHECKING:
    from src.agents.keeper import KeeperResponse


def format_moments_for_context(
    moments: list[AdventureMoment],
    max_count: int = 5,
) -> str:
    """Format adventure moments for inclusion in narrator context.

    Selects the most significant moments and formats them as a summary
    of the story so far, sorted chronologically.

    Args:
        moments: List of adventure moments to format
        max_count: Maximum number of moments to include

    Returns:
        Formatted string for LLM context, empty string if no moments
    """
    if not moments:
        return ""

    # Sort by significance (highest first) and take top moments
    sorted_moments = sorted(
        moments,
        key=lambda m: m.significance,
        reverse=True,
    )
    top_moments = sorted_moments[:max_count]

    # Sort selected moments chronologically for narrative flow
    top_moments.sort(key=lambda m: m.turn)

    lines = ["[STORY SO FAR]"]
    for moment in top_moments:
        lines.append(f"- Turn {moment.turn} ({moment.type}): {moment.summary}")

    return "\n".join(lines)


def build_moment_from_keeper(
    keeper_response: KeeperResponse,
    turn: int,
) -> AdventureMoment | None:
    """Convert KeeperResponse to AdventureMoment if significant.

    Args:
        keeper_response: Response from Keeper's resolve_action_with_moments
        turn: Current adventure turn number

    Returns:
        AdventureMoment if response contains moment data, None otherwise
    """
    if not keeper_response.moment_type or not keeper_response.moment_summary:
        return None

    return AdventureMoment(
        turn=turn,
        type=keeper_response.moment_type,
        summary=keeper_response.moment_summary,
        significance=keeper_response.moment_significance,
    )
