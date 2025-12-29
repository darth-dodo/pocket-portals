# ADR-003: Adventure Pacing System with 50-Turn Budget

**Date**: 2025-12-29
**Status**: Proposed
**Context**: Adventure structure and narrative closure
**Decider(s)**: Architect Persona

---

## Summary

Implement a 50-turn adventure pacing system that provides structured narrative arcs with satisfying conclusions. The system uses turn-based phase transitions combined with quest-driven triggers to guide agents toward natural story closure while maintaining player agency.

---

## Problem Statement

### The Challenge

Adventures in Pocket Portals currently run indefinitely without narrative structure. Players can continue playing forever, but there's no:
- Sense of progression through a story arc
- Build-up toward a climax
- Satisfying conclusion or epilogue
- Pacing guidance for agents

This leads to meandering narratives that eventually lose engagement rather than building to memorable conclusions.

### Why This Matters

- **Player Experience**: Players expect stories to have beginnings, middles, and ends
- **Narrative Quality**: Agents can't pace their output without knowing where they are in the story
- **Replayability**: Defined adventures encourage replaying with different characters/choices
- **Session Management**: Bounded adventures fit better into play sessions

### Success Criteria

- [ ] Adventures complete within 50 turns maximum
- [ ] Clear narrative arc with rising action, climax, and resolution
- [ ] Agents receive pacing context to adjust their output
- [ ] Players receive satisfying, personalized epilogues
- [ ] Quest completion can trigger early (but not premature) endings
- [ ] UI displays turn progress to players

---

## Context

### Current State

**Existing Architecture**:
- `GameState` tracks `creation_turn` (0-5) for character creation only
- `GamePhase` enum: CHARACTER_CREATION, EXPLORATION, COMBAT, DIALOGUE
- Quest system generates initial quest after character creation
- Conversation history limited to 20 exchanges
- No turn counter for general adventure progress

**Pain Points**:
- Adventures have no natural ending point
- Agents don't know if they should be building tension or resolving conflicts
- Players may lose interest without clear progression
- No mechanism for epilogue generation

**Technical Constraints**:
- Must integrate with existing CrewAI flow architecture
- Must not break existing session management
- Context window limits require efficient pacing information
- LLM calls should remain minimal (cost considerations)

### Requirements

**Functional Requirements**:
- Track adventure turn count (0-50)
- Calculate adventure phase based on turn and quest progress
- Pass pacing context to agents
- Trigger epilogue at adventure conclusion
- Support quest-driven early endings (after turn 25)

**Non-Functional Requirements**:
- **Performance**: Pacing calculations < 10ms per turn
- **Scalability**: No additional LLM calls for pacing
- **Maintainability**: Clear phase boundaries and transition logic
- **Reliability**: Hard cap ensures adventures always end

---

## Options Considered

### Option A: Pure Turn-Based Pacing

**Description**:
Fixed 50-turn cap with hard-coded phase thresholds. Adventure always runs exactly 50 turns (or until player quits).

**Implementation**:
```python
def get_phase(turn: int) -> AdventurePhase:
    if turn <= 5: return SETUP
    elif turn <= 20: return RISING_ACTION
    elif turn <= 30: return MID_POINT
    elif turn <= 42: return CLIMAX
    else: return DENOUEMENT
```

**Pros**:
- Simplest implementation
- Predictable session length
- Easy to test

**Cons**:
- Ignores quest progress (quest done at turn 15 → 35 turns of filler)
- Feels artificial/rigid
- No player agency over pacing

**Risks**:
- Players feel "railroaded" by arbitrary turn limits

**Estimated Effort**: 4-6 hours

---

### Option B: Quest-Driven with Turn Budget (Recommended)

**Description**:
Hybrid approach where quest completion drives pacing, but turns provide minimum and maximum boundaries. Quest completion after turn 25 triggers denouement; hard cap at turn 50 ensures closure.

**Implementation**:
```python
def calculate_phase(state: GameState) -> AdventurePhase:
    turn = state.adventure_turn
    turn_phase = get_turn_based_phase(turn)

    # Quest completion accelerates to denouement (but not too early)
    if state.active_quest and state.active_quest.is_complete:
        if turn >= 25:  # Minimum adventure length
            return DENOUEMENT

    # Urgency increases near cap
    if turn >= 40:
        return CLIMAX if not state.climax_reached else DENOUEMENT

    return turn_phase
```

