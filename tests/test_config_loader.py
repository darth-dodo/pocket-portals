"""Tests for configuration loader with LLM config support."""

import pytest

from src.agents.character_builder import CharacterBuilderAgent
from src.agents.character_interviewer import CharacterInterviewerAgent
from src.agents.epilogue import EpilogueAgent
from src.agents.innkeeper import InnkeeperAgent
from src.agents.jester import JesterAgent
from src.agents.keeper import KeeperAgent
from src.agents.narrator import NarratorAgent
from src.agents.quest_designer import QuestDesignerAgent
from src.config.loader import (
    LLMConfig,
    _load_yaml,
    clear_config_cache,
    load_agent_config,
)


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear config cache before each test."""
    clear_config_cache()


class TestLLMConfig:
    """Tests for LLMConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Test that LLMConfig has sensible defaults."""
        config = LLMConfig()

        assert config.model == "anthropic/claude-haiku-4-5"
        assert config.max_tokens == 1024

    def test_custom_values(self) -> None:
        """Test that LLMConfig accepts custom values."""
        config = LLMConfig(
            model="anthropic/claude-sonnet-4-6",
            max_tokens=256,
        )

        assert config.model == "anthropic/claude-sonnet-4-6"
        assert config.max_tokens == 256


class TestAgentConfig:
    """Tests for AgentConfig with LLM config."""

    def test_llm_config_loads_defaults(self) -> None:
        """Test that agent config loads LLM with defaults."""
        config = load_agent_config("narrator")

        assert config.llm.model == "anthropic/claude-haiku-4-5"
        assert isinstance(config.llm, LLMConfig)

    def test_llm_config_overrides_model(self) -> None:
        """Test that agent-specific model overrides default."""
        config = load_agent_config("epilogue")

        # Epilogue uses Sonnet in YAML
        assert config.llm.model == "anthropic/claude-sonnet-4-6"

    def test_llm_config_overrides_max_tokens(self) -> None:
        """Test that agent-specific max_tokens overrides default."""
        config = load_agent_config("keeper")

        # Keeper has max_tokens: 256 in YAML
        assert config.llm.max_tokens == 256

    def test_character_interviewer_has_own_settings(self) -> None:
        """Test that CharacterInterviewer has its own LLM settings."""
        config = load_agent_config("character_interviewer")

        assert config.llm.max_tokens == 512

    def test_memory_field_exists(self) -> None:
        """Test that memory field is available on agent config."""
        narrator = load_agent_config("narrator")
        keeper = load_agent_config("keeper")

        # Narrator has memory enabled, Keeper doesn't
        assert narrator.memory is True
        assert keeper.memory is False


class TestConfigCaching:
    """Tests for config file caching."""

    def test_config_caching_works(self) -> None:
        """Test that config caching prevents repeated file reads."""
        # First load
        config1 = load_agent_config("narrator")

        # Second load should use cache
        config2 = load_agent_config("narrator")

        # Should return equivalent configs
        assert config1.role == config2.role
        assert config1.llm.max_tokens == config2.llm.max_tokens

    def test_clear_cache_works(self) -> None:
        """Test that cache can be cleared."""
        # Load config to populate cache
        load_agent_config("narrator")

        # Clear cache
        clear_config_cache()

        # Should still work after clearing
        config = load_agent_config("narrator")
        assert config.role == "Narrator"


AGENT_CLASSES = [
    CharacterBuilderAgent,
    CharacterInterviewerAgent,
    EpilogueAgent,
    InnkeeperAgent,
    JesterAgent,
    KeeperAgent,
    NarratorAgent,
    QuestDesignerAgent,
]

RETIRED_MODELS = (
    "claude-3-5-haiku-20241022",
    "claude-sonnet-4-20250514",
)


class TestAgentLLMSamplingParams:
    """Tests that agents build LLMs the current Anthropic API accepts.

    Anthropic rejects temperature, top_p and top_k on current models and
    API versions, so no agent may send them.
    """

    def test_llm_config_has_no_sampling_fields(self) -> None:
        """LLMConfig must not expose sampling knobs."""
        fields = set(LLMConfig.model_fields)

        assert "temperature" not in fields
        assert "top_p" not in fields
        assert "top_k" not in fields

    def test_agents_yaml_has_no_sampling_params(self) -> None:
        """No agent in agents.yaml may configure sampling params."""
        agents = _load_yaml("agents.yaml")

        for name, data in agents.items():
            llm = data.get("llm", {})
            for param in ("temperature", "top_p", "top_k"):
                assert param not in llm, f"{name} sets {param}"

    def test_agents_yaml_uses_no_retired_models(self) -> None:
        """No agent in agents.yaml may reference a retired model ID."""
        agents = _load_yaml("agents.yaml")

        for name, data in agents.items():
            model = data.get("llm", {}).get("model", "")
            assert not model.endswith(RETIRED_MODELS), f"{name} uses {model}"

    @pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
    def test_agent_llm_built_without_sampling_params(self, agent_cls: type) -> None:
        """Each agent's LLM is built without temperature or top_p."""
        agent = agent_cls()

        assert agent.llm.temperature is None
        assert getattr(agent.llm, "top_p", None) is None
        assert not agent.llm.model.endswith(RETIRED_MODELS)

    @pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
    def test_agent_request_params_omit_sampling_params(self, agent_cls: type) -> None:
        """The Anthropic request payload carries no sampling params."""
        agent = agent_cls()

        params = agent.llm._prepare_completion_params(
            messages=[{"role": "user", "content": "hi"}]
        )

        assert "temperature" not in params
        assert "top_p" not in params
        assert "top_k" not in params
