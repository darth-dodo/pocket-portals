"""Content safety filtering and combat detection utilities.

This module provides content filtering to redirect inappropriate player input
and combat detection functions to identify combat triggers and enemy types
from player actions.
"""

# Blocked content patterns - redirects inappropriate input to safe message
BLOCKED_PATTERNS = [
    # Self-harm
    "hurt myself",
    "kill myself",
    "harm myself",
    "cut myself",
    "suicide",
    "self-harm",
    "self harm",
    "end my life",
    "end it all",
    # Sexual content
    "sex",
    "seduce",
    "kiss",
    "romance",
    "make love",
    "naked",
    "undress",
    "sexual",
    "erotic",
    "intimate",
    # Violence/torture
    "torture",
    "mutilate",
    "rape",
    "abuse",
    "molest",
    # Hate speech
    "slur",
    "racist",
    "nazi",
]

SAFE_REDIRECT = "take a deep breath and focus on the adventure ahead"

# Combat trigger keywords - subset of mechanical keywords for auto-starting combat
COMBAT_TRIGGER_KEYWORDS = [
    "attack",
    "fight",
    "swing",
    "shoot",
    "hit",
    "strike",
    "charge",
    "lunge",
]

# Enemy keywords to help detect combat context
ENEMY_KEYWORDS = [
    "goblin",
    "orc",
    "troll",
    "skeleton",
    "zombie",
    "bandit",
    "wolf",
    "bear",
    "dragon",
    "monster",
    "enemy",
    "creature",
]


def filter_content(action: str) -> str:
    """Filter inappropriate content from player actions.

    Args:
        action: Player's action text

    Returns:
        Original action if safe, or redirect action if inappropriate
    """
    action_lower = action.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in action_lower:
            return SAFE_REDIRECT
    return action


def detect_combat_trigger(action: str) -> bool:
    """Detect if action contains combat trigger keywords.

    Args:
        action: Player's action text

    Returns:
        True if action likely initiates combat
    """
    action_lower = action.lower()

    # Check for combat trigger keywords
    has_combat_keyword = any(
        keyword in action_lower for keyword in COMBAT_TRIGGER_KEYWORDS
    )

    # Check for enemy keywords to strengthen signal
    has_enemy_keyword = any(keyword in action_lower for keyword in ENEMY_KEYWORDS)

    # Combat trigger if both keywords present, or just combat keyword with strong intent
    return has_combat_keyword and (has_enemy_keyword or len(action_lower.split()) < 5)


def detect_enemy_type(action: str) -> str:
    """Detect enemy type from action text.

    Args:
        action: Player's action text

    Returns:
        Enemy type key for ENEMY_TEMPLATES, defaults to "goblin"
    """
    action_lower = action.lower()

    # Map keywords to enemy types
    enemy_map = {
        "goblin": "goblin",
        "orc": "orc",
        "troll": "troll",
        "skeleton": "skeleton",
        "zombie": "skeleton",  # Use skeleton template for zombie
        "bandit": "goblin",  # Use goblin template for bandit
        "wolf": "goblin",  # Use goblin template for wolf
        "bear": "orc",  # Use orc template for bear (stronger)
        "dragon": "troll",  # Use troll template for dragon (strongest available)
    }

    for keyword, enemy_type in enemy_map.items():
        if keyword in action_lower:
            return enemy_type

    # Default to goblin for generic combat
    return "goblin"
