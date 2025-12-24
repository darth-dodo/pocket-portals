"""Agent routing logic for Pocket Portals."""

import random
from dataclasses import dataclass

from src.state.models import GamePhase


@dataclass
class RoutingDecision:
    """Decision result from agent routing.

    Attributes:
        agents: List of agent identifiers to include in the response
        include_jester: Whether to include jester agent for chaos injection
        reason: Explanation of why this routing decision was made
    """

    agents: list[str]
    include_jester: bool
    reason: str


class AgentRouter:
    """Routes player actions to appropriate agents based on context.

    The router determines which specialized agents should handle a player's
    action based on the current game phase, action content, and recent agent
    history. It manages the inclusion of mechanical (keeper) and chaos (jester)
    agents to create dynamic gameplay.

    Attributes:
        JESTER_PROBABILITY: Chance (0.0-1.0) of jester appearing on any given turn
        JESTER_COOLDOWN: Number of recent turns that must pass before jester can appear again
        MECHANICAL_KEYWORDS: Action keywords that trigger keeper (rules) agent inclusion
    """

    JESTER_PROBABILITY = 0.15
    JESTER_COOLDOWN = 3
    MECHANICAL_KEYWORDS = [
        "attack",
        "fight",
        "roll",
        "cast",
        "defend",
        "dodge",
        "swing",
        "shoot",
        "hit",
        "strike",
    ]

    def route(
        self,
        action: str,
        phase: GamePhase,
        recent_agents: list[str],
    ) -> RoutingDecision:
        """Route an action to appropriate agents.

        Args:
            action: The player's action text
            phase: Current game phase (exploration, combat, dialogue)
            recent_agents: List of recently used agents, most recent last

        Returns:
            RoutingDecision containing agents to use and jester inclusion flag
        """
        agents = []
        include_jester = False
        reason_parts = []

        # Always include narrator as base agent
        agents.append("narrator")
        reason_parts.append(f"{phase.value} phase")

        # Check if action contains mechanical keywords (case-insensitive)
        action_lower = action.lower()
        has_mechanical_keyword = any(
            keyword in action_lower for keyword in self.MECHANICAL_KEYWORDS
        )

        # Include keeper for mechanical actions or combat phase
        if has_mechanical_keyword or phase == GamePhase.COMBAT:
            if "keeper" not in agents:
                agents.append("keeper")
            if has_mechanical_keyword:
                reason_parts.append("mechanical action detected")
            if phase == GamePhase.COMBAT:
                reason_parts.append("combat requires rules")

        # Check for jester inclusion
        jester_in_recent = self._is_jester_in_cooldown(recent_agents)

        if jester_in_recent:
            reason_parts.append("jester on cooldown")
        else:
            # Roll for jester appearance
            if random.random() < self.JESTER_PROBABILITY:
                include_jester = True
                reason_parts.append("jester chaos injection")

        reason = "; ".join(reason_parts)

        return RoutingDecision(
            agents=agents,
            include_jester=include_jester,
            reason=reason,
        )

    def _is_jester_in_cooldown(self, recent_agents: list[str]) -> bool:
        """Check if jester has appeared in recent turns.

        Args:
            recent_agents: List of recently used agents, most recent last

        Returns:
            True if jester appeared in last JESTER_COOLDOWN turns
        """
        # Check last N agents for jester
        recent_window = recent_agents[-self.JESTER_COOLDOWN :]
        return "jester" in recent_window
