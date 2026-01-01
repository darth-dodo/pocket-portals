# Mobile-First UX Improvement Plan
## Pocket Portals - Solo D&D Adventure

**Branch**: `feature/ux-improvements`
**Created**: 2026-01-01
**Status**: Draft for Review

---

## Executive Summary

This plan outlines a comprehensive mobile-first UX overhaul for Pocket Portals. The current implementation uses NES.css styling with basic responsive breakpoints, but lacks modern mobile interaction patterns that users expect from touch-first experiences.

**Key Goals:**
1. Improve choice interaction with bottom sheet pattern
2. Enhance streaming feedback with agent indicators
3. Add adventure progress visualization
4. Create immersive character sheet access
5. Implement gesture-based navigation

---

## Current State Analysis

### What's Working Well
- NES.css retro aesthetic is distinctive and charming
- Basic responsive breakpoints (768px, 600px, 380px)
- Safe area insets for notched devices
- Reading mode toggle for accessibility
- Streaming text with typewriter effect

### Pain Points Identified

| Issue | Impact | Priority |
|-------|--------|----------|
| Choices disconnect from narrative flow | High | P1 |
| Minimal loading feedback | High | P1 |
| No adventure progress indicator | Medium | P2 |
| Character stats not visible in-game | Medium | P2 |
| Combat HUD covers content | Medium | P2 |
| No gesture navigation | Low | P3 |
| No haptic feedback | Low | P3 |

---

## Phase 1: Core Mobile UX (High Priority)

### 1.1 Bottom Sheet for Choices

**Problem**: Current inline choice buttons take up vertical space and feel disconnected from the narrative.

**Solution**: Implement a slide-up bottom sheet that:
- Appears after narrative streaming completes
- Contains choice buttons in a card-like container
- Includes expandable custom action input
- Supports swipe gestures to expand/collapse
- Uses frosted glass effect for visual hierarchy

**Visual Design**:
```
┌──────────────────────────────────────┐
│                                      │
│         NARRATIVE AREA               │
│         (Full height now)            │
│                                      │
├──────────────────────────────────────┤
│  ═══════════════ (handle)            │
│                                      │
│  ⚔️ Choose Your Path                 │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ Enter the mysterious tavern     │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ Explore the dark forest path    │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │ Investigate the ancient ruins   │ │
│  └─────────────────────────────────┘ │
│                                      │
│  ✏️ Write your own action...         │
│                                      │
└──────────────────────────────────────┘
```

**Implementation**:
- New CSS: `.bottom-sheet`, `.bottom-sheet-handle`, `.bottom-sheet-content`
- Touch events: `touchstart`, `touchmove`, `touchend` for swipe
- Animation: `transform: translateY()` with CSS transition
- State: Open, Collapsed, Hidden states

---

### 1.2 Compact Header with Turn Counter

**Problem**: Header takes space without providing gameplay value.

**Solution**: Transform header into a compact game status bar:

```
┌──────────────────────────────────────┐
│  [👤]    Turn 12 · The Cave    [⚙️]  │
│  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░  │
│          Act 1    Act 2    Act 3     │
└──────────────────────────────────────┘
```

**Features**:
- Left button: Opens character sheet drawer
- Center: Turn number + quest/location name
- Right button: Settings (theme, reading mode, sound)
- Progress bar: Shows adventure arc position (0-50 turns)
- Milestone markers: Visual indicators for story phases

**Behavior**:
- Shrinks on scroll down (sticky, minimal)
- Expands on scroll up
- Touch menu for character access

---

### 1.3 Enhanced Streaming Feedback

**Problem**: Current "Adventuring..." text is minimal; users don't know which agent is responding.

**Solution**: Rich response indicator showing active agent:

```
┌──────────────────────────────────────┐
│  ┌─────────────────────────────────┐ │
│  │  📜 Narrator                    │ │
│  │  weaving the tale ● ● ●        │ │
│  └─────────────────────────────────┘ │
└──────────────────────────────────────┘
```

**Variable Speed Streaming**:
| Content Type | Delay |
|--------------|-------|
| Regular text | 12ms |
| Punctuation (.,!?) | 80ms pause |
| Paragraph break | 150ms pause |
| Combat text | 8ms (faster) |
| Descriptions | 18ms (slower) |

**Agent Indicators**:
- 📜 Narrator - "weaving the tale..."
- 🎲 Keeper - "rolling the dice..."
- 🎭 Jester - "stirring mischief..."

---

## Phase 2: Character & Progress

### 2.1 Character Sheet Drawer

**Design**: Slide-out drawer from left edge (70% width on mobile)

```
┌─────────────────────┬────────────────┐
│                     │                │
│  ADVENTURER         │  (Overlay)     │
│  Human Fighter      │                │
│                     │                │
│  HP ▓▓▓▓▓▓▓▓░░ 16/20│                │
│                     │                │
│  ┌─────────────────┐│                │
│  │ STR 16 │ DEX 12 ││                │
│  │ CON 14 │ INT 10 ││                │
│  │ WIS 13 │ CHA  8 ││                │
│  └─────────────────┘│                │
│                     │                │
│  CURRENT QUEST      │                │
│  The Lost Shrine    │                │
│                     │                │
│  JOURNAL            │                │
│  • Entered tavern   │                │
│  • Met innkeeper    │                │
│  • Heard about cave │                │
│                     │                │
└─────────────────────┴────────────────┘
```

**Interactions**:
- Swipe right from left edge to open
- Swipe left to close
- Tap outside to close
- Tap menu button in header to open

---

### 2.2 Adventure Progress Visualization

