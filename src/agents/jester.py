"""Jester agent - adds complications and meta-commentary."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class JesterAgent:
    """Jester agent that adds complications and meta-commentary."""

    def __init__(self) -> None:
        """Initialize the jester from YAML config."""
        config = load_agent_config("jester")

        # CrewAI's native LLM class - playful and surprising
        self.llm = LLM(
            model="anthropic/claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            temperature=0.8,
            max_tokens=256,
        )

        self.agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=config.verbose,
            allow_delegation=config.allow_delegation,
            llm=self.llm,
        )

    def add_complication(self, situation: str, context: str = "") -> str:
        """Add meta-commentary or complication to a situation.

        Args:
            situation: The current game situation
            context: Optional additional context

        Returns:
            Brief meta-commentary or complication
        """
        task_config = load_task_config("add_commentary")

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
