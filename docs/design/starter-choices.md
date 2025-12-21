# Starter Choices Design

**Version**: 1.0
**Date**: 2025-12-21
**Status**: Implemented

---

## 1. Overview

The starter choices system provides adventure hooks to begin the journey, ensuring players have engaging options from the first moment rather than a blank slate.

### 1.1 Problem Statement

**Current State**: Players land on a welcome screen with only free-text input, which can feel daunting for new players unfamiliar with the game.

**Desired State**: Players are presented with 3 curated starter choices (shuffled from a larger pool) that immediately hook them into the adventure, while still supporting custom input.

### 1.2 Requirements

- Present 3 starter choices when beginning a new adventure
- Support shuffle to vary which choices are shown
- Maintain consistency with existing choice system format
- Store choices in session for use with `/action` endpoint

### 1.3 Design Principles

Following XP:
- **Simple Design**: Use existing response model, no new models needed
- **YAGNI**: Pool of 9 starters is sufficient for MVP
- **TDD**: Tests written first, implementation follows

---

## 2. API Design

### 2.1 New Endpoint

```
GET /start?shuffle=true|false
```

**Response Model**: Same as `/action` - `NarrativeResponse`

```json
{
  "narrative": "The mists part before you, revealing crossroads...",
  "session_id": "abc-123",
  "choices": [
    "Enter the mysterious tavern",
    "Explore the dark forest path",
    "Investigate the ancient ruins"
  ]
}
```

### 2.2 Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `shuffle` | bool | `false` | Randomize which 3 choices from pool are shown |

---

## 3. Implementation

### 3.1 Starter Choices Pool

9 adventure hooks designed to appeal to different player preferences:

```python
STARTER_CHOICES_POOL = [
    "Enter the mysterious tavern",      # Classic D&D start
    "Explore the dark forest path",     # Nature/wilderness
    "Investigate the ancient ruins",    # Exploration/mystery
    "Follow the hooded stranger",       # Intrigue/suspense
    "Approach the glowing portal",      # Magic/otherworldly
    "Descend into the forgotten dungeon", # Dungeon crawl
    "Board the departing airship",      # Adventure/travel
    "Answer the distress signal",       # Heroic/rescue
    "Accept the wizard's quest",        # Quest-giver
]
```

### 3.2 Selection Logic

```python
if shuffle:
    choices = random.sample(STARTER_CHOICES_POOL, 3)
else:
    choices = STARTER_CHOICES_POOL[:3]  # Consistent default
```

### 3.3 Welcome Narrative

A thematic introduction that sets the tone:

```python
WELCOME_NARRATIVE = (
    "The mists part before you, revealing crossroads where destiny awaits. "
    "Three paths shimmer with possibility, each promising adventure, danger, "
    "and glory. Choose wisely, brave soul, for your legend begins with a single step..."
)
```

---

## 4. Frontend Integration

### 4.1 Begin Quest Button

Added to welcome screen:
```html
<button class="nes-btn is-primary begin-btn" id="begin-btn">
    <i class="ra ra-player-lift"></i> Begin Quest
</button>
```

### 4.2 Flow

1. User clicks "Begin Quest" button
2. Frontend calls `GET /start?shuffle=true`
3. Session is created and stored
4. Welcome narrative and 3 choices are displayed
5. User can select a choice or type custom action
6. Subsequent actions use `/action` with `session_id`

### 4.3 UI Improvements

- Increased story canvas height (300-500px)
- Improved text readability (larger font, better line-height)
- Pulsing animation on Begin Quest button

---

## 5. Testing

### 5.1 Test Cases

| Test | Description |
|------|-------------|
| `test_start_endpoint_returns_starter_choices` | Returns 3 choices |
| `test_start_choices_are_non_empty_strings` | Choices are valid strings |
| `test_start_endpoint_returns_session_id` | Creates new session |
| `test_start_endpoint_returns_welcome_narrative` | Returns narrative |
| `test_start_shuffle_returns_different_order` | Shuffle param works |
| `test_start_session_can_be_used_for_action` | Session compatible with /action |

### 5.2 Coverage

All tests passing with 78% overall coverage.

---

## 6. Future Enhancements (Out of Scope)

**Not implementing now** (YAGNI):
- Category-based starter selection (combat, mystery, social)
- User preference learning
- Dynamic pool based on time/season
- Starter choice descriptions/hints

**When to implement**:
- Categories: When player feedback shows preference patterns
- Learning: When we have user accounts and history
- Dynamic: When we want seasonal content

---

## 7. References

- **Choice System Design**: `/docs/design/choice-system.md`
- **Product Requirements**: `/product.md` (FR-07, FR-08)
- **API Implementation**: `/src/api/main.py`
- **Tests**: `/tests/test_api.py`
