"""Simple in-memory persistence for CrewAI Flow.

This module provides a simple synchronous persistence implementation
for CrewAI's @persist() decorator, avoiding async complexity.
"""

from __future__ import annotations

import logging
from typing import Any

from crewai.flow.persistence import FlowPersistence
from pydantic import BaseModel

from src.state.models import GameState

logger = logging.getLogger(__name__)


class InMemoryFlowPersistence(FlowPersistence):
    """Simple in-memory persistence for CrewAI Flow.

    Stores game states in a dictionary. No async complexity.
    Suitable for development, testing, and single-process deployments.

    Example:
        >>> persistence = InMemoryFlowPersistence()
        >>> persistence.init_db()
        >>>
        >>> # Used with CrewAI @persist decorator
        >>> @persist(persistence=persistence)
        >>> class GameSessionFlow(Flow[GameState]):
        ...     pass
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._states: dict[str, GameState] = {}
        self._initialized = False

    def init_db(self) -> None:
        """Initialize persistence (no-op for in-memory)."""
        if self._initialized:
            return
        logger.debug("InMemoryFlowPersistence initialized")
        self._initialized = True

    def save_state(
        self,
        flow_uuid: str,
        method_name: str,
        state_data: dict[str, Any] | BaseModel,
    ) -> None:
        """Save flow state.

        Args:
            flow_uuid: Session ID.
            method_name: Method that triggered save.
            state_data: State data to persist.
        """
        # Convert to dict if Pydantic model
        if isinstance(state_data, BaseModel):
            data = state_data.model_dump()
        else:
            data = state_data

        # Ensure session_id is set
        data["session_id"] = flow_uuid

        try:
            game_state = GameState(**data)
            self._states[flow_uuid] = game_state
            logger.debug("Saved state for %s after %s", flow_uuid, method_name)
        except Exception as e:
            logger.error("Failed to save state: %s", e)
            raise ValueError(f"Invalid state data: {e}") from e

    def load_state(self, flow_uuid: str) -> dict[str, Any] | None:
        """Load state by flow UUID.

        Args:
            flow_uuid: Session ID to load.

        Returns:
            State dict or None if not found.
        """
        state = self._states.get(flow_uuid)
        if state is None:
            logger.debug("No state found for %s", flow_uuid)
            return None
        logger.debug("Loaded state for %s", flow_uuid)
        return state.model_dump()

    def exists(self, flow_uuid: str) -> bool:
        """Check if state exists."""
        return flow_uuid in self._states

    def clear(self) -> None:
        """Clear all states (for testing)."""
        self._states.clear()

    @property
    def state_count(self) -> int:
        """Get number of stored states."""
        return len(self._states)