**Pros**:
- Feels organic - quest completion matters
- Minimum length ensures satisfying story
- Maximum ensures closure
- Player choices affect pacing

**Cons**:
- More complex logic
- Edge cases to handle
- Quest progress detection needed

**Risks**:
- Quest detection logic may miss completions
- Mitigation: Use explicit completion markers + keyword detection

**Estimated Effort**: 8-12 hours

---

### Option C: Elastic Adventure Length

**Description**:
Variable adventure length (30-70 turns) based on quest complexity and player engagement signals.

**Implementation**:
- 1 objective quest: 30-turn cap
- 2 objective quest: 50-turn cap
- 3+ objective quest: 70-turn cap
- Engagement signals (combat, dialogue) extend duration

**Pros**:
- Matches content to length
- Highly dynamic
- Respects quest complexity

**Cons**:
- Unpredictable session length
- Complex implementation
- Harder to test

**Risks**:
- Engagement detection may be unreliable
- Players may not understand variable length

**Estimated Effort**: 16-20 hours

---

## Comparison Matrix

| Criteria                  | Weight | Option A | Option B | Option C |
| ------------------------- | ------ | -------- | -------- | -------- |
| **Maintainability**       | High   | 5        | 4        | 2        |
| **Scalability**           | High   | 4        | 4        | 3        |
| **Performance**           | Medium | 5        | 5        | 4        |
| **Player Experience**     | High   | 2        | 5        | 4        |
| **Complexity**            | Medium | 5        | 3        | 2        |
| **Implementation Effort** | Medium | 5        | 3        | 2        |
| **Testing Difficulty**    | Low    | 5        | 4        | 2        |
| **Flexibility**           | Medium | 2        | 4        | 5        |
| **Total Score**           | -      | 33       | 32       | 24       |

**Scoring**: 1 = Poor, 5 = Excellent
**Note**: Option B scores highest on Player Experience (critical) despite slightly lower total

---

## Decision

### Chosen Option

**Selected**: Option B: Quest-Driven with Turn Budget

**Rationale**:
The hybrid approach provides the best balance between narrative satisfaction and implementation complexity. While Option A is simpler, it fails the core requirement of meaningful quest integration. Option C adds complexity without proportional benefit.

**Key Factors**:
- Quest completion should feel meaningful, not arbitrary
- 50-turn cap provides clear boundary for players and developers
- Minimum 25-turn threshold prevents rushed experiences
- Turn-based fallbacks ensure graceful degradation

**Trade-offs Accepted**:
- More complex than pure turn-based approach
- Requires careful edge case handling
- Quest completion detection adds some overhead

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- Adventures have clear narrative arcs
- Agents can pace their output appropriately
- Players know approximately how long an adventure takes

**Long-term Benefits**:
- Foundation for quest chaining (multi-quest campaigns)
- Better player retention through satisfying conclusions
- Data for tuning optimal adventure lengths

### Negative Outcomes

**Immediate Costs**:
- Additional complexity in action processing
- New tests required for phase transitions

**Technical Debt Created**:
- Moment tracking for epilogue (can be enhanced later)

**Trade-offs**:
- Some quest completions before turn 25 won't trigger ending
- Players who want longer sessions must start new adventures

### Risks and Mitigation

**Risk 1**: Quest completion detection misses edge cases
- **Probability**: Medium
- **Impact**: Adventure continues past natural ending
- **Mitigation**: Explicit completion markers + turn 50 hard cap

**Risk 2**: Pacing hints confuse agents
- **Probability**: Low
- **Impact**: Inconsistent narrative quality
- **Mitigation**: Test pacing prompts extensively, iterate on wording

---

## Implementation Plan

### Phases

**Phase 1**: Core Turn Tracking (Subagent: Developer-Backend)
- **Duration**: 2-3 hours
- **Tasks**:
  - [ ] Add `AdventurePhase` enum to models.py
  - [ ] Add `adventure_turn`, `adventure_phase`, `max_turns` to GameState
  - [ ] Add `increment_adventure_turn()` to SessionManager
  - [ ] Add phase calculation function
- **Deliverable**: Turn tracking infrastructure

