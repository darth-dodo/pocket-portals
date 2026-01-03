# Playwright E2E Test Suite

This document describes the End-to-End testing setup and test scenarios for Pocket Portals using Playwright MCP.

## Overview

Pocket Portals uses Playwright for browser automation and E2E testing. The tests verify the complete user journey from landing page through gameplay, including mobile responsiveness and theme switching.

## Test Environment

- **Server**: FastAPI with uvicorn (`src.api.main:app`)
- **Default Port**: 8765
- **Browser**: Chromium (via Playwright MCP)
- **Test Date**: January 3, 2026

## Starting the Test Server

```bash
# Activate virtual environment and start server
source .venv/bin/activate
uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8765
```

## Test Scenarios

### 1. Homepage Load Test

**Objective**: Verify the application loads correctly with all UI elements.

**Steps**:
1. Navigate to `http://127.0.0.1:8765/`
2. Verify page title is "Pocket Portals - Solo D&D Adventure"
3. Verify "Welcome, Adventurer!" heading is visible
4. Verify "Begin Quest" button is present
5. Verify action input field is present

**Expected Result**:
- Console shows "Pocket Portals initialized"
- All UI elements render correctly

**Screenshot**: `e2e-screenshots/01-homepage.png`

---

### 2. Quest Start Test

**Objective**: Verify new game can be started and narrative appears.

**Steps**:
1. Click "Begin Quest" button
2. Wait for streaming response to complete
3. Verify narrative text appears in story box
4. Verify choices are displayed

**Expected Result**:
- Narrative text from the narrator appears
- 3 choice buttons are displayed
- Turn counter shows "1"

**Screenshot**: `e2e-screenshots/02-quest-started.png`

---

### 3. Choice Selection Test

**Objective**: Verify player can select choices and game progresses.

**Steps**:
1. Click on a choice button (e.g., "I am a former military scout...")
2. Wait for streaming response
3. Verify player action appears in chat
4. Verify narrator response appears
5. Verify new choices are displayed
6. Verify turn counter increments to "2"

**Expected Result**:
- Player's choice is echoed in chat
- Narrator responds with follow-up
- New contextual choices appear
- Turn counter updates

**Screenshot**: `e2e-screenshots/03-turn-2-choices.png`

---

### 4. Theme Modal Test

**Objective**: Verify theme selector opens and displays options.

**Steps**:
1. Click settings button (gear icon) in header
2. Verify theme modal opens
3. Verify all 4 themes are listed:
   - RPG Classic
   - Midnight Minimal
   - Monospace
   - iOS Dark
4. Verify "Done" button is present

**Expected Result**:
- Modal overlay appears
- All theme options are clickable
- Current theme is highlighted

**Screenshot**: `e2e-screenshots/04-theme-modal.png`

---

### 5. Theme Switching Test

**Objective**: Verify themes can be switched and persist.

**Steps**:
1. Open theme modal
2. Click "Midnight Minimal" theme
3. Verify UI updates with new theme colors
4. Verify theme persists in localStorage

**Expected Result**:
- UI immediately updates to Midnight theme
- Colors change to elegant dark with serif headers
- `localStorage.getItem('pocket-portals-theme')` returns 'midnight'

**Screenshot**: `e2e-screenshots/05-midnight-theme.png`

---

### 6. Mobile Responsive Test

**Objective**: Verify application works on mobile viewport.

**Steps**:
1. Resize browser to 390x844 (iPhone 14 Pro)
2. Verify header adapts to mobile layout
3. Verify bottom sheet appears instead of inline choices
4. Verify story content is readable

**Expected Result**:
- Header shows compact layout
- Bottom sheet shows "Choose Your Path" with swipe hint
- Content is properly sized for mobile

**Screenshot**: `e2e-screenshots/06-mobile-view.png`

---

### 7. Bottom Sheet Expansion Test

**Objective**: Verify mobile bottom sheet expands to show choices.

