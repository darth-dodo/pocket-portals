# CrewAI Improvements Task List

**Created**: 2025-12-26
**Status**: Planning
**Related Doc**: [2025-12-25-crewai-state-management.md](./2025-12-25-crewai-state-management.md)

> **Note**: For API improvements (modular structure, rate limiting, CORS), see:
> - `tasks.md` - Current status of completed backend improvements
> - `docs/design/2026-01-03-backend-improvements.md` - Design document

---

## Overview

This document contains detailed, actionable tasks for improving the pocket-portals CrewAI implementation. Tasks are organized by priority and include acceptance criteria, implementation details, and testing requirements.

---

## Phase 1: Critical Fixes (Foundation)

### Task 1.1: Fix Jester Agent Duplicate Config Loaders

**Priority**: 🔴 Critical
**Effort**: Small (30 min)
**Files**: `src/agents/jester.py`
**Status**: ✅ COMPLETE (verified 2026-01-09 - already implemented)

**Problem**:
`jester.py` defines its own `load_agent_config()` and `load_task_config()` functions (lines 10-22) instead of using the centralized loader from `src/config/loader.py`.

**Resolution**: Upon inspection, jester.py already uses `from src.config.loader import load_agent_config, load_task_config`. This task was already complete.

**Implementation Steps**:
- [ ] Remove duplicate `load_agent_config()` function from `jester.py`
- [ ] Remove duplicate `load_task_config()` function from `jester.py`
- [ ] Add import: `from src.config.loader import load_agent_config, load_task_config`
- [ ] Update `__init__` to use `config.role` instead of `config["role"]` (Pydantic model access)
- [ ] Update `__init__` to use `config.goal` instead of `config["goal"]`
- [ ] Update `__init__` to use `config.backstory` instead of `config["backstory"]`
- [ ] Update `__init__` to use `config.verbose` instead of `config.get("verbose", True)`
- [ ] Update `__init__` to use `config.allow_delegation` instead of `config.get("allow_delegation", False)`
- [ ] Update `add_complication()` to use `task_config.description` instead of `task_config["description"]`
- [ ] Update `add_complication()` to use `task_config.expected_output` instead of `task_config["expected_output"]`

**Acceptance Criteria**:
- [ ] No duplicate functions in `jester.py`
- [ ] Jester agent uses centralized `src/config/loader.py`
- [ ] All existing tests pass
- [ ] Jester responds correctly in gameplay

**Testing**:
```bash
# Run existing tests
pytest tests/test_jester.py -v

# Manual verification
python -c "from src.agents.jester import JesterAgent; j = JesterAgent(); print(j.respond('test action'))"
```

---

### Task 1.2: Add LLM Configuration to YAML

**Priority**: 🔴 Critical
**Effort**: Medium (2 hours)
**Files**: `src/config/agents.yaml`, `src/config/loader.py`
**Status**: ✅ COMPLETE (verified 2026-01-09 - already implemented)

**Problem**:
LLM settings (model, temperature, max_tokens) are hardcoded in each agent file, making it difficult to change models or tune parameters without code changes.

**Resolution**: Upon inspection, this was already implemented:
- `src/config/loader.py` has `LLMConfig` Pydantic model with defaults
- `src/config/agents.yaml` has `defaults.llm` section and per-agent overrides
- All agents use `config.llm.model`, `config.llm.temperature`, `config.llm.max_tokens`

**Implementation Steps**:

#### Step 1: Update `src/config/loader.py`
- [ ] Add `LLMConfig` Pydantic model:
  ```python
  class LLMConfig(BaseModel):
      """LLM configuration for an agent."""
      model: str = "anthropic/claude-3-5-haiku-20241022"
      temperature: float = 0.7
      max_tokens: int = 1024
  ```
- [ ] Add `llm` field to `AgentConfig`:
  ```python
  class AgentConfig(BaseModel):
      role: str
      goal: str
      backstory: str
      verbose: bool = False
      allow_delegation: bool = False
      llm: LLMConfig = Field(default_factory=LLMConfig)
      memory: bool = False
  ```
- [ ] Add YAML caching to avoid repeated file reads:
  ```python
  _config_cache: dict = {}

  def _load_yaml(filename: str) -> dict:
      if filename not in _config_cache:
          with open(CONFIG_DIR / filename) as f:
              _config_cache[filename] = yaml.safe_load(f)
      return _config_cache[filename]
  ```
