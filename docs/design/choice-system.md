# Choice System Design

**Version**: 1.0
**Date**: 2025-12-21
**Status**: Proposed

---

## 1. Overview

The choice system enhances the narrative experience by providing players with structured options at decision points while maintaining flexibility for creative input.

### 1.1 Problem Statement

**Current State**: Players can only send free-form text actions. There's no guidance on what actions are available or expected.

**Desired State**: Players receive 3 suggested choices with each narrative response, plus the option to input custom actions. The system gracefully handles both predefined and unexpected inputs.

### 1.2 Requirements

From **product.md** section 9.2:
- Present 3 predefined choices at each narrative branch
- Include a custom input option
- Gracefully handle unexpected inputs
- Maintain narrative coherence

### 1.3 Design Principles

Following XP:
- **Simple Design**: Use the simplest solution that works
- **YAGNI**: Implement only what's needed now
- **TDD**: Design for testability from the start
- **Small Steps**: Incremental changes with working software at each step

---

## 2. API Changes

### 2.1 Response Model

**Before**:
```python
class NarrativeResponse(BaseModel):
    narrative: str
    session_id: str
```

**After**:
```python
class Choice(BaseModel):
    """A suggested choice for the player."""
    text: str
    description: str | None = None  # Optional hint/flavor text

class NarrativeResponse(BaseModel):
    narrative: str
    session_id: str
    choices: list[Choice]  # 3 suggested choices
```

**Example Response**:
```json
{
  "narrative": "The ancient door looms before you, covered in runes.",
  "session_id": "abc-123",
  "choices": [
    {"text": "Examine the runes closely", "description": null},
    {"text": "Try to push the door open", "description": null},
    {"text": "Look for another entrance", "description": null}
  ]
}
```

### 2.2 Request Model

**No Changes Required**:
```python
class ActionRequest(BaseModel):
    action: str  # Can be choice text OR free-form input
    session_id: str | None = None
```

**Rationale**: Keep request simple. The system doesn't need to know if the action came from a suggested choice or custom input. This reduces coupling and keeps the API clean.

---

## 3. Architecture

### 3.1 System Components

```
┌─────────────────┐
│  FastAPI        │
│  /action        │
│  endpoint       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  NarratorAgent  │◄────┐
│  .respond()     │     │
└────────┬────────┘     │
         │              │
         ↓              │
┌─────────────────┐     │
│  Narrator Task  │     │
│  (CrewAI)       │     │
└────────┬────────┘     │
         │              │
         ↓              │
┌─────────────────┐     │
│  Claude LLM     │─────┘
│  - Narrative    │
│  - Choices (3)  │
└─────────────────┘
```

### 3.2 Data Flow

1. **Player Action** → API receives `{"action": "...", "session_id": "..."}`
2. **Session Lookup** → Get conversation history
3. **Context Building** → Format history for LLM
4. **Narrator Task** → LLM generates narrative + 3 choices
5. **Parse Response** → Extract narrative text and choices
6. **Update History** → Store turn in session
7. **Return Response** → Send `{narrative, session_id, choices}` to client

### 3.3 Choice Generation Strategy

**Simple Approach (YAGNI)**:

Modify the task prompt to request choices in a structured format:

```yaml
# tasks.yaml - narrate_scene
description: |
  Respond to the player's action with immersive narrative.

  Action: {action}

  After your narrative, provide exactly 3 choices for what the player
  could do next. Format as:

  CHOICES:
  1. [choice text]
  2. [choice text]
  3. [choice text]

expected_output: |
  A narrative response followed by 3 suggested player choices.
```

**Parsing**:
```python
def parse_response(raw: str) -> tuple[str, list[Choice]]:
    """Extract narrative and choices from LLM response."""
    if "CHOICES:" in raw:
        parts = raw.split("CHOICES:")
        narrative = parts[0].strip()
        choice_text = parts[1].strip()

        choices = []
        for line in choice_text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering: "1. " or "- "
                text = line.lstrip("0123456789.-) ").strip()
                if text:
                    choices.append(Choice(text=text))

        # Ensure exactly 3 choices
        while len(choices) < 3:
            choices.append(Choice(text="Continue exploring"))

        return narrative, choices[:3]

    # Fallback: no choices found, generate defaults
    return raw, [
        Choice(text="Continue"),
        Choice(text="Look around"),
        Choice(text="Wait and observe")
    ]
```

---

## 4. Implementation Plan

### 4.1 Step 1: Extend Response Model (5 min)

**File**: `src/api/main.py`

**Changes**:
- Add `Choice` model
- Add `choices: list[Choice]` to `NarrativeResponse`
- Update endpoint to return empty choices initially

**Tests**:
```python
def test_narrative_response_includes_choices(client):
    response = client.post("/action", json={"action": "test"})
    data = response.json()
    assert "choices" in data
    assert isinstance(data["choices"], list)
```

**Result**: API returns new format, backwards compatible (frontend ignores new field)

---

### 4.2 Step 2: Update Narrator Task Prompt (10 min)

**File**: `src/config/tasks.yaml`

**Changes**:
- Modify `narrate_scene` description to request choices
- Update `expected_output` to specify format

**Tests**:
```python
def test_narrator_task_config_includes_choice_instruction():
    config = load_task_config("narrate_scene")
    assert "CHOICES" in config["description"]
    assert "3 choices" in config["description"]
```

**Result**: LLM now generates choices in responses (manual verification)

---

### 4.3 Step 3: Parse LLM Response (20 min)

**File**: `src/agents/narrator.py`