**Phase 2**: Pacing Integration (Subagent: Developer-Backend)
- **Duration**: 2-3 hours
- **Tasks**:
  - [ ] Create `PacingContext` model
  - [ ] Update `build_context()` to include pacing hints
  - [ ] Hook turn increment into `/action` endpoint
  - [ ] Add pacing to agent task descriptions
- **Deliverable**: Agents receive pacing context

**Phase 3**: Closure Triggers (Subagent: Developer-Backend)
- **Duration**: 2-3 hours
- **Tasks**:
  - [ ] Implement hard cap at turn 50
  - [ ] Add quest completion acceleration
  - [ ] Create `_trigger_epilogue()` handler
  - [ ] Add adventure completion state
- **Deliverable**: Adventures conclude properly

**Phase 4**: Epilogue Agent (Subagent: Developer-Agent)
- **Duration**: 3-4 hours
- **Tasks**:
  - [ ] Create EpilogueAgent class
  - [ ] Add epilogue configuration to agents.yaml
  - [ ] Add generate_epilogue task to tasks.yaml
  - [ ] Implement moment tracking
- **Deliverable**: Personalized epilogue generation

**Phase 5**: Testing & Validation (Subagent: QA)
- **Duration**: 2-3 hours
- **Tasks**:
  - [ ] Unit tests for phase calculations
  - [ ] Integration tests for turn progression
  - [ ] E2E test for full 50-turn adventure
  - [ ] Quality gate validation
- **Deliverable**: Validated implementation

### Dependencies

**Prerequisites**:
- Existing GameState model
- SessionManager infrastructure
- Agent system working

**Parallel Work**:
- Phases 1-3 must be sequential
- Phase 4 can parallel with Phase 3
- Phase 5 requires all phases complete

**Blocked By**: None

### Rollback Plan

**Trigger Conditions**:
- Adventure pacing causes > 20% increase in LLM costs
- Player feedback strongly negative
- Performance impact > 100ms per turn

**Rollback Steps**:
1. Feature flag to disable pacing
2. Revert to unbounded adventures
3. Keep turn tracking for analytics

---

## Validation

### Pre-Implementation Checklist

- [x] Decision addresses the original problem
- [x] Success criteria are achievable
- [x] Risks are identified and mitigated
- [x] Implementation plan is realistic
- [x] Dependencies are understood
- [x] Rollback plan exists

### Architect Quality Standards

- [x] **Scalability**: Design accommodates quest chaining extension
- [x] **Maintainability**: Clear phase boundaries, documented logic
- [x] **Best Practices**: Follows CrewAI patterns
- [x] **Simplicity**: Minimum complexity for requirements
- [x] **Trade-offs**: Trade-offs explicit and acceptable

### Post-Implementation Validation

**Success Metrics**:
- Average adventure length: 35-45 turns
- Epilogue satisfaction: > 70% positive (future survey)
- No adventures exceed 50 turns

**Validation Tests**:
- [ ] Turn counter increments correctly
- [ ] Phase transitions at correct boundaries
- [ ] Quest completion triggers denouement after turn 25
- [ ] Epilogue generates at adventure end

**Review Date**: 2025-01-15

---

## Related Decisions

**Related To**:
- Quest System Design (`docs/design/quest-system.md`)
- State Management (`docs/design/2025-12-22-world-state-management.md`)

**Informs**:
- Future: Quest chaining and multi-session campaigns
- Future: Player analytics and engagement tracking

---

## References

### Documentation
- Quest System Design: `docs/design/quest-system.md`
- State Models: `src/state/models.py`
- Session Manager: `src/state/session_manager.py`

### External Resources
- Three-Act Structure: Classic narrative theory
- CrewAI Flows: https://docs.crewai.com/concepts/flows

### Code References
- `src/state/models.py` - GameState, GamePhase
- `src/api/main.py` - Action endpoint
- `src/agents/narrator.py` - Narrative generation

---

## Metadata

**ADR Number**: 003
**Created**: 2025-12-29
**Last Updated**: 2025-12-29
**Version**: 1.0

**Authors**: Architect Persona
**Reviewers**: Pending

**Tags**: architecture, narrative, pacing, adventure, state-management

**Project Phase**: Development

---

**Status**: PROPOSED
**Next Review**: 2025-01-15
