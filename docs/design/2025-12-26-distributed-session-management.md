# Distributed Session Management

**Status:** Superseded (Protocol approach replaced by CrewAI Flow pattern)
**Implementation Date:** 2025-12-26
**Updated:** 2026-01-10
**Related Design Document:** [CrewAI State Management](../design/2025-12-25-crewai-state-management.md)

---

> **📝 UPDATE (2026-01-10)**
>
> The Protocol-based backend approach documented here has been **superseded** by the
> CrewAI Flow-based persistence pattern. The new implementation provides better
> integration with CrewAI's native Flow state management.
>
> **Current Implementation:**
> - `src/engine/game_session.py` - GameSessionFlow using `Flow[GameState]`
> - `src/engine/game_session_service.py` - Async service wrapper for FastAPI
> - `src/engine/flow_persistence.py` - InMemoryFlowPersistence (implements CrewAI FlowPersistence)
>
> **Key Pattern Change:**
> - Old: `SessionBackend.get(id)` → `state` → modify → `SessionBackend.update(id, state)`
> - New: `persistence.load_state(id)` → `Flow(state=..., persistence=...)` → modify → `flow._save()`
>
> See [2026-01-10-crewai-flow-persistence.md](2026-01-10-crewai-flow-persistence.md) for the current design.
>
> The Protocol-based backends (`InMemoryBackend`, `RedisBackend`) remain in the codebase
> for reference but are not the active session management mechanism.

---

## Overview

Pocket Portals uses a pluggable session backend architecture for managing game state. The system supports both in-memory storage for development/testing and Redis for production deployments requiring persistence and horizontal scaling.

**Key Features:**

- Protocol-based backend abstraction for easy extensibility
- Redis as the default backend for both development and production
- Automatic TTL-based session expiration (24 hours)
- Async operations throughout for FastAPI compatibility
- 27 tests validating backend behavior

---

## Architecture

### Backend Protocol

All session backends implement the `SessionBackend` protocol defined in `src/state/backends/base.py`:

```python
@runtime_checkable
class SessionBackend(Protocol):
    async def create(self, session_id: str, state: GameState) -> None: ...
    async def get(self, session_id: str) -> GameState | None: ...
    async def update(self, session_id: str, state: GameState) -> None: ...
    async def delete(self, session_id: str) -> bool: ...
    async def exists(self, session_id: str) -> bool: ...
```

### Available Backends

| Backend | File | Use Case |
|---------|------|----------|
| `RedisBackend` | `src/state/backends/redis.py` | Production and development (default) |
| `InMemoryBackend` | `src/state/backends/memory.py` | Unit testing, single-process deployments |

### Component Diagram

```
+------------------+     +-------------------+     +------------------+
|    FastAPI       | --> | SessionBackend    | --> | RedisBackend     |
|    Endpoints     |     | (Protocol)        |     | or               |
+------------------+     +-------------------+     | InMemoryBackend  |
                                                   +------------------+
                                                            |
                                                            v
                                                   +------------------+
                                                   |     Redis        |
                                                   |  (if enabled)    |
                                                   +------------------+
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_BACKEND` | `redis` | Backend type: `redis` or `memory` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_SESSION_TTL` | `86400` | Session TTL in seconds (24 hours) |

### Settings Class

The configuration is managed through Pydantic settings in `src/config/settings.py`:

```python
class Settings(BaseSettings):
    # Session Backend Configuration
    session_backend: Literal["memory", "redis"] = "redis"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 86400  # 24 hours

    @property
    def is_redis_enabled(self) -> bool:
        return self.session_backend == "redis"
```

---

## Quick Start

### Starting Redis

For local development with Redis (recommended):

```bash
# Start Redis in detached mode
docker-compose up redis -d

# Verify Redis is running
docker exec -it pocket-portals-redis redis-cli ping
# Expected output: PONG
```

### Switching Backends

To use in-memory storage instead of Redis:

```bash
# Option 1: Environment variable
export SESSION_BACKEND=memory

# Option 2: In .env file
SESSION_BACKEND=memory
```

To switch back to Redis:

```bash
export SESSION_BACKEND=redis
```

### Full Development Stack

To run both Redis and the API together:

```bash
# Start all services
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f redis
```

---

## Implementation Details

### RedisBackend

Located at `src/state/backends/redis.py`:

- Uses `redis.asyncio` for non-blocking operations
- Keys are prefixed with `pocket_portals:session:` for namespacing
- Automatic TTL refresh on every update operation
- JSON serialization using Pydantic's `model_dump_json()`

```python
class RedisBackend:
    def __init__(self, redis_url: str, ttl: int = 86400) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl
        self._prefix = "pocket_portals:session:"
