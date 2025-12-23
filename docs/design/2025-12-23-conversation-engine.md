# Conversation Engine Design Document

**Feature**: Multi-agent orchestration for turn-based gameplay
**Author**: Architect Agent
**Date**: 2025-12-23
**Status**: Implemented

---

## Overview

The Conversation Engine orchestrates multiple agents per turn, enabling richer narrative experiences. Instead of single-agent responses, the engine routes actions to appropriate agents based on game phase and context.

---

## Goals

1. **Multi-Agent Turns**: Multiple agents can respond to a single action
2. **Phase-Aware Routing**: Route to agents based on game phase (exploration, combat, etc.)
3. **Jester Injection**: Probabilistically add Jester commentary
4. **Sequential Execution**: Execute agents in order with context passing
5. **YAGNI Compliant**: Build MVP first, defer streaming/combat

---

## Non-Goals (YAGNI - Defer to Future)

- SSE streaming (use simple JSON responses for now)
- Combat phase mechanics (dice, initiative)
- Character creation phase
- Token budget enforcement
- NPC spawning
- Epilogue generation

---

## Architecture

### Component Overview

```
/action request
    ↓
AgentRouter.route(action, phase)
    ↓
TurnExecutor.execute(agents, context)
    ↓
[NarratorAgent] → [KeeperAgent?] → [JesterAgent?]
    ↓
Aggregated TurnResult
```

### File Structure

```
src/
├── engine/
│   ├── __init__.py        # Export router, executor
│   ├── router.py          # AgentRouter class
│   └── executor.py        # TurnExecutor class
└── state/
    └── models.py          # Add GamePhase enum
```

---

## Component Specifications

### 1. GamePhase Enum

```python
from enum import Enum

class GamePhase(str, Enum):
    """Game phases for routing decisions."""
    EXPLORATION = "exploration"  # Default, free-form actions
    COMBAT = "combat"            # Tactical, dice-based (future)
    DIALOGUE = "dialogue"        # NPC conversations (future)
```

**MVP**: Only EXPLORATION phase implemented.

### 2. AgentRouter

```python
@dataclass
class RoutingDecision:
    """Result of agent routing."""
    agents: list[str]  # ["narrator", "keeper", "jester"]
    include_jester: bool
    reason: str  # For debugging

class AgentRouter:
    """Routes actions to appropriate agents based on phase and context."""

    JESTER_PROBABILITY = 0.15  # 15% chance in exploration
    JESTER_COOLDOWN = 3  # Minimum turns between Jester appearances

    def route(
        self,
        action: str,
        phase: GamePhase,
        recent_agents: list[str],  # Last N agents used
    ) -> RoutingDecision:
        """Determine which agents should respond to this action."""
```

**Routing Rules (MVP):**

| Phase | Primary | Secondary | Jester |
|-------|---------|-----------|--------|
| EXPLORATION | Narrator | Keeper (if mechanical) | 15% chance |
| COMBAT | Keeper | Narrator | 0% |
| DIALOGUE | Narrator | - | 10% chance |

**Mechanical Action Detection:**
- Keywords: attack, fight, roll, cast, defend, dodge, swing, shoot
- Pattern: Contains difficulty/DC reference

### 3. TurnExecutor

```python
@dataclass
class AgentResponse:
    """Response from a single agent."""
    agent: str
    content: str

@dataclass
class TurnResult:
    """Aggregated result from all agents in a turn."""
    responses: list[AgentResponse]
    narrative: str  # Combined for display
    choices: list[str]

class TurnExecutor:
    """Executes agents sequentially with context passing."""

    def __init__(
        self,
        narrator: NarratorAgent,
        keeper: KeeperAgent,
        jester: JesterAgent,
    ) -> None:
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
        """Execute agents in order and aggregate responses."""
```

**Execution Flow:**
1. Build context from conversation history
2. Execute Narrator first (always)
3. Execute Keeper if included (mechanical actions)
4. Execute Jester if included (probabilistic)
5. Aggregate responses into TurnResult
6. Generate choices based on narrative

### 4. Updated GameState

```python
class GameState(BaseModel):
    # Existing fields
    session_id: str
    conversation_history: list[dict[str, str]]
    current_choices: list[str]
    character_description: str
    health_current: int
    health_max: int

    # New fields for conversation engine
    phase: GamePhase = GamePhase.EXPLORATION
    recent_agents: list[str] = Field(default_factory=list)  # Last 5 agents
    turns_since_jester: int = 0
```

---

## API Changes

### Updated /action Endpoint

```python
@app.post("/action", response_model=NarrativeResponse)
async def process_action(request: ActionRequest) -> NarrativeResponse:
    state = get_session(request.session_id)
    action = resolve_action(request, state)

    # Route to appropriate agents
    routing = agent_router.route(
        action=action,
        phase=state.phase,
        recent_agents=state.recent_agents,
    )

    # Execute agents
    result = turn_executor.execute(
        action=action,
        routing=routing,
        context=build_context(state.conversation_history),
    )

    # Update state
    session_manager.add_exchange(state.session_id, action, result.narrative)
    session_manager.update_recent_agents(state.session_id, routing.agents)
    session_manager.set_choices(state.session_id, result.choices)

    return NarrativeResponse(
        narrative=result.narrative,
        session_id=state.session_id,
        choices=result.choices,
    )
```

### Response Format

No changes to NarrativeResponse - maintains backward compatibility.

---

## Implementation Plan

### Phase 1: Core Engine (This PR)

1. **GamePhase enum** - Add to `src/state/models.py`
2. **AgentRouter** - Create `src/engine/router.py`
3. **TurnExecutor** - Create `src/engine/executor.py`
4. **API Integration** - Update `/action` endpoint
5. **Tests** - TDD for router and executor

### Phase 2: Enhanced Phases (Future)

- Combat phase with dice mechanics
- Dialogue phase with NPC focus
- Phase transition detection

### Phase 3: Streaming (Future)

- SSE event streaming
- Chunked content delivery
- Frontend integration

---

## Test Plan

### Unit Tests

```
tests/
├── test_router.py          # AgentRouter tests
├── test_executor.py        # TurnExecutor tests
└── test_api.py             # Updated endpoint tests
```

### Test Cases

**AgentRouter Tests:**
1. Exploration phase routes to Narrator
2. Mechanical keywords trigger Keeper inclusion
3. Jester injection respects probability
4. Jester cooldown prevents spam
5. Combat phase routes to Keeper first

**TurnExecutor Tests:**
1. Single agent execution returns response
2. Multi-agent execution aggregates responses
3. Context is passed between agents
4. TurnResult contains all responses

**API Integration Tests:**
1. Action triggers multi-agent response
2. Narrative combines all agent outputs
3. Choices reflect current context

---

## Success Criteria

- [x] AgentRouter routes based on phase and action
- [x] TurnExecutor orchestrates multiple agents
- [x] Jester appears probabilistically (15% in exploration)
- [x] Jester cooldown prevents repetition
- [x] API returns combined narrative
- [x] Test coverage ≥70% (83% achieved)
- [x] All existing tests pass (71 tests)

---

## Related Documents

- `docs/reference/conversation-engine.md` - Full specification (future features)
- `docs/design/2025-12-22-multi-agent-crew.md` - Agent implementation
- `docs/design/2025-12-22-world-state-management.md` - State management
- `src/agents/` - Agent implementations
