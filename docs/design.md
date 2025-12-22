# Pocket Portals Design System

**Version**: 1.0
**Last Updated**: 2025-12-21

---

## 1. Design Philosophy

### 1.1 Vision

Pocket Portals evokes the nostalgia of 8-bit RPG adventures while maintaining modern usability standards. The design balances **retro authenticity** with **readability** and **accessibility**.

### 1.2 Core Principles

| Principle | Description |
|-----------|-------------|
| **Nostalgic Immersion** | Transport players to the golden age of text adventures and 8-bit RPGs |
| **Readability First** | Despite pixel aesthetics, text must be comfortable to read for extended sessions |
| **Clear Hierarchy** | Distinct visual separation between narrator, player, and UI elements |
| **Responsive Adventure** | Seamless experience from desktop to mobile |
| **Accessible Fantasy** | WCAG-conscious design without sacrificing theme |

### 1.3 Design Mood

```
Dark Fantasy + Retro Gaming + Tavern Warmth
```

The UI should feel like reading a magical tome in a candlelit tavern, rendered through an 8-bit lens.

---

## 2. Color Palette

### 2.1 Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Gold** | `#f7d354` | 247, 211, 84 | Titles, narrator labels, highlights, icons |
| **Gold Dark** | `#c9a227` | 201, 162, 39 | Text shadows, gold accents |
| **Green** | `#92cc41` | 146, 204, 65 | Player actions, success states, CTA buttons |
| **Green Dark** | `#6b9e32` | 107, 158, 50 | Green gradients, shadows |
| **Blue** | `#209cee` | 32, 156, 238 | Links, input section, secondary actions |

### 2.2 Background Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Void** | `#0d0d1a` | Deepest background layer |
| **Night** | `#1a1a2e` | Primary dark background |
| **Charcoal** | `#212529` | Container backgrounds |
| **Midnight** | `#16213e` | Gradient accents |
| **Navy** | `#0f3460` | Bottom gradient glow |

### 2.3 Text Colors

| Name | Hex | Usage |
|------|-----|-------|
| **White** | `#e8e8e8` | Narrator text (primary reading) |
| **Silver** | `#adafbc` | Secondary text, footer, muted content |
| **Border** | `#444444` | Borders, dividers, scrollbar tracks |

### 2.4 Semantic Colors

| State | Color | Hex |
|-------|-------|-----|
| Success | Green | `#92cc41` |
| Error | NES Red | `#e76e55` |
| Warning | Gold | `#f7d354` |
| Info | Blue | `#209cee` |

### 2.5 Background Gradients

```css
/* Main body gradient */
background-image:
    radial-gradient(ellipse at top, #1a1a2e 0%, transparent 50%),
    radial-gradient(ellipse at bottom, #16213e 0%, transparent 50%),
    linear-gradient(180deg, #0d0d1a 0%, #1a1a2e 50%, #0f3460 100%);

/* Story box gradient */
background: linear-gradient(180deg, #1a1a2e 0%, #212529 100%);

/* Session bar gradient */
background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);

/* Scrollbar thumb gradient */
background: linear-gradient(180deg, #92cc41 0%, #6b9e32 100%);
```

---

## 3. Typography

### 3.1 Font Stack

| Role | Font | Fallback |
|------|------|----------|
| **Primary** | Press Start 2P | cursive |

```css
font-family: 'Press Start 2P', cursive;
```

**Source**: Google Fonts
**CDN**: `https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap`

### 3.2 Type Scale

| Element | Size | Line Height | Letter Spacing |
|---------|------|-------------|----------------|
| Title (h1) | 1.8rem | 1.2 | 2px |
| Title Mobile | 1.2rem | 1.2 | 2px |
| Heading (h2) | 1rem | 1.4 | 1px |
| Subtitle | 0.65rem | 1.4 | 1px |
| Body Text | 0.75rem | 2.2 | 0.03em |
| Body Mobile | 0.65rem | 2.0 | 0.03em |
| Labels | 0.55rem | 1.4 | normal |
| Small/Footer | 0.45rem | 1.4 | normal |
| Buttons | 0.6rem | 1.2 | normal |

### 3.3 Text Shadows

```css
/* Gold title shadow (3D effect) */
text-shadow:
    4px 4px 0 #c9a227,
    -1px -1px 0 #000,
    1px -1px 0 #000,
    -1px 1px 0 #000,
    1px 1px 0 #000;

/* Subtle gold shadow */
text-shadow: 2px 2px 0 #c9a227;

/* Icon shadow */
text-shadow: 3px 3px 0 #c9a227;
```

---

## 4. Spacing System

### 4.1 Base Unit

**Base**: 4px

### 4.2 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Icon gaps, small margins |
| `--space-3` | 12px | Button padding, row gaps |
| `--space-4` | 16px | Section padding, message padding |
| `--space-5` | 20px | Container padding |
| `--space-6` | 24px | Large margins, message spacing |
| `--space-8` | 32px | Section separation |
| `--space-10` | 40px | Welcome section padding |

