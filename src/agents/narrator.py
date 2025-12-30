"""Narrator agent - describes scenes with rich sensory detail."""

from crewai import LLM, Agent, Task
from pydantic import BaseModel, Field

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class NarratorResponse(BaseModel):
    """Structured response from the narrator agent.

    Contains both the narrative description and suggested player choices,
    enabling a single LLM call for both outputs.
    """

    narrative: str = Field(
        description="The narrative description of what happens in response to the player's action. "
        "Should be 2-4 sentences of immersive, sensory-rich storytelling."
    )
    choices: list[str] = Field(
        description="Exactly 3 short action choices (max 6 words each) the player could take next. "
        "These should be contextually relevant to the scene.",
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
        task_config = load_task_config("narrate_scene")

        description = task_config.description.format(action=action)

        if context:
            description = f"{context}\n\nCurrent action: {description}"

        # Add instruction for choices
        description += (
            "\n\nAfter describing what happens, also suggest exactly 3 short "
            "action choices (max 6 words each) the player could take next."
        )

        task = Task(
            description=description,
            expected_output="A narrative description and 3 player choices",
            agent=self.agent,
            output_pydantic=NarratorResponse,
        )

        result = task.execute_sync()

        # Handle both Pydantic model and raw result
        if hasattr(result, "pydantic") and result.pydantic:
            return result.pydantic
        elif isinstance(result, NarratorResponse):
            return result
        else:
            # Fallback: return default choices with the raw narrative
            return NarratorResponse(
                narrative=str(result),
                choices=["Look around", "Wait", "Leave"],
            )

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
