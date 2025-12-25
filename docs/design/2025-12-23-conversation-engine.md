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

- Combat phase mechanics (dice, initiative)
- Token budget enforcement
- NPC spawning
- Epilogue generation

## Implemented Features (Beyond MVP)

- SSE streaming with `agent_chunk` events for character-by-character delivery
- Character creation phase with interactive interviewer agent
- Context building with character_sheet and character_description parameters
- All agents using claude-3-5-haiku-20241022 model
- Frontend streaming functions (startStreamingMessage, appendStreamingChar, endStreamingMessage)

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

    # Build context with character information
    context = build_context(
        state.conversation_history,
        character_sheet=state.character_sheet,
        character_description=state.character_description,
    )

    # Execute agents
    result = turn_executor.execute(
        action=action,
        routing=routing,
        context=context,
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

**Note**: Current implementation uses SSE streaming endpoint `/action/stream` for real-time character-by-character delivery via `agent_chunk` events.

### Response Format

No changes to NarrativeResponse - maintains backward compatibility.

---

## SSE Streaming Architecture

### Event Types

The streaming endpoint `/action/stream` emits the following Server-Sent Events:

| Event Type | Data Format | Purpose |
|-----------|-------------|---------|
| `agent_start` | `{"agent": "narrator"}` | Signal start of agent response |
| `agent_chunk` | `{"agent": "narrator", "chunk": "Y"}` | Single character of narrative |
| `agent_end` | `{"agent": "narrator"}` | Signal completion of agent response |
| `choices` | `{"choices": [...]}` | Available player actions |
| `error` | `{"error": "message"}` | Error information |
| `done` | `{}` | End of turn processing |

### Frontend Integration

**JavaScript Streaming Functions**:

```javascript
function startStreamingMessage(agentType) {
    // Create new message container for agent
    // Add agent-specific styling (narrator, keeper, jester)
    // Prepare for character-by-character rendering
}

function appendStreamingChar(char) {
    // Append single character to current message
    // Provides smooth typewriter effect
    // Updates UI in real-time
}

function endStreamingMessage() {
    // Finalize message rendering
    // Apply final formatting
    // Clean up streaming state
}
```

**Event Source Processing**:

```javascript
eventSource.addEventListener('agent_chunk', (event) => {
    const data = JSON.parse(event.data);
    appendStreamingChar(data.chunk);
});
```

### Character-by-Character Delivery

The `agent_chunk` event enables smooth narrative delivery:

1. Backend streams each character as it's generated from Claude API
2. Frontend receives individual characters via SSE
3. UI updates progressively using `appendStreamingChar()`
4. Creates natural reading experience with typewriter effect
5. Reduces perceived latency vs. waiting for complete response

### Model Configuration

**Claude 3.5 Haiku Integration**:

```python
# All agents configured with same model for consistency
Agent(
    role="Narrator",
    goal="...",
    backstory="...",
    llm=LLM(
        model="anthropic/claude-3-5-haiku-20241022",
        # Fast streaming response times
        # Cost-effective for high-frequency agent calls
    )
)
```

**Benefits**:
- Consistent response times across all agents
- Optimized cost per adventure session
- Reliable streaming performance
- Low latency for real-time gameplay

---

## Implementation Plan

### Phase 1: Core Engine ✅ Complete

1. ✅ **GamePhase enum** - Add to `src/state/models.py`
2. ✅ **AgentRouter** - Create `src/engine/router.py`
3. ✅ **TurnExecutor** - Create `src/engine/executor.py`
4. ✅ **API Integration** - Update `/action` endpoint
5. ✅ **Tests** - TDD for router and executor

### Phase 2: Streaming ✅ Complete

1. ✅ **SSE Streaming** - `/action/stream` endpoint with agent_chunk events
2. ✅ **Frontend Integration** - startStreamingMessage(), appendStreamingChar(), endStreamingMessage()
3. ✅ **Character-by-character delivery** - Smooth typewriter effect
4. ✅ **Model Configuration** - All agents using claude-3-5-haiku-20241022
5. ✅ **Context Enhancement** - build_context() with character_sheet and character_description

### Phase 3: Enhanced Phases (Future)

- Combat phase with dice mechanics
- Dialogue phase with NPC focus
- Phase transition detection

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

**Core Engine** (Phase 1):
- [x] AgentRouter routes based on phase and action
- [x] TurnExecutor orchestrates multiple agents
- [x] Jester appears probabilistically (15% in exploration)
- [x] Jester cooldown prevents repetition
- [x] API returns combined narrative
- [x] Test coverage ≥70% (83% achieved)
- [x] All existing tests pass (71 tests)

**Streaming Implementation** (Phase 2):
- [x] SSE streaming endpoint functional
- [x] agent_chunk events deliver characters progressively
- [x] Frontend streaming functions integrated
- [x] Character-by-character typewriter effect working
- [x] All agents using claude-3-5-haiku-20241022
- [x] build_context() accepts character_sheet and character_description
- [x] Smooth user experience with minimal perceived latency

---

## Related Documents

- `docs/reference/conversation-engine.md` - Full specification (future features)
- `docs/design/2025-12-22-multi-agent-crew.md` - Agent implementation
- `docs/design/2025-12-22-world-state-management.md` - State management
- `src/agents/` - Agent implementations
