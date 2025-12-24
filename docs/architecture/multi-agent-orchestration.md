# Multi-Agent Orchestration Architecture for Pocket Portals

**Status**: Design Recommendation
**Author**: System Architect
**Date**: 2025-12-23
**Context**: MVP implementation guidance for agent routing and response aggregation

---

## Executive Summary

This document provides architectural patterns for coordinating four specialized agents (Narrator, Keeper, Innkeeper, Jester) in Pocket Portals. It prioritizes **simplicity over sophistication** for MVP, with clear extension points for future orchestration complexity.

**Key Recommendation**: Start with **rule-based sequential routing** with simple response concatenation, deferring CrewAI's full `@crew` orchestration until proven necessary.

---

## 1. Multi-Agent Orchestration Patterns

### 1.1 Pattern Overview

| Pattern | Complexity | Use Case | Pocket Portals Fit |
|---------|-----------|----------|-------------------|
| **Sequential Chain** | Low | Simple workflows with clear dependencies | ✅ MVP (Start here) |
| **Parallel Execution** | Medium | Independent agents work simultaneously | 🔄 Future (Phase 2) |
| **Hierarchical Delegation** | High | Manager agent delegates to specialists | ❌ Over-engineered for MVP |
| **Event-Driven Pub/Sub** | High | Loose coupling, async communication | ❌ Unnecessary complexity |

### 1.2 Recommended Approach: Sequential Chain with State-Aware Routing

```
Player Input → Router → Agent Selection → Sequential Execution → Response Aggregation → UI
                 ↓              ↓                    ↓                     ↓
            Phase State    Context Rules      Execute in Order      Concatenate Outputs
```

**Why This Works for Pocket Portals**:
- Clear turn structure (D&D is inherently turn-based)
- Predictable agent dependencies (Keeper validates before Narrator describes)
- Simple to test and debug
- Minimal latency overhead (agents run in order, not waiting for slowest)

---

## 2. Agent Routing Architecture

### 2.1 Simple Routing Rules (MVP)

**Rule-Based Decision Matrix**:

```python
class AgentRouter:
    """Simple rule-based routing for MVP."""

    def select_agents(
        self,
        player_input: str,
        session_context: SessionContext
    ) -> list[str]:
        """
        Returns ordered list of agent names to invoke.

        Rules:
        1. Narrator ALWAYS responds (except session start)
        2. Keeper ONLY when mechanical resolution needed
        3. Jester probabilistically (10-20% based on phase)
        4. Innkeeper ONLY at session bookends
        """
        agents = []

        # Session start: Innkeeper introduces
        if session_context.turn_count == 0:
            agents.append("innkeeper")
            return agents

        # Check if mechanics needed (dice, damage, state validation)
        if self._needs_mechanics(player_input, session_context):
            agents.append("keeper")

        # Narrator always narrates (primary storyteller)
        agents.append("narrator")

        # Jester randomly interjects
        if self._should_jester_speak(session_context):
            agents.append("jester")

        # Session end: Innkeeper concludes
        if session_context.quest_complete:
            agents.append("innkeeper")

        return agents

    def _needs_mechanics(self, input: str, ctx: SessionContext) -> bool:
        """Check if Keeper should validate mechanics."""
        # Simple keyword detection for MVP
        action_keywords = ["attack", "cast", "persuade", "sneak", "climb"]
        combat_active = ctx.phase == "combat"

        return (
            combat_active or
            any(keyword in input.lower() for keyword in action_keywords)
        )

    def _should_jester_speak(self, ctx: SessionContext) -> bool:
        """Probabilistic Jester intervention."""
        import random

        # Never during combat or epilogue
        if ctx.phase in ["combat", "epilogue"]:
            return False

        # Don't speak consecutively
        if ctx.last_speaker == "jester":
            return False

        # 10-20% chance based on phase
        probabilities = {
            "exploration": 0.15,
            "dialogue": 0.10,
            "quest_intro": 0.20,
        }
        chance = probabilities.get(ctx.phase, 0.10)

        return random.random() < chance
```

**Routing Decision Tree**:

