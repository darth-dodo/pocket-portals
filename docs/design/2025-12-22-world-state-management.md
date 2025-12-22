# World State Management Design Document

**Feature**: Implement world state management for session persistence
**Author**: Architect Agent
**Date**: 2025-12-22
**Status**: ✅ Implemented

---

## Overview

This document defines the design for world state management in Pocket Portals. The goal is to move from simple conversation history tracking to a structured game state that agents can use for richer, more coherent narratives.

---

## Goals

1. **Minimal Viable State**: Only track what agents actually need
2. **Type Safety**: Pydantic models for validation and IDE support
3. **Backward Compatible**: Existing API contracts remain unchanged
4. **Extensible**: Easy to add fields as features mature
5. **YAGNI Compliant**: No speculative features

---

## Non-Goals (YAGNI)

- Full D&D 5e character sheets (stats, skills, proficiencies)
- Inventory system
- Spell slots / resource management
- Experience points / leveling
- Dice roll history
- Combat state (defer to combat feature)
- Persistent storage (in-memory only for now)

---

## Current State Analysis

### What We Have
```python
# src/api/main.py (current implementation)
sessions: dict[str, list[dict[str, str]]] = {}  # {session_id: [{action, narrative}]}
session_choices: dict[str, list[str]] = {}       # {session_id: [choice1, choice2, choice3]}
```

### Problems
1. No character context for personalization
2. No health/damage tracking for Keeper
3. Two separate dicts for related data
4. No type safety or validation

---

## Proposed State Model

### Core GameState (Pydantic)

```python
from pydantic import BaseModel, Field

class GameState(BaseModel):
    """Minimal game state for solo D&D narrative adventure."""

    # Core Identity
    session_id: str

    # Narrative Memory (limit to last 20 for token efficiency)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)

    # UI State
    current_choices: list[str] = Field(default_factory=list)

    # Character Context
    character_description: str = ""

    # Simple Mechanics (Keeper needs these)
    health_current: int = 20
    health_max: int = 20
```

### What Each Agent Needs

| Agent | Needs From State | Purpose |
|-------|------------------|---------|
| **Narrator** | conversation_history, character_description | Coherent narrative, personalization |
| **Innkeeper** | character_description | Quest personalization |
| **Keeper** | health_current, health_max | Damage tracking ("8 damage. 6 left.") |
| **Jester** | conversation_history (recent turns) | Meta-observations, pattern spotting |

---

## Implementation Plan

### File Structure

```
src/
├── state/
│   ├── __init__.py          # Export GameState, SessionManager
│   ├── models.py             # GameState Pydantic model
│   └── session_manager.py    # Session CRUD operations
├── api/
│   └── main.py               # Updated to use SessionManager
```

### SessionManager Interface

```python
class SessionManager:
    """Manages game sessions with in-memory storage."""

    def __init__(self) -> None:
        self._sessions: dict[str, GameState] = {}

    def create_session(self) -> GameState:
        """Create a new session with default state."""
        ...

    def get_session(self, session_id: str) -> GameState | None:
        """Get existing session or None."""
        ...

    def get_or_create_session(self, session_id: str | None) -> GameState:
        """Get existing session or create new one."""
        ...

    def update_session(self, session_id: str, **updates) -> GameState:
        """Update session fields."""
        ...

    def add_exchange(self, session_id: str, action: str, narrative: str) -> None:
        """Add conversation exchange, maintaining history limit."""
        ...

    def update_health(self, session_id: str, damage: int) -> int:
        """Apply damage and return remaining health."""
        ...
```

---

## API Changes

### Response Model Update

```python
class NarrativeResponse(BaseModel):
    narrative: str
    session_id: str
    choices: list[str] = Field(default_factory=list)
    health: int | None = None  # NEW: Include health when relevant
```

### Endpoint Changes

| Endpoint | Change |
|----------|--------|
| `/start` | Accept optional `character_description` |
| `/action` | Return health in response |
| `/keeper/resolve` | Update health on damage |

---

## Test Plan

### Unit Tests

```
tests/
├── test_models.py           # GameState validation
├── test_session_manager.py  # Session CRUD operations
└── test_api.py              # Updated endpoint tests
```

### Test Cases

1. **GameState Model**
   - Default values populated correctly
   - Validation rejects invalid data
   - Serialization/deserialization works

2. **SessionManager**
   - Create session generates UUID
   - Get session returns correct state
   - History limit enforced (max 20)
   - Health updates calculate correctly

3. **API Integration**
   - /start accepts character_description
   - /action returns health
   - Session state persists across requests

---

## Implementation Order

1. **Models** (`src/state/models.py`) - GameState Pydantic model
2. **SessionManager** (`src/state/session_manager.py`) - CRUD operations
3. **Tests** - TDD for each component
4. **API Integration** - Update endpoints to use SessionManager
5. **Documentation** - Update tasks.md, README

Each step follows TDD: Red → Green → Refactor → Commit

---

## Migration Strategy

### Phase 1: Add New System (This PR)
- Implement GameState and SessionManager alongside existing code
- Update endpoints to use new system
- Maintain backward compatibility

### Phase 2: Future Enhancements
- Add optional fields (quest_status, location, reputation)
- Add session expiration
- Add persistence layer (Redis/database)

---

## Success Criteria

- [x] GameState model with type validation
- [x] SessionManager with CRUD operations
- [x] History limit enforced (max 20 exchanges)
- [x] Health tracking for Keeper
- [x] Character description for personalization
- [x] Test coverage ≥70% (82% achieved)
- [x] All existing tests still pass
- [ ] Documentation updated (in progress)

---

## Related Documents

- `docs/product.md` - Product requirements (FR-09)
- `docs/reference/conversation-engine.md` - Future orchestration patterns
- `docs/design/2025-12-22-multi-agent-crew.md` - Agent implementation
- `src/config/loader.py` - Pydantic patterns to follow
