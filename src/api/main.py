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
from src.state import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    GamePhase,
    GameState,
    SessionManager,
)

load_dotenv()

# Content safety filter - redirects inappropriate input
BLOCKED_PATTERNS = [
    # Self-harm
    "hurt myself",
    "kill myself",
    "harm myself",
    "cut myself",
    "suicide",
    "self-harm",
    "self harm",
    "end my life",
    "end it all",
    # Sexual content
    "sex",
    "seduce",
    "kiss",
    "romance",
    "make love",
    "naked",
    "undress",
    "sexual",
    "erotic",
    "intimate",
    # Violence/torture
    "torture",
    "mutilate",
    "rape",
    "abuse",
    "molest",
    # Hate speech
    "slur",
    "racist",
    "nazi",
]

SAFE_REDIRECT = "take a deep breath and focus on the adventure ahead"


def filter_content(action: str) -> str:
    """Filter inappropriate content from player actions.

    Args:
        action: Player's action text

    Returns:
        Original action if safe, or redirect action if inappropriate
    """
    action_lower = action.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in action_lower:
            return SAFE_REDIRECT
    return action


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

# Character creation narrative - innkeeper greeting
CHARACTER_CREATION_NARRATIVE = (
    "You push through the tavern door, escaping the cold night. The warmth of the fire "
    "and the smell of ale wash over you. Behind the bar, a weathered innkeeper looks up "
    "with knowing eyes. 'Well now,' he says, wiping a mug, 'another soul seeking adventure. "
    "Before I point you toward trouble, tell me - who are you, traveler?'"
)

CHARACTER_CREATION_CHOICES = [
    "Describe your character",
    "Tell your backstory",
    "Skip and start adventuring",
]


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
    skip_creation: bool = Query(
        default=False, description="Skip character creation and start with default"
    ),
) -> NarrativeResponse:
    """Start a new adventure with starter choices.

    Returns 3 starter choices from the pool to begin the adventure.
    Use shuffle=true to randomize which choices are presented.
    Optionally provide a character description for personalized narrative.
    Use skip_creation=true to skip character creation with a default character.
    """
    # Create new session
    state = get_session(None)

    if skip_creation:
        # Create default character and skip to exploration
        default_character = CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )
        session_manager.set_character_sheet(state.session_id, default_character)
        session_manager.set_phase(state.session_id, GamePhase.EXPLORATION)

        # Select 3 choices from the adventure pool
        if shuffle:
            choices = random.sample(STARTER_CHOICES_POOL, 3)
        else:
            choices = STARTER_CHOICES_POOL[:3]

        session_manager.set_choices(state.session_id, choices)
        if character:
            session_manager.set_character_description(state.session_id, character)

        return NarrativeResponse(
            narrative=WELCOME_NARRATIVE,
            session_id=state.session_id,
            choices=choices,
        )

    # Start character creation flow
    session_manager.set_creation_turn(state.session_id, 1)
    session_manager.set_choices(state.session_id, CHARACTER_CREATION_CHOICES)

    if character:
        session_manager.set_character_description(state.session_id, character)

    return NarrativeResponse(
        narrative=CHARACTER_CREATION_NARRATIVE,
        session_id=state.session_id,
        choices=CHARACTER_CREATION_CHOICES,
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

    # Apply content safety filter
    action = filter_content(action)

    # Handle CHARACTER_CREATION phase specially
    if state.phase == GamePhase.CHARACTER_CREATION:
        return await _handle_character_creation(state, action)

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


async def _handle_character_creation(
    state: GameState, action: str
) -> NarrativeResponse:
    """Handle actions during character creation phase.

    Args:
        state: Current game state
        action: Player's action/response

    Returns:
        NarrativeResponse with innkeeper's next question or character sheet
    """
    # Increment creation turn
    new_turn = session_manager.increment_creation_turn(state.session_id)

    # Store the exchange
    session_manager.add_exchange(state.session_id, action, "")

    # Check if user wants to skip
    if "skip" in action.lower():
        # Create default character and transition to exploration
        default_character = CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )
        session_manager.set_character_sheet(state.session_id, default_character)
        session_manager.set_phase(state.session_id, GamePhase.EXPLORATION)

        choices = STARTER_CHOICES_POOL[:3]
        session_manager.set_choices(state.session_id, choices)

        return NarrativeResponse(
            narrative=WELCOME_NARRATIVE,
            session_id=state.session_id,
            choices=choices,
        )

    # If we've completed 5 turns, generate character sheet and transition
    if new_turn >= 5:
        # Build character from conversation history
        character_sheet = _generate_character_from_history(state)
        session_manager.set_character_sheet(state.session_id, character_sheet)
        session_manager.set_phase(state.session_id, GamePhase.EXPLORATION)

        choices = STARTER_CHOICES_POOL[:3]
        session_manager.set_choices(state.session_id, choices)

        narrative = (
            f"The innkeeper nods slowly, studying you. 'So, {character_sheet.name} - "
            f"a {character_sheet.race.value} {character_sheet.character_class.value}. "
            "I've seen your kind before. There's work for those willing to take risks.' "
            "He leans closer. 'Choose your path...'"
        )

        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Continue character interview with innkeeper
    # For now, use static prompts based on turn number
    interview_prompts = {
        2: "The innkeeper raises an eyebrow. 'And what skills do you bring? "
        "Are you quick with a blade, clever with magic, or something else entirely?'",
        3: "He nods thoughtfully. 'Every adventurer has a story. "
        "What drove you to seek fortune in these dangerous lands?'",
        4: "The innkeeper glances at your gear. 'What's in that pack of yours? "
        "A traveler's worth is often measured by their tools.'",
    }

    narrative = interview_prompts.get(
        new_turn,
        "The innkeeper strokes his beard. 'Tell me more about yourself, traveler.'",
    )

    choices = [
        "Answer the question",
        "Share more details",
        "Skip and start adventuring",
    ]
    session_manager.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
    )