- [ ] Update `load_agent_config()` to merge defaults:
  ```python
  def load_agent_config(agent_name: str) -> AgentConfig:
      agents = _load_yaml("agents.yaml")
      defaults = agents.get("defaults", {}).get("llm", {})
      agent_data = agents[agent_name].copy()
      llm_config = {**defaults, **agent_data.get("llm", {})}
      agent_data["llm"] = llm_config
      return AgentConfig(**agent_data)
  ```

#### Step 2: Update `src/config/agents.yaml`
- [ ] Add defaults section at top:
  ```yaml
  defaults:
    llm:
      model: "anthropic/claude-3-5-haiku-20241022"
      temperature: 0.7
      max_tokens: 1024
  ```
- [ ] Add LLM overrides to each agent:
  ```yaml
  narrator:
    # ... existing fields ...
    llm:
      temperature: 0.7
      max_tokens: 1024
    memory: true

  keeper:
    # ... existing fields ...
    llm:
      temperature: 0.3
      max_tokens: 256
    memory: false

  jester:
    # ... existing fields ...
    llm:
      temperature: 0.8
      max_tokens: 256
    memory: false

  character_interviewer:
    # ... existing fields ...
    llm:
      temperature: 0.8
      max_tokens: 512
    memory: false

  innkeeper_theron:
    # ... existing fields ...
    llm:
      temperature: 0.6
      max_tokens: 512
    memory: false
  ```

**Acceptance Criteria**:
- [ ] All LLM configs defined in YAML only
- [ ] `LLMConfig` Pydantic model validates settings
- [ ] Config caching prevents repeated file reads
- [ ] Default merging works correctly
- [ ] All agents use config-based LLM settings

**Testing**:
```python
# tests/test_config_loader.py
def test_llm_config_loads_defaults():
    config = load_agent_config("narrator")
    assert config.llm.model == "anthropic/claude-3-5-haiku-20241022"

def test_llm_config_overrides_temperature():
    config = load_agent_config("keeper")
    assert config.llm.temperature == 0.3  # Keeper override

def test_llm_config_overrides_max_tokens():
    config = load_agent_config("keeper")
    assert config.llm.max_tokens == 256  # Keeper override

def test_config_caching():
    # First load
    config1 = load_agent_config("narrator")
    # Second load should use cache
    config2 = load_agent_config("narrator")
    assert config1 == config2
```

---

### Task 1.3: Update Agents to Use Config-Based LLM

**Priority**: 🔴 Critical
**Effort**: Medium (2 hours)
**Files**: `src/agents/narrator.py`, `src/agents/keeper.py`, `src/agents/jester.py`, `src/agents/character_interviewer.py`, `src/agents/innkeeper.py`

**Problem**:
Each agent hardcodes its LLM configuration. Need to update all agents to use the YAML config.

**Implementation Steps**:

#### For each agent file:
- [ ] **narrator.py**:
  - Remove hardcoded LLM instantiation
  - Use `config.llm.model`, `config.llm.temperature`, `config.llm.max_tokens`
  ```python
  def __init__(self) -> None:
      config = load_agent_config("narrator")

      self.llm = LLM(
          model=config.llm.model,
          api_key=settings.anthropic_api_key,
          temperature=config.llm.temperature,
          max_tokens=config.llm.max_tokens,
      )

      self.agent = Agent(
          role=config.role,
          goal=config.goal,
          backstory=config.backstory,
          verbose=config.verbose,
          allow_delegation=config.allow_delegation,
          llm=self.llm,
          memory=config.memory,
      )
  ```

- [ ] **keeper.py**: Same pattern as narrator
- [ ] **jester.py**: Same pattern (after Task 1.1)
- [ ] **character_interviewer.py**: Same pattern
- [ ] **innkeeper.py**: Same pattern (if exists, or create)

**Acceptance Criteria**:
- [ ] No hardcoded model names in agent files
- [ ] No hardcoded temperature values in agent files
- [ ] No hardcoded max_tokens in agent files
- [ ] All agents instantiate correctly from YAML config
- [ ] Changing YAML values changes agent behavior

**Testing**:
```bash
# Run full test suite
pytest tests/ -v

# Verify each agent loads
python -c "
from src.agents import NarratorAgent, KeeperAgent, JesterAgent, CharacterInterviewerAgent
print('Narrator:', NarratorAgent().llm.model)
print('Keeper:', KeeperAgent().llm.model)
print('Jester:', JesterAgent().llm.model)
print('Interviewer:', CharacterInterviewerAgent().llm.model)
"
```

