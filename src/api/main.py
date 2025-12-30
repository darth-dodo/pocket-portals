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
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from sse_starlette.sse import EventSourceResponse

from src.agents.character_interviewer import CharacterInterviewerAgent
from src.agents.epilogue import EpilogueAgent, generate_fallback_epilogue
from src.agents.innkeeper import InnkeeperAgent
from src.agents.jester import JesterAgent
from src.agents.keeper import KeeperAgent
from src.agents.narrator import NarratorAgent
from src.agents.quest_designer import QuestDesignerAgent
from src.engine import AgentRouter, TurnExecutor
from src.engine.combat_manager import CombatManager
from src.engine.pacing import (
    build_pacing_context,
    check_closure_triggers,
    format_pacing_hint,
)
from src.state import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    GamePhase,
    GameState,
    SessionManager,
)
from src.state.backends import create_backend
from src.state.models import CombatPhaseEnum, CombatState

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

# Combat trigger keywords - subset of mechanical keywords for auto-starting combat
COMBAT_TRIGGER_KEYWORDS = [
    "attack",
    "fight",
    "swing",
    "shoot",
    "hit",
    "strike",
    "charge",
    "lunge",
]

# Enemy keywords to help detect combat context
ENEMY_KEYWORDS = [
    "goblin",
    "orc",
    "troll",
    "skeleton",
    "zombie",
    "bandit",
    "wolf",
    "bear",
    "dragon",
    "monster",
    "enemy",
    "creature",
]


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


def _detect_combat_trigger(action: str) -> bool:
    """Detect if action contains combat trigger keywords.

    Args:
        action: Player's action text

    Returns:
        True if action likely initiates combat
    """
    action_lower = action.lower()

    # Check for combat trigger keywords
    has_combat_keyword = any(
        keyword in action_lower for keyword in COMBAT_TRIGGER_KEYWORDS
    )

    # Check for enemy keywords to strengthen signal
    has_enemy_keyword = any(keyword in action_lower for keyword in ENEMY_KEYWORDS)

    # Combat trigger if both keywords present, or just combat keyword with strong intent
    return has_combat_keyword and (has_enemy_keyword or len(action_lower.split()) < 5)


def _detect_enemy_type(action: str) -> str:
    """Detect enemy type from action text.

    Args:
        action: Player's action text

    Returns:
        Enemy type key for ENEMY_TEMPLATES, defaults to "goblin"
    """
    action_lower = action.lower()

    # Map keywords to enemy types
    enemy_map = {
        "goblin": "goblin",
        "orc": "orc",
        "troll": "troll",
        "skeleton": "skeleton",
        "zombie": "skeleton",  # Use skeleton template for zombie
        "bandit": "goblin",  # Use goblin template for bandit
        "wolf": "goblin",  # Use goblin template for wolf
        "bear": "orc",  # Use orc template for bear (stronger)
        "dragon": "troll",  # Use troll template for dragon (strongest available)
    }

    for keyword, enemy_type in enemy_map.items():
        if keyword in action_lower:
            return enemy_type

    # Default to goblin for generic combat
    return "goblin"


# Global state - agents initialized in lifespan
narrator: NarratorAgent | None = None
innkeeper: InnkeeperAgent | None = None
keeper: KeeperAgent | None = None
jester: JesterAgent | None = None
character_interviewer: CharacterInterviewerAgent | None = None
quest_designer: QuestDesignerAgent | None = None
epilogue_agent: EpilogueAgent | None = None
agent_router = AgentRouter()
turn_executor: TurnExecutor | None = None
combat_manager = CombatManager()

# Note: session_manager is now initialized via FastAPI lifespan and accessed via app.state

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
    "I am a battle-hardened dwarf",
    "I am an elven mage seeking knowledge",
    "I am a human rogue with secrets",
]


def get_session_manager(request: Request) -> SessionManager:
    """FastAPI dependency to get session manager from app state.

    Args:
        request: FastAPI Request object

    Returns:
        SessionManager: The session manager instance from app.state
    """
    return request.app.state.session_manager


async def get_session(request: Request, session_id: str | None) -> GameState:
    """Get existing session or create new one.

    Args:
        request: FastAPI Request object (to access app.state)
        session_id: Optional existing session ID

    Returns:
        GameState: Existing or newly created game state
    """
    sm = get_session_manager(request)
    return await sm.get_or_create_session(session_id)