**Progress Bar in Header**:
- Fills left-to-right as turns progress
- Color changes: Green (Act 1) → Yellow (Act 2) → Orange (Act 3)
- Milestone markers at turns 10, 25, 40
- Glow effect when milestone reached

**API Integration**:
- Backend already tracks `adventure_turn`
- Need to expose in SSE `complete` event
- Frontend updates progress bar on each turn

---

## Phase 3: Polish & Delight

### 3.1 Haptic Feedback

Use Vibration API where supported:

```javascript
const haptics = {
  light: () => navigator.vibrate?.(10),
  medium: () => navigator.vibrate?.(25),
  success: () => navigator.vibrate?.([10, 50, 10]),
  error: () => navigator.vibrate?.([50, 50, 50]),
  combat: () => navigator.vibrate?.([15, 30, 15, 30, 50])
};
```

**Trigger Points**:
- Choice selection: Light
- Action submitted: Medium
- Combat hit: Combat pattern
- Victory/Defeat: Success/Error

---

### 3.2 PWA Setup

**manifest.json**:
```json
{
  "name": "Pocket Portals",
  "short_name": "Portals",
  "description": "Solo D&D Adventure",
  "theme_color": "#1a1a2e",
  "background_color": "#212529",
  "display": "standalone",
  "orientation": "portrait",
  "icons": [...]
}
```

**Service Worker**:
- Cache static assets (HTML, CSS, fonts, icons)
- Network-first for API calls
- Offline fallback page

---

### 3.3 Theme System

**Available Themes**:
| Theme | Primary | Secondary | Background |
|-------|---------|-----------|------------|
| Dark (default) | #f7d354 | #92cc41 | #212529 |
| Light | #c9a227 | #2e7d32 | #f5f5f5 |
| Dungeon | #e65100 | #5d4037 | #1a1a1a |
| Forest | #81c784 | #a5d6a7 | #1b2e1b |
| Celestial | #90caf9 | #ce93d8 | #0d1b2a |

**Implementation**:
- CSS custom properties for colors
- Theme class on body element
- LocalStorage persistence
- Settings modal for selection

---

### 3.4 Sound System

**Sound Categories**:
- UI: button clicks, sheet open/close
- Narrative: ambient background (optional)
- Combat: sword clash, dice roll, hit/miss
- Feedback: success fanfare, defeat tone

**Implementation**:
- Howler.js for audio management
- Volume control in settings
- Mute toggle in header
- Auto-pause on tab hidden

---

## Implementation Roadmap

### Sprint 1: Core Mobile UX (Recommended Start)
**Estimated Effort: 4-6 hours**

- [ ] 1.1 Bottom sheet component (HTML/CSS/JS)
- [ ] 1.1 Touch gesture handling
- [ ] 1.2 Compact header redesign
- [ ] 1.2 Progress bar component
- [ ] 1.3 Agent indicator during streaming
- [ ] 1.3 Variable speed streaming

### Sprint 2: Character & Progress
**Estimated Effort: 3-4 hours**

- [ ] 2.1 Character sheet drawer
- [ ] 2.1 Character data display
- [ ] 2.2 Adventure turn tracking in UI
- [ ] 2.2 Milestone visualization

### Sprint 3: Polish (Optional)
**Estimated Effort: 2-3 hours each**

- [ ] 3.1 Haptic feedback integration
- [ ] 3.2 PWA manifest and service worker
- [ ] 3.3 Theme system
- [ ] 3.4 Sound system

---

## Technical Considerations

### Touch Handling
```javascript
// Swipe detection for bottom sheet
let startY = 0;
let currentY = 0;

element.addEventListener('touchstart', (e) => {
  startY = e.touches[0].clientY;
});

element.addEventListener('touchmove', (e) => {
  currentY = e.touches[0].clientY;
  const delta = startY - currentY;
  // Apply transform based on delta
});

element.addEventListener('touchend', (e) => {
  const delta = startY - currentY;
  if (delta > 50) expandSheet();
  else if (delta < -50) collapseSheet();
});
```

### CSS Custom Properties for Theming
```css
:root {
  --color-primary: #f7d354;
  --color-secondary: #92cc41;
  --color-background: #212529;
  --color-surface: #1a1a2e;
  --color-text: #f5f5f5;
  --color-text-muted: #8a8a9a;
}

[data-theme="light"] {
  --color-primary: #c9a227;
  --color-background: #f5f5f5;
  /* ... */
}
```

### Backend Data Needs
The following data should be exposed in SSE events:

```json
// In "complete" event
{
  "session_id": "...",
  "adventure_turn": 12,
  "phase": "exploration",
  "character": {
    "name": "Adventurer",
    "race": "human",
    "class": "fighter",
    "hp": 16,
    "max_hp": 20
  },
  "quest": {
    "title": "The Lost Shrine",
    "progress": 0.4
  }
}
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Touch target size | Varies | 44px minimum |
| Time to first choice | ~3s | <2s |
| Streaming feel | Mechanical | Natural/Dramatic |
| Mobile usability score | ~70 | 90+ |
| User engagement (turns/session) | Unknown | Track |

---

## Questions for Review

1. **Bottom Sheet vs Inline**: Should we keep both options or fully commit to bottom sheet?

2. **Character Sheet Scope**: How much character data to show? Full D&D stats or simplified?

3. **Sound Priority**: Is sound system worth the effort, or focus on visual polish first?

4. **Theme System**: Start with just dark/light, or implement full theme system?

5. **PWA Priority**: Important for mobile app-like experience, but adds complexity.

---

## Next Steps

1. Review and approve this plan
2. Decide on Phase 1 scope (all items or subset)
3. Begin implementation with bottom sheet component
4. Test on real mobile devices throughout development
5. Gather user feedback on each phase before proceeding

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
