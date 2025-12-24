"""Tests for character sheet models."""

import pytest
from pydantic import ValidationError

from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)


class TestCharacterStats:
    """Test suite for CharacterStats model."""

    def test_creates_with_default_values(self) -> None:
        """CharacterStats should create with default values of 10."""
        stats = CharacterStats()

        assert stats.strength == 10
        assert stats.dexterity == 10
        assert stats.constitution == 10
        assert stats.intelligence == 10
        assert stats.wisdom == 10
        assert stats.charisma == 10

    def test_creates_with_custom_values(self) -> None:
        """CharacterStats should accept custom values in valid range."""
        stats = CharacterStats(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=8,
            wisdom=12,
            charisma=10,
        )

        assert stats.strength == 16
        assert stats.dexterity == 14
        assert stats.constitution == 15
        assert stats.intelligence == 8
        assert stats.wisdom == 12
        assert stats.charisma == 10

    def test_rejects_stat_too_high(self) -> None:
        """CharacterStats should reject stats above 18."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(strength=25)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("strength",) for error in errors)

    def test_rejects_stat_too_low(self) -> None:
        """CharacterStats should reject stats below 3."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(dexterity=2)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("dexterity",) for error in errors)

    def test_allows_minimum_stat_value(self) -> None:
        """CharacterStats should allow stat value of 3."""
        stats = CharacterStats(strength=3)
        assert stats.strength == 3

    def test_allows_maximum_stat_value(self) -> None:
        """CharacterStats should allow stat value of 18."""
        stats = CharacterStats(strength=18)
        assert stats.strength == 18

    def test_calculates_modifier_for_low_stat(self) -> None:
        """CharacterStats should calculate negative modifier for low stats."""
        stats = CharacterStats(strength=8)
        assert stats.modifier("strength") == -1

    def test_calculates_modifier_for_high_stat(self) -> None:
        """CharacterStats should calculate positive modifier for high stats."""
        stats = CharacterStats(strength=16)
        assert stats.modifier("strength") == 3

    def test_calculates_modifier_for_average_stat(self) -> None:
        """CharacterStats should calculate zero modifier for 10-11."""
        stats = CharacterStats(strength=10)
        assert stats.modifier("strength") == 0

        stats = CharacterStats(strength=11)
        assert stats.modifier("strength") == 0

    def test_calculates_modifier_for_very_low_stat(self) -> None:
        """CharacterStats should calculate -4 modifier for stat of 3."""
        stats = CharacterStats(strength=3)
        assert stats.modifier("strength") == -4

    def test_calculates_modifier_for_very_high_stat(self) -> None:
        """CharacterStats should calculate +4 modifier for stat of 18."""
        stats = CharacterStats(strength=18)
        assert stats.modifier("strength") == 4

    def test_modifier_raises_for_invalid_stat_name(self) -> None:
        """CharacterStats modifier should raise ValueError for invalid stat name."""
        stats = CharacterStats()
        with pytest.raises(ValueError, match="Invalid stat name"):
            stats.modifier("invalid_stat")


class TestCharacterClass:
    """Test suite for CharacterClass enum."""

    def test_has_fighter(self) -> None:
        """CharacterClass should include fighter."""
        assert CharacterClass.FIGHTER.value == "fighter"

    def test_has_wizard(self) -> None:
        """CharacterClass should include wizard."""
        assert CharacterClass.WIZARD.value == "wizard"

    def test_has_rogue(self) -> None:
        """CharacterClass should include rogue."""
        assert CharacterClass.ROGUE.value == "rogue"

    def test_has_cleric(self) -> None:
        """CharacterClass should include cleric."""
        assert CharacterClass.CLERIC.value == "cleric"

    def test_has_ranger(self) -> None:
        """CharacterClass should include ranger."""
        assert CharacterClass.RANGER.value == "ranger"

    def test_has_bard(self) -> None:
        """CharacterClass should include bard."""
        assert CharacterClass.BARD.value == "bard"


class TestCharacterRace:
    """Test suite for CharacterRace enum."""

    def test_has_human(self) -> None:
        """CharacterRace should include human."""
        assert CharacterRace.HUMAN.value == "human"

    def test_has_elf(self) -> None:
        """CharacterRace should include elf."""
        assert CharacterRace.ELF.value == "elf"

    def test_has_dwarf(self) -> None:
        """CharacterRace should include dwarf."""
        assert CharacterRace.DWARF.value == "dwarf"

    def test_has_halfling(self) -> None:
        """CharacterRace should include halfling."""
        assert CharacterRace.HALFLING.value == "halfling"

    def test_has_dragonborn(self) -> None:
        """CharacterRace should include dragonborn."""
        assert CharacterRace.DRAGONBORN.value == "dragonborn"

    def test_has_tiefling(self) -> None:
        """CharacterRace should include tiefling."""
        assert CharacterRace.TIEFLING.value == "tiefling"


