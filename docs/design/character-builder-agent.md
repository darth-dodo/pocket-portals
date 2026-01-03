# Feature: CharacterBuilder Subagent Integration

**Status: IMPLEMENTED ✅**

## Overview

Integrate intelligent character stat generation into the character creation flow using a new CharacterBuilderAgent subagent that analyzes the 5-turn interview conversation and generates thematic, balanced character stats.

**Business Value**: Characters feel unique and reflect player choices during interview, rather than using generic default stats.

## Implementation Summary

| Task | Status | Notes |
|------|--------|-------|
| Create CharacterBuilderAgent | ✅ Complete | `src/agents/character_builder.py` |
| Add YAML Configuration | ✅ Complete | `agents.yaml`, `tasks.yaml` |
| API Integration | ✅ Complete | `CharacterSheetData`, SSE events, skip fixes |
| Export and Test | ✅ Complete | E2E tests 11-14 passing |

**Key Files**:
- `src/agents/character_builder.py` - CharacterBuilderAgent class
- `src/config/agents.yaml` - `character_builder` agent config
- `src/config/tasks.yaml` - `build_character` task config
- `src/api/main.py` - CharacterSheetData model, SSE integration
- `tests/test_api.py` - Skip character creation tests

**Quality Gates Passed**:
- ✅ Pydantic models have proper validation
- ✅ Agent follows existing CrewAI patterns
- ✅ YAML config matches existing structure
- ✅ E2E tests pass (tests 11-14)
- ✅ No type errors (mypy)
- ✅ Code follows project conventions

## Requirements

### Functional
- Generate character stats (STR, DEX, CON, INT, WIS, CHA) based on conversation analysis
- Extract character name, race, and class from interview dialogue
- Create backstory summary from player choices
- Assign appropriate starting equipment based on class
- Calculate HP based on constitution modifier

### Non-Functional
- Single LLM call at turn 5 (no per-turn overhead)
- Fallback to keyword-based generation on failure
- Response time < 5s for character generation
- Structured Pydantic output for reliable parsing

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Character Creation Flow                       │
├─────────────────────────────────────────────────────────────────┤
│  Turn 1-4: CharacterInterviewerAgent                            │
│     ↓ (conversation_history accumulates)                        │
│  Turn 5: CharacterInterviewerAgent → CharacterBuilderAgent      │
│     ↓ (structured output)                                       │
│  CharacterSheet created and stored                              │
│     ↓                                                           │
│  SSE event: game_state with character_sheet                     │
│     ↓                                                           │
│  Frontend: updateCharacterSheet() → DOM update                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# Output model for LLM (Pydantic)
class CharacterStatsOutput(BaseModel):
    strength: int = Field(ge=3, le=18)
    dexterity: int = Field(ge=3, le=18)
    constitution: int = Field(ge=3, le=18)
    intelligence: int = Field(ge=3, le=18)
    wisdom: int = Field(ge=3, le=18)
    charisma: int = Field(ge=3, le=18)

class CharacterBuildOutput(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    race: str  # Mapped to CharacterRace enum
    character_class: str  # Mapped to CharacterClass enum
    stats: CharacterStatsOutput
    backstory: str = Field(max_length=500)
    equipment: list[str]

# Existing model (target)
CharacterSheet  # from src/state/character.py
```

### API Integration Points

1. **Initialize**: `src/api/main.py` lifespan startup
2. **Call site**: `_generate_character_from_history()` function
3. **Event emission**: After phase transition to EXPLORATION

## Dependencies

- **Internal**:
  - `src/state/character.py` - CharacterSheet, CharacterStats, enums
  - `src/config/loader.py` - load_agent_config, load_task_config
  - `src/config/settings.py` - API key access
- **External**:
  - `crewai` - Agent, Task, LLM classes
  - `pydantic` - BaseModel, Field for structured output

## Implementation Plan

### Task 1: Create CharacterBuilderAgent (45min)
- Create `src/agents/character_builder.py`
- Define Pydantic output models
- Implement `CharacterBuilderAgent` class
- Add `build_character()` method with `output_pydantic` pattern
- Implement enum mapping and fallback logic

### Task 2: Add YAML Configuration (15min)
- Add `character_builder` to `src/config/agents.yaml`
- Add `build_character` task to `src/config/tasks.yaml`

### Task 3: API Integration (30min)
- Initialize CharacterBuilderAgent in main.py lifespan
- Update `_generate_character_from_history()` to use agent
- Add `game_state` SSE event emission after character creation

### Task 4: Export and Test (30min)
- Export from `src/agents/__init__.py`
- Write unit tests for CharacterBuilderAgent
- Run E2E test with Playwright

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM parsing failure | Character not created | Fallback to keyword-based generation |
| Stat imbalance | Overpowered/underpowered chars | Constrain total points in prompt |
| Slow response | Poor UX | Lower max_tokens, use Haiku model |
| Enum mismatch | Validation error | String-to-enum mapping with defaults |

## Testing Strategy

### Unit Tests
- `build_character()` with mock conversation → valid CharacterSheet
- `_convert_to_character_sheet()` with edge cases
- `_create_fallback_character()` returns valid defaults

### Integration Tests
- POST /action through 5 turns → character_sheet in response
- Verify SSE `game_state` event contains character data

### E2E Tests (Playwright)
- Complete character creation flow
- Verify character sheet panel displays after turn 5
- Check stats, HP bar, name render correctly

## Quality Gates

- [x] Pydantic models have proper validation
- [x] Agent follows existing CrewAI patterns
- [x] YAML config matches existing structure
- [x] E2E tests pass (tests 11-14)
- [x] No type errors (mypy)
- [x] Code follows project conventions
