# Testing with Mocks

This document explains the mocking strategy used in Pocket Portals for testing AI agents without making real API calls.

## Why Mock?

Our agents call external LLM APIs (Anthropic Claude) which:
1. **Cost money** - Each API call incurs charges
2. **Require secrets** - CI environments use dummy API keys
3. **Are slow** - Real API calls take 1-5 seconds each
4. **Are non-deterministic** - Same input can produce different outputs

Mocking solves all these problems by replacing real API calls with predictable fake responses.

## The Pattern

### Before (Real API Call)
```python
def test_keeper_resolve_action_returns_string() -> None:
    keeper = KeeperAgent()
    result = keeper.resolve_action("swing sword")  # Calls real API!
    assert isinstance(result, str)
```

This test:
- ❌ Fails in CI (invalid API key)
- ❌ Costs money on each run
- ❌ Takes 2-3 seconds
- ❌ May fail randomly due to API issues

### After (Mocked)
```python
from unittest.mock import MagicMock, patch

@patch("src.agents.keeper.Task")
def test_keeper_resolve_action_returns_string(mock_task: MagicMock) -> None:
    # Configure the mock
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "14. Hits. 6 damage."
    mock_task.return_value = mock_task_instance

    keeper = KeeperAgent()
    result = keeper.resolve_action("swing sword")  # Uses mock!
    assert isinstance(result, str)
    assert len(result) > 0
```

This test:
- ✅ Works in CI with dummy key
- ✅ Free (no API calls)
- ✅ Runs in milliseconds
- ✅ 100% deterministic

## How It Works

### 1. The `@patch` Decorator

```python
@patch("src.agents.keeper.Task")
def test_something(mock_task: MagicMock) -> None:
    ...
```

This replaces `Task` class in `src.agents.keeper` module with a `MagicMock` object for the duration of the test. The mock is passed as a parameter to the test function.

**Important**: The patch path must match where the class is *used*, not where it's *defined*.

```python
# In src/agents/keeper.py:
from crewai import Task  # Task is imported here

# Correct patch path:
@patch("src.agents.keeper.Task")  # ✅ Where it's used

# Wrong patch path:
@patch("crewai.Task")  # ❌ Where it's defined
```

### 2. MagicMock Objects

`MagicMock` automatically creates attributes and methods as you access them:

```python
mock = MagicMock()
mock.anything.you.want()  # Works!
mock.foo.bar.baz = 42     # Works!
```

### 3. Configuring Return Values

```python
# Simple return value
mock_task_instance = MagicMock()
mock_task_instance.execute_sync.return_value = "14. Hits."

# The mock Task class returns our configured instance
mock_task.return_value = mock_task_instance
```

When the code calls `Task(...).execute_sync()`:
1. `Task(...)` returns `mock_task_instance`
2. `.execute_sync()` returns `"14. Hits."`

## What to Mock

### Mock the Boundary, Not the Internals

```
┌─────────────────────────────────────────────┐
│  Your Code (test this)                      │
│  ┌───────────────┐    ┌──────────────────┐  │
│  │ KeeperAgent   │───▶│ Task.execute_sync│──┼──▶ External API
│  └───────────────┘    └──────────────────┘  │    (mock this)
│                              ▲              │
│                              │              │
│                         Mock here           │
└─────────────────────────────────────────────┘
```

**Good**: Mock `Task` (the boundary to external services)
**Bad**: Mock internal methods of `KeeperAgent`

### Our Agent Architecture

```python
class KeeperAgent:
    def __init__(self):
        self.llm = LLM(...)      # LLM configuration
        self.agent = Agent(...)   # CrewAI agent

    def resolve_action(self, action: str) -> str:
        task = Task(...)          # ← Mock this
        result = task.execute_sync()  # ← This calls the API
        return str(result)
```

We mock `Task` because:
- It's the boundary between our code and CrewAI/Anthropic
- It's where the actual API call happens
- Everything else (`LLM`, `Agent`) is just configuration

## Examples from Our Codebase

### InnkeeperAgent Test

