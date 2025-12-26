"""Tests for Redis session backend."""

import fakeredis.aioredis
import pytest

from src.state.backends.redis import RedisBackend
from src.state.models import CombatPhaseEnum, CombatState, GamePhase, GameState


class TestRedisBackend:
    """Test suite for RedisBackend."""

    @pytest.fixture
    async def fake_redis(self) -> fakeredis.aioredis.FakeRedis:
        """Create a fake Redis instance for testing."""
        return fakeredis.aioredis.FakeRedis(decode_responses=True)

    @pytest.fixture
    async def backend(self, fake_redis: fakeredis.aioredis.FakeRedis) -> RedisBackend:
        """Create a RedisBackend with fake Redis."""
        backend = RedisBackend("redis://localhost:6379", ttl=3600)
        backend._redis = fake_redis  # Replace with fake
        return backend

    @pytest.fixture
    def sample_state(self) -> GameState:
        """Create a sample game state for testing."""
        return GameState(
            session_id="test-session-123",
            conversation_history=[{"action": "look around", "narrative": "You see..."}],
            current_choices=["option1", "option2"],
            character_description="A brave warrior",
            health_current=15,
            health_max=20,
            phase=GamePhase.EXPLORATION,
        )

    @pytest.mark.asyncio
    async def test_create_session(
        self, backend: RedisBackend, sample_state: GameState
    ) -> None:
        """Test creating a new session."""
        await backend.create(sample_state.session_id, sample_state)

        assert await backend.exists(sample_state.session_id)

    @pytest.mark.asyncio
    async def test_get_existing_session(
        self, backend: RedisBackend, sample_state: GameState
    ) -> None:
        """Test retrieving an existing session."""
        await backend.create(sample_state.session_id, sample_state)

        retrieved = await backend.get(sample_state.session_id)

        assert retrieved is not None
        assert retrieved.session_id == sample_state.session_id
        assert retrieved.health_current == sample_state.health_current
        assert retrieved.phase == sample_state.phase

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, backend: RedisBackend) -> None:
        """Test retrieving a non-existent session returns None."""
        result = await backend.get("nonexistent-session")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_session(
        self, backend: RedisBackend, sample_state: GameState
    ) -> None:
        """Test updating an existing session."""
        await backend.create(sample_state.session_id, sample_state)

        sample_state.health_current = 10
        sample_state.phase = GamePhase.COMBAT
        await backend.update(sample_state.session_id, sample_state)

        retrieved = await backend.get(sample_state.session_id)
        assert retrieved is not None
        assert retrieved.health_current == 10
        assert retrieved.phase == GamePhase.COMBAT

    @pytest.mark.asyncio
    async def test_delete_existing_session(
        self, backend: RedisBackend, sample_state: GameState
    ) -> None:
        """Test deleting an existing session."""
        await backend.create(sample_state.session_id, sample_state)

        result = await backend.delete(sample_state.session_id)

        assert result is True
        assert not await backend.exists(sample_state.session_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, backend: RedisBackend) -> None:
        """Test deleting a non-existent session returns False."""
        result = await backend.delete("nonexistent-session")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(
        self, backend: RedisBackend, sample_state: GameState
    ) -> None:
        """Test exists returns True for existing session."""
        await backend.create(sample_state.session_id, sample_state)
        assert await backend.exists(sample_state.session_id)

    @pytest.mark.asyncio
    async def test_exists_false(self, backend: RedisBackend) -> None:
        """Test exists returns False for non-existent session."""
        assert not await backend.exists("nonexistent-session")

    @pytest.mark.asyncio
    async def test_key_prefixing(self, backend: RedisBackend) -> None:
        """Test that session keys are properly prefixed."""
        session_id = "test-123"
        expected_key = f"pocket_portals:session:{session_id}"
        assert backend._key(session_id) == expected_key

    @pytest.mark.asyncio
    async def test_session_with_combat_state(self, backend: RedisBackend) -> None:
        """Test serialization of session with combat state."""
        state = GameState(
            session_id="combat-session",
            phase=GamePhase.COMBAT,
            combat_state=CombatState(
                is_active=True,
                phase=CombatPhaseEnum.PLAYER_TURN,
                round_number=2,
            ),
        )

        await backend.create(state.session_id, state)
        retrieved = await backend.get(state.session_id)

        assert retrieved is not None
        assert retrieved.combat_state is not None
        assert retrieved.combat_state.is_active is True
        assert retrieved.combat_state.round_number == 2
