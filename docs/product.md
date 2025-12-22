# Pocket Portals
## Product Requirements Document

**Version 1.0 | December 2025**

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

**✅ Completed Features:**
- FastAPI backend with health, start, and action endpoints
- NarratorAgent using CrewAI + Anthropic Claude Sonnet 4
- Session management for multi-user support
- YAML-based agent configuration (agents.yaml, tasks.yaml)
- Conversation context passing to LLM for continuity
- Choice system with 3 predefined options + free text input
- Starter choices with shuffle feature (9 adventure hooks pool)
- Retro RPG web UI with NES.css styling
- Docker containerization with multi-stage build
- Improved UI readability with proper newline rendering
- CORS middleware for development environment

**🚧 In Progress:**
- Character creation and personalization system
- Additional core agents (Innkeeper, Keeper, Jester)

**📋 Planned:**
- Full multi-agent crew orchestration
- Combat mechanics and dice rolling system
- Character sheet generation
- Adventure epilogue and export features

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
| LLM Provider | Anthropic Claude Sonnet 4 (claude-sonnet-4-20250514) | ✅ |
| Backend | FastAPI | ✅ |
| Frontend | Vanilla HTML/CSS/JavaScript with NES.css | ✅ |
| Styling | NES.css (retro RPG theme) + Press Start 2P font | ✅ |
| Containerization | Docker + Docker Compose | ✅ |
| Deployment | Render.com | ✅ |

---

## 6. Functional Requirements

### 6.1 User Input & Character Creation

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Accept free-form character description (text input) | P0 — Must Have | In Progress |
| FR-02 | Generate character sheet (stats, equipment, backstory) | P0 — Must Have | Planned |
| FR-03 | Allow user to accept or modify generated character | P0 — Must Have | Planned |
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
| FR-10 | Core agents: Innkeeper Theron, Narrator, Keeper, Jester | P0 — Must Have | ✅ (Narrator) / Planned (Others) |
| FR-11 | Dynamic NPC generation with distinct personalities | P0 — Must Have | Planned |
| FR-12 | NPCs remember player actions within session | P0 — Must Have | ✅ |
| FR-13 | Agent annotations visible to user (e.g., Jester hints) | P1 — Should Have | Planned |

### 6.4 Combat & Mechanics

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-14 | Initiative system with turn order display | P0 — Must Have | Planned |
| FR-15 | Dice rolling with animated results | P0 — Must Have | Planned |
| FR-16 | Keeper validation of dice rolls and game state | P0 — Must Have | Planned |
| FR-17 | HP tracking and damage/healing calculations | P0 — Must Have | Planned |
| FR-18 | ASCII battlefield visualization | P2 — Nice to Have | Planned |

### 6.5 Epilogue & Output

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19 | Generate personalized epilogue based on player choices | P0 — Must Have | Planned |
| FR-20 | Final character sheet with achievements and relationships | P0 — Must Have | Planned |
| FR-21 | Downloadable adventure log | P1 — Should Have | Planned |
| FR-22 | Shareable story link | P2 — Nice to Have | Planned |

---

## 7. Agent Architecture

### 7.1 Core Agents (The Tavern Staff)

| Agent | Role | Personality |
|-------|------|-------------|
| **Innkeeper Theron** | Quest introduction, NPC broker, session bookends | Weary, direct, speaks from experience. |
| **Narrator** | Narrative generation, world state, scene description | Sensory, present-tense, adapts to player tone. |
| **Keeper** | Dice rolls, health tracking, game state | Terse, functional, stays out of the way. |
| **Jester** | Complications, observations, meta-commentary | Knowing, casual, fourth-wall aware. |

### 7.2 Agent Interaction Model

1. **Parallel Analysis:** Character Crew (Innkeeper + Keeper + Jester) runs concurrently on character input
2. **Sequential Handoff:** Narrator receives consolidated character context, generates quest
3. **Dynamic Spawning:** NPC agents instantiated as needed with inherited world state
4. **Tool Delegation:** Keeper owns dice tools; Narrator owns narrative tools

### 7.3 Current Implementation Notes

**Implemented:**
- **NarratorAgent:** Fully functional with YAML configuration, using Claude Sonnet 4 with temperature 0.7 and max_tokens 1024
- **Session Management:** In-memory session storage with UUID-based session IDs for multi-user support
- **Conversation Context:** History tracking and context building for narrative continuity across turns
- **Choice System:**
  - 3 predefined choices presented per turn (stored per session)
  - Free text input support via `action` field
  - Choice selection via `choice_index` (1-3)
  - Starter choices pool with 9 adventure hooks, shuffleable via query parameter

