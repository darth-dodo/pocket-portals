"""Innkeeper agent - introduces quests and provides session bookends."""

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


class InnkeeperAgent:
    """Innkeeper agent that welcomes adventurers and introduces quests."""

    def __init__(self) -> None:
        """Initialize the innkeeper from YAML config."""
        config = load_agent_config("innkeeper_theron")

        # CrewAI's native LLM class - no langchain needed
        self.llm = LLM(
            model="anthropic/claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            temperature=0.6,
            max_tokens=512,
        )

        self.agent = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            llm=self.llm,
        )

    def introduce_quest(self, character_description: str, context: str = "") -> str:
        """Introduce a quest to a new adventurer.

        Args:
            character_description: Description of the adventurer
            context: Optional additional context for the quest introduction
        """
        task_config = load_task_config("introduce_quest")

        # Include context if available
        description = task_config["description"].format(
            character_description=character_description
        )
        if context:
            description = f"{context}\n\n{description}"

        task = Task(
            description=description,
            expected_output=task_config["expected_output"],
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