---

## Phase 2: Production Readiness

### Task 2.1: Implement Flow State Persistence with Redis

**Priority**: 🔴 Critical
**Effort**: Large (4-6 hours)
**Files**: `src/engine/flow.py`, `src/settings.py`, `docker-compose.yml`

**Problem**:
Game sessions are stored in-memory and lost on server restart. Need persistent storage.

**Implementation Steps**:

#### Step 1: Update Settings
- [ ] Add Redis URL to `src/settings.py`:
  ```python
  redis_url: str = Field(default="redis://localhost:6379/0")
  session_ttl_seconds: int = Field(default=86400)  # 24 hours
  ```

#### Step 2: Add Redis to Docker Compose
- [ ] Update `docker-compose.yml`:
  ```yaml
  services:
    redis:
      image: redis:7-alpine
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data
      command: redis-server --appendonly yes

  volumes:
    redis_data:
  ```

#### Step 3: Update Flow with @persist
- [ ] Import persist decorator:
  ```python
  from crewai.flow.persistence import persist
  ```
- [ ] Add decorator to ConversationFlow:
  ```python
  @persist(
      storage="redis",
      connection_string=settings.redis_url
  )
  class ConversationFlow(Flow[ConversationFlowState]):
      ...
  ```
- [ ] Add turn counter to state for tracking:
  ```python
  # In ConversationFlowState
  turn_count: int = Field(default=0)
  ```
- [ ] Increment turn count in route_action:
  ```python
  @start()
  def route_action(self) -> ConversationFlowState:
      self.state.turn_count += 1
      # ... rest of method
  ```

#### Step 4: Add Redis Health Check
- [ ] Create `src/utils/redis_health.py`:
  ```python
  import redis
  from src.settings import settings

  async def check_redis_health() -> bool:
      try:
          client = redis.from_url(settings.redis_url)
          return client.ping()
      except Exception:
          return False
  ```

**Acceptance Criteria**:
- [ ] Flow state persists to Redis after each step
- [ ] Sessions survive server restart
- [ ] Session TTL works (expires after 24 hours)
- [ ] Health check endpoint reports Redis status
- [ ] Graceful fallback if Redis unavailable

**Testing**:
```python
# tests/test_flow_persistence.py
import pytest
import redis

@pytest.fixture
def redis_client():
    client = redis.from_url("redis://localhost:6379/1")  # Test DB
    yield client
    client.flushdb()

def test_flow_persists_state(redis_client):
    from src.engine.flow import ConversationFlow
    from src.agents import NarratorAgent, KeeperAgent, JesterAgent

    flow = ConversationFlow(
        narrator=NarratorAgent(),
        keeper=KeeperAgent(),
        jester=JesterAgent(),
    )
    flow.state.session_id = "test-session-123"
    flow.state.action = "look around"

    # Execute flow
    result = flow.kickoff()

    # Verify persistence
    keys = redis_client.keys("*test-session-123*")
    assert len(keys) > 0

def test_flow_resumes_from_redis(redis_client):
    # First execution
    flow1 = ConversationFlow(...)
    flow1.state.session_id = "resume-test"
    flow1.kickoff()
    turn1 = flow1.state.turn_count

    # Second execution should resume
    flow2 = ConversationFlow(...)
    flow2.state.session_id = "resume-test"
    flow2.kickoff()

    assert flow2.state.turn_count == turn1 + 1
```

---

### Task 2.2: Add Execution Hooks for Observability

**Priority**: 🟠 High
**Effort**: Medium (3 hours)
**Files**: `src/agents/hooks.py` (new), `src/agents/__init__.py`

**Problem**:
No visibility into LLM calls, timing, errors, or token usage. Debugging is difficult.

**Implementation Steps**:

