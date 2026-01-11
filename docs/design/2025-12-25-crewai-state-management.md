# CrewAI State Management Refactor Design

**Date:** 2025-12-25
**Status:** ⚠️ SUPERSEDED
**Related Requirements:** Session Persistence, Scalability, Agent Memory
**Dependencies:** CrewAI 0.95+, Redis 7.0+, Pydantic 2.0+
**Implementation Reference:** [Distributed Session Management](../coordination/distributed-session-management.md)

---

> **⚠️ DEPRECATION NOTICE (2026-01-10)**
>
> This design document has been **superseded** by the CrewAI Flow-based persistence implementation.
>
> **New Implementation:**
> - Design Doc: [2026-01-10-crewai-flow-persistence.md](2026-01-10-crewai-flow-persistence.md)
> - Core Files:
>   - `src/engine/game_session.py` - GameSessionFlow with `_save()` pattern
>   - `src/engine/game_session_service.py` - Async service wrapper
>   - `src/engine/flow_persistence.py` - InMemoryFlowPersistence
>
> **Key Differences from This Design:**
> - Uses CrewAI's native `Flow[GameState]` instead of Protocol-based backends
> - Uses `FlowPersistence` interface instead of custom `SessionBackend` protocol
> - Flow reconstruction pattern instead of direct backend access
> - `_save()` helper for automatic persistence after mutations
>
> The SessionBackend Protocol and backend implementations described below remain
> available but are not the primary session management approach going forward.

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| SessionBackend Protocol | Complete | `src/state/backends/base.py` |
| InMemoryBackend | Complete | `src/state/backends/memory.py` |
| RedisBackend | Complete | `src/state/backends/redis.py` |
| Settings Configuration | Complete | `src/config/settings.py` |
| Docker Compose | Complete | Redis service configured |
| Tests | Complete | 29 tests passing |
| GameFlow Refactor | Pending | Existing flow.py still in use |
| Agent Memory | Pending | Not yet implemented |
| API Updates | Pending | Using existing session_manager.py |

---

## Implementation Notes (2025-12-26)

### Completed Components

#### 1. SessionBackend Protocol (`src/state/backends/base.py`)

The protocol defines five async methods using `typing.Protocol` with `@runtime_checkable`:
- `create(session_id, state)` - Create new session
- `get(session_id)` - Retrieve session or None
- `update(session_id, state)` - Update existing session
- `delete(session_id)` - Delete session, returns bool
- `exists(session_id)` - Check session existence

#### 2. InMemoryBackend (`src/state/backends/memory.py`)

Development and testing backend with:
- Simple dict-based storage (`_sessions: dict[str, GameState]`)
- Additional utility methods: `clear()`, `session_count` property
- No persistence across restarts (by design)

#### 3. RedisBackend (`src/state/backends/redis.py`)

Production-ready implementation with:
- **Async client**: `redis.asyncio` for non-blocking I/O
- **TTL expiration**: 24 hours default (86400 seconds), configurable
- **Key prefix**: `pocket_portals:session:` namespace
- **JSON serialization**: Uses Pydantic's `model_dump_json()` and `model_validate_json()`
- **Connection management**: `close()` method for cleanup

#### 4. Settings Configuration (`src/config/settings.py`)

Uses `pydantic-settings` with:
- `redis_url`: Default `redis://localhost:6379/0`
- `redis_session_ttl`: Default 86400 (24 hours)
- `session_backend`: Literal["memory", "redis"], default "redis"
- `is_redis_enabled` property for conditional logic
- Environment variable support via `.env` file

#### 5. Docker Compose (`docker-compose.yml`)

Redis service configuration:
- Image: `redis:7-alpine`
- Persistent volume: `redis-data` with AOF enabled
- Health check: `redis-cli ping`
- Network: `pocket-portals-network` for service isolation
- API depends on Redis with `condition: service_healthy`

#### 6. Test Coverage

Two test files with 29 total tests:
- `tests/test_backends.py` (18 tests): InMemoryBackend, SessionBackend protocol, GameState serialization
- `tests/test_redis_backend.py` (11 tests): RedisBackend with fakeredis

