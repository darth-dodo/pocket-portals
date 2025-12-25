"""Narrator agent - describes scenes with rich sensory detail."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class NarratorAgent:
    """Narrator agent that creates immersive scene descriptions."""

    def __init__(self) -> None:
        """Initialize the narrator from YAML config."""
        config = load_agent_config("narrator")

        # CrewAI's native LLM class - no langchain needed
        self.llm = LLM(
            model="anthropic/claude-3-5-haiku-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.7,
            max_tokens=1024,
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
