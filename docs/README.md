# Pocket Portals Documentation

Technical documentation for the multi-agent AI adventure system.

## Quick Navigation

| Guide | Description |
|-------|-------------|
| [Onboarding](guides/ONBOARDING.md) | Developer setup and workflow |
| [Architecture](architecture.md) | System design and patterns |
| [Blueprint](guides/BLUEPRINT.md) | Comprehensive implementation guide |
| [Crews & Flows](guides/CREWS-AND-FLOWS.md) | CrewAI patterns and agent orchestration |
| [Quest System](design/quest-system.md) | Quest design and selection flow |
| [E2E Testing](playwright-e2e-suite.md) | Playwright test scenarios |

## Documentation Structure

```
docs/
├── README.md                    # This index
├── architecture.md              # System architecture (65K)
├── architecture-diagrams.md     # Visual system diagrams
├── product.md                   # Product requirements
├── improvements.md              # Enhancement backlog
│
├── guides/
│   ├── ONBOARDING.md           # Developer quickstart
│   ├── BLUEPRINT.md            # Implementation reference
│   ├── CREWS-AND-FLOWS.md      # CrewAI patterns
│   └── CRASH-COURSE.md         # Original spike docs
│
├── reference/
│   ├── conversation-engine.md  # Turn mechanics
│   ├── creative-writing.md     # Narrative guidelines
│   ├── testing-mocks.md        # LLM mocking strategy
│   └── xp.md                   # XP methodology
│
├── design/
│   ├── quest-system.md         # Quest generation & selection
│   ├── choice-system.md        # Choice mechanics
│   ├── conversation-context.md # Context management
│   ├── mobile-ux-improvement-plan.md  # Mobile UX design
│   └── 2025-12-*.md            # Design documents
│
├── e2e-screenshots/            # Playwright test screenshots
│
├── adr/
│   └── 001-agent-service-pattern.md
│
└── api/
    └── insomnia-collection.json
```

## Key Concepts

### Multi-Agent Architecture

Six specialized agents coordinate to generate adventures:

| Agent | Role | When Invoked |
|-------|------|--------------|
| Narrator | Scene descriptions | Every turn |
| Keeper | D&D 5e mechanics | Combat/skill checks |
| Jester | Chaos injection | 15% probability |
| Innkeeper | Quest hooks | Session start |
| Interviewer | Character creation | First 5 turns |
| QuestDesigner | Quest generation | Quest selection phase |

### Game Flow

```
CHARACTER_CREATION (5 turns) → QUEST_SELECTION (3 options) → EXPLORATION → Combat/Quest Complete → Loop
```

### Hybrid Design Pattern

- **LLM for narrative**: Rich, contextual storytelling
- **Deterministic combat**: D&D 5e rules, real dice
- **Result**: 25x cost reduction, instant mechanics

### Session Management

```mermaid
graph TD
    A[SessionBackend Protocol] --> B[InMemoryBackend]
    A --> C[RedisBackend]
    B --> D[Development]
    C --> E[Production]
```

## For New Contributors

1. **Start with [Onboarding](guides/ONBOARDING.md)** - Environment setup
2. **Read [Architecture](architecture.md)** - System overview
3. **Review [Blueprint](guides/BLUEPRINT.md)** - Implementation details

## Project Status

- **Backend**: 408 Python tests passing (pytest)
- **Frontend**: 415 Vitest + jsdom tests
- **Coverage**: 77% overall
- **Pre-commit hooks** enforced (ruff, mypy)
- **CI/CD**: Frontend and backend tests run on push/PR to main
- **E2E Testing**: Playwright MCP for browser automation

---

*Updated January 2, 2026*
