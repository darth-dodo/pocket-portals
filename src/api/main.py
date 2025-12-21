"""FastAPI application for Pocket Portals."""

import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.narrator import NarratorAgent

load_dotenv()

# Global state
narrator: NarratorAgent | None = None
sessions: dict[str, list[dict[str, str]]] = {}


def get_session(session_id: str | None) -> tuple[str, list[dict[str, str]]]:
    """Get existing session or create new one."""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = str(uuid.uuid4())
    sessions[new_id] = []
    return new_id, sessions[new_id]


def build_context(history: list[dict[str, str]]) -> str:
    """Format conversation history for LLM context."""
    if not history:
        return ""
    lines = ["Previous conversation:"]
    for turn in history:
        lines.append(f"- Player: {turn['action']}")
        lines.append(f"- Narrator: {turn['narrative']}")
    return "\n".join(lines)


class ActionRequest(BaseModel):
    """Request model for player actions."""

    action: str
    session_id: str | None = Field(default=None)


class NarrativeResponse(BaseModel):
    """Response model containing narrative text."""

    narrative: str
    session_id: str


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    environment: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize narrator on startup."""
    global narrator
    if os.getenv("ANTHROPIC_API_KEY"):
        narrator = NarratorAgent()
    yield
    narrator = None


app = FastAPI(
    title="Pocket Portals API",
    description="Solo D&D adventure generator using multi-agent AI",
    version="0.1.0",
    lifespan=lifespan,
)

environment = os.getenv("ENVIRONMENT", "development")
if environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", environment=environment)


@app.post("/action", response_model=NarrativeResponse)
async def process_action(request: ActionRequest) -> NarrativeResponse:
    """Process player action and return narrative response."""
    session_id, history = get_session(request.session_id)

    if narrator is None:
        return NarrativeResponse(
            narrative="The narrator is not available. Check ANTHROPIC_API_KEY.",
            session_id=session_id,
        )

    context = build_context(history)
    narrative = narrator.respond(request.action, context)
    history.append({"action": request.action, "narrative": narrative})

    return NarrativeResponse(narrative=narrative, session_id=session_id)
