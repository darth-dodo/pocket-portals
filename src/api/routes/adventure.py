"""Adventure endpoints for Pocket Portals API.

Handles /start, /action, and /action/stream endpoints for game flow.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from src.api.content_safety import detect_combat_trigger, filter_content
from src.api.dependencies import build_context, get_session, get_session_manager
from src.api.models import (
    ActionRequest,
    CharacterSheetData,
    NarrativeResponse,
)
from src.api.rate_limiting import require_rate_limit
from src.engine.pacing import check_closure_triggers
from src.state import CharacterClass, CharacterRace, CharacterSheet, GamePhase
from src.state.models import Quest, QuestObjective

router = APIRouter(tags=["adventure"])


def _get_agents(request: Request) -> dict[str, Any]:
    """Get agent instances from app.state.

    Args:
        request: FastAPI Request object with access to app.state

    Returns:
        Dict with narrator, innkeeper, keeper, jester, character_interviewer,
        character_builder, quest_designer, epilogue_agent, agent_router, turn_executor.
    """
    from src.engine import AgentRouter
    from src.engine.combat_manager import CombatManager

    return {
        "narrator": getattr(request.app.state, "narrator", None),
        "innkeeper": getattr(request.app.state, "innkeeper", None),
        "keeper": getattr(request.app.state, "keeper", None),
        "jester": getattr(request.app.state, "jester", None),
        "character_interviewer": getattr(
            request.app.state, "character_interviewer", None
        ),
        "character_builder": getattr(request.app.state, "character_builder", None),
        "quest_designer": getattr(request.app.state, "quest_designer", None),
        "epilogue_agent": getattr(request.app.state, "epilogue_agent", None),
        "agent_router": AgentRouter(),  # Stateless, can be created fresh
        "turn_executor": getattr(request.app.state, "turn_executor", None),
        "combat_manager": CombatManager(),  # Stateless, can be created fresh
    }


@router.get("/start", response_model=NarrativeResponse)
async def start_adventure(
    request: Request,
    shuffle: bool = Query(default=False, description="Shuffle the starter choices"),
    character: str = Query(
        default="", description="Optional character description for personalization"
    ),
    skip_creation: bool = Query(
        default=False, description="Skip character creation and start with default"
    ),
    _rate_limit: None = Depends(require_rate_limit("default")),
) -> NarrativeResponse:
    """Start a new adventure with starter choices.

    Returns 3 starter choices from the pool to begin the adventure.
    Use shuffle=true to randomize which choices are presented.
    Optionally provide a character description for personalized narrative.
    Use skip_creation=true to skip character creation with a default character.
    """
    import logging

    from src.api.constants import (
        CHARACTER_CREATION_CHOICES,
        CHARACTER_CREATION_NARRATIVE,
    )

    logger = logging.getLogger(__name__)
    agents = _get_agents(request)
    quest_designer = agents["quest_designer"]
    character_interviewer = agents["character_interviewer"]

    # Get session manager from app state
    sm = get_session_manager(request)

    # Create new session
    state = await get_session(request, None)

    if skip_creation:
        # Create default character and transition to quest selection
        default_character = CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )
        await sm.set_character_sheet(state.session_id, default_character)
        await sm.set_phase(state.session_id, GamePhase.QUEST_SELECTION)

        # Generate quest options for the player to choose from
        if quest_designer:
            try:
                quest_options = quest_designer.generate_quest_options(
                    character_sheet=default_character,
                    game_context="Character just arrived at the Rusty Tankard tavern.",
                )
            except Exception:
                # Fallback to a single quest if generation fails
                quest_options = [
                    quest_designer._create_fallback_quest(default_character)
                ]
        else:
            # No quest designer - create minimal fallback
            quest_options = [
                Quest(
                    id=str(uuid.uuid4()),
                    title="The Missing Merchant",
                    description="Find the missing merchant who disappeared on the forest road.",
                    objectives=[
                        QuestObjective(
                            id=str(uuid.uuid4()), description="Search the forest road"
                        )
                    ],
                ),
                Quest(
                    id=str(uuid.uuid4()),
                    title="Goblin Troubles",
                    description="Goblins have been raiding nearby farms.",
                    objectives=[
                        QuestObjective(
                            id=str(uuid.uuid4()), description="Find the goblin camp"
                        )
                    ],
                ),
                Quest(
                    id=str(uuid.uuid4()),
                    title="Ancient Artifact",
                    description="Recover an ancient artifact from the old ruins.",
                    objectives=[
                        QuestObjective(
                            id=str(uuid.uuid4()), description="Explore the ruins"
                        )
                    ],
                ),
            ]

        # Store pending quest options
        await sm.set_pending_quest_options(state.session_id, quest_options)

        # Present quest titles as choices
        choices = [f"Accept: {quest.title}" for quest in quest_options]
        await sm.set_choices(state.session_id, choices)

        if character:
            await sm.set_character_description(state.session_id, character)

        narrative = (
            "The innkeeper leans forward, his weathered hands resting on the bar. "
            "'I've heard of several opportunities for someone with your skills. "
            "Choose your path wisely, adventurer...'"
        )

        # Build character sheet data for frontend
        character_sheet_data = CharacterSheetData(
            name=default_character.name,
            race=default_character.race.value,
            character_class=default_character.character_class.value,
            level=default_character.level,
            current_hp=default_character.current_hp,
            max_hp=default_character.max_hp,
            stats={
                "strength": default_character.stats.strength,
                "dexterity": default_character.stats.dexterity,
                "constitution": default_character.stats.constitution,
                "intelligence": default_character.stats.intelligence,
                "wisdom": default_character.stats.wisdom,
                "charisma": default_character.stats.charisma,
            },
            equipment=default_character.equipment,
            backstory=default_character.backstory,
        )

        return NarrativeResponse(
            narrative=narrative,
            session_id=state.session_id,
            choices=choices,
            character_sheet=character_sheet_data,
        )

    # Start character creation flow
    await sm.set_creation_turn(state.session_id, 1)

    # Generate dynamic starter choices using the agent
    if character_interviewer:
        logger.info(
            "start_adventure: Using CharacterInterviewerAgent for starter choices"
        )
        starter_choices = character_interviewer.generate_starter_choices()
        logger.info("start_adventure: Got starter choices: %s", starter_choices)
    else:
        logger.warning(
            "start_adventure: No character_interviewer, using static fallback"
        )
        starter_choices = CHARACTER_CREATION_CHOICES

    await sm.set_choices(state.session_id, starter_choices)

    if character:
        await sm.set_character_description(state.session_id, character)

    return NarrativeResponse(
        narrative=CHARACTER_CREATION_NARRATIVE,
        session_id=state.session_id,
        choices=starter_choices,
    )


@router.post("/action", response_model=NarrativeResponse)
async def process_action(
    request: Request,
    action_request: ActionRequest,
    _rate_limit: None = Depends(require_rate_limit("llm")),
) -> NarrativeResponse:
    """Process player action and return narrative response."""
    import logging

    from src.agents.epilogue import generate_fallback_epilogue
    from src.api.handlers import (
        handle_character_creation as _handle_character_creation_impl,
    )
    from src.api.handlers import (
        handle_combat_action as _handle_combat_action_impl,
    )
    from src.api.handlers import (
        handle_quest_selection as _handle_quest_selection_impl,
    )

    logger = logging.getLogger(__name__)
    agents = _get_agents(request)
    narrator = agents["narrator"]
    keeper = agents["keeper"]
    quest_designer = agents["quest_designer"]
    epilogue_agent = agents["epilogue_agent"]
    agent_router = agents["agent_router"]
    turn_executor = agents["turn_executor"]
    combat_manager = agents["combat_manager"]
    character_interviewer = agents["character_interviewer"]
    character_builder = agents["character_builder"]

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
        return await _handle_character_creation_impl(
            request=request,
            state=state,
            action=action,
            character_interviewer=character_interviewer,
            character_builder=character_builder,
            quest_designer=quest_designer,
        )

    # Handle QUEST_SELECTION phase
    if state.phase == GamePhase.QUEST_SELECTION:
        return await _handle_quest_selection_impl(
            request=request,
            state=state,
            action=action,
        )

    # Handle COMBAT phase or combat triggers
    if state.phase == GamePhase.COMBAT or (
        state.combat_state and state.combat_state.is_active
    ):
        # Already in combat - route to combat handler
        return await _handle_combat_action_impl(
            request=request,
            state=state,
            action=action,
            keeper=keeper,
            narrator=narrator,
            combat_manager=combat_manager,
        )

    # Check for combat triggers in action
    if detect_combat_trigger(action):
        # Auto-start combat
        return await _handle_combat_action_impl(
            request=request,
            state=state,
            action=action,
            keeper=keeper,
            narrator=narrator,
            combat_manager=combat_manager,
        )

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

    # Get the narrative from turn executor result
    narrative = result.narrative

    # Check quest progress if conditions are met
    if state.active_quest and state.phase == GamePhase.EXPLORATION and quest_designer:
        try:
            progress = quest_designer.check_quest_progress(
                active_quest=state.active_quest,
                action=action,
                narrative=narrative,
            )

            if progress["objectives_completed"]:
                for obj_id in progress["objectives_completed"]:
                    await sm.update_quest_objective(state.session_id, obj_id, True)
                logger.info(
                    "Quest objectives completed: %s", progress["objectives_completed"]
                )

            if progress["quest_completed"]:
                await sm.complete_quest(state.session_id)
                narrative += f"\n\n{progress['completion_narrative']}"
                logger.info("Quest completed: %s", state.active_quest.title)

                # Generate new quest options and transition to QUEST_SELECTION
                if state.character_sheet:
                    try:
                        new_quest_options = quest_designer.generate_quest_options(
                            character_sheet=state.character_sheet,
                            game_context="Character has just completed a quest.",
                        )
                        await sm.set_pending_quest_options(
                            state.session_id, new_quest_options
                        )
                        await sm.set_phase(state.session_id, GamePhase.QUEST_SELECTION)

                        # Present new quest choices
                        quest_choices = [
                            f"Accept: {q.title}" for q in new_quest_options
                        ]
                        await sm.set_choices(state.session_id, quest_choices)

                        narrative += (
                            "\n\nThe innkeeper has heard of new opportunities. "
                            "Which path will you take next?"
                        )

                        return NarrativeResponse(
                            narrative=narrative,
                            session_id=state.session_id,
                            choices=quest_choices,
                        )
                    except Exception as e:
                        logger.warning("Failed to generate new quest options: %s", e)
        except Exception as e:
            logger.warning("Quest progress check failed: %s", e)

    # Update recent agents for Jester cooldown tracking
    await sm.update_recent_agents(state.session_id, routing.agents)

    # Use choices from turn result
    await sm.set_choices(state.session_id, result.choices)

    return NarrativeResponse(
        narrative=narrative, session_id=state.session_id, choices=result.choices
    )


@router.post("/action/stream")
async def process_action_stream(
    request: Request,
    action_request: ActionRequest,
    _rate_limit: None = Depends(require_rate_limit("llm")),
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
    from src.api.handlers import (
        handle_character_creation as _handle_character_creation_impl,
    )

    agents = _get_agents(request)
    narrator = agents["narrator"]
    keeper = agents["keeper"]
    jester = agents["jester"]
    agent_router = agents["agent_router"]
    turn_executor = agents["turn_executor"]
    character_interviewer = agents["character_interviewer"]
    character_builder = agents["character_builder"]
    quest_designer = agents["quest_designer"]

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
        result = await _handle_character_creation_impl(
            request=request,
            state=state,
            action=action,
            character_interviewer=character_interviewer,
            character_builder=character_builder,
            quest_designer=quest_designer,
        )

        # Check if character was just created (phase transitioned to EXPLORATION)
        updated_state = await sm.get_or_create_session(state.session_id)
        character_just_created = (
            updated_state.phase == GamePhase.EXPLORATION
            and updated_state.character_sheet is not None
        )

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

            # If character was just created, emit game_state with character_sheet
            if character_just_created and updated_state.character_sheet:
                cs = updated_state.character_sheet
                character_data = {
                    "name": cs.name,
                    "race": cs.race.value,
                    "character_class": cs.character_class.value,
                    "level": cs.level,
                    "current_hp": cs.current_hp,
                    "max_hp": cs.max_hp,
                    "stats": {
                        "strength": cs.stats.strength,
                        "dexterity": cs.stats.dexterity,
                        "constitution": cs.stats.constitution,
                        "intelligence": cs.stats.intelligence,
                        "wisdom": cs.stats.wisdom,
                        "charisma": cs.stats.charisma,
                    },
                    "equipment": cs.equipment,
                    "backstory": cs.backstory,
                }
                yield {
                    "event": "game_state",
                    "data": json.dumps({"character_sheet": character_data}),
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
            agent_instances = {
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
            final_choices = ["Look around", "Wait", "Leave"]  # Default fallback

            # Execute each agent and stream responses
            for agent_name in routing.agents:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": agent_name}),
                }

                # Run agent in executor to not block
                agent = agent_instances.get(agent_name)
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
                        final_choices = structured_response.choices
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
                "data": json.dumps({"choices": final_choices}),
            }

            # Update session state
            await sm.add_exchange(state.session_id, action, full_narrative)
            await sm.update_recent_agents(state.session_id, routing.agents)
            await sm.set_choices(state.session_id, final_choices)

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
project_root = Path(__file__).parent.parent.parent.parent
static_dir = project_root / "static"


@router.get("/")
async def read_root() -> FileResponse:
    """Serve the index.html file."""
    return FileResponse(static_dir / "index.html")


def mount_static_files(app: Any) -> None:
    """Mount static files on the given FastAPI app.

    This should be called after including the router to ensure
    static files are properly mounted.

    Args:
        app: FastAPI application instance
    """
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
