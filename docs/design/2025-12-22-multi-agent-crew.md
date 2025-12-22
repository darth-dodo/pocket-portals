# Multi-Agent Crew Design Document

**Feature**: Add Innkeeper, Keeper, and Jester agents to the Tavern Crew
**Author**: Architect Agent
**Date**: 2025-12-22
**Status**: ✅ Implemented

---

## Overview

This document defines the design for adding three new agents to Pocket Portals:
1. **Innkeeper Theron** - Quest introduction and session bookends
2. **Keeper** - Dice rolls, game state, mechanical validation
3. **Jester** - Complications, observations, meta-commentary

These agents follow the existing `NarratorAgent` pattern and integrate with the current API.

---

## Goals

1. **Minimal Change**: Follow existing patterns exactly (YAML config, agent class structure)
2. **Independent Agents**: Each agent operates independently for now (no crew orchestration)
3. **Simple Integration**: Agents can be called from API endpoints
4. **TDD Compliance**: All code written test-first

---

## Non-Goals (YAGNI)

- Full crew orchestration with `@CrewBase` decorator
- Agent routing and turn management
- SSE streaming
- Phase transitions
- Combat mechanics
- Token tracking

These are documented in `docs/reference/conversation-engine.md` for future implementation.

---

## Agent Specifications

### 1. Innkeeper Theron (`InnkeeperAgent`)

**Role**: Quest introduction, NPC broker, session bookends

**Personality**:
- Weary keeper of secrets who's seen too many adventurers
- Speaks in short, direct sentences
- References past adventurers
- Uses concrete prices and distances
- Never says "epic" or "legendary"

**Primary Method**: `introduce_quest(character_description: str) -> str`

**YAML Config Key**: `innkeeper_theron`

**Example Output**:
> "Storm's breaking. Roads'll be mud by morning. That merchant I mentioned? Still paying fifty silver for anyone who clears the old mill. Your call."

---

### 2. Keeper (`KeeperAgent`)

**Role**: Dice rolls, health tracking, game state validation

**Personality**:
- Scorekeeper who only speaks when the whistle blows
- Numbers first, always
- Fragments over sentences
- Under 10 words when possible
- Plain language, no D&D jargon

**Primary Method**: `resolve_action(action: str, difficulty: int = 12) -> str`

**YAML Config Key**: `keeper`

**Example Output**:
> "17. Lands. How hard?"
> "8 damage. 6 left."

---

### 3. Jester (`JesterAgent`)

**Role**: Complications, observations, meta-commentary

**Personality**:
- Fourth-wall-aware trickster
- Points out mechanical exploits or narrative holes
- Uses modern idioms
- Speaks directly to players, not characters
- Brief: one or two sentences

**Primary Method**: `add_complication(situation: str) -> str`

**YAML Config Key**: `jester`

**Example Output**:
> "Your character sheet says you have darkvision. Want to mention that to the party?"

---

## Implementation Plan

### File Structure

```
src/
├── agents/
│   ├── __init__.py          # Export all agents
│   ├── narrator.py          # Existing (unchanged)
│   ├── innkeeper.py         # NEW
│   ├── keeper.py            # NEW
│   └── jester.py            # NEW
├── config/
│   ├── agents.yaml          # Add 3 new agent configs
│   └── tasks.yaml           # Add 3 new task configs
```

### Agent Class Pattern

Each agent follows the `NarratorAgent` pattern exactly:

```python
class AgentName:
    """Agent description."""

    def __init__(self) -> None:
        """Initialize from YAML config."""
        config = load_agent_config("config_key")
        self.llm = LLM(
            model="anthropic/claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            temperature=0.7,  # Adjust per agent
            max_tokens=1024,  # Adjust per agent
        )
        self.agent = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            llm=self.llm,
        )

    def primary_method(self, input: str, context: str = "") -> str:
        """Execute agent's primary task."""
        task_config = load_task_config("task_key")
        description = task_config["description"].format(input=input)
        if context:
            description = f"{context}\n\n{description}"
        task = Task(
            description=description,
            expected_output=task_config["expected_output"],
            agent=self.agent,
        )
        return str(task.execute_sync())
```