#### Step 1: Create hooks module
- [ ] Create `src/agents/hooks.py`:
  ```python
  """Execution hooks for observability and content safety."""

  import logging
  import time
  from typing import Any

  logger = logging.getLogger(__name__)

  # Metrics storage (replace with proper metrics in production)
  _call_metrics: dict[int, float] = {}

  try:
      from crewai.decorators import before_llm_call, after_llm_call
      HOOKS_AVAILABLE = True
  except ImportError:
      HOOKS_AVAILABLE = False
      logger.warning("CrewAI hooks not available in this version")

  if HOOKS_AVAILABLE:
      @before_llm_call
      def log_llm_request(context: Any) -> None:
          """Log LLM request details."""
          call_id = id(context)
          _call_metrics[call_id] = time.time()

          agent_role = getattr(context.agent, 'role', 'unknown') if context.agent else 'unknown'
          prompt_len = len(context.prompt) if context.prompt else 0

          logger.info(f"LLM Request: agent={agent_role}, prompt_length={prompt_len}")
          return None

      @after_llm_call
      def log_llm_response(context: Any) -> None:
          """Log LLM response with timing."""
          call_id = id(context)
          start_time = _call_metrics.pop(call_id, time.time())
          duration = time.time() - start_time

          agent_role = getattr(context.agent, 'role', 'unknown') if context.agent else 'unknown'
          response_len = len(context.response) if context.response else 0

          logger.info(
              f"LLM Response: agent={agent_role}, "
              f"duration={duration:.3f}s, response_length={response_len}"
          )
          return None

      @before_llm_call
      def content_safety_filter(context: Any) -> bool | None:
          """Pre-filter harmful content."""
          HARMFUL_PATTERNS = [
              "self-harm", "suicide", "kill myself",
              "torture", "abuse", "sexual content"
          ]

          prompt = (context.prompt or "").lower()

          for pattern in HARMFUL_PATTERNS:
              if pattern in prompt:
                  agent_role = getattr(context.agent, 'role', 'unknown')
                  logger.warning(f"Content filter triggered: agent={agent_role}, pattern={pattern}")
                  return False  # Block execution

          return None  # Allow execution
  ```

#### Step 2: Register hooks
- [ ] Update `src/agents/__init__.py`:
  ```python
  # Import hooks to register them (must be before agent imports)
  from src.agents import hooks  # noqa: F401

  from src.agents.narrator import NarratorAgent
  from src.agents.keeper import KeeperAgent
  from src.agents.jester import JesterAgent
  from src.agents.character_interviewer import CharacterInterviewerAgent

  __all__ = [
      "NarratorAgent",
      "KeeperAgent",
      "JesterAgent",
      "CharacterInterviewerAgent",
  ]
  ```

#### Step 3: Configure logging
- [ ] Update `src/settings.py` or create `src/logging_config.py`:
  ```python
  import logging

  def configure_logging():
      logging.basicConfig(
          level=logging.INFO,
          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )

      # Set specific levels
      logging.getLogger('src.agents.hooks').setLevel(logging.INFO)
      logging.getLogger('crewai').setLevel(logging.WARNING)
  ```

**Acceptance Criteria**:
- [ ] All LLM calls are logged with timing
- [ ] Content safety filter blocks harmful prompts
- [ ] Logs include agent role, prompt length, response length
- [ ] Hooks don't break if CrewAI version doesn't support them
- [ ] Performance impact < 10ms per call

**Testing**:
```python
# tests/test_hooks.py
import logging
from unittest.mock import MagicMock, patch

def test_content_filter_blocks_harmful():
    from src.agents.hooks import content_safety_filter

    context = MagicMock()
    context.prompt = "The character wants to hurt themselves"
    context.agent.role = "narrator"

    result = content_safety_filter(context)
    assert result is False  # Blocked

def test_content_filter_allows_normal():
    from src.agents.hooks import content_safety_filter

    context = MagicMock()
    context.prompt = "The hero enters the tavern"
    context.agent.role = "narrator"

    result = content_safety_filter(context)
    assert result is None  # Allowed

def test_timing_logged(caplog):
    from src.agents.hooks import log_llm_request, log_llm_response

    context = MagicMock()
    context.prompt = "test prompt"
    context.response = "test response"
    context.agent.role = "narrator"

    with caplog.at_level(logging.INFO):
        log_llm_request(context)
        log_llm_response(context)

    assert "LLM Request" in caplog.text
    assert "LLM Response" in caplog.text
    assert "duration=" in caplog.text
```

---

### Task 2.3: Add Structured Output Schemas

**Priority**: 🟠 High
**Effort**: Medium (2-3 hours)
**Files**: `src/agents/schemas.py` (new), `src/agents/character_interviewer.py`
**Status**: ✅ COMPLETE (2026-01-09)

**Problem**:
Manual JSON parsing in `character_interviewer.py` is error-prone. Uses regex fallbacks and has ~15% failure rate.

