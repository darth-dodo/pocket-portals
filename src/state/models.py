"""Game state models for Pocket Portals."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class GamePhase(str, Enum):
    """Enumeration of game phases for routing decisions.

    Attributes:
        EXPLORATION: General exploration and navigation phase
        COMBAT: Active combat encounters requiring mechanical resolution
        DIALOGUE: Conversation and social interaction phase
    """

    EXPLORATION = "exploration"
    COMBAT = "combat"
    DIALOGUE = "dialogue"


class GameState(BaseModel):
    """Minimal game state for solo D&D narrative adventure.

    Attributes:
        session_id: Unique identifier for the game session
        conversation_history: List of conversation messages with role and content
        current_choices: Available choices for the player at current state
        character_description: Text description of the player's character
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
    health_current: int = 20
    health_max: int = 20
    phase: GamePhase = GamePhase.EXPLORATION
    recent_agents: list[str] = Field(default_factory=list)
    turns_since_jester: int = 0

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
    def validate_health_relationship(self) -> "GameState":
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
