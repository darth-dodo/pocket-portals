"""Tests for combat state models."""

from src.data.enemies import ENEMY_TEMPLATES
from src.state.models import (
    CombatAction,
    Combatant,
    CombatantType,
    CombatPhaseEnum,
    CombatState,
    Enemy,
)


class TestCombatEnums:
    """Test suite for combat enumeration types."""

    def test_combat_phase_enum_values(self) -> None:
        """CombatPhaseEnum should have all required phases."""
        assert CombatPhaseEnum.INITIATIVE.value == "initiative"
        assert CombatPhaseEnum.PLAYER_TURN.value == "player_turn"
        assert CombatPhaseEnum.ENEMY_TURN.value == "enemy_turn"
        assert CombatPhaseEnum.RESOLUTION.value == "resolution"

    def test_combatant_type_enum_values(self) -> None:
        """CombatantType should have player and enemy types."""
        assert CombatantType.PLAYER.value == "player"
        assert CombatantType.ENEMY.value == "enemy"

    def test_combat_action_enum_values(self) -> None:
        """CombatAction should have all combat actions."""
        assert CombatAction.ATTACK.value == "attack"
        assert CombatAction.DEFEND.value == "defend"
        assert CombatAction.FLEE.value == "flee"


class TestCombatant:
    """Test suite for Combatant model."""

    def test_creates_player_combatant(self) -> None:
        """Should create a player combatant with valid attributes."""
        player = Combatant(
            id="player_1",
            name="Thorin",
            type=CombatantType.PLAYER,
            initiative=15,
            current_hp=20,
            max_hp=20,
            armor_class=16,
        )

        assert player.id == "player_1"
        assert player.name == "Thorin"
        assert player.type == CombatantType.PLAYER
        assert player.initiative == 15
        assert player.current_hp == 20
        assert player.max_hp == 20
        assert player.armor_class == 16
        assert player.is_alive is True

    def test_creates_enemy_combatant(self) -> None:
        """Should create an enemy combatant with valid attributes."""
        enemy = Combatant(
            id="enemy_1",
            name="Goblin",
            type=CombatantType.ENEMY,
            initiative=12,
            current_hp=7,
            max_hp=7,
            armor_class=13,
        )

        assert enemy.id == "enemy_1"
        assert enemy.name == "Goblin"
        assert enemy.type == CombatantType.ENEMY
        assert enemy.initiative == 12
        assert enemy.current_hp == 7
        assert enemy.max_hp == 7
        assert enemy.armor_class == 13
        assert enemy.is_alive is True

    def test_default_initiative_is_zero(self) -> None:
        """Initiative should default to 0 if not specified."""
        combatant = Combatant(
            id="test_1",
            name="Test",
            type=CombatantType.PLAYER,
            current_hp=10,
            max_hp=10,
            armor_class=15,
        )

        assert combatant.initiative == 0

    def test_default_is_alive_is_true(self) -> None:
        """is_alive should default to True."""
        combatant = Combatant(
            id="test_1",
            name="Test",
            type=CombatantType.PLAYER,
            current_hp=10,
            max_hp=10,
            armor_class=15,
        )

        assert combatant.is_alive is True

    def test_can_set_is_alive_to_false(self) -> None:
        """Should be able to set is_alive to False."""
        combatant = Combatant(
            id="test_1",
            name="Test",
            type=CombatantType.PLAYER,
            current_hp=0,
            max_hp=10,
            armor_class=15,
            is_alive=False,
        )

        assert combatant.is_alive is False

    def test_serializes_to_dict_and_back(self) -> None:
        """Combatant should serialize and deserialize correctly."""
        original = Combatant(
            id="player_1",
            name="Elara",
            type=CombatantType.PLAYER,
            initiative=18,
            current_hp=15,
            max_hp=20,
            armor_class=14,
            is_alive=True,
        )

        # Serialize to dict
        combatant_dict = original.model_dump()

        # Deserialize back
        restored = Combatant(**combatant_dict)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.initiative == original.initiative
        assert restored.current_hp == original.current_hp
        assert restored.max_hp == original.max_hp
        assert restored.armor_class == original.armor_class
        assert restored.is_alive == original.is_alive


