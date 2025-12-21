# Pocket Portals Conversation Engine

**Technical Specification for Agent Orchestration**

---

## Overview

The conversation engine manages the flow of dialogue between the player and the four agents: Innkeeper Theron, Narrator, Keeper, and Jester. It handles turn-taking, context passing, state updates, and streaming responses.

---

## Conversation State Machine

```
                    ┌─────────────────┐
                    │     IDLE        │
                    │  (Waiting for   │
                    │   player)       │
                    └────────┬────────┘
                             │ player_input
                             v
                    ┌─────────────────┐
                    │   PROCESSING    │
                    │  (Agents work)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              v              v              v
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │ NARRATE  │   │  COMBAT  │   │  CHOICE  │
       └────┬─────┘   └────┬─────┘   └────┬─────┘
            │              │              │
            └──────────────┼──────────────┘
                           v
                    ┌─────────────────┐
                    │   STREAMING     │
                    │  (SSE to UI)    │
                    └────────┬────────┘
                             │ complete
                             v
                    ┌─────────────────┐
                    │     IDLE        │
                    └─────────────────┘
```

---

## Session Context

Each session maintains a context object passed between agents:

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class GamePhase(str, Enum):
    CHARACTER_CREATION = "character_creation"
    QUEST_INTRODUCTION = "quest_introduction"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    DIALOGUE = "dialogue"
    EPILOGUE = "epilogue"


class SessionContext(BaseModel):
    """Shared context passed between all agents."""

    session_id: str
    phase: GamePhase = GamePhase.CHARACTER_CREATION

    # Character data
    character_sheet: Optional[dict] = None
    character_name: str = ""
    character_backstory: str = ""

    # Quest data
    quest_hook: Optional[dict] = None
    quest_npcs: list[dict] = Field(default_factory=list)

    # World state
    current_location: str = "tavern"
    time_of_day: str = "evening"
    world_facts: list[str] = Field(default_factory=list)

    # Conversation history (last N exchanges)
    history: list[dict] = Field(default_factory=list)
    history_limit: int = 20

    # Player choices made
    choices_made: list[dict] = Field(default_factory=list)

    # Combat state (when active)
    combat_state: Optional[dict] = None

    # Token tracking
    tokens_used: int = 0
    token_budget: int = 50000

    def add_exchange(self, role: str, content: str, agent: str = "system"):
        """Add an exchange to history, maintaining limit."""
        self.history.append({
            "role": role,
            "content": content,
            "agent": agent,
        })
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

    def add_choice(self, choice: str, consequence: str):
        """Record a player choice and its consequence."""
        self.choices_made.append({
            "choice": choice,
            "consequence": consequence,
            "location": self.current_location,
            "phase": self.phase,
        })
```

---

## Agent Router

The router decides which agent handles each turn:

```python
from enum import Enum


class AgentRole(str, Enum):
    INNKEEPER = "innkeeper"
    NARRATOR = "narrator"
    CHRONICLER = "chronicler"
    JESTER = "jester"


class AgentRouter:
    """Routes conversation turns to appropriate agents."""

    def route(self, context: SessionContext, player_input: str) -> list[AgentRole]:
        """Determine which agents should respond and in what order."""

        agents = []

        # Phase-based primary routing
        if context.phase == GamePhase.CHARACTER_CREATION:
            agents.append(AgentRole.CHRONICLER)  # Stats and validation
            agents.append(AgentRole.INNKEEPER)   # Welcome and context

        elif context.phase == GamePhase.QUEST_INTRODUCTION:
            agents.append(AgentRole.INNKEEPER)   # Quest hook
            agents.append(AgentRole.NARRATOR)    # Scene setting

        elif context.phase == GamePhase.COMBAT:
            agents.append(AgentRole.CHRONICLER)  # Mechanics first
            agents.append(AgentRole.NARRATOR)    # Narrate outcome

        elif context.phase == GamePhase.EXPLORATION:
            agents.append(AgentRole.NARRATOR)    # Primary

        elif context.phase == GamePhase.DIALOGUE:
            agents.append(AgentRole.NARRATOR)    # NPC dialogue

        elif context.phase == GamePhase.EPILOGUE:
            agents.append(AgentRole.NARRATOR)    # Story conclusion
            agents.append(AgentRole.INNKEEPER)   # Final reflection

        # Jester injection (probabilistic)
        if self._should_jester_intervene(context, player_input):
            agents.append(AgentRole.JESTER)

        return agents

    def _should_jester_intervene(self, context: SessionContext, player_input: str) -> bool:
        """Determine if Jester should add a complication."""

        # Skip during combat and epilogue
        if context.phase in [GamePhase.COMBAT, GamePhase.EPILOGUE]:
            return False

        # Check for calm streak (3+ exchanges without complications)
        recent_agents = [h.get("agent") for h in context.history[-6:]]
        if "jester" in recent_agents:
            return False

        # Probability based on phase
        import random
        probabilities = {
            GamePhase.CHARACTER_CREATION: 0.0,
            GamePhase.QUEST_INTRODUCTION: 0.1,
            GamePhase.EXPLORATION: 0.2,
            GamePhase.DIALOGUE: 0.15,
        }
        return random.random() < probabilities.get(context.phase, 0.1)
