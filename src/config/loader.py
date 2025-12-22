"""Configuration loader with Pydantic models for type safety."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for a CrewAI agent."""

    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False


class TaskConfig(BaseModel):
    """Configuration for a CrewAI task."""

    description: str
    expected_output: str


CONFIG_DIR = Path(__file__).parent


def load_agent_config(agent_name: str) -> AgentConfig:
    """Load agent configuration from agents.yaml."""
    with open(CONFIG_DIR / "agents.yaml") as f:
        agents = yaml.safe_load(f)
    return AgentConfig(**agents[agent_name])


def load_task_config(task_name: str) -> TaskConfig:
    """Load task configuration from tasks.yaml."""
    with open(CONFIG_DIR / "tasks.yaml") as f:
        tasks = yaml.safe_load(f)
    return TaskConfig(**tasks[task_name])
