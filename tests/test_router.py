"""Tests for AgentRouter."""

from unittest.mock import patch

import pytest

from src.engine.router import AgentRouter, RoutingDecision
from src.state.models import GamePhase


class TestAgentRouter:
    """Test suite for AgentRouter class."""

    @pytest.fixture
    def router(self) -> AgentRouter:
        """Create an AgentRouter instance."""
        return AgentRouter()

    def test_exploration_phase_routes_to_narrator_by_default(
        self, router: AgentRouter
    ) -> None:
        """Test that exploration phase routes to narrator by default."""
        action = "I walk down the hallway"
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        decision = router.route(action, phase, recent_agents)

        assert "narrator" in decision.agents
        assert len(decision.agents) == 1
        assert decision.include_jester is False
        assert "exploration" in decision.reason.lower()

    def test_mechanical_keywords_trigger_keeper_inclusion(
        self, router: AgentRouter
    ) -> None:
        """Test that mechanical keywords trigger keeper inclusion."""
        mechanical_actions = [
            "I attack the goblin",
            "I fight the dragon",
            "I roll for initiative",
            "I cast fireball",
            "I defend against the blow",
            "I dodge the arrow",
        ]
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        for action in mechanical_actions:
            decision = router.route(action, phase, recent_agents)

            assert "keeper" in decision.agents
            assert "narrator" in decision.agents
            assert len(decision.agents) == 2
            assert "mechanical" in decision.reason.lower()

    def test_jester_injection_based_on_probability(self, router: AgentRouter) -> None:
        """Test that jester is injected based on probability."""
        action = "I walk down the hallway"
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        # Test when random roll triggers jester (< 0.15)
        with patch("random.random", return_value=0.10):
            decision = router.route(action, phase, recent_agents)
            assert decision.include_jester is True
            assert "jester" in decision.reason.lower()

        # Test when random roll doesn't trigger jester (>= 0.15)
        with patch("random.random", return_value=0.20):
            decision = router.route(action, phase, recent_agents)
            assert decision.include_jester is False

    def test_jester_cooldown_prevents_spam(self, router: AgentRouter) -> None:
        """Test that jester cooldown prevents spam."""
        action = "I walk down the hallway"
        phase = GamePhase.EXPLORATION

        # Recent agents with jester in last 3 positions
        recent_with_jester = ["narrator", "jester", "narrator"]

        # Even with favorable random roll, jester should not appear
        with patch("random.random", return_value=0.10):
            decision = router.route(action, phase, recent_with_jester)
            assert decision.include_jester is False
            assert "cooldown" in decision.reason.lower()

    def test_jester_cooldown_expires_after_three_turns(
        self, router: AgentRouter
    ) -> None:
        """Test that jester can appear again after cooldown expires."""
        action = "I walk down the hallway"
        phase = GamePhase.EXPLORATION

        # Recent agents with jester outside last 3 positions
        # Last 3 are: narrator, keeper, narrator (no jester)
        recent_agents = ["jester", "narrator", "keeper", "narrator"]

        # Jester should be able to appear again
        with patch("random.random", return_value=0.10):
            decision = router.route(action, phase, recent_agents)
            assert decision.include_jester is True

    def test_returns_routing_decision_with_required_fields(
        self, router: AgentRouter
    ) -> None:
        """Test that route returns RoutingDecision with all required fields."""
        action = "I explore the room"
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        decision = router.route(action, phase, recent_agents)

        assert isinstance(decision, RoutingDecision)
        assert hasattr(decision, "agents")
        assert hasattr(decision, "include_jester")
        assert hasattr(decision, "reason")
        assert isinstance(decision.agents, list)
        assert isinstance(decision.include_jester, bool)
        assert isinstance(decision.reason, str)

    def test_combat_phase_includes_keeper(self, router: AgentRouter) -> None:
        """Test that combat phase always includes keeper."""
        action = "I wait for my turn"
        phase = GamePhase.COMBAT
        recent_agents: list[str] = []

        decision = router.route(action, phase, recent_agents)

        assert "keeper" in decision.agents
        assert "narrator" in decision.agents
        assert "combat" in decision.reason.lower()

    def test_dialogue_phase_routes_to_narrator(self, router: AgentRouter) -> None:
        """Test that dialogue phase routes to narrator."""
        action = "I ask the merchant about prices"
        phase = GamePhase.DIALOGUE
        recent_agents: list[str] = []

        decision = router.route(action, phase, recent_agents)

        assert "narrator" in decision.agents
        assert "dialogue" in decision.reason.lower()

    def test_multiple_mechanical_keywords_still_single_keeper(
        self, router: AgentRouter
    ) -> None:
        """Test that multiple mechanical keywords don't duplicate keeper."""
        action = "I attack and fight and roll to hit"
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        decision = router.route(action, phase, recent_agents)

        assert decision.agents.count("keeper") == 1
        assert "narrator" in decision.agents

    def test_case_insensitive_mechanical_keyword_matching(
        self, router: AgentRouter
    ) -> None:
        """Test that mechanical keyword matching is case-insensitive."""
        actions = [
            "I ATTACK the enemy",
            "I Attack the enemy",
            "I aTtAcK the enemy",
        ]
        phase = GamePhase.EXPLORATION
        recent_agents: list[str] = []

        for action in actions:
            decision = router.route(action, phase, recent_agents)
            assert "keeper" in decision.agents