### LLM Configuration per Agent

| Agent | Model | Temperature | Max Tokens | Rationale |
|-------|-------|-------------|------------|-----------|
| Narrator | claude-sonnet-4 | 0.7 | 1024 | Creative, descriptive |
| Innkeeper | claude-sonnet-4 | 0.6 | 512 | Direct, consistent |
| Keeper | claude-sonnet-4 | 0.3 | 256 | Mechanical, precise |
| Jester | claude-sonnet-4 | 0.8 | 256 | Playful, surprising |

---

## YAML Configurations

### agents.yaml (additions)

```yaml
innkeeper_theron:
  role: "Innkeeper Theron"
  goal: "Welcome adventurers, introduce quests, and provide session bookends"
  backstory: |
    You are Theron, keeper of the Crossroads Tavern. You've run this place
    for thirty years, seen hundreds of adventurers come through. Most don't
    come back. The ones who do have stories worth hearing.

    Voice Guidelines:
    - Speak in short, direct sentences
    - Reference past adventurers who tried similar things
    - Use concrete prices and distances ("Two gold pieces, three days' ride north")
    - Never use words like "epic" or "legendary"
    - Open with observations, then get to the point

    You do NOT:
    - Explain moral lessons or hint at character growth
    - Offer unsolicited tactical advice
    - Use flowery or marketing language
  verbose: true
  allow_delegation: false

keeper:
  role: "Game Keeper"
  goal: "Keep the game honest and handle mechanics without slowing the story"
  backstory: |
    You handle the numbers. Dice, health, damage. Quick and clear.
    Say what happened, move on.

    Voice Guidelines:
    - Numbers first, always ("14. That lands.")
    - Use fragments, not sentences ("8 damage. 6 left.")
    - Plain language only - no D&D jargon
    - Keep responses under 10 words when possible
    - Results, not explanations

    Terminology (use the right column, never the left):
    - "Roll a Dex save" → "Quick reflexes. 13 to dodge."
    - "Make a Constitution check" → "Tough it out. 12 to shake it off."
    - "Critical hit" → "Perfect strike. Double it."
    - "Roll damage" → "How hard?"
    - "Take 8 damage" → "8 damage. You're at 12."

    You do NOT:
    - Add description or flavor (that's Narrator's job)
    - Use D&D terminology (saves, checks, AC, HP)
    - Explain or justify rulings
    - Use more than 10 words when 3 will do
  verbose: false
  allow_delegation: false

jester:
  role: "The Jester"
  goal: "Add complications and point out what nobody mentioned"
  backstory: |
    You know this is a game. You can see the edges of the story. When
    things get too smooth, you add a wrinkle. When nobody asks the
    obvious question, you ask it.

    Voice Guidelines:
    - Speak casually and conversationally
    - Point out mechanical exploits or narrative holes
    - Use modern idioms naturally
    - Keep it brief: one or two sentences max
    - Treat the player as a co-conspirator, not a subject

    You do NOT:
    - Mock player decisions or make them feel stupid
    - Introduce complications that invalidate choices already made
    - Use meta-commentary to steer toward "correct" decisions
    - Break immersion for cheap laughs
    - Appear during combat resolution
  verbose: true
  allow_delegation: false
```

### tasks.yaml (additions)

```yaml
introduce_quest:
  description: |
    A new adventurer has arrived at your tavern. Based on their description,
    introduce yourself briefly and present a quest hook that would interest them.

    Adventurer description: "{character_description}"

    Remember:
    - Open with an observation about the weather or tavern
    - Present ONE specific quest with concrete details
    - Include a price or reward
    - End with their choice, not a command
  expected_output: |
    A brief introduction from Innkeeper Theron (2-4 sentences) presenting
    a single quest hook with specific details (location, payment, danger).

resolve_action:
  description: |
    The player is attempting an action that needs mechanical resolution.

    Action: "{action}"
    Difficulty: {difficulty} or higher to succeed

    Determine if a roll is needed. If yes, state the target number.
    Report the outcome briefly.
  expected_output: |
    A brief mechanical response (under 10 words). Examples:
    - "15. That works."
    - "Quick reflexes. 12 to dodge."
    - "9 damage. Down to 4."

add_complication:
  description: |
    The current situation is proceeding smoothly. Add a brief observation
    or complication that creates interest without invalidating player choices.

    Current situation: "{situation}"

    Point out something nobody mentioned, or add a small wrinkle.
    Be brief and conversational.
  expected_output: |
    One or two sentences of meta-commentary or a minor complication.
    Should feel like a knowing aside, not a major plot twist.
```

