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
- `e2e-screenshots/13a-theme-midnight-minimal.png`
- `e2e-screenshots/13b-theme-monospace.png`
- `e2e-screenshots/13c-theme-ios-dark.png`
- `e2e-screenshots/13d-theme-rpg-classic.png`

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

**Screenshots**:
- `e2e-screenshots/14a-mobile-character-sheet.png`
- `e2e-screenshots/14b-mobile-top-view.png`
- `e2e-screenshots/14c-mobile-collapsed.png`

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
| Character Sheet Display | PASS | Stats, HP bar, quest section visible |
| Character Sheet Collapse | PASS | Toggle works, collapsed shows name+HP |
| Character Sheet Themes | PASS | All 4 themes match styling |
| Character Sheet Mobile | PASS | 2-column grid, collapse works |

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
├── 10-exploration-after-quest-selection.png
├── 11-character-sheet.png
├── 12-character-sheet-collapsed.png
├── 13a-theme-midnight-minimal.png
├── 13b-theme-monospace.png
├── 13c-theme-ios-dark.png
├── 13d-theme-rpg-classic.png
├── 14a-mobile-character-sheet.png
├── 14b-mobile-top-view.png
└── 14c-mobile-collapsed.png
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

### 15. Full Game Flow Test (Session Persistence)

**Objective**: Verify complete game flow from start through exploration with CrewAI Flow state persistence.

**Preconditions**:
- Server running with CrewAI Flow-based session management
- Fresh browser session (no existing localStorage)

**Steps**:
1. Navigate to homepage
2. Click "Begin Quest" to start character creation
3. Complete 5 turns of character creation interview:
   - Turn 1: Begin Quest
   - Turn 2: Select character background (e.g., "charming diplomat")
   - Turn 3: Select special ability (e.g., "psychic mediator")
   - Turn 4: Select motivation (e.g., "prevent intergalactic war")
   - Turn 5: Select equipment (e.g., "quantum emotional translation implant")
4. Verify character sheet appears with stats
5. Select a quest from the 3 options presented
6. Enter custom action in text input
7. Click "Act" button to submit
8. Verify narrative response appears
9. Continue for 2-3 more turns

**Expected Result**:
- Turn counter increments correctly (1 → 9+)
- Character sheet displays: name, race, class, level, HP, ability scores
- Quest selection transitions to exploration phase
- Custom actions are processed and generate narrative responses
- State persists across all interactions (CrewAI Flow)
- Session ID visible in header ("Quest: fb261f8b...")

**Console Messages**:
```
Routing: {agents: Array(1), reason: exploration phase}
Received choices: [...]
updateChoices called with: [...]
```

**Verified**: January 10, 2026

---

### 16. Custom Action Input Flow Test

**Objective**: Verify players can type and submit custom actions during gameplay.

**Preconditions**:
- Game in exploration phase (after character creation and quest selection)

**Steps**:
1. Locate the "What do you do?" text input
2. Type a custom action (e.g., "I draw my sword and demand information")
3. Click the "Act" button
4. Wait for narrator response
5. Verify custom action appears in conversation history
6. Verify narrator generates contextual response
7. Verify new choices appear

**Expected Result**:
- Text input accepts any player input
- "Act" button triggers action submission
- Player's exact text appears in story log
- Narrator responds appropriately to custom action
- 3 new contextual choices are generated
- Turn counter increments

**Screenshot**: `e2e-screenshots/16-custom-action-flow.png`

---

### 17. Session State Persistence Test

**Objective**: Verify session state is maintained via CrewAI Flow persistence.

**Preconditions**:
- Server using `GameSessionFlow` with `InMemoryFlowPersistence`

**Steps**:
1. Start new game and note session ID from header
2. Progress through character creation (5 turns)
3. Select a quest
4. Make 2-3 exploration actions
5. Verify state is consistent:
   - Turn counter matches expected value
   - Character sheet data persists
   - Conversation history is maintained
   - Active quest is displayed

**Expected Result**:
- Session ID remains constant throughout
- All state mutations persist via `_save()` pattern
- `GameSessionService` methods correctly read/write state
- No state reset between actions (bug from prior implementation fixed)

**Technical Verification**:
- `GameSessionFlow._save()` called after each mutation
- `InMemoryFlowPersistence.load_state()` returns correct state
- `GameSessionService._get_flow()` reconstructs flow without calling `kickoff_async()` for existing sessions

---

### 18. Multi-Turn Exploration Test

**Objective**: Verify extended gameplay sessions work correctly.

**Preconditions**:
- Game in exploration phase

**Steps**:
1. Make 5+ exploration actions using choice buttons
2. Verify each action:
   - Player action appears in log
   - Narrator responds with narrative
   - New choices are generated
   - Turn counter increments
3. Alternate between choice buttons and custom input
4. Verify conversation history shows all exchanges

**Expected Result**:
- Game handles extended sessions (10+ turns)
- Conversation history maintained (max 20 entries)
- Adventure phase transitions based on turn count:
  - Turns 1-5: SETUP
  - Turns 6-20: RISING_ACTION
  - Turns 21-30: MID_POINT
  - Turns 31-42: CLIMAX
  - Turns 43+: DENOUEMENT
