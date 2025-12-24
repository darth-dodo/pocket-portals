"""FastAPI application for Pocket Portals."""

import asyncio
import json
import os
import random
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from sse_starlette.sse import EventSourceResponse

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
    result = await turn_executor.execute_async(
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


@app.post("/action/stream")
async def process_action_stream(request: ActionRequest) -> EventSourceResponse:
    """Process player action with streaming response via Server-Sent Events.

    Streams agent responses as they complete, providing real-time feedback.
    Events sent:
    - agent_start: When an agent begins processing
    - agent_response: When an agent completes with its response
    - choices: Final choices for next action
    - complete: Signal that streaming is done
    - error: If something goes wrong
    """
    state = get_session(request.session_id)

    # Resolve action from choice_index or direct action
    if request.choice_index is not None:
        choices = state.current_choices or ["Look around", "Wait", "Leave"]
        action = choices[request.choice_index - 1]
    else:
        action = request.action or ""

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        """Generate SSE events as agents respond."""
        try:
            if turn_executor is None:
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {"message": "Narrator not available. Check ANTHROPIC_API_KEY."}
                    ),
                }
                return

            # Route to appropriate agents
            routing = agent_router.route(
                action=action,
                phase=state.phase,
                recent_agents=state.recent_agents,
            )

            # Signal which agents will respond
            agents_list = routing.agents.copy()
            if routing.include_jester:
                agents_list.append("jester")

            yield {
                "event": "routing",
                "data": json.dumps({"agents": agents_list, "reason": routing.reason}),
            }

            # Build initial context from conversation history
            accumulated_context = build_context(state.conversation_history)

            # Get agent instances
            agents = {
                "narrator": narrator,
                "keeper": keeper,
                "jester": jester,
            }

            # Agent labels for context building
            agent_labels = {
                "narrator": "Narrator",
                "keeper": "Keeper (Game Mechanics)",
                "jester": "Jester",
            }

            narrative_parts = []

            # Execute each agent and stream responses
            for agent_name in routing.agents:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": agent_name}),
                }

                # Run agent in executor to not block
                agent = agents.get(agent_name)
                if agent:
                    # Capture current context for closure
                    current_context = accumulated_context

                    # Execute synchronously but in a thread pool
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda ctx=current_context, a=agent: a.respond(
                            action=action, context=ctx
                        ),
                    )

                    narrative_parts.append(response)

                    # Accumulate context for subsequent agents
                    label = agent_labels.get(agent_name, agent_name.title())
                    if accumulated_context:
                        accumulated_context = (
                            f"{accumulated_context}\n\n[{label} just said]: {response}"
                        )
                    else:
                        accumulated_context = f"[{label} just said]: {response}"

                    yield {
                        "event": "agent_response",
                        "data": json.dumps({"agent": agent_name, "content": response}),
                    }

            # Execute jester if included (sees all previous responses)
            if routing.include_jester and jester:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": "jester"}),
                }

                # Capture current context for closure
                current_context = accumulated_context

                loop = asyncio.get_event_loop()
                jester_response = await loop.run_in_executor(
                    None,
                    lambda ctx=current_context: jester.respond(
                        action=action, context=ctx
                    ),
                )

                narrative_parts.append(jester_response)

                yield {
                    "event": "agent_response",
                    "data": json.dumps({"agent": "jester", "content": jester_response}),
                }

            # Combine narrative
            full_narrative = "\n\n".join(narrative_parts)

            # Generate choices (ask narrator for contextual choices)
            choices = ["Look around", "Wait", "Leave"]  # Default
            if narrator and full_narrative:
                try:
                    choice_prompt = (
                        f"Based on this scene:\n\n{full_narrative}\n\n"
                        "Suggest exactly 3 short action choices (max 6 words each) "
                        "the player could take next. Format as a simple numbered list:\n"
                        "1. [action]\n2. [action]\n3. [action]"
                    )
                    loop = asyncio.get_event_loop()
                    choice_response = await loop.run_in_executor(
                        None, lambda: narrator.respond(action=choice_prompt, context="")
                    )

                    # Parse choices
                    parsed = []
                    for line in choice_response.strip().split("\n"):
                        line = line.strip()
                        if (
                            line
                            and len(line) > 2
                            and line[0].isdigit()
                            and line[1] in ".):"
                        ):
                            choice = line[2:].strip().lstrip(".): ")
                            if choice:
                                parsed.append(choice)

                    if len(parsed) >= 3:
                        choices = parsed[:3]
                except Exception:
                    pass

            yield {
                "event": "choices",
                "data": json.dumps({"choices": choices}),
            }

            # Update session state
            session_manager.add_exchange(state.session_id, action, full_narrative)
            session_manager.update_recent_agents(state.session_id, routing.agents)
            session_manager.set_choices(state.session_id, choices)

            yield {
                "event": "complete",
                "data": json.dumps({"session_id": state.session_id}),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())


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
