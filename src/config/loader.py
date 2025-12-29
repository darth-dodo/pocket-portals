"""Configuration loader with Pydantic models for type safety."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration for an agent."""

    model: str = "anthropic/claude-3-5-haiku-20241022"
    temperature: float = 0.7
    max_tokens: int = 1024


class AgentConfig(BaseModel):
    """Configuration for a CrewAI agent."""

    role: str
    goal: str
    backstory: str
    verbose: bool = False
    allow_delegation: bool = False
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: bool = False


class TaskConfig(BaseModel):
    """Configuration for a CrewAI task."""

    description: str
    expected_output: str


CONFIG_DIR = Path(__file__).parent

# Config cache to avoid repeated file reads
_config_cache: dict[str, Any] = {}


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load YAML file with caching."""
    if filename not in _config_cache:
        with open(CONFIG_DIR / filename) as f:
            _config_cache[filename] = yaml.safe_load(f)
    return _config_cache[filename]


def clear_config_cache() -> None:
    """Clear the config cache. Useful for testing."""
    _config_cache.clear()


def load_agent_config(agent_name: str) -> AgentConfig:
    """Load agent configuration from agents.yaml with default merging."""
    agents = _load_yaml("agents.yaml")

    # Get defaults (if present)
    defaults = agents.get("defaults", {})
    default_llm = defaults.get("llm", {})

    # Get agent-specific config
    agent_data = agents[agent_name].copy()

    # Merge LLM config: defaults + agent-specific overrides
    agent_llm = agent_data.get("llm", {})
    merged_llm = {**default_llm, **agent_llm}
    agent_data["llm"] = merged_llm

    return AgentConfig(**agent_data)


def load_task_config(task_name: str) -> TaskConfig:
    """Load task configuration from tasks.yaml."""
    tasks = _load_yaml("tasks.yaml")
    return TaskConfig(**tasks[task_name])
