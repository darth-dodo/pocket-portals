"""Tests for KeeperAgent - game mechanics resolution."""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.keeper import KeeperAgent
from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)
from src.state.models import CombatantType, CombatPhaseEnum


def test_keeper_initializes() -> None:
    """Test that KeeperAgent initializes when API key is present."""
    keeper = KeeperAgent()

    assert keeper is not None
    assert keeper.agent is not None
    assert keeper.llm is not None


@patch("src.agents.keeper.Task")
def test_keeper_resolve_action_returns_string(mock_task: MagicMock) -> None:
    """Test that resolve_action returns a non-empty string."""
    # Mock the task execution
    mock_task_instance = MagicMock()
    mock_task_instance.execute_sync.return_value = "14. Hits. 6 damage."
    mock_task.return_value = mock_task_instance

    keeper = KeeperAgent()

    action = "swing sword at goblin"
    context = "You're in combat with a goblin guard"

    result = keeper.resolve_action(action=action, context=context)

    assert isinstance(result, str)
    assert len(result) > 0


class TestFormatInitiativeResult:
    """Tests for format_initiative_result method."""

    def test_formats_initiative_with_player_first(self) -> None:
        """Should format initiative results with player going first."""
        keeper = KeeperAgent()

        results = [
            {"id": "player", "roll": 15, "modifier": 2, "total": 17},
            {"id": "enemy", "roll": 10, "modifier": 1, "total": 11},
        ]

        output = keeper.format_initiative_result(results)

        assert "Initiative!" in output
        assert "Player:" in output
        assert "1d20+2 = 17" in output
        assert "rolled 15" in output
        assert "Enemy:" in output
        assert "1d20+1 = 11" in output
        assert "rolled 10" in output
        assert "Player goes first!" in output

    def test_formats_initiative_with_enemy_first(self) -> None:
        """Should format initiative results with enemy going first."""
        keeper = KeeperAgent()

        results = [
            {"id": "player", "roll": 8, "modifier": 2, "total": 10},
            {"id": "enemy", "roll": 18, "modifier": 1, "total": 19},
        ]

        output = keeper.format_initiative_result(results)

        assert "Initiative!" in output
        assert "Enemy goes first!" in output

    def test_formats_negative_modifier(self) -> None:
        """Should correctly format negative modifiers."""
        keeper = KeeperAgent()

        results = [
            {"id": "player", "roll": 12, "modifier": 2, "total": 14},
            {"id": "enemy", "roll": 10, "modifier": -1, "total": 9},
        ]

        output = keeper.format_initiative_result(results)

        assert "1d20-1 = 9" in output

    def test_handles_zero_modifier(self) -> None:
        """Should correctly format zero modifiers."""
        keeper = KeeperAgent()

        results = [
            {"id": "player", "roll": 12, "modifier": 0, "total": 12},
            {"id": "enemy", "roll": 8, "modifier": 0, "total": 8},
        ]

        output = keeper.format_initiative_result(results)

        assert "1d20+0 = 12" in output
        assert "1d20+0 = 8" in output

    def test_handles_empty_results(self) -> None:
        """Should handle empty results list gracefully."""
        keeper = KeeperAgent()

        output = keeper.format_initiative_result([])

        assert "No initiative results" in output

    def test_capitalizes_combatant_names(self) -> None:
        """Should capitalize combatant names properly."""
        keeper = KeeperAgent()

        results = [
            {"id": "player", "roll": 12, "modifier": 0, "total": 12},
            {"id": "goblin_raider", "roll": 8, "modifier": 0, "total": 8},
        ]

        output = keeper.format_initiative_result(results)

        assert "Player:" in output
        assert "Goblin Raider:" in output


class TestKeeperCombat:
    """Test suite for KeeperAgent combat methods."""

    @pytest.fixture
    def keeper(self) -> KeeperAgent:
        """Create a KeeperAgent instance for testing."""
        return KeeperAgent()

    @pytest.fixture
    def character_sheet(self) -> CharacterSheet:
        """Create a test character sheet."""
        stats = CharacterStats(
            strength=14,
            dexterity=16,
            constitution=12,
            intelligence=10,
            wisdom=12,
            charisma=8,
        )
        return CharacterSheet(
            name="Test Hero",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
            stats=stats,
            current_hp=20,
            max_hp=20,
        )

    def test_start_combat_creates_active_state(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Starting combat creates active CombatState."""
        combat_state, _ = keeper.start_combat(character_sheet, "goblin")
        assert combat_state.is_active is True

    def test_start_combat_creates_player_combatant(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Player combatant created from character sheet."""
        combat_state, _ = keeper.start_combat(character_sheet, "goblin")
        player = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        assert player.name == "Test Hero"
        assert player.current_hp == 20
        assert player.max_hp == 20

    def test_start_combat_creates_enemy_combatant(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Enemy combatant created from template."""
        combat_state, _ = keeper.start_combat(character_sheet, "goblin")
        enemy = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )
        assert enemy.name == "Goblin Raider"
        assert enemy.max_hp == 7

    def test_initiative_results_returned(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Initiative results contain rolls for each combatant."""
        _, results = keeper.start_combat(character_sheet, "goblin")
        assert len(results) == 2
        for result in results:
            assert "id" in result
            assert "total" in result

    def test_turn_order_sorted_by_initiative(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Turn order sorted high to low by initiative total."""
        combat_state, results = keeper.start_combat(character_sheet, "goblin")
        # Get totals in turn order
        totals = []
        for combatant_id in combat_state.turn_order:
            result = next(r for r in results if r["id"] == combatant_id)
            totals.append(result["total"])
        assert totals == sorted(totals, reverse=True)

    def test_phase_set_to_first_combatant_turn(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Phase is set based on who goes first."""
        combat_state, _ = keeper.start_combat(character_sheet, "goblin")
        first_id = combat_state.turn_order[0]
        first_combatant = next(c for c in combat_state.combatants if c.id == first_id)
        if first_combatant.type == CombatantType.PLAYER:
            assert combat_state.phase == CombatPhaseEnum.PLAYER_TURN
        else:
            assert combat_state.phase == CombatPhaseEnum.ENEMY_TURN

    def test_invalid_enemy_type_raises_error(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Unknown enemy type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown enemy type"):
            keeper.start_combat(character_sheet, "dragon")

    def test_roll_initiative_returns_results(self, keeper: KeeperAgent) -> None:
        """roll_initiative returns properly formatted results."""
        from src.state.models import Combatant

        combatants = [
            Combatant(
                id="player",
                name="Hero",
                type=CombatantType.PLAYER,
                current_hp=20,
                max_hp=20,
                armor_class=15,
            ),
            Combatant(
                id="enemy",
                name="Goblin",
                type=CombatantType.ENEMY,
                current_hp=7,
                max_hp=7,
                armor_class=13,
            ),
        ]
        dex_modifiers = {"player": 2, "enemy": 1}

        results = keeper.roll_initiative(combatants, dex_modifiers)

        assert len(results) == 2
        for result in results:
            assert "id" in result
            assert "roll" in result
            assert "modifier" in result
            assert "total" in result
            assert result["total"] == result["roll"] + result["modifier"]

    def test_get_current_turn_combatant(
        self, keeper: KeeperAgent, character_sheet: CharacterSheet
    ) -> None:
        """Returns correct combatant for current turn."""
        combat_state, _ = keeper.start_combat(character_sheet, "goblin")
        current = keeper.get_current_turn_combatant(combat_state)
        assert current is not None
        assert current.id == combat_state.turn_order[0]