```python
# tests/test_innkeeper.py

@patch("src.agents.innkeeper.Task")
def test_innkeeper_introduce_quest_returns_string(mock_task: MagicMock) -> None:
    """Test that introduce_quest method returns a non-empty string."""
    # Configure mock to return innkeeper-style response
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "Storm's breaking. Roads'll be mud by morning."
    mock_task.return_value = mock_task_instance

    innkeeper = InnkeeperAgent()
    result = innkeeper.introduce_quest("A weary warrior")

    assert isinstance(result, str)
    assert len(result) > 0
```

### JesterAgent Test

```python
# tests/test_jester.py

@patch("src.agents.jester.Task")
def test_jester_add_complication_returns_string(mock_task: MagicMock) -> None:
    """Test that add_complication returns a non-empty string."""
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "Did anyone check if the parrot speaks Common?"
    mock_task.return_value = mock_task_instance

    jester = JesterAgent()
    result = jester.add_complication("Sneaking past guards with a parrot")

    assert isinstance(result, str)
    assert len(result) > 0
```

## Initialization Tests (No Mock Needed)

Some tests don't call the API and don't need mocks:

```python
def test_keeper_initializes() -> None:
    """Test that KeeperAgent initializes when API key is present."""
    keeper = KeeperAgent()

    assert keeper is not None
    assert keeper.agent is not None
    assert keeper.llm is not None
```

This only tests that the agent can be created—no API calls happen during `__init__`.

## Advanced Patterns

### Verifying Mock Was Called

```python
@patch("src.agents.keeper.Task")
def test_keeper_creates_task_correctly(mock_task: MagicMock) -> None:
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "Result"
    mock_task.return_value = mock_task_instance

    keeper = KeeperAgent()
    keeper.resolve_action("attack", difficulty=15)

    # Verify Task was created
    mock_task.assert_called_once()

    # Verify execute_sync was called
    mock_task_instance.execute_sync.assert_called_once()
```

### Multiple Calls

```python
@patch("src.agents.keeper.Task")
def test_multiple_actions(mock_task: MagicMock) -> None:
    mock_task_instance = MagicMock()
    # Different return values for sequential calls
    mock_task_instance.execute_sync.side_effect = [
        "14. Hits.",
        "8. Miss.",
        "20! Critical!"
    ]
    mock_task.return_value = mock_task_instance

    keeper = KeeperAgent()

    r1 = keeper.resolve_action("attack 1")  # "14. Hits."
    r2 = keeper.resolve_action("attack 2")  # "8. Miss."
    r3 = keeper.resolve_action("attack 3")  # "20! Critical!"
```

### Context Manager Style

```python
def test_with_context_manager() -> None:
    with patch("src.agents.keeper.Task") as mock_task:
        mock_instance = MagicMock()
        mock_instance.execute_sync.return_value = "Result"
        mock_task.return_value = mock_instance

        keeper = KeeperAgent()
        result = keeper.resolve_action("test")

        assert result == "Result"

    # Mock is automatically cleaned up after `with` block
```

## Common Mistakes

### 1. Wrong Patch Path

```python
# ❌ Wrong: patching where Task is defined
@patch("crewai.Task")

# ✅ Correct: patching where Task is imported/used
@patch("src.agents.keeper.Task")
```

### 2. Forgetting return_value Chain

```python
# ❌ Wrong: only setting return_value on class
mock_task.return_value = "Result"

# ✅ Correct: setting up the instance that Task() returns
mock_instance = MagicMock()
mock_instance.execute_sync.return_value = "Result"
mock_task.return_value = mock_instance
```

### 3. Mocking Too Deep

```python
# ❌ Wrong: mocking internal implementation details
@patch("src.agents.keeper.KeeperAgent._format_response")

# ✅ Correct: mocking the external boundary
@patch("src.agents.keeper.Task")
```

## When NOT to Mock

1. **Integration tests** - Test real API calls (run locally, not in CI)
2. **Pure functions** - No external dependencies, just test directly
3. **Configuration** - Test that agents initialize correctly

## Summary

| Aspect | Without Mock | With Mock |
|--------|--------------|-----------|
| CI Compatible | ❌ | ✅ |
| Speed | Slow (2-5s) | Fast (ms) |
| Cost | $ per call | Free |
| Deterministic | ❌ | ✅ |
| Tests Real API | ✅ | ❌ |

**Rule of thumb**: Mock external services in unit tests, use real services in integration tests (run locally with real keys).
