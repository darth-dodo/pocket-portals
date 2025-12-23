"""Turn execution logic for Pocket Portals."""

from dataclasses import dataclass
from typing import Any

from src.engine.router import RoutingDecision


@dataclass
class AgentResponse:
    """Response from a single agent.

    Attributes:
        agent: Name of the agent that generated the response
        content: The agent's response text
    """

    agent: str
    content: str


@dataclass
class TurnResult:
    """Complete result of turn execution.

    Attributes:
        responses: List of all agent responses in execution order
        narrative: Combined narrative text from all agents
        choices: Available player choices for next action
    """

    responses: list[AgentResponse]
    narrative: str
    choices: list[str]


class TurnExecutor:
    """Executes player turns by coordinating multiple agents.

    The executor takes a routing decision and executes the specified agents
    in order, aggregating their responses into a coherent narrative with
    player choices.

    Attributes:
        DEFAULT_CHOICES: Standard player choices offered each turn
    """

    DEFAULT_CHOICES = [
        "Investigate further",
        "Talk to someone nearby",
        "Move to a new location",
    ]

    def __init__(self, narrator: Any, keeper: Any, jester: Any) -> None:
        """Initialize executor with agent instances.

        Args:
            narrator: NarratorAgent instance for storytelling
            keeper: KeeperAgent instance for lore and mechanics
            jester: JesterAgent instance for chaos and humor
        """
        self.agents = {
            "narrator": narrator,
            "keeper": keeper,
            "jester": jester,
        }

    def execute(
        self,
        action: str,
        routing: RoutingDecision,
        context: str,
    ) -> TurnResult:
        """Execute a turn by coordinating agents.

        Executes each agent specified in the routing decision in order,
        collecting their responses and combining them into a narrative.

        Args:
            action: The player's action text
            routing: Routing decision specifying which agents to use
            context: Current game context/state

        Returns:
            TurnResult containing all responses, combined narrative, and choices
        """
        responses = []

        # Execute agents in the order specified by routing.agents
        for agent_name in routing.agents:
            agent = self.agents[agent_name]
            content = agent.respond(action=action, context=context)
            responses.append(AgentResponse(agent=agent_name, content=content))

        # Add jester if specified in routing
        if routing.include_jester:
            jester_content = self.agents["jester"].respond(
                action=action, context=context
            )
            responses.append(AgentResponse(agent="jester", content=jester_content))

        # Combine all responses into a single narrative
        narrative = self._combine_narrative(responses)

        return TurnResult(
            responses=responses,
            narrative=narrative,
            choices=self.DEFAULT_CHOICES,
        )

    def _combine_narrative(self, responses: list[AgentResponse]) -> str:
        """Combine multiple agent responses into a single narrative.

        Args:
            responses: List of agent responses to combine

        Returns:
            Combined narrative with responses separated by double newlines
        """
        return "\n\n".join(response.content for response in responses)
