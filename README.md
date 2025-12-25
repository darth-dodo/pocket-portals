# Pocket Portals

Solo D&D adventure generator using multi-agent AI.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
  - [Local Development](#local-development)
  - [Docker (Alternative)](#docker-alternative)
- [API](#api)
  - [Health Check](#health-check)
  - [Generate Narrative](#generate-narrative)
  - [Response Format](#response-format)
- [Stack](#stack)
- [Project Structure](#project-structure)
- [Development](#development)
- [Docker](#docker)
- [Deployment](#deployment)
- [Current Phase](#current-phase)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

Pocket Portals uses CrewAI agents powered by Anthropic Claude to generate immersive, dynamic D&D narratives. Each agent plays a specialized role in crafting the adventure experience.

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run development server
make dev

# Run tests
make test
```

### Docker (Alternative)

```bash
# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Build and run
make docker-build
make docker-run

# View at http://localhost:8888
```

## API

### Health Check
```bash
curl http://localhost:8888/health
```

### Start Adventure
```bash
curl http://localhost:8888/start
```

### Generate Narrative
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

## Stack

- **Python 3.12** - Runtime
- **FastAPI** - API framework with Server-Sent Events (SSE) for streaming
- **CrewAI** - Agent orchestration
- **Anthropic Claude Haiku** (claude-3-5-haiku-20241022) - LLM provider for all agents

## Project Structure

```
src/
├── api/main.py          # FastAPI endpoints
├── agents/
│   ├── narrator.py      # NarratorAgent - scene descriptions
│   ├── innkeeper.py     # InnkeeperAgent - quest introductions
│   ├── keeper.py        # KeeperAgent - game mechanics
│   └── jester.py        # JesterAgent - meta-commentary
└── config/
    ├── agents.yaml      # Agent definitions
    ├── tasks.yaml       # Task templates
    └── loader.py        # Pydantic config models
```

## Development

```bash
make dev      # Start server (port 8888)
make test     # Run pytest with coverage
make lint     # Run ruff check + format
```

## Docker

### Build Image
```bash
make docker-build
```

### Run Container
```bash
# Production mode
make docker-run

# Development mode with hot reload
make docker-dev
```

### Container Management
```bash
# View logs
make docker-logs

# Stop container
make docker-stop

# Clean up
make docker-clean
```

### Notes
- Container runs on port 8888 (mapped to host)
- Environment variables loaded from `.env` file
- Development mode mounts source code for hot reload
- Production mode uses optimized multi-stage build

## Deployment

### Render

The project includes a `render.yaml` blueprint for easy deployment to Render.com:

- **Platform**: Render Web Service
- **Runtime**: Python 3.12
- **Build**: Standard pip installation
- **Start**: Uvicorn ASGI server on port 8888

Set `ANTHROPIC_API_KEY` in Render environment variables before deploying.

## Current Phase

**Multi-Agent Crew** - Four agents working together: Narrator, Innkeeper, Keeper, and Jester.

- ✅ 36 tests passing, 79% coverage
- ✅ CI/CD with GitHub Actions
- ✅ Pre-commit hooks (ruff, mypy)
- ✅ Character-by-character streaming with typewriter effect
- ✅ Session context with character sheet persistence
- ✅ Mobile-optimized UI with improved readability

### Recent Features

**Streaming Experience**
- Character-by-character streaming for all agent responses
- Animated blinking cursor during content generation
- Server-Sent Events (SSE) for real-time updates

**Character Persistence**
- Session context now includes character details (name, race, class, background)
- Improved narrative continuity across multi-turn adventures
- Character info displayed in UI during gameplay

**Mobile Improvements**
- Larger fonts for better readability (18px base)
- Touch-friendly button sizing (min 44px height)
- Safe area insets for modern mobile devices
- Improved spacing and visual hierarchy

**Character Creation**
- Fixed custom input flow for race, class, and background
- Smooth transitions between selection and custom entry
- Validation and error handling

See `tasks.md` for current progress and `docs/guides/ONBOARDING.md` for detailed development guide.

## Documentation

| Document | Description |
|----------|-------------|
| [Crash Course](docs/guides/CRASH-COURSE.md) | Comprehensive spike documentation |
| [Onboarding Guide](docs/guides/ONBOARDING.md) | Getting started for developers |
| [Product Requirements](docs/product.md) | PRD and feature specifications |
| [Architecture](docs/reference/architecture.md) | Technical architecture and XP practices |
| [Design System](docs/design/design.md) | UI design system and components |

## License

MIT