**Steps**:
1. In mobile viewport, tap on bottom sheet header
2. Verify bottom sheet expands
3. Verify all choices are visible
4. Verify custom action input is available

**Expected Result**:
- Bottom sheet expands with animation
- Choice buttons are fully visible
- Custom input field with submit button appears

**Screenshot**: `e2e-screenshots/07-mobile-bottom-sheet-expanded.png`

---

### 8. Custom Action Input Test

**Objective**: Verify player can type custom actions.

**Steps**:
1. Focus on action input field
2. Type custom action text
3. Verify text appears in input
4. (Optional) Submit and verify response

**Expected Result**:
- Input field accepts text
- Submit button is enabled
- Custom action can be submitted to game

**Screenshot**: `e2e-screenshots/08-custom-input.png`

---

### 9. Quest Selection Flow Test

**Objective**: Verify quest selection appears after character creation and player can choose a quest.

**Steps**:
1. Complete character creation (5 turns of interview)
2. Verify transition to quest selection phase
3. Verify 3 quest options are displayed as choices
4. Verify quest titles are descriptive and unique

**Expected Result**:
- After character creation, innkeeper presents 3 quest options
- Quest options are contextual to character class/abilities
- Each quest has a clear title describing the objective

**Screenshot**: `e2e-screenshots/09-quest-selection.png`

---

### 10. Quest Activation Test

**Objective**: Verify selecting a quest activates it and starts exploration.

**Steps**:
1. From quest selection screen, click a quest option
2. Verify quest is activated (shown in header)
3. Verify transition to exploration phase
4. Verify narrative describes quest location/objective

**Expected Result**:
- Selected quest becomes active
- Exploration narrative begins
- New contextual choices appear for exploration
- Turn counter increments

**Screenshot**: `e2e-screenshots/10-exploration-after-quest-selection.png`

---

### 11. Character Sheet Display Test

**Objective**: Verify character sheet panel appears after character creation and displays stats correctly.

**Steps**:
1. Complete character creation (5 turns of interview)
2. Select a quest to enter exploration phase
3. Verify character sheet panel is visible
4. Verify character identity (name, race, class, level) is displayed
5. Verify HP bar shows current/max HP with color coding
6. Verify all 6 ability scores are displayed with modifiers

**Expected Result**:
- Character sheet panel appears in sidebar (desktop) or collapsible header (mobile)
- Name, race, class, level match created character
- HP bar shows green (>50%), yellow (26-50%), or red (≤25%) based on health
- Stats show values (3-18) with calculated modifiers (+4 to -4)
- Quest section shows active quest title and objectives

**Screenshot**: `e2e-screenshots/11-character-sheet.png`

---

### 12. Character Sheet Collapse/Expand Test

**Objective**: Verify character sheet panel can be collapsed and expanded.

**Steps**:
1. With character sheet visible, click the toggle button
2. Verify panel collapses with smooth animation
3. Verify collapsed state shows minimal info (name + HP)
4. Click toggle again to expand
5. Verify full character sheet content is visible

**Expected Result**:
- Toggle button (↑/↓ icons) works correctly
- Collapse animation is smooth (300ms transition)
- Collapsed state persists across page interactions
- Expanded state shows all character information

**Screenshot**: `e2e-screenshots/12-character-sheet-collapsed.png`

---

### 13. Character Sheet Theme Integration Test

**Objective**: Verify character sheet matches each theme's visual style.

**Steps**:
1. Start game and create character
2. For each theme (RPG, Midnight, Mono, iOS):
   - Open theme modal and select theme
   - Verify character sheet colors match theme
   - Verify font styles match theme
   - Verify border radius matches theme

**Expected Result**:
- **RPG Classic**: Gold accents, Press Start 2P font, 8px radius
- **Midnight Minimal**: White accents, Playfair Display font, no radius
- **Monospace**: White accents, IBM Plex Mono font, underlines
- **iOS Dark**: White accents, DM Sans font, 16px radius

