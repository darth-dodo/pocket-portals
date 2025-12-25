"""Keeper agent - handles game mechanics without slowing the story."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class KeeperAgent:
    """Keeper agent that handles game mechanics with terse, numbers-first language."""

    def __init__(self) -> None:
        """Initialize the Keeper agent from YAML config."""
        config = load_agent_config("keeper")

        self.llm = LLM(
            model="anthropic/claude-3-5-haiku-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.3,
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

    def respond(self, action: str, context: str = "") -> str:
        """Generate keeper response to player action.

        Provides the standard interface expected by the conversation flow.

        Args:
            action: The player's action
            context: Optional conversation history

        Returns:
            Mechanical resolution of the action
        """
        return self.resolve_action(action=action, context=context)

    def resolve_action(
        self, action: str, context: str = "", difficulty: int = 12
    ) -> str:
        """Resolve a game action mechanically.

        Args:
            action: The action being attempted
            context: Optional context from previous conversation
            difficulty: Target number to succeed (default 12)

        Returns:
            Brief mechanical resolution
        """
        task_config = load_task_config("resolve_action")

        description = task_config.description.format(
            action=action,
            difficulty=difficulty,
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