**Technical Decisions:**
- Using CrewAI's native LLM class (no langchain dependency)
- YAML-based configuration for agents and tasks (src/config/)
- Synchronous task execution with `task.execute_sync()`
- Static file serving for frontend (index.html)
- CORS enabled for development environment

**Pending Implementation:**
- Additional agents (Innkeeper, Keeper, Jester)
- Parallel agent execution with CrewAI crews
- Dynamic NPC spawning
- Character sheet generation
- Combat mechanics and dice rolling tools

---

## 8. Product Architecture

| Component | Function | Key Technologies | Status |
|-----------|----------|------------------|--------|
| Entry Portal | Adventure start, choice presentation | NES.css, vanilla JavaScript | ✅ |
| Character Engine | Parallel agent analysis, sheet generation | CrewAI parallel tasks | Planned |
| Quest Factory | Personalized adventure generation | CrewAI sequential flow, memory | ✅ (Basic) |
| NPC Spawner | Dynamic agent instantiation | CrewAI dynamic agents | Planned |
| Combat Manager | Turn-based mechanics, dice tools | CrewAI tools, function calling | Planned |
| Flow Controller | State machine, branching logic | FastAPI sessions, in-memory state | ✅ |
| Narrative Handler | Real-time narrative delivery | FastAPI REST endpoints | ✅ |
| Export Service | Adventure log, character sheet output | PDF/Markdown generation | Planned |

**Current API Endpoints:**
- `GET /health` - Health check with environment info
- `GET /start` - Initialize new adventure session with starter choices
- `POST /action` - Process player action and return narrative response

---

## 9. User Experience Flow

### 9.1 Core Loop

**Current Implementation:**
1. **✅ ENTER:** User lands on retro RPG-styled welcome screen
2. **✅ START:** Click "Begin Adventure" to receive welcome narrative and 3 starter choices
3. **✅ CHOOSE:** Select from 3 predefined choices or enter custom action via free text
4. **✅ PLAY:** Narrator responds with immersive narrative, maintaining conversation history
5. **✅ CONTINUE:** Receive new choices and continue the adventure
6. **🚧 DESCRIBE:** Character creation (pending)
7. **📋 RESOLVE:** Epilogue generation (planned)
8. **📋 EXPORT:** Download adventure log (planned)

**Implemented Flow Details:**
- Session created on `/start` with unique UUID
- Player selects action via choice button (1-3) or custom input field
- Action sent to `/action` endpoint with session_id
- Narrator processes action with full conversation context
- Response includes narrative text and 3 new choices
- Session history maintained in memory for continuity

### 9.2 Decision Points

**Current Implementation:**
- Each turn presents exactly 3 predefined choices (e.g., "Investigate further", "Talk to someone nearby", "Move to a new location")
- Custom input field accepts free-form player actions
- System validates that either a choice or custom action is provided
- Narrator receives context of all previous turns for coherent responses
- Starter choices can be randomized via `shuffle=true` query parameter

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

### 13.4 Implementation Achievements

**Core Infrastructure (✅ Complete):**
- FastAPI backend with health monitoring and RESTful endpoints
- Session-based state management supporting concurrent users
- Docker containerization with multi-stage builds for production deployment
- Environment-aware CORS configuration for development/production

**AI Agent System (✅ Complete):**
- NarratorAgent with CrewAI framework integration
- YAML-based configuration system for agents and tasks
- Anthropic Claude Sonnet 4 integration via native CrewAI LLM class
- Conversation context tracking and history management
- Synchronous task execution pattern

**User Experience (✅ Complete):**
- Retro RPG aesthetic with NES.css framework
- Press Start 2P font for authentic 8-bit feel
- Responsive design with mobile-friendly interface
- Proper text rendering with newline preservation
- Interactive choice system (3 options + custom input)
- Adventure hook system with 9 diverse starter scenarios
- Shuffle functionality for replay variety

**API Design (✅ Complete):**
- `/health` - Environment monitoring
- `/start` - Session initialization with configurable starter choices
- `/action` - Turn-based narrative progression with dual input modes

**Next Development Priorities:**
1. Character creation and sheet generation system
2. Expand agent crew (Innkeeper, Keeper, Jester)
3. Parallel agent execution workflows
4. Combat mechanics with dice rolling
5. Adventure epilogue and export features

---