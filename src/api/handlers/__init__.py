"""Handlers package for Pocket Portals API.

This package contains handler functions extracted from main.py for better
code organization and maintainability.

Modules:
    character: Character creation and interview handling
    quest: Quest selection and progression handling
    combat: Combat state and action handling
"""

from src.api.handlers.character import (
    generate_character_from_history,
    handle_character_creation,
)
from src.api.handlers.combat import (
    handle_combat_action,
)
from src.api.handlers.quest import (
    handle_quest_selection,
)

__all__ = [
    # Character handlers
    "handle_character_creation",
    "generate_character_from_history",
    # Quest handlers
    "handle_quest_selection",
    # Combat handlers
    "handle_combat_action",
]