```
┌─────────────────────────────────────────────────────┐
│           Player Input + Session Context            │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Turn Count == 0?    │──Yes──→ [Innkeeper]
         └──────────┬───────────┘
                    │ No
                    ▼
         ┌──────────────────────┐
         │ Action Keywords OR   │──Yes──→ [Keeper] → [Narrator]
         │   Combat Phase?      │
         └──────────┬───────────┘
                    │ No
                    ▼
                [Narrator]
                    │
                    ▼
         ┌──────────────────────┐
         │ Random(0-1) < Prob   │──Yes──→ [Jester]
         │  AND not combat?     │
         └──────────┬───────────┘
                    │ No
                    ▼
         ┌──────────────────────┐
         │  Quest Complete?     │──Yes──→ [Innkeeper]
         └──────────────────────┘
```

### 2.2 Context-Sensitive Routing

**Session Context Structure**:

```python
@dataclass
class SessionContext:
    session_id: str
    turn_count: int = 0
    phase: str = "exploration"  # exploration, combat, dialogue, epilogue
    quest_complete: bool = False
    last_speaker: str = ""

    # For Jester logic
    calm_streak: int = 0  # Turns without complications

    # For Keeper logic
    last_roll_turn: int = -1

    # Conversation history (for context passing)
    history: list[dict] = field(default_factory=list)
```

**Phase-Specific Routing**:

| Phase | Primary Agent | Optional Agents | Logic |
|-------|--------------|----------------|-------|
| `session_start` | Innkeeper | None | Welcome + quest hook |
| `exploration` | Narrator | Jester (15%), Keeper (if action) | Standard gameplay |
| `combat` | Keeper → Narrator | None | Mechanics first, then narration |
| `dialogue` | Narrator | Jester (10%) | NPC interactions |
| `epilogue` | Narrator → Innkeeper | None | Story conclusion |

---

## 3. Sequential vs Parallel Execution

### 3.1 MVP: Sequential Execution

**Why Sequential for MVP**:
- **Dependency Chain**: Keeper validates → Narrator narrates result
- **Context Passing**: Later agents can reference earlier responses
- **Simpler Error Handling**: One agent fails, stop chain gracefully
- **Predictable Latency**: Sum of agent times, not slowest agent

**Implementation Pattern**:

```python
async def execute_turn(agents: list[str], context: SessionContext) -> list[dict]:
    """Execute agents sequentially, passing updated context."""
    responses = []

    for agent_name in agents:
        agent = get_agent(agent_name)

        # Pass accumulated context including previous responses
        turn_context = {
            "player_input": context.player_input,
            "session": context.to_dict(),
            "previous_responses": responses,  # Let later agents see earlier outputs
        }

        # Execute agent
        response = await agent.execute(turn_context)

        # Accumulate responses
        responses.append({
            "agent": agent_name,
            "content": response,
        })

        # Update context for next agent
        context.history.append(response)

    return responses
```

**Expected Latency** (Sequential):
- Keeper: ~500ms
- Narrator: ~1.5s
- Jester: ~400ms
- **Total**: ~2.4s (acceptable for turn-based game)

### 3.2 Future: Parallel Execution (Phase 2)

**When Parallel Makes Sense**:
- Character creation (stat generation + backstory analysis)
- Combat (multiple enemy turns)
- NOT for narrative chain (dependencies break parallelism)

**Deferred Pattern**:

```python
# YAGNI for MVP - implement only when needed
async def execute_parallel(agents: list[str], context: SessionContext):
    """Execute independent agents in parallel."""
    tasks = [get_agent(name).execute(context) for name in agents]
    responses = await asyncio.gather(*tasks)
    return responses
```

---

## 4. Response Aggregation Strategy

### 4.1 Simple Concatenation (MVP)

**Pattern**: Sequential narrative flow

```python
def aggregate_responses(responses: list[dict]) -> str:
    """Concatenate agent responses in execution order."""
    parts = []

    for resp in responses:
        agent_name = resp["agent"]
        content = resp["content"]

        # Add agent attribution
        formatted = f"[{agent_name.upper()}]\n{content}\n"
        parts.append(formatted)

    return "\n".join(parts)
```

