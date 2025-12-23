"""FastAPI application for Pocket Portals."""

import os
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from src.agents.innkeeper import InnkeeperAgent
from src.agents.jester import JesterAgent
from src.agents.keeper import KeeperAgent
from src.agents.narrator import NarratorAgent
from src.engine import AgentRouter, TurnExecutor
from src.state import GameState, SessionManager

load_dotenv()

# Global state
narrator: NarratorAgent | None = None
innkeeper: InnkeeperAgent | None = None
keeper: KeeperAgent | None = None
jester: JesterAgent | None = None
session_manager = SessionManager()
agent_router = AgentRouter()
turn_executor: TurnExecutor | None = None

# Starter choices pool - adventure hooks to begin the journey
STARTER_CHOICES_POOL = [
    "Enter the mysterious tavern",
    "Explore the dark forest path",
    "Investigate the ancient ruins",
    "Follow the hooded stranger",
    "Approach the glowing portal",
    "Descend into the forgotten dungeon",
    "Board the departing airship",
    "Answer the distress signal",
    "Accept the wizard's quest",
]

WELCOME_NARRATIVE = (
    "The mists part before you, revealing crossroads where destiny awaits. "
    "Three paths shimmer with possibility, each promising adventure, danger, "
    "and glory. Choose wisely, brave soul, for your legend begins with a single step..."
)


def get_session(session_id: str | None) -> GameState:
    """Get existing session or create new one."""
    return session_manager.get_or_create_session(session_id)


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


class QuestResponse(BaseModel):
    """Response model for innkeeper quest introduction."""

    narrative: str


class ResolveRequest(BaseModel):
    """Request model for keeper action resolution."""

    action: str
    difficulty: int = Field(default=12, ge=1, le=30)
    session_id: str | None = Field(default=None)


class ResolveResponse(BaseModel):
    """Response model for keeper action resolution."""

    result: str


class ComplicateRequest(BaseModel):
    """Request model for jester complication."""

    situation: str
    session_id: str | None = Field(default=None)


class ComplicateResponse(BaseModel):
    """Response model for jester complication."""

    complication: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize agents on startup."""
    global narrator, innkeeper, keeper, jester, turn_executor
    if os.getenv("ANTHROPIC_API_KEY"):
        narrator = NarratorAgent()
        innkeeper = InnkeeperAgent()
        keeper = KeeperAgent()
        jester = JesterAgent()
        turn_executor = TurnExecutor(
            narrator=narrator,
            keeper=keeper,
            jester=jester,
        )
    yield
    narrator = None
    innkeeper = None
    keeper = None
    jester = None
    turn_executor = None


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


@app.get("/start", response_model=NarrativeResponse)
async def start_adventure(
    shuffle: bool = Query(default=False, description="Shuffle the starter choices"),
    character: str = Query(
        default="", description="Optional character description for personalization"
    ),
) -> NarrativeResponse:
    """Start a new adventure with starter choices.

    Returns 3 starter choices from the pool to begin the adventure.
    Use shuffle=true to randomize which choices are presented.
    Optionally provide a character description for personalized narrative.
    """
    # Create new session
    state = get_session(None)

    # Select 3 choices from the pool
    if shuffle:
        choices = random.sample(STARTER_CHOICES_POOL, 3)
    else:
        # Default: first 3 choices for consistency
        choices = STARTER_CHOICES_POOL[:3]

    # Store choices and character description in session state
    session_manager.set_choices(state.session_id, choices)
    if character:
        session_manager.set_character_description(state.session_id, character)

    return NarrativeResponse(
        narrative=WELCOME_NARRATIVE,
        session_id=state.session_id,
        choices=choices,
    )


@app.post("/action", response_model=NarrativeResponse)
async def process_action(request: ActionRequest) -> NarrativeResponse:
    """Process player action and return narrative response."""
    state = get_session(request.session_id)

    # Resolve action from choice_index or direct action
    if request.choice_index is not None:
        # Use stored choice from session state
        choices = state.current_choices or ["Look around", "Wait", "Leave"]
        action = choices[request.choice_index - 1]  # Convert 1-indexed to 0-indexed
    else:
        action = request.action or ""

    if turn_executor is None:
        choices = ["Look around", "Wait", "Leave"]
        session_manager.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative="The narrator is not available. Check ANTHROPIC_API_KEY.",
            session_id=state.session_id,
            choices=choices,
        )

    # Route to appropriate agents based on phase and action
    routing = agent_router.route(
        action=action,
        phase=state.phase,
        recent_agents=state.recent_agents,
    )

    # Execute agents and get aggregated result
    context = build_context(state.conversation_history)
    result = turn_executor.execute(
        action=action,
        routing=routing,
        context=context,
    )

    # Store exchange in session (auto-limits to 20)
    session_manager.add_exchange(state.session_id, action, result.narrative)

    # Update recent agents for Jester cooldown tracking
    session_manager.update_recent_agents(state.session_id, routing.agents)

    # Use choices from turn result
    session_manager.set_choices(state.session_id, result.choices)

    return NarrativeResponse(
        narrative=result.narrative, session_id=state.session_id, choices=result.choices
    )


@app.get("/innkeeper/quest", response_model=QuestResponse)
async def get_quest(
    character: str = Query(
        ..., description="Character description for quest introduction"
    ),
) -> QuestResponse:
    """Get a quest introduction from the innkeeper.

    Args:
        character: Description of the adventurer receiving the quest
    """
    if innkeeper is None:
        return QuestResponse(
            narrative="The innkeeper is not available. Check ANTHROPIC_API_KEY."
        )

    narrative = innkeeper.introduce_quest(character_description=character)
    return QuestResponse(narrative=narrative)


@app.post("/keeper/resolve", response_model=ResolveResponse)
async def resolve_action(request: ResolveRequest) -> ResolveResponse:
    """Resolve game mechanics for a player action.

    Args:
        request: Action resolution request with action, difficulty, and optional session_id
    """
    if keeper is None:
        return ResolveResponse(
            result="The keeper is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if request.session_id:
        state = get_session(request.session_id)
        context = build_context(state.conversation_history)

    result = keeper.resolve_action(
        action=request.action, context=context, difficulty=request.difficulty
    )
    return ResolveResponse(result=result)


@app.post("/jester/complicate", response_model=ComplicateResponse)
async def add_complication(request: ComplicateRequest) -> ComplicateResponse:
    """Add a complication or meta-commentary to a situation.

    Args:
        request: Complication request with situation and optional session_id
    """
    if jester is None:
        return ComplicateResponse(
            complication="The jester is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if request.session_id:
        state = get_session(request.session_id)
        context = build_context(state.conversation_history)

    complication = jester.add_complication(situation=request.situation, context=context)
    return ComplicateResponse(complication=complication)


# Static file serving
# Get the project root directory (pocket-portals/)
project_root = Path(__file__).parent.parent.parent
static_dir = project_root / "static"


@app.get("/")
async def read_root() -> FileResponse:
    """Serve the index.html file."""
    return FileResponse(static_dir / "index.html")


# Mount static files at /static for CSS, JS, images, etc.
# Note: We don't mount at "/" because it would override API routes like /start
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
