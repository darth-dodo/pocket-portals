# Pocket Portals Architecture

**Version 1.0 | Extreme Programming + BDD Edition**

---

## XP Principles Applied

This architecture embraces Extreme Programming values throughout:

| XP Value | Application |
|----------|-------------|
| **Simplicity** | Do the simplest thing that could possibly work. No speculative features. |
| **Feedback** | Fast cycles: user input → agent response → user choice. Continuous learning. |
| **Communication** | Agents communicate intent via annotations. Code communicates via tests. |
| **Courage** | Delete code that isn't working. Refactor mercilessly. Ship early. |
| **Respect** | Respect user time (60s to adventure). Respect token budgets. Respect constraints. |

---

## BDD Principles Applied

Behavior-Driven Development ensures we build what users actually need:

| BDD Concept | Application |
|-------------|-------------|
| **Ubiquitous Language** | "Adventure", "Quest", "Tavern" — domain terms used everywhere |
| **Outside-In** | Start with user behavior, work inward to implementation |
| **Living Documentation** | Feature files ARE the specification |
| **Three Amigos** | User story, agent behavior, and test all align |
| **Given-When-Then** | Every scenario follows this structure |

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                    HTMX + Jinja2 Templates                      │
│         (Progressive enhancement, no JS framework)              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ SSE / HTTP
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Session    │  │    Stream    │  │    Export    │          │
│  │   Manager    │  │   Handler    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CREWAI LAYER                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    TAVERN CREW                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │Innkeeper │ │ Narrator │ │Keeper│ │  Jester  │  │   │
│  │  │  Theron  │ │          │ │          │ │          │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SHARED TOOLS                          │   │
│  │  [DiceRoller] [CharacterSheet] [WorldState] [Combat]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ANTHROPIC CLAUDE API                          │
│            Sonnet (narrative) │ Haiku (mechanics)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. XP Practice: Simple Design

### The Simplest Thing That Works

**What we build:**
- Single FastAPI application (monolith)
- In-memory session state (dict per session)
- Server-rendered HTML with HTMX for interactivity
- CrewAI for agent orchestration
- SQLite for adventure logs (if persistence needed)

**What we DON'T build (yet):**
- Microservices
- Redis/external cache
- WebSocket complexity
- User accounts/auth
- Database for session state
- Frontend JavaScript framework

### Four Rules of Simple Design

1. **Passes all tests** → Every agent output validated by Keeper
2. **Reveals intention** → Agent annotations explain reasoning
3. **No duplication** → Shared tools, single source of truth for world state
4. **Fewest elements** → Minimal agent count that delivers value

---

## 3. XP Practice: Incremental Design

### Walking Skeleton (Week 1)

The thinnest possible slice through all layers:

```
User Input → FastAPI → Single Agent (Narrator) → Streaming Response → UI
```

**Deliverable:** User types "A grumpy dwarf fighter" → Gets narrative response streamed to screen.

**No:**
- Character sheet generation
- Multiple agents
- Dice rolling
- Choices/branching

### Iteration 1: Character Creation (Week 2)

```
User Input → Character Crew (parallel) → Character Sheet → UI Review
```

**Add:**
- Keeper agent (stats generation)
- Character sheet Pydantic model
- Accept/modify UI flow

### Iteration 2: Quest Generation (Week 3)

```
Character Sheet → Innkeeper Agent → Quest Hook → Narrator Agent → Scene 1
```

**Add:**
- Innkeeper agent
- Quest personalization from backstory
- World state initialization

### Iteration 3: Gameplay Loop (Week 4)

```
Scene → Choices → User Input → Narrator Response → Consequence Tracking
```

**Add:**
- Branching choices
- World state updates
- Jester interventions

### Iteration 4: Combat & Resolution (Week 5)

```
Combat Trigger → Initiative → Turn Loop → Resolution → Epilogue
```

**Add:**
- Dice tools
- HP tracking
- Combat state machine
- Epilogue generation

---

## 4. XP Practice: Test-First Development

### Test Pyramid for AI Agents

```
         ╱╲
        ╱  ╲         E2E Tests (few)
       ╱────╲        Full adventure playthrough
      ╱      ╲
     ╱────────╲      Integration Tests (some)
    ╱          ╲     Agent → Tools → Output validation
   ╱────────────╲
  ╱              ╲   Unit Tests (many)
 ╱────────────────╲  Tools, schemas, state management
```

