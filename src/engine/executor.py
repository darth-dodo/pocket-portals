"""Turn execution logic for Pocket Portals.

This module provides the TurnExecutor class which serves as the primary interface
for executing player turns. It internally uses ConversationFlow for orchestration
while maintaining a simple external API.
"""

from dataclasses import dataclass
from typing import Any

from src.engine.flow import ConversationFlow
from src.engine.flow_state import ConversationFlowState
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
    """Executes player turns using ConversationFlow orchestration.

    The executor provides a simplified interface for turn execution while
    internally leveraging CrewAI's Flow-based orchestration for agent
    coordination and response aggregation.

    Attributes:
        flow: ConversationFlow instance for orchestration
    """

    def __init__(self, narrator: Any, keeper: Any, jester: Any) -> None:
        """Initialize executor with agent instances.

        Args:
            narrator: NarratorAgent instance for storytelling
            keeper: KeeperAgent instance for lore and mechanics
            jester: JesterAgent instance for chaos and humor
        """
        self.flow = ConversationFlow(
            narrator=narrator,
            keeper=keeper,
            jester=jester,
        )

    def execute(
        self,
        action: str,
        routing: RoutingDecision,
        context: str,
        session_id: str = "default",
    ) -> TurnResult:
        """Execute a turn using ConversationFlow orchestration.

        Sets up the flow state with the provided parameters and kicks off
        the flow execution. The flow handles routing, agent execution,
        response aggregation, and choice generation.

        Args:
            action: The player's action text
            routing: Routing decision specifying which agents to use
            context: Current game context/state
            session_id: Unique identifier for the session

        Returns:
            TurnResult containing all responses, combined narrative, and choices
        """
        # Initialize flow state with input parameters
        initial_state = ConversationFlowState(
            session_id=session_id,
            action=action,
            context=context,
            phase="exploration",  # Default phase, will be updated by flow
            agents_to_invoke=routing.agents.copy(),
            include_jester=routing.include_jester,
            routing_reason=routing.reason,
        )

        # Execute the flow
        final_state = self.flow.kickoff(inputs=initial_state.model_dump())

        # Build AgentResponse list from flow responses
        responses = self._build_responses(final_state)

        return TurnResult(
            responses=responses,
            narrative=final_state.narrative,
            choices=final_state.choices,
        )

    def _build_responses(self, state: ConversationFlowState) -> list[AgentResponse]:
        """Build AgentResponse list from flow state.

        Preserves the order of agent execution by iterating through
        agents_to_invoke first, then adding jester if included.

        Args:
            state: Final flow state containing agent responses

        Returns:
            List of AgentResponse objects in execution order
        """
        responses = []

        # Add responses in agent execution order
        for agent_name in state.agents_to_invoke:
            if agent_name in state.responses:
                responses.append(
                    AgentResponse(agent=agent_name, content=state.responses[agent_name])
                )

        # Add jester response if included
        if state.include_jester and "jester" in state.responses:
            responses.append(
                AgentResponse(agent="jester", content=state.responses["jester"])
            )

        return responses