- State remains consistent throughout

---

### 19. New Game Reset Test

**Objective**: Verify "New Game" button resets all state correctly.

**Preconditions**:
- Game in progress with character created and quest active

**Steps**:
1. Click "New Game" button in footer
2. Verify confirmation (if any)
3. Verify page resets to initial state:
   - Turn counter shows "0" or "1"
   - "Begin Quest" button appears
   - Character sheet is hidden or empty
   - Conversation history cleared
   - New session ID generated

**Expected Result**:
- All game state is reset
- New session created with fresh UUID
- localStorage cleared for game state
- User can start new character creation

---

### 20. API Health and Session Creation Test

**Objective**: Verify API endpoints work correctly via browser.

**Preconditions**:
- Server running on port 8000 or 8765

**Steps**:
1. Navigate to `/docs` (Swagger UI)
2. Test `/start` endpoint
3. Verify response includes:
   - `session_id` (UUID format)
   - `phase` (character_creation)
   - `narrative` (welcome text)
   - `choices` (3 options)
4. Test `/action` endpoint with session_id and action
5. Verify response includes updated state

**Expected Result**:
- Swagger UI loads correctly
- `/start` creates new session
- `/action` processes player input
- Responses match `GameState` model schema

**Screenshot**: `e2e-screenshots/20-swagger-api-test.png`

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
| Character Sheet Display | PASS | Stats, HP bar, quest section visible |
| Character Sheet Collapse | PASS | Toggle works, collapsed shows name+HP |
| Character Sheet Themes | PASS | All 4 themes match styling |
| Character Sheet Mobile | PASS | 2-column grid, collapse works |
| **Full Game Flow** | **PASS** | 9+ turns, state persists (Jan 10, 2026) |
| **Custom Action Flow** | **PASS** | Custom input processed correctly |
| **Session Persistence** | **PASS** | CrewAI Flow state management works |
| **Multi-Turn Exploration** | **PASS** | Extended sessions stable |
| New Game Reset | PENDING | Not yet tested |
| API Health | PASS | Swagger UI + endpoints functional |

## Console Messages Observed

```
Pocket Portals initialized
updateChoices called with: [...]
Received choices: [...]
Routing: {agents: Array(1), reason: exploration phase}
```

## Known Issues

1. **404 on some resources**: Some static resources return 404 (non-critical)
2. **Redis fallback**: Warning about Redis connection, falls back to in-memory sessions
3. **Port conflict**: Server may fail if port 8000/8765 already in use

## Running Automated Tests

### Unit Tests (Vitest)
```bash
npm test                 # Run all 468 tests
npm run test:watch       # Watch mode
npm run test:coverage    # With coverage report
```

### Python Tests (pytest)
```bash
pytest tests/            # Run all Python tests
pytest tests/test_game_session_flow.py      # 29 flow tests
pytest tests/test_game_session_service.py   # 26 service tests
```

### E2E Tests (Manual with Playwright MCP)
1. Start the server: `uv run uvicorn src.api.main:app --port 8000`
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
├── 10-exploration-after-quest-selection.png
├── 11-character-sheet.png
├── 12-character-sheet-collapsed.png
├── 13a-theme-midnight-minimal.png
├── 13b-theme-monospace.png
├── 13c-theme-ios-dark.png
├── 13d-theme-rpg-classic.png
├── 14a-mobile-character-sheet.png
├── 14b-mobile-top-view.png
├── 14c-mobile-collapsed.png
├── 16-custom-action-flow.png
└── 20-swagger-api-test.png
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

## Session Management Architecture

### CrewAI Flow Pattern (as of January 2026)

```
GameSessionFlow(Flow[GameState])
    ├── _save() → InMemoryFlowPersistence.save_state()
    ├── set_phase() → _save()
    ├── add_exchange() → _save()
    ├── update_health() → _save()
    └── ... (all mutations call _save())

GameSessionService (async API wrapper)
    ├── create_session() → GameSessionFlow().kickoff_async()
    ├── get_session() → persistence.load_state() → GameState
    └── _get_flow() → reconstruct flow WITHOUT kickoff for existing sessions
```

### State Persistence Flow

1. **New Session**: `create_session()` → `GameSessionFlow()` → `kickoff_async()` → `@start()` → `_save()`
2. **Existing Session**: `_get_flow()` → `load_state()` → `Flow.__init__()` (no kickoff)
3. **Mutations**: Any method → modify `self.state` → `_save()` → persist

## Future Test Additions

1. Combat system E2E tests (HP changes during combat)
2. ~~New game reset flow~~ (Test #19 - pending)
3. Error handling scenarios
4. Network failure recovery
5. Accessibility testing (keyboard navigation, screen readers)
6. Quest completion and new quest selection
7. Character sheet real-time HP updates during combat
8. Session recovery after page refresh
9. Concurrent session isolation testing
