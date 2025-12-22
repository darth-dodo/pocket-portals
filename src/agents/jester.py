"""Jester agent - adds complications and meta-commentary."""

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
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            llm=self.llm,
        )

    def add_complication(self, situation: str, context: str = "") -> str:
        """Add meta-commentary or complication to a situation.

        Args:
            situation: The current game situation
            context: Optional additional context
        """
        task_config = load_task_config("add_commentary")

        # Include context if available
        description = task_config["description"].format(situation=situation)
        if context:
            description = f"{context}\n\n{description}"

        task = Task(
            description=description,
            expected_output=task_config["expected_output"],
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
