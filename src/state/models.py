"""Game state models for Pocket Portals."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    pass


class GamePhase(str, Enum):
    """Enumeration of game phases for routing decisions.

    Attributes:
        CHARACTER_CREATION: Initial character creation/interview phase
        EXPLORATION: General exploration and navigation phase
        COMBAT: Active combat encounters requiring mechanical resolution
        DIALOGUE: Conversation and social interaction phase
    """

    CHARACTER_CREATION = "character_creation"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    DIALOGUE = "dialogue"


class CombatPhaseEnum(str, Enum):
    """Enumeration of combat phases.

    Attributes:
        INITIATIVE: Rolling for initiative to determine turn order
        PLAYER_TURN: Player's turn to take action
        ENEMY_TURN: Enemy's turn to take action
        RESOLUTION: Combat resolution and cleanup
    """

    INITIATIVE = "initiative"
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    RESOLUTION = "resolution"


class CombatantType(str, Enum):
    """Type of combatant.

    Attributes:
        PLAYER: Player character
        ENEMY: Enemy or NPC combatant
    """

    PLAYER = "player"
    ENEMY = "enemy"


class CombatAction(str, Enum):
    """Available combat actions.

    Attributes:
        ATTACK: Attack the enemy
        DEFEND: Take defensive stance
        FLEE: Attempt to flee from combat
    """

    ATTACK = "attack"
    DEFEND = "defend"
    FLEE = "flee"


class GameState(BaseModel):
    """Minimal game state for solo D&D narrative adventure.

    Attributes:
        session_id: Unique identifier for the game session
        conversation_history: List of conversation messages with role and content
        current_choices: Available choices for the player at current state
        character_description: Text description of the player's character (legacy)
        character_sheet: Structured character sheet (new)
        health_current: Current health points
        health_max: Maximum health points
        phase: Current game phase for routing decisions
        recent_agents: List of recently used agents for Jester cooldown
        turns_since_jester: Number of turns since last Jester appearance
    """

    session_id: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    current_choices: list[str] = Field(default_factory=list)
    character_description: str = ""
    character_sheet: Any = (
        None  # CharacterSheet | None - using Any to avoid circular import
    )
    health_current: int = 20
    health_max: int = 20
    phase: GamePhase = GamePhase.CHARACTER_CREATION
    creation_turn: int = Field(default=0, ge=0, le=5)
    recent_agents: list[str] = Field(default_factory=list)
    turns_since_jester: int = 0
    combat_state: CombatState | None = None

    @field_validator("character_sheet", mode="before")
    @classmethod
    def validate_character_sheet(cls, v: Any) -> Any:
        """Reconstruct CharacterSheet from dict if needed.

        Args:
            v: The character_sheet value (dict, CharacterSheet, or None)

        Returns:
            CharacterSheet instance or None
        """
        if v is None:
            return None
        if isinstance(v, dict):
            # Import here to avoid circular import
            from src.state.character import CharacterSheet

            return CharacterSheet(**v)
        return v

    @property
    def has_character(self) -> bool:
        """Check if character sheet is complete.

        Returns:
            True if character_sheet is set, False otherwise.
        """
        return self.character_sheet is not None

    @field_validator("health_current")
    @classmethod
    def health_current_valid(cls, v: int) -> int:
        """Validate that current health is not negative.

        Args:
            v: The health_current value to validate

        Returns:
            The validated health_current value

        Raises:
            ValueError: If health_current is negative
        """
        if v < 0:
            raise ValueError("health_current cannot be negative")
        return v

    @model_validator(mode="after")
    def validate_health_relationship(self) -> GameState:
        """Validate that current health does not exceed max health.

        Returns:
            The validated model instance

        Raises:
            ValueError: If health_current exceeds health_max
        """
        if self.health_current > self.health_max:
            raise ValueError(
                f"health_current ({self.health_current}) cannot exceed "
                f"health_max ({self.health_max})"
            )
        return self


class Combatant(BaseModel):
    """Individual combatant in combat.

    Attributes:
        id: Unique identifier for the combatant
        name: Display name of the combatant
        type: Type of combatant (PLAYER or ENEMY)
        initiative: Initiative roll value (determines turn order)
        current_hp: Current hit points
        max_hp: Maximum hit points
        armor_class: Armor class (AC) for defense
        is_alive: Whether the combatant is still alive
    """

    id: str
    name: str
    type: CombatantType
    initiative: int = 0
    current_hp: int
    max_hp: int
    armor_class: int
    is_alive: bool = True


class Enemy(BaseModel):
    """Enemy template with stats and information.

    Attributes:
        name: Display name of the enemy
        description: Descriptive text about the enemy
        max_hp: Maximum hit points
        armor_class: Armor class (AC) for defense
        attack_bonus: Bonus to attack rolls
        damage_dice: Dice notation for damage (e.g., "1d6+2")
    """

    name: str
    description: str
    max_hp: int
    armor_class: int
    attack_bonus: int
    damage_dice: str


class CombatState(BaseModel):
    """State for active combat encounter.

    Attributes:
        is_active: Whether combat is currently active
        phase: Current phase of combat
        round_number: Current round number
        combatants: List of all combatants in the encounter
        turn_order: Ordered list of combatant IDs by initiative
        current_turn_index: Index into turn_order for current turn
        enemy_template: Template used to create the enemy
        combat_log: Log of combat events and messages
        player_defending: True if player used Defend last turn
    """

    is_active: bool = False
    phase: CombatPhaseEnum = CombatPhaseEnum.INITIATIVE
    round_number: int = 0
    combatants: list[Combatant] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)
    current_turn_index: int = 0
    enemy_template: Enemy | None = None
    combat_log: list[str] = Field(default_factory=list)
    player_defending: bool = False