```

### InMemoryBackend

Located at `src/state/backends/memory.py`:

- Simple dictionary-based storage
- No persistence across process restarts
- Includes `clear()` method for test cleanup
- Exposes `session_count` property for monitoring

```python
class InMemoryBackend:
    def __init__(self) -> None:
        self._sessions: dict[str, GameState] = {}
```

---

## Testing

### Running Backend Tests

```bash
# Run all backend tests
uv run pytest tests/test_backends.py tests/test_redis_backend.py -v

# Run with coverage
uv run pytest tests/test_backends.py tests/test_redis_backend.py --cov=src/state/backends
```

### Test Coverage

The backend implementation has the following test coverage:

| Module | Coverage |
|--------|----------|
| `src/state/backends/__init__.py` | 100% |
| `src/state/backends/memory.py` | 100% |
| `src/state/backends/redis.py` | 97% |

Total: 27 tests passing

### Using InMemoryBackend in Tests

For unit tests that do not require Redis:

```python
import pytest
from src.state.backends import InMemoryBackend
from src.state.models import GameState

@pytest.fixture
def backend():
    backend = InMemoryBackend()
    yield backend
    backend.clear()

@pytest.mark.asyncio
async def test_session_operations(backend):
    state = GameState(session_id="test-123")
    await backend.create("test-123", state)

    loaded = await backend.get("test-123")
    assert loaded.session_id == "test-123"
```

---

## Docker Configuration

The `docker-compose.yml` includes a production-ready Redis configuration:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: pocket-portals-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

The API service is configured to depend on Redis:

```yaml
  api:
    environment:
      - REDIS_URL=redis://redis:6379/0
      - SESSION_BACKEND=redis
    depends_on:
      redis:
        condition: service_healthy
```

---

## Monitoring and Debugging

### Redis CLI Access

```bash
# Connect to Redis CLI
docker exec -it pocket-portals-redis redis-cli

# List all sessions
KEYS pocket_portals:session:*

# Get a specific session
GET pocket_portals:session:<session-id>

# Check session TTL
TTL pocket_portals:session:<session-id>

# Delete a session manually
DEL pocket_portals:session:<session-id>
```

### Checking Redis Health

```bash
# Via Docker health check
docker inspect pocket-portals-redis --format='{{.State.Health.Status}}'

# Via Redis CLI
docker exec -it pocket-portals-redis redis-cli ping
```

---

## Migration Notes

### From Design Document to Implementation

The implementation follows the design specification from [2025-12-25-crewai-state-management.md](../design/2025-12-25-crewai-state-management.md) with these key decisions:

1. **Backend Protocol**: Uses Python's `Protocol` with `@runtime_checkable` for structural subtyping instead of abstract base class
2. **Default Backend**: Redis is the default for both development and production (not just production)
3. **Key Prefix**: Uses `pocket_portals:session:` namespace instead of simple `session:` prefix
4. **Configuration**: Uses `SESSION_BACKEND` environment variable for backend selection

### File Locations

| Component | Location |
|-----------|----------|
| Protocol Definition | `src/state/backends/base.py` |
| In-Memory Backend | `src/state/backends/memory.py` |
| Redis Backend | `src/state/backends/redis.py` |
| Package Exports | `src/state/backends/__init__.py` |
| Settings | `src/config/settings.py` |
| Docker Config | `docker-compose.yml` |
| Backend Tests | `tests/test_backends.py` |
| Redis Tests | `tests/test_redis_backend.py` |

---

## Troubleshooting

### Redis Connection Refused

```
Error: Connection refused on redis://localhost:6379
```

**Solution:** Ensure Redis is running:
```bash
docker-compose up redis -d
```

### Session Not Found After Restart

**Cause:** Using `InMemoryBackend` which does not persist data.

**Solution:** Switch to Redis backend:
```bash
export SESSION_BACKEND=redis
docker-compose up redis -d
```

### Redis Memory Issues

For long-running deployments, monitor Redis memory:

```bash
docker exec -it pocket-portals-redis redis-cli INFO memory
```

Sessions automatically expire after 24 hours (configurable via `REDIS_SESSION_TTL`).

---

## Future Considerations

1. **Session Migration**: Add tooling to migrate sessions between backends
2. **Clustering**: Redis Cluster support for high availability
3. **Metrics**: Prometheus metrics for session counts and latencies
4. **Compression**: Optional session state compression for large game states

---

**End of Document**