def _generate_character_from_history(state: GameState) -> CharacterSheet:
    """Generate a character sheet from conversation history.

    For MVP, this creates a basic character. Future versions will use
    InnkeeperAgent to parse the conversation and generate appropriate stats.

    Args:
        state: Game state with conversation history

    Returns:
        Generated CharacterSheet
    """
    # Extract character info from conversation history
    history_text = " ".join(
        entry.get("action", "") for entry in state.conversation_history
    ).lower()

    # Detect race from keywords
    race = CharacterRace.HUMAN
    if "elf" in history_text:
        race = CharacterRace.ELF
    elif "dwarf" in history_text:
        race = CharacterRace.DWARF
    elif "halfling" in history_text:
        race = CharacterRace.HALFLING
    elif "dragonborn" in history_text or "dragon" in history_text:
        race = CharacterRace.DRAGONBORN
    elif "tiefling" in history_text:
        race = CharacterRace.TIEFLING

    # Detect class from keywords
    character_class = CharacterClass.FIGHTER
    if "wizard" in history_text or "magic" in history_text or "mage" in history_text:
        character_class = CharacterClass.WIZARD
    elif (
        "rogue" in history_text or "thief" in history_text or "stealth" in history_text
    ):
        character_class = CharacterClass.ROGUE
    elif (
        "cleric" in history_text or "priest" in history_text or "healer" in history_text
    ):
        character_class = CharacterClass.CLERIC
    elif (
        "ranger" in history_text or "archer" in history_text or "hunter" in history_text
    ):
        character_class = CharacterClass.RANGER
    elif (
        "bard" in history_text
        or "musician" in history_text
        or "performer" in history_text
    ):
        character_class = CharacterClass.BARD

    # Extract name if mentioned (simple heuristic)
    name = "Adventurer"
    for entry in state.conversation_history:
        action_text = entry.get("action", "")
        # Look for "I am X" or "my name is X" patterns
        if "i am " in action_text.lower():
            parts = action_text.lower().split("i am ")
            if len(parts) > 1:
                potential_name = parts[1].split()[0].strip(".,!?")
                if potential_name and len(potential_name) > 1:
                    name = potential_name.title()
                    break
        elif "name is " in action_text.lower():
            parts = action_text.lower().split("name is ")
            if len(parts) > 1:
                potential_name = parts[1].split()[0].strip(".,!?")
                if potential_name and len(potential_name) > 1:
                    name = potential_name.title()
                    break

    return CharacterSheet(
        name=name,
        race=race,
        character_class=character_class,
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

    # Apply content safety filter
    action = filter_content(action)

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