**Screenshots**:
- `e2e-screenshots/13-charsheet-rpg.png`
- `e2e-screenshots/13-charsheet-midnight.png`
- `e2e-screenshots/13-charsheet-mono.png`
- `e2e-screenshots/13-charsheet-ios.png`

---

### 14. Character Sheet Mobile Test

**Objective**: Verify character sheet works on mobile viewport.

**Steps**:
1. Set viewport to 390x844 (iPhone 14 Pro)
2. Start game and create character
3. Verify character sheet is collapsed by default on mobile
4. Tap toggle to expand
5. Verify full content is visible and scrollable if needed

**Expected Result**:
- Panel is collapsed by default on mobile (<768px)
- Toggle button has 44px+ touch target
- Expanded state shows 2-column stats grid
- Quest objectives are visible and readable

**Screenshot**: `e2e-screenshots/14-charsheet-mobile.png`

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Homepage Load | PASS | All elements render, JS initializes |
| Quest Start | PASS | Narrative streams, choices appear |
| Choice Selection | PASS | Game progresses, turn counter updates |
| Theme Modal | PASS | Opens correctly, all themes listed |
| Theme Switching | PASS | Midnight theme applies immediately |
| Mobile Responsive | PASS | Bottom sheet pattern works |
| Bottom Sheet Expansion | PASS | Expands to show choices |
| Custom Action Input | PASS | Text input functional |
| Quest Selection Flow | PASS | 3 quest options after character creation |
| Quest Activation | PASS | Quest activates, exploration begins |
| Character Sheet Display | PENDING | Stats, HP bar, quest objectives |
| Character Sheet Collapse | PENDING | Toggle, animation, persistence |
| Character Sheet Themes | PENDING | All 4 themes match |
| Character Sheet Mobile | PENDING | Mobile-first, 44px targets |

## Console Messages Observed

```
Pocket Portals initialized
updateChoices called with: [...]
Received choices: [...]
```

## Known Issues

1. **404 on some resources**: Some static resources return 404 (non-critical)
2. **Redis fallback**: Warning about Redis connection, falls back to in-memory sessions

## Running Automated Tests

### Unit Tests (Vitest)
```bash
npm test                 # Run all 468 tests
npm run test:watch       # Watch mode
npm run test:coverage    # With coverage report
```

### E2E Tests (Manual with Playwright MCP)
1. Start the server: `uv run uvicorn src.api.main:app --port 8765`
2. Use Playwright MCP tools to interact with the browser
3. Use `browser_navigate`, `browser_click`, `browser_type`, etc.

## Screenshots Directory

All E2E screenshots are stored in `docs/e2e-screenshots/`:

```
docs/e2e-screenshots/
├── 01-homepage.png
├── 02-quest-started.png
├── 03-turn-2-choices.png
├── 04-theme-modal.png
├── 05-midnight-theme.png
├── 06-mobile-view.png
├── 07-mobile-bottom-sheet-expanded.png
├── 08-custom-input.png
├── 09-quest-selection.png
└── 10-exploration-after-quest-selection.png
```

## Mobile UX Features Tested

- **Haptic Feedback**: Vibration API integration (tested via code review)
- **Touch Targets**: 48px minimum touch targets (WCAG 2.1 AAA)
- **iOS Safe Areas**: `env(safe-area-inset-*)` CSS support
- **Bottom Sheet**: Native-feeling swipe interactions
- **Theme Persistence**: localStorage-based theme memory

## Browser Compatibility

Tested on:
- Chromium (via Playwright)
- Desktop viewport (1280x720)
- Mobile viewport (390x844 - iPhone 14 Pro)

## Future Test Additions

1. Combat system E2E tests (HP changes during combat)
2. New game reset flow (character sheet clears)
3. Error handling scenarios
4. Network failure recovery
5. Accessibility testing (keyboard navigation, screen readers)
6. Quest completion and new quest selection
7. Character sheet real-time HP updates during combat
