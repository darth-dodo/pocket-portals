"""Character sheet models for Pocket Portals."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class CharacterClass(str, Enum):
    """D&D character classes.

    Attributes:
        FIGHTER: Martial warrior with combat expertise
        WIZARD: Spellcaster with arcane magic
        ROGUE: Sneaky specialist with skills and cunning
        CLERIC: Divine spellcaster with healing and support
        RANGER: Wilderness warrior with tracking and nature magic
        BARD: Charismatic performer with music and magic
    """

    FIGHTER = "fighter"
    WIZARD = "wizard"
    ROGUE = "rogue"
    CLERIC = "cleric"
    RANGER = "ranger"
    BARD = "bard"


class CharacterRace(str, Enum):
    """D&D character races.

    Attributes:
        HUMAN: Versatile and adaptable
        ELF: Graceful and long-lived
        DWARF: Sturdy and resilient
        HALFLING: Small and nimble
        DRAGONBORN: Draconic heritage with breath weapon
        TIEFLING: Infernal heritage with supernatural traits
    """

    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"
    DRAGONBORN = "dragonborn"
    TIEFLING = "tiefling"


class CharacterStats(BaseModel):
    """Character ability scores (3-18 range).

    Attributes:
        strength: Physical power and athleticism
        dexterity: Agility, reflexes, and balance
        constitution: Health, stamina, and vital force
        intelligence: Reasoning, memory, and analytical skill
        wisdom: Awareness, intuition, and insight
        charisma: Force of personality and leadership
    """

    strength: int = Field(ge=3, le=18, default=10)
    dexterity: int = Field(ge=3, le=18, default=10)
    constitution: int = Field(ge=3, le=18, default=10)
    intelligence: int = Field(ge=3, le=18, default=10)
    wisdom: int = Field(ge=3, le=18, default=10)
    charisma: int = Field(ge=3, le=18, default=10)

    def modifier(self, stat_name: str) -> int:
        """Calculate ability modifier for a stat.

        D&D 5e modifier formula: (stat - 10) // 2

        Args:
            stat_name: Name of the stat (e.g., 'strength', 'dexterity')

        Returns:
            The ability modifier (typically -4 to +4 for stats 3-18)

        Raises:
            ValueError: If stat_name is not a valid stat

        Examples:
            >>> stats = CharacterStats(strength=16)
            >>> stats.modifier('strength')
            3
            >>> stats = CharacterStats(dexterity=8)
            >>> stats.modifier('dexterity')
            -1
        """
        valid_stats = {
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        }

        if stat_name not in valid_stats:
            raise ValueError(f"Invalid stat name: {stat_name}")

        stat_value = getattr(self, stat_name)
        return (stat_value - 10) // 2


class CharacterSheet(BaseModel):
    """Complete D&D character sheet.

    Attributes:
        name: Character's name (1-50 characters)
        race: Character's race
        character_class: Character's class
        level: Character level (1-20)
        stats: Ability scores
        current_hp: Current hit points
        max_hp: Maximum hit points
        equipment: List of equipment items
        backstory: Character backstory (max 500 characters)
    """

    # Identity
    name: str = Field(min_length=1, max_length=50)
    race: CharacterRace
    character_class: CharacterClass
    level: int = Field(ge=1, le=20, default=1)

    # Stats
    stats: CharacterStats = Field(default_factory=CharacterStats)

    # Vitals
    current_hp: int = Field(ge=0, default=20)
    max_hp: int = Field(ge=1, default=20)

    # Equipment
    equipment: list[str] = Field(
        default_factory=lambda: ["Basic clothes", "10 gold pieces"]
    )

    # Narrative
    backstory: str = Field(
        max_length=500, default="An adventurer seeking fortune and glory."
    )

    @model_validator(mode="after")
    def validate_hp_relationship(self) -> "CharacterSheet":
        """Validate that current HP does not exceed max HP.

        Returns:
            The validated model instance

        Raises:
            ValueError: If current_hp exceeds max_hp
        """
        if self.current_hp > self.max_hp:
            raise ValueError(
                f"current_hp ({self.current_hp}) cannot exceed max_hp ({self.max_hp})"
            )
        return self

    def to_display_text(self) -> str:
        """Format character sheet for display to user.

        Returns:
            Formatted multi-line string with character information

        Examples:
            >>> sheet = CharacterSheet(
            ...     name="Thorin",
            ...     race=CharacterRace.DWARF,
            ...     character_class=CharacterClass.FIGHTER
            ... )
            >>> print(sheet.to_display_text())
            CHARACTER SHEET
            ===============
            ...
        """
        return f"""CHARACTER SHEET
===============

Name: {self.name}
Race: {self.race.value.title()}
Class: {self.character_class.value.title()}
Level: {self.level}

ABILITY SCORES
--------------
Strength:     {self.stats.strength}
Dexterity:    {self.stats.dexterity}
Constitution: {self.stats.constitution}
Intelligence: {self.stats.intelligence}
Wisdom:       {self.stats.wisdom}
Charisma:     {self.stats.charisma}

VITALS
------
Health: {self.current_hp}/{self.max_hp}

EQUIPMENT
---------
{chr(10).join(f"- {item}" for item in self.equipment)}

BACKSTORY
---------
{self.backstory}""".strip()
