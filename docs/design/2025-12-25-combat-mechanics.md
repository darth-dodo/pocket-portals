# Combat Mechanics System Design

**Date:** 2025-12-25
**Status:** Implemented
**Implementation Date:** 2025-12-26
**Related Requirements:** FR-14, FR-15, FR-16, FR-17
**Dependencies:** Character Creation (FR-01, FR-02), Keeper Agent

---

## Implementation Summary

The combat system was implemented using **Approach 5: Batched Summary** for cost-efficient design. This approach uses zero LLM calls during combat rounds, with a single Narrator LLM call at the end to summarize the entire battle.

### Key Implementation Decisions

1. **Cost Efficiency**: All combat mechanics (dice rolls, damage calculation, HP tracking) handled by `CombatManager` without LLM calls
2. **Narrative Quality**: Single `Narrator.summarize_combat()` call at combat end generates dramatic 2-4 sentence summary from combat log
3. **D&D 5e Compliance**: Initiative (d20 + DEX), attack rolls vs AC, weapon damage by class, advantage/disadvantage mechanics
4. **Defensive Actions**: Defend action gives enemy disadvantage on next attack; Flee triggers opportunity attack with advantage on failure

### Files Implemented

| File | Purpose |
|------|---------|
| `src/engine/combat_manager.py` | Core combat logic, attack resolution, turn management |
| `src/utils/dice.py` | D&D notation parser, advantage/disadvantage support |
| `src/data/enemies.py` | Enemy templates (goblin, bandit, skeleton, wolf, orc) |
| `src/agents/keeper.py` | Combat method delegation to CombatManager |
| `src/agents/narrator.py` | `summarize_combat()` method for end-of-combat narrative |
| `src/state/models.py` | CombatState, Combatant, Enemy, CombatAction models |
| `src/api/main.py` | `/combat/start` and `/combat/action` endpoints |
| `static/index.html` | Combat UI (HP bars, action buttons, dice display) |
| `static/combat-test.html` | Standalone combat testing interface |

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Design Principles](#2-design-principles)
- [3. Combat State Model](#3-combat-state-model)
- [4. Dice Rolling System](#4-dice-rolling-system)
- [5. Combat Actions](#5-combat-actions)
- [6. Damage Calculation](#6-damage-calculation)
- [7. Combat Flow](#7-combat-flow)
- [8. Keeper Integration](#8-keeper-integration)
- [9. API Design](#9-api-design)
- [10. Frontend UI](#10-frontend-ui)
- [11. Implementation Phases](#11-implementation-phases)
- [12. Future Enhancements](#12-future-enhancements)

---

## 1. Executive Summary

This document specifies the combat mechanics system for Pocket Portals, implementing D&D 5e-inspired turn-based combat with real dice rolling, initiative tracking, and damage calculation. The system follows YAGNI principles, starting with basic attack/defend mechanics and expanding incrementally.

**Core Features:**
- Initiative-based turn order
- Real dice rolling with character stat modifiers
- Attack resolution with armor class (AC) and damage dice
- HP tracking with death state handling
- Keeper agent validation of all mechanical actions

**Non-Goals (for MVP):**
- Multiple simultaneous enemies
- Spell slots and resource management
- Status effects (poison, paralysis, etc.)
- Tactical positioning on grid
- Critical hit rules beyond basic damage doubling

---

## 2. Design Principles

### 2.1 YAGNI First
Start with minimal viable combat:
- Single enemy encounters
- Basic attack action only
- Simple damage calculation
- No complex conditions or effects

### 2.2 Fast and Fun
- Target latency: <500ms for dice rolls
- Clear feedback on all mechanical results
- Visible dice rolls build trust and excitement

### 2.3 PG-13 Compliance
- Narrative descriptions avoid gore/graphic violence
- Combat described as "heroic" rather than brutal
- Death handled with dignity ("falls unconscious" vs. explicit death)

### 2.4 Agent-Driven
- Keeper agent validates all mechanical actions
- Narrator translates mechanics into narrative
- System enforces rules, agents provide story

---

## 3. Combat State Model

### 3.1 Data Models

**CombatState** (new model in `src/state/models.py`)
```python
from enum import Enum
from pydantic import BaseModel, Field

class CombatPhaseEnum(str, Enum):
    """Combat sub-phases."""
    INITIATIVE = "initiative"  # Rolling for turn order
    PLAYER_TURN = "player_turn"  # Player choosing action
    ENEMY_TURN = "enemy_turn"   # Enemy acting
    RESOLUTION = "resolution"    # Combat ending

class CombatantType(str, Enum):
    """Type of combatant."""
    PLAYER = "player"
    ENEMY = "enemy"

class Combatant(BaseModel):
    """A participant in combat."""
    id: str  # "player" or enemy identifier
    name: str
    type: CombatantType
    initiative: int = 0
    current_hp: int
    max_hp: int
    armor_class: int  # AC - target number to hit
    is_alive: bool = True

class Enemy(BaseModel):
    """Enemy template for combat encounters."""
    name: str
    description: str  # Brief narrative description
    max_hp: int
    armor_class: int
    attack_bonus: int  # Modifier to attack rolls
    damage_dice: str  # Format: "1d8+2" or "2d6"

class CombatState(BaseModel):
    """Active combat state."""
    is_active: bool = False
    phase: CombatPhaseEnum = CombatPhaseEnum.INITIATIVE
    round_number: int = 0
    combatants: list[Combatant] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)  # Ordered combatant IDs
    current_turn_index: int = 0
    enemy_template: Enemy | None = None
    combat_log: list[str] = Field(default_factory=list)  # Recent combat events
```

**GameState Updates**
```python
class GameState(BaseModel):
    # ... existing fields ...
    combat_state: CombatState = Field(default_factory=CombatState)
```

### 3.2 State Transitions

```
EXPLORATION
    │
    ▼
[Enemy Encounter Detected]
    │
    ▼
COMBAT.INITIATIVE
    │
    ├─ Roll player initiative (d20 + DEX modifier)
    ├─ Roll enemy initiative (d20 + DEX modifier)
    └─ Sort combatants by initiative (high to low)
    │
    ▼
COMBAT.PLAYER_TURN / COMBAT.ENEMY_TURN
    │
    ├─ Display HP, AC, turn order
    ├─ Process combat action
    ├─ Advance to next combatant
    └─ Increment round if turn_index wraps
    │
    ▼
[Combat Ends: HP <= 0 or Flee Success]
    │
    ▼
COMBAT.RESOLUTION
    │
    ├─ Victory: Narrative epilogue, loot
    ├─ Defeat: Death state, respawn options
    └─ Fled: Narrative consequences
    │
    ▼
EXPLORATION
```

---

## 4. Dice Rolling System

### 4.1 Core Dice Engine

**DiceRoller** (new utility in `src/utils/dice.py`)
```python
import random
import re
from dataclasses import dataclass

@dataclass
class DiceRoll:
    """Result of a dice roll."""
    notation: str  # e.g., "1d20+3"
    rolls: list[int]  # Individual die results
    modifier: int
    total: int

    def __str__(self) -> str:
        dice_str = " + ".join(str(r) for r in self.rolls)
        if self.modifier != 0:
            sign = "+" if self.modifier >= 0 else ""
            return f"{dice_str} {sign}{self.modifier} = {self.total}"
        return f"{dice_str} = {self.total}"

class DiceRoller:
    """Dice rolling engine with D&D notation support."""

    @staticmethod
    def roll(notation: str) -> DiceRoll:
        """Roll dice using standard notation.

        Supported formats:
        - "1d20" - Single die
        - "2d6" - Multiple dice
        - "1d8+3" - Die plus modifier
        - "2d6-2" - Dice minus modifier

        Args:
            notation: Dice notation string

        Returns:
            DiceRoll with individual results and total

        Raises:
            ValueError: If notation is invalid
        """
        # Parse notation: XdY+Z or XdY-Z
        pattern = r"(\d+)d(\d+)([\+\-]\d+)?"
        match = re.match(pattern, notation.lower())

        if not match:
            raise ValueError(f"Invalid dice notation: {notation}")

        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        # Roll dice
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier

        return DiceRoll(
            notation=notation,
            rolls=rolls,
            modifier=modifier,
            total=total
        )

    @staticmethod
    def roll_with_advantage() -> DiceRoll:
        """Roll d20 with advantage (roll twice, take higher)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return DiceRoll(
            notation="1d20 (advantage)",
            rolls=[roll1, roll2],
            modifier=0,
            total=max(roll1, roll2)
        )

    @staticmethod
    def roll_with_disadvantage() -> DiceRoll:
        """Roll d20 with disadvantage (roll twice, take lower)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        return DiceRoll(
            notation="1d20 (disadvantage)",
            rolls=[roll1, roll2],
            modifier=0,
            total=min(roll1, roll2)
        )
```

### 4.2 Character Stat Integration

Use existing `CharacterStats.modifier()` method:
```python
# Example: Attack roll with STR modifier
attack_roll = DiceRoller.roll("1d20")
str_modifier = character_sheet.stats.modifier("strength")
total_attack = attack_roll.total + str_modifier
```

---

## 5. Combat Actions

### 5.1 MVP Actions

**Attack** (implemented first)
- Player declares attack on enemy
- Roll 1d20 + STR modifier (for melee) or DEX modifier (for ranged)
- Compare to enemy AC
- If hit, roll weapon damage dice
- Apply damage to enemy HP

**Defend** (implemented first)
- Player takes defensive stance
- Next enemy attack has disadvantage
- Alternative: Player skips turn to gain temporary AC bonus

**Flee** (implemented first)
- Player attempts to escape combat
- Roll 1d20 + DEX modifier vs. DC 12
- Success: Combat ends, narrative consequence
- Failure: Enemy gets free attack with advantage

### 5.2 Action Data Structure

```python
class CombatAction(str, Enum):
    """Available combat actions."""
    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"
    # Future: CAST_SPELL, USE_ITEM, DASH, HIDE

class CombatActionRequest(BaseModel):
    """Player combat action request."""
    session_id: str
    action: CombatAction
    target_id: str | None = None  # For multi-enemy combat (future)
```

---

## 6. Damage Calculation

### 6.1 Attack Resolution Algorithm

```python
def resolve_attack(
    attacker: Combatant,
    defender: Combatant,
    attack_bonus: int,
    damage_dice: str
) -> dict:
    """Resolve a single attack.

    Returns:
        {
            "hit": bool,
            "attack_roll": DiceRoll,
            "damage_roll": DiceRoll | None,
            "damage_dealt": int,
            "defender_hp_remaining": int
        }
    """
    # Roll attack
    attack_roll = DiceRoller.roll("1d20")
    total_attack = attack_roll.total + attack_bonus

    # Check if hit
    hit = total_attack >= defender.armor_class

    if not hit:
        return {
            "hit": False,
            "attack_roll": attack_roll,
            "damage_roll": None,
            "damage_dealt": 0,
            "defender_hp_remaining": defender.current_hp
        }

    # Roll damage
    damage_roll = DiceRoller.roll(damage_dice)
    damage_dealt = max(0, damage_roll.total)  # Never heal on attack

    # Apply damage
    defender.current_hp -= damage_dealt
    if defender.current_hp < 0:
        defender.current_hp = 0
    if defender.current_hp == 0:
        defender.is_alive = False

    return {
        "hit": True,
        "attack_roll": attack_roll,
        "damage_roll": damage_roll,
        "damage_dealt": damage_dealt,
        "defender_hp_remaining": defender.current_hp
    }
```

### 6.2 Weapon Damage by Class

Default damage dice for player attacks (based on character class):

| Class | Weapon Type | Damage Dice | Stat Modifier |
|-------|-------------|-------------|---------------|
| Fighter | Longsword | 1d8 | STR |
| Wizard | Quarterstaff | 1d6 | STR |
| Rogue | Dagger | 1d4 | DEX |
| Cleric | Mace | 1d6 | STR |
| Ranger | Longbow | 1d8 | DEX |
| Bard | Rapier | 1d8 | DEX |

### 6.3 Critical Hits (Future)

For Phase 2 implementation:
- Natural 20 on attack roll = automatic hit
- Roll damage dice twice, add modifiers once
- Narrative acknowledgment from Narrator agent

---

## 7. Combat Flow

### 7.1 Initiative Phase

```
[Combat Triggered]
    │
    ▼
System: Create CombatState
    ├─ Generate Enemy from template
    ├─ Create Combatant for player
    ├─ Create Combatant for enemy
    │
    ▼
Keeper: Roll initiative for all combatants
    ├─ Player: 1d20 + DEX modifier
    ├─ Enemy: 1d20 + DEX modifier
    ├─ Sort by total (ties broken randomly)
    └─ Set turn_order
    │
    ▼
Narrator: Describe combat scene
    └─ "The [enemy] lunges forward! [Initiative results]"
    │
    ▼
Transition to first combatant's turn
```

### 7.2 Player Turn

```
[COMBAT.PLAYER_TURN]
    │
    ▼
Frontend: Display combat UI
    ├─ HP bars for player and enemy
    ├─ Initiative order
    ├─ Available actions: Attack, Defend, Flee
    │
    ▼
Player: Select action
    │
    ├─ ATTACK ─────────────┐
    ├─ DEFEND ─────────────┤
    └─ FLEE ───────────────┤
                           │
                           ▼
POST /combat/action
    │
    ▼
Keeper: Validate and resolve mechanics
    ├─ Roll dice
    ├─ Calculate results
    ├─ Update HP
    └─ Check for combat end
    │
    ▼
Narrator: Describe outcome
    └─ Translate mechanics into narrative
    │
    ▼
System: Advance turn
    ├─ If combat ongoing → ENEMY_TURN
    └─ If combat ended → RESOLUTION
```

### 7.3 Enemy Turn

```
[COMBAT.ENEMY_TURN]
    │
    ▼
Keeper: Execute enemy AI
    ├─ Select action (attack for MVP)
    ├─ Roll attack: 1d20 + attack_bonus
    ├─ Compare to player AC
    ├─ If hit, roll damage
    └─ Apply damage to player HP
    │
    ▼
Narrator: Describe enemy action
    └─ "The goblin swings its rusty blade!"
    │
    ▼
System: Check player HP
    ├─ If HP > 0 → Advance to next turn
    └─ If HP <= 0 → RESOLUTION (defeat)
```

### 7.4 Combat Resolution

```
[COMBAT.RESOLUTION]
    │
    ├─ Victory (enemy HP <= 0)
    │   ├─ Keeper: Grant XP (future)
    │   ├─ Narrator: Victory narrative
    │   └─ Loot generation (future)
    │
    ├─ Defeat (player HP <= 0)
    │   ├─ Keeper: Record death state
    │   ├─ Narrator: Defeat narrative (PG-13)
    │   └─ Respawn options (future)
    │
    └─ Fled (successful flee roll)
        ├─ Narrator: Escape narrative
        └─ Consequence tracking (future)
    │
    ▼
System: Cleanup combat state
    ├─ Set combat_state.is_active = False
    ├─ Reset phase to EXPLORATION
    └─ Preserve combat_log for narrative continuity
```

---

## 8. Keeper Integration

### 8.1 Extended Keeper Responsibilities

**Current:** Mechanical resolution with terse language
**New Combat Duties:**
- Roll and validate all dice (initiative, attacks, damage)
- Enforce combat rules (turn order, hit/miss, HP bounds)
- Execute enemy AI decisions
- Detect combat end conditions

### 8.2 New Keeper Methods

```python
# src/agents/keeper.py

class KeeperAgent:
    # ... existing __init__, respond, resolve_action ...

    def roll_initiative(
        self,
        combatants: list[dict],
        character_sheet: CharacterSheet
    ) -> dict:
        """Roll initiative for all combatants.

        Args:
            combatants: List of combatant dicts with dex_modifier
            character_sheet: Player character sheet

        Returns:
            {
                "turn_order": ["player", "enemy_1", ...],
                "results": [
                    {"id": "player", "roll": 15, "modifier": 2, "total": 17},
                    ...
                ]
            }
        """
        # Implementation uses DiceRoller
        pass

    def resolve_combat_action(
        self,
        action: CombatAction,
        attacker: Combatant,
        defender: Combatant,
        character_sheet: CharacterSheet | None = None
    ) -> dict:
        """Resolve a combat action mechanically.

        Args:
            action: Combat action type
            attacker: Combatant performing action
            defender: Combatant being targeted
            character_sheet: Player sheet if attacker is player

        Returns:
            Mechanical results dict (varies by action)
        """
        # Implementation delegates to action-specific handlers
        pass

    def check_combat_end(self, combat_state: CombatState) -> tuple[bool, str]:
        """Check if combat should end.

        Returns:
            (should_end: bool, reason: str)
        """
        # Check for any combatant death
        for combatant in combat_state.combatants:
            if not combatant.is_alive:
                if combatant.type == CombatantType.PLAYER:
                    return (True, "player_defeat")
                else:
                    return (True, "enemy_defeat")
        return (False, "")
```

### 8.3 Keeper Configuration Updates

**Config YAML changes** (`src/config/agents.yaml`):
```yaml
keeper:
  role: "Game Mechanics Referee"
  goal: |
    Resolve game mechanics with precision and speed.
    Roll dice, enforce rules, track HP, validate actions.
    Respond with numbers first, minimal text.
  backstory: |
    You are the Keeper - the silent arbiter of fate and fortune.
    When dice must roll, you roll them. When rules must be checked,
    you check them. You speak in stats, not stories. That's the
    Narrator's job. You just make sure the numbers add up.

    Combat Protocol:
    - Roll initiative: 1d20 + DEX modifier
    - Attack rolls: 1d20 + attack bonus vs. AC
    - Damage rolls: Use appropriate dice for weapon/class
    - HP tracking: Never allow negative HP, mark death at 0
    - End detection: Combat ends when any combatant reaches 0 HP
  verbose: false
  allow_delegation: false
```

**New task configs** (`src/config/tasks.yaml`):
```yaml
roll_initiative:
  description: |
    Roll initiative for combat.
    Combatants: {combatants}
    Format: "[Name]: 1d20+[modifier] = [total]" for each, then turn order.
  expected_output: "Initiative order with rolls shown"

resolve_attack:
  description: |
    Resolve attack action.
    Attacker: {attacker_name} (AC {attacker_ac}, HP {attacker_hp})
    Defender: {defender_name} (AC {defender_ac}, HP {defender_hp})
    Attack bonus: {attack_bonus}
    Damage dice: {damage_dice}

    Roll 1d20+{attack_bonus} vs AC {defender_ac}
    If hit, roll {damage_dice} for damage.
  expected_output: "Attack: [roll]. Hit/Miss. Damage: [roll]. HP: [remaining]"
```

---

## 9. API Design

### 9.1 Implemented Endpoints

**POST /combat/start**
```python
class StartCombatRequest(BaseModel):
    session_id: str
    enemy_type: str  # "goblin", "bandit", "skeleton", "wolf", "orc"

class StartCombatResponse(BaseModel):
    narrative: str  # Combined scene description + initiative results
    combat_state: CombatState
    initiative_results: list[dict]  # {"id", "roll", "modifier", "total"}
```

**POST /combat/action**
```python
class CombatActionRequest(BaseModel):
    session_id: str
    action: str  # "attack", "defend", "flee"

class CombatActionResponse(BaseModel):
    success: bool              # Action executed successfully
    result: dict               # Attack/defend/flee result details
    message: str               # Formatted combat log text
    narrative: str | None      # Narrator summary (only at combat end)
    combat_state: CombatState  # Updated state
    combat_ended: bool         # True if combat is over
    victory: bool | None       # True=win, False=lose, None=ongoing/fled
    fled: bool = False         # True if player successfully escaped
```

**Implementation Notes:**
- `/combat/start` requires valid session with completed character sheet
- `/combat/action` validates player turn before executing
- Narrator narrative only generated at combat end (cost efficiency)
- Enemy turn auto-executes after player action if combat continues

### 9.2 Enemy Templates

**Implemented in `src/data/enemies.py`:**

| Enemy Type | Name | HP | AC | Attack | Damage |
|------------|------|----|----|--------|--------|
| `goblin` | Goblin Raider | 7 | 13 | +4 | 1d6+2 |
| `bandit` | Bandit Outlaw | 11 | 12 | +3 | 1d6+1 |
| `skeleton` | Skeleton Warrior | 13 | 13 | +4 | 1d6+2 |
| `wolf` | Dire Wolf | 11 | 13 | +5 | 2d4+3 |
| `orc` | Orc Warrior | 15 | 13 | +5 | 1d12+3 |

```python
ENEMY_TEMPLATES = {
    "goblin": Enemy(
        name="Goblin Raider",
        description="A small, green-skinned creature with a wicked grin and sharp teeth",
        max_hp=7,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6+2",
    ),
    "bandit": Enemy(
        name="Bandit Outlaw",
        description="A rough-looking human with a scarred face and tattered leather armor",
        max_hp=11,
        armor_class=12,
        attack_bonus=3,
        damage_dice="1d6+1",
    ),
    "skeleton": Enemy(
        name="Skeleton Warrior",
        description="An animated skeleton wielding a rusty sword and wearing tattered armor",
        max_hp=13,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6+2",
    ),
    "wolf": Enemy(
        name="Dire Wolf",
        description="A large, fierce wolf with matted gray fur and glowing yellow eyes",
        max_hp=11,
        armor_class=13,
        attack_bonus=5,
        damage_dice="2d4+3",
    ),
    "orc": Enemy(
        name="Orc Warrior",
        description="A muscular, gray-skinned humanoid with tusks and a battle-scarred face",
        max_hp=15,
        armor_class=13,
        attack_bonus=5,
        damage_dice="1d12+3",
    ),
}
```

### 9.3 Integration with Existing Flow

**AgentRouter updates** (`src/engine/router.py`):
```python
def route(
    self,
    action: str,
    phase: GamePhase,
    recent_agents: list[str],
    combat_state: CombatState | None = None  # NEW
) -> RoutingDecision:
    # ... existing logic ...

    # Always include keeper in combat phase
    if phase == GamePhase.COMBAT:
        if "keeper" not in agents:
            agents.append("keeper")
        reason_parts.append("combat active")

        # Check if combat action keyword
        if any(kw in action_lower for kw in ["attack", "defend", "flee"]):
            reason_parts.append("combat action")
```

---

## 10. Frontend UI

### 10.1 Combat UI Components

**Combat HUD** (displayed when `combat_state.is_active == true`):

```html
<!-- src/static/index.html additions -->
<div id="combat-hud" class="nes-container is-dark" style="display: none;">
    <!-- Initiative Tracker -->
    <div class="initiative-tracker">
        <h3>Turn Order</h3>
        <ul id="turn-order-list">
            <!-- Populated dynamically -->
            <!-- <li class="active">🗡️ Player (Initiative: 17)</li> -->
            <!-- <li>👹 Goblin Raider (Initiative: 12)</li> -->
        </ul>
    </div>

    <!-- HP Displays -->
    <div class="hp-displays">
        <!-- Player HP -->
        <div class="hp-bar">
            <label>Your HP</label>
            <progress
                class="nes-progress is-success"
                id="player-hp-bar"
                value="20"
                max="20"
            ></progress>
            <span id="player-hp-text">20/20</span>
        </div>

        <!-- Enemy HP -->
        <div class="hp-bar">
            <label id="enemy-name">Enemy HP</label>
            <progress
                class="nes-progress is-error"
                id="enemy-hp-bar"
                value="7"
                max="7"
            ></progress>
            <span id="enemy-hp-text">7/7</span>
        </div>
    </div>

    <!-- Combat Actions -->
    <div class="combat-actions">
        <button class="nes-btn is-error" onclick="combatAction('attack')">
            ⚔️ Attack
        </button>
        <button class="nes-btn is-primary" onclick="combatAction('defend')">
            🛡️ Defend
        </button>
        <button class="nes-btn is-warning" onclick="combatAction('flee')">
            🏃 Flee
        </button>
    </div>

    <!-- Dice Roll Display (appears during rolls) -->
    <div id="dice-result" class="nes-container is-rounded" style="display: none;">
        <p id="dice-notation">Rolling 1d20+3...</p>
        <div class="dice-animation">🎲</div>
        <p id="dice-total" class="result"></p>
    </div>
</div>
```

### 10.2 Combat CSS

```css
/* static/style.css additions */

.combat-hud {
    position: fixed;
    top: 20px;
    right: 20px;
    width: 300px;
    z-index: 100;
    background: rgba(0, 0, 0, 0.9);
}

.initiative-tracker ul {
    list-style: none;
    padding: 0;
}

.initiative-tracker li {
    padding: 5px;
    margin: 5px 0;
    background: #333;
}

.initiative-tracker li.active {
    background: #4CAF50;
    font-weight: bold;
}

.hp-bar {
    margin: 10px 0;
}

.hp-bar label {
    display: block;
    margin-bottom: 5px;
}

.combat-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.combat-actions button {
    flex: 1;
}

.dice-animation {
    font-size: 48px;
    text-align: center;
    animation: spin 0.5s ease-in-out;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

#dice-total.result {
    font-size: 24px;
    font-weight: bold;
    text-align: center;
    color: #FFD700;
}
```

### 10.3 Combat JavaScript

```javascript
// static/script.js additions

let combatState = null;

function updateCombatHUD(state) {
    combatState = state;
    const hud = document.getElementById('combat-hud');

    if (!state || !state.is_active) {
        hud.style.display = 'none';
        return;
    }

    hud.style.display = 'block';

    // Update turn order
    const turnList = document.getElementById('turn-order-list');
    turnList.innerHTML = '';
    state.turn_order.forEach((combatantId, index) => {
        const combatant = state.combatants.find(c => c.id === combatantId);
        const li = document.createElement('li');
        li.textContent = `${combatant.name} (Init: ${combatant.initiative})`;
        if (index === state.current_turn_index) {
            li.classList.add('active');
        }
        turnList.appendChild(li);
    });

    // Update HP bars
    const player = state.combatants.find(c => c.type === 'player');
    const enemy = state.combatants.find(c => c.type === 'enemy');

    document.getElementById('player-hp-bar').value = player.current_hp;
    document.getElementById('player-hp-bar').max = player.max_hp;
    document.getElementById('player-hp-text').textContent =
        `${player.current_hp}/${player.max_hp}`;

    if (enemy) {
        document.getElementById('enemy-name').textContent = enemy.name;
        document.getElementById('enemy-hp-bar').value = enemy.current_hp;
        document.getElementById('enemy-hp-bar').max = enemy.max_hp;
        document.getElementById('enemy-hp-text').textContent =
            `${enemy.current_hp}/${enemy.max_hp}`;
    }
}

async function combatAction(action) {
    const response = await fetch('/combat/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: currentSessionId,
            action: action
        })
    });

    const result = await response.json();

    // Show dice roll animation if present
    if (result.mechanical_result.attack_roll) {
        showDiceRoll(result.mechanical_result.attack_roll);
    }

    // Display narrative
    appendNarrative(result.narrative);

    // Update combat HUD
    updateCombatHUD(result.combat_state);

    // Check for combat end
    if (!result.combat_ongoing) {
        if (result.victory === true) {
            appendNarrative("🎉 Victory! The enemy is defeated.");
        } else if (result.victory === false) {
            appendNarrative("💀 You have been defeated...");
        } else {
            appendNarrative("🏃 You successfully fled from combat.");
        }

        setTimeout(() => {
            document.getElementById('combat-hud').style.display = 'none';
        }, 3000);
    }
}

function showDiceRoll(rollData) {
    const diceResult = document.getElementById('dice-result');
    document.getElementById('dice-notation').textContent =
        `Rolling ${rollData.notation}...`;

    diceResult.style.display = 'block';

    setTimeout(() => {
        document.getElementById('dice-total').textContent =
            `Result: ${rollData.total}`;

        setTimeout(() => {
            diceResult.style.display = 'none';
        }, 2000);
    }, 500);
}
```

---

## 11. Implementation Phases

> **All phases completed on 2025-12-26**

### Phase 1: Foundation - COMPLETE
**Goal:** Basic combat state and dice rolling

**Tasks:**
1. Implement `CombatState`, `Combatant`, `Enemy` models - `src/state/models.py`
2. Create `DiceRoller` utility with tests - `src/utils/dice.py`
3. Add `combat_state` to `GameState` - `src/state/models.py`
4. Create enemy templates database - `src/data/enemies.py`
5. Unit tests for dice rolling

**Implementation Notes:**
- `DiceRoller` supports standard notation (XdY+Z), advantage, and disadvantage
- Five enemy templates: goblin, bandit, skeleton, wolf, orc
- `DiceRoll` dataclass provides formatted output for combat log

### Phase 2: Initiative System - COMPLETE
**Goal:** Turn order establishment

**Tasks:**
1. Implement `CombatManager.roll_initiative()` - `src/engine/combat_manager.py`
2. Create `/combat/start` endpoint - `src/api/main.py`
3. Keeper formats initiative results - `src/agents/keeper.py`
4. Frontend: Display initiative order UI - `static/index.html`

**Implementation Notes:**
- Initiative uses 1d20 + DEX modifier (D&D 5e standard)
- `KeeperAgent.format_initiative_result()` provides human-readable output
- Turn order sorted high to low, ties handled by roll order

### Phase 3: Attack Resolution - COMPLETE
**Goal:** Basic attack mechanics

**Tasks:**
1. Implement `CombatManager.resolve_attack()` - `src/engine/combat_manager.py`
2. Add weapon damage by class lookup - `WEAPON_DAMAGE` dict in combat_manager.py
3. Create `/combat/action` endpoint - `src/api/main.py`
4. Frontend: Combat action buttons - `static/index.html`

**Implementation Notes:**
- Attack resolution: d20 + attack_bonus vs AC
- Damage calculation: weapon_dice + stat_modifier
- Combat log entries generated for each action
- Class-based weapons: Fighter (1d8+STR), Rogue (1d4+DEX), Wizard (1d6+STR), etc.

### Phase 4: Combat Flow - COMPLETE
**Goal:** Complete turn-based combat loop

**Tasks:**
1. Implement `CombatManager.advance_turn()` - handles turn/round progression
2. Implement `CombatManager.execute_enemy_turn()` - enemy AI (always attacks)
3. Implement `CombatManager.check_combat_end()` - victory/defeat detection
4. Implement `Narrator.summarize_combat()` - end-of-combat narrative
5. Frontend: HP bars and live updates - `static/index.html`

**Implementation Notes:**
- Turn advancement wraps to next round when all combatants have acted
- Phase transitions: PLAYER_TURN <-> ENEMY_TURN based on turn_order
- Single Narrator LLM call at combat end (cost-efficient design)
- Combat log preserved for narrative generation

### Phase 5: Defend and Flee - COMPLETE
**Goal:** Additional player actions

**Tasks:**
1. Implement `CombatManager.execute_defend()` - sets `player_defending` flag
2. Implement `CombatManager.execute_flee()` - DEX check vs DC 12
3. Implement opportunity attack on failed flee - enemy attacks with advantage
4. Update frontend with action buttons - Attack, Defend, Flee

**Implementation Notes:**
- Defend: Sets `combat_state.player_defending = True`, enemy next attack has disadvantage
- Flee success: Combat ends immediately, player escapes
- Flee failure: Enemy gets free attack with advantage (opportunity attack)
- `CombatActionResponse.fled` flag indicates successful escape

---

## 12. Future Enhancements

### Already Implemented Beyond Original MVP
- Advantage/disadvantage mechanics
- Opportunity attacks (on failed flee)
- Combat log for narrative generation
- Five enemy types (originally planned 3)

### Phase 6: Advanced Combat (Post-MVP)
- Multiple simultaneous enemies
- Critical hit rules (nat 20 doubles damage)
- Status effects (poisoned, stunned, etc.)
- Spell casting for wizard/cleric classes
- Item usage during combat
- Tactical positioning on ASCII grid

### Phase 7: Combat Variety (Post-MVP)
- Boss encounters with multi-stage HP
- Environmental hazards (lava, traps)
- Ally NPCs joining combat
- Stealth-based combat initiation
- Dialogue options during combat

### Phase 8: Progression (Post-MVP)
- XP gain from victories
- Level-up mechanics
- Loot drops and inventory
- Equipment bonuses to AC/damage
- Character death/resurrection system

---

## Appendix A: D&D 5e Reference

**Core Mechanics Used:**
- Ability modifiers: (score - 10) / 2
- Attack rolls: d20 + attack bonus vs. AC
- Damage rolls: weapon dice + ability modifier
- Initiative: d20 + DEX modifier
- Advantage/Disadvantage: Roll 2d20, take higher/lower

**Simplified for MVP:**
- No spell slots or spell selection
- No reactions or opportunity attacks
- No conditions beyond HP = 0
- Single weapon per class (no equipment swapping)
- Flat AC (no armor bonuses)

---

## Appendix B: File Locations

```
pocket-portals/
├── src/
│   ├── state/
│   │   └── models.py               # CombatState, Combatant, Enemy, CombatAction, CombatPhaseEnum
│   ├── engine/
│   │   └── combat_manager.py       # CombatManager - core combat logic
│   ├── utils/
│   │   └── dice.py                 # DiceRoller, DiceRoll dataclass
│   ├── data/
│   │   └── enemies.py              # ENEMY_TEMPLATES (goblin, bandit, skeleton, wolf, orc)
│   ├── agents/
│   │   ├── keeper.py               # Combat method delegation to CombatManager
│   │   └── narrator.py             # summarize_combat() for end-of-combat narrative
│   ├── api/
│   │   └── main.py                 # /combat/start, /combat/action endpoints
│   └── config/
│       └── tasks.yaml              # summarize_combat task config
├── static/
│   ├── index.html                  # Combat HUD (HP bars, actions, initiative)
│   └── combat-test.html            # Standalone combat testing interface
└── tests/
    └── (combat tests)              # Integration tests for combat flow
```

### Key Classes and Methods

**CombatManager** (`src/engine/combat_manager.py`):
- `start_combat(character_sheet, enemy_type)` - Initialize combat encounter
- `roll_initiative(combatants, dex_modifiers)` - Roll initiative for all
- `resolve_attack(attacker, defender, ...)` - Resolve attack with advantage/disadvantage
- `execute_player_attack(combat_state, character_sheet)` - Player attack action
- `execute_enemy_turn(combat_state)` - Enemy AI attack
- `execute_defend(combat_state, character_sheet)` - Defend action
- `execute_flee(combat_state, character_sheet)` - Flee with opportunity attack
- `advance_turn(combat_state)` - Turn/round progression
- `check_combat_end(combat_state)` - Victory/defeat detection
- `end_combat(combat_state, result)` - Cleanup and finalize

**DiceRoller** (`src/utils/dice.py`):
- `roll(notation)` - Parse and roll D&D notation (e.g., "2d6+3")
- `roll_with_advantage()` - Roll 2d20, take higher
- `roll_with_disadvantage()` - Roll 2d20, take lower

**NarratorAgent** (`src/agents/narrator.py`):
- `summarize_combat(combat_log, victory, enemy_name, player_name)` - Single LLM call for combat narrative

---

## Appendix C: Example Combat Sequence

```
# Player enters dark forest
Narrator: "Shadows shift between the trees. A goblin springs from the bushes!"

# System initiates combat
POST /combat/start { session_id: "abc", enemy_type: "goblin" }

# Initiative rolls
Keeper: "Initiative! Player: 1d20+2 = 17. Goblin: 1d20+1 = 12. Player goes first."

# Player turn
Frontend: [Attack] [Defend] [Flee]
Player clicks: Attack

# Attack resolution
POST /combat/action { session_id: "abc", action: "attack" }
Keeper: "Attack: 1d20+3 = 18 vs AC 13. Hit! Damage: 1d8+3 = 7. Goblin HP: 0/7"

Narrator: "Your blade strikes true! The goblin crumples to the ground, defeated."

# Combat ends
System: combat_state.is_active = false
Frontend: Combat HUD fades out
Narrator: "You catch your breath and search the body, finding 5 gold pieces."
```

---

**End of Document**
