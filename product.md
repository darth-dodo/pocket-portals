# Pocket Portals
## Product Requirements Document

**Version 1.0 | December 2025**

---

## 1. Executive Summary

Pocket Portals is a web application that generates personalized one-shot D&D adventures using multi-agent AI. Users enter a magical tavern, describe their character in plain English, and receive a complete adventure run by a crew of AI agents — complete with dice rolls, NPC interactions, combat, and branching narrative outcomes. Built on CrewAI and Anthropic Claude.

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

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Agent Framework | CrewAI |
| LLM Provider | Anthropic Claude (Sonnet for narrative, Haiku for mechanics) |
| Backend | FastAPI |
| Frontend | HTMX + Jinja2 Templates |
| Deployment | Fly.io |

---

## 6. Functional Requirements

### 6.1 User Input & Character Creation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Accept free-form character description (text input) | P0 — Must Have |
| FR-02 | Generate character sheet (stats, equipment, backstory) | P0 — Must Have |
| FR-03 | Allow user to accept or modify generated character | P0 — Must Have |
| FR-04 | Display parallel agent activity during generation | P1 — Should Have |

### 6.2 Narrative & Quest System

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05 | Generate personalized quest based on character backstory | P0 — Must Have |
| FR-06 | Stream narrative text in real-time (typewriter effect) | P0 — Must Have |
| FR-07 | Present branching choices at decision points | P0 — Must Have |
| FR-08 | Support custom/free-form player responses | P0 — Must Have |
| FR-09 | Maintain world state and consequence tracking | P0 — Must Have |

### 6.3 NPC & Agent System

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10 | Core agents: Innkeeper Theron, Narrator, Keeper, Jester | P0 — Must Have |
| FR-11 | Dynamic NPC generation with distinct personalities | P0 — Must Have |
| FR-12 | NPCs remember player actions within session | P0 — Must Have |
| FR-13 | Agent annotations visible to user (e.g., Jester hints) | P1 — Should Have |

### 6.4 Combat & Mechanics

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-14 | Initiative system with turn order display | P0 — Must Have |
| FR-15 | Dice rolling with animated results | P0 — Must Have |
| FR-16 | Keeper validation of dice rolls and game state | P0 — Must Have |
| FR-17 | HP tracking and damage/healing calculations | P0 — Must Have |
| FR-18 | ASCII battlefield visualization | P2 — Nice to Have |

### 6.5 Epilogue & Output

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-19 | Generate personalized epilogue based on player choices | P0 — Must Have |
| FR-20 | Final character sheet with achievements and relationships | P0 — Must Have |
| FR-21 | Downloadable adventure log | P1 — Should Have |
| FR-22 | Shareable story link | P2 — Nice to Have |

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

---

## 8. Product Architecture

| Component | Function | Key Technologies |
|-----------|----------|------------------|
| Entry Portal | Character input, tavern UI | HTMX, Jinja2 |
| Character Engine | Parallel agent analysis, sheet generation | CrewAI parallel tasks |
| Quest Factory | Personalized adventure generation | CrewAI sequential flow, memory |
| NPC Spawner | Dynamic agent instantiation | CrewAI dynamic agents |
| Combat Manager | Turn-based mechanics, dice tools | CrewAI tools, function calling |
| Flow Controller | State machine, branching logic | CrewAI human-in-loop |
| Stream Handler | Real-time narrative delivery | FastAPI SSE, HTMX |
| Export Service | Adventure log, character sheet output | PDF/Markdown generation |

---

## 9. User Experience Flow

### 9.1 Core Loop

1. **ENTER:** User lands on tavern entrance screen
2. **DESCRIBE:** User inputs character description (free text)
3. **GENERATE:** Parallel crew analyzes input (visible activity indicators)
4. **REVIEW:** User accepts/modifies generated character sheet
5. **HOOK:** Innkeeper introduces quest-giver NPC
6. **PLAY:** Adventure unfolds with choices, dice, combat
7. **RESOLVE:** Epilogue generated based on choices
8. **EXPORT:** Download character sheet and adventure log

### 9.2 Decision Points

At each narrative branch, user is presented with 3-4 predefined choices plus a custom input option. System must gracefully handle unexpected inputs while maintaining narrative coherence.

---

## 10. Dependencies & Constraints

### 10.1 External Dependencies

- **Anthropic Claude API:** Rate limits, token costs, model availability
- **CrewAI Framework:** Version stability, breaking changes
- **Fly.io:** Platform availability, pricing changes

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

- **[architecture.md](architecture.md)** - Technical architecture and XP practices
- **[creative-writing.md](creative-writing.md)** - Agent voices and narrative guidelines
- **[conversation-engine.md](conversation-engine.md)** - Turn-taking and state management
- **[crewai.md](crewai.md)** - CrewAI project template

### 13.3 External References

- CrewAI Documentation: https://docs.crewai.com
- Anthropic Claude API: https://docs.anthropic.com
- FastAPI: https://fastapi.tiangolo.com
- HTMX: https://htmx.org
- Fly.io: https://fly.io/docs

---