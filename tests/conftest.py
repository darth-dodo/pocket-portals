"""Shared pytest fixtures for Pocket Portals tests."""

import asyncio
from collections.abc import Generator
from typing import Any, TypeVar

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.state import GamePhase, SessionManager
from src.state.backends.memory import InMemoryBackend
from src.state.character import CharacterSheet
from src.state.models import CombatState, GameState

T = TypeVar("T")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client for API with lifespan context.

    This fixture uses the lifespan context manager to properly initialize
    the session backend and manager before tests run.
    """
    # Use lifespan context to initialize app.state
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def session_manager() -> SessionManager:
    """Create a session manager with in-memory backend for unit tests."""
    backend = InMemoryBackend()
    return SessionManager(backend)


def run_async(coro: Any) -> Any:
    """Helper to run async code in sync tests.

    Since TestClient creates its own event loop, we need to use
    asyncio.get_event_loop() or create a new one.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class SessionStateHelper:
    """Helper class to access session state in sync tests.

    This provides sync wrappers around the async SessionManager methods
    for use in sync test functions.
    """

    def __init__(self, sm: SessionManager):
        self._sm = sm

    def get_phase(self, session_id: str) -> GamePhase | None:
        """Get the game phase for a session."""
        result: GamePhase | None = run_async(self._sm.get_phase(session_id))
        return result

    def get_character_sheet(self, session_id: str) -> CharacterSheet | None:
        """Get the character sheet for a session."""
        result: CharacterSheet | None = run_async(
            self._sm.get_character_sheet(session_id)
        )
        return result

    def get_creation_turn(self, session_id: str) -> int:
        """Get the character creation turn for a session."""
        result: int = run_async(self._sm.get_creation_turn(session_id))
        return result

    def get_session(self, session_id: str) -> GameState | None:
        """Get a session by ID."""
        result: GameState | None = run_async(self._sm.get_session(session_id))
        return result

    def set_combat_state(
        self, session_id: str, combat_state: CombatState | None
    ) -> None:
        """Set combat state for a session."""
        run_async(self._sm.set_combat_state(session_id, combat_state))


@pytest.fixture
def session_state(client: TestClient) -> SessionStateHelper:
    """Provide sync access to session state through the app's session manager.

    This fixture provides a helper that wraps the async SessionManager methods
    in sync functions for use in tests that need to verify session state.
    """
    sm = client.app.state.session_manager
    return SessionStateHelper(sm)