### Test Categories

**Unit Tests (fast, many):**
```python
# test_dice.py
def test_roll_d20_returns_valid_range():
    result = dice_roller.roll("1d20")
    assert 1 <= result.total <= 20

def test_character_sheet_validates_stats():
    with pytest.raises(ValidationError):
        CharacterSheet(strength=25)  # Max is 20
```

**Integration Tests (medium speed, some):**
```python
# test_agents.py
def test_chronicler_validates_combat_action():
    action = CombatAction(type="attack", target="goblin", roll=15)
    result = chronicler.validate(action, character_sheet)
    assert result.is_valid
    assert result.damage > 0

def test_dm_generates_scene_with_character_context():
    character = CharacterSheet(name="Grimlock", backstory="Lost his clan")
    scene = dm.generate_scene(character, quest_hook)
    assert "clan" in scene.lower() or "loss" in scene.lower()
```

**E2E Tests (slow, few):**
```python
# test_adventure.py
def test_complete_adventure_flow():
    session = create_session()

    # Character creation
    character = session.create_character("A vengeful tiefling warlock")
    assert character.class_ == "Warlock"

    # Quest hook
    quest = session.get_quest_hook()
    assert quest.relates_to(character.backstory)

    # Make choices through adventure
    for _ in range(5):
        choices = session.get_choices()
        session.choose(choices[0])

    # Epilogue
    epilogue = session.get_epilogue()
    assert epilogue.references_choices_made()
```

### Mocking Strategy

```python
# Expensive: Real Claude API calls
# Cheap: Recorded responses for deterministic tests

@pytest.fixture
def mock_claude():
    with vcr.use_cassette("character_creation.yaml"):
        yield

def test_character_creation_with_recorded_response(mock_claude):
    result = character_crew.analyze("A sneaky halfling rogue")
    assert result.class_ == "Rogue"
```

---

## 5. BDD Practice: Feature Specifications

### Gherkin Feature Files

All user-facing behavior is specified in Gherkin before implementation:

```gherkin
# features/character_creation.feature

Feature: Character Creation
  As a solo adventurer
  I want to describe my character in plain English
  So that I can start an adventure without complex forms

  Background:
    Given I am at the tavern entrance
    And the Innkeeper is ready to greet me

  @P0 @happy-path
  Scenario: Create character from description
    When I describe my character as "A grumpy dwarf fighter who lost his clan to orcs"
    Then the Keeper should generate a character sheet
    And the character class should be "Fighter"
    And the character race should be "Dwarf"
    And the backstory should reference "clan" and "orcs"
    And I should see the character sheet within 30 seconds

  @P0 @validation
  Scenario: Character stats are valid D&D 5e
    When I describe my character as "An elderly wizard"
    Then all ability scores should be between 3 and 18
    And the total ability score points should follow standard array or point buy
    And the character level should be 1

  @P0 @modification
  Scenario: Modify generated character
    Given the Keeper has generated my character sheet
    When I modify my character name to "Grimlock Stonefist"
    And I accept the character
    Then my adventure should begin with that name
    And the Innkeeper should address me as "Grimlock"

  @P1 @edge-case
  Scenario: Handle vague character description
    When I describe my character as "someone cool"
    Then the Keeper should ask clarifying questions
    And I should see suggested character concepts
```

```gherkin
# features/quest_generation.feature

Feature: Personalized Quest Generation
  As a solo adventurer
  I want quests tailored to my character's backstory
  So that my adventure feels personal and meaningful

  @P0 @personalization
  Scenario: Quest hooks into backstory
    Given I have a character with backstory "Seeking revenge for my murdered sister"
    When the Innkeeper introduces a quest
    Then the quest should reference family, loss, or revenge
    And an NPC should have connection to my backstory

  @P0 @variety
  Scenario Outline: Different backstories get different quests
    Given I have a character with backstory "<backstory>"
    When the Innkeeper introduces a quest
    Then the quest theme should match "<expected_theme>"

    Examples:
      | backstory                          | expected_theme     |
      | Exiled from my homeland            | redemption/return  |
      | Hunting a legendary monster        | hunt/tracking      |
      | Searching for a lost artifact      | discovery/treasure |
      | Fleeing from a dark past           | pursuit/secrets    |

  @P0 @npcs
  Scenario: Quest introduces memorable NPC
    Given I have accepted a quest
    When I meet the quest-giver NPC
    Then the NPC should have a distinct personality
    And the NPC should have a name
    And the NPC should remember my character's name
```

