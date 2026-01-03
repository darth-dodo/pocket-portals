"""Character Builder Agent - Generates character sheets from interview data.

This subagent analyzes the 5-turn character interview conversation and generates
intelligent character stats based on player choices using CrewAI's structured
Pydantic output pattern.
"""

import logging

from crewai import LLM, Agent, Task
from pydantic import BaseModel, Field

from src.config.loader import load_agent_config, load_task_config
from src.config.settings import settings
from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)

logger = logging.getLogger(__name__)


class CharacterStatsOutput(BaseModel):
    """Structured output for character ability scores (3-18 range)."""

    strength: int = Field(ge=3, le=18, description="Physical power")
    dexterity: int = Field(ge=3, le=18, description="Agility and reflexes")
    constitution: int = Field(ge=3, le=18, description="Health and stamina")
    intelligence: int = Field(ge=3, le=18, description="Reasoning and memory")
    wisdom: int = Field(ge=3, le=18, description="Insight and perception")
    charisma: int = Field(ge=3, le=18, description="Force of personality")


class CharacterBuildOutput(BaseModel):
    """Structured output for complete character generation from LLM."""

    name: str = Field(min_length=1, max_length=50, description="Character name")
    race: str = Field(
        description="One of: human, elf, dwarf, halfling, dragonborn, tiefling"
    )
    character_class: str = Field(
        description="One of: fighter, wizard, rogue, cleric, ranger, bard"
    )
    stats: CharacterStatsOutput = Field(
        description="Ability scores based on conversation"
    )
    backstory: str = Field(
        max_length=500,
        default="An adventurer seeking fortune.",
        description="Brief backstory",
    )
    equipment: list[str] = Field(
        default_factory=list, description="Starting equipment based on class"
    )


class CharacterBuilderAgent:
    """Agent that generates character sheets from interview conversations.

    Uses CrewAI's structured Pydantic output pattern to reliably extract
    character information from the 5-turn character interview.
    """

    # String to enum mapping with lowercase keys
    RACE_MAP: dict[str, CharacterRace] = {
        "human": CharacterRace.HUMAN,
        "elf": CharacterRace.ELF,
        "dwarf": CharacterRace.DWARF,
        "halfling": CharacterRace.HALFLING,
        "dragonborn": CharacterRace.DRAGONBORN,
        "tiefling": CharacterRace.TIEFLING,
    }

    CLASS_MAP: dict[str, CharacterClass] = {
        "fighter": CharacterClass.FIGHTER,
        "wizard": CharacterClass.WIZARD,
        "rogue": CharacterClass.ROGUE,
        "cleric": CharacterClass.CLERIC,
        "ranger": CharacterClass.RANGER,
        "bard": CharacterClass.BARD,
    }

    def __init__(self) -> None:
        """Initialize the Character Builder agent from YAML config."""
        config = load_agent_config("character_builder")

        self.llm = LLM(
            model=config.llm.model,
            api_key=settings.anthropic_api_key,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

        self.agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=config.verbose,
            allow_delegation=config.allow_delegation,
            llm=self.llm,
        )

    def build_character(self, conversation_history: str) -> CharacterSheet:
        """Generate a character sheet from interview conversation.

        Analyzes the 5-turn character creation conversation and generates
        appropriate stats based on player choices.

        Args:
            conversation_history: Formatted string of player-innkeeper exchanges

        Returns:
            CharacterSheet with intelligent stat generation based on conversation
        """
        try:
            task_config = load_task_config("build_character")

            task = Task(
                description=task_config.description.format(
                    conversation_history=conversation_history
                ),
                expected_output=task_config.expected_output,
                agent=self.agent,
                output_pydantic=CharacterBuildOutput,
            )

            result = task.execute_sync()

            # Check if we got structured output
            if hasattr(result, "pydantic") and result.pydantic is not None:
                # Cast to our expected output type
                output: CharacterBuildOutput = result.pydantic
                logger.info(
                    f"CharacterBuilder generated: {output.name} the {output.race} {output.character_class}"
                )
                return self._convert_to_character_sheet(output)

            # Fallback if pydantic parsing failed
            logger.warning("CharacterBuilder: Pydantic output was None, using fallback")
            return self._create_fallback_character()

        except Exception as e:
            logger.error(f"CharacterBuilder failed: {e}", exc_info=True)
            return self._create_fallback_character()

    def _convert_to_character_sheet(
        self, output: CharacterBuildOutput
    ) -> CharacterSheet:
        """Convert CharacterBuildOutput to CharacterSheet model.

        Args:
            output: The structured output from the LLM

        Returns:
            A valid CharacterSheet model instance
        """
        # Map race string to enum (with fallback to human)
        race_key = output.race.lower().strip()
        race = self.RACE_MAP.get(race_key, CharacterRace.HUMAN)

        # Map class string to enum (with fallback to fighter)
        class_key = output.character_class.lower().strip()
        character_class = self.CLASS_MAP.get(class_key, CharacterClass.FIGHTER)

        # Build stats from output
        stats = CharacterStats(
            strength=output.stats.strength,
            dexterity=output.stats.dexterity,
            constitution=output.stats.constitution,
            intelligence=output.stats.intelligence,
            wisdom=output.stats.wisdom,
            charisma=output.stats.charisma,
        )

        # Calculate HP based on constitution modifier
        con_modifier = (output.stats.constitution - 10) // 2
        base_hp = 10 + con_modifier
        max_hp = max(1, base_hp)  # Ensure at least 1 HP

        # Use provided equipment or generate defaults based on class
        equipment = (
            output.equipment if output.equipment else self._default_equipment(class_key)
        )

        return CharacterSheet(
            name=output.name,
            race=race,
            character_class=character_class,
            stats=stats,
            current_hp=max_hp,
            max_hp=max_hp,
            equipment=equipment,
            backstory=output.backstory or "An adventurer seeking fortune and glory.",
        )

    def _default_equipment(self, character_class: str) -> list[str]:
        """Generate default equipment based on character class.

        Args:
            character_class: The character's class name (lowercase)

        Returns:
            List of starting equipment items
        """
        equipment_by_class = {
            "fighter": ["Longsword", "Shield", "Chain mail", "10 gold pieces"],
            "wizard": [
                "Quarterstaff",
                "Spellbook",
                "Component pouch",
                "10 gold pieces",
            ],
            "rogue": [
                "Shortsword",
                "Dagger",
                "Thieves' tools",
                "Leather armor",
                "10 gold pieces",
            ],
            "cleric": ["Mace", "Holy symbol", "Scale mail", "Shield", "10 gold pieces"],
            "ranger": [
                "Longbow",
                "Quiver of arrows",
                "Shortsword",
                "Leather armor",
                "10 gold pieces",
            ],
            "bard": ["Rapier", "Lute", "Leather armor", "10 gold pieces"],
        }
        return equipment_by_class.get(
            character_class, ["Basic clothes", "10 gold pieces"]
        )

    def _create_fallback_character(self) -> CharacterSheet:
        """Create a fallback character when generation fails.

        Returns:
            A basic human fighter with default stats
        """
        logger.info("CharacterBuilder: Using fallback character generation")
        return CharacterSheet(
            name="Adventurer",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=14,
                dexterity=12,
                constitution=13,
                intelligence=10,
                wisdom=11,
                charisma=10,
            ),
            current_hp=11,  # 10 + 1 (CON modifier for 13)
            max_hp=11,
            equipment=["Longsword", "Shield", "Chain mail", "10 gold pieces"],
            backstory="A wandering adventurer seeking fortune and glory.",
        )