def build_context(
    history: list[dict[str, str]],
    character_sheet: Any = None,
    character_description: str = "",
    state: GameState | None = None,
    include_pacing: bool = True,
) -> str:
    """Format conversation history and character info for LLM context.

    Args:
        history: List of conversation exchanges
        character_sheet: Optional CharacterSheet with structured character data
        character_description: Optional text description of character
        state: Optional GameState for pacing context
        include_pacing: Whether to include pacing hints (default True)

    Returns:
        Formatted context string for LLM
    """
    lines = []

    # Prepend pacing hint if state is provided and pacing is enabled
    if include_pacing and state and state.adventure_turn > 0:
        pacing_context = build_pacing_context(state)
        pacing_hint = format_pacing_hint(pacing_context)
        lines.append(pacing_hint)
        lines.append("")

    # Include character information for continuity
    if character_sheet:
        lines.append("Character:")
        lines.append(f"- Name: {character_sheet.name}")
        lines.append(f"- Race: {character_sheet.race.value}")
        lines.append(f"- Class: {character_sheet.character_class.value}")
        if character_sheet.backstory:
            lines.append(f"- Backstory: {character_sheet.backstory}")
        lines.append("")

    # Include character description if no sheet but description exists
    elif character_description:
        lines.append(f"Character: {character_description}")
        lines.append("")

    # Include conversation history
    if history:
        lines.append("Previous conversation:")
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


class StartCombatRequest(BaseModel):
    """Request model for starting combat."""

    session_id: str
    enemy_type: str  # "goblin", "bandit", etc.


class StartCombatResponse(BaseModel):
    """Response model for combat start."""

    narrative: str
    combat_state: CombatState
    initiative_results: list[dict]


class CombatActionRequest(BaseModel):
    """Request model for combat action."""

    session_id: str
    action: str  # "attack" for now, "defend"/"flee" in Phase 5