```gherkin
# features/gameplay_loop.feature

Feature: Interactive Adventure Gameplay
  As a solo adventurer
  I want meaningful choices that affect my story
  So that my adventure feels like real D&D

  @P0 @choices
  Scenario: Branching narrative choices
    Given I am in an active scene
    When the Narrator presents a decision point
    Then I should see 3-4 predefined choices
    And I should have an option for custom input
    And each choice should have visible consequences

  @P0 @consequences
  Scenario: Choices have lasting effects
    Given I chose to "spare the bandit leader"
    When I encounter related NPCs later
    Then they should reference my earlier choice
    And the world state should reflect my decision

  @P0 @custom-input
  Scenario: Handle unexpected player actions
    Given the Narrator presents choices: Attack, Negotiate, Flee
    When I type "I try to seduce the dragon"
    Then the Narrator should acknowledge my creative choice
    And the Keeper should determine if a roll is needed
    And the narrative should continue coherently

  @P1 @jester
  Scenario: Jester adds complications
    Given I am progressing smoothly through the adventure
    When a scene has been calm for 3 exchanges
    Then the Jester may introduce a complication
    And I should see a Jester annotation
    And the complication should be narratively appropriate
```

```gherkin
# features/combat.feature

Feature: Turn-Based Combat
  As a solo adventurer
  I want tactical combat with real dice rolls
  So that battles feel exciting and consequential

  @P0 @initiative
  Scenario: Combat begins with initiative
    Given I encounter hostile enemies
    When combat begins
    Then the Keeper should roll initiative for all combatants
    And I should see the turn order displayed
    And the highest initiative should act first

  @P0 @dice-rolls
  Scenario: Attack with dice mechanics
    Given it is my turn in combat
    When I choose to attack an enemy
    Then the Keeper should roll a d20 for attack
    And I should see the dice result with animation
    And if the roll meets or exceeds AC, damage should be rolled
    And the Narrator should narrate the outcome

  @P0 @damage
  Scenario: Track HP and damage
    Given I have 25 HP
    When an enemy hits me for 8 damage
    Then my HP should be reduced to 17
    And I should see my updated HP displayed
    And the Narrator should describe the hit narratively

  @P0 @death
  Scenario: Character reaches 0 HP
    Given I have 3 HP
    When an enemy hits me for 10 damage
    Then I should fall unconscious
    And the Keeper should explain death saving throws
    And the adventure should handle defeat gracefully

  @P2 @battlefield
  Scenario: ASCII battlefield visualization
    Given combat has multiple combatants
    When I view the battlefield
    Then I should see an ASCII grid showing positions
    And my character should be marked distinctly
    And enemies should show remaining HP indicators
```

```gherkin
# features/epilogue.feature

Feature: Adventure Conclusion
  As a solo adventurer
  I want a personalized ending that reflects my journey
  So that my adventure feels complete and memorable

  @P0 @epilogue
  Scenario: Generate personalized epilogue
    Given I have completed the main quest
    When the adventure concludes
    Then the Narrator should generate an epilogue
    And the epilogue should reference my key choices
    And the epilogue should mention NPCs I befriended or opposed
    And the tone should match my adventure's outcome

  @P0 @character-sheet
  Scenario: Final character sheet with achievements
    Given the adventure has concluded
    When I view my final character sheet
    Then I should see any XP or level gains
    And I should see notable achievements listed
    And I should see key relationships formed

  @P1 @export
  Scenario: Download adventure log
    Given the adventure has concluded
    When I click "Download Adventure Log"
    Then I should receive a markdown file
    And the file should contain the full narrative
    And the file should include my character sheet
    And the file should list my choices and outcomes
```

### Step Definitions Structure

