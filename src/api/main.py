"""FastAPI application for Pocket Portals."""

import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()


class ActionRequest(BaseModel):
    """Request model for player actions."""

    action: str


class NarrativeResponse(BaseModel):
    """Response model containing narrative text."""

    narrative: str


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    environment: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Lifespan context manager for startup/shutdown events."""
    # Startup: validate required environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set")

    yield

    # Shutdown: cleanup if needed
    pass


# Create FastAPI application
app = FastAPI(
    title="Pocket Portals API",
    description="Solo D&D adventure generator using multi-agent AI",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for development
environment = os.getenv("ENVIRONMENT", "development")
if environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        environment=environment,
    )


@app.post("/action", response_model=NarrativeResponse)
async def process_action(request: ActionRequest) -> NarrativeResponse:
    """
    Process player action and return narrative response.

    Args:
        request: ActionRequest containing the player's action

    Returns:
        NarrativeResponse with generated narrative text
    """
    # Placeholder response - will be replaced with agent integration
    narrative = (
        f"You attempt to '{request.action}'. "
        "The ancient portal shimmers with ethereal light, "
        "awaiting your next move..."
    )

    return NarrativeResponse(narrative=narrative)