**Resolution**: Implemented Pydantic schemas with CrewAI's output_pydantic feature:
- Created `src/agents/schemas.py` with InterviewResponse, StarterChoicesResponse, AdventureHooksResponse
- Updated CharacterInterviewerAgent to use output_pydantic instead of manual JSON parsing
- Removed deprecated `_parse_json_response()` method
- Added 55 comprehensive tests in `tests/test_schemas.py`
- Branch: feature/config-improvements, Commit: e28e80c

**Implementation Steps**:

#### Step 1: Create schemas module
- [ ] Create `src/agents/schemas.py`:
  ```python
  """Pydantic schemas for structured agent outputs."""

  from typing import Any, Tuple
  from pydantic import BaseModel, Field, field_validator

  class InterviewResponse(BaseModel):
      """Structured response from character interview."""
      narrative: str = Field(..., min_length=10, max_length=500)
      choices: list[str] = Field(..., min_length=3, max_length=5)

      @field_validator('choices')
      @classmethod
      def validate_choices(cls, v: list[str]) -> list[str]:
          if len(v) < 3:
              raise ValueError("Need at least 3 choices")
          return v[:3]  # Truncate to 3

  class AdventureHooksResponse(BaseModel):
      """Structured response for adventure hooks."""
      choices: list[str] = Field(..., min_length=3, max_length=5)

      @field_validator('choices')
      @classmethod
      def validate_choices(cls, v: list[str]) -> list[str]:
          if len(v) < 3:
              raise ValueError("Need at least 3 choices")
          return v[:3]

  class StarterChoicesResponse(BaseModel):
      """Structured response for starter choices."""
      choices: list[str] = Field(..., min_length=3, max_length=5)

  def validate_interview_response(result: Any) -> Tuple[bool, Any]:
      """Guardrail validator for interview responses."""
      try:
          raw = result.raw if hasattr(result, 'raw') else str(result)
          parsed = InterviewResponse.model_validate_json(raw)
          return (True, parsed.model_dump())
      except Exception as e:
          return (False, f"Invalid interview response: {e}")

  def validate_adventure_hooks(result: Any) -> Tuple[bool, Any]:
      """Guardrail validator for adventure hooks."""
      try:
          raw = result.raw if hasattr(result, 'raw') else str(result)
          parsed = AdventureHooksResponse.model_validate_json(raw)
          return (True, parsed.model_dump())
      except Exception as e:
          return (False, f"Invalid adventure hooks: {e}")

  def validate_starter_choices(result: Any) -> Tuple[bool, Any]:
      """Guardrail validator for starter choices."""
      try:
          raw = result.raw if hasattr(result, 'raw') else str(result)
          parsed = StarterChoicesResponse.model_validate_json(raw)
          return (True, parsed.model_dump())
      except Exception as e:
          return (False, f"Invalid starter choices: {e}")
  ```

#### Step 2: Update CharacterInterviewerAgent
- [ ] Add guardrails to interview_turn():
  ```python
  from crewai import Task
  from src.agents.schemas import validate_interview_response

  def interview_turn(
      self, turn_number: int, conversation_history: str
  ) -> dict[str, Any]:
      task_config = load_task_config("interview_character")

      description = task_config.description.format(
          turn_number=turn_number,
          conversation_history=conversation_history or "No previous conversation.",
      )

      task = Task(
          description=description,
          expected_output=task_config.expected_output,
          agent=self.agent,
          guardrail=validate_interview_response,
          guardrail_max_retries=3,
      )

      result = task.execute_sync()

      # Result is validated by guardrail
      if isinstance(result, dict) and "narrative" in result:
          return result

      # Fallback if guardrail exhausted retries
      return {
          "narrative": self._get_fallback_narrative(turn_number),
          "choices": self._get_fallback_choices(turn_number),
      }
  ```

- [ ] Add guardrails to generate_starter_choices()
- [ ] Add guardrails to generate_adventure_hooks()
- [ ] Remove manual `_parse_json_response()` method (or keep as fallback)

**Acceptance Criteria**:
- [ ] All JSON outputs use Pydantic validation
- [ ] Guardrails auto-retry on invalid JSON (up to 3 times)
- [ ] Validation errors are logged
- [ ] Parse success rate > 99%
- [ ] Fallbacks work when guardrails exhausted

