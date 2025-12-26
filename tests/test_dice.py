"""Tests for DiceRoller utility."""

import pytest

from src.utils.dice import DiceRoll, DiceRoller


class TestDiceRoll:
    """Test suite for DiceRoll data class."""

    def test_creates_with_all_attributes(self) -> None:
        """DiceRoll should create with all required attributes."""
        roll = DiceRoll(
            notation="1d6+2",
            rolls=[4],
            modifier=2,
            total=6,
        )

        assert roll.notation == "1d6+2"
        assert roll.rolls == [4]
        assert roll.modifier == 2
        assert roll.total == 6

    def test_str_format_with_single_die_and_modifier(self) -> None:
        """DiceRoll string format should show die + modifier = total."""
        roll = DiceRoll(notation="1d6+2", rolls=[4], modifier=2, total=6)
        result = str(roll)

        # Should show: "4 + 2 = 6"
        assert "4" in result
        assert "+2" in result or "+ 2" in result
        assert "6" in result

    def test_str_format_with_multiple_dice_and_modifier(self) -> None:
        """DiceRoll string format should show all dice + modifier = total."""
        roll = DiceRoll(notation="2d6+3", rolls=[4, 5], modifier=3, total=12)
        result = str(roll)

        # Should show: "4 + 5 + 3 = 12"
        assert "4" in result
        assert "5" in result
        assert "+3" in result or "+ 3" in result
        assert "12" in result

    def test_str_format_with_negative_modifier(self) -> None:
        """DiceRoll string format should handle negative modifiers."""
        roll = DiceRoll(notation="1d6-2", rolls=[5], modifier=-2, total=3)
        result = str(roll)

        # Should show: "5 - 2 = 3"
        assert "5" in result
        assert "-2" in result or "- 2" in result
        assert "3" in result

    def test_str_format_without_modifier(self) -> None:
        """DiceRoll string format should work without modifier."""
        roll = DiceRoll(notation="1d20", rolls=[15], modifier=0, total=15)
        result = str(roll)

        # Should show: "15 = 15" or just "15"
        assert "15" in result


class TestDiceRollerBasicRolls:
    """Test suite for basic DiceRoller functionality."""

    def test_roll_single_die_returns_valid_range(self) -> None:
        """Rolling 1d6 should return value between 1 and 6."""
        for _ in range(20):  # Test multiple times for randomness
            result = DiceRoller.roll("1d6")
            assert result.notation == "1d6"
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 6
            assert result.modifier == 0
            assert result.total == result.rolls[0]

    def test_roll_multiple_dice_returns_correct_count(self) -> None:
        """Rolling 2d6 should return exactly 2 die results."""
        for _ in range(20):
            result = DiceRoller.roll("2d6")
            assert result.notation == "2d6"
            assert len(result.rolls) == 2
            assert all(1 <= roll <= 6 for roll in result.rolls)
            assert result.modifier == 0
            assert result.total == sum(result.rolls)

    def test_roll_d20_returns_valid_range(self) -> None:
        """Rolling 1d20 should return value between 1 and 20."""
        for _ in range(20):
            result = DiceRoller.roll("1d20")
            assert result.notation == "1d20"
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 20
            assert result.total == result.rolls[0]

    def test_roll_with_positive_modifier(self) -> None:
        """Rolling 1d6+3 should add modifier to total."""
        for _ in range(20):
            result = DiceRoller.roll("1d6+3")
            assert result.notation == "1d6+3"
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 6
            assert result.modifier == 3
            assert result.total == result.rolls[0] + 3
            assert 4 <= result.total <= 9

    def test_roll_with_negative_modifier(self) -> None:
        """Rolling 1d6-2 should subtract modifier from total."""
        for _ in range(20):
            result = DiceRoller.roll("1d6-2")
            assert result.notation == "1d6-2"
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 6
            assert result.modifier == -2
            assert result.total == result.rolls[0] - 2
            # Minimum is 1-2=-1, maximum is 6-2=4
            assert -1 <= result.total <= 4

    def test_roll_multiple_dice_with_modifier(self) -> None:
        """Rolling 2d6+3 should work correctly."""
        for _ in range(20):
            result = DiceRoller.roll("2d6+3")
            assert result.notation == "2d6+3"
            assert len(result.rolls) == 2
            assert all(1 <= roll <= 6 for roll in result.rolls)
            assert result.modifier == 3
            assert result.total == sum(result.rolls) + 3
            # Minimum is 2+3=5, maximum is 12+3=15
            assert 5 <= result.total <= 15


