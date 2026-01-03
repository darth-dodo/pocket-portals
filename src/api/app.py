"""FastAPI application factory for Pocket Portals.

This module provides the application factory pattern for creating
configured FastAPI instances with all middleware and routes.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agents.character_builder import CharacterBuilderAgent
from src.agents.character_interviewer import CharacterInterviewerAgent
from src.agents.epilogue import EpilogueAgent
from src.agents.innkeeper import InnkeeperAgent
from src.agents.jester import JesterAgent
from src.agents.keeper import KeeperAgent
from src.agents.narrator import NarratorAgent
from src.agents.quest_designer import QuestDesignerAgent
from src.api.routes import mount_static_files, router
from src.config.settings import settings
from src.engine import TurnExecutor
from src.state import SessionManager
from src.state.backends import create_backend

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize backend, session manager, and agents on startup.

    This lifespan context manager handles:
    - Creating the session backend (memory or Redis)
    - Initializing the SessionManager
    - Creating agent instances if API key is available
    - Cleaning up resources on shutdown

    Args:
        app: FastAPI application instance

    Yields:
        None (agents are stored in app.state)
    """
    # Initialize session backend and manager
    backend = await create_backend()
    app.state.backend = backend
    app.state.session_manager = SessionManager(backend)

    # Initialize agents if API key available
    if os.getenv("ANTHROPIC_API_KEY"):
        app.state.narrator = NarratorAgent()
        app.state.innkeeper = InnkeeperAgent()
        app.state.keeper = KeeperAgent()
        app.state.jester = JesterAgent()
        app.state.character_interviewer = CharacterInterviewerAgent()
        app.state.character_builder = CharacterBuilderAgent()
        app.state.quest_designer = QuestDesignerAgent()
        app.state.epilogue_agent = EpilogueAgent()
        app.state.turn_executor = TurnExecutor(
            narrator=app.state.narrator,
            keeper=app.state.keeper,
            jester=app.state.jester,
        )
        logger.info("Agents initialized successfully")
    else:
        app.state.narrator = None
        app.state.innkeeper = None
        app.state.keeper = None
        app.state.jester = None
        app.state.character_interviewer = None
        app.state.character_builder = None
        app.state.quest_designer = None
        app.state.epilogue_agent = None
        app.state.turn_executor = None
        logger.warning("ANTHROPIC_API_KEY not set - agents not initialized")

    yield

    # Shutdown: close backend connection if applicable
    if hasattr(backend, "close"):
        await backend.close()

    # Clear agent references
    app.state.narrator = None
    app.state.innkeeper = None
    app.state.keeper = None
    app.state.jester = None
    app.state.character_interviewer = None
    app.state.character_builder = None
    app.state.quest_designer = None
    app.state.epilogue_agent = None
    app.state.turn_executor = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This factory function creates a new FastAPI instance with:
    - Application metadata (title, description, version)
    - Lifespan context manager for agent initialization
    - CORS middleware configured from settings
    - All API routes included

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Pocket Portals API",
        description="Solo D&D adventure generator using multi-agent AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware: allow all origins in development, use configured origins otherwise
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            ["*"] if settings.environment == "development" else settings.cors_origins
        ),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=(
            ["*"]
            if settings.environment == "development"
            else settings.cors_allow_methods
        ),
        allow_headers=(
            ["*"]
            if settings.environment == "development"
            else settings.cors_allow_headers
        ),
    )

    # Include all API routes
    app.include_router(router)

    # Mount static files
    mount_static_files(app)

    return app
