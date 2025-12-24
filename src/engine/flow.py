"""Conversation flow orchestration using CrewAI Flows.

This module implements the multi-agent conversation orchestration using CrewAI's
Flow system. It coordinates routing decisions, agent execution, and response
aggregation through a declarative flow-based approach.
"""

from typing import Any

from crewai.flow.flow import Flow, listen, router, start

from src.engine.flow_state import ConversationFlowState
from src.engine.router import AgentRouter, RoutingDecision
from src.state.models import GamePhase


class ConversationFlow(Flow[ConversationFlowState]):
    """Orchestrates multi-agent conversations using CrewAI Flows.

    This flow implements the complete turn execution pipeline:
    1. Route action to appropriate agents based on context
    2. Execute each agent in sequence
    3. Aggregate responses into coherent narrative
    4. Generate player choices for next action

    The flow uses CrewAI's declarative routing system to handle both success
    and error paths gracefully.

    Attributes:
        agents: Dictionary mapping agent names to agent instances
        router: AgentRouter instance for routing decisions
        DEFAULT_CHOICES: Standard player choices offered each turn
    """

    DEFAULT_CHOICES = [
        "Investigate further",
        "Talk to someone nearby",
        "Move to a new location",
    ]

    def __init__(self, narrator: Any, keeper: Any, jester: Any) -> None:
        """Initialize the conversation flow with agent instances.

        Args:
            narrator: NarratorAgent instance for storytelling
            keeper: KeeperAgent instance for lore and mechanics
            jester: JesterAgent instance for chaos and humor
        """
        super().__init__()
        self.agents = {
            "narrator": narrator,
            "keeper": keeper,
            "jester": jester,
        }
        self.router = AgentRouter()

    @start()
    def route_action(self) -> ConversationFlowState:
        """Route the player action to appropriate agents.

        This is the entry point of the flow. If agents_to_invoke is already set
        (from TurnExecutor), it uses that routing. Otherwise, it uses the
        AgentRouter to determine which agents should handle the action.

        Returns:
            Updated state with routing decision applied
        """
        # If routing is already provided, skip re-routing
        if self.state.agents_to_invoke:
            return self.state

        # Convert string phase to GamePhase enum
        phase = GamePhase(self.state.phase)

        # Get routing decision from router
        routing: RoutingDecision = self.router.route(
            action=self.state.action,
            phase=phase,
            recent_agents=self.state.recent_agents,
        )

        # Update state with routing decision
        self.state.agents_to_invoke = routing.agents.copy()
        self.state.include_jester = routing.include_jester
        self.state.routing_reason = routing.reason

        return self.state

    @listen(route_action)
    def execute_agents(self) -> ConversationFlowState:
        """Execute each routed agent and collect responses.

        Executes agents in the order specified by the routing decision,
        calling each agent's respond method with the current action and context.
        If jester inclusion is flagged, executes jester last.

        Returns:
            Updated state with agent responses stored
        """
        try:
            # Execute main routed agents
            for agent_name in self.state.agents_to_invoke:
                agent = self.agents[agent_name]
                content = agent.respond(
                    action=self.state.action,
                    context=self.state.context,
                )
                self.state.responses[agent_name] = content

            # Execute jester if flagged
            if self.state.include_jester:
                jester_content = self.agents["jester"].respond(
                    action=self.state.action,
                    context=self.state.context,
                )
                self.state.responses["jester"] = jester_content

            return self.state

        except Exception as e:
            # Set error on state for routing to error handler
            self.state.error = f"Agent execution failed: {str(e)}"
            return self.state

    @router(execute_agents)
    def check_execution_status(self) -> str:
        """Route flow based on agent execution success or failure.

        Returns:
            "success" if execution completed without errors, "error" otherwise
        """
        if self.state.error is not None:
            return "error"
        return "success"

    @listen("success")
    def aggregate_responses(self) -> ConversationFlowState:
        """Aggregate all agent responses into a coherent narrative.

        Combines individual agent responses into a single narrative string,
        preserving the order of execution. Responses are joined with double
        newlines for readability.

        Returns:
            Updated state with combined narrative
        """
        # Build narrative from responses in execution order
        narrative_parts = []

        # Add main agent responses
        for agent_name in self.state.agents_to_invoke:
            if agent_name in self.state.responses:
                narrative_parts.append(self.state.responses[agent_name])

        # Add jester response if present
        if self.state.include_jester and "jester" in self.state.responses:
            narrative_parts.append(self.state.responses["jester"])

        # Combine into single narrative
        self.state.narrative = "\n\n".join(narrative_parts)

        return self.state

    @listen("error")
    def handle_error(self) -> ConversationFlowState:
        """Handle agent execution errors gracefully.

        Sets a fallback narrative and default choices when agent execution fails.
        This ensures the flow always produces usable output even on errors.

        Returns:
            Updated state with error narrative and default choices
        """
        self.state.narrative = (
            "The magical energies flicker and waver. "
            "Something went wrong in the weave of reality. "
            f"[Error: {self.state.error}]"
        )
        self.state.choices = self.DEFAULT_CHOICES

        return self.state

    @listen(aggregate_responses)
    def generate_choices(self) -> ConversationFlowState:
        """Generate available player choices for the next action.

        Currently sets default choices. This method can be extended to generate
        context-aware choices based on narrative content and game state.

        Returns:
            Updated state with player choices set
        """
        self.state.choices = self.DEFAULT_CHOICES

        return self.state
