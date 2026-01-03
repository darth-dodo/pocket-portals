"""Request models for Pocket Portals API."""

from pydantic import BaseModel, Field, model_validator


class ActionRequest(BaseModel):
    """Request model for player actions."""

    action: str | None = Field(default=None)
    choice_index: int | None = Field(default=None, ge=1, le=3)
    session_id: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_action_or_choice(self) -> "ActionRequest":
        """Ensure either action or choice_index is provided."""
        if self.action is None and self.choice_index is None:
            raise ValueError("Either 'action' or 'choice_index' must be provided")
        return self


class ResolveRequest(BaseModel):
    """Request model for keeper action resolution."""

    action: str
    difficulty: int = Field(default=12, ge=1, le=30)
    session_id: str | None = Field(default=None)


class ComplicateRequest(BaseModel):
    """Request model for jester complication."""

    situation: str
    session_id: str | None = Field(default=None)


class StartCombatRequest(BaseModel):
    """Request model for starting combat."""

    session_id: str
    enemy_type: str  # "goblin", "bandit", etc.


class CombatActionRequest(BaseModel):
    """Request model for combat action."""

    session_id: str
    action: str  # "attack" for now, "defend"/"flee" in Phase 5