class TestDiceRollerInvalidNotation:
    """Test suite for invalid dice notation handling."""

    def test_invalid_notation_raises_error(self) -> None:
        """Invalid dice notation should raise ValueError."""
        invalid_notations = [
            "invalid",
            "d6",  # Missing number of dice
            "1d",  # Missing die size
            "1d6+",  # Incomplete modifier
            "1d6+abc",  # Non-numeric modifier
            "abc1d6",  # Invalid format
            "",  # Empty string
            "1d0",  # Zero-sided die
            "0d6",  # Zero dice
        ]

        for notation in invalid_notations:
            with pytest.raises(ValueError, match=r"Invalid dice notation"):
                DiceRoller.roll(notation)

    def test_negative_dice_count_raises_error(self) -> None:
        """Negative dice count should raise ValueError."""
        with pytest.raises(ValueError, match=r"Invalid dice notation"):
            DiceRoller.roll("-1d6")

    def test_negative_die_size_raises_error(self) -> None:
        """Negative die size should raise ValueError."""
        with pytest.raises(ValueError, match=r"Invalid dice notation"):
            DiceRoller.roll("1d-6")


class TestDiceRollerAdvantageDisadvantage:
    """Test suite for advantage/disadvantage mechanics."""

    def test_roll_with_advantage_rolls_two_dice(self) -> None:
        """Advantage should roll 2d20 and take the higher."""
        for _ in range(20):
            result = DiceRoller.roll_with_advantage()
            assert result.notation == "2d20 (advantage)"
            assert len(result.rolls) == 2
            assert all(1 <= roll <= 20 for roll in result.rolls)
            assert result.modifier == 0
            # Total should be the maximum of the two rolls
            assert result.total == max(result.rolls)

    def test_roll_with_disadvantage_rolls_two_dice(self) -> None:
        """Disadvantage should roll 2d20 and take the lower."""
        for _ in range(20):
            result = DiceRoller.roll_with_disadvantage()
            assert result.notation == "2d20 (disadvantage)"
            assert len(result.rolls) == 2
            assert all(1 <= roll <= 20 for roll in result.rolls)
            assert result.modifier == 0
            # Total should be the minimum of the two rolls
            assert result.total == min(result.rolls)

    def test_advantage_total_greater_or_equal_to_disadvantage(self) -> None:
        """Advantage should generally give better results than disadvantage."""
        # This is a probabilistic test - run many times
        advantage_totals = [DiceRoller.roll_with_advantage().total for _ in range(100)]
        disadvantage_totals = [
            DiceRoller.roll_with_disadvantage().total for _ in range(100)
        ]

        # Average of advantage should be higher than disadvantage
        assert sum(advantage_totals) / len(advantage_totals) > sum(
            disadvantage_totals
        ) / len(disadvantage_totals)


class TestDiceRollerEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_roll_maximum_dice(self) -> None:
        """Rolling many dice should work correctly."""
        result = DiceRoller.roll("10d6")
        assert result.notation == "10d6"
        assert len(result.rolls) == 10
        assert all(1 <= roll <= 6 for roll in result.rolls)
        assert result.total == sum(result.rolls)
        # 10d6 should be between 10 and 60
        assert 10 <= result.total <= 60

    def test_roll_d100(self) -> None:
        """Rolling a d100 (percentile die) should work."""
        for _ in range(20):
            result = DiceRoller.roll("1d100")
            assert result.notation == "1d100"
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 100
            assert result.total == result.rolls[0]

    def test_roll_notation_case_insensitive(self) -> None:
        """Dice notation should accept both 'D' and 'd'."""
        result_lower = DiceRoller.roll("1d6")
        result_upper = DiceRoller.roll("1D6")

        # Both should parse correctly
        assert result_lower.notation == "1d6" or result_lower.notation == "1D6"
        assert result_upper.notation == "1D6" or result_upper.notation == "1d6"
        assert 1 <= result_lower.total <= 6
        assert 1 <= result_upper.total <= 6

    def test_roll_with_spaces_in_notation(self) -> None:
        """Dice notation should handle spaces gracefully."""
        # This test might need to be adjusted based on implementation
        # If spaces are not supported, this should raise an error
        try:
            result = DiceRoller.roll("1d6 + 3")
            # If spaces are stripped and handled
            assert result.modifier == 3
        except ValueError:
            # If spaces are not supported, that's also valid
            pass