**Testing**:
```python
# tests/test_schemas.py
import pytest
from src.agents.schemas import (
    InterviewResponse,
    validate_interview_response,
    validate_adventure_hooks,
)

def test_interview_response_valid():
    data = '{"narrative": "Hello adventurer!", "choices": ["A", "B", "C"]}'
    response = InterviewResponse.model_validate_json(data)
    assert response.narrative == "Hello adventurer!"
    assert len(response.choices) == 3

def test_interview_response_rejects_few_choices():
    data = '{"narrative": "Hello!", "choices": ["A"]}'
    with pytest.raises(ValueError):
        InterviewResponse.model_validate_json(data)

def test_guardrail_validates():
    class MockResult:
        raw = '{"narrative": "Test narrative", "choices": ["A", "B", "C"]}'

    success, data = validate_interview_response(MockResult())
    assert success is True
    assert data["narrative"] == "Test narrative"

def test_guardrail_rejects_invalid():
    class MockResult:
        raw = 'not valid json'

    success, error = validate_interview_response(MockResult())
    assert success is False
    assert "Invalid" in error
```

---

## Phase 3: Quality Improvements

### Task 3.1: Enable Memory System for Narrative Agents

**Priority**: 🟠 High
**Effort**: Medium (2-3 hours)
**Files**: `src/agents/narrator.py`, `src/settings.py`, `src/config/agents.yaml`

**Problem**:
Agents don't remember previous interactions. Narrator forgets story details between turns.

**Implementation Steps**:

#### Step 1: Add embedder settings
- [ ] Update `src/settings.py`:
  ```python
  voyage_api_key: str | None = Field(default=None, description="Voyage AI API key for embeddings")
  openai_api_key: str | None = Field(default=None, description="OpenAI API key (fallback embedder)")
  ```

#### Step 2: Create embedder config helper
- [ ] Add to `src/config/loader.py`:
  ```python
  from src.settings import settings

  def get_embedder_config() -> dict | None:
      """Get embedder configuration based on available API keys."""
      if settings.voyage_api_key:
          return {
              "provider": "voyageai",
              "config": {
                  "api_key": settings.voyage_api_key,
                  "model": "voyage-3"
              }
          }
      elif settings.openai_api_key:
          return {
              "provider": "openai",
              "config": {
                  "model": "text-embedding-3-small"
              }
          }
      return None  # Memory will be disabled
  ```

#### Step 3: Update NarratorAgent with memory
- [ ] Update `src/agents/narrator.py`:
  ```python
  from src.config.loader import load_agent_config, get_embedder_config

  class NarratorAgent:
      def __init__(self) -> None:
          config = load_agent_config("narrator")
          embedder = get_embedder_config()

          self.llm = LLM(
              model=config.llm.model,
              api_key=settings.anthropic_api_key,
              temperature=config.llm.temperature,
              max_tokens=config.llm.max_tokens,
          )

          self.agent = Agent(
              role=config.role,
              goal=config.goal,
              backstory=config.backstory,
              verbose=config.verbose,
              allow_delegation=config.allow_delegation,
              llm=self.llm,
              memory=config.memory and embedder is not None,
              embedder=embedder if config.memory else None,
          )
  ```

**Acceptance Criteria**:
- [ ] Narrator remembers story elements across turns
- [ ] Memory works with Voyage AI or OpenAI embeddings
- [ ] Graceful fallback when no embedder API key
- [ ] Memory disabled for stateless agents (Keeper)

**Testing**:
```python
# tests/test_memory.py
def test_narrator_with_memory(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")

    narrator = NarratorAgent()

    # First turn
    response1 = narrator.respond("I enter the tavern and see a mysterious stranger")

    # Second turn should remember
    response2 = narrator.respond("I approach the stranger")

    # Verify memory is enabled
    assert narrator.agent.memory is True

def test_narrator_without_embedder():
    # No API keys set
    narrator = NarratorAgent()

    # Should still work, just without memory
    response = narrator.respond("test action")
    assert response is not None
```

---

### Task 3.2: Add D&D Knowledge Sources

**Priority**: 🟡 Medium
**Effort**: Small (1-2 hours)
**Files**: `src/agents/knowledge.py` (new), `src/agents/narrator.py`, `src/agents/keeper.py`

**Problem**:
Agents lack reference material for D&D rules. Rely solely on LLM training data.

**Implementation Steps**:

#### Step 1: Create knowledge sources
- [ ] Create `src/agents/knowledge.py`:
  ```python
  """D&D knowledge sources for agents."""

  from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

  DND_COMBAT_RULES = StringKnowledgeSource(
      content="""
      D&D 5e Combat Quick Reference:

      ATTACK ROLLS:
      - Roll 1d20 + attack bonus
      - Compare to target's Armor Class (AC)
      - If roll >= AC, attack hits
      - Natural 20 = Critical Hit (double damage dice)
      - Natural 1 = Automatic Miss

      DAMAGE:
      - Roll weapon damage dice + modifier
      - Apply damage to target's HP
      - At 0 HP, creature is unconscious or dead

      ADVANTAGE/DISADVANTAGE:
      - Advantage: Roll 2d20, take higher
      - Disadvantage: Roll 2d20, take lower
      - They cancel each other out

      COMMON DCs:
      - Easy: 10
      - Medium: 15
      - Hard: 20
      - Very Hard: 25
      """
  )

  DND_NARRATIVE_ELEMENTS = StringKnowledgeSource(
      content="""
      Fantasy Narrative Elements:

      SETTINGS:
      - Taverns: Warm hearth, ale, rumors, quest boards
      - Dungeons: Torchlight, echoes, danger, treasure
      - Forests: Ancient trees, hidden paths, mysterious creatures
      - Cities: Bustling markets, guards, guilds, politics

      ATMOSPHERE:
      - Use sensory details: sight, sound, smell
      - Create tension through pacing
      - End scenes with hooks or questions
      - Let players drive the action

      TONE:
      - Heroic fantasy (not grimdark)
      - PG-13 content rating
      - Focus on adventure and courage
      """
  )
  ```

#### Step 2: Add to Keeper agent
- [ ] Update `src/agents/keeper.py`:
  ```python
  from src.agents.knowledge import DND_COMBAT_RULES

  class KeeperAgent:
      def __init__(self) -> None:
          config = load_agent_config("keeper")

          self.agent = Agent(
              # ... existing config ...
              knowledge_sources=[DND_COMBAT_RULES],
          )
  ```

#### Step 3: Add to Narrator agent
- [ ] Update `src/agents/narrator.py`:
  ```python
  from src.agents.knowledge import DND_NARRATIVE_ELEMENTS

  class NarratorAgent:
      def __init__(self) -> None:
          config = load_agent_config("narrator")

          self.agent = Agent(
              # ... existing config ...
              knowledge_sources=[DND_NARRATIVE_ELEMENTS],
          )
  ```

**Acceptance Criteria**:
- [ ] Keeper references D&D rules in mechanical responses
- [ ] Narrator uses narrative guidelines
- [ ] Knowledge doesn't interfere with agent personality
- [ ] No performance degradation

---

### Task 3.3: Create Custom Tools for Agents

**Priority**: 🟡 Medium
**Effort**: Medium (2-3 hours)
**Files**: `src/agents/tools.py` (new), `src/agents/keeper.py`

**Problem**:
Keeper calls DiceRoller directly in code. Could be more autonomous with tools.

**Implementation Steps**:

#### Step 1: Create tools module
- [ ] Create `src/agents/tools.py`:
  ```python
  """Custom tools for CrewAI agents."""

  from crewai.tools import BaseTool
  from pydantic import Field
  from src.utils.dice import DiceRoller

  class DiceRollerTool(BaseTool):
      """Tool for rolling dice using D&D notation."""
      name: str = "dice_roller"
      description: str = (
          "Roll dice using standard D&D notation. "
          "Examples: '1d20' for a d20, '2d6+3' for 2d6 plus 3, '1d20-2' for d20 minus 2. "
          "Returns individual rolls and total."
      )

      def _run(self, notation: str) -> str:
          """Execute the dice roll."""
          try:
              notation = notation.strip()
              result = DiceRoller.roll(notation)
              rolls_str = ", ".join(str(r) for r in result.rolls)

              if result.modifier != 0:
                  mod_str = f"+{result.modifier}" if result.modifier > 0 else str(result.modifier)
                  return f"Rolled {notation}: [{rolls_str}] {mod_str} = {result.total}"
              return f"Rolled {notation}: [{rolls_str}] = {result.total}"
          except ValueError as e:
              return f"Invalid dice notation '{notation}': {e}"

  class HealthStatusTool(BaseTool):
      """Tool for checking health status."""
      name: str = "health_status"
      description: str = "Check current health points and status."

      current_hp: int = Field(default=20)
      max_hp: int = Field(default=20)

      def _run(self, query: str = "") -> str:
          """Return health status."""
          percentage = (self.current_hp / self.max_hp) * 100

          if percentage > 75:
              status = "healthy"
          elif percentage > 50:
              status = "lightly wounded"
          elif percentage > 25:
              status = "injured"
          else:
              status = "critical"

          return f"HP: {self.current_hp}/{self.max_hp} ({percentage:.0f}%) - {status}"
  ```

