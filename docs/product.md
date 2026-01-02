# Pocket Portals
## Product Requirements Document

**Version 1.1 | January 2026**

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Problem Statement](#2-problem-statement)
- [3. Target Audience](#3-target-audience)
- [4. Product Vision](#4-product-vision)
- [5. Technology Stack](#5-technology-stack)
- [6. Functional Requirements](#6-functional-requirements)
- [7. Agent Architecture](#7-agent-architecture)
- [8. Product Architecture](#8-product-architecture)
- [9. User Experience Flow](#9-user-experience-flow)
- [10. Dependencies & Constraints](#10-dependencies--constraints)
- [11. Risks & Mitigations](#11-risks--mitigations)
- [12. Open Questions](#12-open-questions)
- [13. Appendix](#13-appendix)

---

## 1. Executive Summary

Pocket Portals is a web application that generates personalized one-shot D&D adventures using multi-agent AI. Users enter a magical tavern, describe their character in plain English, and receive a complete adventure run by a crew of AI agents — complete with dice rolls, NPC interactions, combat, and branching narrative outcomes. Built on CrewAI and Anthropic Claude.

### Current Implementation Status

#### ✅ Completed Features

| Category | Feature | Details |
|----------|---------|---------|
| **Backend** | FastAPI REST API | `/health`, `/start`, `/action`, `/action/stream` endpoints |
| **Backend** | SSE Streaming | Real-time agent responses via Server-Sent Events |
| **Backend** | Session Management | UUID-based multi-user support with in-memory state |
| **Agents** | Multi-Agent System | Narrator, Keeper, Jester, Innkeeper, CharacterInterviewer, QuestDesigner, Epilogue |
| **Agents** | Agent Router | Phase-based routing with mechanical keyword detection |
| **Agents** | Turn Executor | Context accumulation across sequential agent calls |
| **Agents** | Character Creation | Dynamic 5-turn LLM-powered interview with CharacterInterviewerAgent |
| **Agents** | Quest Selection | 3 personalized quest options with QuestDesignerAgent |
| **Agents** | Adventure Pacing | 50-turn narrative arc with 5 phases, EpilogueAgent for conclusions |
| **Orchestration** | CrewAI Flows | `@start`, `@listen`, `@router` decorator-based orchestration |
| **Config** | YAML-based Config | `agents.yaml`, `tasks.yaml` for agent personalities |
| **Frontend** | Modern RPG UI | Custom CSS (NES.css removed), mobile-first design |
| **Frontend** | Mobile Experience | Haptic feedback, 48px touch targets, iOS safe areas, bottom sheet |
| **Frontend** | SSE Integration | Real-time agent indicators (Narrator/Keeper/Jester) |
| **Frontend** | Choice System | 3 predefined options + free text input |
| **Frontend** | Theme System | 5 themes (RPG, Modern, Midnight, Mono, iOS) with localStorage persistence |
| **Combat** | D&D 5e Mechanics | Initiative, attack/defend/flee, HP tracking, dice rolling |
| **DevOps** | Docker | Multi-stage build with docker-compose |
| **DevOps** | CI/CD | GitHub Actions with lint, test, coverage gates |
| **Quality** | Python Tests | 408 tests passing, 77% coverage |
| **Quality** | JavaScript Tests | 415 tests passing, 96.49% coverage |
| **Quality** | XP Practices | TDD, pre-commit hooks (ruff, mypy), continuous integration |
| **Docs** | E2E Test Suite | Playwright-based testing with 10 documented scenarios |

#### ✅ Recently Completed (January 2026)

| Feature | Details |
|---------|---------|
| Quest Selection Flow | QUEST_SELECTION phase with 3 personalized quest options |
| Quest Progress Tracking | `check_quest_progress()` integrated in action loop |
| Quest Personalization | Class-specific quest generation using CHARACTER_STRENGTHS |
| Quest Variety | Shuffled quest pool ensures diverse options |

#### 🚧 In Progress

| Feature | Requirements | Status |
|---------|--------------|--------|
| Character Sheet Display | FR-03 | Show character info in frontend UI |

#### 📋 Planned

| Feature | Priority | Dependencies |
|---------|----------|--------------|
| Character Stat Influence | P1 | Keeper uses stats for mechanical resolution |
| Export Features | P1 | Adventure log download |
| Shareable Story Links | P2 | Adventure sharing |
| Quest Completion Loop | P1 | New quests after completing current quest |

---

## 2. Problem Statement

### 2.1 Current State

- Solo D&D experiences lack the dynamic, responsive storytelling of a human DM
- Existing AI narrative tools produce generic, non-personalized content
- No product delivers complete one-shot adventures tailored to user-created characters

### 2.2 Desired Future State

Users receive fully personalized adventures in minutes. The AI crew adapts to their character's backstory, tracks consequences, and delivers emotionally resonant conclusions — no prep, no waiting for a group.

---

## 3. Target Audience

### 3.1 Primary Persona: The Solo Adventurer

- D&D curious or experienced, lacks consistent group
- Wants narrative experiences without scheduling hassles
- Values personalization and replayability

### 3.2 Secondary Persona: The Creative Writer

- Uses RPG frameworks for character development and story ideation
- Wants to see their characters tested in dynamic scenarios
- Values exportable adventure logs for reference

---

## 4. Product Vision

### 4.1 Core Value Proposition

*"Your character. Your adventure. No group required."*

Pocket Portals delivers the magic of a skilled Dungeon Master on demand — personalized quests, memorable NPCs, meaningful choices, and consequences that matter.

### 4.2 Design Principles

1. **Instant Magic:** Adventure starts within 60 seconds of character input.
2. **Deep Personalization:** Every quest hooks into user's character backstory.
3. **Real Stakes:** Dice matter. Choices matter. Outcomes vary.
4. **Memorable Endings:** Epilogues that resonate and reward investment.

---

## 5. Technology Stack

| Layer | Technology | Status |
|-------|------------|--------|
| Language | Python 3.12 | ✅ |
| Agent Framework | CrewAI | ✅ |
| LLM Provider | Anthropic Claude 3.5 Haiku | ✅ |
| Backend | FastAPI | ✅ |
| Frontend | Vanilla HTML/CSS/JavaScript (ES6 Modules) | ✅ |
| Styling | Custom CSS + RPG Awesome icons + Press Start 2P font | ✅ |
| Testing (Python) | Pytest + pytest-cov (75% coverage) | ✅ |
| Testing (JS) | Vitest + jsdom (96.49% coverage) | ✅ |
| E2E Testing | Playwright MCP | ✅ |
| Containerization | Docker + Docker Compose | ✅ |
| CI/CD | GitHub Actions | ✅ |
| Deployment | Render.com | ✅ |

---

## 6. Functional Requirements

### 6.1 User Input & Character Creation

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Accept free-form character description (text input) | P0 — Must Have | ✅ |
| FR-02 | Generate character sheet (stats, equipment, backstory) | P0 — Must Have | ✅ |
| FR-03 | Allow user to accept or modify generated character | P0 — Must Have | In Progress |
| FR-04 | Display parallel agent activity during generation | P1 — Should Have | Planned |

### 6.2 Narrative & Quest System

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-05 | Generate personalized quest based on character backstory | P0 — Must Have | In Progress |
| FR-06 | Stream narrative text in real-time (typewriter effect) | P0 — Must Have | ✅ |
| FR-07 | Present branching choices at decision points | P0 — Must Have | ✅ |
| FR-08 | Support custom/free-form player responses | P0 — Must Have | ✅ |
| FR-09 | Maintain world state and consequence tracking | P0 — Must Have | ✅ |

### 6.3 NPC & Agent System

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-10 | Core agents: Innkeeper Theron, Narrator, Keeper, Jester | P0 — Must Have | ✅ All implemented (Innkeeper needs flow integration) |
| FR-11 | Dynamic NPC generation with distinct personalities | P0 — Must Have | Planned |
| FR-12 | NPCs remember player actions within session | P0 — Must Have | ✅ |
| FR-13 | Agent annotations visible to user (e.g., Jester hints) | P1 — Should Have | Planned |

### 6.4 Combat & Mechanics

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-14 | Initiative system with turn order display | P0 — Must Have | ✅ |
| FR-15 | Dice rolling with animated results | P0 — Must Have | ✅ |
| FR-16 | Keeper validation of dice rolls and game state | P0 — Must Have | ✅ |
| FR-17 | HP tracking and damage/healing calculations | P0 — Must Have | ✅ |
| FR-18 | ASCII battlefield visualization | P2 — Nice to Have | Planned |

### 6.5 Epilogue & Output

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19 | Generate personalized epilogue based on player choices | P0 — Must Have | ✅ |
| FR-20 | Final character sheet with achievements and relationships | P0 — Must Have | In Progress |
| FR-21 | Downloadable adventure log | P1 — Should Have | Planned |
| FR-22 | Shareable story link | P2 — Nice to Have | Planned |

---

## 7. Agent Architecture

### 7.1 Core Agents (The Tavern Staff)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        POCKET PORTALS AGENTS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🍺 INNKEEPER THERON          📜 NARRATOR                          │
│  ├─ Quest introductions       ├─ Scene descriptions                │
│  ├─ NPC broker                ├─ World state narration             │
│  ├─ Session bookends          ├─ Phase-aware pacing guidelines     │
│  └─ Weary, direct voice       └─ Sensory, present-tense            │
│                                                                     │
│  🎲 KEEPER                    🎭 JESTER                             │
│  ├─ Dice roll validation      ├─ Chaos injection (15% chance)      │
│  ├─ HP/damage tracking        ├─ Meta-commentary                   │
│  ├─ Game state enforcement    ├─ Fourth-wall awareness             │
│  └─ Terse, mechanical         └─ Knowing, playful                  │
│                                                                     │
│  🎭 CHARACTER INTERVIEWER     📖 EPILOGUE                          │
│  ├─ Dynamic character creation├─ Personalized conclusions          │
│  ├─ 5-turn LLM interview      ├─ Adventure summary                 │
│  ├─ Fallback mechanisms       ├─ Character growth reflection       │
│  └─ Creative, engaging        └─ Dramatic, rewarding               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| Agent | Role | Personality | Integration Status |
|-------|------|-------------|-------------------|
| **Innkeeper Theron** | Quest introduction, NPC broker, session bookends | Weary, direct, speaks from experience | ✅ In flow |
| **Narrator** | Narrative generation, world state, scene description | Sensory, present-tense, phase-aware pacing | ✅ In flow |
| **Keeper** | Dice rolls, health tracking, game state | Terse, functional, stays out of the way | ✅ In flow |
| **Jester** | Complications, observations, meta-commentary | Knowing, casual, fourth-wall aware | ✅ In flow |
| **CharacterInterviewer** | Dynamic character creation, 5-turn interview | Creative, engaging, context-aware | ✅ In flow |
| **Epilogue** | Personalized adventure conclusions | Dramatic, rewarding, reflective | ✅ In flow |

### 7.2 Agent Interaction Model

```
Player Action
     │
     ▼
┌─────────────┐     ┌─────────────────────────────────────┐
│ AgentRouter │────▶│ Routing Decision                    │
└─────────────┘     │ • Phase-based (exploration/combat)  │
                    │ • Keyword detection (attack, roll)  │
                    │ • Jester probability (15%, 3-turn   │
                    │   cooldown)                         │
                    └─────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    TurnExecutor                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ Narrator │───▶│  Keeper  │───▶│  Jester  │          │
│  │ (always) │    │(if mech) │    │(if rand) │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│        │              │               │                 │
│        └──────────────┴───────────────┘                 │
│                       │                                 │
│              Context Accumulation                       │
│         (each agent sees previous responses)            │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Combined Narrative
                    + 3 Choice Options
```

### 7.3 LLM Configuration

| Agent | Temperature | Max Tokens | Rationale |
|-------|-------------|------------|-----------|
| Narrator | 0.7 | 1024 | Creative, descriptive storytelling |
| Innkeeper | 0.6 | 512 | Consistent, direct communication |
| Keeper | 0.3 | 256 | Mechanical precision, low variance |
| Jester | 0.8 | 256 | Playful unpredictability |

### 7.4 Technical Implementation

**Agent Pattern:**
```python
class AgentName:
    def __init__(self):
        config = load_agent_config("agent_name")  # From YAML
        self.agent = Agent(role=..., goal=..., llm=...)

    def respond(self, action: str, context: str) -> str:
        task = Task(description=..., agent=self.agent)
        return task.execute_sync()
```

**Key Files:**
- `src/agents/*.py` — Agent implementations
- `src/config/agents.yaml` — Agent personalities and goals
- `src/config/tasks.yaml` — Task templates
- `src/engine/router.py` — AgentRouter logic
- `src/engine/executor.py` — TurnExecutor orchestration

### 7.5 Adventure Pacing System

Every adventure follows a 50-turn narrative arc:

| Phase | Turns | Description |
|-------|-------|-------------|
| **Setup** | 1-5 | Establish world and hook |
| **Rising Action** | 6-20 | Develop complications |
| **Mid Point** | 21-30 | Major revelation or shift |
| **Climax** | 31-42 | Final confrontation |
| **Denouement** | 43-50 | Resolution and epilogue |

- Minimum 25 turns before quest can trigger ending
- Hard cap at 50 turns
- PacingContext provides urgency and directive hints to agents
- EpilogueAgent generates personalized conclusions

### 7.6 Pending Implementation

| Feature | Description | Priority |
|---------|-------------|----------|
| Character Sheet UI | Display character info in frontend | High |
| Character Stat Influence | Keeper uses stats for resolution | Medium |
| Dynamic NPC Spawning | Agent instantiation from templates | Low |

---

## 8. Product Architecture

| Component | Function | Key Technologies | Status |
|-----------|----------|------------------|--------|
| Entry Portal | Adventure start, choice presentation | Custom CSS, ES6 Modules | ✅ |
| Character Engine | Dynamic interview, sheet generation | CharacterInterviewerAgent, CrewAI | ✅ |
| Quest Factory | Personalized adventure generation | CrewAI sequential flow, memory | ✅ |
| NPC Spawner | Dynamic agent instantiation | CrewAI dynamic agents | Planned |
| Combat Manager | Turn-based mechanics, dice tools | CombatManager, DiceRoller | ✅ |
| Pacing Engine | 50-turn narrative arc management | PacingContext, AdventurePhase | ✅ |
| Flow Controller | State machine, branching logic | FastAPI sessions, in-memory state | ✅ |
| Narrative Handler | Real-time narrative delivery | FastAPI REST + SSE endpoints | ✅ |
| Epilogue Generator | Personalized adventure conclusions | EpilogueAgent with fallbacks | ✅ |
| Export Service | Adventure log, character sheet output | PDF/Markdown generation | Planned |

**Current API Endpoints:**
- `GET /health` - Health check with environment info
- `GET /start` - Initialize new adventure session with starter choices
- `POST /action` - Process player action and return narrative response

---

## 9. User Experience Flow

### 9.1 Core Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADVENTURE FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │  ENTER  │───▶│  START  │───▶│ DESCRIBE│───▶│  PLAY   │     │
│  │   ✅    │    │   ✅    │    │   🚧    │    │   ✅    │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│   Welcome        Begin          Character       Turn-based     │
│   Screen        Adventure       Creation        Adventure      │
│                                                    │            │
│                                                    ▼            │
│                              ┌─────────┐    ┌─────────┐        │
│                              │ RESOLVE │◀───│CONTINUE │◀───┘   │
│                              │   📋    │    │   ✅    │        │
│                              └─────────┘    └─────────┘        │
│                               Epilogue       Loop back          │
│                                  │                              │
│                                  ▼                              │
│                              ┌─────────┐                        │
│                              │ EXPORT  │                        │
│                              │   📋    │                        │
│                              └─────────┘                        │
│                              Download log                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Phase | Status | Description |
|-------|--------|-------------|
| **ENTER** | ✅ | User lands on modern RPG-styled welcome screen |
| **START** | ✅ | Click "Begin Quest" → welcome narrative + 3 starter choices |
| **DESCRIBE** | ✅ | Character creation via CharacterInterviewerAgent (5-turn interview) |
| **PLAY** | ✅ | Turn-based adventure with multi-agent responses (50-turn arc) |
| **CONTINUE** | ✅ | Receive new choices, loop back to PLAY |
| **RESOLVE** | ✅ | EpilogueAgent generates personalized conclusion |
| **EXPORT** | 📋 | Download adventure log |

### 9.2 Turn Flow (PLAY Phase)

```
┌──────────────────────────────────────────────────────────────┐
│                       SINGLE TURN                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Player Input                                                │
│  ├─ Choice button (1-3)                                      │
│  └─ OR custom text input                                     │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │  POST /action   │  (or /action/stream for SSE)           │
│  │  {action,       │                                         │
│  │   session_id}   │                                         │
│  └─────────────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  AgentRouter    │───▶│  TurnExecutor   │                 │
│  │  (route agents) │    │  (run agents)   │                 │
│  └─────────────────┘    └─────────────────┘                 │
│                                │                             │
│                                ▼                             │
│  Response                                                    │
│  ├─ Combined narrative (Narrator + Keeper? + Jester?)       │
│  ├─ 3 new choices                                           │
│  └─ Session state updated                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 9.3 SSE Streaming Events

When using `/action/stream`, the frontend receives real-time events:

| Event | Payload | UI Action |
|-------|---------|-----------|
| `routing` | `{agents: [...], reason: "..."}` | Log which agents will respond |
| `agent_start` | `{agent: "narrator"}` | Show "Narrator is speaking..." indicator |
| `agent_response` | `{agent: "narrator", content: "..."}` | Display agent's message |
| `choices` | `{choices: ["...", "...", "..."]}` | Update choice buttons |
| `complete` | `{session_id: "..."}` | Hide loading, enable input |
| `error` | `{message: "..."}` | Show error message |

---

## 10. Dependencies & Constraints

### 10.1 External Dependencies

- **Anthropic Claude API:** Rate limits, token costs, model availability
- **CrewAI Framework:** Version stability, breaking changes
- **Render.com:** Platform availability, pricing changes

### 10.2 Technical Constraints

- Session state must be maintained server-side (no client-side persistence required for MVP)
- Target response latency: <3s for narrative chunks, <500ms for dice rolls
- Mobile-responsive design required; primary target is desktop

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucination breaks game logic | High | Rules Lawyer agent validates all mechanical outputs; structured output schemas |
| API costs exceed budget | Medium | Haiku for routine tasks, Sonnet for narrative; token budgets per session |
| CrewAI breaking changes | Medium | Pin versions; abstract framework behind internal interfaces |
| Narrative coherence degrades over long sessions | Medium | Summarization checkpoints; sliding context window management |
| Inappropriate content generation | High | Claude's built-in guardrails; content filter layer; session logging for audit |

---

## 12. Open Questions

1. **Persistence:** Should users be able to save/resume adventures across sessions?
2. **Multiplayer:** Future scope for co-op adventures?
3. **Monetization:** Free tier with limited adventures vs. subscription?
4. **Narrator Personas:** How many alternative narration styles? User-selectable?
5. **Content Rating:** PG-13 default with optional mature toggle?

---

## 13. Appendix

### 13.1 Glossary

- **Agent:** An LLM-powered entity with defined role, tools, and personality
- **Crew:** A coordinated group of agents working on a task
- **One-shot:** A self-contained adventure completable in a single session
- **World State:** Persistent context tracking choices, relationships, and consequences
- **Human-in-Loop:** Workflow pattern requiring user input at decision points

### 13.2 Related Documents

- **[Architecture](reference/architecture.md)** - Technical architecture and XP practices
- **[Creative Writing](reference/creative-writing.md)** - Agent voices and narrative guidelines
- **[Conversation Engine](reference/conversation-engine.md)** - Turn-taking and state management
- **[CrewAI Guide](reference/crewai.md)** - CrewAI project template

### 13.3 External References

- CrewAI Documentation: https://docs.crewai.com
- Anthropic Claude API: https://docs.anthropic.com
- FastAPI: https://fastapi.tiangolo.com
- NES.css: https://nostalgic-css.github.io/NES.css/
- Render.com: https://render.com/docs

### 13.4 API Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                        API ENDPOINTS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Core Endpoints                                                 │
│  ├─ GET  /health              → Health check + environment     │
│  ├─ GET  /start?shuffle=true  → New session + starter choices  │
│  ├─ POST /action              → Process action (blocking)      │
│  └─ POST /action/stream       → Process action (SSE stream)    │
│                                                                 │
│  Agent Endpoints (Standalone)                                   │
│  ├─ GET  /innkeeper/quest?character=...  → Quest intro         │
│  ├─ POST /keeper/resolve      → Mechanical resolution          │
│  └─ POST /jester/complicate   → Add complication               │
│                                                                 │
│  Static Files                                                   │
│  ├─ GET  /                    → index.html                     │
│  └─ GET  /static/*            → CSS, JS, images                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 13.5 Development Roadmap

| Phase | Features | Status |
|-------|----------|--------|
| **Phase 1: Foundation** | FastAPI, Narrator, Sessions, Docker | ✅ Complete |
| **Phase 2: Multi-Agent** | Keeper, Jester, Router, Executor | ✅ Complete |
| **Phase 3: Streaming** | SSE endpoint, Frontend integration | ✅ Complete |
| **Phase 4: Character** | CharacterInterviewerAgent, 5-turn interview, content safety | ✅ Complete |
| **Phase 5: Combat** | D&D 5e mechanics, DiceRoller, CombatManager, HP tracking | ✅ Complete |
| **Phase 6: Pacing** | 50-turn arc, 5 phases, EpilogueAgent | ✅ Complete |
| **Phase 7: Mobile UX** | Haptic feedback, touch targets, safe areas, bottom sheet | ✅ Complete |
| **Phase 8: Testing** | 368 Python tests (75%), 415 JS tests (96.49%), E2E suite | ✅ Complete |
| **Phase 9: Polish** | Character sheet UI, stat influence, export features | 🚧 In Progress |

### 13.6 XP Practices

This project follows **Extreme Programming (XP)** methodology:

| Practice | Implementation |
|----------|----------------|
| **TDD** | Red-Green-Refactor cycle for all features |
| **Simple Design** | Build simplest solution that works |
| **Small Steps** | Commits every 15-30 min |
| **YAGNI** | No speculative features |
| **CI** | GitHub Actions with lint + test gates |
| **Quality Gates** | Pre-commit hooks (ruff, mypy), 70% coverage minimum |

See `docs/xp.md` for comprehensive XP guide.

---
