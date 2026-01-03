"""Character creation handlers for Pocket Portals API.

This module contains handler functions for character creation flow,
including the interview process and character sheet generation.
"""

import logging
from typing import TYPE_CHECKING

from fastapi import Request

from src.api.constants import (
    STARTER_CHOICES_POOL,
    WELCOME_NARRATIVE,
)
from src.api.models import CharacterSheetData, NarrativeResponse
from src.state import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    GamePhase,
    GameState,
    SessionManager,
)

if TYPE_CHECKING:
    from src.agents.character_builder import CharacterBuilderAgent
    from src.agents.character_interviewer import CharacterInterviewerAgent
    from src.agents.quest_designer import QuestDesignerAgent

logger = logging.getLogger(__name__)


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state.

    Args:
        request: FastAPI Request object

    Returns:
        SessionManager: The session manager instance from app.state
    """
    return request.app.state.session_manager


async def handle_character_creation(
    request: Request,
    state: GameState,
    action: str,
    character_interviewer: "CharacterInterviewerAgent | None",
    character_builder: "CharacterBuilderAgent | None",
    quest_designer: "QuestDesignerAgent | None",
) -> NarrativeResponse:
    """Handle actions during character creation phase.

    Args:
        request: FastAPI Request object (to access app.state)
        state: Current game state
        action: Player's action/response
        character_interviewer: Character interviewer agent instance
        character_builder: Character builder agent instance
        quest_designer: Quest designer agent instance

    Returns:
        NarrativeResponse with innkeeper's next question or character sheet
    """
    sm = get_session_manager(request)

    # Increment creation turn
    new_turn = await sm.increment_creation_turn(state.session_id)

    # Check if user wants to skip
    if "skip" in action.lower():
        return await _handle_skip_character_creation(request, state, action, sm)

    # If we've completed 5 turns, generate character sheet and transition
    if new_turn >= 5:
        return await _handle_character_creation_complete(
            request,
            state,
            action,
            sm,
            character_interviewer,
            character_builder,
            quest_designer,
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


async def _handle_skip_character_creation(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
) -> NarrativeResponse:
    """Handle skipping character creation with a default character.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's action
        sm: Session manager instance

    Returns:
        NarrativeResponse with default character and welcome narrative
    """
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
        narrative=WELCOME_NARRATIVE,
        session_id=state.session_id,
        choices=choices,
        character_sheet=character_sheet_data,
    )


async def _handle_character_creation_complete(
    request: Request,
    state: GameState,
    action: str,
    sm: SessionManager,
    character_interviewer: "CharacterInterviewerAgent | None",
    character_builder: "CharacterBuilderAgent | None",
    quest_designer: "QuestDesignerAgent | None",
) -> NarrativeResponse:
    """Handle completion of character creation interview.

    Args:
        request: FastAPI Request object
        state: Current game state
        action: Player's final action
        sm: Session manager instance
        character_interviewer: Character interviewer agent
        character_builder: Character builder agent
        quest_designer: Quest designer agent

    Returns:
        NarrativeResponse with character sheet and quest introduction
    """
    # Build character from conversation history (include current action)
    await sm.add_exchange(state.session_id, action, "")
    updated_state = await sm.get_or_create_session(state.session_id)
    character_sheet = generate_character_from_history(updated_state, character_builder)
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
            narrative, choices = _generate_fallback_transition(
                character_sheet, character_interviewer
            )
    else:
        # No quest designer available - use adventure hooks
        narrative, choices = _generate_fallback_transition(
            character_sheet, character_interviewer
        )

    await sm.set_choices(state.session_id, choices)

    return NarrativeResponse(
        narrative=narrative,
        session_id=state.session_id,
        choices=choices,
    )


def _generate_fallback_transition(
    character_sheet: CharacterSheet,
    character_interviewer: "CharacterInterviewerAgent | None",
) -> tuple[str, list[str]]:
    """Generate fallback narrative and choices when quest generation fails.

    Args:
        character_sheet: Generated character sheet
        character_interviewer: Character interviewer agent

    Returns:
        Tuple of (narrative, choices)
    """
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

    return narrative, choices


def generate_character_from_history(
    state: GameState,
    character_builder: "CharacterBuilderAgent | None",
) -> CharacterSheet:
    """Generate a character sheet from conversation history.

    Uses CharacterBuilderAgent for intelligent stat generation based on
    the 5-turn character interview. Falls back to keyword-based generation
    if the agent fails or is unavailable.

    Args:
        state: Game state with conversation history
        character_builder: Character builder agent instance

    Returns:
        Generated CharacterSheet with intelligent stats
    """
    # Build conversation history string for the agent
    history_lines = []
    for entry in state.conversation_history:
        if entry.get("action"):
            history_lines.append(f"Player: {entry['action']}")
        if entry.get("narrative"):
            history_lines.append(f"Innkeeper: {entry['narrative']}")
    conversation_history = "\n".join(history_lines)

    # Try using CharacterBuilderAgent for intelligent stat generation
    if character_builder and conversation_history:
        try:
            logger.info("CharacterBuilder: Generating character from interview")
            character_sheet = character_builder.build_character(conversation_history)
            logger.info(
                f"CharacterBuilder: Created {character_sheet.name} the "
                f"{character_sheet.race.value} {character_sheet.character_class.value}"
            )
            return character_sheet
        except Exception as e:
            logger.warning(f"CharacterBuilder failed, using fallback: {e}")

    # Fallback to keyword-based generation
    return _generate_character_from_keywords(state)


def _generate_character_from_keywords(state: GameState) -> CharacterSheet:
    """Generate a character sheet using keyword-based heuristics.

    Args:
        state: Game state with conversation history

    Returns:
        Generated CharacterSheet based on keyword matching
    """
    logger.info("CharacterBuilder: Using keyword-based fallback")
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
