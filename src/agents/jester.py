"""Jester agent - adds complications and meta-commentary."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class JesterAgent:
    """Jester agent that adds complications and meta-commentary."""

    def __init__(self) -> None:
        """Initialize the jester from YAML config."""
        config = load_agent_config("jester")

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
        """Generate jester response to player action.

        Provides the standard interface expected by the conversation flow.

        Args:
            action: The player's action
            context: Optional conversation history

        Returns:
            Jester's meta-commentary or complication
        """
        return self.add_complication(situation=action, context=context)

    def add_complication(self, situation: str, context: str = "") -> str:
        """Add meta-commentary or complication to a situation.

        Args:
            situation: The current game situation
            context: Optional additional context
        """
        task_config = load_task_config("add_commentary")

        # Include context if available
        description = task_config.description.format(situation=situation)
        if context:
            description = f"{context}\n\n{description}"

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