```

---

## Turn Executor

Handles the execution of a single conversation turn:

```python
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class AgentResponse:
    agent: AgentRole
    content: str
    annotations: list[str]
    tokens_used: int


class TurnExecutor:
    """Executes a single conversation turn across agents."""

    def __init__(self, crew, router: AgentRouter):
        self.crew = crew
        self.router = router

    async def execute(
        self,
        context: SessionContext,
        player_input: str
    ) -> AsyncGenerator[AgentResponse, None]:
        """Execute turn and stream agent responses."""

        # Get agent order
        agents = self.router.route(context, player_input)

        # Build shared context for this turn
        turn_context = {
            "player_input": player_input,
            "session": context.model_dump(),
            "previous_responses": [],
        }

        # Execute agents in order
        for agent_role in agents:
            response = await self._execute_agent(agent_role, turn_context)

            # Update turn context with this response
            turn_context["previous_responses"].append({
                "agent": agent_role.value,
                "content": response.content,
            })

            # Update session context
            context.add_exchange("assistant", response.content, agent_role.value)
            context.tokens_used += response.tokens_used

            yield response

        # Add player input to history
        context.add_exchange("user", player_input)

    async def _execute_agent(
        self,
        agent_role: AgentRole,
        turn_context: dict
    ) -> AgentResponse:
        """Execute a single agent."""

        # Map role to crew agent
        agent_map = {
            AgentRole.INNKEEPER: self.crew.innkeeper_theron,
            AgentRole.NARRATOR: self.crew.narrator,
            AgentRole.CHRONICLER: self.crew.chronicler,
            AgentRole.JESTER: self.crew.jester,
        }

        agent = agent_map[agent_role]

        # Execute via CrewAI
        result = await agent.execute_async(
            task_description=self._build_task(agent_role, turn_context),
            context=turn_context,
        )

        return AgentResponse(
            agent=agent_role,
            content=result.raw,
            annotations=self._extract_annotations(result.raw),
            tokens_used=result.token_usage.total_tokens,
        )

    def _build_task(self, agent_role: AgentRole, turn_context: dict) -> str:
        """Build task description for agent."""

        player_input = turn_context["player_input"]
        session = turn_context["session"]

        tasks = {
            AgentRole.INNKEEPER: f"""
                Respond to the player as Innkeeper Theron.
                Player said: "{player_input}"
                Current location: {session["current_location"]}
                Quest status: {session.get("quest_hook", "No active quest")}
            """,
            AgentRole.NARRATOR: f"""
                Narrate the scene in response to the player.
                Player action: "{player_input}"
                Location: {session["current_location"]}
                Time: {session["time_of_day"]}
                End with "What do you do?" or present 3-4 choices.
            """,
            AgentRole.CHRONICLER: f"""
                Check if this action needs a dice roll.
                Action: "{player_input}"
                Character: {session.get("character_sheet", {})}
                If yes, call for a roll and report the result.
                Keep it short.
            """,
            AgentRole.JESTER: f"""
                Add a complication or observation to the current scene.
                Current situation: {turn_context.get("previous_responses", [])}
                Be brief. Point out something nobody mentioned.
                Do not mock the player.
            """,
        }

        return tasks[agent_role]

    def _extract_annotations(self, content: str) -> list[str]:
        """Extract agent annotations from response."""
        # Annotations are marked with [[ ]] in agent output
        import re
        return re.findall(r'\[\[(.*?)\]\]', content)
