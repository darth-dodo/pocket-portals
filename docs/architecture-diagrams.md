# Pocket Portals Architecture Diagrams

Comprehensive Mermaid diagrams documenting the system architecture, game flows, and component interactions.

---

## Table of Contents

1. [System Architecture](#1-system-architecture-diagram)
2. [Complete Game Flow](#2-complete-game-flow)
3. [Agent Routing Decision Flow](#3-agent-routing-decision-flow)
4. [Turn Execution Flow (CrewAI)](#4-turn-execution-flow-crewai-flow)
5. [State Management Architecture](#5-state-management-architecture)
6. [Combat System Flow](#6-combat-system-flow)
7. [Streaming Response Flow](#7-streaming-response-flow)
8. [Configuration-Driven Agent Architecture](#8-configuration-driven-agent-architecture)

---

## 1. System Architecture Diagram

High-level view of all system components and their relationships.

```mermaid
flowchart TB
    subgraph Client["🌐 Client Layer"]
        Browser["Browser<br/>NES.css Frontend"]
        SSE["SSE Stream<br/>Real-time Updates"]
    end

    subgraph API["⚡ API Layer (FastAPI)"]
        Main["main.py"]
        Endpoints["Endpoints"]

        subgraph Routes["Routes"]
            Start["/start"]
            Action["/action"]
            ActionStream["/action/stream"]
            CombatStart["/combat/start"]
            CombatAction["/combat/action"]
        end
    end

    subgraph Engine["🎮 Engine Layer"]
        Router["AgentRouter<br/>• MECHANICAL_KEYWORDS<br/>• JESTER_PROBABILITY<br/>• JESTER_COOLDOWN"]
        Executor["TurnExecutor"]
        Flow["ConversationFlow<br/>CrewAI Flow"]
        CombatMgr["CombatManager<br/>• Initiative<br/>• Attack/Defend/Flee<br/>• Turn Order"]
    end

    subgraph Agents["🤖 Agent Layer (CrewAI)"]
        Narrator["NarratorAgent<br/>40-80 words"]
        Keeper["KeeperAgent<br/><10 words"]
        Jester["JesterAgent<br/>15% chance"]
        Innkeeper["InnkeeperAgent<br/>30-50 words"]
        Interviewer["CharacterInterviewer<br/>5-turn flow"]
    end

    subgraph State["💾 State Layer"]
        SessionMgr["SessionManager"]

        subgraph Backends["Pluggable Backends"]
            Memory["InMemoryBackend<br/>Development"]
            Redis["RedisBackend<br/>Production"]
        end

        subgraph Models["Pydantic Models"]
            GameState["GameState"]
            CombatState["CombatState"]
            CharSheet["CharacterSheet"]
            FlowState["ConversationFlowState"]
        end
    end

    subgraph Config["⚙️ Configuration"]
        AgentsYAML["agents.yaml<br/>• Personalities<br/>• Word limits<br/>• Temperature"]
        TasksYAML["tasks.yaml<br/>Task templates"]
        Settings["settings.py<br/>Environment"]
    end

    subgraph Data["📊 Data Layer"]
        Enemies["ENEMY_TEMPLATES<br/>• Goblin<br/>• Bandit<br/>• Skeleton<br/>• Wolf<br/>• Orc"]
        Dice["DiceRoller<br/>• roll()<br/>• advantage<br/>• disadvantage"]
    end

    subgraph External["☁️ External"]
        Claude["Anthropic Claude<br/>Haiku 3.5"]
    end

    Browser --> Main
    SSE --> ActionStream

    Main --> Routes
    Routes --> Engine

    Router --> Flow
    Executor --> Flow
    Flow --> Agents
    CombatMgr --> Dice

    Agents --> Claude
    Agents --> Config

    SessionMgr --> Backends
    Backends --> Models

    CombatMgr --> Enemies
    CombatMgr --> Models
```

---

## 2. Complete Game Flow

Full player journey from app start through character creation, exploration, and combat.

```mermaid
flowchart TD
    Start([🎮 Player Opens App]) --> NewSession[Create Session<br/>UUID Generated]
    NewSession --> CharCreation{Skip Character<br/>Creation?}

    CharCreation -->|Yes| DefaultChar[Create Default<br/>Human Fighter]
    CharCreation -->|No| Interview[Character Interview<br/>Phase]

    subgraph CharacterCreation["📝 Character Creation (5 Turns)"]
        Interview --> Turn1[Turn 1: Who are you?]
        Turn1 --> Turn2[Turn 2: Skills & abilities?]
        Turn2 --> Turn3[Turn 3: Motivation?]
        Turn3 --> Turn4[Turn 4: Equipment?]
        Turn4 --> Turn5[Turn 5: Summary]
        Turn5 --> ParseHistory[Parse History<br/>Extract Race/Class/Name]
    end

    ParseHistory --> CharSheet[Generate<br/>CharacterSheet]
    DefaultChar --> CharSheet
    CharSheet --> SetPhase[Set Phase:<br/>EXPLORATION]

    SetPhase --> AdventureHooks[Generate Contextual<br/>Adventure Hooks]
    AdventureHooks --> GameLoop

    subgraph GameLoop["🔄 Main Game Loop"]
        ShowNarrative[Display Narrative<br/>+ 3 Choices]
        ShowNarrative --> PlayerInput{Player Input}

        PlayerInput -->|Choice 1-3| ResolveChoice[Map Choice Index<br/>to Action Text]
        PlayerInput -->|Custom Text| CustomAction[Use Custom<br/>Action Text]

        ResolveChoice --> ContentFilter
        CustomAction --> ContentFilter

        ContentFilter[Content Safety<br/>Filter] --> SafeAction{Safe?}
        SafeAction -->|No| Redirect[Redirect to<br/>Safe Action]
        SafeAction -->|Yes| RouteAction
        Redirect --> RouteAction

        RouteAction[AgentRouter<br/>Decides Agents] --> ExecuteAgents

        subgraph ExecuteAgents["Execute Agents"]
            ExecNarrator[Narrator<br/>Describes Scene]
            ExecNarrator --> ExecKeeper{Mechanical<br/>Keywords?}
            ExecKeeper -->|Yes| RunKeeper[Keeper<br/>Resolves Action]
            ExecKeeper -->|No| CheckJester
            RunKeeper --> CheckJester
            CheckJester{Jester<br/>Roll?}
            CheckJester -->|15% & Cooldown OK| RunJester[Jester<br/>Adds Chaos]
            CheckJester -->|No| Aggregate
            RunJester --> Aggregate
        end

        Aggregate[Aggregate<br/>Responses] --> GenerateChoices[Generate<br/>Contextual Choices]
        GenerateChoices --> UpdateSession[Update Session<br/>• Add Exchange<br/>• Track Agents]
        UpdateSession --> ShowNarrative
    end

    PlayerInput -->|Combat Trigger| StartCombat[Start Combat<br/>Encounter]

    subgraph CombatLoop["⚔️ Combat Loop"]
        StartCombat --> InitRoll[Roll Initiative<br/>d20 + DEX]
        InitRoll --> DetermineOrder[Sort by<br/>Initiative]
        DetermineOrder --> CombatTurn{Whose Turn?}

        CombatTurn -->|Player| PlayerTurn[Player Turn]
        CombatTurn -->|Enemy| EnemyTurn[Enemy Attacks]

        PlayerTurn --> PlayerAction{Action?}
        PlayerAction -->|Attack| PlayerAttack[Roll Attack<br/>d20 + MOD vs AC]
        PlayerAction -->|Defend| PlayerDefend[Set Defending<br/>Enemy Disadvantage]
        PlayerAction -->|Flee| PlayerFlee[Roll d20 + DEX<br/>vs DC 12]

        PlayerAttack --> DamageRoll{Hit?}
        DamageRoll -->|Yes| ApplyDamage[Roll Damage<br/>Apply to Enemy]
        DamageRoll -->|No| Miss[Miss!]

        PlayerDefend --> EnemyTurn
        PlayerFlee --> FleeCheck{Success?}
        FleeCheck -->|Yes| Escaped[Combat Ends<br/>Player Escaped]
        FleeCheck -->|No| FreeAttack[Enemy Free Attack<br/>with Advantage]

        ApplyDamage --> CheckDeath{Enemy Dead?}
        Miss --> EnemyTurn
        CheckDeath -->|Yes| Victory[Victory!]
        CheckDeath -->|No| EnemyTurn

        EnemyTurn --> EnemyAttack[Roll Attack<br/>Check Defending]
        EnemyAttack --> EnemyDamage{Hit?}
        EnemyDamage -->|Yes| PlayerDamage[Apply Damage<br/>to Player]
        EnemyDamage -->|No| EnemyMiss[Miss!]

        PlayerDamage --> PlayerDead{Player Dead?}
        EnemyMiss --> NextRound
        PlayerDead -->|Yes| Defeat[Defeat!]
        PlayerDead -->|No| NextRound[Next Round]

        NextRound --> CombatTurn

        Victory --> NarratorSummary[Narrator Summarizes<br/>Battle]
        Defeat --> NarratorSummary
        FreeAttack --> PlayerDead
    end

    NarratorSummary --> GameLoop
    Escaped --> GameLoop
```

---

## 3. Agent Routing Decision Flow

How the AgentRouter determines which agents handle each player action.

```mermaid
flowchart TD
    Action[Player Action] --> ParsePhase{Game Phase?}

    ParsePhase -->|CHARACTER_CREATION| CharFlow[Character Interviewer<br/>Handles Directly]
    ParsePhase -->|COMBAT| CombatFlow[Combat Manager<br/>Handles Directly]
    ParsePhase -->|EXPLORATION| ExploreRoute
    ParsePhase -->|DIALOGUE| DialogueRoute

    subgraph ExploreRoute["Exploration Routing"]
        E1[Start with<br/>Narrator] --> E2{Contains<br/>MECHANICAL_KEYWORDS?}
        E2 -->|Yes| E3[Add Keeper]
        E2 -->|No| E4[Narrator Only]
        E3 --> JesterCheck
        E4 --> JesterCheck
    end

    subgraph DialogueRoute["Dialogue Routing"]
        D1[Start with<br/>Narrator] --> D2{Social/Persuasion<br/>Keywords?}
        D2 -->|Yes| D3[May Add Keeper]
        D2 -->|No| D4[Narrator Only]
        D3 --> JesterCheck
        D4 --> JesterCheck
    end

    subgraph JesterCheck["Jester Inclusion Check"]
        J1{Jester in<br/>Recent Agents?} -->|Yes| J2{Cooldown<br/>Elapsed?}
        J1 -->|No| J3[Roll 15%<br/>Probability]
        J2 -->|No| NoJester[No Jester]
        J2 -->|Yes| J3
        J3 -->|Success| AddJester[Include Jester]
        J3 -->|Fail| NoJester
    end

    AddJester --> BuildDecision
    NoJester --> BuildDecision

    BuildDecision[Build RoutingDecision<br/>• agents list<br/>• include_jester<br/>• reason]

    subgraph Keywords["MECHANICAL_KEYWORDS"]
        K1["attack, fight, roll"]
        K2["cast, defend, dodge"]
        K3["swing, shoot, hit, strike"]
    end

    subgraph Constants["Routing Constants"]
        C1["JESTER_PROBABILITY = 0.15"]
        C2["JESTER_COOLDOWN = 3 turns"]
    end
```

---

## 4. Turn Execution Flow (CrewAI Flow)

Detailed flow of how CrewAI orchestrates multi-agent turn execution.

```mermaid
flowchart TD
    subgraph TurnExecutor["TurnExecutor"]
        Start([execute_async]) --> CreateState[Create Initial<br/>ConversationFlowState]
        CreateState --> Kickoff[flow.kickoff_async]
    end

    subgraph CrewAIFlow["ConversationFlow (CrewAI)"]
        subgraph StartPhase["@start()"]
            Route[route_action] --> CheckRouting{Routing<br/>Provided?}
            CheckRouting -->|Yes| UseProvided[Use Provided<br/>Routing]
            CheckRouting -->|No| CallRouter[Call AgentRouter]
            CallRouter --> SetAgents[Set agents_to_invoke<br/>include_jester<br/>routing_reason]
        end

        subgraph ExecutePhase["@listen(route_action)"]
            UseProvided --> Execute
            SetAgents --> Execute
            Execute[execute_agents] --> InitContext[Get Initial<br/>Context]

            InitContext --> Loop{More Agents?}
            Loop -->|Yes| CallAgent[agent.respond<br/>action, context]
            CallAgent --> StoreResponse[Store in<br/>responses dict]
            StoreResponse --> Accumulate[Accumulate Context<br/>'Agent just said: ...']
            Accumulate --> Loop

            Loop -->|No| JesterFlag{include_jester?}
            JesterFlag -->|Yes| CallJester[jester.respond<br/>sees all context]
            JesterFlag -->|No| Done[Done]
            CallJester --> Done
        end

        subgraph RouterPhase["@router(execute_agents)"]
            Done --> CheckError{Error?}
            CheckError -->|Yes| ErrorPath["error"]
            CheckError -->|No| SuccessPath["success"]
        end

        subgraph SuccessPhase["@listen('success')"]
            SuccessPath --> Aggregate[aggregate_responses]
            Aggregate --> JoinNarrative[Join responses<br/>with newlines]
            JoinNarrative --> GenChoices
        end

        subgraph ChoicesPhase["@listen(aggregate_responses)"]
            GenChoices[generate_choices] --> AskNarrator[Ask Narrator for<br/>3 contextual choices]
            AskNarrator --> ParseChoices[Parse numbered<br/>list response]
            ParseChoices --> SetChoices{Valid?}
            SetChoices -->|Yes| UseChoices[Use parsed choices]
            SetChoices -->|No| DefaultChoices[Use DEFAULT_CHOICES]
        end

        subgraph ErrorPhase["@listen('error')"]
            ErrorPath --> HandleError[handle_error]
            HandleError --> ErrorNarrative[Set error narrative<br/>'Magical energies flicker...']
            ErrorNarrative --> DefaultChoices
        end
    end

    UseChoices --> Return
    DefaultChoices --> Return

    Return([Return TurnResult<br/>• responses<br/>• narrative<br/>• choices])
```

---

## 5. State Management Architecture

Backend protocol pattern and data model relationships.

```mermaid
flowchart TB
    subgraph Models["Pydantic Models"]
        GameState["GameState<br/>• session_id<br/>• conversation_history[20]<br/>• current_choices<br/>• character_sheet<br/>• health_current/max<br/>• phase: GamePhase<br/>• creation_turn: 0-5<br/>• recent_agents[5]<br/>• turns_since_jester<br/>• combat_state"]

        CharSheet["CharacterSheet<br/>• name<br/>• race: CharacterRace<br/>• character_class<br/>• stats: StatBlock<br/>• current_hp/max_hp<br/>• backstory"]

        CombatState["CombatState<br/>• is_active<br/>• phase: CombatPhaseEnum<br/>• round_number<br/>• combatants[]<br/>• turn_order[]<br/>• current_turn_index<br/>• enemy_template<br/>• combat_log[]<br/>• player_defending"]

        GameState --> CharSheet
        GameState --> CombatState
    end

    subgraph Enums["Enums"]
        GamePhase["GamePhase<br/>• CHARACTER_CREATION<br/>• EXPLORATION<br/>• COMBAT<br/>• DIALOGUE"]

        CombatPhase["CombatPhaseEnum<br/>• INITIATIVE<br/>• PLAYER_TURN<br/>• ENEMY_TURN<br/>• RESOLUTION"]

        CombatAction["CombatAction<br/>• ATTACK<br/>• DEFEND<br/>• FLEE"]
    end

    subgraph Backend["Backend Protocol"]
        Protocol["SessionBackend (Protocol)<br/>• create(id, state)<br/>• get(id) -> state<br/>• update(id, state)<br/>• delete(id) -> bool<br/>• exists(id) -> bool"]

        Memory["InMemoryBackend<br/>dict[str, GameState]"]
        Redis["RedisBackend<br/>• redis_url<br/>• ttl: 24h<br/>• JSON serialization"]

        Protocol --> Memory
        Protocol --> Redis
    end

    subgraph Factory["Backend Factory"]
        Create["create_backend()"] --> Check{SESSION_BACKEND<br/>setting?}
        Check -->|memory| ReturnMemory[Return InMemoryBackend]
        Check -->|redis| TryRedis[Try Redis Connection]
        TryRedis --> Ping{Ping OK?}
        Ping -->|Yes| ReturnRedis[Return RedisBackend]
        Ping -->|No| Fallback[Log Warning<br/>Fallback to Memory]
        Fallback --> ReturnMemory
    end

    subgraph SessionManager["SessionManager"]
        SM["SessionManager(backend)"]
        SM --> Methods["Methods:<br/>• create_session()<br/>• get_session(id)<br/>• get_or_create_session(id)<br/>• add_exchange(id, action, narrative)<br/>• update_health(id, damage)<br/>• set_character_sheet(id, sheet)<br/>• set_phase(id, phase)<br/>• set_choices(id, choices)<br/>• update_recent_agents(id, agents)<br/>• set_combat_state(id, state)"]
    end

    Factory --> SM
    SM --> Backend
```

---

## 6. Combat System Flow

D&D 5e-inspired combat mechanics with initiative, actions, and resolution.

```mermaid
flowchart TD
    subgraph Init["Combat Initialization"]
        Trigger[Combat Triggered] --> GetEnemy[Get Enemy Template<br/>from ENEMY_TEMPLATES]
        GetEnemy --> CreatePlayer[Create Player Combatant<br/>from CharacterSheet]
        CreatePlayer --> CreateEnemy[Create Enemy Combatant<br/>from Template]
        CreateEnemy --> RollInit[Roll Initiative<br/>Both: 1d20 + DEX mod]
        RollInit --> SortOrder[Sort by Total<br/>Highest First]
        SortOrder --> SetPhase[Set Phase:<br/>PLAYER_TURN or ENEMY_TURN]
    end

    subgraph PlayerActions["Player Actions"]
        PlayerTurn[Player Turn] --> ActionChoice{Action?}

        ActionChoice -->|Attack| Attack
        subgraph Attack["Attack Action"]
            A1[Get Weapon Damage<br/>by Class] --> A2[Calculate Attack Bonus<br/>STR or DEX mod]
            A2 --> A3[Roll 1d20 + bonus]
            A3 --> A4{Total >= AC?}
            A4 -->|Yes| A5[Roll Damage Dice<br/>+ modifier]
            A4 -->|No| A6[Miss - No Damage]
            A5 --> A7[Apply Damage<br/>floor at 0 HP]
        end

        ActionChoice -->|Defend| Defend
        subgraph Defend["Defend Action"]
            D1[Set player_defending = True] --> D2[Log Defensive Stance]
            D2 --> D3[Enemy gets<br/>Disadvantage next attack]
        end

        ActionChoice -->|Flee| Flee
        subgraph Flee["Flee Action"]
            F1[Roll 1d20 + DEX] --> F2{Total >= 12?}
            F2 -->|Yes| F3[Escape!<br/>Combat Ends]
            F2 -->|No| F4[Failed!<br/>Enemy Free Attack<br/>with Advantage]
        end
    end

    subgraph EnemyActions["Enemy Turn"]
        EnemyTurn[Enemy Turn] --> CheckDefend{Player<br/>Defending?}
        CheckDefend -->|Yes| Disadvantage[Roll with<br/>Disadvantage<br/>2d20 take lower]
        CheckDefend -->|No| NormalRoll[Normal Attack<br/>1d20]
        Disadvantage --> EnemyAttack
        NormalRoll --> EnemyAttack
        EnemyAttack[Roll + attack_bonus<br/>vs Player AC] --> EnemyHit{Hit?}
        EnemyHit -->|Yes| EnemyDamage[Roll damage_dice<br/>Apply to Player]
        EnemyHit -->|No| EnemyMiss[Miss]
        EnemyDamage --> ResetDefend[Reset<br/>player_defending]
    end

    subgraph Resolution["Combat Resolution"]
        CheckEnd{Any HP <= 0?} -->|Enemy Dead| Victory[Victory!]
        CheckEnd -->|Player Dead| Defeat[Defeat]
        CheckEnd -->|Both Alive| NextTurn[Advance Turn<br/>Increment Round if wrap]

        Victory --> Cleanup
        Defeat --> Cleanup
        Cleanup[Set is_active = False<br/>Set phase = RESOLUTION<br/>Log Final Entry] --> Summary[Narrator Summarizes<br/>ONE LLM Call]
    end

    A7 --> CheckEnd
    A6 --> EnemyTurn
    D3 --> EnemyTurn
    F3 --> ExitCombat[Exit Combat]
    F4 --> CheckEnd
    EnemyDamage --> CheckEnd
    EnemyMiss --> NextTurn
    ResetDefend --> CheckEnd
    NextTurn --> PlayerTurn
```

---

## 7. Streaming Response Flow

Server-Sent Events (SSE) sequence for real-time narrative delivery.

```mermaid
sequenceDiagram
    participant Browser
    participant API as FastAPI
    participant Router as AgentRouter
    participant N as Narrator
    participant K as Keeper
    participant J as Jester
    participant SM as SessionManager

    Browser->>API: POST /action/stream
    API->>SM: get_or_create_session()
    SM-->>API: GameState

    API->>Router: route(action, phase, recent_agents)
    Router-->>API: RoutingDecision

    API-->>Browser: SSE: routing {agents, reason}

    loop For each agent in routing.agents
        API-->>Browser: SSE: agent_start {agent}
        API->>N: respond(action, context)
        N-->>API: response

        loop Character by character
            API-->>Browser: SSE: agent_chunk {agent, char}
            Note over Browser: 15ms delay<br/>Typewriter effect
        end

        API-->>Browser: SSE: agent_response {agent, content}
        Note over API: Accumulate context<br/>"[Agent just said]: ..."
    end

    alt include_jester
        API-->>Browser: SSE: agent_start {jester}
        API->>J: respond(action, accumulated_context)
        J-->>API: response

        loop Character by character
            API-->>Browser: SSE: agent_chunk {jester, char}
        end

        API-->>Browser: SSE: agent_response {jester, content}
    end

    API->>N: Generate 3 choices
    N-->>API: Numbered list
    API->>API: Parse choices

    API-->>Browser: SSE: choices {choices[]}

    API->>SM: add_exchange()
    API->>SM: update_recent_agents()
    API->>SM: set_choices()

    API-->>Browser: SSE: complete {session_id}
```

---

## 8. Configuration-Driven Agent Architecture

How YAML configuration drives agent behavior at runtime.

```mermaid
flowchart TB
    subgraph Config["agents.yaml Configuration"]
        Defaults["defaults:<br/>  model: claude-3-5-haiku<br/>  temperature: 0.7<br/>  max_tokens: 1024"]

        NarratorCfg["narrator:<br/>  role: 'Narrator'<br/>  goal: 'Create tight, punchy scenes'<br/>  backstory: '40-80 words...'<br/>  temperature: 0.7<br/>  memory: true"]

        KeeperCfg["keeper:<br/>  role: 'Game Keeper'<br/>  goal: 'Handle mechanics'<br/>  backstory: '<10 words...'<br/>  temperature: 0.3<br/>  memory: false"]

        JesterCfg["jester:<br/>  role: 'The Jester'<br/>  goal: 'Add complications'<br/>  backstory: 'Meta-commentary...'<br/>  temperature: 0.8<br/>  memory: false"]
    end

    subgraph Loader["Config Loader"]
        LoadAgent["load_agent_config(name)"] --> Parse["Parse YAML<br/>Apply Defaults"]
        LoadTask["load_task_config(name)"] --> TaskParse["Parse Task<br/>Templates"]
    end

    subgraph AgentInit["Agent Initialization"]
        NAgent["NarratorAgent.__init__()"]
        NAgent --> LoadCfg["config = load_agent_config('narrator')"]
        LoadCfg --> CreateLLM["LLM(<br/>  model=config.llm.model,<br/>  temperature=config.llm.temperature<br/>)"]
        CreateLLM --> CreateAgent["Agent(<br/>  role=config.role,<br/>  goal=config.goal,<br/>  backstory=config.backstory,<br/>  llm=llm<br/>)"]
    end

    subgraph Runtime["Runtime Behavior"]
        Respond["agent.respond(action, context)"]
        Respond --> LoadTaskCfg["task_config = load_task_config('narrate_scene')"]
        LoadTaskCfg --> FormatDesc["description = template.format(action=action)"]
        FormatDesc --> CreateTask["Task(<br/>  description=description,<br/>  expected_output=config.expected_output,<br/>  agent=self.agent<br/>)"]
        CreateTask --> Execute["task.execute_sync()"]
        Execute --> Claude["→ Claude API"]
    end

    Config --> Loader
    Loader --> AgentInit
    AgentInit --> Runtime
```

---

## Component Summary

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Client** | Browser, SSE | User interface, real-time updates |
| **API** | FastAPI, Routes | HTTP endpoints, request handling |
| **Engine** | Router, Executor, Flow, CombatManager | Orchestration, game logic |
| **Agents** | Narrator, Keeper, Jester, Innkeeper, Interviewer | LLM-powered content generation |
| **State** | SessionManager, Backends, Models | Persistence, data validation |
| **Config** | YAML files, Settings | Behavior configuration |
| **Data** | Enemy templates, Dice utilities | Static game data |
| **External** | Anthropic Claude | LLM inference |

---

## Key Design Patterns

1. **Protocol-based Backend** - Pluggable storage with graceful fallback
2. **Configuration-driven Behavior** - Agent personalities in YAML, not code
3. **CrewAI Flow Orchestration** - Declarative multi-agent coordination
4. **Explicit Context Accumulation** - Each agent sees previous responses
5. **Controlled Randomness** - Probability and cooldown for emergent behavior
6. **Minimize LLM Calls** - Mechanics computed, narrative generated
7. **Type-safe State** - Pydantic models for all game state
8. **SSE Streaming** - Character-by-character real-time delivery