Tests use `fakeredis.aioredis` to avoid requiring a real Redis instance.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_SESSION_TTL` | `86400` | Session TTL in seconds |
| `SESSION_BACKEND` | `redis` | Backend type (memory or redis) |

### File Structure

```
src/
  config/
    settings.py          # Pydantic settings with Redis config
  state/
    backends/
      __init__.py        # Exports SessionBackend, InMemoryBackend, RedisBackend
      base.py            # SessionBackend Protocol
      memory.py          # InMemoryBackend class
      redis.py           # RedisBackend class
tests/
  test_backends.py       # InMemoryBackend + protocol + serialization tests
  test_redis_backend.py  # RedisBackend tests with fakeredis
```

### Remaining Work

1. **GameFlow Refactor**: Port `src/engine/flow.py` to use new backend system
2. **API Updates**: Update `src/api/main.py` to use backend factory
3. **Agent Memory**: Implement CrewAI memory configuration
4. **Legacy Cleanup**: Remove `src/state/session_manager.py` after migration

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Current State Analysis](#2-current-state-analysis)
- [3. Target Architecture](#3-target-architecture)
- [4. Unified State Model](#4-unified-state-model)
- [5. Redis Session Store](#5-redis-session-store)
- [6. GameFlow Implementation](#6-gameflow-implementation)
- [7. Agent Memory Configuration](#7-agent-memory-configuration)
- [8. API Updates](#8-api-updates)
- [9. Files to Delete](#9-files-to-delete)
- [10. Testing Requirements](#10-testing-requirements)
- [11. Implementation Tasks](#11-implementation-tasks)

---

## 1. Executive Summary

Replace the manual `SessionManager` with Redis-backed session persistence integrated with CrewAI Flow. This enables horizontal scaling, session TTL, and distributed deployments.

**What Changes:**
- Delete `SessionManager` class entirely
- Delete `ConversationFlowState` model
- Create unified `GameState` model
- Create `RedisSessionStore` for persistence
- Create `GameFlow` using Redis store
- Add agent memory for narrative continuity

**What Stays the Same:**
- Public API endpoints (`/action`, `/session/new`, `/stream`)
- Frontend behavior
- Agent definitions and tasks

**Why Redis:**
- Horizontal scaling across multiple instances
- Built-in TTL for automatic session expiration
- Sub-millisecond read/write latency
- Production-ready for distributed deployments
- Pub/sub for future real-time features

---

## 2. Current State Analysis

### 2.1 Current Architecture (To Be Replaced)

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│   FastAPI    │────▶│  SessionManager  │────▶│   GameState    │
│   Endpoints  │     │  (in-memory dict)│     │   (Pydantic)   │
└──────────────┘     └──────────────────┘     └────────────────┘
        │
        ▼
┌──────────────────┐     ┌─────────────────────┐
│ ConversationFlow │────▶│ ConversationFlowState│
│   (CrewAI Flow)  │     │     (Pydantic)       │
└──────────────────┘     └─────────────────────┘
```

### 2.2 Problems Being Solved

| Problem | Current | After |
|---------|---------|-------|
| No persistence | Sessions lost on restart | Redis with TTL |
| Single instance only | In-memory dict | Distributed Redis |
| Dual state models | GameState + FlowState | Single unified GameState |
| Manual sync | Copy data between models | Direct state access |
| No session cleanup | Sessions accumulate forever | Redis TTL expiration |
| No agent memory | Agents forget everything | CrewAI memory system |

---

## 3. Target Architecture

```
┌──────────────┐     ┌─────────────────────────────────────┐
│   FastAPI    │────▶│           GameFlow                  │
│   Endpoints  │     │   Flow[GameState]                   │
└──────────────┘     │                                     │
                     │  ┌───────────────────────────────┐  │
                     │  │         GameState             │  │
                     │  │  (single source of truth)     │  │
                     │  └───────────────────────────────┘  │
                     │                 │                   │
                     │                 ▼                   │
                     │  ┌───────────────────────────────┐  │
                     │  │      RedisSessionStore        │  │
                     │  │  - JSON serialization         │  │
                     │  │  - TTL: 24 hours              │  │
                     │  │  - Key: session:{id}          │  │
                     │  └───────────────────────────────┘  │
                     └─────────────────────────────────────┘
                                       │
                                       ▼
                     ┌─────────────────────────────────────┐
                     │              Redis                  │
                     │  - Session state storage            │
                     │  - Automatic expiration             │
                     │  - Multi-instance support           │
                     └─────────────────────────────────────┘
                                       │
                                       ▼
                     ┌─────────────────────────────────────┐
                     │         Crew with Memory            │
                     │  - short_term_memory (conversation) │
                     │  - entity_memory (characters/NPCs)  │
                     └─────────────────────────────────────┘
```