class TestEnemy:
    """Test suite for Enemy template model."""

    def test_creates_enemy_template(self) -> None:
        """Should create an enemy template with all attributes."""
        enemy = Enemy(
            name="Goblin Raider",
            description="A small, green-skinned creature",
            max_hp=7,
            armor_class=13,
            attack_bonus=4,
            damage_dice="1d6+2",
        )

        assert enemy.name == "Goblin Raider"
        assert enemy.description == "A small, green-skinned creature"
        assert enemy.max_hp == 7
        assert enemy.armor_class == 13
        assert enemy.attack_bonus == 4
        assert enemy.damage_dice == "1d6+2"

    def test_serializes_to_dict_and_back(self) -> None:
        """Enemy should serialize and deserialize correctly."""
        original = Enemy(
            name="Skeleton Warrior",
            description="An undead warrior",
            max_hp=13,
            armor_class=13,
            attack_bonus=4,
            damage_dice="1d6+2",
        )

        # Serialize to dict
        enemy_dict = original.model_dump()

        # Deserialize back
        restored = Enemy(**enemy_dict)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.max_hp == original.max_hp
        assert restored.armor_class == original.armor_class
        assert restored.attack_bonus == original.attack_bonus
        assert restored.damage_dice == original.damage_dice


class TestCombatState:
    """Test suite for CombatState model."""

    def test_initializes_with_defaults(self) -> None:
        """CombatState should initialize with sensible defaults."""
        state = CombatState()

        assert state.is_active is False
        assert state.phase == CombatPhaseEnum.INITIATIVE
        assert state.round_number == 0
        assert state.combatants == []
        assert state.turn_order == []
        assert state.current_turn_index == 0
        assert state.enemy_template is None
        assert state.combat_log == []

    def test_creates_with_custom_values(self) -> None:
        """CombatState should accept custom initialization values."""
        player = Combatant(
            id="player_1",
            name="Thorin",
            type=CombatantType.PLAYER,
            current_hp=20,
            max_hp=20,
            armor_class=16,
        )
        enemy = Combatant(
            id="enemy_1",
            name="Goblin",
            type=CombatantType.ENEMY,
            current_hp=7,
            max_hp=7,
            armor_class=13,
        )

        state = CombatState(
            is_active=True,
            phase=CombatPhaseEnum.PLAYER_TURN,
            round_number=1,
            combatants=[player, enemy],
            turn_order=["player_1", "enemy_1"],
            current_turn_index=0,
        )

        assert state.is_active is True
        assert state.phase == CombatPhaseEnum.PLAYER_TURN
        assert state.round_number == 1
        assert len(state.combatants) == 2
        assert state.turn_order == ["player_1", "enemy_1"]
        assert state.current_turn_index == 0

    def test_add_combatants(self) -> None:
        """Should be able to add combatants to combat state."""
        state = CombatState()

        player = Combatant(
            id="player_1",
            name="Elara",
            type=CombatantType.PLAYER,
            current_hp=18,
            max_hp=18,
            armor_class=15,
        )
        enemy = Combatant(
            id="enemy_1",
            name="Bandit",
            type=CombatantType.ENEMY,
            current_hp=11,
            max_hp=11,
            armor_class=12,
        )

        state.combatants.append(player)
        state.combatants.append(enemy)

        assert len(state.combatants) == 2
        assert state.combatants[0].name == "Elara"
        assert state.combatants[1].name == "Bandit"

    def test_stores_enemy_template(self) -> None:
        """Should be able to store enemy template."""
        enemy_template = Enemy(
            name="Goblin Raider",
            description="A small goblin",
            max_hp=7,
            armor_class=13,
            attack_bonus=4,
            damage_dice="1d6+2",
        )

        state = CombatState(enemy_template=enemy_template)

        assert state.enemy_template is not None
        assert state.enemy_template.name == "Goblin Raider"
        assert state.enemy_template.max_hp == 7

    def test_combat_log_functionality(self) -> None:
        """Should be able to add messages to combat log."""
        state = CombatState()

        state.combat_log.append("Combat begins!")
        state.combat_log.append("Player attacks goblin")
        state.combat_log.append("Goblin takes 5 damage")

        assert len(state.combat_log) == 3
        assert state.combat_log[0] == "Combat begins!"
        assert state.combat_log[2] == "Goblin takes 5 damage"

    def test_serializes_to_dict_and_back(self) -> None:
        """CombatState should serialize and deserialize correctly."""
        player = Combatant(
            id="player_1",
            name="Thorin",
            type=CombatantType.PLAYER,
            initiative=15,
            current_hp=20,
            max_hp=20,
            armor_class=16,
        )
        enemy_template = Enemy(
            name="Goblin",
            description="A goblin",
            max_hp=7,
            armor_class=13,
            attack_bonus=4,
            damage_dice="1d6+2",
        )

        original = CombatState(
            is_active=True,
            phase=CombatPhaseEnum.PLAYER_TURN,
            round_number=2,
            combatants=[player],
            turn_order=["player_1"],
            current_turn_index=0,
            enemy_template=enemy_template,
            combat_log=["Combat started", "Player rolled initiative: 15"],
        )

        # Serialize to dict
        state_dict = original.model_dump()

        # Deserialize back
        restored = CombatState(**state_dict)

        assert restored.is_active == original.is_active
        assert restored.phase == original.phase
        assert restored.round_number == original.round_number
        assert len(restored.combatants) == 1
        assert restored.combatants[0].name == "Thorin"
        assert restored.turn_order == original.turn_order
        assert restored.current_turn_index == original.current_turn_index
        assert restored.enemy_template is not None
        assert restored.enemy_template.name == "Goblin"
        assert len(restored.combat_log) == 2

    def test_serializes_to_json_and_back(self) -> None:
        """CombatState should serialize to JSON and deserialize correctly."""
        original = CombatState(
            is_active=True,
            phase=CombatPhaseEnum.INITIATIVE,
            round_number=1,
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize from JSON
        restored = CombatState.model_validate_json(json_str)

        assert restored.is_active == original.is_active
        assert restored.phase == original.phase
        assert restored.round_number == original.round_number


class TestEnemyTemplates:
    """Test suite for enemy templates database."""

    def test_enemy_templates_exist(self) -> None:
        """ENEMY_TEMPLATES should be importable and non-empty."""
        assert ENEMY_TEMPLATES is not None
        assert isinstance(ENEMY_TEMPLATES, dict)
        assert len(ENEMY_TEMPLATES) > 0

    def test_goblin_template_exists(self) -> None:
        """Goblin template should exist with correct attributes."""
        assert "goblin" in ENEMY_TEMPLATES
        goblin = ENEMY_TEMPLATES["goblin"]

        assert isinstance(goblin, Enemy)
        assert goblin.name == "Goblin Raider"
        assert (
            "goblin" in goblin.description.lower()
            or "green" in goblin.description.lower()
        )
        assert goblin.max_hp == 7
        assert goblin.armor_class == 13
        assert goblin.attack_bonus == 4
        assert goblin.damage_dice == "1d6+2"

    def test_bandit_template_exists(self) -> None:
        """Bandit template should exist."""
        assert "bandit" in ENEMY_TEMPLATES
        bandit = ENEMY_TEMPLATES["bandit"]

        assert isinstance(bandit, Enemy)
        assert "bandit" in bandit.name.lower()
        assert bandit.max_hp > 0
        assert bandit.armor_class > 0
        assert bandit.attack_bonus >= 0

    def test_skeleton_template_exists(self) -> None:
        """Skeleton template should exist."""
        assert "skeleton" in ENEMY_TEMPLATES
        skeleton = ENEMY_TEMPLATES["skeleton"]

        assert isinstance(skeleton, Enemy)
        assert "skeleton" in skeleton.name.lower()
        assert skeleton.max_hp > 0
        assert skeleton.armor_class > 0
        assert skeleton.attack_bonus >= 0

    def test_all_templates_are_valid_enemies(self) -> None:
        """All enemy templates should be valid Enemy instances."""
        for key, enemy in ENEMY_TEMPLATES.items():
            assert isinstance(enemy, Enemy)
            assert isinstance(key, str)
            assert len(enemy.name) > 0
            assert len(enemy.description) > 0
            assert enemy.max_hp > 0
            assert enemy.armor_class > 0
            assert enemy.attack_bonus >= 0
            assert len(enemy.damage_dice) > 0

    def test_enemy_templates_can_create_combatants(self) -> None:
        """Enemy templates should be usable to create Combatants."""
        goblin_template = ENEMY_TEMPLATES["goblin"]

        combatant = Combatant(
            id="enemy_1",
            name=goblin_template.name,
            type=CombatantType.ENEMY,
            current_hp=goblin_template.max_hp,
            max_hp=goblin_template.max_hp,
            armor_class=goblin_template.armor_class,
        )

        assert combatant.name == "Goblin Raider"
        assert combatant.current_hp == 7
        assert combatant.max_hp == 7
        assert combatant.armor_class == 13
        assert combatant.type == CombatantType.ENEMY