### 4.3 Component Spacing

| Component | Padding | Margin |
|-----------|---------|--------|
| Container | - | 0 auto |
| Header | 16px | 0 0 24px 0 |
| Story Box | 24px | 0 |
| Message | 16px | 0 0 24px 0 |
| Choices Section | 20px | 20px 0 0 0 |
| Input Section | 20px | 20px 0 0 0 |
| Session Bar | 16px 20px | 20px 0 0 0 |
| Footer | 16px | 24px 0 0 0 |

---

## 5. Layout

### 5.1 Container

```css
.container {
    max-width: 900px;
    margin: 0 auto;
}
```

### 5.2 Grid Structure

```
┌─────────────────────────────────────┐
│            HEADER                   │
│    Title + Subtitle (centered)      │
├─────────────────────────────────────┤
│        GAME CONTAINER               │
│  ┌───────────────────────────────┐  │
│  │         STORY BOX             │  │
│  │    (scrollable, 350-450px)    │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │      CHOICES SECTION          │  │
│  │    (3 choice buttons)         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │       INPUT SECTION           │  │
│  │    [input field] [Act btn]    │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│          SESSION BAR                │
│   Quest ID          [New Game]      │
├─────────────────────────────────────┤
│            FOOTER                   │
└─────────────────────────────────────┘
```

### 5.3 Responsive Breakpoints

| Breakpoint | Max Width | Adjustments |
|------------|-----------|-------------|
| Desktop | > 600px | Full layout |
| Mobile | <= 600px | Stacked input, smaller text, reduced heights |

---

## 6. Components

### 6.1 Message Cards

**Narrator Message**
```css
.message-narrator {
    color: #e8e8e8;
    background: rgba(15, 52, 96, 0.3);
    border-left: 4px solid #f7d354;
    padding: 16px;
    border-radius: 8px;
}
```

**Player Message**
```css
.message-player {
    color: #92cc41;
    background: rgba(146, 204, 65, 0.1);
    border-left: 4px solid #92cc41;
    padding: 16px;
    border-radius: 8px;
}
```

### 6.2 Buttons

**Primary (Begin Quest)**
- Class: `nes-btn is-primary`
- Color: Green background
- Shadow: `0 4px 0 #1e6c28`
- Hover: translateY(-2px), shadow grows

**Choice Buttons**
- Class: `nes-btn choice-btn`
- Full width, left-aligned
- Hover: translateX(8px), gold left shadow

**Action Button**
- Class: `nes-btn is-success`
- Compact padding for input row

**Danger Button (New Game)**
- Class: `nes-btn is-error`
- Small font size (0.45rem)

### 6.3 Input Field

```css
.nes-input.is-dark {
    font-size: 0.6rem;
    padding: 12px;
}
```

### 6.4 Sections

**Choices Section**
```css
.choices-section {
    background: rgba(26, 26, 46, 0.5);
    border: 2px dashed #444;
    border-radius: 8px;
    padding: 20px;
}
```

**Input Section**
```css
.input-section {
    background: rgba(32, 156, 238, 0.1);
    border: 2px dashed #444;
    border-radius: 8px;
    padding: 20px;
}
```

### 6.5 Custom Scrollbar

```css
::-webkit-scrollbar { width: 14px; }
::-webkit-scrollbar-track {
    background: #1a1a2e;
    border: 3px solid #444;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #92cc41 0%, #6b9e32 100%);
    border: 3px solid #444;
    border-radius: 4px;
}
```

---

## 7. Iconography

### 7.1 Icon Library

**RPG Awesome** - Fantasy-themed icon set
**CDN**: `https://cdn.jsdelivr.net/npm/rpg-awesome@0.2.0/css/rpg-awesome.min.css`

### 7.2 Icon Usage

| Context | Icon | Class |
|---------|------|-------|
| Title | Door | `ra ra-door-open` |
| Subtitle | Swords | `ra ra-crossed-swords` |
| Welcome | Scroll | `ra ra-scroll-unfurled` |
| Begin Quest | Player | `ra ra-player-lift` |
| Loading | Crystal Ball | `ra ra-crystal-ball` |
| Choices Label | Forge | `ra ra-forging` |
| Choice 1 | Axe | `ra ra-axe` |
| Choice 2 | Speech | `ra ra-speech-bubble` |
| Choice 3 | Boot | `ra ra-boot-stomp` |
| Input Label | Quill | `ra ra-quill-ink` |
| Act Button | Lightning | `ra ra-lightning-bolt` |
| Session | Player | `ra ra-player` |
| New Game | Cycle | `ra ra-cycle` |
| Footer | Dragon | `ra ra-dragon` |
| Narrator Label | Scroll | `ra ra-scroll-unfurled` |
| Player Label | Player | `ra ra-player` |

### 7.3 Icon Sizing

| Context | Size |
|---------|------|
| Welcome Hero | 4rem (2.5rem mobile) |
| Loading | 2rem |
| Section Labels | 1rem |
| Inline Icons | 0.8rem |
| Footer | 1.5rem |