---

## 4. Unified State Model

### 4.1 New Model

Update `src/state/models.py` to replace the existing `GameState`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from src.state.models import GamePhase, CombatState
from src.state.character import CharacterSheet


class GameState(BaseModel):
    """Single state model for game session and flow execution.

    Replaces both the old GameState and ConversationFlowState.
    Serialized to JSON and stored in Redis.
    """

    # === Session ===
    session_id: str = ""

    # === Character ===
    character_description: str = ""
    character_sheet: CharacterSheet | None = None

    # === Health ===
    health_current: int = 20
    health_max: int = 20

    # === Phase ===
    phase: GamePhase = GamePhase.CHARACTER_CREATION
    creation_turn: int = Field(default=0, ge=0, le=5)

    # === Combat ===
    combat_state: CombatState | None = None

    # === Conversation ===
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    current_choices: list[str] = Field(default_factory=list)

    # === Agent Tracking ===
    recent_agents: list[str] = Field(default_factory=list)
    turns_since_jester: int = 0

    # === Flow Execution ===
    current_action: str = ""
    current_context: str = ""
    active_agents: list[str] = Field(default_factory=list)
    agent_responses: dict[str, str] = Field(default_factory=dict)
    final_narrative: str = ""

    @property
    def has_character(self) -> bool:
        return self.character_sheet is not None

    @property
    def is_in_combat(self) -> bool:
        return self.combat_state is not None and self.combat_state.is_active

    @field_validator("character_sheet", mode="before")
    @classmethod
    def validate_character_sheet(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            from src.state.character import CharacterSheet
            return CharacterSheet(**v)
        return v

    @field_validator("health_current")
    @classmethod
    def health_not_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("health_current cannot be negative")
        return v

    @model_validator(mode="after")
    def health_within_max(self) -> GameState:
        if self.health_current > self.health_max:
            raise ValueError("health_current cannot exceed health_max")
        return self
```

---

## 5. Redis Session Store

### 5.1 Configuration

Add to `src/config/settings.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 86400  # 24 hours

    class Config:
        env_file = ".env"
        env_prefix = "POCKET_PORTALS_"


settings = Settings()
```

Add to `.env`:

```bash
POCKET_PORTALS_REDIS_URL=redis://localhost:6379/0
POCKET_PORTALS_SESSION_TTL_SECONDS=86400
```

### 5.2 Redis Store Implementation

Create `src/state/redis_store.py`:

```python
from __future__ import annotations

import json
from typing import TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from src.config.settings import settings
from src.state.models import GameState


T = TypeVar("T", bound=BaseModel)


class RedisSessionStore:
    """Redis-backed session storage for game state.

    Features:
    - Automatic JSON serialization/deserialization
    - TTL-based session expiration
    - Async operations for FastAPI compatibility
    """

    KEY_PREFIX = "session:"

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.KEY_PREFIX}{session_id}"

    async def save(self, state: GameState) -> None:
        """Save state to Redis with TTL."""
        key = self._key(state.session_id)
        data = state.model_dump_json()
        await self.client.setex(
            key,
            settings.session_ttl_seconds,
            data,
        )

    async def load(self, session_id: str) -> GameState | None:
        """Load state from Redis."""
        key = self._key(session_id)
        data = await self.client.get(key)

        if data is None:
            return None

        return GameState.model_validate_json(data)

    async def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        key = self._key(session_id)
        return await self.client.exists(key) > 0

    async def delete(self, session_id: str) -> bool:
        """Delete session. Returns True if deleted."""
        key = self._key(session_id)
        return await self.client.delete(key) > 0

    async def refresh_ttl(self, session_id: str) -> bool:
        """Refresh session TTL. Returns True if session exists."""
        key = self._key(session_id)
        return await self.client.expire(key, settings.session_ttl_seconds)

    async def get_ttl(self, session_id: str) -> int:
        """Get remaining TTL in seconds. Returns -2 if key doesn't exist."""
        key = self._key(session_id)
        return await self.client.ttl(key)


