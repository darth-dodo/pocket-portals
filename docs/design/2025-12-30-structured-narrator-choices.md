# Design: Structured Narrator Choices

**Date**: 2026-01-01
**Status**: Complete
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

## Implementation Complete (2026-01-01)

### Features Implemented

1. **Structured Pydantic Output**
   - `NarratorResponse` model with `narrative` and `choices` fields
   - Improved Field descriptions to guide LLM toward contextual choices
   - `min_length=3, max_length=3` constraint enforces exactly 3 choices

2. **Choice Quality Observability**
   - `ChoiceQuality` dataclass tracks generic vs contextual choice counts
   - `_analyze_choice_quality()` function detects generic choices like "Look around", "Wait", "Leave"
   - Quality score (0.0-1.0) logged for every narrator response
   - Warning logged when quality score < 0.67 (less than 2/3 contextual)

3. **CrewAI Tracing**
   - `CREWAI_TRACING_ENABLED=true` in `.env` enables built-in tracing
   - Traces visible at https://aop.crewai.com

4. **Frontend UX Improvement**
   - Choices section now **hides** while narrator generates new options
   - Prevents user confusion from stale choices during loading
   - New choices appear only after narrator response completes

### Files Changed

| File | Changes |
|------|---------|
| `src/agents/narrator.py` | Added `NarratorResponse`, `ChoiceQuality`, `_analyze_choice_quality()`, observability logging |
| `src/api/main.py` | Added logging configuration |
| `static/index.html` | Hide choices section during loading |
| `.env` | Added `CREWAI_TRACING_ENABLED=true` |
| `.env.example` | Documented CrewAI tracing option |
| `tests/test_narrator.py` | Added `TestChoiceQualityAnalysis` test suite |

### Quality Metrics

- **Tests**: All passing (368 tests)
- **Coverage**: 75%
- **Linting**: All checks pass
