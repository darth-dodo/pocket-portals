# Pocket Portals Onboarding

Solo D&D adventure generator with multi-agent AI. Python 3.12 + FastAPI + CrewAI + Claude.

---

## Developer Setup

### Prerequisites

- Python 3.12+
- uv (package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker (optional, for Redis)

### Quick Start

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

### Development Commands

```bash
# Backend Testing (Python)
uv run pytest              # Full suite (296+ tests)
uv run pytest -x           # Stop on first failure
uv run pytest -v           # Verbose

# Frontend Testing (JavaScript)
npm test                   # Run Vitest tests
npm run test:watch         # Watch mode
npm run test:coverage      # With coverage report

# Quality
uv run ruff check src/     # Lint
uv run ruff format src/    # Format
uv run mypy src/           # Type check

# Server
make dev                   # Port 8888
uv run uvicorn src.api.main:app --reload  # Port 8000
```

### Configuration

**.env variables**:
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Required
SESSION_BACKEND=memory        # or redis
REDIS_URL=redis://localhost:6379/0
```

---

## AI Agent Onboarding

### First Steps (Do These In Order)

```bash
# 1. Verify environment works
uv run pytest

# 2. Read current project state
cat tasks.md

# 3. Check git status
git status && git branch

# 4. Create feature branch
git checkout -b feature/your-feature-name

# 5. Verify server runs (optional)
make dev
```

**If any step fails, STOP and fix it before proceeding.**

### Project Structure

```
src/
├── agents/          # AI agents (Narrator, Keeper, Jester, Epilogue)
├── api/             # FastAPI endpoints
├── config/          # YAML agent/task configs
├── engine/          # Game logic (combat, pacing, routing)
├── state/           # Session & state management
└── utils/           # Dice rolling, helpers

static/
├── index.html       # Main web UI
├── css/             # Modular CSS (themes, responsive, combat)
│   ├── themes.css   # 5 themes with CSS custom properties
│   ├── responsive.css  # Mobile-first breakpoints, iOS safe areas
│   └── ...          # Component-specific styles
└── js/
    ├── haptics.js   # Mobile haptic feedback module
    ├── themes.js    # Theme system with localStorage
    ├── combat.js    # Combat UI logic
    ├── __tests__/   # Vitest frontend tests
    └── ...          # Game state, API, controllers

tests/               # Python test suite (296+ tests, 70%+ coverage)
```

### Key Agents

| Agent | Purpose |
|-------|---------|
| **Narrator** | Scene descriptions (no action choices - choices generated separately) |
| **Keeper** | Dice rolls, mechanics, combat resolution |
| **Jester** | Meta-commentary, complications (10% chance) |
| **Interviewer** | Character creation interview flow |
| **Quest Designer** | Generate contextual quests |
| **Epilogue** | Adventure conclusions |

All agents use **Claude 3.5 Haiku** for cost efficiency.

### Adventure Pacing (50-Turn System)

| Phase | Turns | Focus |
|-------|-------|-------|
| SETUP | 1-5 | Establish world, character |
| RISING_ACTION | 6-20 | Build tension, complications |
| MID_POINT | 21-30 | Major revelation, stakes rise |
| CLIMAX | 31-42 | Maximum tension, confrontation |
| DENOUEMENT | 43-50 | Resolution, closure |

**Closure triggers**: Quest complete (after turn 25) OR hard cap (turn 50).

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/start` | GET | New game with starter choices |
| `/character` | POST | Character creation interview |
| `/action` | POST | Player action (SSE streaming) |
| `/combat/start` | POST | Start combat encounter |
| `/combat/action` | POST | Combat action (attack/defend/flee) |

### Git Workflow

```bash
# Always start with
git status && git branch
cat tasks.md

# Create feature branch (never work on main)
git checkout -b feature/your-feature

# Commit format
git commit -m "feat: add X"
git commit -m "fix: resolve Y"
git commit -m "test: add Z tests"
```

### Quality Gates (Before Every Commit)

```bash
# Backend
uv run pytest              # All Python tests pass
uv run ruff check src/     # No lint errors
uv run mypy src/           # No type errors

# Frontend
npm test                   # All JavaScript tests pass
```

Pre-commit hooks run automatically on `git commit`.

**CI/CD**: Both frontend and backend tests run on push/PR to main branch.

### Code Standards & Conventions

**Python Style**:
- Follow existing patterns in `src/` - don't introduce new conventions
- Type hints required on all functions: `def foo(x: str) -> dict[str, Any]:`
- Docstrings: Google style with Args/Returns sections
- Imports: stdlib → third-party → local (ruff enforces this)

**Testing Standards**:
- Minimum 70% coverage (current: 72%)
- Test file naming: `test_<module>.py`
- Use fixtures from `conftest.py` - don't create redundant mocks
- Integration tests mock only external APIs (Anthropic), not internal modules

**Agent Configuration**:
- Agent prompts live in `src/config/agents.yaml` - read before modifying behavior
- Task templates in `src/config/tasks.yaml` - used by CrewAI
- Changes to prompts require testing the full gameplay loop

**Architecture Decisions**:
- Read `docs/adr/` before proposing structural changes
- New patterns require ADR documentation
- State changes go through `GameState` model - no side-channel state

### Maintaining Quality

**Before Pushing**:
```bash
# Backend
uv run pytest                    # All 296+ Python tests pass
uv run ruff check src/ tests/    # Zero lint errors
uv run ruff format src/ tests/   # Consistent formatting
uv run mypy src/                 # No type errors

# Frontend
npm test                         # All JavaScript tests pass
```

**PR Requirements**:
- All quality gates pass (pre-commit hooks enforce this)
- New features include tests
- Breaking changes documented
- Commit messages follow conventional format: `feat:`, `fix:`, `test:`, `docs:`

**Code Review Checklist**:
- [ ] Tests added/updated for changes
- [ ] Type hints on new functions
- [ ] No `# TODO` without linked issue
- [ ] Agent prompts don't leak implementation details
- [ ] State changes properly serializable (Pydantic models)

### Common Pitfalls

| Don't | Do Instead |
|-------|------------|
| Work on main/master | Create feature branch |
| Skip reading tasks.md | Always read it first |
| Make giant commits | Commit every working increment |
| Write code before tests | TDD: test first, then code |
| Leave tests failing | Fix immediately |
| Forget to update tasks.md | Update every 30 minutes |
| Add `# type: ignore` | Fix the type error properly |
| Mock internal modules | Only mock external APIs |
| Change agent prompts blindly | Test full gameplay loop |

### Key Files to Read

1. **tasks.md** - Current project state and priorities
2. **src/api/main.py** - API structure
3. **src/config/agents.yaml** - Agent definitions and prompts
4. **src/config/tasks.yaml** - Task templates
5. **docs/adr/** - Architecture decisions

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Tests fail with API key error | Add `ANTHROPIC_API_KEY` to `.env` |
| Redis connection error | Use `SESSION_BACKEND=memory` or start Redis |
| Port in use | Check `lsof -i :8000` or use different port |
| Import errors | Run `uv sync` to install dependencies |

---

## TL;DR

**Developers**:
```bash
uv sync && cp .env.example .env && make dev
```

**AI Agents**:
```bash
cat tasks.md                    # Read first
git checkout -b feature/name    # Branch
uv run pytest                   # Verify
# ... do work ...
uv run pytest && git commit     # Commit
```

**Remember**: Tests first. Commit often. Update tasks.md.
