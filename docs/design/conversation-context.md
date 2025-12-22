# Feature: Conversation Context Passing

## Overview

Pass conversation history to the Narrator agent so it can reference past actions and maintain narrative continuity across turns.

**Business Value**: Players get coherent, contextual narratives that remember their actions.

## Requirements

### Functional Requirements
- Narrator receives conversation history with each request
- History formatted as readable context for the LLM
- Context includes both player actions and narrator responses

### Non-Functional Requirements
- No performance degradation (history formatting <10ms)
- Simple implementation (YAGNI - no premature optimization)

## Architecture

### Components

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  /action    │────▶│ build_context│────▶│ NarratorAgent  │
│  endpoint   │     │   function   │     │   .respond()   │
└─────────────┘     └──────────────┘     └────────────────┘
       │                   │                     │
       │ history[]         │ context string      │ task description
       ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│  Task: "Previous conversation:\n- Player: ...\n..."    │
│        "Current action: {action}"                      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. `/action` endpoint receives request with optional `session_id`
2. `get_session()` retrieves or creates session history
3. `build_context()` formats history into LLM-readable string
4. `narrator.respond(action, context)` includes context in task
5. Response appended to history for next turn

### Interface Changes

**main.py** - New function:
```python
def build_context(history: list[dict[str, str]]) -> str:
    """Format conversation history for LLM context."""
```

**narrator.py** - Updated signature:
```python
def respond(self, action: str, context: str = "") -> str:
    """Generate narrative response with optional context."""
```

## Implementation Plan

1. **Write failing test** for `build_context()` function
2. **Implement** `build_context()` - minimal code to pass
3. **Write failing test** for narrator with context
4. **Update** `narrator.respond()` to accept context parameter
5. **Wire up** context in `/action` endpoint
6. **Run quality gates** - all tests, lint, coverage

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Token overflow with long history | YAGNI - address when it becomes a problem |
| LLM confused by context format | Simple, clear format with labeled sections |

## Testing Strategy

- **Unit tests**: `build_context()` with various history states
- **Integration tests**: Endpoint passes context to narrator
- **Coverage target**: Maintain ≥70%

## Acceptance Criteria

- [ ] `build_context()` formats history correctly
- [ ] `narrator.respond()` accepts optional context
- [ ] `/action` endpoint passes context to narrator
- [ ] All existing tests still pass
- [ ] New tests for context functionality
