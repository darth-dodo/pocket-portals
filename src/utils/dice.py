"""Dice rolling utility for D&D-style dice notation."""

import random
import re
from dataclasses import dataclass


@dataclass
class DiceRoll:
    """Result of a dice roll.

    Attributes:
        notation: The dice notation used (e.g., "1d20+3")
        rolls: List of individual die results
        modifier: The modifier applied to the roll
        total: The final total (sum of rolls + modifier)
    """

    notation: str
    rolls: list[int]
    modifier: int
    total: int

    def __str__(self) -> str:
        """Format dice roll as human-readable string.

        Returns:
            Formatted string like "5 + 3 + 2 = 10" or "5 + 3 = 8"

        Examples:
            >>> roll = DiceRoll("1d6+2", [4], 2, 6)
            >>> str(roll)
            '4 + 2 = 6'
            >>> roll = DiceRoll("2d6+3", [4, 5], 3, 12)
            >>> str(roll)
            '4 + 5 + 3 = 12'
        """
        # Build the parts of the equation
        parts = [str(roll) for roll in self.rolls]

        # Add modifier if non-zero
        if self.modifier > 0:
            parts.append(f"+{self.modifier}")
        elif self.modifier < 0:
            parts.append(str(self.modifier))

        # Join with spaces and add equals sign
        equation = " + ".join(parts)
        return f"{equation} = {self.total}"


class DiceRoller:
    """Utility class for rolling dice using D&D-style notation.

    Supports standard dice notation like:
    - 1d20 (single twenty-sided die)
    - 2d6 (two six-sided dice)
    - 1d8+3 (one eight-sided die plus 3)
    - 1d6-2 (one six-sided die minus 2)

    Also supports advantage/disadvantage mechanics (roll 2d20, take higher/lower).
    """

    # Regex pattern for dice notation: XdY+Z or XdY-Z
    DICE_PATTERN = re.compile(r"^(\d+)[dD](\d+)([+-]\d+)?$")

    @staticmethod
    def roll(notation: str) -> DiceRoll:
        """Parse and roll dice notation.

        Args:
            notation: Dice notation string (e.g., "1d20", "2d6+3", "1d8-2")

        Returns:
            DiceRoll object with results

        Raises:
            ValueError: If notation is invalid or contains invalid values

        Examples:
            >>> result = DiceRoller.roll("1d20")
            >>> 1 <= result.total <= 20
            True
            >>> result = DiceRoller.roll("2d6+3")
            >>> 5 <= result.total <= 15
            True
        """
        # Strip whitespace
        notation = notation.strip()

        # Match against pattern
        match = DiceRoller.DICE_PATTERN.match(notation)
        if not match:
            raise ValueError(
                f"Invalid dice notation: {notation}. "
                f"Expected format like '1d20', '2d6+3', or '1d8-2'"
            )

        # Extract components
        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier_str = match.group(3)

        # Validate values
        if num_dice <= 0:
            raise ValueError(
                f"Invalid dice notation: {notation}. Number of dice must be positive"
            )
        if die_size <= 0:
            raise ValueError(
                f"Invalid dice notation: {notation}. Die size must be positive"
            )

        # Parse modifier (default to 0)
        modifier = 0
        if modifier_str:
            modifier = int(modifier_str)

        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]

        # Calculate total
        total = sum(rolls) + modifier

        return DiceRoll(
            notation=notation,
            rolls=rolls,
            modifier=modifier,
            total=total,
        )

    @staticmethod
    def roll_with_advantage() -> DiceRoll:
        """Roll with advantage (2d20, take higher).

        In D&D 5e, advantage means you roll two d20s and take the higher result.

        Returns:
            DiceRoll object with two d20 rolls, total is the higher value

        Examples:
            >>> result = DiceRoller.roll_with_advantage()
            >>> len(result.rolls) == 2
            True
            >>> result.total == max(result.rolls)
            True
        """
        # Roll 2d20
        rolls = [random.randint(1, 20), random.randint(1, 20)]

        # Take the higher roll
        total = max(rolls)

        return DiceRoll(
            notation="2d20 (advantage)",
            rolls=rolls,
            modifier=0,
            total=total,
        )

    @staticmethod
    def roll_with_disadvantage() -> DiceRoll:
        """Roll with disadvantage (2d20, take lower).

        In D&D 5e, disadvantage means you roll two d20s and take the lower result.

        Returns:
            DiceRoll object with two d20 rolls, total is the lower value

        Examples:
            >>> result = DiceRoller.roll_with_disadvantage()
            >>> len(result.rolls) == 2
            True
            >>> result.total == min(result.rolls)
            True
        """
        # Roll 2d20
        rolls = [random.randint(1, 20), random.randint(1, 20)]

        # Take the lower roll
        total = min(rolls)

        return DiceRoll(
            notation="2d20 (disadvantage)",
            rolls=rolls,
            modifier=0,
            total=total,
        )