```python
# tests/bdd/steps/character_steps.py

from behave import given, when, then
from pocket_portals.schemas import CharacterSheet


@given("I am at the tavern entrance")
def step_at_tavern(context):
    context.session = create_test_session()
    context.location = "tavern_entrance"


@when('I describe my character as "{description}"')
def step_describe_character(context, description):
    context.character_input = description
    context.character = context.session.create_character(description)


@then("the Keeper should generate a character sheet")
def step_chronicler_generates(context):
    assert context.character is not None
    assert isinstance(context.character, CharacterSheet)


@then('the character class should be "{expected_class}"')
def step_verify_class(context, expected_class):
    assert context.character.class_ == expected_class


@then('the backstory should reference "{keyword1}" and "{keyword2}"')
def step_backstory_references(context, keyword1, keyword2):
    backstory = context.character.backstory.lower()
    assert keyword1.lower() in backstory or keyword2.lower() in backstory
```

```python
# tests/bdd/steps/combat_steps.py

from behave import given, when, then


@given("I encounter hostile enemies")
def step_encounter_enemies(context):
    context.enemies = context.session.spawn_enemies(count=2)


@when("combat begins")
def step_combat_begins(context):
    context.combat = context.session.start_combat(context.enemies)
    context.initiative_order = context.combat.roll_initiative()


@then("the Keeper should roll initiative for all combatants")
def step_initiative_rolled(context):
    assert len(context.initiative_order) == len(context.enemies) + 1


@then("I should see the turn order displayed")
def step_turn_order_visible(context):
    for combatant in context.initiative_order:
        assert combatant.initiative_roll is not None
        assert combatant.name is not None
```

### BDD Test Organization

```
tests/
├── bdd/
│   ├── features/
│   │   ├── character_creation.feature
│   │   ├── quest_generation.feature
│   │   ├── gameplay_loop.feature
│   │   ├── combat.feature
│   │   └── epilogue.feature
│   │
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── character_steps.py
│   │   ├── quest_steps.py
│   │   ├── gameplay_steps.py
│   │   ├── combat_steps.py
│   │   └── epilogue_steps.py
│   │
│   ├── environment.py          # Behave hooks
│   └── behave.ini              # Behave configuration
│
├── unit/                       # XP unit tests
├── integration/                # XP integration tests
└── e2e/                        # XP E2E tests
```

### Running BDD Tests

```bash
# Run all BDD scenarios
make bdd

# Run specific feature
uv run behave tests/bdd/features/combat.feature

# Run by tag
uv run behave --tags=@P0           # Must-have features only
uv run behave --tags=@happy-path   # Happy path scenarios
uv run behave --tags=~@P2          # Exclude nice-to-have

# Generate living documentation
uv run behave --format html --outfile docs/features.html
```

### BDD + Agent Alignment

Each agent's behavior maps to specific Gherkin scenarios:

| Agent | Primary Features | Key Scenarios |
|-------|-----------------|---------------|
| Innkeeper | quest_generation.feature | Quest hooks, NPC introductions |
| Narrator | gameplay_loop.feature, epilogue.feature | Scene generation, choices, endings |
| Keeper | character_creation.feature, combat.feature | Stats, dice, mechanics |
| Jester | gameplay_loop.feature | Complications, foreshadowing |

---

## 6. XP Practice: Continuous Integration

### CI Pipeline (Every Push)

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Lint
        run: uv run ruff check src/ tests/

      - name: Type check
        run: uv run mypy src/

      - name: Unit tests
        run: uv run pytest tests/unit -v

      - name: Integration tests
        run: uv run pytest tests/integration -v
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Coverage
        run: uv run pytest --cov=src --cov-fail-under=80

      - name: BDD Tests (P0 scenarios)
        run: uv run behave tests/bdd --tags=@P0
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Ten-Minute Build

**Target:** All tests complete in <10 minutes

**Strategy:**
- Parallel test execution
- Mock expensive API calls in unit tests
- Real API calls only in integration suite (with VCR recording)
- Skip E2E in CI (run nightly)

---

## 6. XP Practice: Pair Programming (Agent Edition)

### Agent Pairing Strategy

Every significant output involves two agents:

| Primary Agent | Pair Agent | Purpose |
|--------------|------------|---------|
| Narrator | Jester | Narrator writes scene, Jester adds complications |
| Keeper | Narrator | Keeper validates mechanics, Narrator narrates outcome |
| Innkeeper | Narrator | Innkeeper hooks quest, Narrator develops it |

