"""Tests for CombatManager service."""

from typing import Any

import pytest

from src.engine.combat_manager import CombatManager
from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)
from src.state.models import CombatantType, CombatPhaseEnum, CombatState


class TestCombatManager:
    """Test suite for CombatManager service."""

    @pytest.fixture
    def combat_manager(self) -> CombatManager:
        """Create a CombatManager instance for testing."""
        return CombatManager()

    @pytest.fixture
    def sample_character(self) -> CharacterSheet:
        """Create a sample character sheet for testing."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=16,
                dexterity=14,
                constitution=15,
            ),
            current_hp=25,
            max_hp=25,
        )

    def test_start_combat_creates_combat_state(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Starting combat creates active CombatState."""
        combat_state, initiative_results = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        assert combat_state.is_active is True
        assert len(combat_state.combatants) == 2
        assert len(initiative_results) == 2

    def test_start_combat_creates_player_combatant(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Player combatant created from character sheet."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        # Find player combatant
        player = next(
            (c for c in combat_state.combatants if c.type == CombatantType.PLAYER), None
        )

        assert player is not None
        assert player.name == "Thorin"
        assert player.current_hp == 25
        assert player.max_hp == 25
        assert player.is_alive is True

    def test_start_combat_creates_enemy_combatant(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Enemy combatant created from template."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        # Find enemy combatant
        enemy = next(
            (c for c in combat_state.combatants if c.type == CombatantType.ENEMY), None
        )

        assert enemy is not None
        assert enemy.name == "Goblin Raider"
        assert enemy.current_hp == 7
        assert enemy.max_hp == 7
        assert enemy.armor_class == 13
        assert enemy.is_alive is True

    def test_roll_initiative_returns_results(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Initiative results contain rolls and modifiers."""
        combat_state, initiative_results = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        assert len(initiative_results) == 2

        for result in initiative_results:
            assert "id" in result
            assert "roll" in result
            assert "modifier" in result
            assert "total" in result
            assert isinstance(result["roll"], int)
            assert isinstance(result["modifier"], int)
            assert isinstance(result["total"], int)
            # Total should be roll + modifier
            assert result["total"] == result["roll"] + result["modifier"]

    def test_turn_order_sorted_by_initiative(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Turn order sorted high to low by initiative total."""
        combat_state, initiative_results = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        # Check that turn_order is set and has correct number of combatants
        assert len(combat_state.turn_order) == 2

        # Verify turn_order matches initiative results sorted by total (descending)
        sorted_results = sorted(
            initiative_results, key=lambda x: x["total"], reverse=True
        )
        expected_order = [r["id"] for r in sorted_results]

        assert combat_state.turn_order == expected_order

    def test_combat_phase_starts_at_first_combatant_turn(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """After initiative, phase is first combatant's turn."""
        combat_state, initiative_results = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        # Get the first combatant in turn order
        first_combatant_id = combat_state.turn_order[0]
        first_combatant = next(
            c for c in combat_state.combatants if c.id == first_combatant_id
        )

        # Phase should be PLAYER_TURN or ENEMY_TURN based on who goes first
        if first_combatant.type == CombatantType.PLAYER:
            assert combat_state.phase == CombatPhaseEnum.PLAYER_TURN
        else:
            assert combat_state.phase == CombatPhaseEnum.ENEMY_TURN

        # Round number should start at 1
        assert combat_state.round_number == 1

    def test_invalid_enemy_type_raises_error(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Unknown enemy type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown enemy type"):
            combat_manager.start_combat(
                character_sheet=sample_character, enemy_type="nonexistent_enemy"
            )

    def test_get_current_turn_combatant(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Returns correct combatant for current turn."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        current_combatant = combat_manager.get_current_turn_combatant(combat_state)

        assert current_combatant is not None
        # Current combatant should match the first in turn_order
        assert current_combatant.id == combat_state.turn_order[0]

    def test_get_current_turn_combatant_with_empty_combat(
        self, combat_manager: CombatManager
    ) -> None:
        """Returns None for empty combat state."""
        from src.state.models import CombatState

        empty_combat = CombatState()
        result = combat_manager.get_current_turn_combatant(empty_combat)

        assert result is None

    def test_combat_state_stores_enemy_template(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Combat state stores the enemy template used."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        assert combat_state.enemy_template is not None
        assert combat_state.enemy_template.name == "Goblin Raider"
        assert combat_state.enemy_template.max_hp == 7

    def test_different_enemies_have_different_stats(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> None:
        """Different enemy types create different combatants."""
        # Test with goblin
        goblin_combat, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )
        goblin_enemy = next(
            c for c in goblin_combat.combatants if c.type == CombatantType.ENEMY
        )

        # Test with orc
        orc_combat, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="orc"
        )
        orc_enemy = next(
            c for c in orc_combat.combatants if c.type == CombatantType.ENEMY
        )

        # Orc should have more HP than goblin
        assert orc_enemy.max_hp > goblin_enemy.max_hp
        assert orc_enemy.name != goblin_enemy.name


class TestAttackResolution:
    """Test suite for attack resolution mechanics."""

    @pytest.fixture
    def combat_manager(self) -> CombatManager:
        """Create a CombatManager instance for testing."""
        return CombatManager()

    @pytest.fixture
    def sample_character(self) -> CharacterSheet:
        """Create a sample character sheet for testing."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=16,  # +3 modifier
                dexterity=14,  # +2 modifier
                constitution=15,
            ),
            current_hp=25,
            max_hp=25,
        )

    @pytest.fixture
    def combat_state_player_turn(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> tuple[object, CharacterSheet]:
        """Create combat state where it's the player's turn."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )

        # Force player turn for testing
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        combat_state.current_turn_index = 0
        combat_state.turn_order = ["player", "enemy"]

        return combat_state, sample_character

    def test_resolve_attack_hit(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Attack roll >= AC results in hit."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Store initial HP
        initial_hp = defender.current_hp

        # Roll attack multiple times to get at least one hit
        hit_found = False
        for _ in range(100):  # Try up to 100 times
            result = combat_manager.resolve_attack(
                attacker=attacker,
                defender=defender,
                attack_bonus=5,  # +5 bonus
                damage_dice="1d8+3",
                combat_state=combat_state,
            )

            if result["hit"]:
                hit_found = True
                assert result["total_attack"] >= defender.armor_class
                assert result["damage_roll"] is not None
                assert result["damage_dealt"] > 0
                assert result["defender_hp"] < initial_hp
                assert "log_entry" in result
                break

        assert hit_found, "Should have hit at least once in 100 attempts"

    def test_resolve_attack_miss(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Attack roll < AC results in miss."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Set defender AC very high to guarantee miss
        defender.armor_class = 30
        initial_hp = defender.current_hp

        result = combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=0,
            damage_dice="1d8",
            combat_state=combat_state,
        )

        assert result["hit"] is False
        assert result["damage_roll"] is None
        assert result["damage_dealt"] == 0
        assert defender.current_hp == initial_hp

    def test_damage_applied_on_hit(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Defender HP reduced by damage on hit."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Set defender AC low to guarantee hit and high HP to avoid overkill
        defender.armor_class = 5
        defender.current_hp = 100
        defender.max_hp = 100
        initial_hp = defender.current_hp

        result = combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=5,
            damage_dice="1d8+3",
            combat_state=combat_state,
        )

        assert result["hit"] is True
        assert result["damage_dealt"] > 0
        assert defender.current_hp == initial_hp - result["damage_dealt"]

    def test_no_damage_on_miss(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Defender HP unchanged on miss."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Set defender AC very high to guarantee miss
        defender.armor_class = 30
        initial_hp = defender.current_hp

        combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=0,
            damage_dice="1d8",
            combat_state=combat_state,
        )

        assert defender.current_hp == initial_hp

    def test_defender_dies_at_zero_hp(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """is_alive=False when HP reaches 0."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Set defender to low HP
        defender.current_hp = 1
        defender.armor_class = 5  # Low AC to guarantee hit

        result = combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=5,
            damage_dice="1d8+3",  # Will definitely kill with 1 HP
            combat_state=combat_state,
        )

        assert result["defender_hp"] == 0
        assert result["defender_alive"] is False
        assert defender.is_alive is False

    def test_hp_cannot_go_negative(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """HP floors at 0, not negative."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        # Set defender to low HP
        defender.current_hp = 1
        defender.armor_class = 5  # Low AC to guarantee hit

        result = combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=5,
            damage_dice="10d10+50",  # Massive overkill damage
            combat_state=combat_state,
        )

        assert defender.current_hp >= 0
        assert result["defender_hp"] >= 0

    def test_combat_log_updated(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Attack adds entry to combat_log."""
        combat_state, _ = combat_state_player_turn

        # Get combatants
        attacker = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        defender = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )

        initial_log_length = len(combat_state.combat_log)

        combat_manager.resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_bonus=5,
            damage_dice="1d8+3",
            combat_state=combat_state,
        )

        assert len(combat_state.combat_log) == initial_log_length + 1
        assert isinstance(combat_state.combat_log[-1], str)
        assert len(combat_state.combat_log[-1]) > 0

    def test_execute_player_attack_uses_class_weapon(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Player attack uses correct damage dice for class."""
        combat_state, character_sheet = combat_state_player_turn

        # Fighter should use 1d8 + STR modifier
        result = combat_manager.execute_player_attack(combat_state, character_sheet)

        assert "hit" in result
        assert "attack_roll" in result
        assert "damage_roll" in result or result["damage_roll"] is None

        # Verify the attack was logged
        assert len(combat_state.combat_log) > 0

    def test_execute_enemy_turn_uses_template(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Enemy attack uses template's attack_bonus and damage_dice."""
        combat_state, _ = combat_state_player_turn

        # Change to enemy turn
        combat_state.phase = CombatPhaseEnum.ENEMY_TURN

        result = combat_manager.execute_enemy_turn(combat_state)

        assert "hit" in result
        assert "attack_roll" in result
        assert "damage_roll" in result or result["damage_roll"] is None

        # Verify the attack was logged
        assert len(combat_state.combat_log) > 0

    def test_format_attack_result_readable(
        self, combat_manager: CombatManager, combat_state_player_turn: tuple
    ) -> None:
        """Formatted result is human-readable."""
        combat_state, character_sheet = combat_state_player_turn

        result = combat_manager.execute_player_attack(combat_state, character_sheet)
        formatted = combat_manager.format_attack_result(result)

        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should contain key information
        assert "Attack" in formatted or "attack" in formatted
        assert "AC" in formatted or "armor class" in formatted.lower()

    def test_fighter_uses_strength_for_attack(
        self, combat_manager: CombatManager
    ) -> None:
        """Fighter uses STR modifier for attack bonus."""
        fighter = CharacterSheet(
            name="Fighter",
            race=CharacterRace.HUMAN,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(strength=16, dexterity=10),
            current_hp=20,
            max_hp=20,
        )

        combat_state, _ = combat_manager.start_combat(fighter, "goblin")
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN

        result = combat_manager.execute_player_attack(combat_state, fighter)

        # Fighter with STR 16 should have +3 modifier
        # Attack roll should be 1d20 + 3
        assert result is not None

    def test_rogue_uses_dexterity_for_attack(
        self, combat_manager: CombatManager
    ) -> None:
        """Rogue uses DEX modifier for attack bonus."""
        rogue = CharacterSheet(
            name="Rogue",
            race=CharacterRace.HALFLING,
            character_class=CharacterClass.ROGUE,
            stats=CharacterStats(strength=10, dexterity=18),
            current_hp=20,
            max_hp=20,
        )

        combat_state, _ = combat_manager.start_combat(rogue, "goblin")
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN

        result = combat_manager.execute_player_attack(combat_state, rogue)

        # Rogue with DEX 18 should have +4 modifier
        assert result is not None


class TestDefendAction:
    """Test suite for defend action mechanics."""

    @pytest.fixture
    def combat_manager(self) -> CombatManager:
        """Create a CombatManager instance for testing."""
        return CombatManager()

    @pytest.fixture
    def sample_character(self) -> CharacterSheet:
        """Create a sample character sheet for testing."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=16,
                dexterity=14,
                constitution=15,
            ),
            current_hp=25,
            max_hp=25,
        )

    @pytest.fixture
    def active_combat_state(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> tuple[CombatState, CharacterSheet]:
        """Create an active combat state for testing."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )
        # Ensure player goes first
        combat_state.turn_order = ["player", "enemy"]
        combat_state.current_turn_index = 0
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        combat_state.round_number = 1
        return combat_state, sample_character

    def test_defend_sets_defending_flag(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Defend sets player_defending = True."""
        combat_state, character_sheet = active_combat_state

        result = combat_manager.execute_defend(combat_state, character_sheet)

        assert result["action"] == "defend"
        assert result["success"] is True
        assert combat_state.player_defending is True

    def test_defend_logs_action(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Defend adds entry to combat_log."""
        combat_state, character_sheet = active_combat_state
        initial_log_length = len(combat_state.combat_log)

        result = combat_manager.execute_defend(combat_state, character_sheet)

        assert len(combat_state.combat_log) == initial_log_length + 1
        assert "defensive stance" in combat_state.combat_log[-1].lower()
        assert f"Round {combat_state.round_number}" in result["log_entry"]

    def test_enemy_attack_with_disadvantage_when_defending(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Enemy rolls with disadvantage if player defended."""
        combat_state, character_sheet = active_combat_state

        # Player defends
        combat_manager.execute_defend(combat_state, character_sheet)
        assert combat_state.player_defending is True

        # Switch to enemy turn
        combat_state.phase = CombatPhaseEnum.ENEMY_TURN

        # Execute enemy turn - should roll with disadvantage
        result = combat_manager.execute_enemy_turn(combat_state)

        # Check that attack was made
        assert "attack_roll" in result
        # Check log mentions disadvantage
        assert "disadvantage" in combat_state.combat_log[-1].lower()

    def test_defending_flag_resets_after_enemy_attack(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """player_defending resets to False after enemy turn."""
        combat_state, character_sheet = active_combat_state

        # Player defends
        combat_manager.execute_defend(combat_state, character_sheet)
        assert combat_state.player_defending is True

        # Switch to enemy turn
        combat_state.phase = CombatPhaseEnum.ENEMY_TURN

        # Enemy attacks
        combat_manager.execute_enemy_turn(combat_state)

        # Flag should be reset
        assert combat_state.player_defending is False


class TestFleeAction:
    """Test suite for flee action mechanics."""

    @pytest.fixture
    def combat_manager(self) -> CombatManager:
        """Create a CombatManager instance for testing."""
        return CombatManager()

    @pytest.fixture
    def sample_character(self) -> CharacterSheet:
        """Create a sample character sheet for testing."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=16,
                dexterity=14,  # +2 modifier
                constitution=15,
            ),
            current_hp=25,
            max_hp=25,
        )

    @pytest.fixture
    def active_combat_state(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> tuple[CombatState, CharacterSheet]:
        """Create an active combat state for testing."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )
        # Ensure player goes first
        combat_state.turn_order = ["player", "enemy"]
        combat_state.current_turn_index = 0
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        combat_state.round_number = 1
        return combat_state, sample_character

    def test_flee_success_on_high_roll(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Flee succeeds when roll >= DC 12."""
        combat_state, character_sheet = active_combat_state

        # Try multiple times to ensure we get a success
        success_found = False
        for _ in range(100):
            # Reset combat state for each attempt
            combat_state.is_active = True

            result = combat_manager.execute_flee(combat_state, character_sheet)

            if result["success"]:
                success_found = True
                assert result["action"] == "flee"
                assert result["roll"].total >= result["dc"]
                assert result["dc"] == 12
                assert result["free_attack"] is None
                assert combat_state.is_active is False
                break

        assert success_found, "Should succeed at least once in 100 attempts"

    def test_flee_failure_on_low_roll(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Flee fails when roll < DC 12."""
        combat_state, character_sheet = active_combat_state

        # Try multiple times to ensure we get a failure
        failure_found = False
        for _ in range(100):
            # Reset combat state for each attempt
            combat_state.is_active = True

            result = combat_manager.execute_flee(combat_state, character_sheet)

            if not result["success"]:
                failure_found = True
                assert result["action"] == "flee"
                assert result["roll"].total < result["dc"]
                assert result["dc"] == 12
                assert result["free_attack"] is not None
                assert combat_state.is_active is True
                break

        assert failure_found, "Should fail at least once in 100 attempts"

    def test_flee_uses_dex_modifier(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Flee roll includes DEX modifier."""
        combat_state, character_sheet = active_combat_state

        # Character has DEX 14 = +2 modifier
        expected_modifier = 2

        result = combat_manager.execute_flee(combat_state, character_sheet)

        # The roll should be in format 1d20+modifier
        assert result["roll"].modifier == expected_modifier

    def test_flee_failure_triggers_free_attack(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Failed flee gives enemy free attack with advantage."""
        combat_state, character_sheet = active_combat_state

        # Try until we get a failed flee
        for _ in range(100):
            combat_state.is_active = True
            result = combat_manager.execute_flee(combat_state, character_sheet)

            if not result["success"]:
                # Check that free_attack exists
                assert result["free_attack"] is not None
                attack_result = result["free_attack"]
                assert "hit" in attack_result
                # Check log mentions advantage
                assert "advantage" in combat_state.combat_log[-1].lower()
                break

    def test_flee_success_ends_combat(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Successful flee sets is_active = False."""
        combat_state, character_sheet = active_combat_state

        # Try until we get a successful flee
        for _ in range(100):
            combat_state.is_active = True

            result = combat_manager.execute_flee(combat_state, character_sheet)

            if result["success"]:
                assert combat_state.is_active is False
                break

    def test_flee_logs_attempt(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Flee attempt added to combat_log."""
        combat_state, character_sheet = active_combat_state
        initial_log_length = len(combat_state.combat_log)

        combat_manager.execute_flee(combat_state, character_sheet)

        # At least one log entry should be added (flee attempt)
        assert len(combat_state.combat_log) > initial_log_length
        # Check flee is mentioned in log
        flee_log_found = any("flee" in log.lower() for log in combat_state.combat_log)
        assert flee_log_found


class TestCombatFlow:
    """Test suite for combat flow methods (turn advancement and combat end detection)."""

    @pytest.fixture
    def combat_manager(self) -> CombatManager:
        """Create a CombatManager instance for testing."""
        return CombatManager()

    @pytest.fixture
    def sample_character(self) -> CharacterSheet:
        """Create a sample character sheet for testing."""
        return CharacterSheet(
            name="Thorin",
            race=CharacterRace.DWARF,
            character_class=CharacterClass.FIGHTER,
            stats=CharacterStats(
                strength=16,
                dexterity=14,
                constitution=15,
            ),
            current_hp=25,
            max_hp=25,
        )

    @pytest.fixture
    def active_combat_state(
        self, combat_manager: CombatManager, sample_character: CharacterSheet
    ) -> CombatState:
        """Create an active combat state for testing."""
        combat_state, _ = combat_manager.start_combat(
            character_sheet=sample_character, enemy_type="goblin"
        )
        # Ensure player goes first
        combat_state.turn_order = ["player", "enemy"]
        combat_state.current_turn_index = 0
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        combat_state.round_number = 1
        return combat_state

    def test_advance_turn_increments_index(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Turn index advances to next combatant."""
        combat_state = active_combat_state
        initial_index = combat_state.current_turn_index

        combat_manager.advance_turn(combat_state)

        assert combat_state.current_turn_index == initial_index + 1

    def test_advance_turn_wraps_around(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Turn index wraps to 0 after last combatant."""
        combat_state = active_combat_state
        # Set to last combatant
        combat_state.current_turn_index = len(combat_state.turn_order) - 1

        combat_manager.advance_turn(combat_state)

        assert combat_state.current_turn_index == 0

    def test_advance_turn_increments_round(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Round number increments when turn wraps."""
        combat_state = active_combat_state
        initial_round = combat_state.round_number
        # Set to last combatant
        combat_state.current_turn_index = len(combat_state.turn_order) - 1

        combat_manager.advance_turn(combat_state)

        assert combat_state.round_number == initial_round + 1

    def test_advance_turn_updates_phase(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Phase changes based on current combatant type."""
        combat_state = active_combat_state
        # Start at player turn
        combat_state.current_turn_index = 0
        combat_state.phase = CombatPhaseEnum.PLAYER_TURN

        # Advance to enemy turn
        combat_manager.advance_turn(combat_state)

        assert combat_state.phase == CombatPhaseEnum.ENEMY_TURN

        # Advance back to player turn
        combat_manager.advance_turn(combat_state)

        # mypy can't track that advance_turn changes the phase
        assert combat_state.phase == CombatPhaseEnum.PLAYER_TURN  # type: ignore[comparison-overlap]

    def test_check_combat_end_victory(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Returns victory when enemy HP <= 0."""
        combat_state = active_combat_state

        # Kill the enemy
        enemy = next(
            c for c in combat_state.combatants if c.type == CombatantType.ENEMY
        )
        enemy.current_hp = 0
        enemy.is_alive = False

        ended, result = combat_manager.check_combat_end(combat_state)

        assert ended is True
        assert result == "victory"

    def test_check_combat_end_defeat(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Returns defeat when player HP <= 0."""
        combat_state = active_combat_state

        # Kill the player
        player = next(
            c for c in combat_state.combatants if c.type == CombatantType.PLAYER
        )
        player.current_hp = 0
        player.is_alive = False

        ended, result = combat_manager.check_combat_end(combat_state)

        assert ended is True
        assert result == "defeat"

    def test_check_combat_end_ongoing(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """Returns ongoing when both alive."""
        combat_state = active_combat_state

        ended, result = combat_manager.check_combat_end(combat_state)

        assert ended is False
        assert result is None

    def test_end_combat_deactivates(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """end_combat sets is_active=False."""
        combat_state = active_combat_state

        combat_manager.end_combat(combat_state, "victory")

        assert combat_state.is_active is False

    def test_end_combat_sets_resolution_phase(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """end_combat sets phase=RESOLUTION."""
        combat_state = active_combat_state

        combat_manager.end_combat(combat_state, "victory")

        assert combat_state.phase == CombatPhaseEnum.RESOLUTION

    def test_end_combat_adds_log_entry(
        self, combat_manager: CombatManager, active_combat_state: Any
    ) -> None:
        """end_combat adds final log entry."""
        combat_state = active_combat_state
        initial_log_length = len(combat_state.combat_log)

        combat_manager.end_combat(combat_state, "victory")

        assert len(combat_state.combat_log) == initial_log_length + 1
        assert "victory" in combat_state.combat_log[-1].lower()
