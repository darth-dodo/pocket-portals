# Pocket Portals

Solo D&D adventure generator using multi-agent AI.

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

**Spike/One-Turn** - Proving the concept with a single Narrator agent.

See `tasks.md` for current progress and `docs/ONBOARDING.md` for detailed development guide.

## License

MIT