```

---

## Streaming Handler

Manages SSE streaming to the UI:

```python
from fastapi import Request
from fastapi.responses import StreamingResponse
import json


class StreamingHandler:
    """Handles SSE streaming of agent responses."""

    async def stream_turn(
        self,
        request: Request,
        executor: TurnExecutor,
        context: SessionContext,
        player_input: str
    ) -> StreamingResponse:
        """Stream a conversation turn via SSE."""

        async def event_generator():
            try:
                async for response in executor.execute(context, player_input):
                    # Send agent identifier
                    yield self._format_event("agent", {
                        "name": response.agent.value,
                        "display_name": self._display_name(response.agent),
                    })

                    # Stream content in chunks
                    for chunk in self._chunk_content(response.content):
                        yield self._format_event("content", {"text": chunk})

                    # Send annotations
                    if response.annotations:
                        yield self._format_event("annotations", {
                            "items": response.annotations
                        })

                    # Send completion for this agent
                    yield self._format_event("agent_complete", {
                        "agent": response.agent.value
                    })

                # Send turn complete
                yield self._format_event("turn_complete", {
                    "tokens_used": context.tokens_used,
                    "tokens_remaining": context.token_budget - context.tokens_used,
                })

            except Exception as e:
                yield self._format_event("error", {"message": str(e)})

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    def _format_event(self, event_type: str, data: dict) -> str:
        """Format SSE event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def _display_name(self, agent: AgentRole) -> str:
        """Get display name for agent."""
        names = {
            AgentRole.INNKEEPER: "Innkeeper Theron",
            AgentRole.NARRATOR: "Narrator",
            AgentRole.CHRONICLER: "Keeper",
            AgentRole.JESTER: "Jester",
        }
        return names[agent]

    def _chunk_content(self, content: str, chunk_size: int = 50) -> list[str]:
        """Split content into chunks for streaming effect."""
        words = content.split()
        chunks = []
        current = []

        for word in words:
            current.append(word)
            if len(" ".join(current)) >= chunk_size:
                chunks.append(" ".join(current) + " ")
                current = []

        if current:
            chunks.append(" ".join(current))

        return chunks
```

---

## CrewAI Integration

How the conversation engine integrates with CrewAI:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Model configuration (update versions as needed)
SONNET_MODEL = "anthropic/claude-sonnet"  # Narrative agents
HAIKU_MODEL = "anthropic/claude-haiku"    # Mechanics agents


@CrewBase
class TavernCrew:
    """The Tavern Crew for Pocket Portals."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def innkeeper_theron(self) -> Agent:
        """Quest giver and session bookends."""
        return Agent(
            config=self.agents_config["innkeeper_theron"],
            llm=SONNET_MODEL,  # Narrative quality
            verbose=True,
        )

    @agent
    def narrator(self) -> Agent:
        """Scene description and world state."""
        return Agent(
            config=self.agents_config["narrator"],
            llm=SONNET_MODEL,  # Narrative quality
            verbose=True,
        )

    @agent
    def chronicler(self) -> Agent:
        """Dice rolls and game state."""
        return Agent(
            config=self.agents_config["chronicler"],
            llm=HAIKU_MODEL,  # Fast for mechanics
            verbose=True,
        )

    @agent
    def jester(self) -> Agent:
        """Complications and observations."""
        return Agent(
            config=self.agents_config["jester"],
            llm=HAIKU_MODEL,  # Fast for brief interjections
            verbose=True,
        )

    def create_turn_task(self, agent_role: str, context: dict) -> Task:
        """Create a task for a single turn."""
        return Task(
            description=context["task_description"],
            expected_output="A response in the agent's voice",
            agent=getattr(self, agent_role)(),
        )
```

---

## Agent Configuration

### config/agents.yaml

```yaml
innkeeper_theron:
  role: "Innkeeper Theron"
  goal: "Welcome adventurers, introduce quests, and provide session bookends"
  backstory: |
    You are Theron, keeper of the Crossroads Tavern. You've run this place
    for thirty years, seen hundreds of adventurers come through. Most don't
    come back. The ones who do have stories worth hearing.

    Your voice:
    - Speak in short, direct sentences
    - Reference past adventurers who tried similar things
    - Use concrete prices and distances
    - Never use words like "epic" or "legendary"
    - Open with observations, then get to the point

    You do NOT:
    - Explain moral lessons
    - Offer tactical advice unless asked
    - Use flowery language