**Example Output**:

```
[KEEPER]
14. That lands. How hard?

[NARRATOR]
Your blade cuts through the goblin's leather armor.
It staggers back, snarling. Two more emerge from the shadows.

What do you do?

[JESTER]
Just two more? Check the bushes. There's always more goblins.
```

**UI Rendering**:
- Each agent gets distinct visual styling (color, icon, border)
- Responses render sequentially as they complete
- Natural reading flow top-to-bottom

### 4.2 Structured Aggregation (Future)

**When Needed**: Complex combat with battlefield state

```python
# YAGNI - Only implement if narrative clarity suffers
@dataclass
class AggregatedResponse:
    narrative: str         # Narrator's description
    mechanics: str         # Keeper's roll results
    complications: str     # Jester's observations
    choices: list[str]     # Extracted from Narrator

    def render_for_ui(self) -> dict:
        """Structured format for rich UI."""
        return {
            "story": self.narrative,
            "dice_results": self.mechanics,
            "meta_commentary": self.complications,
            "available_actions": self.choices,
        }
```

---

## 5. Agent Invocation Patterns

### 5.1 When to Invoke Each Agent

**Narrator** - ALWAYS (except session start)
- **Trigger**: Any player input
- **Output**: Scene description + choices
- **Context Needs**: World state, previous actions, current location

**Keeper** - CONDITIONAL (mechanical resolution)
- **Trigger**: Combat, skill checks, dice rolls
- **Detection**: Keywords (attack, cast, persuade) OR combat phase
- **Output**: Roll results, HP updates, mechanical state
- **Context Needs**: Character stats, current combat state

**Jester** - PROBABILISTIC (10-20%)
- **Trigger**: Random chance based on phase
- **Suppression**: Combat, epilogue, consecutive turns
- **Output**: Meta-commentary, complications
- **Context Needs**: Recent narrative flow, player patterns

**Innkeeper** - BOOKENDS (session start/end)
- **Trigger**: Turn 0 OR quest complete
- **Output**: Quest introduction OR epilogue reflection
- **Context Needs**: Character backstory, quest status

### 5.2 Invocation Decision Logic

```python
class AgentInvoker:
    """Manages when and how agents are called."""

    def invoke(self, agent_name: str, context: SessionContext) -> str:
        """Invoke agent with appropriate context."""
        agent_methods = {
            "narrator": self._invoke_narrator,
            "keeper": self._invoke_keeper,
            "jester": self._invoke_jester,
            "innkeeper": self._invoke_innkeeper,
        }

        return agent_methods[agent_name](context)

    def _invoke_narrator(self, ctx: SessionContext) -> str:
        """Always narrates scene + presents choices."""
        return narrator_agent.generate_narrative(
            player_action=ctx.player_input,
            location=ctx.location,
            world_state=ctx.world_state,
        )

    def _invoke_keeper(self, ctx: SessionContext) -> str:
        """Only when mechanics needed."""
        return keeper_agent.resolve_action(
            action=ctx.player_input,
            difficulty=self._calculate_dc(ctx),
            character_stats=ctx.character,
        )

    def _invoke_jester(self, ctx: SessionContext) -> str:
        """Probabilistic intervention."""
        return jester_agent.add_complication(
            situation=self._summarize_recent_narrative(ctx),
        )

    def _invoke_innkeeper(self, ctx: SessionContext) -> str:
        """Session bookends."""
        if ctx.turn_count == 0:
            return innkeeper_agent.introduce_quest(
                character=ctx.character_description,
            )
        else:
            return innkeeper_agent.conclude_session(
                quest_outcome=ctx.quest_status,
            )
```

---

## 6. YAGNI Considerations

### 6.1 What NOT to Build for MVP

**Deferred Complexity** (Build only when pain proven):

