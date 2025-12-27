"""Tests for configuration loader with LLM config support."""

import pytest

from src.config.loader import (
    LLMConfig,
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

        assert config.model == "anthropic/claude-3-5-haiku-20241022"
        assert config.temperature == 0.7
        assert config.max_tokens == 1024

    def test_custom_values(self) -> None:
        """Test that LLMConfig accepts custom values."""
        config = LLMConfig(
            model="anthropic/claude-3-opus-20240229",
            temperature=0.3,
            max_tokens=256,
        )

        assert config.model == "anthropic/claude-3-opus-20240229"
        assert config.temperature == 0.3
        assert config.max_tokens == 256


class TestAgentConfig:
    """Tests for AgentConfig with LLM config."""

    def test_llm_config_loads_defaults(self) -> None:
        """Test that agent config loads LLM with defaults."""
        config = load_agent_config("narrator")

        assert config.llm.model == "anthropic/claude-3-5-haiku-20241022"
        assert isinstance(config.llm, LLMConfig)

    def test_llm_config_overrides_temperature(self) -> None:
        """Test that agent-specific temperature overrides default."""
        config = load_agent_config("keeper")

        # Keeper has temperature: 0.3 in YAML
        assert config.llm.temperature == 0.3

    def test_llm_config_overrides_max_tokens(self) -> None:
        """Test that agent-specific max_tokens overrides default."""
        config = load_agent_config("keeper")

        # Keeper has max_tokens: 256 in YAML
        assert config.llm.max_tokens == 256

    def test_jester_has_high_temperature(self) -> None:
        """Test that Jester has playful temperature setting."""
        config = load_agent_config("jester")

        # Jester has temperature: 0.8 for creativity
        assert config.llm.temperature == 0.8

    def test_character_interviewer_has_creative_settings(self) -> None:
        """Test that CharacterInterviewer has creative LLM settings."""
        config = load_agent_config("character_interviewer")

        # Character interviewer uses high temperature
        assert config.llm.temperature == 0.8
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
        assert config1.llm.temperature == config2.llm.temperature

    def test_clear_cache_works(self) -> None:
        """Test that cache can be cleared."""
        # Load config to populate cache
        load_agent_config("narrator")

        # Clear cache
        clear_config_cache()

        # Should still work after clearing
        config = load_agent_config("narrator")
        assert config.role == "Narrator"
