"""Adventure pacing system for narrative arc management.

This module provides pacing context and utilities to guide agents through
a structured 50-turn adventure with clear narrative phases.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field

from src.state.models import AdventurePhase, GameState


class PacingContext(BaseModel):
    """Pacing information passed to agents for narrative guidance.

    This context helps agents understand where they are in the story
    arc and adjust their output accordingly.

    Attributes:
        current_turn: Current turn number in the adventure (1-50)
        max_turns: Maximum turns for this adventure (default 50)
        turns_remaining: Number of turns left in the adventure
        current_phase: Current narrative phase (SETUP through DENOUEMENT)
        urgency_level: Urgency factor from 0.0-1.0, increases as adventure progresses
        directive: Narrative directive (ESTABLISH, DEVELOP, etc.)
        quest_progress: Progress toward quest completion (0.0-1.0)
    """

    current_turn: int = Field(ge=0, le=100)
    max_turns: int = Field(default=50, ge=25, le=100)
    turns_remaining: int = Field(ge=0)
    current_phase: AdventurePhase
    urgency_level: float = Field(ge=0.0, le=1.0)
    directive: str
    quest_progress: float = Field(default=0.0, ge=0.0, le=1.0)

    @computed_field
    @property
    def is_early_game(self) -> bool:
        """Check if adventure is in early game (turns 1-15).

        Returns:
            True if current turn is 15 or less
        """
        return self.current_turn <= 15

    @computed_field
    @property
    def is_late_game(self) -> bool:
        """Check if adventure is in late game (turns 35+).

        Returns:
            True if current turn is 35 or greater
        """
        return self.current_turn >= 35

    @computed_field
    @property
    def should_build_tension(self) -> bool:
        """Check if current phase should focus on building tension.

        Returns:
            True if in RISING_ACTION or MID_POINT phases
        """
        return self.current_phase in (
            AdventurePhase.RISING_ACTION,
            AdventurePhase.MID_POINT,
        )

    @computed_field
    @property
    def should_resolve(self) -> bool:
        """Check if current phase should focus on resolution.

        Returns:
            True if in DENOUEMENT phase
        """
        return self.current_phase == AdventurePhase.DENOUEMENT


def calculate_quest_progress(state: GameState) -> float:
    """Calculate quest completion progress as a float 0.0-1.0.

    Args:
        state: Current game state with quest information

    Returns:
        Float from 0.0 to 1.0 representing quest progress
    """
    if not state.active_quest:
        return 0.0

    objectives = state.active_quest.objectives
    if not objectives:
        return 0.0

    completed = sum(1 for obj in objectives if obj.is_completed)
    return completed / len(objectives)


def calculate_urgency(state: GameState) -> float:
    """Calculate urgency level (0.0-1.0) based on adventure progress.

    Urgency increases as:
    - Adventure progresses toward turn limit
    - Quest nears completion
    - Critical narrative moments occur

    Args:
        state: Current game state

    Returns:
        Float from 0.0 to 1.0 representing urgency level
    """
    # Base urgency from turn progress
    turn_urgency = state.adventure_turn / state.max_turns

    # Quest progress modifier (adds up to 0.2)
    quest_modifier = calculate_quest_progress(state) * 0.2

    # Phase modifier - different phases have different base urgency
    phase_modifiers = {
        AdventurePhase.SETUP: 0.0,
        AdventurePhase.RISING_ACTION: 0.1,
        AdventurePhase.MID_POINT: 0.2,
        AdventurePhase.CLIMAX: 0.4,
        AdventurePhase.DENOUEMENT: 0.3,  # Slightly lower - winding down
    }
    phase_modifier = phase_modifiers.get(state.adventure_phase, 0.0)

    # Combine and clamp to 1.0
    urgency = turn_urgency + quest_modifier + phase_modifier
    return min(1.0, urgency)


def get_pacing_directive(state: GameState) -> str:
    """Get narrative directive based on current phase and progress.

    Directives guide agent behavior for the current narrative moment.

    Args:
        state: Current game state

    Returns:
        String directive for agents (e.g., "ESTABLISH - Introduce character and world")
    """
    phase = state.adventure_phase
    turn = state.adventure_turn

    if phase == AdventurePhase.SETUP:
        return "ESTABLISH - Introduce character and world"

    elif phase == AdventurePhase.RISING_ACTION:
        if turn < 10:
            return "DEVELOP - Build quest engagement"
        else:
            return "ESCALATE - Increase tension and stakes"

    elif phase == AdventurePhase.MID_POINT:
        return "REVEAL - Introduce twist or major revelation"

    elif phase == AdventurePhase.CLIMAX:
        if turn >= 40:
            return "CONFRONT - Drive toward final confrontation"
        else:
            return "INTENSIFY - Build maximum tension"

    else:  # DENOUEMENT
        return "RESOLVE - Wind down and provide closure"


def build_pacing_context(state: GameState) -> PacingContext:
    """Build a PacingContext from the current game state.

    Args:
        state: Current game state

    Returns:
        PacingContext with all pacing information calculated
    """
    return PacingContext(
        current_turn=state.adventure_turn,
        max_turns=state.max_turns,
        turns_remaining=state.max_turns - state.adventure_turn,
        current_phase=state.adventure_phase,
        urgency_level=calculate_urgency(state),
        directive=get_pacing_directive(state),
        quest_progress=calculate_quest_progress(state),
    )


def format_pacing_hint(pacing: PacingContext) -> str:
    """Format pacing context as a hint string for agents.

    This creates a structured hint that agents can use to adjust
    their narrative output based on the current adventure state.

    Args:
        pacing: PacingContext with current pacing information

    Returns:
        Formatted string with pacing information for agent context
    """
    return f"""[NARRATIVE PACING - Turn {pacing.current_turn}/{pacing.max_turns}]
Phase: {pacing.current_phase.value.upper()}
Urgency: {pacing.urgency_level:.0%}
Directive: {pacing.directive}
Quest Progress: {pacing.quest_progress:.0%}"""


class ClosureStatus(BaseModel):
    """Result of closure trigger check.

    Attributes:
        should_trigger_epilogue: True if adventure should end
        reason: Reason for closure (quest_complete, hard_cap, or None)
        turns_remaining: Number of turns remaining until hard cap
    """

    should_trigger_epilogue: bool
    reason: str | None
    turns_remaining: int


def check_closure_triggers(state: GameState) -> ClosureStatus:
    """Check if adventure should end.

    Evaluates closure conditions in order of priority:
    1. Hard cap at max_turns (default 50) - adventure ends regardless
    2. Quest completion after turn 25 - allows quest-driven endings

    Args:
        state: Current game state with quest and turn information

    Returns:
        ClosureStatus with should_trigger_epilogue, reason, and turns_remaining
    """
    turns_remaining = state.max_turns - state.adventure_turn
    quest_progress = calculate_quest_progress(state)

    # Hard cap at max_turns
    if state.adventure_turn >= state.max_turns:
        return ClosureStatus(
            should_trigger_epilogue=True,
            reason="hard_cap",
            turns_remaining=0,
        )

    # Quest-driven ending (after turn 25 to ensure minimum adventure length)
    if quest_progress >= 1.0 and state.adventure_turn >= 25:
        return ClosureStatus(
            should_trigger_epilogue=True,
            reason="quest_complete",
            turns_remaining=turns_remaining,
        )

    # Adventure continues
    return ClosureStatus(
        should_trigger_epilogue=False,
        reason=None,
        turns_remaining=turns_remaining,
    )