| Feature | Why Deferred | When to Revisit |
|---------|-------------|----------------|
| **CrewAI `@crew` decorator** | Simple routing sufficient | If agent dependencies become complex |
| **Parallel agent execution** | Sequential works for turn-based | If latency >5s becomes issue |
| **Dynamic agent injection** | Fixed 4 agents is manageable | If agent types grow beyond 6 |
| **ML-based routing** | Rules cover 90% of cases | If manual rules become unmaintainable |
| **Response quality voting** | Single narrator maintains consistency | If narrative quality varies significantly |
| **Agent memory isolation** | Shared context is simpler | If agents conflict on world state |

### 6.2 Explicit Extension Points

**Design for Future**:

```python
# Router interface allows swapping implementations
class IAgentRouter(Protocol):
    def select_agents(self, input: str, ctx: SessionContext) -> list[str]:
        ...

# Can swap RuleBasedRouter → MLRouter → CrewOrchestrator later
router: IAgentRouter = RuleBasedRouter()  # MVP
# router = CrewOrchestrator()              # Future
```

```python
# Aggregator interface allows different strategies
class IResponseAggregator(Protocol):
    def aggregate(self, responses: list[dict]) -> str:
        ...

# Can swap SimpleConcat → StructuredAggregator → TemplateRenderer
aggregator: IResponseAggregator = SimpleConcatenator()  # MVP
# aggregator = StructuredAggregator()                    # Future
```

---

## 7. Testing Strategy

### 7.1 Router Tests

```python
def test_router_selects_narrator_always():
    """Narrator should respond to any non-session-start input."""
    router = AgentRouter()
    ctx = SessionContext(turn_count=5, phase="exploration")

    agents = router.select_agents("I look around", ctx)

    assert "narrator" in agents

def test_router_invokes_keeper_on_combat():
    """Keeper validates mechanics during combat."""
    router = AgentRouter()
    ctx = SessionContext(phase="combat")

    agents = router.select_agents("I attack", ctx)

    assert agents[0] == "keeper"  # Keeper first
    assert "narrator" in agents    # Then narrator

def test_jester_never_during_combat():
    """Jester stays silent during tactical resolution."""
    router = AgentRouter()
    ctx = SessionContext(phase="combat")

    for _ in range(100):  # Even with RNG
        agents = router.select_agents("I swing my sword", ctx)
        assert "jester" not in agents
```

### 7.2 Aggregation Tests

```python
def test_aggregation_preserves_order():
    """Responses appear in execution order."""
    responses = [
        {"agent": "keeper", "content": "14. That hits."},
        {"agent": "narrator", "content": "Your blade strikes true."},
    ]

    result = aggregate_responses(responses)

    assert result.index("keeper") < result.index("narrator")

def test_aggregation_handles_empty():
    """Gracefully handle no responses."""
    result = aggregate_responses([])
    assert result == ""
```

### 7.3 Integration Tests

```python
@pytest.mark.asyncio
async def test_full_turn_execution():
    """Complete turn with multiple agents."""
    ctx = SessionContext(
        player_input="I attack the goblin",
        phase="combat",
    )

    router = AgentRouter()
    agents = router.select_agents(ctx.player_input, ctx)

    responses = await execute_turn(agents, ctx)

    assert len(responses) >= 2  # At least Keeper + Narrator
    assert responses[0]["agent"] == "keeper"
    assert responses[1]["agent"] == "narrator"
```

---

## 8. Implementation Roadmap

### Phase 1: MVP (Current)
- ✅ Individual agent classes working
- ✅ Simple API endpoints per agent
- ⬜ **Rule-based router** (this document)
- ⬜ **Sequential executor**
- ⬜ **Simple concatenation aggregator**
- ⬜ Integration tests

**Estimated Effort**: 2-3 days
**Risk**: Low (all dependencies exist)

### Phase 2: Orchestration Polish (Future)
- ⬜ Streaming SSE responses
- ⬜ Context persistence (session storage)
- ⬜ Phase transition logic
- ⬜ Jester personality tuning

**Estimated Effort**: 3-5 days
**Trigger**: After MVP user testing

### Phase 3: Advanced Features (If Needed)
- ⬜ Parallel agent execution
- ⬜ CrewAI `@crew` orchestration
- ⬜ ML-based routing
- ⬜ Response quality checks