class TestCharacterSheet:
    """Test suite for CharacterSheet model."""

    def test_creates_with_minimal_required_fields(self) -> None:
        """CharacterSheet should create with name, race, and class."""
        sheet = CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
        )

        assert sheet.name == "Thorin"
        assert sheet.race == CharacterRace.DWARF
        assert sheet.character_class == CharacterClass.FIGHTER
        assert sheet.level == 1
        assert isinstance(sheet.stats, CharacterStats)

    def test_creates_with_all_fields(self) -> None:
        """CharacterSheet should accept all character fields."""
        stats = CharacterStats(strength=16, dexterity=14, constitution=15)
        sheet = CharacterSheet(
            name="Thorin Ironforge",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            level=3,
            stats=stats,
            current_hp=25,
            max_hp=35,
            equipment=["Warhammer", "Chain mail", "50 gold"],
            backstory="A blacksmith seeking redemption.",
        )

        assert sheet.name == "Thorin Ironforge"
        assert sheet.race == CharacterRace.DWARF
        assert sheet.character_class == CharacterClass.FIGHTER
        assert sheet.level == 3
        assert sheet.stats.strength == 16
        assert sheet.current_hp == 25
        assert sheet.max_hp == 35
        assert len(sheet.equipment) == 3
        assert sheet.backstory == "A blacksmith seeking redemption."

    def test_rejects_empty_name(self) -> None:
        """CharacterSheet should reject empty name."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_rejects_name_too_long(self) -> None:
        """CharacterSheet should reject name longer than 50 characters."""
        long_name = "A" * 51
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name=long_name,
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_rejects_level_too_low(self) -> None:
        """CharacterSheet should reject level below 1."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                level=0,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("level",) for error in errors)

    def test_rejects_level_too_high(self) -> None:
        """CharacterSheet should reject level above 20."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                level=21,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("level",) for error in errors)

    def test_rejects_current_hp_exceeding_max_hp(self) -> None:
        """CharacterSheet should reject current HP greater than max HP."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                current_hp=30,
                max_hp=20,
            )

        errors = exc_info.value.errors()
        assert any("cannot exceed" in error["msg"] for error in errors)

    def test_rejects_negative_current_hp(self) -> None:
        """CharacterSheet should reject negative current HP."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                current_hp=-1,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("current_hp",) for error in errors)

    def test_rejects_backstory_too_long(self) -> None:
        """CharacterSheet should reject backstory longer than 500 characters."""
        long_backstory = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            CharacterSheet(
                name="Test",
                race=CharacterRace.HUMAN,
                character_class=CharacterClass.FIGHTER,
                backstory=long_backstory,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("backstory",) for error in errors)

    def test_to_display_text_formats_correctly(self) -> None:
        """CharacterSheet to_display_text should format character information."""
        stats = CharacterStats(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=8,
            wisdom=12,
            charisma=10,
        )
        sheet = CharacterSheet(
            name="Thorin Ironforge",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            level=1,
            stats=stats,
            current_hp=20,
            max_hp=20,
            equipment=["Warhammer", "Chain mail"],
            backstory="A blacksmith seeking redemption.",
        )

        display = sheet.to_display_text()

        # Check key sections are present
        assert "CHARACTER SHEET" in display
        assert "Name: Thorin Ironforge" in display
        assert "Race: Dwarf" in display
        assert "Class: Fighter" in display
        assert "Level: 1" in display
        assert "ABILITY SCORES" in display
        assert "Strength:     16" in display
        assert "Dexterity:    14" in display
        assert "Constitution: 15" in display
        assert "Intelligence: 8" in display
        assert "Wisdom:       12" in display
        assert "Charisma:     10" in display
        assert "Health: 20/20" in display
        assert "EQUIPMENT" in display
        assert "- Warhammer" in display
        assert "- Chain mail" in display
        assert "BACKSTORY" in display
        assert "A blacksmith seeking redemption." in display

    def test_to_display_text_handles_default_equipment(self) -> None:
        """CharacterSheet to_display_text should show default equipment."""
        sheet = CharacterSheet(
            name="Test",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
        )

        display = sheet.to_display_text()

        assert "EQUIPMENT" in display
        # Default equipment should be present

    def test_serializes_to_dict_and_back(self) -> None:
        """CharacterSheet should serialize to dict and deserialize correctly."""
        original_sheet = CharacterSheet(
            name="Elara",
            race=CharacterRace.ELF,
            character_class=CharacterClass.WIZARD,
            level=2,
            stats=CharacterStats(strength=8, intelligence=16),
            current_hp=12,
            max_hp=14,
            equipment=["Spellbook", "Staff"],
            backstory="An academic mage.",
        )

        # Serialize to dict
        sheet_dict = original_sheet.model_dump()

        assert isinstance(sheet_dict, dict)
        assert sheet_dict["name"] == "Elara"
        assert sheet_dict["race"] == "elf"
        assert sheet_dict["character_class"] == "wizard"

        # Deserialize back to CharacterSheet
        restored_sheet = CharacterSheet(**sheet_dict)

        assert restored_sheet.name == original_sheet.name
        assert restored_sheet.race == original_sheet.race
        assert restored_sheet.character_class == original_sheet.character_class
        assert restored_sheet.level == original_sheet.level
        assert restored_sheet.stats.intelligence == original_sheet.stats.intelligence
        assert restored_sheet.current_hp == original_sheet.current_hp
        assert restored_sheet.max_hp == original_sheet.max_hp
        assert restored_sheet.equipment == original_sheet.equipment
        assert restored_sheet.backstory == original_sheet.backstory