### Review Agent Pattern

```python
class AgentPair:
    """XP Pair Programming applied to AI agents."""

    def __init__(self, driver: Agent, navigator: Agent):
        self.driver = driver      # Generates content
        self.navigator = navigator # Reviews/validates

    def execute(self, task: Task) -> Output:
        draft = self.driver.execute(task)
        review = self.navigator.review(draft)

        if review.needs_revision:
            return self.driver.revise(draft, review.feedback)
        return draft
```

---

## 7. XP Practice: Collective Code Ownership

### Shared Components

No agent "owns" code. All agents share:

```
src/pocket_portals/
├── agents/           # Agent definitions (all can modify)
│   ├── innkeeper.py
│   ├── narrator.py
│   ├── chronicler.py
│   └── jester.py
│
├── tools/            # Shared tools (any agent can use)
│   ├── dice.py
│   ├── character_sheet.py
│   ├── world_state.py
│   └── combat.py
│
├── schemas/          # Shared data models
│   ├── character.py
│   ├── quest.py
│   ├── scene.py
│   └── combat.py
│
├── crew/             # Crew orchestration
│   ├── character_crew.py
│   └── adventure_crew.py
│
└── api/              # FastAPI endpoints
    ├── routes.py
    └── streaming.py
```

### Tool Ownership Matrix

| Tool | Primary User | Can Also Use |
|------|-------------|--------------|
| DiceRoller | Keeper | Narrator (narrative rolls) |
| WorldState | Narrator | All (read), Narrator (write) |
| CharacterSheet | Keeper | All (read) |
| CombatManager | Keeper | Narrator (narration) |

---

## 8. XP Practice: Sustainable Pace

### Token Budget Per Session

Sustainable API costs = sustainable development:

```python
class TokenBudget:
    """Enforce sustainable token usage per adventure."""

    MAX_TOKENS_PER_SESSION = 50_000  # ~$0.50 per adventure

    ALLOCATION = {
        "character_creation": 5_000,   # 10%
        "quest_generation": 5_000,     # 10%
        "narrative_scenes": 25_000,    # 50%
        "combat": 10_000,              # 20%
        "epilogue": 5_000,             # 10%
    }

    def check_budget(self, phase: str, tokens_used: int) -> bool:
        return tokens_used <= self.ALLOCATION[phase]
```

### Model Selection Strategy

| Task | Model | Why |
|------|-------|-----|
| Narrative generation | Claude Sonnet | Quality matters |
| Stat calculations | Claude Haiku | Fast, cheap, deterministic |
| Validation | Claude Haiku | Binary decisions |
| Epilogue | Claude Sonnet | Emotional resonance |

---

## 9. XP Practice: On-Site Customer (Feedback Loops)

### Feedback Integration Points

```
User Input ──────────────────────────────────────────────────────┐
     │                                                           │
     ▼                                                           │
Character Sheet ──[ACCEPT/MODIFY]──────────────────────────────┐ │
     │                                                         │ │
     ▼                                                         │ │
Quest Hook ──[BEGIN ADVENTURE]─────────────────────────────────┼─┤
     │                                                         │ │
     ▼                                                         │ │
Scene ──[CHOICE 1/2/3/CUSTOM]──────────────────────────────────┼─┤
     │                                                         │ │
     ▼                                                         │ │
Combat ──[ACTION/FLEE/TALK]────────────────────────────────────┼─┤
     │                                                         │ │
     ▼                                                         │ │
Epilogue ──[EXPORT/NEW ADVENTURE]──────────────────────────────┘ │
                                                                  │
                    [Every interaction is feedback] ◄─────────────┘
```

### Agent Transparency

Users see agent thinking (XP: Communication):

```html
<div class="agent-annotation jester">
    <span class="agent-icon">🎲</span>
    <span class="agent-name">Jester</span>
    <span class="agent-thought">
        "Ooh, a paladin with a dark secret?
        This is going to be FUN. :)"
    </span>
</div>
```

---

## 10. XP Practice: Coding Standards

### Python Standards

```python
# ruff.toml
[lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
]

[format]
quote-style = "double"
indent-style = "space"
```