**Estimated Effort**: 1-2 weeks
**Trigger**: Proven pain points from Phase 2

---

## 9. Comparison: Simple vs CrewAI Orchestration

### 9.1 Simple Approach (Recommended for MVP)

**Code Example**:

```python
# Clean, testable, explicit
async def handle_turn(player_input: str, ctx: SessionContext):
    router = AgentRouter()
    agents = router.select_agents(player_input, ctx)

    responses = []
    for agent_name in agents:
        resp = await invoke_agent(agent_name, ctx)
        responses.append(resp)

    return aggregate_responses(responses)
```

**Pros**:
- Explicit control flow (easy to debug)
- Simple to test (mock individual agents)
- Predictable latency (sum of agents)
- No framework magic

**Cons**:
- Manual context passing
- No built-in error recovery
- Reinventing some orchestration wheels

### 9.2 CrewAI `@crew` Approach (Future)

**Code Example**:

```python
# Framework-heavy, but handles complexity
@CrewBase
class TavernCrew:
    @crew
    def run_turn(self) -> Crew:
        return Crew(
            agents=[self.narrator(), self.keeper(), self.jester()],
            tasks=self.turn_tasks(),
            process=Process.sequential,
        )
```

**Pros**:
- Built-in task delegation
- Automatic context management
- Error recovery mechanisms
- Parallel execution support

**Cons**:
- More abstraction (harder to debug)
- Framework lock-in
- Overhead for simple use cases
- Learning curve

**Recommendation**: Start simple, migrate to `@crew` only if routing becomes complex enough to justify framework overhead.

---

## 10. Key Architectural Decisions

### ADR: Sequential Execution for MVP

**Status**: Accepted
**Context**: Need to coordinate 4 agents for narrative generation
**Decision**: Use sequential execution with rule-based routing

**Rationale**:
- Turn-based gameplay fits sequential model
- Agent dependencies (Keeper → Narrator) require ordering
- Latency <3s is acceptable for D&D turns
- Simpler to test and debug than parallel

**Consequences**:
- ✅ Predictable behavior
- ✅ Easy context passing
- ⚠️ Not optimal for parallel-friendly operations (character creation)
- ⚠️ May need refactor if latency becomes issue

### ADR: Rule-Based Routing Over ML

**Status**: Accepted
**Context**: Need to decide which agents respond to player input
**Decision**: Use explicit if/else rules with context state

**Rationale**:
- Agent selection rules are simple and deterministic
- Four agents with clear responsibilities
- YAGNI - no evidence rules will become unmanageable
- Easier to test than ML-based routing

**Consequences**:
- ✅ Transparent decision logic
- ✅ No training data needed
- ⚠️ May need tuning as game complexity grows
- ⚠️ Jester probability requires manual balancing

---

## 11. Success Criteria

**MVP is successful when**:
- ✅ Router selects correct agents 95% of time (tested)
- ✅ Keeper only invoked when mechanics needed (not every turn)
- ✅ Jester appears 10-20% of non-combat turns
- ✅ Responses aggregate into coherent narrative
- ✅ Turn latency <3s for 90th percentile
- ✅ Zero agent conflicts (e.g., Narrator contradicting Keeper)

**When to revisit architecture**:
- ❌ Routing rules exceed 100 lines of if/else
- ❌ Turn latency >5s becomes user complaint
- ❌ Agent conflicts require manual intervention >10% of time
- ❌ Adding new agent requires touching >3 files

---

## 12. Related Documents

- [Multi-Agent Crew Design](../design/2025-12-22-multi-agent-crew.md) - Agent specifications
- [Conversation Engine](../reference/conversation-engine.md) - Full orchestration design (future state)
- [Architecture](../architecture.md) - Overall system architecture
- [Product Requirements](../product.md) - Agent roles and behaviors

---

**Next Steps**:
1. Implement `AgentRouter` with rule-based logic
2. Build `TurnExecutor` for sequential execution
3. Create `ResponseAggregator` for simple concatenation
4. Add integration tests for full turn flow
5. Measure latency and tune Jester probability
