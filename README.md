# Pocket Portals

Solo D&D adventure generator using multi-agent AI. Step through the portal and begin your quest.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
- [Architecture](#architecture)
  - [Multi-Agent System](#multi-agent-system)
  - [Session Management](#session-management)
  - [Combat System](#combat-system)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

Pocket Portals uses CrewAI agents powered by Anthropic Claude to generate immersive, dynamic D&D narratives. Each agent plays a specialized role in crafting the adventure experience, from character creation to combat encounters.

**Tech Stack:**
- **Python 3.12** - Runtime
- **FastAPI** - API framework with Server-Sent Events (SSE) for streaming
- **CrewAI** - Multi-agent orchestration
- **Anthropic Claude Haiku** (claude-3-5-haiku-20241022) - Cost-efficient LLM for all agents
- **Redis** - Distributed session storage (with in-memory fallback)
- **NES.css** - Retro RPG-styled frontend

---

## Features

### D&D 5e Combat System
Turn-based combat with authentic D&D 5e mechanics:
- Initiative-based turn order (d20 + DEX modifier)
- Attack, Defend, and Flee actions with real dice rolling
- HP tracking with visual progress bars
- Dramatic narrative summaries at battle conclusion
- Cost-efficient design (~$0.002 per combat encounter)

### Distributed Session Management
Redis-backed sessions with automatic fallback:
- Persistent game state across browser sessions
- 24-hour session TTL (configurable)
- Graceful degradation to in-memory storage
- Character sheet persistence throughout adventures

### Real-Time Streaming
Character-by-character narrative delivery:
- Server-Sent Events (SSE) for real-time updates
- Animated blinking cursor during content generation
- Typewriter effect for immersive storytelling

### Character Creation
Interactive character builder:
- Race, class, and background selection
- Custom input support for personalized characters
- D&D 5e stat generation and modifiers
- Contextual adventure hooks based on character choices

### Mobile-First Design
Optimized for adventuring on the go:
- Larger fonts for readability (18px base)
- Touch-friendly button sizing (min 44px height)
- Safe area insets for modern mobile devices
- NES.css retro RPG aesthetic

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker and Docker Compose (optional, for Redis)
- Anthropic API key

### Local Development

```bash
# Clone and enter the dungeon
git clone https://github.com/yourusername/pocket-portals.git
cd pocket-portals

# Install dependencies with uv
make install

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Start the adventure (uses in-memory sessions)
make dev

# View at http://localhost:8888
```

### Docker Compose (Recommended)

Docker Compose provides Redis for distributed session management:

```bash
# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Start all services (API + Redis)
make docker-dev

# View at http://localhost:8888
# API docs at http://localhost:8888/docs
```

**Docker Commands:**
```bash
make docker-dev      # Start with hot reload
make docker-down     # Stop services
make docker-logs     # View logs
make docker-clean    # Remove containers and volumes
```

---

## Architecture

### Multi-Agent System

Pocket Portals uses a crew of specialized AI agents, each with a distinct role:

| Agent | Role | Description |
|-------|------|-------------|
| **Narrator** | Scene descriptions | Paints vivid scenes and describes the world |
| **Keeper** | Game mechanics | Resolves actions with D&D 5e rules and dice |
| **Jester** | Meta-commentary | Adds humor, complications, and unexpected twists |
| **Innkeeper** | Quest introduction | Provides rumors, quests, and adventure hooks |
| **Character Interviewer** | Character creation | Guides players through character building |

All agents use Claude Haiku for cost-efficient generation while maintaining narrative quality.

### Session Management

The session system uses a pluggable backend architecture:

```
SessionBackend (Protocol)
    |
    +-- InMemoryBackend (default fallback)
    |       - Simple dict-based storage
    |       - No persistence across restarts
    |
    +-- RedisBackend (production)
            - Distributed session storage
            - Configurable TTL (default: 24 hours)
            - Automatic reconnection handling
```

**Backend Selection:**
1. If `SESSION_BACKEND=redis` and Redis is available: Use Redis
2. Otherwise: Fall back to in-memory storage with a warning

### Combat System

D&D 5e-inspired turn-based combat:

```
Combat Flow:
1. Encounter triggered by narrative
2. Initiative rolled (d20 + DEX modifier)
3. Turn order established
4. Player chooses: Attack / Defend / Flee
5. Dice resolved, HP updated
6. Repeat until victory, defeat, or escape
7. LLM generates battle summary
```

**Cost Efficiency:**
- Combat uses pre-computed mechanics, not LLM calls
- Only the final battle summary requires an LLM call
- Average combat cost: ~$0.002 per encounter

---

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `SESSION_BACKEND` | `redis` | Session storage: `redis` or `memory` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_SESSION_TTL` | `86400` | Session TTL in seconds (24 hours) |
| `ENVIRONMENT` | `development` | Environment mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

---

## API Reference

### Health Check
```bash
curl http://localhost:8888/health
```

### Start Adventure
```bash
curl http://localhost:8888/start
```

### Player Action
```bash
# New session
curl -X POST http://localhost:8888/action \
  -H "Content-Type: application/json" \
  -d '{"action": "I enter the dark tavern"}'

# Continue session
curl -X POST http://localhost:8888/action \
  -H "Content-Type: application/json" \
  -d '{"action": "I order an ale", "session_id": "your-session-id"}'
```

### Agent Endpoints
```bash
# Innkeeper - Quest introduction
curl "http://localhost:8888/innkeeper/quest?character=A%20weary%20dwarf%20warrior"

# Keeper - Resolve game mechanics
curl -X POST http://localhost:8888/keeper/resolve \
  -H "Content-Type: application/json" \
  -d '{"action": "swing sword at goblin", "difficulty": 12}'

# Jester - Add complication
curl -X POST http://localhost:8888/jester/complicate \
  -H "Content-Type: application/json" \
  -d '{"situation": "The party is searching for treasure"}'
```

### Response Format
```json
{
  "narrative": "The tavern keeper nods...",
  "session_id": "abc123-def456-ghi789",
  "choices": ["Investigate further", "Talk to someone nearby", "Move to a new location"]
}
```

---

## Project Structure

```
pocket-portals/
+-- src/
|   +-- api/
|   |   +-- main.py              # FastAPI endpoints and SSE streaming
|   +-- agents/
|   |   +-- narrator.py          # NarratorAgent - scene descriptions
|   |   +-- innkeeper.py         # InnkeeperAgent - quest introductions
|   |   +-- keeper.py            # KeeperAgent - game mechanics
|   |   +-- jester.py            # JesterAgent - meta-commentary
|   |   +-- character_interviewer.py  # Character creation flow
|   +-- engine/
|   |   +-- combat_manager.py    # D&D 5e combat system
|   |   +-- flow.py              # Adventure flow orchestration
|   |   +-- router.py            # Action routing logic
|   |   +-- executor.py          # Action execution
|   +-- state/
|   |   +-- models.py            # Pydantic models (GameState, CombatState)
|   |   +-- session_manager.py   # Session orchestration
|   |   +-- character.py         # CharacterSheet model
|   |   +-- backends/
|   |       +-- base.py          # SessionBackend protocol
|   |       +-- memory.py        # InMemoryBackend
|   |       +-- redis.py         # RedisBackend
|   +-- config/
|   |   +-- agents.yaml          # Agent definitions
|   |   +-- tasks.yaml           # Task templates
|   |   +-- loader.py            # Pydantic config models
|   +-- data/
|   |   +-- enemies.py           # Enemy templates
|   +-- utils/
|       +-- dice.py              # Dice rolling utilities
+-- static/
|   +-- index.html               # NES.css retro frontend
+-- tests/                       # 280+ test cases
+-- docs/                        # Documentation
+-- docker-compose.yml           # Redis + API services
+-- Dockerfile                   # Multi-stage build
+-- Makefile                     # Development commands
+-- pyproject.toml               # uv/pip dependencies
```

---

## Development

### Commands

```bash
# Setup
make install          # Install dependencies with uv + pre-commit hooks

# Development
make dev              # Start server (port 8888)
make dev-reload       # Start with auto-reload

# Testing (TDD workflow)
make test             # Run all tests with coverage
make test-fast        # Stop on first failure
make test-cov         # Generate HTML coverage report

# Quality
make lint             # Check code style (ruff)
make format           # Auto-fix code style
make check            # Run all quality gates

# Docker
make docker-dev       # Start API + Redis with hot reload
make docker-down      # Stop services
make docker-clean     # Remove containers and volumes
```

### Pre-commit Hooks

Pre-commit hooks are installed automatically with `make install`:
- **ruff** - Linting and formatting
- **mypy** - Type checking

### TDD Workflow

```
1. RED:    Write failing test      -> make test-fast (should fail)
2. GREEN:  Write minimal code      -> make test-fast (should pass)
3. REFACTOR: Clean up code         -> make test (should still pass)
4. COMMIT: Run quality gates       -> make check && git commit
```

---

## Deployment

### Render

The project includes a `render.yaml` blueprint for deployment to Render.com:

1. Set `ANTHROPIC_API_KEY` in Render environment variables
2. For Redis: Add a Redis service or use Render's managed Redis
3. Set `REDIS_URL` to your Redis instance URL

### Docker Production

```bash
# Build production image
make docker-build

# Run container
docker run -d \
  --name pocket-portals \
  -p 8888:8888 \
  -e ANTHROPIC_API_KEY=your-key \
  -e SESSION_BACKEND=memory \
  pocket-portals:latest
```

---

## Current Status

**Phase: Multi-Agent Combat System**

- 280+ tests passing
- Pre-commit hooks (ruff, mypy)
- CI/CD with GitHub Actions
- Character-by-character streaming
- D&D 5e combat mechanics
- Redis session management

---

## Documentation

| Document | Description |
|----------|-------------|
| [Crash Course](docs/guides/CRASH-COURSE.md) | Comprehensive spike documentation |
| [Onboarding Guide](docs/guides/ONBOARDING.md) | Getting started for developers |
| [Product Requirements](docs/product.md) | PRD and feature specifications |
| [Architecture](docs/reference/architecture.md) | Technical architecture and XP practices |
| [Design System](docs/design/design.md) | UI design system and components |

---

## License

MIT
