# Combat UI Visual Guide

## Combat HUD States and Layouts

### Desktop View (1920x1080)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                   ┌─────────────┐│
│  POCKET PORTALS                                   │  COMBAT     ││
│  Solo D&D Adventure                               │  ─────────  ││
│                                                   │             ││
│  ┌─────────────────────────────────────┐         │ 🗡️ Hero     ││
│  │                                     │         │ 👹 Goblin   ││← Initiative
│  │  Story Area                         │         │             ││  Tracker
│  │                                     │         │ You         ││
│  │  Narrator: A goblin appears!        │         │ ████░░ 8/10 ││← Player HP
│  │                                     │         │             ││
│  │  Keeper: Roll initiative!           │         │ Goblin      ││
│  │                                     │         │ ███░░░ 3/7  ││← Enemy HP
│  │                                     │         │             ││
│  └─────────────────────────────────────┘         │ [⚔️ Attack] ││
│                                                   │ [🛡️ Defend] ││← Actions
│  Choices:                                         │ [🏃 Flee]   ││
│  [Explore forest] [Check inventory]              │             ││
│                                                   │ 🎲          ││← Dice
│  Input: What do you do?  [Submit]                │ 1d20+3 = 15 ││  Display
│                                                   └─────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
      │
      │ HUD positioned: top-right, 280px width
      │ Z-index: 100 (always on top)
      │ Background: Dark NES.css container
      └─ Fixed position (follows scroll)
```

---

### Mobile View (375x667)

```
┌─────────────────────────┐
│ POCKET PORTALS          │
│ Solo D&D Adventure      │
│                         │
│ ┌─────────────────────┐ │
│ │                     │ │
│ │  Story Area         │ │
│ │                     │ │
│ │  A goblin appears!  │ │
│ │                     │ │
│ │  Roll initiative!   │ │
│ │                     │ │
│ └─────────────────────┘ │
│                         │
│ (Story scrolls here)    │
│                         │
│                         │
├─────────────────────────┤← Combat HUD
│ ⚔️ COMBAT               │  (bottom fixed)
│ ─────────────           │
│ 🗡️ Hero  👹 Goblin     │
│                         │
│ You                     │
│ ████░░ 8/10             │
│                         │
│ Goblin                  │
│ ███░░░ 3/7              │
│                         │
│ [⚔️Attack] [🛡️Defend]  │
│ [🏃 Flee]               │
│                         │
│ 🎲 1d20+3 = 15          │
└─────────────────────────┘
```

---

## HUD Element Breakdown

### 1. Initiative Tracker

```
┌─────────────────┐
│ ⚔️ COMBAT       │← Title (0.6rem, gold color)
│ ───────────     │
│                 │
│ 🗡️ Hero        │← Current player (highlighted green)
│ 👹 Goblin      │← Next in order
│                 │
└─────────────────┘
```

**Active Turn State:**
```css
.active-turn {
  background: #92cc41;  /* Green */
  color: #000;          /* Black text */
  font-weight: bold;
}
```

---

### 2. HP Progress Bars

```
┌─────────────────┐
│ You             │← Label (0.5rem, gold)
│ ████████░░      │← Progress bar (green)
│          20/20  │← HP text (overlaid)
│                 │
│ Goblin          │← Enemy name (dynamic)
│ ████░░░░░░      │← Progress bar (red)
│           7/7   │← HP text
└─────────────────┘
```

**Colors:**
- Player HP: `nes-progress is-success` (green)
- Enemy HP: `nes-progress is-error` (red)
- Text overlay: Black on bars for contrast

---

### 3. Action Buttons

```
┌─────────────────┐
│ [⚔️ Attack]     │← Red button (is-error)
│ [🛡️ Defend]     │← Blue button (is-primary)
│ [🏃 Flee]       │← Yellow button (is-warning)
└─────────────────┘
```

**Button States:**
- **Enabled**: Player's turn, clickable
- **Disabled**: Enemy's turn, greyed out
- **Hover**: Slight scale effect (desktop)
- **Active**: Pressed state

---

### 4. Dice Display

```
┌─────────────────┐
│       🎲        │← Spinning animation
│   1d20+3 = 15   │← Roll notation + result
└─────────────────┘
```

**Animation Sequence:**
1. Show dice icon
2. Spin 360° (0.3s)
3. Display result text
4. Auto-hide after 2s

**Notation Examples:**
- Attack: `1d20+3 = 15`
- Damage: `1d8+2 = 7`
- Flee: `1d20+2 = 14`

---

## State Transitions

### Combat Start

```
Normal View          →    Combat View
┌────────────┐           ┌────────────┐
│            │           │            │
│  Story     │           │  Story     │
│            │           │            │
│            │           │  HUD       │
│  Input     │           │  ░░░░░░    │← HUD appears
└────────────┘           └────────────┘
```

### Turn Change

```
Player Turn                Enemy Turn
┌────────────┐            ┌────────────┐
│ 🗡️ Hero ← │            │ 🗡️ Hero    │
│ 👹 Goblin  │            │ 👹 Goblin← │← Highlight moves
│            │            │            │
│ [Attack]   │← Enabled  │ [Attack]   │← Disabled
└────────────┘            └────────────┘
```

### Combat End

```
Combat Active        →    Combat Ended
┌────────────┐           ┌────────────┐
│  HUD       │           │            │
│  ░░░░░░    │           │  Story     │
│  [Attack]  │           │  Victory!  │
└────────────┘           └────────────┘
                         │            │
                         └────────────┘
                              ↑
                         HUD hides after 2s
