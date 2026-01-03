"""Response models for Pocket Portals API."""

from typing import Any

from pydantic import BaseModel, Field

from src.state.models import CombatState


class CharacterSheetData(BaseModel):
    """Character sheet data for API responses."""

    name: str
    race: str
    character_class: str
    level: int = 1
    current_hp: int
    max_hp: int
    stats: dict[str, int]
    equipment: list[str]
    backstory: str


class NarrativeResponse(BaseModel):
    """Response model containing narrative text."""

    narrative: str
    session_id: str
    choices: list[str] = Field(default_factory=lambda: ["Look around", "Wait", "Leave"])
    character_sheet: CharacterSheetData | None = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    environment: str


class QuestResponse(BaseModel):
    """Response model for innkeeper quest introduction."""

    narrative: str


class ResolveResponse(BaseModel):
    """Response model for keeper action resolution."""

    result: str


class ComplicateResponse(BaseModel):
    """Response model for jester complication."""

    complication: str


class StartCombatResponse(BaseModel):
    """Response model for combat start."""

    narrative: str
    combat_state: CombatState
    initiative_results: list[dict[str, Any]]


class CombatActionResponse(BaseModel):
    """Response model for combat action."""

    success: bool
    result: dict[str, Any]  # Attack result details
    message: str  # Formatted text result
    narrative: str | None = None  # LLM summary at combat end
    combat_state: CombatState
    combat_ended: bool
    victory: bool | None  # True=win, False=lose, None=ongoing
    fled: bool = False  # True if player successfully fled
