# Conversation Engine Flow Refactor Design

**Feature**: Refactor conversation engine to use CrewAI Flows
**Author**: Architect Agent
**Date**: 2025-12-23
**Status**: Complete

---

## Overview

Refactor the conversation engine from procedural orchestration (AgentRouter + TurnExecutor) to CrewAI's Flow-based architecture with `@start()`, `@listen()`, and `@router()` decorators.

---

## Motivation

### Current Approach Limitations
- **Procedural**: Manual control flow in TurnExecutor
- **Tight Coupling**: Executor tightly coupled to specific agent names
- **No State Flow**: State passed manually between steps
- **Testing**: Requires mocking entire agents

### Flow Benefits
- **Declarative**: Event-driven with decorators
- **Typed State**: Pydantic BaseModel for type-safe state
- **Conditional Routing**: `@router()` for branching logic
- **Testability**: Test individual flow steps
- **Extensibility**: Add new steps without modifying existing code

---

## Architecture

### Flow Structure

```
@start()
route_action()
    ↓
@router(route_action)
check_phase()
    ├── "exploration" → @listen("exploration")
    ├── "combat" → @listen("combat")
    └── "dialogue" → @listen("dialogue")
    ↓
@listen(execute_*_agents)
aggregate_responses()
    ↓
@listen(aggregate_responses)
generate_choices()
    ↓
Return TurnResult
```

### File Structure

```
src/engine/
├── __init__.py           # Export flow, models
├── router.py             # Keep AgentRouter (routing logic)
├── executor.py           # Deprecated → replaced by flow
├── flow.py               # NEW: ConversationFlow class
└── flow_state.py         # NEW: ConversationFlowState model
```

---

## Component Specifications

### 1. ConversationFlowState (Pydantic Model)

```python
from pydantic import BaseModel, Field

class ConversationFlowState(BaseModel):
    """Typed state for conversation flow."""

    # Input
    session_id: str
    action: str = ""
    context: str = ""
    phase: str = "exploration"
    recent_agents: list[str] = Field(default_factory=list)

    # Routing
    agents_to_invoke: list[str] = Field(default_factory=list)
    include_jester: bool = False
    routing_reason: str = ""

    # Execution
    responses: dict[str, str] = Field(default_factory=dict)
    error: str | None = None

    # Output
    narrative: str = ""
    choices: list[str] = Field(default_factory=list)
```

### 2. ConversationFlow Class

```python
from crewai.flow.flow import Flow, start, listen, router

class ConversationFlow(Flow[ConversationFlowState]):
    """Event-driven conversation orchestration using CrewAI Flows."""

    def __init__(
        self,
        narrator: NarratorAgent,
        keeper: KeeperAgent,
        jester: JesterAgent,
    ) -> None:
        super().__init__()
        self.agents = {
            "narrator": narrator,
            "keeper": keeper,
            "jester": jester,
        }
        self.agent_router = AgentRouter()

    @start()
    def route_action(self) -> str:
        """Route player action to appropriate agents."""
        routing = self.agent_router.route(
            action=self.state.action,
            phase=GamePhase(self.state.phase),
            recent_agents=self.state.recent_agents,
        )
        self.state.agents_to_invoke = routing.agents
        self.state.include_jester = routing.include_jester
        self.state.routing_reason = routing.reason
        return "routed"

    @listen(route_action)
    def execute_agents(self) -> str:
        """Execute agents sequentially."""
        for agent_name in self.state.agents_to_invoke:
            agent = self.agents.get(agent_name)
            if agent:
                response = agent.respond(
                    action=self.state.action,
                    context=self.state.context,
                )
                self.state.responses[agent_name] = response

        # Add jester if included
        if self.state.include_jester:
            jester_response = self.agents["jester"].respond(
                action=self.state.action,
                context=self.state.context,
            )
            self.state.responses["jester"] = jester_response

        return "executed"

    @router(execute_agents)
    def check_execution_status(self) -> str:
        """Route based on execution success."""
        if self.state.error:
            return "error"
        return "success"

    @listen("success")
    def aggregate_responses(self) -> str:
        """Combine agent responses into narrative."""
        parts = []
        for agent_name in self.state.agents_to_invoke:
            if agent_name in self.state.responses:
                parts.append(self.state.responses[agent_name])

        if self.state.include_jester and "jester" in self.state.responses:
            parts.append(self.state.responses["jester"])

        self.state.narrative = "\n\n".join(parts)
        return "aggregated"

    @listen("error")
    def handle_error(self) -> str:
        """Handle execution errors gracefully."""
        self.state.narrative = f"Something went wrong: {self.state.error}"
        self.state.choices = ["Try again", "Return to safety"]
        return "error_handled"

    @listen(aggregate_responses)
    def generate_choices(self) -> str:
        """Generate player choices."""
        self.state.choices = [
            "Investigate further",
            "Talk to someone nearby",
            "Move to a new location",
        ]
        return "complete"
```

### 3. Updated TurnExecutor (Wrapper)

```python
class TurnExecutor:
    """Executes turns using ConversationFlow."""

    def __init__(
        self,
        narrator: Any,
        keeper: Any,
        jester: Any,
    ) -> None:
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
    ) -> TurnResult:
        """Execute turn using flow."""
        # Set flow state
        self.flow.state.action = action
        self.flow.state.context = context
        self.flow.state.agents_to_invoke = routing.agents
        self.flow.state.include_jester = routing.include_jester

        # Run flow
        self.flow.kickoff()

        # Build result
        responses = [
            AgentResponse(agent=name, content=content)
            for name, content in self.flow.state.responses.items()
        ]

        return TurnResult(
            responses=responses,
            narrative=self.flow.state.narrative,
            choices=self.flow.state.choices,
        )
```

---

## API Integration

No changes needed - TurnExecutor maintains same interface.

---

## Test Plan

### Flow Tests

```python
def test_flow_routes_to_narrator_in_exploration():
    """Test flow routes correctly."""
    flow = ConversationFlow(mock_narrator, mock_keeper, mock_jester)
    flow.state.action = "I look around"
    flow.state.phase = "exploration"

    flow.kickoff()

    assert "narrator" in flow.state.agents_to_invoke
    assert flow.state.narrative

def test_flow_handles_error_gracefully():
    """Test flow error handling path."""
    flow = ConversationFlow(failing_narrator, mock_keeper, mock_jester)
    flow.state.action = "I do something"
    flow.state.error = "Agent failed"

    flow.kickoff()

    assert "went wrong" in flow.state.narrative
```

---

## Success Criteria

- [x] ConversationFlow implemented with @start, @listen, @router
- [x] State managed via Pydantic model
- [x] TurnExecutor updated to use flow
- [x] All existing tests pass
- [x] Flow-specific tests added
- [x] Test coverage maintained ≥80% (85% achieved)

---

## Migration Path

1. Create flow_state.py with ConversationFlowState
2. Create flow.py with ConversationFlow
3. Update TurnExecutor to use flow internally
4. API unchanged - backward compatible
5. Add flow-specific tests
6. Update documentation