---

## 8. Animation

### 8.1 Keyframes

**Fade In (Messages)**
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
/* Duration: 0.4s, Easing: ease-out */
```

**Pulse (Loading, CTA)**
```css
@keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}
/* Duration: 1.5-2s, Easing: ease-in-out, Infinite */
```

**Bounce (Loading Icon)**
```css
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
}
/* Duration: 0.6s, Easing: ease-in-out, Infinite */
```

### 8.2 Transitions

| Element | Property | Duration | Easing |
|---------|----------|----------|--------|
| Choice buttons | all | 0.2s | ease |
| Links | color | 0.2s | ease |
| Begin button hover | transform, box-shadow | default | default |

### 8.3 Hover Effects

**Choice Button**
```css
.choice-btn:hover {
    transform: translateX(8px);
    box-shadow: -4px 0 0 #f7d354;
}
```

**Begin Button**
```css
.begin-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 0 #1e6c28;
}
```

---

## 9. States

### 9.1 Loading State

- Loading overlay appears with crystal ball icon
- Bouncing animation on icon
- Pulsing text: "The narrator consults the fates..."
- All interactive elements disabled

### 9.2 Error State

- Red NES container with error message
- Auto-dismisses after 5 seconds
- Appears below story box

### 9.3 Empty State (Welcome)

- Centered layout
- Large scroll icon
- "Welcome, Adventurer!" heading
- Pulsing "Begin Quest" CTA

### 9.4 Active Game State

- Story box shows message history
- Choices section visible with 3 options
- Input section always available
- Session bar shows quest ID

---

## 10. Accessibility

### 10.1 Color Contrast

| Pair | Ratio | Status |
|------|-------|--------|
| White (#e8e8e8) on Dark (#1a1a2e) | ~12:1 | Pass AAA |
| Gold (#f7d354) on Dark (#212529) | ~9:1 | Pass AAA |
| Green (#92cc41) on Dark (#212529) | ~8:1 | Pass AAA |

### 10.2 Focus States

- Inherits NES.css focus styles
- Visible focus rings on all interactive elements

### 10.3 Keyboard Navigation

- Tab order: Begin Quest → Choices → Input → Act → New Game
- Enter key submits input
- All buttons keyboard accessible

### 10.4 Screen Reader Considerations

- Semantic HTML structure
- Labels on form inputs
- ARIA attributes inherited from NES.css

---

## 11. Dependencies

### 11.1 External Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| NES.css | 2.3.0 | 8-bit UI framework |
| Press Start 2P | - | Pixel font |
| RPG Awesome | 0.2.0 | Fantasy icons |

### 11.2 CDN Links

```html
<!-- NES.css -->
<link href="https://unpkg.com/nes.css@2.3.0/css/nes.min.css" rel="stylesheet" />

<!-- Press Start 2P -->
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">

<!-- RPG Awesome -->
<link href="https://cdn.jsdelivr.net/npm/rpg-awesome@0.2.0/css/rpg-awesome.min.css" rel="stylesheet">
```

---

## 12. Design Tokens (Future CSS Variables)

```css
:root {
    /* Colors */
    --color-gold: #f7d354;
    --color-gold-dark: #c9a227;
    --color-green: #92cc41;
    --color-green-dark: #6b9e32;
    --color-blue: #209cee;

    /* Backgrounds */
    --bg-void: #0d0d1a;
    --bg-night: #1a1a2e;
    --bg-charcoal: #212529;
    --bg-midnight: #16213e;
    --bg-navy: #0f3460;

    /* Text */
    --text-primary: #e8e8e8;
    --text-secondary: #adafbc;
    --text-border: #444444;

    /* Typography */
    --font-family: 'Press Start 2P', cursive;
    --font-size-title: 1.8rem;
    --font-size-body: 0.75rem;
    --font-size-small: 0.55rem;
    --line-height-body: 2.2;

    /* Spacing */
    --space-unit: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 40px;

    /* Borders */
    --border-radius: 8px;
    --border-width: 4px;

    /* Animation */
    --transition-fast: 0.2s ease;
    --transition-normal: 0.4s ease-out;
}
```

---

## 13. Future Considerations

### 13.1 Planned Enhancements

- [ ] Dark/Light theme toggle (maintain retro feel)
- [ ] Sound effects integration
- [ ] Achievement badges UI
- [ ] Character portrait display
- [ ] Inventory panel design
- [ ] Map/location indicator
- [ ] Combat UI states

### 13.2 Design Debt

- Consider extracting CSS to separate stylesheet
- Implement CSS custom properties for theming
- Add loading skeleton states
- Optimize font loading (font-display: swap)

---

## 14. Assets

### 14.1 Required Assets

Currently no custom assets - all visual elements are CSS-based or icon fonts.

### 14.2 Potential Future Assets

- Custom pixel art logo
- Character sprite sheets
- Location background tiles
- Item icons

---

*This design system is a living document. Updates should be reflected here as the UI evolves.*
