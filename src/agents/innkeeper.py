"""Innkeeper agent - introduces quests and provides session bookends."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class InnkeeperAgent:
    """Innkeeper agent that welcomes adventurers and introduces quests."""

    def __init__(self) -> None:
        """Initialize the Innkeeper agent from YAML config."""
        config = load_agent_config("innkeeper_theron")

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

    def introduce_quest(self, character_description: str, context: str = "") -> str:
        """Introduce a quest to a new adventurer.

        Args:
            character_description: Description of the adventurer
            context: Optional context from previous conversation

        Returns:
            Quest introduction narrative
        """
        task_config = load_task_config("introduce_quest")

        description = task_config.description.format(
            character_description=character_description
        )

        if context:
            description = f"{context}\n\n{description}"

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
