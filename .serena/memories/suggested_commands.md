# Pocket Portals - Development Commands

## Quick Reference

### Setup
```bash
make install          # Install dependencies with uv + pre-commit hooks
cp .env.example .env  # Set up environment, add ANTHROPIC_API_KEY
```

### Development Server
```bash
make dev              # Run FastAPI server (port 8888)
make dev-reload       # Run with auto-reload for development
```

### Testing (TDD Workflow)
```bash
make test             # Full test suite with coverage
make test-fast        # Stop on first failure (TDD red/green cycle)
make test-cov         # Generate HTML coverage report
uv run pytest -x -v   # Run tests, stop on first failure
uv run pytest tests/test_api.py::test_name  # Run specific test
```

### Quality Gates
```bash
make lint             # Check code style (ruff check + format check)
make format           # Auto-fix code style
make check            # Run all quality gates (lint + test)
uv run mypy src/      # Type checking (optional, configured but not in CI)
```

### Docker
```bash
make docker-build     # Build Docker image
make docker-run       # Run container (detached, port 8888)
make docker-dev       # Run with docker-compose (hot reload)
make docker-logs      # View container logs
make docker-stop      # Stop and remove container
make docker-clean     # Remove images and containers
```

### Cleanup
```bash
make clean            # Remove build artifacts (__pycache__, .pytest_cache, etc.)
```

### Git Workflow
```bash
git status && git branch   # Always check status first
git checkout -b feature/name  # Create feature branch
git add . && git commit -m "feat: description"  # Commit frequently
```

## API Testing
```bash
# Health check
curl http://localhost:8888/health

# Start new adventure
curl http://localhost:8888/start

# Start with shuffled choices
curl "http://localhost:8888/start?shuffle=true"

# Submit action
curl -X POST http://localhost:8888/action \
  -H "Content-Type: application/json" \
  -d '{"action": "I enter the tavern"}'

# Continue session
curl -X POST http://localhost:8888/action \
  -H "Content-Type: application/json" \
  -d '{"choice_index": 2, "session_id": "your-session-id"}'
```

## Interactive API Docs
- Swagger UI: http://localhost:8888/docs
- ReDoc: http://localhost:8888/redoc

## System Commands (Darwin/macOS)
- `ls`, `cd`, `pwd` - Standard navigation
- `git` - Version control
- `open htmlcov/index.html` - Open coverage report in browser