#### Step 2: Add tools to Keeper
- [ ] Update `src/agents/keeper.py`:
  ```python
  from src.agents.tools import DiceRollerTool

  class KeeperAgent:
      def __init__(self) -> None:
          config = load_agent_config("keeper")

          self.dice_tool = DiceRollerTool()

          self.agent = Agent(
              role=config.role,
              goal=config.goal,
              backstory=config.backstory,
              verbose=config.verbose,
              allow_delegation=config.allow_delegation,
              llm=self.llm,
              tools=[self.dice_tool],  # Agent can roll dice autonomously
          )
  ```

**Acceptance Criteria**:
- [ ] DiceRollerTool works with all valid notations
- [ ] Tool returns readable results
- [ ] Keeper can use tool autonomously in tasks
- [ ] Error handling for invalid notation

**Testing**:
```python
# tests/test_tools.py
from src.agents.tools import DiceRollerTool, HealthStatusTool

def test_dice_roller_basic():
    tool = DiceRollerTool()
    result = tool._run("1d20")
    assert "Rolled 1d20" in result
    assert "=" in result

def test_dice_roller_with_modifier():
    tool = DiceRollerTool()
    result = tool._run("1d6+3")
    assert "+3" in result

def test_dice_roller_invalid():
    tool = DiceRollerTool()
    result = tool._run("invalid")
    assert "Invalid" in result

def test_health_status_healthy():
    tool = HealthStatusTool(current_hp=20, max_hp=20)
    result = tool._run()
    assert "20/20" in result
    assert "healthy" in result

def test_health_status_critical():
    tool = HealthStatusTool(current_hp=3, max_hp=20)
    result = tool._run()
    assert "critical" in result
```

---

## Phase 4: Polish & Documentation

### Task 4.1: Add Flow Visualization

**Priority**: 🟢 Low
**Effort**: Small (30 min)
**Files**: `scripts/visualize_flow.py` (new)

**Implementation Steps**:
- [ ] Create visualization script:
  ```python
  """Generate flow diagram for documentation."""

  from src.engine.flow import ConversationFlow
  from src.agents import NarratorAgent, KeeperAgent, JesterAgent

  def main():
      flow = ConversationFlow(
          narrator=NarratorAgent(),
          keeper=KeeperAgent(),
          jester=JesterAgent(),
      )

      flow.plot("docs/diagrams/conversation_flow")
      print("Flow diagram saved to docs/diagrams/conversation_flow.png")

  if __name__ == "__main__":
      main()
  ```

---

### Task 4.2: Update Documentation

**Priority**: 🟢 Low
**Effort**: Medium (2 hours)
**Files**: `docs/architecture.md`, `README.md`

**Implementation Steps**:
- [ ] Document new YAML config structure
- [ ] Document hook system
- [ ] Document memory/knowledge features
- [ ] Document tool creation
- [ ] Add architecture diagram
- [ ] Update setup instructions for Redis

---

## Summary Checklist

### Phase 1 (Critical)
- [x] Task 1.1: Fix jester.py duplicate loaders ✅ (already complete)
- [x] Task 1.2: Add LLM config to YAML ✅ (already complete)
- [x] Task 1.3: Update agents to use config-based LLM ✅ (already complete)

### Phase 2 (Production)
- [ ] Task 2.1: Implement @persist with Redis
- [ ] Task 2.2: Add execution hooks
- [x] Task 2.3: Add structured output schemas ✅ (2026-01-09)

### Phase 3 (Quality)
- [ ] Task 3.1: Enable memory system
- [ ] Task 3.2: Add D&D knowledge sources
- [ ] Task 3.3: Create custom tools

### Phase 4 (Polish)
- [ ] Task 4.1: Add flow visualization
- [ ] Task 4.2: Update documentation

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Config duplication | 4 files | 1 file | ✓ |
| Session persistence | 0% | 100% | ✓ |
| JSON parse success | ~85% | 99%+ | ✓ |
| LLM call visibility | 0% | 100% | ✓ |
| Agent memory | None | Enabled | ✓ |
| Tool integration | 0 | 3+ | ✓ |