# Global store instance
session_store = RedisSessionStore()
```

### 5.3 FastAPI Lifecycle Integration

Update `src/api/main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.state.redis_store import session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Redis connection lifecycle."""
    await session_store.connect()
    yield
    await session_store.disconnect()


app = FastAPI(title="Pocket Portals", lifespan=lifespan)
```

---

## 6. GameFlow Implementation

### 6.1 Main Flow

Create `src/engine/game_flow.py`:

```python
from __future__ import annotations

import uuid
from crewai.flow.flow import Flow, start, listen

from src.state.models import GameState, GamePhase
from src.state.redis_store import session_store
from src.engine.router import AgentRouter
from src.agents.factory import AgentFactory


class GameFlow(Flow[GameState]):
    """Main game flow with Redis persistence."""

    def __init__(self, state: GameState | None = None):
        super().__init__()
        if state:
            self.state = state
        self.agent_router = AgentRouter()
        self.agent_factory = AgentFactory()

    @start()
    def initialize(self) -> GameState:
        """Initialize session ID if new."""
        if not self.state.session_id:
            self.state.session_id = str(uuid.uuid4())
        return self.state

    @listen(initialize)
    def route_agents(self) -> GameState:
        """Determine which agents should respond."""
        if not self.state.current_action:
            return self.state

        routing = self.agent_router.route(
            action=self.state.current_action,
            phase=self.state.phase,
            recent_agents=self.state.recent_agents,
            combat_state=self.state.combat_state,
        )

        self.state.active_agents = routing.agents
        return self.state

    @listen(route_agents)
    def execute_agents(self) -> GameState:
        """Execute selected agents and collect responses."""
        if not self.state.active_agents:
            return self.state

        self.state.agent_responses = {}

        for agent_name in self.state.active_agents:
            agent = self.agent_factory.create(agent_name)
            response = agent.respond(
                action=self.state.current_action,
                context=self._build_context(),
                character_sheet=self.state.character_sheet,
            )
            self.state.agent_responses[agent_name] = response

        return self.state

    @listen(execute_agents)
    def aggregate_responses(self) -> GameState:
        """Combine agent responses into final narrative."""
        responses = list(self.state.agent_responses.values())

        if len(responses) == 1:
            self.state.final_narrative = responses[0]
        elif responses:
            self.state.final_narrative = "\n\n".join(responses)

        # Update conversation history
        if self.state.current_action:
            self.state.conversation_history.append({
                "role": "user",
                "content": self.state.current_action,
            })
        if self.state.final_narrative:
            self.state.conversation_history.append({
                "role": "assistant",
                "content": self.state.final_narrative,
            })

        # Update agent tracking
        self.state.recent_agents = self.state.active_agents[-3:]

        return self.state

    def _build_context(self) -> str:
        """Build context string from recent history."""
        recent = self.state.conversation_history[-6:]
        return "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in recent
        )


class GameFlowService:
    """Service layer for GameFlow with Redis persistence."""

    @staticmethod
    async def create_session() -> GameState:
        """Create a new game session."""
        flow = GameFlow()
        flow.kickoff()
        await session_store.save(flow.state)
        return flow.state

    @staticmethod
    async def get_session(session_id: str) -> GameState | None:
        """Get existing session."""
        return await session_store.load(session_id)

    @staticmethod
    async def process_action(session_id: str, action: str) -> GameState:
        """Process player action and persist state."""
        state = await session_store.load(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")

        state.current_action = action
        flow = GameFlow(state=state)
        flow.kickoff()

        await session_store.save(flow.state)
        return flow.state

    @staticmethod
    async def process_action_async(session_id: str, action: str) -> GameState:
        """Async version of process_action."""
        state = await session_store.load(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")

        state.current_action = action
        flow = GameFlow(state=state)
        await flow.kickoff_async()

        await session_store.save(flow.state)
        return flow.state

    @staticmethod
    async def update_health(session_id: str, delta: int) -> int:
        """Update health and return new value."""
        state = await session_store.load(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")

        new_health = max(0, min(state.health_max, state.health_current + delta))
        state.health_current = new_health

        await session_store.save(state)
        return new_health

    @staticmethod
    async def set_phase(session_id: str, phase: GamePhase) -> None:
        """Update game phase."""
        state = await session_store.load(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")

        state.phase = phase
        await session_store.save(state)

    @staticmethod
    async def set_choices(session_id: str, choices: list[str]) -> None:
        """Set available choices."""
        state = await session_store.load(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found")

        state.current_choices = choices
        await session_store.save(state)

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """Delete session."""
        return await session_store.delete(session_id)
```

---

## 7. Agent Memory Configuration

### 7.1 Crew with Memory

Update `src/engine/crews.py`:

```python
from crewai import Crew


def create_crew_with_memory(agents: list, tasks: list) -> Crew:
    """Create a Crew with memory enabled."""
    return Crew(
        agents=agents,
        tasks=tasks,
        memory=True,
        verbose=False,
        embedder={
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"}
        },
    )
```

### 7.2 Memory-Aware Agent Prompts

Update agent backstories in `src/config/agents.yaml`:

```yaml
narrator:
  backstory: |
    You are the Narrator, weaver of tales in this solo adventure.

    MEMORY INSTRUCTIONS:
    - Reference previous events when relevant
    - Remember character name and traits
    - Build on established story elements
    - Never contradict what happened before

keeper:
  backstory: |
    You are the Keeper, arbiter of game mechanics.

    MEMORY INSTRUCTIONS:
    - Track combat results and HP changes
    - Remember dice roll outcomes
    - Maintain consistency in stat applications
```

---

## 8. API Updates

### 8.1 Updated Endpoints

Update `src/api/main.py`:

```python
import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from src.state.redis_store import session_store
from src.engine.game_flow import GameFlowService
from src.api.models import ActionRequest, SessionResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await session_store.connect()
    yield
    await session_store.disconnect()


app = FastAPI(title="Pocket Portals", lifespan=lifespan)


@app.post("/session/new")
async def new_session() -> SessionResponse:
    """Create a new game session."""
    state = await GameFlowService.create_session()
    return SessionResponse(
        session_id=state.session_id,
        phase=state.phase.value,
        health_current=state.health_current,
        health_max=state.health_max,
    )


@app.post("/action")
async def process_action(request: ActionRequest) -> dict:
    """Process player action."""
    try:
        state = await GameFlowService.process_action_async(
            request.session_id,
            request.action,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "narrative": state.final_narrative,
        "choices": state.current_choices,
        "health_current": state.health_current,
        "health_max": state.health_max,
        "phase": state.phase.value,
    }


@app.get("/session/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get session state."""
    state = await GameFlowService.get_session(session_id)

    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": state.session_id,
        "phase": state.phase.value,
        "health_current": state.health_current,
        "health_max": state.health_max,
        "has_character": state.has_character,
        "choices": state.current_choices,
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete session."""
    deleted = await GameFlowService.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@app.post("/stream")
async def stream_action(request: ActionRequest) -> StreamingResponse:
    """Process action with SSE streaming."""
    # Verify session exists first
    state = await GameFlowService.get_session(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generate():
        try:
            result_state = await GameFlowService.process_action_async(
                request.session_id,
                request.action,
            )

            # Stream character by character
            for char in result_state.final_narrative:
                yield f"data: {json.dumps({'char': char})}\n\n"
                await asyncio.sleep(0.02)

            # Send final state
            yield f"data: {json.dumps({
                'done': True,
                'choices': result_state.current_choices,
                'health': result_state.health_current,
                'phase': result_state.phase.value,
            })}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 9. Files to Delete

Remove these files after implementing the new system:

```
src/state/session_manager.py      # Replaced by redis_store.py + GameFlowService
src/engine/flow.py                # Replaced by game_flow.py
src/engine/flow_state.py          # Merged into models.py (GameState)
tests/test_session_manager.py     # Replaced by test_game_flow.py
```

Update imports in all files that reference deleted modules.

---

## 10. Testing Requirements

### 10.1 Unit Tests

Update `tests/test_models.py` with new GameState tests:

```python
import pytest
from pydantic import ValidationError

from src.state.models import GameState, GamePhase, CombatState


class TestGameState:

    def test_creates_with_defaults(self) -> None:
        state = GameState()
        assert state.session_id == ""
        assert state.health_current == 20
        assert state.phase == GamePhase.CHARACTER_CREATION

    def test_has_character_property(self) -> None:
        state = GameState()
        assert state.has_character is False

    def test_is_in_combat_property(self) -> None:
        state = GameState()
        assert state.is_in_combat is False

        state.combat_state = CombatState(is_active=True)
        assert state.is_in_combat is True

    def test_rejects_negative_health(self) -> None:
        with pytest.raises(ValidationError):
            GameState(health_current=-5)

    def test_rejects_health_exceeding_max(self) -> None:
        with pytest.raises(ValidationError):
            GameState(health_current=30, health_max=20)

    def test_serializes_round_trip(self) -> None:
        original = GameState(
            session_id="test-123",
            health_current=15,
            phase=GamePhase.EXPLORATION,
        )
        json_data = original.model_dump_json()
        restored = GameState.model_validate_json(json_data)
        assert restored.session_id == original.session_id
        assert restored.health_current == original.health_current
```

### 10.2 Redis Store Tests

Create `tests/test_redis_store.py`:

```python
import pytest
import pytest_asyncio

from src.state.redis_store import RedisSessionStore
from src.state.models import GameState, GamePhase


@pytest.fixture
def redis_store():
    """Create Redis store for testing."""
    return RedisSessionStore("redis://localhost:6379/15")  # Use test DB


@pytest_asyncio.fixture
async def connected_store(redis_store):
    """Connected Redis store."""
    await redis_store.connect()
    yield redis_store
    # Cleanup test keys
    keys = await redis_store.client.keys("session:test-*")
    if keys:
        await redis_store.client.delete(*keys)
    await redis_store.disconnect()


class TestRedisSessionStore:

    @pytest.mark.asyncio
    async def test_save_and_load(self, connected_store) -> None:
        state = GameState(
            session_id="test-save-load",
            health_current=15,
            phase=GamePhase.EXPLORATION,
        )

        await connected_store.save(state)
        loaded = await connected_store.load("test-save-load")

        assert loaded is not None
        assert loaded.session_id == "test-save-load"
        assert loaded.health_current == 15
        assert loaded.phase == GamePhase.EXPLORATION

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, connected_store) -> None:
        loaded = await connected_store.load("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_exists(self, connected_store) -> None:
        state = GameState(session_id="test-exists")
        await connected_store.save(state)

        assert await connected_store.exists("test-exists") is True
        assert await connected_store.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_delete(self, connected_store) -> None:
        state = GameState(session_id="test-delete")
        await connected_store.save(state)

        assert await connected_store.delete("test-delete") is True
        assert await connected_store.exists("test-delete") is False

    @pytest.mark.asyncio
    async def test_ttl(self, connected_store) -> None:
        state = GameState(session_id="test-ttl")
        await connected_store.save(state)

        ttl = await connected_store.get_ttl("test-ttl")
        assert ttl > 0  # Should have TTL set
```

### 10.3 Integration Tests

Create `tests/test_game_flow.py`:

```python
import pytest
import pytest_asyncio

from src.state.redis_store import session_store
from src.engine.game_flow import GameFlow, GameFlowService
from src.state.models import GamePhase


@pytest_asyncio.fixture
async def redis_connected():
    """Connect Redis for testing."""
    await session_store.connect()
    yield
    # Cleanup
    keys = await session_store.client.keys("session:*")
    if keys:
        await session_store.client.delete(*keys)
    await session_store.disconnect()


class TestGameFlow:

    def test_creates_new_session(self) -> None:
        flow = GameFlow()
        flow.kickoff()
        assert flow.state.session_id != ""

    def test_uses_provided_state(self) -> None:
        from src.state.models import GameState

        state = GameState(session_id="provided-id")
        flow = GameFlow(state=state)
        flow.kickoff()
        assert flow.state.session_id == "provided-id"


class TestGameFlowService:

    @pytest.mark.asyncio
    async def test_create_session(self, redis_connected) -> None:
        state = await GameFlowService.create_session()

        assert state.session_id != ""
        assert state.phase == GamePhase.CHARACTER_CREATION

        # Verify persisted
        loaded = await session_store.load(state.session_id)
        assert loaded is not None

    @pytest.mark.asyncio
    async def test_get_session(self, redis_connected) -> None:
        state = await GameFlowService.create_session()
        loaded = await GameFlowService.get_session(state.session_id)

        assert loaded is not None
        assert loaded.session_id == state.session_id

    @pytest.mark.asyncio
    async def test_update_health(self, redis_connected) -> None:
        state = await GameFlowService.create_session()

        new_health = await GameFlowService.update_health(state.session_id, -5)
        assert new_health == 15

        loaded = await GameFlowService.get_session(state.session_id)
        assert loaded.health_current == 15

    @pytest.mark.asyncio
    async def test_health_cannot_go_negative(self, redis_connected) -> None:
        state = await GameFlowService.create_session()

        new_health = await GameFlowService.update_health(state.session_id, -100)
        assert new_health == 0

    @pytest.mark.asyncio
    async def test_delete_session(self, redis_connected) -> None:
        state = await GameFlowService.create_session()

        deleted = await GameFlowService.delete_session(state.session_id)
        assert deleted is True

        loaded = await GameFlowService.get_session(state.session_id)
        assert loaded is None
```

---

## 11. Implementation Tasks

### Task List

1. **Add Dependencies**
   ```bash
   uv add redis pydantic-settings
   ```

2. **Create Settings** (`src/config/settings.py`)
   - Redis URL configuration
   - Session TTL configuration
   - Environment variable support

3. **Update GameState** (`src/state/models.py`)
   - Merge old GameState and ConversationFlowState fields
   - Add validators and properties
   - Update existing tests

4. **Create RedisSessionStore** (`src/state/redis_store.py`)
   - Async Redis operations
   - JSON serialization
   - TTL management
   - Write tests

5. **Create GameFlow** (`src/engine/game_flow.py`)
   - Flow with @start, @listen
   - GameFlowService with Redis persistence
   - Port logic from ConversationFlow

6. **Update API** (`src/api/main.py`)
   - Add lifespan for Redis connection
   - Replace SessionManager with GameFlowService
   - Update all endpoints

7. **Add Memory to Crews** (`src/engine/crews.py`)
   - Enable memory=True
   - Configure embedder
   - Update agent prompts

8. **Delete Old Files**
   - Remove session_manager.py
   - Remove flow.py
   - Remove flow_state.py
   - Update all imports

9. **Update Tests**
   - Delete test_session_manager.py
   - Update test_models.py with new GameState tests
   - Create test_redis_store.py
   - Create test_game_flow.py
   - Ensure coverage >= 70%

10. **Docker/Deployment**
    - Add Redis to docker-compose.yml
    - Update deployment documentation

---

## Appendix A: Docker Compose

Add Redis service:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POCKET_PORTALS_REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

---

## Appendix B: File Changes Summary

| Action | File |
|--------|------|
| CREATE | `src/config/settings.py` |
| UPDATE | `src/state/models.py` (expand GameState) |
| CREATE | `src/state/redis_store.py` |
| CREATE | `src/engine/game_flow.py` |
| UPDATE | `src/api/main.py` |
| UPDATE | `src/engine/crews.py` |
| UPDATE | `src/config/agents.yaml` |
| UPDATE | `docker-compose.yml` |
| UPDATE | `pyproject.toml` (add redis) |
| DELETE | `src/state/session_manager.py` |
| DELETE | `src/engine/flow.py` |
| DELETE | `src/engine/flow_state.py` |
| UPDATE | `tests/test_models.py` (add GameState tests) |
| CREATE | `tests/test_redis_store.py` |
| CREATE | `tests/test_game_flow.py` |
| DELETE | `tests/test_session_manager.py` |

---

## Appendix C: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POCKET_PORTALS_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `POCKET_PORTALS_SESSION_TTL_SECONDS` | `86400` | Session TTL (24 hours) |

---

**End of Document**
