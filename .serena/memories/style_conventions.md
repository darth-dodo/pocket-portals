# Pocket Portals - Code Style & Conventions

## Python Style

### General
- **Python Version**: 3.11+ (targeting 3.12)
- **Line Length**: 88 characters (ruff default)
- **Import Sorting**: isort rules via ruff, first-party = `src`

### Type Hints
- **Required**: All functions must have type hints (mypy strict mode)
- **Return Types**: Always specify return types
- **Optional**: Use `X | None` syntax (Python 3.10+), not `Optional[X]`

```python
def get_session(session_id: str | None) -> tuple[str, list[dict[str, str]]]:
    """Get existing session or create new one."""
```

### Docstrings
- Use docstrings for all public classes and functions
- Format: Google style (brief description, Args, Returns)

```python
def respond(self, action: str, context: str = "") -> str:
    """Generate narrative response to player action.

    Args:
        action: The player's action
        context: Optional conversation history for continuity
    """
```

### Naming Conventions
- **Functions/Variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Files**: snake_case.py

### Pydantic Models
- Use Pydantic v2 syntax (`model_validator(mode="after")`)
- Use `Field()` for validation and defaults

```python
class ActionRequest(BaseModel):
    """Request model for player actions."""
    action: str | None = Field(default=None)
    choice_index: int | None = Field(default=None, ge=1, le=3)
```

## Testing Style

### Test Organization
- Tests in `tests/` directory
- Test file naming: `test_<module>.py`
- Test function naming: `test_<what>_<condition>` or `test_<what>_<expected_result>`

```python
def test_health_endpoint_returns_200(client: TestClient) -> None:
def test_action_endpoint_validates_request_schema(client: TestClient) -> None:
```

### Fixtures
- Use pytest fixtures for shared setup
- Type hint fixture returns

```python
@pytest.fixture
def client() -> TestClient:
    """Create test client for API."""
    return TestClient(app)
```

## Linting Rules (ruff)
- E: pycodestyle errors
- W: pycodestyle warnings
- F: pyflakes
- I: isort
- B: flake8-bugbear
- C4: flake8-comprehensions
- UP: pyupgrade

## XP Principles Applied
1. **TDD**: Write failing test first, then implement
2. **Simple Design**: Simplest solution that works
3. **YAGNI**: Don't build speculative features
4. **Small Commits**: Frequent, incremental commits
