"""Shared pytest fixtures for Pocket Portals tests."""

import asyncio
import os
from collections.abc import Generator
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment before any imports that might cache settings
os.environ["ENVIRONMENT"] = "test"

# Clear the settings cache to pick up test environment
from src.config.settings import get_settings

get_settings.cache_clear()

from src.agents.narrator import NarratorResponse  # noqa: E402
from src.agents.quest_designer import (  # noqa: E402
    QuestObjectiveOutput,
    QuestOptionsOutput,
    QuestOutput,
)
from src.api.main import app  # noqa: E402
from src.state import GamePhase, SessionManager  # noqa: E402
from src.state.backends.memory import InMemoryBackend  # noqa: E402
from src.state.character import CharacterSheet  # noqa: E402
from src.state.models import CombatState, GameState  # noqa: E402

T = TypeVar("T")


# ============================================================================
# Mock LLM Calls - Single Point of Control
# ============================================================================


class MockTaskResult:
    """Mock CrewAI TaskOutput that mimics real LLM responses."""

    def __init__(self, raw: str, pydantic: Any = None):
        self.raw = raw
        self.pydantic = pydantic

    def __str__(self) -> str:
        return self.raw


def mock_task_execute_sync(self: Any) -> MockTaskResult:
    """Mock Task.execute_sync() to return deterministic responses.

    This is the single point where all LLM calls are intercepted.
    """
    # Check if this task expects Pydantic output (narrator with choices)
    if hasattr(self, "output_pydantic") and self.output_pydantic == NarratorResponse:
        return MockTaskResult(
            raw="The ancient door creaks open...",
            pydantic=NarratorResponse(
                narrative=(
                    "The ancient door creaks open, revealing a dimly lit chamber. "
                    "Dust motes dance in the flickering torchlight as you step inside. "
                    "The air is thick with the scent of forgotten secrets."
                ),
                choices=[
                    "Examine the dusty tomes on the shelf",
                    "Light another torch from the wall sconce",
                    "Listen for sounds in the darkness ahead",
                ],
            ),
        )

    # Check if this task expects QuestOptionsOutput (quest selection)
    if hasattr(self, "output_pydantic") and self.output_pydantic == QuestOptionsOutput:
        return MockTaskResult(
            raw="Quest options generated...",
            pydantic=QuestOptionsOutput(
                quests=[
                    QuestOutput(
                        title="The Missing Merchant",
                        description="A merchant has gone missing on the forest road.",
                        objectives=[
                            QuestObjectiveOutput(
                                id="obj-1", description="Find the merchant"
                            )
                        ],
                        rewards="50 gold pieces",
                        given_by="Innkeeper Theron",
                        location_hint="The old forest road",
                    ),
                    QuestOutput(
                        title="Goblin Troubles",
                        description="Goblins have been raiding nearby farms.",
                        objectives=[
                            QuestObjectiveOutput(
                                id="obj-2", description="Clear the goblin camp"
                            )
                        ],
                        rewards="75 gold pieces",
                        given_by="Farmer Giles",
                        location_hint="The eastern hills",
                    ),
                    QuestOutput(
                        title="Ancient Artifact",
                        description="Recover an ancient artifact from the old ruins.",
                        objectives=[
                            QuestObjectiveOutput(
                                id="obj-3", description="Explore the ruins"
                            )
                        ],
                        rewards="100 gold pieces and a magic trinket",
                        given_by="Scholar Elara",
                        location_hint="The ancient ruins",
                    ),
                ]
            ),
        )

    # Default narrative response for all other tasks
    return MockTaskResult(
        raw=(
            "The ancient door creaks open, revealing a dimly lit chamber. "
            "Dust motes dance in the flickering torchlight as you step inside."
        )
    )


@pytest.fixture(autouse=True)
def mock_crewai_tasks() -> Generator[MagicMock, None, None]:
    """Mock all CrewAI Task executions to avoid real LLM calls.

    This single fixture intercepts all LLM calls at the Task.execute_sync level,
    making tests fast (~3s vs ~3min) and deterministic.
    """
    with patch(
        "crewai.Task.execute_sync",
        mock_task_execute_sync,
    ) as mock:
        yield mock


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client for API with lifespan context."""
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def session_manager() -> SessionManager:
    """Create a session manager with in-memory backend for unit tests."""
    backend = InMemoryBackend()
    return SessionManager(backend)


def run_async(coro: Any) -> Any:
    """Helper to run async code in sync tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class SessionStateHelper:
    """Helper class to access session state in sync tests."""

    def __init__(self, sm: SessionManager):
        self._sm = sm

    def get_phase(self, session_id: str) -> GamePhase | None:
        result: GamePhase | None = run_async(self._sm.get_phase(session_id))
        return result

    def get_character_sheet(self, session_id: str) -> CharacterSheet | None:
        result: CharacterSheet | None = run_async(
            self._sm.get_character_sheet(session_id)
        )
        return result

    def get_creation_turn(self, session_id: str) -> int:
        result: int = run_async(self._sm.get_creation_turn(session_id))
        return result

    def get_session(self, session_id: str) -> GameState | None:
        result: GameState | None = run_async(self._sm.get_session(session_id))
        return result

    def set_combat_state(
        self, session_id: str, combat_state: CombatState | None
    ) -> None:
        run_async(self._sm.set_combat_state(session_id, combat_state))


@pytest.fixture
def session_state(client: TestClient) -> SessionStateHelper:
    """Provide sync access to session state through the app's session manager."""
    sm = client.app.state.session_manager
    return SessionStateHelper(sm)