narrator:
  role: "Narrator"
  goal: "Paint vivid scenes and present meaningful choices"
  backstory: |
    You are the voice that describes the world. Present tense. Sensory
    details. Let the player see, hear, smell what's happening.

    Your voice:
    - Lead with the most important sensory detail
    - Use specific numbers: "Twenty feet away", "Three guards"
    - End scenes with "What do you do?" or present 3-4 choices
    - Match the player's tone (serious, light, chaotic)

    You do NOT:
    - Tell players how their character feels
    - Use metaphors during action
    - Describe outcomes before dice are rolled
    - Add choices labeled "Other" (always allow custom input)

chronicler:
  role: "Keeper"
  goal: "Keep the game honest without slowing it down"
  backstory: |
    You handle the numbers. Dice, health, damage. Quick and clear.
    Say what happened, move on.

    Your voice:
    - Short and direct: "Roll for it. 12 or better."
    - Results first: "That hits. 9 damage."
    - Status when it matters: "You're hurt. 4 health left."

    You do NOT:
    - Lecture about rules
    - Turn simple actions into dice checks
    - Slow the story with mechanics

jester:
  role: "Jester"
  goal: "Add complications and point out what nobody mentioned"
  backstory: |
    You know this is a game. You can see the edges of the story. When
    things get too smooth, you add a wrinkle. When nobody asks the
    obvious question, you ask it.

    Your voice:
    - Casual, conversational
    - Point out mechanical exploits or narrative holes
    - Use modern idioms
    - Keep it brief: one or two sentences

    You do NOT:
    - Mock player decisions
    - Invalidate choices already made
    - Steer toward "correct" answers
    - Appear during combat or epilogue
```

---

## Phase Transitions

How the engine moves between game phases:

```python
class PhaseManager:
    """Manages transitions between game phases."""

    def check_transition(self, context: SessionContext, player_input: str) -> Optional[GamePhase]:
        """Check if phase should transition."""

        current = context.phase

        if current == GamePhase.CHARACTER_CREATION:
            if context.character_sheet and self._player_accepts(player_input):
                return GamePhase.QUEST_INTRODUCTION

        elif current == GamePhase.QUEST_INTRODUCTION:
            if context.quest_hook and self._player_engages(player_input):
                return GamePhase.EXPLORATION

        elif current == GamePhase.EXPLORATION:
            if self._combat_triggered(context, player_input):
                return GamePhase.COMBAT
            elif self._dialogue_triggered(context, player_input):
                return GamePhase.DIALOGUE

        elif current == GamePhase.COMBAT:
            if self._combat_resolved(context):
                return GamePhase.EXPLORATION

        elif current == GamePhase.DIALOGUE:
            if self._dialogue_ended(player_input):
                return GamePhase.EXPLORATION

        # Check for epilogue trigger
        if self._quest_complete(context):
            return GamePhase.EPILOGUE

        return None

    def _player_accepts(self, player_input: str) -> bool:
        accept_phrases = ["accept", "yes", "looks good", "let's go", "start"]
        return any(phrase in player_input.lower() for phrase in accept_phrases)

    def _player_engages(self, player_input: str) -> bool:
        engage_phrases = ["tell me more", "i'll do it", "where", "how much", "accept"]
        return any(phrase in player_input.lower() for phrase in engage_phrases)

    def _combat_triggered(self, context: SessionContext, player_input: str) -> bool:
        combat_phrases = ["attack", "fight", "strike", "cast", "shoot"]
        return any(phrase in player_input.lower() for phrase in combat_phrases)

    def _combat_resolved(self, context: SessionContext) -> bool:
        if not context.combat_state:
            return True
        return context.combat_state.get("resolved", False)

    def _dialogue_triggered(self, context: SessionContext, player_input: str) -> bool:
        dialogue_phrases = ["talk to", "speak with", "ask", "tell them"]
        return any(phrase in player_input.lower() for phrase in dialogue_phrases)

    def _dialogue_ended(self, player_input: str) -> bool:
        end_phrases = ["leave", "goodbye", "walk away", "done talking"]
        return any(phrase in player_input.lower() for phrase in end_phrases)

    def _quest_complete(self, context: SessionContext) -> bool:
        if not context.quest_hook:
            return False
        return context.quest_hook.get("completed", False)
