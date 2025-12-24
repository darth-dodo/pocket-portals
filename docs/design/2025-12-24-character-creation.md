# Character Creation System Design Document

**Feature**: Character creation and personalization system
**Author**: System Architect
**Date**: 2025-12-24
**Status**: Proposed
**Related Requirements**: FR-01, FR-02, FR-03

---

## Table of Contents

1. [Overview](#1-overview)
2. [User Flow](#2-user-flow)
3. [Character Data Model](#3-character-data-model)
4. [Agent Design](#4-agent-design)
5. [API Design](#5-api-design)
6. [Implementation Plan](#6-implementation-plan)
7. [Testing Strategy](#7-testing-strategy)
8. [Future Enhancements](#8-future-enhancements)
9. [Risk Assessment](#9-risk-assessment)
10. [Success Criteria](#10-success-criteria)

---

## 1. Overview

### 1.1 Problem Statement

**Current State**: Users can optionally provide a character description via query parameter on `/start`, but there is no structured character creation flow, no character sheet generation, and no ability to review/modify generated characters.

**Desired State**: Users engage in a conversational character creation process with InnkeeperAgent, receive a complete D&D character sheet with stats and backstory, and can accept or request modifications before beginning their adventure.

### 1.2 Requirements

From `docs/product.md` Section 6.1:

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Accept free-form character description (text input) | P0 - Must Have |
| FR-02 | Generate character sheet (stats, equipment, backstory) | P0 - Must Have |
| FR-03 | Allow user to accept or modify generated character | P0 - Must Have |

### 1.3 Design Principles

Following XP and repository patterns:
- **Simple Design**: Use existing agent patterns (InnkeeperAgent)
- **YAGNI**: Implement only essential character creation features
- **TDD**: Write tests first, following established patterns
- **Incremental**: Build on existing session management and agent infrastructure

---

## 2. User Flow

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. START: User lands on welcome screen                  │
│    - Sees "Begin Adventure" button                      │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. CHARACTER CREATION: Multi-turn conversation          │
│    - InnkeeperAgent asks character questions            │
│    - User provides free-form responses                  │
│    - 3-5 turns of back-and-forth                        │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. SHEET GENERATION: Generate character sheet           │
│    - InnkeeperAgent processes collected info            │
│    - Generate stats (STR, DEX, CON, INT, WIS, CHA)      │
│    - Select starting equipment                          │
│    - Create backstory snippet                           │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. REVIEW: Display character sheet to user              │
│    - Show all stats, equipment, backstory               │
│    - Choices: "Accept", "Modify [aspect]", "Start over" │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. ADVENTURE START: Begin quest with personalized hook  │
│    - InnkeeperAgent introduces quest based on character │
│    - Transition to normal conversation flow             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Detailed Character Creation Flow

**Phase 1: Introduction (Turn 1)**
- InnkeeperAgent: "You push open the tavern door. I'm Theron. You here for work or trouble?"
- User provides initial character concept (e.g., "I'm a dwarven blacksmith seeking adventure")

**Phase 2: Character Interview (Turns 2-4)**
- Innkeeper asks targeted questions based on user input:
  - "What brought you to adventuring?" (backstory)
  - "What are you good at? What do you struggle with?" (stats/skills)
  - "What's in your pack?" (equipment)
- User provides free-form answers
- Innkeeper acknowledges and asks follow-up questions

**Phase 3: Sheet Generation (System)**
- Parse all conversation turns
- Generate character sheet using structured format
- Store in GameState

**Phase 4: Review & Confirmation (Turn 5+)**
- Display character sheet
- Offer modification choices:
  - "Accept character and begin adventure"
  - "Adjust stats" (triggers re-generation with constraints)
  - "Change backstory" (edit specific field)
  - "Start character creation over"
- Loop until user accepts

**Phase 5: Quest Introduction (Final Turn)**
- Innkeeper presents personalized quest hook
- Transition to adventure (normal conversation flow with NarratorAgent)

---

## 3. Character Data Model

### 3.1 CharacterSheet Model

```python
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class CharacterClass(str, Enum):
    """D&D character classes."""
    FIGHTER = "fighter"
    ROGUE = "rogue"
    WIZARD = "wizard"
    CLERIC = "cleric"
    RANGER = "ranger"
    BARBARIAN = "barbarian"

class CharacterRace(str, Enum):
    """D&D character races."""
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"
    ORC = "orc"
    TIEFLING = "tiefling"

class CharacterStats(BaseModel):
    """Character ability scores (3-18 range)."""
    strength: int = Field(ge=3, le=18, default=10)
    dexterity: int = Field(ge=3, le=18, default=10)
    constitution: int = Field(ge=3, le=18, default=10)
    intelligence: int = Field(ge=3, le=18, default=10)
    wisdom: int = Field(ge=3, le=18, default=10)
    charisma: int = Field(ge=3, le=18, default=10)

    @property
    def total(self) -> int:
        """Calculate total stat points (standard array = 72)."""
        return (
            self.strength + self.dexterity + self.constitution +
            self.intelligence + self.wisdom + self.charisma
        )

class CharacterSheet(BaseModel):
    """Complete D&D character sheet."""

    # Identity
    name: str = Field(min_length=1, max_length=50)
    race: CharacterRace
    character_class: CharacterClass
    level: int = Field(ge=1, le=20, default=1)

    # Stats
    stats: CharacterStats = Field(default_factory=CharacterStats)

    # Vitals (derived from stats)
    health_max: int = Field(ge=1, default=20)
    health_current: int = Field(ge=0, default=20)

    # Equipment
    equipment: list[str] = Field(
        default_factory=lambda: ["Basic clothes", "10 gold pieces"]
    )

    # Narrative
    backstory: str = Field(
        max_length=500,
        default="An adventurer seeking fortune and glory."
    )

    # Traits (optional flavor)
    traits: list[str] = Field(default_factory=list)

    @field_validator("health_current")
    @classmethod
    def health_current_valid(cls, v: int, info) -> int:
        """Validate that current health does not exceed max health."""
        if "health_max" in info.data and v > info.data["health_max"]:
            raise ValueError(
                f"health_current ({v}) cannot exceed health_max ({info.data['health_max']})"
            )
        return v

    def to_display_text(self) -> str:
        """Format character sheet for display to user."""
        return f"""
CHARACTER SHEET
===============

Name: {self.name}
Race: {self.race.value.title()}
Class: {self.character_class.value.title()}
Level: {self.level}

ABILITY SCORES
--------------
Strength:     {self.stats.strength}
Dexterity:    {self.stats.dexterity}
Constitution: {self.stats.constitution}
Intelligence: {self.stats.intelligence}
Wisdom:       {self.stats.wisdom}
Charisma:     {self.stats.charisma}

VITALS
------
Health: {self.health_current}/{self.health_max}

EQUIPMENT
---------
{chr(10).join(f"- {item}" for item in self.equipment)}

BACKSTORY
---------
{self.backstory}

TRAITS
------
{chr(10).join(f"- {trait}" for trait in self.traits) if self.traits else "None"}
        """.strip()
```

### 3.2 GameState Integration

Extend existing `GameState` model in `src/state/models.py`:

```python
class GamePhase(str, Enum):
    """Enumeration of game phases for routing decisions."""
    CHARACTER_CREATION = "character_creation"  # NEW
    EXPLORATION = "exploration"
    COMBAT = "combat"
    DIALOGUE = "dialogue"

class GameState(BaseModel):
    """Minimal game state for solo D&D narrative adventure."""

    session_id: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    current_choices: list[str] = Field(default_factory=list)

    # Character
    character_description: str = ""  # Existing (free-form)
    character_sheet: CharacterSheet | None = None  # NEW (structured)

    # Health (keep for backwards compatibility, derive from character_sheet)
    health_current: int = 20
    health_max: int = 20

    # Phase
    phase: GamePhase = GamePhase.CHARACTER_CREATION  # NEW default
    recent_agents: list[str] = Field(default_factory=list)
    turns_since_jester: int = 0

    @property
    def has_character(self) -> bool:
        """Check if character sheet is complete."""
        return self.character_sheet is not None
```

---

## 4. Agent Design

### 4.1 Agent Responsibilities

**InnkeeperAgent** (Primary):
- Conducts character interview (3-5 turns)
- Asks targeted questions to elicit character details
- Generates structured character sheet from conversation
- Presents quest hook tailored to character

**KeeperAgent** (Supporting):
- Validates stat totals (standard array = 72 points)
- Ensures stats within valid ranges (3-18)
- Handles stat modification requests

**NarratorAgent** (Handoff):
- Takes over after character creation complete
- Receives character context for personalized narrative

### 4.2 New Agent Tasks

Add to `src/config/tasks.yaml`:

```yaml
interview_character:
  description: |
    You are Innkeeper Theron conducting a character interview for a new adventurer.

    Current turn: {turn_number}/5
    Previous conversation: {context}

    Based on what you've learned so far, ask ONE focused question to understand:
    - Turn 1: Who they are (name, race, class)
    - Turn 2: Their background and what brought them here
    - Turn 3: Their strengths and weaknesses (for stats)
    - Turn 4: What gear they're carrying
    - Turn 5: Confirm and prepare to generate character sheet

    Keep your questions short, direct, and in Theron's weary voice.
    Reference their previous answers to show you're listening.
  expected_output: |
    A single focused question (1-2 sentences) in Theron's voice, advancing
    the character creation process.
  agent: innkeeper_theron

generate_character_sheet:
  description: |
    Based on this character interview conversation:

    {interview_transcript}

    Generate a complete D&D character sheet in JSON format with the following structure:
    {{
      "name": "character name",
      "race": "human|elf|dwarf|halfling|orc|tiefling",
      "character_class": "fighter|rogue|wizard|cleric|ranger|barbarian",
      "level": 1,
      "stats": {{
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
      }},
      "health_max": 20,
      "equipment": ["item1", "item2", ...],
      "backstory": "brief backstory based on interview",
      "traits": ["trait1", "trait2"]
    }}

    Guidelines:
    - Stats should total 72 (standard array)
    - Stats range: 3-18
    - Assign higher stats to abilities matching their described strengths
    - Equipment should match their class and background
    - Backstory should be 2-3 sentences summarizing their interview
    - Include 2-3 personality traits mentioned in conversation

    Return ONLY valid JSON, no additional text.
  expected_output: "Valid JSON matching CharacterSheet schema"
  agent: innkeeper_theron

present_character_sheet:
  description: |
    You've generated this character sheet:

    {character_sheet_text}

    Present it to the adventurer in Theron's voice. Keep it brief.
    Then offer them three choices:
    1. Accept this character and begin adventure
    2. Adjust stats or equipment
    3. Start character creation over

    Format:
    [Brief Theron comment about the character]

    [Character sheet display]

    CHOICES:
    1. Accept character and begin
    2. Adjust stats
    3. Start over
  expected_output: "Character sheet presentation with 3 choices"
  agent: innkeeper_theron
```

### 4.3 Character Sheet Generation Method

Add to `InnkeeperAgent` class:

```python
def generate_character_sheet(
    self, interview_transcript: str, context: str = ""
) -> CharacterSheet:
    """Generate character sheet from interview conversation.

    Args:
        interview_transcript: Full conversation history from character creation
        context: Optional additional context

    Returns:
        Validated CharacterSheet instance

    Raises:
        ValueError: If LLM returns invalid JSON or validation fails
    """
    task_config = load_task_config("generate_character_sheet")

    description = task_config.description.format(
        interview_transcript=interview_transcript
    )

    if context:
        description = f"{context}\n\n{description}"

    task = Task(
        description=description,
        expected_output=task_config.expected_output,
        agent=self.agent,
    )

    result = task.execute_sync()
    result_str = str(result)

    # Parse JSON response
    try:
        # Extract JSON from response (LLM might add extra text)
        import json
        import re

        # Find JSON object in response
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in LLM response")

        json_str = json_match.group(0)
        character_data = json.loads(json_str)

        # Validate and create CharacterSheet
        character_sheet = CharacterSheet(**character_data)

        return character_sheet

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Fallback: create default character
        raise ValueError(f"Failed to parse character sheet: {e}")
```

---

## 5. API Design

### 5.1 New Endpoints

#### 5.1.1 POST /character/create

Start character creation process.

**Request**:
```python
class CharacterCreateRequest(BaseModel):
    """Request to start character creation."""
    initial_concept: str | None = Field(
        default=None,
        description="Optional initial character concept"
    )
    session_id: str | None = None
```

**Response**:
```python
class CharacterCreateResponse(BaseModel):
    """Response from character creation start."""
    narrative: str  # Innkeeper's opening question
    session_id: str
    choices: list[str] = Field(
        default_factory=lambda: [
            "Answer the question",
            "Provide different information",
            "Skip character creation"
        ]
    )
    turn: int = 1  # Character creation turn (1-5)
```

**Example**:
```bash
POST /character/create
{
  "initial_concept": "A dwarven blacksmith"
}

Response:
{
  "narrative": "You push through the door. I'm Theron. Blacksmith, you said? What's your name, and what brings a smith to adventuring?",
  "session_id": "abc-123",
  "choices": [
    "Answer the question",
    "Provide different information",
    "Skip character creation"
  ],
  "turn": 1
}
```

#### 5.1.2 POST /character/respond

Continue character creation conversation.

**Request**:
```python
class CharacterRespondRequest(BaseModel):
    """Response during character creation."""
    action: str  # User's answer to Innkeeper's question
    session_id: str
```

**Response**:
- If turn < 5: Returns next question (same as CharacterCreateResponse)
- If turn == 5: Generates and presents character sheet

```python
class CharacterSheetResponse(BaseModel):
    """Response with generated character sheet."""
    narrative: str  # Innkeeper's presentation
    character_sheet: dict  # CharacterSheet.dict()
    character_sheet_display: str  # Formatted for display
    session_id: str
    choices: list[str] = Field(
        default_factory=lambda: [
            "Accept character and begin",
            "Adjust stats",
            "Start over"
        ]
    )
```

#### 5.1.3 POST /character/accept

Accept character sheet and begin adventure.

**Request**:
```python
class CharacterAcceptRequest(BaseModel):
    """Accept character and begin adventure."""
    session_id: str
    modifications: dict | None = Field(
        default=None,
        description="Optional stat/equipment modifications"
    )
```

**Response**:
```python
class QuestStartResponse(BaseModel):
    """Response when adventure begins."""
    narrative: str  # Innkeeper's quest introduction
    session_id: str
    choices: list[str]  # Quest-specific choices
    phase: str = "exploration"  # GamePhase
```

### 5.2 Modified Endpoints

#### /start

Update to check for existing character:

```python
@app.get("/start", response_model=NarrativeResponse)
async def start_adventure(
    shuffle: bool = Query(default=False),
    character: str = Query(default=""),
    skip_character_creation: bool = Query(
        default=False,
        description="Skip character creation and use default character"
    ),
) -> NarrativeResponse:
    """Start a new adventure.

    If skip_character_creation=False (default), redirects to character creation.
    If skip_character_creation=True, creates default character and begins quest.
    """
    state = get_session(None)

    if not skip_character_creation:
        # Redirect to character creation
        # (Frontend should call /character/create instead)
        return NarrativeResponse(
            narrative="Please use /character/create to begin character creation.",
            session_id=state.session_id,
            choices=["Begin character creation"]
        )

    # Create default character
    default_character = CharacterSheet(
        name="Adventurer",
        race=CharacterRace.HUMAN,
        character_class=CharacterClass.FIGHTER,
        stats=CharacterStats(),
    )
    session_manager.set_character_sheet(state.session_id, default_character)
    session_manager.set_phase(state.session_id, GamePhase.EXPLORATION)

    # Continue with existing starter choices logic...
```

---

## 6. Implementation Plan

### 6.1 Implementation Order (TDD)

Following the repository's TDD pattern:

**Step 1: Character Models (Day 1)**
1. Add `CharacterSheet`, `CharacterStats`, `CharacterClass`, `CharacterRace` models
2. Write tests for model validation (stats range, health validation, etc.)
3. Extend `GameState` with `character_sheet` field
4. Write tests for GameState integration

**Files**:
- `src/state/models.py` (extend)
- `tests/test_models.py` (extend)

**Step 2: Session Manager Character Methods (Day 1)**
1. Add `set_character_sheet()`, `get_character_sheet()` to SessionManager
2. Add `set_phase()`, `get_phase()` for phase management
3. Write tests for character storage/retrieval

**Files**:
- `src/state/session.py` (extend)
- `tests/test_session_manager.py` (extend)

**Step 3: InnkeeperAgent Character Methods (Day 2)**
1. Add YAML task configs (interview_character, generate_character_sheet, present_character_sheet)
2. Implement `interview_character()` method
3. Implement `generate_character_sheet()` method with JSON parsing
4. Write tests with mocked Task.execute_sync()

**Files**:
- `src/config/tasks.yaml` (extend)
- `src/agents/innkeeper.py` (extend)
- `tests/test_innkeeper.py` (extend)

**Step 4: API Endpoints (Day 2-3)**
1. Implement `/character/create` endpoint
2. Implement `/character/respond` endpoint
3. Implement `/character/accept` endpoint
4. Modify `/start` to redirect to character creation
5. Write integration tests

**Files**:
- `src/api/main.py` (extend)
- `tests/test_api.py` (extend)

**Step 5: Character Creation Flow Orchestration (Day 3)**
1. Implement turn counter logic (1-5)
2. Implement transition from interview → sheet generation → review
3. Add character sheet validation on accept
4. Write end-to-end tests

**Files**:
- `src/api/main.py` (extend)
- `tests/test_api.py` (extend)

**Step 6: Integration with Quest System (Day 4)**
1. Update `/start` and existing quest flow to use character_sheet
2. Pass character context to NarratorAgent
3. Test complete flow: create → review → accept → quest → adventure

**Files**:
- `src/api/main.py` (extend)
- `src/agents/narrator.py` (potentially extend)
- `tests/test_api.py` (extend)

### 6.2 File Changes Summary

```
src/
├── state/
│   └── models.py              # ADD: CharacterSheet, CharacterStats, Enums
│                              # MODIFY: GameState (add character_sheet, phase)
├── agents/
│   └── innkeeper.py          # ADD: generate_character_sheet(), interview_character()
├── config/
│   └── tasks.yaml            # ADD: 3 new tasks
├── api/
│   └── main.py               # ADD: 3 new endpoints
│                              # MODIFY: /start
tests/
├── test_models.py            # ADD: CharacterSheet tests
├── test_session_manager.py   # ADD: character_sheet storage tests
├── test_innkeeper.py         # ADD: character generation tests
└── test_api.py               # ADD: character creation flow tests
```

### 6.3 Dependencies

**New Dependencies**: None (uses existing CrewAI, Pydantic, FastAPI)

**Configuration**:
- Innkeeper LLM temperature: 0.6 (existing)
- Innkeeper max_tokens: 512 → increase to 1024 for character sheet JSON
- New YAML tasks use existing task loading patterns

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Test Models** (`tests/test_models.py`):
```python
class TestCharacterSheet:
    def test_character_stats_validation(self):
        """Test stats must be in 3-18 range."""
        with pytest.raises(ValueError):
            CharacterStats(strength=25)  # Too high
        with pytest.raises(ValueError):
            CharacterStats(dexterity=2)  # Too low

    def test_health_validation(self):
        """Test current health cannot exceed max health."""
        with pytest.raises(ValueError):
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                health_current=30,
                health_max=20
            )

    def test_character_sheet_display_format(self):
        """Test character sheet formats correctly for display."""
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )
        display = sheet.to_display_text()
        assert "Name: Thorin" in display
        assert "Race: Dwarf" in display
        assert "Class: Fighter" in display
```

**Test InnkeeperAgent** (`tests/test_innkeeper.py`):
```python
class TestInnkeeperCharacterCreation:
    @patch("src.agents.innkeeper.Task")
    def test_generate_character_sheet_returns_valid_sheet(
        self, mock_task: MagicMock
    ) -> None:
        """Test character sheet generation from interview."""
        # Mock JSON response
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = '''
        {
          "name": "Thorin",
          "race": "dwarf",
          "character_class": "fighter",
          "level": 1,
          "stats": {
            "strength": 16,
            "dexterity": 10,
            "constitution": 14,
            "intelligence": 8,
            "wisdom": 12,
            "charisma": 12
          },
          "health_max": 20,
          "equipment": ["Warhammer", "Chain mail"],
          "backstory": "A blacksmith turned adventurer.",
          "traits": ["Stubborn", "Loyal"]
        }
        '''
        mock_task.return_value = mock_task_instance

        innkeeper = InnkeeperAgent()
        transcript = "User described a dwarven fighter..."

        sheet = innkeeper.generate_character_sheet(transcript)

        assert isinstance(sheet, CharacterSheet)
        assert sheet.name == "Thorin"
        assert sheet.race == CharacterRace.DWARF
        assert sheet.stats.strength == 16

    @patch("src.agents.innkeeper.Task")
    def test_generate_character_sheet_handles_invalid_json(
        self, mock_task: MagicMock
    ) -> None:
        """Test graceful handling of invalid LLM response."""
        mock_task_instance = MagicMock()
        mock_task_instance.execute_sync.return_value = "Not valid JSON"
        mock_task.return_value = mock_task_instance

        innkeeper = InnkeeperAgent()

        with pytest.raises(ValueError, match="Failed to parse"):
            innkeeper.generate_character_sheet("transcript")
```

### 7.2 Integration Tests

**Test API Flow** (`tests/test_api.py`):
```python
class TestCharacterCreationFlow:
    def test_complete_character_creation_flow(self, client):
        """Test full character creation from start to quest."""

        # Step 1: Start character creation
        response = client.post(
            "/character/create",
            json={"initial_concept": "A dwarven blacksmith"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "narrative" in data
        assert data["turn"] == 1
        session_id = data["session_id"]

        # Step 2-4: Answer interview questions
        for turn in range(2, 5):
            response = client.post(
                "/character/respond",
                json={
                    "action": f"Answer for turn {turn}",
                    "session_id": session_id
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["turn"] == turn

        # Step 5: Receive character sheet
        response = client.post(
            "/character/respond",
            json={
                "action": "Final answer",
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "character_sheet" in data
        assert "character_sheet_display" in data

        # Step 6: Accept character
        response = client.post(
            "/character/accept",
            json={"session_id": session_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == "exploration"
        assert "quest" in data["narrative"].lower()

    def test_character_modification_flow(self, client):
        """Test modifying character stats during review."""
        # Create character (abbreviated)
        session_id = "test-session"

        # Accept with modifications
        response = client.post(
            "/character/accept",
            json={
                "session_id": session_id,
                "modifications": {
                    "stats": {"strength": 16, "dexterity": 14}
                }
            }
        )
        assert response.status_code == 200
```

### 7.3 Test Coverage Targets

- Character models: 100% (Pydantic validation)
- InnkeeperAgent character methods: 90%+ (with mocked LLM calls)
- API endpoints: 85%+ (integration tests)
- Overall project coverage: Maintain 73%+ (current level)

---

## 8. Future Enhancements

**Not implementing now (YAGNI)**:

1. **Multiple Character Classes**: Only implement 6 core classes for MVP
2. **Multiclass Support**: Single class per character for MVP
3. **Spell Selection**: Wizards/Clerics start with basic spell list
4. **Skill Proficiencies**: Simplified to class defaults
5. **Character Portraits**: Text-only for MVP
6. **Character Templates**: No quick-start templates
7. **Character Export**: No PDF/JSON export initially
8. **Character Persistence**: Characters tied to session only (no accounts)

**When to implement**:
- Spell selection: When wizard/cleric players request more control
- Templates: When >30% of users skip character creation
- Export: When users request shareable character sheets
- Persistence: When multi-session adventures are implemented

---

## 9. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM returns invalid JSON | High | Medium | Robust parsing with fallbacks, retry logic |
| Users want to skip character creation | Medium | High | Provide skip option with default character |
| Interview too long (5+ turns) | Medium | Low | Limit to 5 turns, allow partial info |
| Stat generation feels unfair | Low | Medium | Show stat calculation logic, allow re-roll |
| Character sheet too complex | Medium | Low | Start simple, add complexity based on feedback |
| Integration breaks existing flow | High | Low | Comprehensive integration tests, feature flag |

**Mitigation Strategies**:

1. **JSON Parsing Resilience**:
   ```python
   def parse_character_json(response: str) -> CharacterSheet:
       try:
           # Primary: extract JSON from LLM response
           return CharacterSheet(**json.loads(extract_json(response)))
       except (JSONDecodeError, ValidationError):
           # Fallback 1: retry with clearer prompt
           # Fallback 2: create default character
           # Fallback 3: ask user to try again
   ```

2. **Skip Option**:
   - Add `skip_character_creation=true` query param to `/start`
   - Create sensible default character
   - Log skip rate for future analysis

3. **Feature Flag**:
   - Environment variable: `ENABLE_CHARACTER_CREATION=true`
   - Gradual rollout capability

---

## 10. Success Criteria

**Functional Requirements**:
- [ ] Users can describe character in free-form text (FR-01)
- [ ] System generates complete character sheet with all stats (FR-02)
- [ ] Users can review and modify character before accepting (FR-03)
- [ ] Character context flows into quest introduction
- [ ] All existing tests continue to pass

**Quality Requirements**:
- [ ] Character sheet validation prevents invalid states
- [ ] Test coverage remains ≥70%
- [ ] API response time <3s for character generation
- [ ] Character interview completes in ≤5 turns
- [ ] JSON parsing success rate ≥95%

**User Experience**:
- [ ] Interview feels conversational, not like a form
- [ ] Generated stats align with described character
- [ ] Equipment makes sense for class/backstory
- [ ] Quest hook references character background
- [ ] Skip option works for users who want quick start

**Technical**:
- [ ] No new external dependencies
- [ ] Follows existing agent/task patterns
- [ ] Proper error handling and fallbacks
- [ ] Clean separation of concerns (models, agents, API)

---

## Appendix A: Example Interactions

### A.1 Full Character Creation Example

**Turn 1: Initial Concept**
```
POST /character/create
{
  "initial_concept": "A dwarven blacksmith seeking redemption"
}

Response:
{
  "narrative": "You push through the door, soot still on your hands. I'm Theron. Blacksmith, you said? What's your name, and what needs redeeming?",
  "session_id": "abc-123",
  "choices": ["Answer the question", "Provide different information", "Skip"],
  "turn": 1
}
```

**Turn 2: Backstory**
```
POST /character/respond
{
  "session_id": "abc-123",
  "action": "I'm Thorin Ironforge. I forged a cursed blade that killed my brother. I need to make things right."
}

Response:
{
  "narrative": "Thorin. That's a heavy burden. What are you good at, besides the forge? Where do you struggle?",
  "session_id": "abc-123",
  "choices": ["Answer", "Ask a question", "Continue"],
  "turn": 2
}
```

**Turn 3: Strengths/Weaknesses**
```
POST /character/respond
{
  "session_id": "abc-123",
  "action": "I'm strong and resilient, but not much for books or smooth talking."
}

Response:
{
  "narrative": "Strong and stubborn. I've seen it before. What's in your pack?",
  "session_id": "abc-123",
  "choices": ["List equipment", "Default gear", "Continue"],
  "turn": 3
}
```

**Turn 4: Equipment**
```
POST /character/respond
{
  "session_id": "abc-123",
  "action": "My smithing hammer, some chain mail I made, and fifty gold I saved."
}

Response:
{
  "narrative": "Practical. Let me see what we're working with here.",
  "session_id": "abc-123",
  "choices": ["Wait", "Continue"],
  "turn": 4
}
```

**Turn 5: Character Sheet Presentation**
```
POST /character/respond
{
  "session_id": "abc-123",
  "action": "Continue"
}

Response:
{
  "narrative": "Here's what I'm seeing, Thorin. Looks right to me.",
  "character_sheet": {
    "name": "Thorin Ironforge",
    "race": "dwarf",
    "character_class": "fighter",
    "level": 1,
    "stats": {
      "strength": 16,
      "dexterity": 10,
      "constitution": 14,
      "intelligence": 8,
      "wisdom": 12,
      "charisma": 12
    },
    "health_max": 20,
    "equipment": ["Smithing hammer (warhammer)", "Chain mail", "50 gold pieces"],
    "backstory": "Thorin Ironforge, a dwarven blacksmith haunted by a cursed blade he forged that claimed his brother's life. He seeks redemption through adventure.",
    "traits": ["Strong", "Resilient", "Stubborn", "Not book-smart"]
  },
  "character_sheet_display": "CHARACTER SHEET\n===============\n...",
  "session_id": "abc-123",
  "choices": [
    "Accept character and begin",
    "Adjust stats",
    "Start over"
  ]
}
```

**Turn 6: Accept & Begin**
```
POST /character/accept
{
  "session_id": "abc-123"
}

Response:
{
  "narrative": "Right then, Thorin. Word is the old smith north of here vanished three nights back. Left his forge running. Locals say they hear hammering at night, but nobody's working the bellows. Might be nothing. Might be something a blacksmith would understand. Pays twenty gold if you sort it.",
  "session_id": "abc-123",
  "choices": [
    "Accept the quest",
    "Ask for more details",
    "Look for other work"
  ],
  "phase": "exploration"
}
```

### A.2 Skip Character Creation Example

```
GET /start?skip_character_creation=true

Response:
{
  "narrative": "The mists part before you, revealing crossroads where destiny awaits...",
  "session_id": "def-456",
  "choices": [
    "Enter the mysterious tavern",
    "Explore the dark forest path",
    "Investigate the ancient ruins"
  ]
}

(Default character created: Human Fighter, Level 1, standard stats)
```

---

## Appendix B: Alternative Approaches Considered

### B.1 Single-Turn Character Creation

**Approach**: User provides full character description in one input, system generates sheet immediately.

**Pros**:
- Faster for users who know what they want
- Simpler implementation (no turn management)
- Less LLM calls

**Cons**:
- No guidance for new players
- Misses opportunity for immersive interview
- Less character development/attachment
- Harder to extract structured info from unstructured blob

**Decision**: Multi-turn interview provides better UX and aligns with tavern setting.

### B.2 Form-Based Character Creation

**Approach**: Traditional dropdown selects for race, class, stat allocation UI.

**Pros**:
- Precise control
- Guaranteed valid output
- Familiar to D&D players

**Cons**:
- Breaks immersion
- Requires frontend form design
- Not aligned with "free-form description" requirement (FR-01)
- Less accessible to non-D&D players

**Decision**: Conversation-based approach better matches product vision.

### B.3 Parallel Agent Character Generation

**Approach**: Run InnkeeperAgent, KeeperAgent, JesterAgent in parallel on character description.

**Pros**:
- Faster processing
- Multiple perspectives on character

**Cons**:
- Complex orchestration
- May generate conflicting information
- YAGNI for MVP

**Decision**: Sequential interview with single agent (Innkeeper) is simpler and sufficient.

---

## Appendix C: Related Documents

- `docs/product.md` - Product requirements (Section 6.1, 9.1)
- `docs/design/2025-12-22-multi-agent-crew.md` - Agent patterns and testing
- `docs/design/2025-12-21-choice-system.md` - Choice presentation patterns
- `src/agents/innkeeper.py` - InnkeeperAgent implementation
- `src/state/models.py` - GameState model
- `src/api/main.py` - API endpoints

---

## Appendix D: Open Questions

1. **Should character level increase during adventure?**
   - Deferred: MVP characters remain level 1 for one-shot adventures
   - Future: Level progression in multi-session play

2. **How to handle character death?**
   - Deferred: Not implementing death mechanics in MVP
   - Future: Epilogue system handles character fate

3. **Should stats affect narrative outcomes?**
   - Yes: Pass character context to NarratorAgent for personalization
   - Future: Keeper can reference stats for mechanical resolution

4. **Allow character re-use across sessions?**
   - Deferred: Characters tied to single session for MVP
   - Future: Character library with authentication

5. **Validate stat total strictly (72 points)?**
   - Yes: KeeperAgent validates during generation
   - Allow minor variance (±3 points) for narrative flexibility

---

**End of Document**

Last Updated: 2025-12-24
Status: Ready for Implementation
