"""Narrator agent - describes scenes with rich sensory detail."""

import logging
import time
from dataclasses import dataclass

from crewai import LLM, Agent, Task
from pydantic import BaseModel, Field

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings

logger = logging.getLogger(__name__)

# Generic choices that indicate poor contextual generation
GENERIC_CHOICES = frozenset(
    {
        "look around",
        "wait",
        "leave",
        "investigate further",
        "talk to someone nearby",
        "move to a new location",
        "explore the area",
        "search the room",
        "continue forward",
        "go back",
    }
)


@dataclass
class ChoiceQuality:
    """Quality metrics for generated choices."""

    generic_count: int
    contextual_count: int
    quality_score: float
    generic_choices: list[str]


def _analyze_choice_quality(choices: list[str]) -> ChoiceQuality:
    """Analyze the quality of generated choices.

    Args:
        choices: List of generated choice strings

    Returns:
        ChoiceQuality with metrics for observability
    """
    generic_matches = []
    for choice in choices:
        choice_lower = choice.lower().strip()
        if choice_lower in GENERIC_CHOICES:
            generic_matches.append(choice)

    generic_count = len(generic_matches)
    contextual_count = len(choices) - generic_count
    quality_score = contextual_count / len(choices) if choices else 0.0

    return ChoiceQuality(
        generic_count=generic_count,
        contextual_count=contextual_count,
        quality_score=quality_score,
        generic_choices=generic_matches,
    )


class NarratorResponse(BaseModel):
    """Structured response from the narrator agent.

    Contains both the narrative description and suggested player choices,
    enabling a single LLM call for both outputs. Also includes content
    safety assessment to avoid word-boundary issues with pattern matching.
    """

    content_safe: bool = Field(
        default=True,
        description="Set to false ONLY if the player's input contains genuinely "
        "inappropriate content: self-harm, explicit sexual content, graphic torture, "
        "or hate speech. Use good judgment - 'assassin', 'Scunthorpe', 'therapist' "
        "are safe words. Fantasy violence like 'attack the goblin' is allowed. "
        "When in doubt, it's safe.",
    )
    narrative: str = Field(
        description="A 2-4 sentence description of what happens in response to the "
        "player's action. Use second person, sensory details, and end with "
        "atmosphere or tension - NOT action suggestions. If content_safe is false, "
        "write a gentle redirection like 'You take a deep breath and focus on the "
        "adventure ahead. The path before you beckons with promise.'"
    )
    choices: list[str] = Field(
        description="Exactly 3 short action choices (max 6 words each) that DIRECTLY "
        "reference specific elements from YOUR narrative above. Each choice MUST "
        "mention a character, object, location, or situation you just described. "
        "NEVER use generic choices like 'Look around', 'Wait', 'Leave', or "
        "'Investigate further'. Be specific to the scene.",
        min_length=3,
        max_length=3,
    )


class NarratorAgent:
    """Narrator agent that creates immersive scene descriptions."""

    def __init__(self) -> None:
        """Initialize the narrator from YAML config."""
        config = load_agent_config("narrator")

        # CrewAI's native LLM class - config-driven
        self.llm = LLM(
            model=config.llm.model,
            api_key=settings.anthropic_api_key,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

        self.agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=config.verbose,
            allow_delegation=config.allow_delegation,
            llm=self.llm,
        )

    def respond(self, action: str, context: str = "") -> str:
        """Generate narrative response to player action.

        Args:
            action: The player's action
            context: Optional conversation history for continuity

        Returns:
            Narrative description of what happens
        """
        task_config = load_task_config("narrate_scene")

        description = task_config.description.format(action=action)

        if context:
            description = f"{context}\n\nCurrent action: {description}"

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)

    def respond_with_choices(self, action: str, context: str = "") -> NarratorResponse:
        """Generate narrative response AND contextual choices in a single LLM call.

        This is the preferred method for turn execution as it returns both
        the narrative and player choices in one structured response, avoiding
        a second LLM call for choice generation.

        Args:
            action: The player's action
            context: Optional conversation history for continuity

        Returns:
            NarratorResponse with narrative and 3 contextual choices
        """
        start_time = time.perf_counter()
        used_fallback = False

        task_config = load_task_config("narrate_scene")

        description = task_config.description.format(action=action)

        if context:
            description = f"{context}\n\nCurrent action: {description}"

        task = Task(
            description=description,
            expected_output="A narrative description and 3 scene-specific player choices",
            agent=self.agent,
            output_pydantic=NarratorResponse,
        )

        result = task.execute_sync()

        # Handle both Pydantic model and raw result
        if hasattr(result, "pydantic") and result.pydantic:
            pydantic_result = result.pydantic
            if isinstance(pydantic_result, NarratorResponse):
                response = pydantic_result
            else:
                # Fallback if pydantic result is wrong type
                used_fallback = True
                response = NarratorResponse(
                    narrative=str(pydantic_result),
                    choices=["Look around", "Wait", "Leave"],
                )
        elif isinstance(result, NarratorResponse):
            response = result
        else:
            # Fallback: return default choices with the raw narrative
            used_fallback = True
            response = NarratorResponse(
                narrative=str(result),
                choices=["Look around", "Wait", "Leave"],
            )

        # Observability: log choice generation metrics
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        quality = _analyze_choice_quality(response.choices)

        # Log content moderation if blocked
        if not response.content_safe:
            logger.warning(
                "content_moderation_blocked",
                extra={
                    "action": action[:100],  # Truncate for logging
                    "blocked_by": "narrator_agent",
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )

        logger.info(
            "narrator_response_generated",
            extra={
                "action": action[:100],  # Truncate for logging
                "narrative_length": len(response.narrative),
                "choices": response.choices,
                "choice_quality_score": quality.quality_score,
                "generic_count": quality.generic_count,
                "contextual_count": quality.contextual_count,
                "content_safe": response.content_safe,
                "used_fallback": used_fallback,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )

        # Warn if choices are too generic
        if quality.quality_score < 0.67:  # Less than 2/3 contextual
            logger.warning(
                "low_quality_choices_detected",
                extra={
                    "action": action[:100],
                    "choices": response.choices,
                    "generic_choices": quality.generic_choices,
                    "quality_score": quality.quality_score,
                },
            )

        return response

    def summarize_combat(
        self,
        combat_log: list[str],
        victory: bool,
        enemy_name: str,
        player_name: str,
    ) -> str:
        """Generate dramatic narrative summary of combat.

        This is the ONE LLM call for the entire combat.

        Args:
            combat_log: List of mechanical log entries
            victory: True if player won, False if defeated
            enemy_name: Name of the enemy fought
            player_name: Player character name

        Returns:
            2-4 sentence dramatic summary of the battle
        """
        task_config = load_task_config("summarize_combat")

        # Format combat log as numbered lines
        formatted_log = "\n".join(
            f"{i + 1}. {entry}" for i, entry in enumerate(combat_log)
        )

        # Determine outcome text
        outcome = "Victory" if victory else "Defeat"

        # Format the description with all context
        description = task_config.description.format(
            player_name=player_name,
            enemy_name=enemy_name,
            outcome=outcome,
            combat_log=formatted_log,
        )

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