```

---

## Color Palette

### HUD Colors
```css
--hud-background: #212529       /* Dark grey */
--hud-border: #444              /* Medium grey */
--title-color: #f7d354          /* Gold */
--player-color: #92cc41         /* Green */
--enemy-color: #e76e55          /* Red */
--active-highlight: #92cc41     /* Green */
--dice-result: #f7d354          /* Gold */
```

### Button Colors
```css
--attack-button: #e76e55        /* Red (is-error) */
--defend-button: #209cee        /* Blue (is-primary) */
--flee-button: #f7d51d          /* Yellow (is-warning) */
```

---

## Typography

### Font Sizes
```css
.combat-hud {
  /* Desktop */
  h4: 0.6rem;              /* Title */
  li: 0.5rem;              /* Initiative */
  label: 0.5rem;           /* HP labels */
  button: 0.5rem;          /* Actions */
  .dice-result: 0.5rem;    /* Dice */
}

@media (max-width: 768px) {
  /* Mobile */
  button: 0.6rem;          /* Larger touch targets */
}
```

### Font Family
- Primary: `Press Start 2P` (retro pixel font)
- Fallback: `cursive`

---

## Animations

### 1. HUD Show/Hide
```css
/* Show */
.combat-hud {
  display: none;
}
.combat-hud.active {
  display: block;
}
```

### 2. Dice Spin
```css
@keyframes dice-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dice-icon {
  animation: dice-spin 0.3s ease-out;
}
```

### 3. HP Bar Update
```html
<progress value="8" max="10"></progress>
<!-- Browser handles smooth transition -->
```

---

## Responsive Breakpoints

### Desktop (> 768px)
- HUD: Top-right, 280px width
- Buttons: 3 columns, flexible width
- Font: 0.5rem base

### Tablet (768px)
- HUD: Top-right, full width available
- Buttons: 3 columns, larger touch targets
- Font: 0.6rem buttons

### Mobile (< 768px)
- HUD: Bottom fixed, 100% width
- Buttons: 3 columns, full width
- Font: 0.6rem buttons

### Small Mobile (< 380px)
- HUD: Bottom, compact padding
- Buttons: Stacked or wrapped
- Font: 0.45rem labels

---

## Accessibility Features

### Semantic HTML
```html
<progress class="nes-progress"
          value="8"
          max="10"
          aria-label="Player health">
</progress>
```

### Keyboard Navigation
- Tab through buttons
- Enter to activate
- Focus indicators visible

### Screen Reader
- HP values announced
- Button labels clear
- Turn state communicated

### Color Contrast
- All text meets WCAG AA
- HP bars distinguishable
- Active states clear

---

## Example: Complete Combat Flow

```
1. COMBAT START
   ┌──────────────┐
   │ ⚔️ COMBAT    │
   │ 🗡️ Hero      │ ← Player goes first (initiative 15)
   │ 👹 Goblin    │
   │ You: 20/20   │
   │ Goblin: 7/7  │
   │ [Actions]    │ ← Buttons enabled
   └──────────────┘

2. PLAYER ATTACKS
   Click [⚔️ Attack]
   ┌──────────────┐
   │ 🎲           │ ← Dice animation
   │ 1d20+3 = 15  │ ← Attack roll
   └──────────────┘

   Story: "1d20+3=15 vs AC 13. Hit! 1d8+3=7 damage."

3. HUD UPDATES
   ┌──────────────┐
   │ 🗡️ Hero      │
   │ 👹 Goblin    │ ← Enemy turn now
   │ You: 20/20   │
   │ Goblin: 0/7  │ ← HP reduced
   │ [Actions]    │ ← Disabled
   └──────────────┘

4. COMBAT ENDS (Enemy HP = 0)
   Story: "Victory! The goblin falls."

   ┌──────────────┐
   │ [HUD fades]  │ ← 2 second delay
   └──────────────┘

   Normal gameplay resumes.
```

---

## Developer Notes

### DOM IDs
- `#combat-hud` - Main container
- `#turn-order-list` - Initiative tracker `<ul>`
- `#player-hp-bar` - Player `<progress>`
- `#player-hp-text` - Player HP text
- `#enemy-hp-bar` - Enemy `<progress>`
- `#enemy-hp-text` - Enemy HP text
- `#enemy-name-label` - Enemy name
- `#dice-display` - Dice container
- `#dice-result-text` - Dice result text

### JavaScript State
```javascript
combatState = {
  is_active: bool,
  phase: 'player_turn' | 'enemy_turn',
  round_number: int,
  combatants: [...],
  turn_order: [...],
  current_turn_index: int
}
```

### Event Handlers
- `executeCombatAction('attack')` - Player action
- `showCombatHUD(state)` - Display HUD
- `hideCombatHUD()` - Hide HUD
- `updateCombatHUD(state)` - Refresh display

---

## Testing Checklist

Visual elements to verify:
- [ ] HUD appears in correct position (desktop/mobile)
- [ ] Turn order shows correct combatants
- [ ] Active turn is highlighted green
- [ ] HP bars show correct values
- [ ] HP text overlays correctly
- [ ] Action buttons are properly sized
- [ ] Dice animation plays smoothly
- [ ] Dice result text is readable
- [ ] HUD hides after combat ends
- [ ] All colors match theme
- [ ] Typography is consistent
- [ ] Mobile layout doesn't overlap content

---

This visual guide provides a comprehensive reference for understanding the Combat UI layout, states, and behavior across different screen sizes.
