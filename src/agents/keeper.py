"""Keeper agent - handles game mechanics without slowing the story."""

from pathlib import Path

import yaml
from crewai import LLM, Agent, Task

from src.settings import settings

# Load agent config from YAML
CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_agent_config(agent_name: str) -> dict:
    """Load agent configuration from agents.yaml."""
    with open(CONFIG_DIR / "agents.yaml") as f:
        agents = yaml.safe_load(f)
    return agents[agent_name]


def load_task_config(task_name: str) -> dict:
    """Load task configuration from tasks.yaml."""
    with open(CONFIG_DIR / "tasks.yaml") as f:
        tasks = yaml.safe_load(f)
    return tasks[task_name]


class KeeperAgent:
    """Keeper agent that handles game mechanics with terse, numbers-first language."""

    def __init__(self) -> None:
        """Initialize the keeper from YAML config."""
        config = load_agent_config("keeper")

        # CrewAI's native LLM class - mechanical and precise
        self.llm = LLM(
            model="anthropic/claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            temperature=0.3,
            max_tokens=256,
        )

        self.agent = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", False),
            allow_delegation=config.get("allow_delegation", False),
            llm=self.llm,
        )

    def resolve_action(
        self, action: str, context: str = "", difficulty: int = 12
    ) -> str:
        """Resolve game mechanics for player action.

        Args:
            action: The player's action to resolve
            context: Optional current situation context
            difficulty: Optional difficulty number (default: 12)
        """
        task_config = load_task_config("resolve_action")

        # Include context if available
        description = task_config["description"].format(
            action=action, context=context or "Unknown situation"
        )

        task = Task(
            description=description,
            expected_output=task_config["expected_output"],
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
