# Pocket Portals

Solo D&D adventure generator using multi-agent AI.

## Overview

Pocket Portals uses CrewAI agents powered by Anthropic Claude to generate immersive, dynamic D&D narratives. Each agent plays a specialized role in crafting the adventure experience.

## Quick Start

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

## API

### Health Check
```bash
curl http://localhost:8888/health
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

### Response Format
```json
{
  "narrative": "The tavern keeper nods...",
  "session_id": "abc123-def456-ghi789"
}
```

## Stack

- **Python 3.12** - Runtime
- **FastAPI** - API framework
- **CrewAI** - Agent orchestration
- **Anthropic Claude** - LLM provider

## Project Structure

```
src/
├── api/main.py          # FastAPI endpoints
├── agents/narrator.py   # NarratorAgent (CrewAI)
└── config/
    ├── agents.yaml      # Agent definitions
    └── tasks.yaml       # Task templates
```

## Development

```bash
make dev      # Start server (port 8888)
make test     # Run pytest with coverage
make lint     # Run ruff check + format
```

## Current Phase

**Spike/One-Turn** - Proving the concept with a single Narrator agent.

See `tasks.md` for current progress and `docs/ONBOARDING.md` for detailed development guide.

## License

MIT
