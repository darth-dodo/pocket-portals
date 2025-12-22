# Pocket Portals - Project Overview

## Purpose
Solo D&D adventure generator using multi-agent AI. Uses CrewAI agents powered by Anthropic Claude to generate immersive, dynamic D&D narratives.

## Current Phase
**Spike/One-Turn** - Proving the concept with a single Narrator agent.

## Tech Stack
- **Runtime**: Python 3.12
- **API Framework**: FastAPI
- **Agent Orchestration**: CrewAI
- **LLM Provider**: Anthropic Claude (claude-sonnet-4-20250514)
- **Package Manager**: uv (with pip compatibility)
- **Build System**: hatchling
- **Testing**: pytest, pytest-cov, pytest-asyncio
- **Linting/Formatting**: ruff
- **Type Checking**: mypy (strict mode)
- **Pre-commit Hooks**: pre-commit

## Project Structure
```
pocket-portals/
├── src/
│   ├── api/main.py          # FastAPI endpoints
│   ├── agents/narrator.py   # NarratorAgent (CrewAI)
│   ├── config/
│   │   ├── agents.yaml      # Agent definitions
│   │   └── tasks.yaml       # Task templates
│   └── settings.py          # Application settings
├── tests/
│   └── test_api.py          # API tests
├── static/                   # Web UI (NES.css styling)
├── docs/                     # Documentation
│   ├── guides/              # ONBOARDING.md, CRASH-COURSE.md
│   ├── design/              # Design docs
│   ├── reference/           # Technical references
│   └── adr/                 # Architecture decision records
├── .agentic-framework/      # Workflow and quality gate definitions
├── pyproject.toml           # Python project config
├── Makefile                 # Development commands
├── Dockerfile               # Container build
├── docker-compose.yml       # Container orchestration
└── render.yaml              # Render.com deployment
```

## Key Features (Completed)
- FastAPI app with `/health`, `/start`, and `/action` endpoints
- NarratorAgent using CrewAI + Anthropic Claude
- Session management for multi-user support
- YAML-based agent configuration
- Conversation context passing to LLM
- Choice system (3 options + free text input)
- Starter choices with shuffle from pool of 9 adventure hooks
- Retro RPG web UI with NES.css styling
- Docker containerization

## Environment Variables
- `ANTHROPIC_API_KEY` - Required for LLM calls
- `ENVIRONMENT` - development/production (affects CORS)
- `LOG_LEVEL` - Logging verbosity
