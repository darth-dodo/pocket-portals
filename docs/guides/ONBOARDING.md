# Pocket Portals Onboarding

Solo D&D adventure generator with multi-agent AI. Python 3.12 + FastAPI + CrewAI + Claude.

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/darth-dodo/pocket-portals.git
cd pocket-portals
uv sync

# 2. Configure
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

# 3. Run
uv run uvicorn src.api.main:app --reload

# 4. Verify
curl http://localhost:8000/health
```

---

## Project Structure

```
src/
├── agents/          # AI agents (Narrator, Keeper, Jester, Epilogue)
├── api/             # FastAPI endpoints
├── config/          # YAML agent/task configs
├── engine/          # Game logic (combat, pacing, routing)
├── state/           # Session & state management
└── utils/           # Dice rolling, helpers

static/              # Web UI (index.html)
tests/               # Test suite (356 tests, 72% coverage)
```

---

## Key Agents

| Agent | Purpose |
|-------|---------|
| **Narrator** | Scene descriptions (no action choices) |
| **Keeper** | Dice rolls, mechanics, combat |
| **Jester** | Meta-commentary, complications |
| **Interviewer** | Character creation flow |
| **Quest Designer** | Generate quests from context |
| **Epilogue** | Adventure conclusions |

All agents use **Claude 3.5 Haiku** for cost efficiency.

---

## Adventure Pacing (50-Turn System)

| Phase | Turns | Focus |
|-------|-------|-------|
| SETUP | 1-5 | Establish world, character |
| RISING_ACTION | 6-20 | Build tension, complications |
| MID_POINT | 21-30 | Major revelation, stakes rise |
| CLIMAX | 31-42 | Maximum tension, confrontation |
| DENOUEMENT | 43-50 | Resolution, closure |

**Closure triggers**: Quest complete (after turn 25) OR hard cap (turn 50).

---

## Development Commands

```bash
# Testing
uv run pytest              # Full suite
uv run pytest -x           # Stop on first failure
uv run pytest -v           # Verbose

# Quality
uv run ruff check src/     # Lint
uv run ruff format src/    # Format
uv run mypy src/           # Type check

# Server
make dev                   # Port 8888
uv run uvicorn src.api.main:app --reload  # Port 8000
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/start` | GET | New game with starter choices |
| `/character` | POST | Character creation interview |
| `/action` | POST | Player action (SSE streaming) |
| `/combat/start` | POST | Start combat encounter |
| `/combat/action` | POST | Combat action (attack/defend/flee) |

---

## Configuration

**.env variables**:
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Required
SESSION_BACKEND=memory        # or redis
REDIS_URL=redis://localhost:6379/0
```

**Agent configs**: `src/config/agents.yaml`
**Task configs**: `src/config/tasks.yaml`

---

## Git Workflow

```bash
# Always start with
git status && git branch
cat tasks.md

# Create feature branch
git checkout -b feature/your-feature

# Commit format
git commit -m "feat: add X"
git commit -m "fix: resolve Y"
git commit -m "test: add Z tests"
```

**Branch types**: `feature/`, `fix/`, `hotfix/`, `spike/`

---

## Quality Gates

Before committing:
```bash
uv run pytest              # All tests pass
uv run ruff check src/     # No lint errors
uv run mypy src/           # No type errors
```

Pre-commit hooks handle formatting automatically.

---

## Testing

```bash
# Run specific test file
uv run pytest tests/test_api.py -v

# Run specific test
uv run pytest tests/test_api.py::test_health -v

# Coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

Current: **356 tests, 72% coverage**

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Tests fail with API key error | Add `ANTHROPIC_API_KEY` to `.env` |
| Redis connection error | Use `SESSION_BACKEND=memory` or start Redis |
| Port in use | Check `lsof -i :8000` or use different port |
| Import errors | Run `uv sync` to install dependencies |

---

## Key Files to Read

1. `tasks.md` - Current project state and priorities
2. `src/api/main.py` - API structure
3. `src/config/agents.yaml` - Agent definitions
4. `docs/adr/` - Architecture decisions

---

## TL;DR

```bash
uv sync                    # Install
cp .env.example .env       # Configure (add API key)
uv run pytest              # Test
make dev                   # Run
```

**Remember**: Tests first. Commit often. Update tasks.md.
