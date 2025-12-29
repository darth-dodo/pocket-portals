# Adventure Pacing System Design Document

**Project**: Pocket Portals
**Feature**: 50-Turn Adventure Structure with Narrative Arcs
**Status**: Design Complete
**Last Updated**: 2025-12-29
**ADR Reference**: [ADR-003](../adr/003-adventure-pacing-system.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Models](#data-models)
4. [Turn Budget Allocation](#turn-budget-allocation)
5. [Phase Transition Logic](#phase-transition-logic)
6. [Agent Pacing Integration](#agent-pacing-integration)
7. [Closure Triggers](#closure-triggers)
8. [Epilogue System](#epilogue-system)
9. [Implementation Tasks](#implementation-tasks)
10. [Testing Strategy](#testing-strategy)

---

## Overview

The Adventure Pacing System provides structured 50-turn adventures with clear narrative arcs. It combines turn-based phase thresholds with quest-driven triggers to guide agents toward satisfying conclusions while maintaining player agency.

### Key Features

- **Turn Tracking**: Every action increments the adventure turn counter
- **Phase-Based Pacing**: Five narrative phases (Setup → Rising Action → Mid-Point → Climax → Denouement)
- **Quest Integration**: Quest completion can trigger early endings (after turn 25)
- **Agent Awareness**: Pacing context passed to agents for narrative guidance
- **Epilogue Generation**: Personalized adventure conclusions

### Design Principles

1. **Organic Feel**: Quest progress matters more than arbitrary turn counts
2. **Bounded Length**: Hard cap at 50 turns ensures closure
3. **Minimum Satisfaction**: Adventures can't end before turn 25
4. **Agent Guidance**: Pacing hints, not rigid scripts

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ADVENTURE PACING SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  GameState  │───▶│   Pacing    │───▶│   Agents    │             │
│  │ (turn, phase)    │  Calculator │    │ (context)   │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                   │                  │                     │
│        │                   ▼                  ▼                     │
│        │           ┌─────────────┐    ┌─────────────┐             │
│        │           │   Phase     │    │  Narrative  │             │
│        │           │ Transitions │    │   Output    │             │
│        │           └─────────────┘    └─────────────┘             │
│        │                   │                  │                     │
│        ▼                   ▼                  ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   Session   │    │   Closure   │    │  Epilogue   │             │
│  │   Manager   │    │  Triggers   │    │   Agent     │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Player Action
     │
     ▼
┌─────────────────┐
│ Increment Turn  │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Calculate Phase │──────────────────────────┐
└─────────────────┘                          │
     │                                       │
     ▼                                       ▼
┌─────────────────┐                ┌─────────────────┐
│ Check Closure   │───────────────▶│ Trigger         │
│ Conditions      │  if met        │ Epilogue        │
└─────────────────┘                └─────────────────┘
     │ not met                            │
     ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│ Build Pacing    │                │ Adventure       │
│ Context         │                │ Complete        │
└─────────────────┘                └─────────────────┘
     │
     ▼
┌─────────────────┐
│ Execute Agents  │
│ with Context    │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Return Narrative│
│ + Choices       │
└─────────────────┘
```

---

## Data Models

### AdventurePhase Enum

```python
class AdventurePhase(str, Enum):
    """Narrative phases for adventure pacing.

    Each phase has specific narrative characteristics:
    - SETUP: Character introduction, world establishment
    - RISING_ACTION: Conflict introduction, stakes building
    - MID_POINT: Major revelation, point of no return
    - CLIMAX: Maximum tension, confrontation
    - DENOUEMENT: Resolution, reflection, closure
    """
    SETUP = "setup"              # Turns 1-5
    RISING_ACTION = "rising"     # Turns 6-20
    MID_POINT = "midpoint"       # Turns 21-30
    CLIMAX = "climax"            # Turns 31-42
    DENOUEMENT = "denouement"    # Turns 43-50
```

### GameState Additions

```python
class GameState(BaseModel):
    # ... existing fields ...

    # Adventure pacing fields
    adventure_turn: int = Field(default=0, ge=0, le=50)
    adventure_phase: AdventurePhase = AdventurePhase.SETUP
    max_turns: int = Field(default=50, ge=25, le=100)
    adventure_completed: bool = False
    climax_reached: bool = False  # Track if main conflict resolved

    # Moment tracking for epilogue
    adventure_moments: list[AdventureMoment] = Field(default_factory=list)
```

### AdventureMoment Model

```python
class AdventureMoment(BaseModel):
    """Significant moment during adventure for epilogue generation.

    Attributes:
        turn: Turn number when moment occurred
        type: Category of moment (combat_victory, discovery, choice, etc.)
        summary: Brief description of what happened
        significance: Weight for epilogue inclusion (0.0-1.0)
    """
    turn: int
    type: str  # "combat_victory", "discovery", "choice", "npc_interaction"
    summary: str
    significance: float = Field(default=0.5, ge=0.0, le=1.0)
```

### PacingContext Model

```python
class PacingContext(BaseModel):
    """Pacing information passed to agents for narrative guidance.

    This context helps agents understand where they are in the story
    arc and adjust their output accordingly.
    """
    current_turn: int
    max_turns: int
    turns_remaining: int
    current_phase: AdventurePhase
    urgency_level: float  # 0.0-1.0, increases as adventure progresses
    directive: str  # "DEVELOP", "ESCALATE", or "RESOLVE"
    quest_progress: float  # 0.0-1.0, based on objective completion

    @property
    def is_early_game(self) -> bool:
        return self.current_turn <= 15

    @property
    def is_late_game(self) -> bool:
        return self.current_turn >= 35

    @property
    def should_build_tension(self) -> bool:
        return self.current_phase in (
            AdventurePhase.RISING_ACTION,
            AdventurePhase.MID_POINT
        )

    @property
    def should_resolve(self) -> bool:
        return self.current_phase == AdventurePhase.DENOUEMENT
```

---

## Turn Budget Allocation

### Phase Boundaries

| Phase | Turn Range | Percentage | Narrative Focus |
|-------|------------|------------|-----------------|
| **SETUP** | 1-5 | 10% | Character creation, world establishment |
| **RISING_ACTION** | 6-20 | 30% | Quest discovery, obstacles, stakes building |
| **MID_POINT** | 21-30 | 20% | Revelation, point of no return |
| **CLIMAX** | 31-42 | 24% | Maximum tension, confrontation |
| **DENOUEMENT** | 43-50 | 16% | Resolution, rewards, epilogue |

### Visual Timeline

```
Turn:  1    5   10   15   20   25   30   35   40   45   50
       │    │    │    │    │    │    │    │    │    │    │
Phase: ├SETUP├─────RISING ACTION─────├──MID-POINT──├──CLIMAX──├─DENOUE─┤
       │    │    │    │    │    │    │    │    │    │    │
Events:│    │    │    │    │    │    │    │    │    │    │
       │    │    │    │    │    │    │    │    │    │    │
       │ Character    │ First │    │Twist│    │Final│    │Epilogue
       │ created      │ combat│    │     │    │boss │    │
```

---

## Phase Transition Logic

### Core Phase Calculation

```python
def get_turn_based_phase(turn: int) -> AdventurePhase:
    """Calculate phase based purely on turn number."""
    if turn <= 5:
        return AdventurePhase.SETUP
    elif turn <= 20:
        return AdventurePhase.RISING_ACTION
    elif turn <= 30:
        return AdventurePhase.MID_POINT
    elif turn <= 42:
        return AdventurePhase.CLIMAX
    else:
        return AdventurePhase.DENOUEMENT


def calculate_adventure_phase(state: GameState) -> AdventurePhase:
    """Calculate phase considering both turns and quest progress.

    Quest completion can accelerate to denouement, but only after
    minimum adventure length (turn 25) to ensure satisfying story.
    """
    turn = state.adventure_turn
    turn_phase = get_turn_based_phase(turn)

    # Quest completion acceleration (after minimum length)
    if state.active_quest and state.active_quest.is_complete:
        if turn >= 25:
            return AdventurePhase.DENOUEMENT

    # Urgency escalation near cap
    if turn >= 40 and turn_phase == AdventurePhase.CLIMAX:
        # If climax moment hasn't happened, escalate urgency
        if not state.climax_reached:
            return AdventurePhase.CLIMAX  # Stay in climax, agents handle urgency

    return turn_phase
```

### Urgency Level Calculation

```python
def calculate_urgency(state: GameState) -> float:
    """Calculate urgency level (0.0-1.0) based on adventure progress.

    Urgency increases as:
    - Adventure progresses toward turn limit
    - Quest nears completion
    - Critical moments occur
    """
    turn_urgency = state.adventure_turn / state.max_turns

    # Quest progress modifier
    quest_modifier = 0.0
    if state.active_quest:
        completed = sum(1 for o in state.active_quest.objectives if o.is_completed)
        total = len(state.active_quest.objectives)
        quest_modifier = (completed / total) * 0.2 if total > 0 else 0.0

    # Phase modifier
    phase_modifiers = {
        AdventurePhase.SETUP: 0.0,
        AdventurePhase.RISING_ACTION: 0.1,
        AdventurePhase.MID_POINT: 0.2,
        AdventurePhase.CLIMAX: 0.4,
        AdventurePhase.DENOUEMENT: 0.3,  # Slightly lower - winding down
    }
    phase_modifier = phase_modifiers.get(state.adventure_phase, 0.0)

    # Combine and clamp
    urgency = turn_urgency + quest_modifier + phase_modifier
    return min(1.0, urgency)
```

### Pacing Directive

```python
def get_pacing_directive(state: GameState) -> str:
    """Get narrative directive based on current phase and progress."""
    phase = state.adventure_phase
    turn = state.adventure_turn

    if phase == AdventurePhase.SETUP:
        return "ESTABLISH - Introduce character and world"

    elif phase == AdventurePhase.RISING_ACTION:
        if turn < 10:
            return "DEVELOP - Build quest engagement"
        else:
            return "ESCALATE - Increase tension and stakes"

    elif phase == AdventurePhase.MID_POINT:
        return "REVEAL - Introduce twist or major revelation"

    elif phase == AdventurePhase.CLIMAX:
        if turn >= 40:
            return "CONFRONT - Drive toward final confrontation"
        else:
            return "INTENSIFY - Build maximum tension"

    else:  # DENOUEMENT
        return "RESOLVE - Wind down and provide closure"
```

---

## Agent Pacing Integration

### Context Building

```python
def build_context_with_pacing(
    state: GameState,
    history: list[dict[str, str]],
) -> str:
    """Build context string including pacing information for agents."""

    # Calculate pacing context
    pacing = PacingContext(
        current_turn=state.adventure_turn,
        max_turns=state.max_turns,
        turns_remaining=state.max_turns - state.adventure_turn,
        current_phase=state.adventure_phase,
        urgency_level=calculate_urgency(state),
        directive=get_pacing_directive(state),
        quest_progress=calculate_quest_progress(state),
    )

    # Build pacing hint for agents
    pacing_hint = f"""
[NARRATIVE PACING - Turn {pacing.current_turn}/{pacing.max_turns}]
Phase: {pacing.current_phase.value.upper()}
Urgency: {pacing.urgency_level:.0%}
Directive: {pacing.directive}
Quest Progress: {pacing.quest_progress:.0%}
"""

    # Combine with existing context
    base_context = build_context(
        history,
        character_sheet=state.character_sheet,
        character_description=state.character_description,
    )

    return pacing_hint + "\n" + base_context
```

### Narrator Backstory Update

Add pacing guidelines to `src/config/agents.yaml`:

```yaml
narrator:
  # ... existing config ...
  backstory: |
    # ... existing backstory ...

    PACING GUIDELINES (adjust based on [NARRATIVE PACING] context):

    SETUP (turns 1-5):
    - Establish the character's presence in the world
    - Introduce the initial situation vividly but concisely
    - Create atmosphere and set expectations
    - End scenes with hooks toward the quest

    RISING_ACTION (turns 6-20):
    - Build tension gradually through complications
    - Introduce obstacles that test the character
    - Deepen emotional investment in the quest
    - Include minor victories and setbacks
    - Foreshadow larger conflicts to come

    MID_POINT (turns 21-30):
    - Reveal something that changes everything
    - Raise stakes significantly - what was minor becomes major
    - Create a point of no return for the character
    - Shift the emotional tone of the adventure
    - Connect earlier events to larger pattern

    CLIMAX (turns 31-42):
    - Maximum tension in every scene
    - Confrontation with the main obstacle/enemy
    - Player choices carry heavy weight
    - Build inexorably toward resolution
    - Use shorter, punchier descriptions

    DENOUEMENT (turns 43-50):
    - Wind down gracefully from peak tension
    - Show consequences of player choices
    - Provide emotional closure appropriate to outcome
    - Celebrate victories or honor sacrifices
    - Leave room for reflection
```

---

## Closure Triggers

### Trigger Hierarchy

1. **Hard Cap (Turn 50)**: Adventure ends regardless of quest state
2. **Quest Completion + Turn ≥ 25**: Triggers denouement phase
3. **Soft Trigger (Turn 48+)**: If in denouement, prompt for conclusion

### Implementation

```python
async def check_closure_triggers(
    state: GameState,
    sm: SessionManager,
) -> tuple[bool, str | None]:
    """Check if adventure should end.

    Returns:
        Tuple of (should_end, closure_reason)
    """
    turn = state.adventure_turn

    # Hard cap
    if turn >= state.max_turns:
        return True, "turn_limit"

    # Quest completion after minimum length
    if state.active_quest and state.active_quest.is_complete:
        if turn >= 25:
            return True, "quest_complete"

    # Soft trigger in denouement
    if state.adventure_phase == AdventurePhase.DENOUEMENT:
        if turn >= 48:
            return True, "denouement_complete"

    return False, None


async def _trigger_epilogue(
    request: Request,
    state: GameState,
    closure_reason: str,
) -> NarrativeResponse:
    """Generate epilogue and mark adventure complete."""
    sm = get_session_manager(request)

    # Mark adventure complete
    await sm.set_adventure_completed(state.session_id, True)

    # Generate epilogue
    if epilogue_agent:
        epilogue_context = build_epilogue_context(state)
        epilogue = epilogue_agent.generate_epilogue(
            character_sheet=state.character_sheet,
            quest_summary=format_quest_summary(state),
            outcome=determine_outcome(state),
            key_moments=get_top_moments(state, count=5),
            turns_taken=state.adventure_turn,
            closure_reason=closure_reason,
        )
    else:
        # Fallback epilogue
        epilogue = generate_fallback_epilogue(state, closure_reason)

    return NarrativeResponse(
        narrative=epilogue,
        session_id=state.session_id,
        choices=["Begin New Adventure", "View Character Sheet", "Share Story"],
    )
```

---

## Epilogue System

### EpilogueAgent Configuration

```yaml
# src/config/agents.yaml

epilogue_writer:
  role: "Adventure Chronicler"
  goal: "Create personalized, emotionally resonant adventure conclusions"
  backstory: |
    You are the chronicler who records every hero's tale. You have witnessed
    countless endings - triumphant, bittersweet, tragic, and hopeful. Your
    role is to craft the final chapter that honors the journey.

    EPILOGUE STRUCTURE:
    1. Opening hook: "And so..." or "Thus concluded..." (varies by tone)
    2. Journey recap: 2-3 key moments from the adventure
    3. Character growth: How the hero changed through their trials
    4. Quest outcome: The concrete result of their efforts
    5. Future hook: What lies ahead (encourages replay)

    TONE MATCHING:
    - Victory: Triumphant but not saccharine. Honor the struggle.
    - Partial Success: Bittersweet. Acknowledge both achievement and cost.
    - Quest Incomplete: Honorable. Emphasize growth over failure.
    - Defeat: Respectful. The hero's story continues beyond this setback.

    STYLE GUIDELINES:
    - Reference specific player choices by name
    - Use character's name throughout
    - Match the narrative voice established earlier
    - Keep epilogue 150-200 words (concise but complete)
    - End with a forward-looking statement

    Content Rating (PG-13): Epilogues are hopeful. No dark endings, trauma,
    or punishment. Even defeats are framed as learning experiences.

  verbose: false
  allow_delegation: false
  llm:
    model: claude-sonnet-4-20250514
    temperature: 0.6  # Consistent but creative
    max_tokens: 400   # Enough for complete epilogue
```

### Epilogue Task Configuration

```yaml
# src/config/tasks.yaml

generate_epilogue:
  description: |
    Generate a personalized epilogue for this adventure.

    CHARACTER:
    {character_summary}

    QUEST:
    {quest_summary}

    OUTCOME: {outcome}

    KEY MOMENTS FROM THE ADVENTURE:
    {key_moments}

    ADVENTURE LENGTH: {turns_taken} of {max_turns} turns
    CLOSURE REASON: {closure_reason}

    Create a 150-200 word epilogue that:
    1. Opens with an appropriate narrative hook
    2. References 2-3 specific moments from the adventure
    3. Describes how the character has changed
    4. States the quest outcome clearly
    5. Ends with a forward-looking statement

    The tone should match the outcome:
    - "victory": triumphant, celebratory
    - "partial": bittersweet, thoughtful
    - "incomplete": respectful, encouraging

  expected_output: "A complete epilogue narrative (150-200 words)"
  agent: epilogue_writer
```

### Moment Tracking

```python
def detect_adventure_moments(
    action: str,
    narrative: str,
    state: GameState,
) -> list[AdventureMoment]:
    """Detect significant moments from action and narrative.

    Called after each turn to track memorable events for epilogue.
    """
    moments = []

    # Combat victory detection
    if state.combat_state and not state.combat_state.is_active:
        if "victory" in narrative.lower() or "defeated" in narrative.lower():
            enemy_name = (
                state.combat_state.enemy_template.name
                if state.combat_state.enemy_template
                else "enemy"
            )
            moments.append(AdventureMoment(
                turn=state.adventure_turn,
                type="combat_victory",
                summary=f"Defeated {enemy_name} in combat",
                significance=0.8,
            ))

    # Quest objective completion
    if state.active_quest:
        for obj in state.active_quest.objectives:
            if obj.is_completed:
                moments.append(AdventureMoment(
                    turn=state.adventure_turn,
                    type="discovery",
                    summary=f"Completed: {obj.description[:50]}",
                    significance=0.7,
                ))

    # Key choice detection
    choice_indicators = [
        "choose", "decide", "accept", "refuse", "sacrifice",
        "agree", "decline", "promise", "betray"
    ]
    if any(indicator in action.lower() for indicator in choice_indicators):
        moments.append(AdventureMoment(
            turn=state.adventure_turn,
            type="choice",
            summary=action[:80],
            significance=0.6,
        ))

    # Discovery detection
    discovery_indicators = ["find", "discover", "reveal", "uncover", "learn"]
    if any(indicator in narrative.lower() for indicator in discovery_indicators):
        # Extract brief summary from narrative
        summary = narrative[:80] + "..." if len(narrative) > 80 else narrative
        moments.append(AdventureMoment(
            turn=state.adventure_turn,
            type="discovery",
            summary=summary,
            significance=0.5,
        ))

    return moments


def get_top_moments(state: GameState, count: int = 5) -> list[str]:
    """Get top N moments by significance for epilogue."""
    sorted_moments = sorted(
        state.adventure_moments,
        key=lambda m: (m.significance, m.turn),
        reverse=True,
    )
    return [m.summary for m in sorted_moments[:count]]
```

---

## Implementation Tasks

### Phase 1: Core Turn Tracking

**Files to modify**: `src/state/models.py`, `src/state/session_manager.py`

```python
# Task 1.1: Add AdventurePhase enum
# Task 1.2: Add pacing fields to GameState
# Task 1.3: Add AdventureMoment model
# Task 1.4: Add SessionManager methods:
#   - increment_adventure_turn()
#   - set_adventure_phase()
#   - set_adventure_completed()
#   - add_adventure_moment()
```

### Phase 2: Pacing Integration

**Files to modify**: `src/api/main.py`, `src/config/agents.yaml`

```python
# Task 2.1: Create pacing utility module (src/engine/pacing.py)
# Task 2.2: Add PacingContext model
# Task 2.3: Update build_context() with pacing hints
# Task 2.4: Hook turn increment into /action endpoint
# Task 2.5: Update narrator backstory with pacing guidelines
```

### Phase 3: Closure Triggers

**Files to modify**: `src/api/main.py`

```python
# Task 3.1: Implement check_closure_triggers()
# Task 3.2: Implement _trigger_epilogue()
# Task 3.3: Add closure checks to /action endpoint
# Task 3.4: Handle adventure completion state
```

### Phase 4: Epilogue Agent

**New files**: `src/agents/epilogue.py`
**Files to modify**: `src/config/agents.yaml`, `src/config/tasks.yaml`, `src/api/main.py`

```python
# Task 4.1: Create EpilogueAgent class
# Task 4.2: Add epilogue_writer config to agents.yaml
# Task 4.3: Add generate_epilogue task to tasks.yaml
# Task 4.4: Implement moment tracking in /action
# Task 4.5: Initialize epilogue agent in lifespan
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_pacing.py

def test_get_turn_based_phase_boundaries():
    """Test phase transitions at exact boundaries."""
    assert get_turn_based_phase(1) == AdventurePhase.SETUP
    assert get_turn_based_phase(5) == AdventurePhase.SETUP
    assert get_turn_based_phase(6) == AdventurePhase.RISING_ACTION
    assert get_turn_based_phase(20) == AdventurePhase.RISING_ACTION
    assert get_turn_based_phase(21) == AdventurePhase.MID_POINT
    assert get_turn_based_phase(30) == AdventurePhase.MID_POINT
    assert get_turn_based_phase(31) == AdventurePhase.CLIMAX
    assert get_turn_based_phase(42) == AdventurePhase.CLIMAX
    assert get_turn_based_phase(43) == AdventurePhase.DENOUEMENT
    assert get_turn_based_phase(50) == AdventurePhase.DENOUEMENT


def test_quest_completion_triggers_denouement_after_turn_25():
    """Quest completion should trigger denouement after minimum length."""
    state = GameState(
        session_id="test",
        adventure_turn=30,
        active_quest=Quest(
            id="q1",
            title="Test",
            description="Test quest",
            objectives=[QuestObjective(id="o1", description="Test", is_completed=True)],
        ),
    )
    assert calculate_adventure_phase(state) == AdventurePhase.DENOUEMENT


def test_quest_completion_doesnt_trigger_before_turn_25():
    """Quest completion should NOT trigger denouement before turn 25."""
    state = GameState(
        session_id="test",
        adventure_turn=15,
        active_quest=Quest(
            id="q1",
            title="Test",
            description="Test quest",
            objectives=[QuestObjective(id="o1", description="Test", is_completed=True)],
        ),
    )
    assert calculate_adventure_phase(state) != AdventurePhase.DENOUEMENT


def test_urgency_increases_with_turn():
    """Urgency should increase as adventure progresses."""
    state_early = GameState(session_id="test", adventure_turn=10, max_turns=50)
    state_late = GameState(session_id="test", adventure_turn=45, max_turns=50)

    assert calculate_urgency(state_late) > calculate_urgency(state_early)


def test_closure_triggers_at_turn_50():
    """Adventure should end at turn 50 regardless of quest state."""
    state = GameState(session_id="test", adventure_turn=50, max_turns=50)
    should_end, reason = await check_closure_triggers(state, mock_sm)

    assert should_end is True
    assert reason == "turn_limit"
```

### Integration Tests

```python
# tests/test_api.py

async def test_turn_increments_on_action():
    """Turn counter should increment with each action."""
    response = await client.get("/start?skip_creation=true")
    session_id = response.json()["session_id"]

    # First action
    response = await client.post("/action", json={
        "session_id": session_id,
        "action": "Look around",
    })
    # State should show turn 1

    # Second action
    response = await client.post("/action", json={
        "session_id": session_id,
        "action": "Move forward",
    })
    # State should show turn 2


async def test_adventure_ends_at_turn_50():
    """Adventure should trigger epilogue at turn 50."""
    # Create session and advance to turn 49
    # Execute action
    # Verify epilogue response returned
    pass


async def test_pacing_context_included_in_agent_calls():
    """Verify pacing context is passed to agents."""
    # Mock agent and verify context includes pacing hint
    pass
```

### Manual Testing Checklist

- [ ] Complete 50-turn adventure - verify epilogue appears
- [ ] Complete quest at turn 30 - verify denouement triggers
- [ ] Complete quest at turn 15 - verify adventure continues
- [ ] Verify narrative tone changes across phases
- [ ] Check epilogue references actual player choices
- [ ] Test adventure completion UI state

---

## Appendix: File Reference

| File | Purpose |
|------|---------|
| `src/state/models.py` | AdventurePhase, AdventureMoment, GameState additions |
| `src/state/session_manager.py` | Turn tracking methods |
| `src/engine/pacing.py` | PacingContext, phase calculation, urgency |
| `src/agents/epilogue.py` | EpilogueAgent implementation |
| `src/config/agents.yaml` | Epilogue agent config, narrator pacing guidelines |
| `src/config/tasks.yaml` | generate_epilogue task |
| `src/api/main.py` | Closure triggers, epilogue integration |
| `tests/test_pacing.py` | Pacing unit tests |
| `tests/test_api.py` | Integration tests |

---

**Document Version**: 1.0
**Author**: Architect Persona
**Review Status**: Ready for Implementation