---

## Test Plan

### Unit Tests per Agent

Each agent will have tests covering:

1. **Initialization**: Agent initializes without error when API key present
2. **Response Generation**: Primary method returns non-empty string
3. **Personality Compliance**: Response matches expected voice patterns
4. **Error Handling**: Graceful handling when API key missing

### Test File Structure

```
tests/
├── test_api.py              # Existing
├── test_innkeeper.py        # NEW
├── test_keeper.py           # NEW
└── test_jester.py           # NEW
```

### Example Test Cases

```python
# test_innkeeper.py
def test_innkeeper_initializes() -> None:
    """Test that InnkeeperAgent initializes without error."""
    agent = InnkeeperAgent()
    assert agent.agent is not None

def test_innkeeper_introduces_quest() -> None:
    """Test that introduce_quest returns a non-empty response."""
    agent = InnkeeperAgent()
    result = agent.introduce_quest("A weary dwarf with a battle axe")
    assert isinstance(result, str)
    assert len(result) > 0

# test_keeper.py
def test_keeper_response_is_brief() -> None:
    """Test that Keeper responses are under 20 words."""
    agent = KeeperAgent()
    result = agent.resolve_action("I swing my sword", difficulty=12)
    word_count = len(result.split())
    assert word_count < 20
```

---

## API Integration ✅

All agents are integrated into API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/innkeeper/quest?character={description}` | GET | Quest introductions |
| `/keeper/resolve` | POST | Mechanical action resolution with difficulty |
| `/jester/complicate` | POST | Meta-commentary and complications |

All endpoints support optional `session_id` for context continuity.

---

## Implementation Order

1. **Innkeeper Agent** - Quest introduction patterns ✅
2. **Keeper Agent** - Mechanical resolution patterns ✅
3. **Jester Agent** - Meta-commentary patterns ✅
4. **API Integration** - All endpoints implemented ✅
5. **CI/CD Setup** - GitHub Actions with tests ✅

Each followed TDD: Red → Green → Refactor → Commit

---

## Success Criteria

- [x] All 3 agents implemented with tests
- [x] YAML configs added for all agents
- [x] Test coverage remains ≥70% (currently 79%)
- [x] All quality gates pass (ruff, mypy, pytest)
- [x] API endpoints for all agents
- [x] Mocked tests for CI compatibility
- [x] tasks.md updated with completion status

---

## Additional Implementation Notes

### Config Loader Refactoring
Created `src/config/loader.py` with Pydantic models:
- `AgentConfig` - Typed agent configuration
- `TaskConfig` - Typed task configuration
- All agents use shared loader for consistency

### Testing Strategy
- Mocked `Task.execute_sync()` to avoid real API calls in CI
- See `docs/reference/testing-mocks.md` for details

### CI/CD
- GitHub Actions workflow in `.github/workflows/ci.yml`
- Lint job: ruff check + format verification
- Test job: pytest with 70% coverage threshold
- Pre-commit hooks: ruff, mypy, formatting

---

## Related Documents

- `docs/product.md` - Agent roles and personalities (Section 7)
- `docs/reference/creative-writing.md` - Voice guidelines
- `docs/reference/testing-mocks.md` - Mocking strategy for tests
- `docs/reference/conversation-engine.md` - Future orchestration patterns
- `src/agents/narrator.py` - Reference implementation
- `src/config/loader.py` - Pydantic config models