class CombatActionResponse(BaseModel):
    """Response model for combat action."""

    success: bool
    result: dict  # Attack result details
    message: str  # Formatted text result
    narrative: str | None = None  # LLM summary at combat end
    combat_state: CombatState
    combat_ended: bool
    victory: bool | None  # True=win, False=lose, None=ongoing
    fled: bool = False  # True if player successfully fled


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize backend, session manager, and agents on startup."""
    global \
        narrator, \
        innkeeper, \
        keeper, \
        jester, \
        character_interviewer, \
        quest_designer, \
        epilogue_agent, \
        turn_executor

    # Initialize session backend and manager
    backend = await create_backend()
    app.state.backend = backend
    app.state.session_manager = SessionManager(backend)

    # Initialize agents if API key available
    if os.getenv("ANTHROPIC_API_KEY"):
        narrator = NarratorAgent()
        innkeeper = InnkeeperAgent()
        keeper = KeeperAgent()
        jester = JesterAgent()
        character_interviewer = CharacterInterviewerAgent()
        quest_designer = QuestDesignerAgent()
        epilogue_agent = EpilogueAgent()
        turn_executor = TurnExecutor(
            narrator=narrator,
            keeper=keeper,
            jester=jester,
        )
    yield

    # Shutdown: close backend connection if applicable
    if hasattr(backend, "close"):
        await backend.close()

    narrator = None
    innkeeper = None
    keeper = None
    jester = None
    character_interviewer = None
    epilogue_agent = None
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
    request: Request,
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
    # Get session manager from app state
    sm = get_session_manager(request)

    # Create new session
    state = await get_session(request, None)

    if skip_creation:
        # Create default character and skip to exploration
        default_character = CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )
        await sm.set_character_sheet(state.session_id, default_character)
        await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

        # Select 3 choices from the adventure pool
        if shuffle:
            choices = random.sample(STARTER_CHOICES_POOL, 3)
        else:
            choices = STARTER_CHOICES_POOL[:3]

        await sm.set_choices(state.session_id, choices)
        if character:
            await sm.set_character_description(state.session_id, character)

        return NarrativeResponse(
            narrative=WELCOME_NARRATIVE,
            session_id=state.session_id,
            choices=choices,
        )

    # Start character creation flow
    await sm.set_creation_turn(state.session_id, 1)

    # Generate dynamic starter choices using the agent
    if character_interviewer:
        starter_choices = character_interviewer.generate_starter_choices()
    else:
        starter_choices = CHARACTER_CREATION_CHOICES

    await sm.set_choices(state.session_id, starter_choices)

    if character:
        await sm.set_character_description(state.session_id, character)

    return NarrativeResponse(
        narrative=CHARACTER_CREATION_NARRATIVE,
        session_id=state.session_id,
        choices=starter_choices,
    )


@app.post("/action", response_model=NarrativeResponse)
async def process_action(
    request: Request, action_request: ActionRequest
) -> NarrativeResponse:
    """Process player action and return narrative response."""
    # Get session manager from app state
    sm = get_session_manager(request)

    state = await get_session(request, action_request.session_id)

    # Resolve action from choice_index or direct action
    if action_request.choice_index is not None:
        # Use stored choice from session state
        choices = state.current_choices or ["Look around", "Wait", "Leave"]
        action = choices[
            action_request.choice_index - 1
        ]  # Convert 1-indexed to 0-indexed
    else:
        action = action_request.action or ""

    # Apply content safety filter
    action = filter_content(action)

    # Handle CHARACTER_CREATION phase specially
    if state.phase == GamePhase.CHARACTER_CREATION:
        return await _handle_character_creation(request, state, action)

    # Handle COMBAT phase or combat triggers
    if state.phase == GamePhase.COMBAT or (
        state.combat_state and state.combat_state.is_active
    ):
        # Already in combat - route to combat handler
        return await _handle_combat_action(request, state, action)

    # Check for combat triggers in action
    if _detect_combat_trigger(action):
        # Auto-start combat
        return await _handle_combat_action(request, state, action)

    if turn_executor is None:
        choices = ["Look around", "Wait", "Leave"]
        await sm.set_choices(state.session_id, choices)
        return NarrativeResponse(
            narrative="The narrator is not available. Check ANTHROPIC_API_KEY.",
            session_id=state.session_id,
            choices=choices,
        )

    # Increment adventure turn before executing agents
    await sm.increment_adventure_turn(state.session_id)
    # Refresh state to get updated turn and phase
    state = await sm.get_or_create_session(state.session_id)

    # Check closure triggers after turn increment
    closure_status = check_closure_triggers(state)
    if closure_status.should_trigger_epilogue:
        # Trigger epilogue and mark adventure complete
        updated_state = await sm.trigger_epilogue(
            state.session_id, closure_status.reason or ""
        )
        if updated_state is None:
            # Fallback if state couldn't be updated
            choices = ["Begin New Adventure", "View Character Sheet"]
            return NarrativeResponse(
                narrative="Your adventure has concluded.",
                session_id=action_request.session_id or "",
                choices=choices,
            )
        state = updated_state

        # Generate epilogue narrative using EpilogueAgent
        reason = closure_status.reason or "hard_cap"
        if epilogue_agent:
            try:
                # Build context for epilogue generation
                context = build_context(
                    state.conversation_history,
                    character_sheet=state.character_sheet,
                    character_description=state.character_description,
                    state=state,
                    include_pacing=False,
                )
                epilogue_narrative = epilogue_agent.generate_epilogue(
                    state=state,
                    reason=reason,
                    context=context,
                )
            except Exception:
                # Fallback to static epilogue if agent fails
                epilogue_narrative = generate_fallback_epilogue(reason, state)
        else:
            # No agent available - use static fallback
            epilogue_narrative = generate_fallback_epilogue(reason, state)

        choices = ["Begin New Adventure", "View Character Sheet", "Share Story"]
        await sm.set_choices(state.session_id, choices)
        await sm.add_exchange(state.session_id, action, epilogue_narrative)

        return NarrativeResponse(
            narrative=epilogue_narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Route to appropriate agents based on phase and action
    routing = agent_router.route(
        action=action,
        phase=state.phase,
        recent_agents=state.recent_agents,
    )

    # Execute agents and get aggregated result (with pacing context)
    context = build_context(
        state.conversation_history,
        character_sheet=state.character_sheet,
        character_description=state.character_description,
        state=state,
        include_pacing=True,
    )
    result = await turn_executor.execute_async(
        action=action,
        routing=routing,
        context=context,
    )

    # Store exchange in session (auto-limits to 20)
    await sm.add_exchange(state.session_id, action, result.narrative)

    # Update recent agents for Jester cooldown tracking
    await sm.update_recent_agents(state.session_id, routing.agents)

    # Use choices from turn result
    await sm.set_choices(state.session_id, result.choices)

    return NarrativeResponse(
        narrative=result.narrative, session_id=state.session_id, choices=result.choices
    )


async def _handle_character_creation(
    request: Request, state: GameState, action: str
) -> NarrativeResponse:
    """Handle actions during character creation phase.

    Args:
        request: FastAPI Request object (to access app.state)
        state: Current game state
        action: Player's action/response

    Returns:
        NarrativeResponse with innkeeper's next question or character sheet
    """
    # Get session manager from app state
    sm = get_session_manager(request)

    # Increment creation turn
    new_turn = await sm.increment_creation_turn(state.session_id)

    # Check if user wants to skip
    if "skip" in action.lower():
        # Create default character and transition to exploration
        default_character = CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )
        await sm.set_character_sheet(state.session_id, default_character)
        await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

        choices = STARTER_CHOICES_POOL[:3]
        await sm.add_exchange(state.session_id, action, WELCOME_NARRATIVE)
        await sm.set_choices(state.session_id, choices)

        return NarrativeResponse(
            narrative=WELCOME_NARRATIVE,
            session_id=state.session_id,
            choices=choices,
        )

    # If we've completed 5 turns, generate character sheet and transition
    if new_turn >= 5:
        # Build character from conversation history (include current action)
        await sm.add_exchange(state.session_id, action, "")
        updated_state = await sm.get_or_create_session(state.session_id)
        character_sheet = _generate_character_from_history(updated_state)
        await sm.set_character_sheet(state.session_id, character_sheet)
        await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

        # Generate a contextual quest for this character immediately
        if quest_designer:
            try:
                quest = quest_designer.generate_quest(
                    character_sheet=character_sheet,
                    quest_history="",  # No quest history yet
                    game_context="Character just finished creation at the Rusty Tankard tavern.",
                )
                await sm.set_active_quest(state.session_id, quest)

                # Create choices from quest objectives
                if quest.objectives:
                    choices = [obj.description for obj in quest.objectives[:3]]
                    # Ensure we have 3 choices
                    while len(choices) < 3:
                        choices.append("Ask more about the quest")
                else:
                    choices = STARTER_CHOICES_POOL[:3]

                # Build narrative with quest introduction
                narrative = (
                    f"The innkeeper nods slowly, studying you. 'So, {character_sheet.name} - "
                    f"a {character_sheet.race.value} {character_sheet.character_class.value}. "
                    f"I've seen your kind before.'\n\n"
                    f"He leans forward, voice lowering. '{quest.description}'\n\n"
                    f"**Quest: {quest.title}**\n"
                    f"Reward: {quest.rewards or 'The satisfaction of a job well done'}"
                )
            except Exception:
                # Fallback if quest generation fails
                if character_interviewer:
                    character_info = (
                        f"Name: {character_sheet.name}\n"
                        f"Race: {character_sheet.race.value}\n"
                        f"Class: {character_sheet.character_class.value}"
                    )
                    if character_sheet.backstory:
                        character_info += f"\nBackstory: {character_sheet.backstory}"
                    choices = character_interviewer.generate_adventure_hooks(
                        character_info
                    )
                else:
                    choices = STARTER_CHOICES_POOL[:3]

                narrative = (
                    f"The innkeeper nods slowly, studying you. 'So, {character_sheet.name} - "
                    f"a {character_sheet.race.value} {character_sheet.character_class.value}. "
                    "I've seen your kind before. There's work for those willing to take risks.' "
                    "He leans closer. 'Choose your path...'"
                )
        else:
            # No quest designer available - use adventure hooks
            if character_interviewer:
                character_info = (
                    f"Name: {character_sheet.name}\n"
                    f"Race: {character_sheet.race.value}\n"
                    f"Class: {character_sheet.character_class.value}"
                )
                if character_sheet.backstory:
                    character_info += f"\nBackstory: {character_sheet.backstory}"
                choices = character_interviewer.generate_adventure_hooks(character_info)
            else:
                choices = STARTER_CHOICES_POOL[:3]

            narrative = (
                f"The innkeeper nods slowly, studying you. 'So, {character_sheet.name} - "
                f"a {character_sheet.race.value} {character_sheet.character_class.value}. "
                "I've seen your kind before. There's work for those willing to take risks.' "
                "He leans closer. 'Choose your path...'"
            )

        await sm.set_choices(state.session_id, choices)

        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Build conversation history for context, including current action
    history_lines = []
    for entry in state.conversation_history:
        if entry.get("action"):
            history_lines.append(f"Player: {entry['action']}")
        if entry.get("narrative"):
            history_lines.append(f"Innkeeper: {entry['narrative']}")
    # Add current action to context so agent sees what player just said
    history_lines.append(f"Player: {action}")
    conversation_history = "\n".join(history_lines)

    # Use agent to generate dynamic interview response
    if character_interviewer:
        interview_result = character_interviewer.interview_turn(
            turn_number=new_turn,
            conversation_history=conversation_history,
        )
        narrative = interview_result["narrative"]
        choices = interview_result["choices"]
    else:
        # Fallback to static responses
        narrative = (
            "The innkeeper waits for your response. 'Tell me more about yourself.'"
        )
        choices = [
            "I am a warrior",
            "I am a scholar",
            "I am a wanderer",
        ]

    # Store the exchange with the actual narrative response
    await sm.add_exchange(state.session_id, action, narrative)
    await sm.set_choices(state.session_id, choices)

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


async def _handle_combat_action(
    request: Request, state: GameState, action: str
) -> NarrativeResponse:
    """Handle combat-related actions in the main action flow.

    This function:
    1. Auto-starts combat if combat keywords detected and not in combat
    2. Routes to combat handler if already in combat
    3. Handles combat end transitions back to exploration

    Args:
        request: FastAPI Request object (to access app.state)
        state: Current game state
        action: Player's action text

    Returns:
        NarrativeResponse with combat results
    """
    # Get session manager from app state
    sm = get_session_manager(request)

    # Case 1: Already in combat - route to combat action handler
    if state.combat_state and state.combat_state.is_active:
        # Parse action for combat intent (attack/defend/flee)
        action_lower = action.lower()

        # Handle flee action
        if "flee" in action_lower or "run" in action_lower or "escape" in action_lower:
            # End combat, transition back to exploration
            await sm.set_combat_state(state.session_id, None)
            await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

            narrative = (
                "You turn and flee from the battle! "
                "The enemy doesn't pursue as you make your escape."
            )
            choices = ["Look around", "Catch your breath", "Continue onward"]
            await sm.add_exchange(state.session_id, action, narrative)
            await sm.set_choices(state.session_id, choices)

            return NarrativeResponse(
                narrative=narrative,
                session_id=state.session_id,
                choices=choices,
            )

        # Validate character sheet
        if not state.character_sheet:
            narrative = "You need a character to engage in combat!"
            choices = ["Look around", "Wait", "Leave"]
            await sm.set_choices(state.session_id, choices)
            return NarrativeResponse(
                narrative=narrative,
                session_id=state.session_id,
                choices=choices,
            )

        combat_state = state.combat_state

        # Validate it's player's turn
        if combat_state.phase != CombatPhaseEnum.PLAYER_TURN:
            narrative = "Wait for your turn in combat!"
            choices = ["Wait", "Assess the situation"]
            await sm.set_choices(state.session_id, choices)
            return NarrativeResponse(
                narrative=narrative,
                session_id=state.session_id,
                choices=choices,
            )

        # Execute player attack
        if keeper:
            player_result = keeper.resolve_player_attack(
                combat_state, state.character_sheet
            )
        else:
            player_result = combat_manager.execute_player_attack(
                combat_state, state.character_sheet
            )

        player_message = (
            combat_manager.format_attack_result(player_result)
            if combat_manager
            else player_result["log_entry"]
        )

        # Check if enemy defeated
        enemy_hp = player_result.get("enemy_hp", 0)
        if enemy_hp <= 0:
            # Combat won! End combat and transition back to exploration
            await sm.set_combat_state(state.session_id, None)
            await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

            victory_narrative = (
                f"{player_message}\n\n"
                f"Victory! The enemy falls defeated. "
                f"You stand victorious and can continue your adventure."
            )
            choices = ["Search the area", "Rest briefly", "Continue onward"]
            await sm.add_exchange(state.session_id, action, victory_narrative)
            await sm.set_choices(state.session_id, choices)

            return NarrativeResponse(
                narrative=victory_narrative,
                session_id=state.session_id,
                choices=choices,
            )

        # Enemy turn
        if keeper:
            enemy_result = keeper.resolve_enemy_attack(combat_state)
        else:
            enemy_result = combat_manager.execute_enemy_turn(combat_state)

        enemy_message = (
            combat_manager.format_attack_result(enemy_result)
            if combat_manager
            else enemy_result["log_entry"]
        )

        # Check if player defeated
        player_hp = enemy_result.get("player_hp", state.character_sheet.hit_points)
        if player_hp <= 0:
            # Combat lost! End combat
            await sm.set_combat_state(state.session_id, None)
            await sm.set_phase(state.session_id, GamePhase.EXPLORATION)

            defeat_narrative = (
                f"{player_message}\n\n{enemy_message}\n\n"
                f"Defeat! You fall unconscious. "
                f"When you awaken, you find yourself back at the tavern, bruised but alive."
            )
            choices = ["Recover", "Plan your next move", "Leave the tavern"]
            await sm.add_exchange(state.session_id, action, defeat_narrative)
            await sm.set_choices(state.session_id, choices)

            return NarrativeResponse(
                narrative=defeat_narrative,
                session_id=state.session_id,
                choices=choices,
            )

        # Combat continues
        full_narrative = f"{player_message}\n\n{enemy_message}"
        choices = ["Attack again", "Defend", "Flee"]
        await sm.add_exchange(state.session_id, action, full_narrative)
        await sm.set_choices(state.session_id, choices)

        return NarrativeResponse(
            narrative=full_narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Case 2: Combat keywords detected but not in combat - auto-start combat
    if _detect_combat_trigger(action):
        # Validate character sheet
        if not state.character_sheet:
            narrative = "You need a character to engage in combat!"
            choices = ["Look around", "Wait", "Leave"]
            await sm.set_choices(state.session_id, choices)
            return NarrativeResponse(
                narrative=narrative,
                session_id=state.session_id,
                choices=choices,
            )

        # Detect enemy type from action
        enemy_type = _detect_enemy_type(action)

        # Start combat using keeper
        try:
            if keeper:
                combat_state, initiative_results = keeper.start_combat(
                    character_sheet=state.character_sheet,
                    enemy_type=enemy_type,
                )
            else:
                combat_state, initiative_results = combat_manager.start_combat(
                    character_sheet=state.character_sheet,
                    enemy_type=enemy_type,
                )
        except ValueError:
            # Invalid enemy type, fall back to goblin
            if keeper:
                combat_state, initiative_results = keeper.start_combat(
                    character_sheet=state.character_sheet,
                    enemy_type="goblin",
                )
            else:
                combat_state, initiative_results = combat_manager.start_combat(
                    character_sheet=state.character_sheet,
                    enemy_type="goblin",
                )

        # Format initiative
        if keeper:
            initiative_narrative = keeper.format_initiative_result(initiative_results)
        else:
            initiative_narrative = "Initiative rolled. Combat begins!"

        # Get scene description
        scene_narrative = ""
        if narrator and combat_state.enemy_template:
            enemy_desc = combat_state.enemy_template.description
            enemy_name = combat_state.enemy_template.name

            context = build_context(
                state.conversation_history,
                character_sheet=state.character_sheet,
            )

            scene_prompt = (
                f"A {enemy_name} appears! {enemy_desc}. "
                f"Describe this combat encounter dramatically in 2-3 sentences."
            )

            scene_narrative = narrator.respond(action=scene_prompt, context=context)
        else:
            enemy_name = (
                combat_state.enemy_template.name
                if combat_state.enemy_template
                else "enemy"
            )
            scene_narrative = f"A {enemy_name} appears before you!"

        # Combine narratives
        full_narrative = f"{scene_narrative}\n\n{initiative_narrative}"

        # Store combat state
        await sm.set_combat_state(state.session_id, combat_state)
        await sm.set_phase(state.session_id, GamePhase.COMBAT)

        choices = ["Attack", "Defend", "Flee"]
        await sm.add_exchange(state.session_id, action, full_narrative)
        await sm.set_choices(state.session_id, choices)

        return NarrativeResponse(
            narrative=full_narrative,
            session_id=state.session_id,
            choices=choices,
        )

    # Case 3: No combat - this shouldn't be called, but return safe fallback
    narrative = "The adventure continues..."
    choices = ["Look around", "Wait", "Leave"]
    await sm.set_choices(state.session_id, choices)
    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
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
async def resolve_action(
    request: Request, resolve_request: ResolveRequest
) -> ResolveResponse:
    """Resolve game mechanics for a player action.

    Args:
        request: FastAPI Request object
        resolve_request: Action resolution request with action, difficulty, and optional session_id
    """
    if keeper is None:
        return ResolveResponse(
            result="The keeper is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if resolve_request.session_id:
        state = await get_session(request, resolve_request.session_id)
        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
            character_description=state.character_description,
        )

    result = keeper.resolve_action(
        action=resolve_request.action,
        context=context,
        difficulty=resolve_request.difficulty,
    )
    return ResolveResponse(result=result)


@app.post("/jester/complicate", response_model=ComplicateResponse)
async def add_complication(
    request: Request, complicate_request: ComplicateRequest
) -> ComplicateResponse:
    """Add a complication or meta-commentary to a situation.

    Args:
        request: FastAPI Request object
        complicate_request: Complication request with situation and optional session_id
    """
    if jester is None:
        return ComplicateResponse(
            complication="The jester is not available. Check ANTHROPIC_API_KEY."
        )

    # Build context from session if provided
    context = ""
    if complicate_request.session_id:
        state = await get_session(request, complicate_request.session_id)
        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
            character_description=state.character_description,
        )

    complication = jester.add_complication(
        situation=complicate_request.situation, context=context
    )
    return ComplicateResponse(complication=complication)


@app.post("/combat/start", response_model=StartCombatResponse)
async def start_combat(
    request: Request, combat_request: StartCombatRequest
) -> StartCombatResponse:
    """Start a new combat encounter.

    Args:
        request: FastAPI Request object
        combat_request: Combat start request with session_id and enemy_type

    Returns:
        StartCombatResponse with narrative, combat state, and initiative results

    Raises:
        HTTPException: 404 if session not found, 400 if no character or invalid enemy
    """
    from fastapi import HTTPException

    # Get session manager from app state
    sm = get_session_manager(request)

    # 1. Get session - validate that this specific session_id exists
    state = await sm.get_session(combat_request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate character exists
    if not state.character_sheet:
        raise HTTPException(
            status_code=400,
            detail="Character sheet required. Complete character creation first.",
        )

    # 3. Use Keeper to start combat (Keeper handles all combat mechanics)
    # Fallback to combat_manager if keeper not available (e.g., in tests without API key)
    try:
        if keeper:
            combat_state, initiative_results = keeper.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=combat_request.enemy_type,
            )
        else:
            # Fallback for testing/development without API key
            combat_state, initiative_results = combat_manager.start_combat(
                character_sheet=state.character_sheet,
                enemy_type=combat_request.enemy_type,
            )
    except ValueError as e:
        # Invalid enemy type
        raise HTTPException(status_code=400, detail=str(e)) from e

    # 4. Get Keeper to format initiative results
    if keeper:
        initiative_narrative = keeper.format_initiative_result(initiative_results)
    else:
        # Fallback formatting
        initiative_narrative = "Initiative rolled. Combat begins!"

    # 5. Get Narrator to describe combat scene
    scene_narrative = ""
    if narrator and combat_state.enemy_template:
        enemy_desc = combat_state.enemy_template.description
        enemy_name = combat_state.enemy_template.name

        context = build_context(
            state.conversation_history,
            character_sheet=state.character_sheet,
        )

        # Ask narrator to describe the encounter
        scene_prompt = (
            f"A {enemy_name} appears! {enemy_desc}. "
            f"Describe this combat encounter dramatically in 2-3 sentences."
        )

        scene_narrative = narrator.respond(action=scene_prompt, context=context)
    else:
        # Fallback if narrator not available
        enemy_name = (
            combat_state.enemy_template.name if combat_state.enemy_template else "enemy"
        )
        scene_narrative = f"A {enemy_name} appears before you!"

    # Combine narratives
    full_narrative = f"{scene_narrative}\n\n{initiative_narrative}"

    # 6. Store combat state in session
    state.combat_state = combat_state
    state.phase = GamePhase.COMBAT

    # 7. Return response
    return StartCombatResponse(
        narrative=full_narrative,
        combat_state=combat_state,
        initiative_results=initiative_results,
    )


@app.post("/combat/action", response_model=CombatActionResponse)
async def combat_action(
    request: Request, combat_action_request: CombatActionRequest
) -> CombatActionResponse:
    """Execute a combat action.

    Args:
        request: FastAPI Request object
        combat_action_request: Combat action request with session_id and action

    Returns:
        CombatActionResponse with result, message, updated combat state, and end status

    Raises:
        HTTPException: 404 if session not found, 400 if no active combat or not player turn
    """
    from fastapi import HTTPException

    # Get session manager from app state
    sm = get_session_manager(request)

    # 1. Validate session and active combat
    state = await sm.get_session(combat_action_request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not state.combat_state or not state.combat_state.is_active:
        raise HTTPException(status_code=400, detail="No active combat")

    if not state.character_sheet:
        raise HTTPException(status_code=400, detail="No character sheet found")

    combat_state = state.combat_state

    # 2. Validate it's player's turn
    if combat_state.phase != CombatPhaseEnum.PLAYER_TURN:
        raise HTTPException(
            status_code=400,
            detail=f"Not player's turn. Current phase: {combat_state.phase}",
        )

    # 3. Execute player action via keeper
    action = combat_action_request.action.lower()
    fled = False

    if action == "attack":
        # Use keeper to resolve attack
        if keeper:
            player_result = keeper.resolve_player_attack(
                combat_state, state.character_sheet
            )
        else:
            # Fallback to combat_manager
            player_result = combat_manager.execute_player_attack(
                combat_state, state.character_sheet
            )

        # Format the message
        player_message = (
            combat_manager.format_attack_result(player_result)
            if combat_manager
            else player_result["log_entry"]
        )
    elif action == "defend":
        # Execute defend action
        player_result = combat_manager.execute_defend(
            combat_state, state.character_sheet
        )
        player_message = player_result["log_entry"]
    elif action == "flee":
        # Execute flee action
        player_result = combat_manager.execute_flee(combat_state, state.character_sheet)
        player_message = player_result["log_entry"]

        if player_result["success"]:
            # Successful flee - combat ends, player escaped
            fled = True
            combat_ended = True
            victory = None  # Neither victory nor defeat
            narrative = None  # No narrator summary for flee
        # If flee failed, free_attack is already logged in combat_log
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    # 4. Check if combat ended after player action (for attack/defend)
    if action != "flee" or not fled:
        combat_ended, result = combat_manager.check_combat_end(combat_state)
    else:
        # Fled successfully - already handled above
        combat_ended = True
        result = None

    victory = None
    narrative = None

    if combat_ended and not fled and result is not None:
        # Combat ended - clean up and get narrative
        victory = result == "victory"
        combat_manager.end_combat(combat_state, result)

        # Get narrator summary (ONE LLM call for entire combat)
        if narrator and combat_state.enemy_template:
            narrative = narrator.summarize_combat(
                combat_log=combat_state.combat_log,
                victory=victory,
                enemy_name=combat_state.enemy_template.name,
                player_name=state.character_sheet.name,
            )

    # 5. If combat continues, execute enemy turn
    enemy_message = ""
    if not combat_ended:
        # Execute enemy attack
        if keeper:
            enemy_result = keeper.resolve_enemy_attack(combat_state)
        else:
            enemy_result = combat_manager.execute_enemy_turn(combat_state)

        enemy_message = (
            combat_manager.format_attack_result(enemy_result)
            if combat_manager
            else enemy_result["log_entry"]
        )

        # Check if combat ended after enemy attack
        combat_ended, result = combat_manager.check_combat_end(combat_state)

        if combat_ended and result is not None:
            # Combat ended - clean up and get narrative
            victory = result == "victory"
            combat_manager.end_combat(combat_state, result)

            # Get narrator summary (ONE LLM call for entire combat)
            if narrator and combat_state.enemy_template:
                narrative = narrator.summarize_combat(
                    combat_log=combat_state.combat_log,
                    victory=victory,
                    enemy_name=combat_state.enemy_template.name,
                    player_name=state.character_sheet.name,
                )

    # 6. Combine messages
    full_message = player_message
    if enemy_message:
        full_message += f"\n\n{enemy_message}"

    # 7. Update session combat state
    await sm.set_combat_state(combat_action_request.session_id, combat_state)

    # If combat ended, also update phase back to EXPLORATION
    if combat_ended:
        await sm.set_phase(combat_action_request.session_id, GamePhase.EXPLORATION)

    # 8. Return response
    return CombatActionResponse(
        success=True,
        result=player_result,
        message=full_message,
        narrative=narrative,
        combat_state=combat_state,
        combat_ended=combat_ended,
        victory=victory,
        fled=fled,
    )


@app.post("/action/stream")
async def process_action_stream(
    request: Request, action_request: ActionRequest
) -> EventSourceResponse:
    """Process player action with streaming response via Server-Sent Events.

    Streams agent responses as they complete, providing real-time feedback.
    Events sent:
    - agent_start: When an agent begins processing
    - agent_response: When an agent completes with its response
    - choices: Final choices for next action
    - complete: Signal that streaming is done
    - error: If something goes wrong
    """
    # Get session manager from app state
    sm = get_session_manager(request)

    state = await get_session(request, action_request.session_id)

    # Resolve action from choice_index or direct action
    if action_request.choice_index is not None:
        choices = state.current_choices or ["Look around", "Wait", "Leave"]
        action = choices[action_request.choice_index - 1]
    else:
        action = action_request.action or ""

    # Apply content safety filter
    action = filter_content(action)

    # Handle CHARACTER_CREATION phase with character-by-character streaming
    if state.phase == GamePhase.CHARACTER_CREATION:
        result = await _handle_character_creation(request, state, action)

        async def creation_generator() -> AsyncGenerator[dict[str, Any], None]:
            # Signal agent starting
            yield {
                "event": "agent_start",
                "data": json.dumps({"agent": "narrator"}),
            }

            # Stream narrative character by character
            for char in result.narrative:
                yield {
                    "event": "agent_chunk",
                    "data": json.dumps({"agent": "narrator", "chunk": char}),
                }
                await asyncio.sleep(0.02)  # 20ms delay for typewriter effect

            # Signal narrative complete
            yield {
                "event": "agent_response",
                "data": json.dumps({"agent": "narrator", "content": result.narrative}),
            }

            # Send choices
            yield {
                "event": "choices",
                "data": json.dumps({"choices": result.choices}),
            }
            yield {
                "event": "complete",
                "data": json.dumps({"session_id": result.session_id}),
            }

        return EventSourceResponse(creation_generator())

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
            accumulated_context = build_context(
                state.conversation_history,
                character_sheet=state.character_sheet,
                character_description=state.character_description,
            )

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
            choices = ["Look around", "Wait", "Leave"]  # Default fallback

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

                    # Narrator uses structured response with choices
                    if agent_name == "narrator" and hasattr(
                        agent, "respond_with_choices"
                    ):
                        structured_response = await loop.run_in_executor(
                            None,
                            lambda ctx=current_context, a=agent: a.respond_with_choices(
                                action=action, context=ctx
                            ),
                        )
                        response = structured_response.narrative
                        choices = structured_response.choices
                    else:
                        response = await loop.run_in_executor(
                            None,
                            lambda ctx=current_context, a=agent: a.respond(
                                action=action, context=ctx
                            ),
                        )

                    narrative_parts.append(response)

                    # Stream response character by character
                    for char in response:
                        yield {
                            "event": "agent_chunk",
                            "data": json.dumps({"agent": agent_name, "chunk": char}),
                        }
                        await asyncio.sleep(0.015)  # 15ms delay for typewriter effect

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

                # Stream jester response character by character
                for char in jester_response:
                    yield {
                        "event": "agent_chunk",
                        "data": json.dumps({"agent": "jester", "chunk": char}),
                    }
                    await asyncio.sleep(0.015)  # 15ms delay for typewriter effect

                yield {
                    "event": "agent_response",
                    "data": json.dumps({"agent": "jester", "content": jester_response}),
                }

            # Combine narrative
            full_narrative = "\n\n".join(narrative_parts)

            # Choices were already extracted from narrator's structured response
            # No need for a second LLM call

            yield {
                "event": "choices",
                "data": json.dumps({"choices": choices}),
            }

            # Update session state
            await sm.add_exchange(state.session_id, action, full_narrative)
            await sm.update_recent_agents(state.session_id, routing.agents)
            await sm.set_choices(state.session_id, choices)

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