### Naming Conventions

```python
# Agents: Personality in name
barkeep_mordecai = Agent(...)
chaos_goblin = Agent(...)

# Tools: Verb + noun
roll_dice(...)
update_world_state(...)
validate_action(...)

# Schemas: Noun, singular
class CharacterSheet(BaseModel): ...
class QuestHook(BaseModel): ...
class CombatAction(BaseModel): ...
```

### Docstring Standard

```python
def generate_quest_hook(character: CharacterSheet) -> QuestHook:
    """Generate personalized quest based on character backstory.

    XP: Simple Design - hooks into ONE backstory element, not all.

    Args:
        character: The player's character sheet with backstory.

    Returns:
        QuestHook with personalized connection to character.

    Example:
        >>> character = CharacterSheet(backstory="Lost my family to orcs")
        >>> hook = generate_quest_hook(character)
        >>> "orc" in hook.description.lower()
        True
    """
```

---

## 11. XP Practice: Refactoring

### Refactoring Triggers

Refactor when you see:

| Smell | Refactoring |
|-------|-------------|
| Agent doing too much | Extract responsibilities to new agent |
| Duplicate tool logic | Extract shared utility |
| Complex conditionals | Replace with state machine |
| Long method | Extract smaller methods |
| Hardcoded values | Extract to configuration |

### Safe Refactoring Checklist

```markdown
□ All tests pass before refactoring
□ Make ONE structural change
□ Run tests
□ Commit
□ Repeat
```

### Example: Extract Combat Manager

**Before (in Narrator agent):**
```python
class Narrator:
    def handle_combat(self, action, enemies, character):
        initiative = self.roll_initiative(enemies, character)
        while enemies_alive(enemies) and character.hp > 0:
            for combatant in initiative:
                # 50 lines of combat logic
                ...
```

**After (extracted):**
```python
class CombatManager:
    """Single Responsibility: Combat resolution."""

    def __init__(self, dice_roller, chronicler):
        self.dice = dice_roller
        self.chronicler = chronicler

    def run_combat(self, combatants: list[Combatant]) -> CombatResult:
        initiative = self._roll_initiative(combatants)
        return self._combat_loop(initiative)

class DungeonMaster:
    def handle_combat(self, action, enemies, character):
        result = self.combat_manager.run_combat([character] + enemies)
        return self.narrate_combat_result(result)
```

---

## 12. Project Structure

```
pocket-portals/
├── src/pocket_portals/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # HTTP endpoints
│   │   └── streaming.py        # SSE handlers
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── innkeeper.py          # Quest introduction
│   │   ├── narrator.py               # Narrative generation
│   │   ├── chronicler.py       # Mechanics validation
│   │   └── jester.py     # Complications
│   │
│   ├── crews/
│   │   ├── __init__.py
│   │   ├── character_crew.py   # Parallel character analysis
│   │   └── adventure_crew.py   # Sequential adventure flow
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── dice.py             # Dice rolling
│   │   ├── character.py        # Sheet management
│   │   ├── world_state.py      # State tracking
│   │   └── combat.py           # Combat mechanics
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── character.py        # CharacterSheet model
│   │   ├── quest.py            # QuestHook model
│   │   ├── scene.py            # Scene, Choice models
│   │   └── combat.py           # CombatAction, Result models
│   │
│   ├── config/
│   │   ├── agents.yaml         # Agent definitions
│   │   └── tasks.yaml          # Task definitions
│   │
│   └── templates/
│       ├── base.html           # Layout
│       ├── tavern.html         # Entry screen
│       ├── character.html      # Character review
│       ├── adventure.html      # Main gameplay
│       └── components/
│           ├── agent_annotation.html
│           ├── choice_buttons.html
│           └── dice_roll.html
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures
│   ├── unit/                   # XP: Fast, many
│   │   ├── test_dice.py
│   │   ├── test_character.py
│   │   └── test_world_state.py
│   ├── integration/            # XP: Medium, some
│   │   ├── test_agents.py
│   │   └── test_crews.py
│   ├── e2e/                    # XP: Slow, few
│   │   └── test_adventure.py
│   └── bdd/                    # BDD: Living documentation
│       ├── features/
│       │   ├── character_creation.feature
│       │   ├── quest_generation.feature
│       │   ├── gameplay_loop.feature
│       │   ├── combat.feature
│       │   └── epilogue.feature
│       ├── steps/
│       │   ├── character_steps.py
│       │   ├── quest_steps.py
│       │   ├── gameplay_steps.py
│       │   ├── combat_steps.py
│       │   └── epilogue_steps.py
│       ├── environment.py
│       └── behave.ini
│
├── docs/
│   ├── architecture.md         # This file
│   └── adr/                    # Architecture Decision Records
│       └── 001-htmx-over-react.md
│
├── pyproject.toml
├── Makefile
├── Dockerfile
├── fly.toml
└── README.md
```