```

---

## Error Handling

```python
from enum import Enum


class ConversationError(Exception):
    """Base exception for conversation engine."""
    pass


class TokenBudgetExceeded(ConversationError):
    """Raised when token budget is exhausted."""
    pass


class AgentTimeout(ConversationError):
    """Raised when agent takes too long to respond."""
    pass


class InvalidPhaseTransition(ConversationError):
    """Raised when attempting invalid phase transition."""
    pass


class ErrorHandler:
    """Handles errors gracefully within conversation flow."""

    def handle(self, error: Exception, context: SessionContext) -> str:
        """Return user-friendly message for error."""

        if isinstance(error, TokenBudgetExceeded):
            return self._budget_exceeded_message(context)

        elif isinstance(error, AgentTimeout):
            return self._timeout_message()

        else:
            return self._generic_error_message()

    def _budget_exceeded_message(self, context: SessionContext) -> str:
        return """
The tale has grown long, and even the Keeper's quill needs rest.

Your adventure has reached its natural pause. You can:
- Download your adventure log to continue another day
- Start a fresh adventure with a new character

What would you like to do?
"""

    def _timeout_message(self) -> str:
        return """
The mists of uncertainty cloud the tavern for a moment...

*The Narrator clears their throat*

"Apologies, traveler. Where were we?"

(Please try your action again.)
"""

    def _generic_error_message(self) -> str:
        return """
Something went wrong in the telling of this tale.

The Innkeeper slides you a fresh mug. "On the house. Try again?"
"""
```

---

## Usage Example

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

# Initialize components
crew = TavernCrew()
router = AgentRouter()
executor = TurnExecutor(crew, router)
streaming = StreamingHandler()

# Session storage (in-memory for MVP)
sessions: dict[str, SessionContext] = {}


@app.post("/turn")
async def handle_turn(request: Request, session_id: str, player_input: str):
    """Handle a single conversation turn."""

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = SessionContext(session_id=session_id)

    context = sessions[session_id]

    # Check for phase transition
    phase_manager = PhaseManager()
    new_phase = phase_manager.check_transition(context, player_input)
    if new_phase:
        context.phase = new_phase

    # Stream response
    return await streaming.stream_turn(request, executor, context, player_input)


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state."""
    if session_id not in sessions:
        return {"error": "Session not found"}
    return sessions[session_id].model_dump()
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| First response chunk | < 500ms | Time to first SSE event |
| Full turn completion | < 5s | Time to turn_complete event |
| Token usage per turn | < 2000 | Average across all agents |
| Session memory | < 50KB | Context object size |

---

## Testing

```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_context():
    return SessionContext(
        session_id="test-123",
        phase=GamePhase.EXPLORATION,
        character_name="Grimlock",
        current_location="forest_path",
    )


@pytest.fixture
def mock_crew():
    crew = MagicMock()
    crew.narrator.execute_async = AsyncMock(return_value=MagicMock(
        raw="You step into the clearing. Three paths branch before you.",
        token_usage=MagicMock(total_tokens=150),
    ))
    return crew


class TestAgentRouter:
    def test_exploration_routes_to_narrator(self, mock_context):
        router = AgentRouter()
        agents = router.route(mock_context, "I look around")
        assert AgentRole.NARRATOR in agents

    def test_combat_routes_chronicler_first(self, mock_context):
        mock_context.phase = GamePhase.COMBAT
        router = AgentRouter()
        agents = router.route(mock_context, "I attack the goblin")
        assert agents[0] == AgentRole.CHRONICLER


class TestTurnExecutor:
    @pytest.mark.asyncio
    async def test_executes_agents_in_order(self, mock_context, mock_crew):
        router = AgentRouter()
        executor = TurnExecutor(mock_crew, router)

        responses = []
        async for response in executor.execute(mock_context, "I look around"):
            responses.append(response)

        assert len(responses) >= 1
        assert responses[0].agent == AgentRole.NARRATOR
```

---

*The engine that keeps the conversation flowing.*

---

## Related Documents

- **[product.md](product.md)** - Product requirements and features
- **[architecture.md](architecture.md)** - System architecture and project structure
- **[creative-writing.md](creative-writing.md)** - Agent voices and writing guidelines
- **[crewai.md](crewai.md)** - CrewAI project patterns
