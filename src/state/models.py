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


class QuestStatus(str, Enum):
    """Quest completion status.

    Attributes:
        ACTIVE: Quest is currently active
        COMPLETED: Quest has been completed successfully
        FAILED: Quest has failed or been abandoned
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AdventurePhase(str, Enum):
    """Narrative phases for adventure pacing.

    Each phase has specific narrative characteristics that guide agent output:
        SETUP: Character introduction, world establishment (turns 1-5)
        RISING_ACTION: Conflict introduction, stakes building (turns 6-20)
        MID_POINT: Major revelation, point of no return (turns 21-30)
        CLIMAX: Maximum tension, confrontation (turns 31-42)
        DENOUEMENT: Resolution, reflection, closure (turns 43-50)
    """

    SETUP = "setup"
    RISING_ACTION = "rising"
    MID_POINT = "midpoint"
    CLIMAX = "climax"
    DENOUEMENT = "denouement"


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


class AdventureMoment(BaseModel):
    """Significant moment during adventure for epilogue generation.

    Tracks notable events that occurred during the adventure to enable
    personalized epilogue generation that references the player's journey.

    Attributes:
        turn: Turn number when moment occurred
        type: Category of moment (combat_victory, discovery, choice, npc_interaction)
        summary: Brief description of what happened
        significance: Weight for epilogue inclusion (0.0-1.0)
    """

    turn: int
    type: str
    summary: str
    significance: float = Field(default=0.5, ge=0.0, le=1.0)


class QuestObjective(BaseModel):
    """Individual quest objective with completion tracking.

    Attributes:
        id: Unique identifier for the objective
        description: Text description of what needs to be done
        is_completed: Whether this objective has been completed
        target_count: Optional target count for quantity-based objectives
        current_count: Current progress toward target_count
    """

    id: str
    description: str
    is_completed: bool = False
    target_count: int | None = None
    current_count: int = 0

    def check_completion(self) -> bool:
        """Check if objective is complete based on target count.

        Returns:
            True if objective is complete, False otherwise
        """
        if self.target_count is not None:
            self.is_completed = self.current_count >= self.target_count
        return self.is_completed


class Quest(BaseModel):
    """Quest with objectives and rewards.

    Attributes:
        id: Unique identifier for the quest
        title: Short quest title
        description: Detailed quest description
        objectives: List of quest objectives to complete
        rewards: Description of quest rewards
        status: Current quest status
        given_by: Name of NPC who gave the quest
        location_hint: Hint about where to find quest objectives
    """

    id: str
    title: str
    description: str
    objectives: list[QuestObjective] = Field(default_factory=list)
    rewards: str | None = None
    status: QuestStatus = QuestStatus.ACTIVE
    given_by: str = "Innkeeper Theron"
    location_hint: str | None = None

    @property
    def is_complete(self) -> bool:
        """Check if all objectives are completed.

        Returns:
            True if all objectives are complete, False otherwise
        """
        return all(obj.is_completed for obj in self.objectives)

    def complete_objective(self, objective_id: str) -> bool:
        """Mark an objective as completed.

        Args:
            objective_id: ID of the objective to complete

        Returns:
            True if objective was found and completed, False otherwise
        """
        for obj in self.objectives:
            if obj.id == objective_id:
                obj.is_completed = True
                return True
        return False

    def increment_objective(self, objective_id: str, amount: int = 1) -> bool:
        """Increment progress on a quantity-based objective.

        Args:
            objective_id: ID of the objective to increment
            amount: Amount to increment by (default 1)

        Returns:
            True if objective was found and incremented, False otherwise
        """
        for obj in self.objectives:
            if obj.id == objective_id and obj.target_count is not None:
                obj.current_count += amount
                obj.check_completion()
                return True
        return False


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
        adventure_turn: Current turn number in the adventure (0-50)
        adventure_phase: Current narrative phase for pacing
        max_turns: Maximum turns for this adventure (default 50)
        adventure_completed: Whether the adventure has concluded
        climax_reached: Whether the main conflict has been resolved
        adventure_moments: Significant moments for epilogue generation
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
    active_quest: Quest | None = None
    completed_quests: list[Quest] = Field(default_factory=list)

    # Adventure pacing fields
    adventure_turn: int = Field(default=0, ge=0, le=50)
    adventure_phase: AdventurePhase = AdventurePhase.SETUP
    max_turns: int = Field(default=50, ge=25, le=100)
    adventure_completed: bool = False
    climax_reached: bool = False
    adventure_moments: list[AdventureMoment] = Field(default_factory=list)

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

    def to_json(self) -> str:
        """Serialize the GameState to a JSON string.

        This method provides a convenient way to serialize the entire game state,
        including nested models like CharacterSheet and CombatState, to a JSON
        string suitable for storage in Redis or other backends.

        Returns:
            JSON string representation of the game state

        Examples:
            >>> state = GameState(session_id="test-123")
            >>> json_str = state.to_json()
            >>> isinstance(json_str, str)
            True
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> GameState:
        """Deserialize a GameState from a JSON string.

        This class method reconstructs a GameState instance from its JSON
        representation, properly handling nested models like CharacterSheet
        and CombatState.

        Args:
            json_str: JSON string representation of a GameState

        Returns:
            Reconstructed GameState instance

        Raises:
            pydantic.ValidationError: If the JSON is invalid or doesn't match
                the expected schema

        Examples:
            >>> state = GameState(session_id="test-123")
            >>> json_str = state.to_json()
            >>> restored = GameState.from_json(json_str)
            >>> restored.session_id == state.session_id
            True
        """
        return cls.model_validate_json(json_str)


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
