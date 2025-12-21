"""FastAPI application for Pocket Portals."""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from src.agents.narrator import NarratorAgent

load_dotenv()

# Global state
narrator: NarratorAgent | None = None
sessions: dict[str, list[dict[str, str]]] = {}
session_choices: dict[str, list[str]] = {}  # Store last choices per session


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

    action: str | None = Field(default=None)
    choice_index: int | None = Field(default=None, ge=1, le=3)
    session_id: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_action_or_choice(self) -> "ActionRequest":
        """Ensure either action or choice_index is provided."""
        if self.action is None and self.choice_index is None:
            raise ValueError("Either 'action' or 'choice_index' must be provided")
        return self


class NarrativeResponse(BaseModel):
    """Response model containing narrative text."""

    narrative: str
    session_id: str
    choices: list[str] = Field(default_factory=lambda: ["Look around", "Wait", "Leave"])


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

    # Resolve action from choice_index or direct action
    if request.choice_index is not None:
        # Use stored choice from previous response
        choices = session_choices.get(session_id, ["Look around", "Wait", "Leave"])
        action = choices[request.choice_index - 1]  # Convert 1-indexed to 0-indexed
    else:
        action = request.action or ""

    if narrator is None:
        choices = ["Look around", "Wait", "Leave"]
        session_choices[session_id] = choices
        return NarrativeResponse(
            narrative="The narrator is not available. Check ANTHROPIC_API_KEY.",
            session_id=session_id,
            choices=choices,
        )

    context = build_context(history)
    narrative = narrator.respond(action, context)
    history.append({"action": action, "narrative": narrative})

    # Generate contextual choices (simple default for now - YAGNI)
    choices = [
        "Investigate further",
        "Talk to someone nearby",
        "Move to a new location",
    ]
    session_choices[session_id] = choices

    return NarrativeResponse(
        narrative=narrative, session_id=session_id, choices=choices
    )


# Static file serving
# Get the project root directory (pocket-portals/)
project_root = Path(__file__).parent.parent.parent
static_dir = project_root / "static"

# Serve index.html at root path
@app.get("/")
async def read_root() -> FileResponse:
    """Serve the index.html file."""
    return FileResponse(static_dir / "index.html")


# Mount static files for all other static assets
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