---

## 13. Architecture Decision Records

### ADR-001: HTMX Over React

**Status:** Accepted

**Context:** Need interactive UI for streaming narrative and choices.

**Decision:** Use HTMX + Jinja2 instead of React/Vue.

**Consequences:**
- ✅ Simpler stack (XP: Simplicity)
- ✅ No build step for frontend
- ✅ SSE streaming works naturally
- ✅ Progressive enhancement
- ⚠️ Less ecosystem for complex UI
- ⚠️ Team must learn HTMX patterns

### ADR-002: In-Memory Session State

**Status:** Accepted

**Context:** Need to track adventure state per user session.

**Decision:** Use Python dict per session, no external database for MVP.

**Consequences:**
- ✅ Zero infrastructure (XP: Simplicity)
- ✅ Fast reads/writes
- ⚠️ State lost on server restart
- ⚠️ No horizontal scaling (acceptable for MVP)

### ADR-003: Model Tiering

**Status:** Accepted

**Context:** Balance quality vs. cost for LLM calls.

**Decision:** Sonnet for narrative, Haiku for mechanics.

**Consequences:**
- ✅ ~60% cost reduction
- ✅ Faster mechanical operations
- ✅ Quality maintained where it matters
- ⚠️ Two models to maintain

---

## 14. The Tavern Crew: Agent Personalities

### Innkeeper Theron

**Role:** Quest introduction, NPC broker, session bookends

**Personality:** Ancient, knowing, cryptic. Speaks in implications.

**Responsibilities:**
- Welcome adventurers to the tavern
- Sense character backstory hooks
- Introduce quest-giver NPCs
- Deliver epilogue reflections

### Narrator

**Role:** Narrative generation, world state, scene description

**Personality:** Dramatic, evocative, adaptive to player tone.

**Responsibilities:**
- Generate immersive scene descriptions
- Maintain world state consistency
- Adapt narrative tone to player choices
- Orchestrate story pacing

### Keeper

**Role:** Scorekeeper for dice, health, and game state

**Personality:** Quick, clear, stays out of the way.

**Responsibilities:**
- Handle dice rolls when needed
- Track health and resources
- Report results without slowing the story
- Keep the game honest

### Jester

**Role:** Complications, foreshadowing, meta-commentary

**Personality:** Gleefully chaotic, fourth-wall adjacent, uses :) unironically.

**Responsibilities:**
- Add unexpected complications
- Drop foreshadowing hints
- Provide meta-commentary annotations
- Keep adventures from becoming predictable

---

## 15. Success Metrics (XP: Feedback)

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >80% | pytest-cov |
| Build time | <10 min | CI pipeline |
| Response latency | <3s narrative, <500ms dice | APM |
| Token budget adherence | 100% sessions under limit | Logging |

### User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first scene | <60s | Client timing |
| Adventure completion rate | >70% | Session tracking |
| Return rate | >30% within 7 days | Analytics |

---

## 16. Getting Started

```bash
# Clone and setup
git clone <repo>
cd pocket-portals
uv sync

# Run tests (XP: Test First)
make test

# Start development server
make dev

# Open browser
open http://localhost:8000
```

---

**XP Mantra:** "Do the simplest thing that could possibly work, then iterate based on feedback."

---

## Related Documents

- **[product.md](product.md)** - Product requirements and user stories
- **[creative-writing.md](creative-writing.md)** - Agent voices and narrative style
- **[conversation-engine.md](conversation-engine.md)** - Turn execution and state management
- **[crewai.md](crewai.md)** - CrewAI patterns and templates