**Changes**:
- Add `parse_response()` function
- Modify `respond()` to return `tuple[str, list[Choice]]`
- Add default choices fallback

**Tests**:
```python
def test_parse_response_extracts_choices():
    raw = "You enter.\n\nCHOICES:\n1. Go left\n2. Go right\n3. Go back"
    narrative, choices = parse_response(raw)
    assert narrative == "You enter."
    assert len(choices) == 3
    assert choices[0].text == "Go left"

def test_parse_response_handles_missing_choices():
    raw = "Just narrative text"
    narrative, choices = parse_response(raw)
    assert len(choices) == 3  # Defaults
```

**Result**: Parser extracts choices reliably

---

### 4.4 Step 4: Wire Up Endpoint (10 min)

**File**: `src/api/main.py`

**Changes**:
- Update `process_action()` to get tuple from `narrator.respond()`
- Construct `NarrativeResponse` with choices

**Tests**:
```python
def test_action_endpoint_returns_three_choices(client):
    response = client.post("/action", json={"action": "test"})
    data = response.json()
    assert len(data["choices"]) == 3
    assert all("text" in choice for choice in data["choices"])
```

**Result**: End-to-end working system

---

### 4.5 Step 5: Integration Test (5 min)

**File**: `tests/test_api.py`

**Tests**:
```python
def test_choice_system_end_to_end(client):
    # First action
    response1 = client.post("/action", json={"action": "enter tavern"})
    data1 = response1.json()

    assert "narrative" in data1
    assert "choices" in data1
    assert len(data1["choices"]) == 3

    # Use one of the suggested choices
    choice_text = data1["choices"][0]["text"]
    session_id = data1["session_id"]

    # Second action using suggested choice
    response2 = client.post(
        "/action",
        json={"action": choice_text, "session_id": session_id}
    )
    data2 = response2.json()

    assert data2["session_id"] == session_id
    assert len(data2["choices"]) == 3

    # Third action using custom input
    response3 = client.post(
        "/action",
        json={"action": "dance on the table", "session_id": session_id}
    )
    data3 = response3.json()

    assert data3["session_id"] == session_id
    assert len(data3["choices"]) == 3
```

**Result**: System handles both suggested and custom actions

---

## 5. Future Enhancements (Out of Scope)

**Not implementing now** (YAGNI):
- Choice descriptions/hints
- Choice validation or filtering
- Dynamic choice count (always 3)
- Choice consequences tracking
- Choice metadata (difficulty, risk level)
- Structured output parsing (Pydantic models)

**When to implement**:
- Choice descriptions: When user feedback requests hints
- Validation: When we see common problematic choices
- Dynamic count: When narrative complexity requires it
- Structured parsing: When text parsing proves unreliable (>5% failure rate)

---

## 6. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM doesn't follow format | Medium | Fallback to default choices |
| Parsing fails on edge cases | Low | Default choices + logging |
| Choices not contextual | Medium | Improve prompt engineering |
| Performance degradation | Low | Same LLM call, minimal overhead |

---

## 7. Success Criteria

- [ ] API returns 3 choices with every narrative response
- [ ] Choices are contextually relevant to narrative
- [ ] System accepts both suggested and custom actions
- [ ] All existing tests pass
- [ ] New tests cover choice parsing and fallbacks
- [ ] Response time remains <3s (no degradation)

---

## 8. Open Questions

1. **Should choices be numbered in the UI?** → Deferred to frontend
2. **What if LLM generates <3 choices?** → Pad with defaults
3. **What if choices are duplicates?** → Accept for MVP, fix if problematic
4. **Should we log choice usage?** → Not for MVP, add later for analytics

---

## 9. Appendix

### 9.1 Example Interactions

**Scenario 1: Using Suggested Choice**
```
Request: {"action": "enter tavern"}
Response: {
  "narrative": "The tavern is warm and crowded...",
  "choices": [
    {"text": "Approach the bar"},
    {"text": "Find a quiet table"},
    {"text": "Talk to the hooded figure"}
  ]
}

Request: {"action": "Approach the bar", "session_id": "abc"}
Response: {
  "narrative": "The bartender wipes a glass...",
  "choices": [...]
}
```

**Scenario 2: Using Custom Action**
```
Request: {"action": "dance on the table", "session_id": "abc"}
Response: {
  "narrative": "The tavern goes silent as you leap onto the table...",
  "choices": [
    {"text": "Bow and step down"},
    {"text": "Start singing"},
    {"text": "Challenge someone to a duel"}
  ]
}
```

### 9.2 Alternative Approaches Considered

**1. Structured Output (JSON mode)**
```python
# Pros: Reliable parsing, type safety
# Cons: More complex, requires Pydantic models, less flexible
response = llm.generate(response_format={"type": "json_schema", ...})
```

**2. Separate Choice Generation Task**
```python
# Pros: Separation of concerns
# Cons: Two LLM calls (slower, more expensive)
narrative = narrator.respond(action)
choices = choice_generator.generate(narrative)
```

**3. Pre-defined Choice Trees**
```python
# Pros: Guaranteed quality, fast
# Cons: Not scalable, rigid, defeats AI purpose
CHOICE_TREE = {"enter_tavern": ["bar", "table", "leave"], ...}
```

**Decision**: Simple text parsing with fallbacks balances reliability, cost, and flexibility for MVP.

---

## 10. References

- **Product Requirements**: `product.md` (Section 9.2)
- **Current API**: `src/api/main.py`
- **Narrator Agent**: `src/agents/narrator.py`
- **CrewAI Docs**: https://docs.crewai.com
- **XP Practices**: Simple Design, YAGNI, TDD
