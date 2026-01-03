"""Constants for the Pocket Portals API.

This module contains game-related constants including starter choices,
narrative text, and character creation options used throughout the API.
"""

# Starter choices pool - adventure hooks to begin the journey
STARTER_CHOICES_POOL = [
    "Enter the mysterious tavern",
    "Explore the dark forest path",
    "Investigate the ancient ruins",
    "Follow the hooded stranger",
    "Approach the glowing portal",
    "Descend into the forgotten dungeon",
    "Board the departing airship",
    "Answer the distress signal",
    "Accept the wizard's quest",
]

WELCOME_NARRATIVE = (
    "The mists part before you, revealing crossroads where destiny awaits. "
    "Three paths shimmer with possibility, each promising adventure, danger, "
    "and glory. Choose wisely, brave soul, for your legend begins with a single step..."
)

# Character creation narrative - innkeeper greeting
CHARACTER_CREATION_NARRATIVE = (
    "You push through the tavern door, escaping the cold night. The warmth of the fire "
    "and the smell of ale wash over you. Behind the bar, a weathered innkeeper looks up "
    "with knowing eyes. 'Well now,' he says, wiping a mug, 'another soul seeking adventure. "
    "Before I point you toward trouble, tell me - who are you, traveler?'"
)

CHARACTER_CREATION_CHOICES = [
    "I am a battle-hardened dwarf",
    "I am an elven mage seeking knowledge",
    "I am a human rogue with secrets",
]
