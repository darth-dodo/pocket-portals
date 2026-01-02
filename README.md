# Pocket Portals

**Solo D&D adventures powered by AI.** Step through the portal and begin your quest.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-415%20passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-96.49%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What It Does

Pocket Portals generates interactive text-based RPG adventures using multiple AI agents. Each agent has a distinct personality and role—the Narrator paints vivid scenes, the Keeper resolves dice rolls, and the Jester adds unexpected twists.

**Try it:** Create a character, explore dungeons, fight monsters, and shape your own story.

## Features

### Dynamic Storytelling
Six specialized AI agents collaborate to create your adventure:
- **Narrator** — Describes scenes and environments with phase-aware pacing
- **Keeper** — Handles D&D 5e rules and dice
- **Jester** — Injects chaos and complications (15% chance per turn)
- **Innkeeper** — Introduces quests and rumors
- **Interviewer** — Guides character creation
- **Epilogue** — Crafts personalized adventure conclusions

### Adventure Pacing
Every adventure follows a 50-turn narrative arc:
- **Setup** (turns 1-5) — Establish world and hook
- **Rising Action** (6-20) — Develop complications
- **Mid Point** (21-30) — Major revelation or shift
- **Climax** (31-42) — Final confrontation
- **Denouement** (43-50) — Resolution and epilogue

### Authentic Combat
Turn-based encounters with real D&D 5e mechanics:
- Initiative rolls determine turn order
- Attack, Defend, or Flee each round
- HP tracking with visual progress bars
- Dramatic battle summaries

### Character Creation
Interactive 5-turn interview builds your hero:
- Choose race, class, and background
- Define motivations and equipment
- Stats generated with proper modifiers
- Personalized adventure hooks

### Real-Time Streaming
Watch your story unfold character by character:
- Typewriter effect for immersion
- Blinking cursor during generation
- No waiting for full responses

### Mobile-First Experience
Optimized for touch devices with native-feeling interactions:
- **Haptic Feedback** — Tactile vibration on button presses (light, medium, snap presets)
- **Touch Targets** — 48px minimum touch areas for comfortable tapping
- **iOS Safe Areas** — Proper spacing for notch and home indicator
- **Responsive Layout** — Seamless experience from mobile to desktop

### Theme System
Five visual themes to match your mood:
- **RPG** — Classic fantasy aesthetic (default)
- **Modern** — Clean contemporary design
- **Midnight** — Dark mode for night sessions
- **Mono** — Minimalist black and white
- **iOS** — Native Apple-inspired look

Themes persist across sessions via localStorage.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/pocket-portals.git
cd pocket-portals
make install

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# Play
make dev
# Open http://localhost:8888
```

## How It Works

```mermaid
flowchart LR
    Player["Player Action"] --> Router["Agent Router"]
    Router --> Agents["AI Agents"]
    Agents --> Story["Narrative + Choices"]
    Story --> Player
```

The system routes each player action to the appropriate agents based on context. Exploration triggers the Narrator. Combat keywords activate the Keeper. The Jester appears randomly to keep things interesting.

**Cost-efficient design:** Combat uses deterministic D&D mechanics (not LLM calls), with AI generating only the battle summary. Result: ~$0.002 per encounter.

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI with SSE streaming |
| AI | CrewAI + Claude 3.5 Haiku |
| State | Redis (production) / Memory (dev) |
| Frontend | NES.css retro aesthetic |
| Testing | Vitest (96.49% coverage) |

## Documentation

| Guide | Description |
|-------|-------------|
| [Architecture](docs/architecture.md) | System design |
| [Onboarding](docs/guides/ONBOARDING.md) | Developer setup |
| [Blueprint](docs/guides/BLUEPRINT.md) | Implementation patterns |

## Development

```bash
make dev          # Start server
make test         # Run Python tests
make lint         # Code quality
make docker-dev   # Start with Redis
```

### JavaScript Test Suite

The frontend includes a comprehensive Vitest test suite with 415 tests and 96.49% code coverage:

```bash
npm test              # Run all 415 tests
npm run test:watch    # Watch mode for development
npm run test:coverage # Generate coverage report
npm run test:ui       # Interactive test UI
```

**Coverage by module:**
| Module | Coverage |
|--------|----------|
| api.js | 99.24% |
| combat.js | 99.38% |
| game-state.js | 100% |
| haptics.js | 100% |
| messages.js | 100% |
| main.js | 98.24% |
| controllers.js | 93.61% |
| themes.js | 80% |

## License

MIT

---

*Built with CrewAI, FastAPI, and Claude*
