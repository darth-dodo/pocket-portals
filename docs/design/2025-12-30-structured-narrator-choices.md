# Design: Structured Narrator Choices

**Date**: 2025-12-30
**Status**: In Progress
**Author**: AI Assistant
**Branch**: `fix/structured-narrator-choices`

## Problem Statement

The current choice generation system is broken:

1. **Two LLM calls per turn**: The narrator makes one call to generate the narrative, then a second call to generate choices
2. **Silent failures**: Choice generation errors are swallowed, falling back to generic defaults like "Look around", "Wait", "Leave"
3. **Inconsistent choices**: The second LLM call has no memory of the creative decisions made in the first call, leading to contextually-disconnected choices
4. **Duplicate logic**: The streaming endpoint (`/action/stream`) duplicates the choice generation logic from the flow, causing maintenance burden

## Solution

Use CrewAI's `output_pydantic` feature to return **both narrative and choices in a single structured response**.

### New Pydantic Model

```python
class NarratorResponse(BaseModel):
    """Structured response from the narrator agent."""

    narrative: str = Field(
        description="The narrative description (2-4 sentences)"
    )
    choices: list[str] = Field(
        description="Exactly 3 short action choices (max 6 words each)",
        min_length=3,
        max_length=3,
    )
```

### New Narrator Method

```python
def respond_with_choices(self, action: str, context: str = "") -> NarratorResponse:
    """Generate narrative AND choices in a single LLM call."""
    task = Task(
        description=description,
        expected_output="A narrative description and 3 player choices",
        agent=self.agent,
        output_pydantic=NarratorResponse,
    )
    result = task.execute_sync()
    return result.pydantic
```

## Architecture Changes

### Before

```
┌─────────────────────────────────────────────────────────────┐
│                     Turn Execution                          │
├─────────────────────────────────────────────────────────────┤
│  1. execute_agents()                                        │
│     └── narrator.respond() ──► LLM Call #1 ──► narrative   │
│     └── keeper.respond()   ──► LLM Call #2 ──► mechanics   │
│     └── jester.respond()   ──► LLM Call #3 ──► humor       │
│                                                             │
│  2. aggregate_responses()                                   │
│     └── Combine narratives                                  │
│                                                             │
│  3. generate_choices()                                      │
│     └── narrator.respond() ──► LLM Call #4 ──► choices     │
│         (OFTEN FAILS SILENTLY → defaults)                   │
└─────────────────────────────────────────────────────────────┘
```

### After

```
┌─────────────────────────────────────────────────────────────┐
│                     Turn Execution                          │
├─────────────────────────────────────────────────────────────┤
│  1. execute_agents()                                        │
│     └── narrator.respond_with_choices()                     │
│         ──► LLM Call #1 ──► { narrative, choices }         │
│     └── keeper.respond()   ──► LLM Call #2 ──► mechanics   │
│     └── jester.respond()   ──► LLM Call #3 ──► humor       │
│                                                             │
│  2. aggregate_responses()                                   │
│     └── Combine narratives                                  │
│                                                             │
│  3. generate_choices()                                      │
│     └── If choices exist → return them                      │
│     └── Else → use defaults (rare fallback)                 │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| LLM calls per turn | 4 | 3 |
| Choice context awareness | Low (separate call) | High (same call) |
| Failure rate | High (silent) | Low (structured) |
| Token cost | ~2x for choices | ~0x extra |
| Latency | +1 API round-trip | None |

## Files Changed

1. **`src/agents/narrator.py`**
   - Add `NarratorResponse` Pydantic model
   - Add `respond_with_choices()` method

2. **`src/engine/flow.py`**
   - Update `execute_agents()` to use `respond_with_choices()` for narrator
   - Simplify `generate_choices()` to use pre-populated choices

3. **`src/api/main.py`** (streaming endpoint)
   - Update streaming loop to use structured response for narrator
   - Remove duplicate choice generation logic

## Testing Strategy

1. **Unit test**: `NarratorAgent.respond_with_choices()` returns valid `NarratorResponse`
2. **Integration test**: Flow produces contextual choices, not defaults
3. **E2E test**: `/action` and `/action/stream` return story-relevant choices

## Rollback Plan

If structured output fails:
1. `respond_with_choices()` catches exceptions and returns fallback `NarratorResponse`
2. `generate_choices()` still falls back to `DEFAULT_CHOICES` if needed
3. Original `respond()` method is preserved for backward compatibility

## Migration Path

1. Deploy with both `respond()` and `respond_with_choices()` methods
2. Gradually transition callers to structured method
3. Monitor choice quality and fallback rates
4. Remove duplicate choice generation code once stable
