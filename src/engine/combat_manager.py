"""Combat manager for Pocket Portals combat system."""

from src.data.enemies import ENEMY_TEMPLATES
from src.state.character import CharacterSheet
from src.state.models import (
    Combatant,
    CombatantType,
    CombatPhaseEnum,
    CombatState,
)
from src.utils.dice import DiceRoll, DiceRoller

# Weapon damage by class
WEAPON_DAMAGE: dict[str, tuple[str, str]] = {
    # class: (damage_dice, stat_for_modifier)
    "Fighter": ("1d8", "strength"),
    "Wizard": ("1d6", "strength"),
    "Rogue": ("1d4", "dexterity"),
    "Cleric": ("1d6", "strength"),
    "Ranger": ("1d8", "dexterity"),
    "Bard": ("1d8", "dexterity"),
}


class CombatManager:
    """Manages combat encounters and state transitions.

    This service orchestrates combat encounters by:
    - Creating combat state from character sheets and enemy templates
    - Rolling initiative for all combatants
    - Sorting and tracking turn order
    - Managing combat phases
    """

    def start_combat(
        self, character_sheet: CharacterSheet, enemy_type: str
    ) -> tuple[CombatState, list[dict]]:
        """Start a new combat encounter.

        Args:
            character_sheet: Player's character sheet
            enemy_type: Key from ENEMY_TEMPLATES (e.g., "goblin", "bandit")

        Returns:
            Tuple of (CombatState, initiative_results)
            - CombatState: Active combat state with combatants and turn order
            - initiative_results: List of dicts with initiative roll details

        Raises:
            ValueError: If enemy_type is not found in ENEMY_TEMPLATES

        Examples:
            >>> manager = CombatManager()
            >>> sheet = CharacterSheet(name="Hero", ...)
            >>> combat, results = manager.start_combat(sheet, "goblin")
            >>> combat.is_active
            True
            >>> len(combat.combatants)
            2
        """
        # 1. Get enemy template
        if enemy_type not in ENEMY_TEMPLATES:
            raise ValueError(
                f"Unknown enemy type: {enemy_type}. "
                f"Available types: {', '.join(ENEMY_TEMPLATES.keys())}"
            )

        enemy_template = ENEMY_TEMPLATES[enemy_type]

        # 2. Create player combatant from character_sheet
        player = Combatant(
            id="player",
            name=character_sheet.name,
            type=CombatantType.PLAYER,
            current_hp=character_sheet.current_hp,
            max_hp=character_sheet.max_hp,
            # In D&D 5e, AC = 10 + DEX modifier + armor (simplified to 10 + DEX mod)
            armor_class=10 + character_sheet.stats.modifier("dexterity"),
            is_alive=True,
        )

        # 3. Create enemy combatant from template
        enemy = Combatant(
            id="enemy",
            name=enemy_template.name,
            type=CombatantType.ENEMY,
            current_hp=enemy_template.max_hp,
            max_hp=enemy_template.max_hp,
            armor_class=enemy_template.armor_class,
            is_alive=True,
        )

        combatants = [player, enemy]

        # 4. Roll initiative for both
        # In D&D 5e, initiative = 1d20 + DEX modifier
        dex_modifiers = {
            "player": character_sheet.stats.modifier("dexterity"),
            "enemy": 0,  # Most basic enemies have 0 modifier
        }

        initiative_results = self.roll_initiative(combatants, dex_modifiers)

        # 5. Sort and set turn order (highest initiative first)
        sorted_results = sorted(
            initiative_results, key=lambda x: x["total"], reverse=True
        )
        turn_order = [result["id"] for result in sorted_results]

        # Update combatant initiative values
        for result in initiative_results:
            combatant = next(c for c in combatants if c.id == result["id"])
            combatant.initiative = result["total"]

        # 6. Determine starting phase based on who goes first
        first_combatant = next(c for c in combatants if c.id == turn_order[0])
        if first_combatant.type == CombatantType.PLAYER:
            phase = CombatPhaseEnum.PLAYER_TURN
        else:
            phase = CombatPhaseEnum.ENEMY_TURN

        # 7. Create and return combat state
        combat_state = CombatState(
            is_active=True,
            phase=phase,
            round_number=1,
            combatants=combatants,
            turn_order=turn_order,
            current_turn_index=0,
            enemy_template=enemy_template,
            combat_log=[],
        )

        return combat_state, initiative_results

    def roll_initiative(
        self, combatants: list[Combatant], dex_modifiers: dict[str, int]
    ) -> list[dict]:
        """Roll initiative for all combatants.

        Initiative is rolled as 1d20 + DEX modifier for each combatant.

        Args:
            combatants: List of combatants to roll initiative for
            dex_modifiers: Dict mapping combatant_id to DEX modifier

        Returns:
            List of dicts with format:
            {
                "id": str,
                "roll": int (the raw d20 roll),
                "modifier": int (DEX modifier),
                "total": int (roll + modifier)
            }

        Examples:
            >>> manager = CombatManager()
            >>> combatants = [player, enemy]
            >>> modifiers = {"player": 2, "enemy": 0}
            >>> results = manager.roll_initiative(combatants, modifiers)
            >>> len(results) == 2
            True
            >>> all("total" in r for r in results)
            True
        """
        results = []

        for combatant in combatants:
            modifier = dex_modifiers.get(combatant.id, 0)

            # Roll 1d20 for initiative
            dice_roll = DiceRoller.roll(f"1d20+{modifier}")

            results.append(
                {
                    "id": combatant.id,
                    "roll": dice_roll.rolls[0],  # The raw d20 roll
                    "modifier": modifier,
                    "total": dice_roll.total,
                }
            )

        return results

    def get_current_turn_combatant(self, combat_state: CombatState) -> Combatant | None:
        """Get the combatant whose turn it is.

        Args:
            combat_state: Current combat state

        Returns:
            Combatant whose turn it is, or None if combat state is empty

        Examples:
            >>> manager = CombatManager()
            >>> current = manager.get_current_turn_combatant(combat_state)
            >>> current.id == combat_state.turn_order[0]
            True
        """
        if not combat_state.turn_order or not combat_state.combatants:
            return None

        current_id = combat_state.turn_order[combat_state.current_turn_index]
        return next((c for c in combat_state.combatants if c.id == current_id), None)

    def resolve_attack(
        self,
        attacker: Combatant,
        defender: Combatant,
        attack_bonus: int,
        damage_dice: str,
        combat_state: CombatState,
        has_advantage: bool = False,
        has_disadvantage: bool = False,
    ) -> dict:
        """Resolve an attack action using DiceRoller.

        Args:
            attacker: The combatant making the attack
            defender: The combatant being attacked
            attack_bonus: Bonus to add to attack roll
            damage_dice: Dice notation for damage (e.g., "1d8+3")
            combat_state: Current combat state (for logging)
            has_advantage: Whether to roll with advantage (2d20, take higher)
            has_disadvantage: Whether to roll with disadvantage (2d20, take lower)

        Returns:
            Dict with keys:
                - hit: bool - Whether the attack hit
                - attack_roll: DiceRoll - The attack roll result
                - total_attack: int - Attack roll total + bonus
                - target_ac: int - Defender's armor class
                - damage_roll: DiceRoll | None - Damage roll if hit, None if miss
                - damage_dealt: int - Actual damage dealt
                - defender_hp: int - Defender's HP after damage
                - defender_alive: bool - Whether defender is still alive
                - log_entry: str - Human-readable summary

        Examples:
            >>> manager = CombatManager()
            >>> result = manager.resolve_attack(player, enemy, 3, "1d8+2", combat_state)
            >>> result["hit"]  # True or False based on roll
            >>> result["damage_dealt"] >= 0
            True
        """
        # 1. Roll 1d20 for attack (with advantage/disadvantage if applicable)
        if has_advantage:
            attack_roll = DiceRoller.roll_with_advantage()
        elif has_disadvantage:
            attack_roll = DiceRoller.roll_with_disadvantage()
        else:
            attack_roll = DiceRoller.roll("1d20")

        # 2. Add attack_bonus to roll
        total_attack = attack_roll.total + attack_bonus

        # 3. Compare to defender.armor_class
        hit = total_attack >= defender.armor_class

        # 4. Initialize damage variables
        damage_roll: DiceRoll | None = None
        damage_dealt = 0

        # 5. If hit, roll damage and apply it
        if hit:
            damage_roll = DiceRoller.roll(damage_dice)
            damage_dealt = damage_roll.total

            # Apply damage (floor at 0)
            defender.current_hp = max(0, defender.current_hp - damage_dealt)

            # 6. Check if defender is dead
            if defender.current_hp <= 0:
                defender.is_alive = False

        # 7. Create log entry
        advantage_text = ""
        if has_advantage:
            advantage_text = " (advantage)"
        elif has_disadvantage:
            advantage_text = " (disadvantage)"

        if hit:
            if has_advantage or has_disadvantage:
                # Show both dice rolls for advantage/disadvantage
                roll_text = f"{attack_roll.rolls[0]}/{attack_roll.rolls[1]}"
                log_entry = (
                    f"Round {combat_state.round_number}: {attacker.name} attacks {defender.name}{advantage_text}. "
                    f"1d20={roll_text}, takes {attack_roll.total}. {attack_roll.total}+{attack_bonus}={total_attack} "
                    f"vs AC {defender.armor_class}. Hit! "
                    f"{damage_dice}={damage_dealt} damage. "
                    f"{defender.name} HP: {defender.current_hp}/{defender.max_hp}"
                )
            else:
                log_entry = (
                    f"Round {combat_state.round_number}: {attacker.name} attacks {defender.name}. "
                    f"1d20+{attack_bonus}={total_attack} vs AC {defender.armor_class}. Hit! "
                    f"{damage_dice}={damage_dealt} damage. "
                    f"{defender.name} HP: {defender.current_hp}/{defender.max_hp}"
                )
        else:
            if has_advantage or has_disadvantage:
                roll_text = f"{attack_roll.rolls[0]}/{attack_roll.rolls[1]}"
                log_entry = (
                    f"Round {combat_state.round_number}: {attacker.name} attacks {defender.name}{advantage_text}. "
                    f"1d20={roll_text}, takes {attack_roll.total}. {attack_roll.total}+{attack_bonus}={total_attack} "
                    f"vs AC {defender.armor_class}. Miss!"
                )
            else:
                log_entry = (
                    f"Round {combat_state.round_number}: {attacker.name} attacks {defender.name}. "
                    f"1d20+{attack_bonus}={total_attack} vs AC {defender.armor_class}. Miss!"
                )

        # 8. Add to combat log
        combat_state.combat_log.append(log_entry)

        # 9. Return result dict
        return {
            "hit": hit,
            "attack_roll": attack_roll,
            "total_attack": total_attack,
            "target_ac": defender.armor_class,
            "damage_roll": damage_roll,
            "damage_dealt": damage_dealt,
            "defender_hp": defender.current_hp,
            "defender_alive": defender.is_alive,
            "log_entry": log_entry,
        }

    def execute_player_attack(
        self, combat_state: CombatState, character_sheet: CharacterSheet
    ) -> dict:
        """Execute player's attack on current enemy.

        Uses character class to determine weapon damage.

        Args:
            combat_state: Current combat state
            character_sheet: Player's character sheet

        Returns:
            Attack result dict from resolve_attack()

        Examples:
            >>> manager = CombatManager()
            >>> result = manager.execute_player_attack(combat_state, fighter_sheet)
            >>> "hit" in result
            True
        """
        # Get player and enemy combatants
        player = next(
            (c for c in combat_state.combatants if c.type == CombatantType.PLAYER), None
        )
        enemy = next(
            (c for c in combat_state.combatants if c.type == CombatantType.ENEMY), None
        )

        if not player or not enemy:
            raise ValueError("Missing player or enemy combatant")

        # Look up weapon damage for class
        class_name = character_sheet.character_class.value.title()
        damage_dice_base, stat_name = WEAPON_DAMAGE.get(
            class_name,
            ("1d6", "strength"),  # Default to 1d6 + STR
        )

        # Calculate attack bonus (stat modifier)
        attack_modifier = character_sheet.stats.modifier(stat_name)

        # Build damage dice with modifier
        damage_dice = f"{damage_dice_base}+{attack_modifier}"

        # Call resolve_attack()
        return self.resolve_attack(
            attacker=player,
            defender=enemy,
            attack_bonus=attack_modifier,
            damage_dice=damage_dice,
            combat_state=combat_state,
        )

    def execute_enemy_turn(self, combat_state: CombatState) -> dict:
        """Execute enemy's turn (always attacks for MVP).

        Uses enemy template's attack_bonus and damage_dice.
        If player is defending, rolls with disadvantage.

        Args:
            combat_state: Current combat state

        Returns:
            Attack result dict from resolve_attack()

        Examples:
            >>> manager = CombatManager()
            >>> result = manager.execute_enemy_turn(combat_state)
            >>> "hit" in result
            True
        """
        # Get enemy and player combatants
        enemy = next(
            (c for c in combat_state.combatants if c.type == CombatantType.ENEMY), None
        )
        player = next(
            (c for c in combat_state.combatants if c.type == CombatantType.PLAYER), None
        )

        if not enemy or not player:
            raise ValueError("Missing enemy or player combatant")

        if not combat_state.enemy_template:
            raise ValueError("Missing enemy template")

        # Check if player is defending (for disadvantage)
        has_disadvantage = combat_state.player_defending

        # Use enemy template's attack_bonus and damage_dice
        result = self.resolve_attack(
            attacker=enemy,
            defender=player,
            attack_bonus=combat_state.enemy_template.attack_bonus,
            damage_dice=combat_state.enemy_template.damage_dice,
            combat_state=combat_state,
            has_disadvantage=has_disadvantage,
        )

        # Reset defending flag after attack
        if combat_state.player_defending:
            combat_state.player_defending = False

        return result

    def format_attack_result(self, result: dict) -> str:
        """Format attack result as readable text (no LLM).

        Args:
            result: Attack result dict from resolve_attack()

        Returns:
            Human-readable formatted text

        Examples:
            >>> manager = CombatManager()
            >>> result = {"hit": True, "total_attack": 18, "target_ac": 13, ...}
            >>> formatted = manager.format_attack_result(result)
            >>> "Attack" in formatted
            True
        """
        return result["log_entry"]

    def advance_turn(self, combat_state: CombatState) -> None:
        """Advance to next combatant's turn.

        - Increment current_turn_index
        - Wrap around when reaching end of turn_order
        - Increment round_number when wrapping
        - Update phase to PLAYER_TURN or ENEMY_TURN

        Args:
            combat_state: Current combat state to modify

        Examples:
            >>> manager = CombatManager()
            >>> combat_state.current_turn_index = 0
            >>> manager.advance_turn(combat_state)
            >>> combat_state.current_turn_index
            1
        """
        # Increment turn index
        combat_state.current_turn_index += 1

        # Wrap around and increment round if at end
        if combat_state.current_turn_index >= len(combat_state.turn_order):
            combat_state.current_turn_index = 0
            combat_state.round_number += 1

        # Update phase based on current combatant
        current_id = combat_state.turn_order[combat_state.current_turn_index]
        current_combatant = next(
            c for c in combat_state.combatants if c.id == current_id
        )

        if current_combatant.type == CombatantType.PLAYER:
            combat_state.phase = CombatPhaseEnum.PLAYER_TURN
        else:
            combat_state.phase = CombatPhaseEnum.ENEMY_TURN

    def check_combat_end(self, combat_state: CombatState) -> tuple[bool, str | None]:
        """Check if combat should end.

        Returns:
            (ended: bool, result: "victory" | "defeat" | None)

        Examples:
            >>> manager = CombatManager()
            >>> ended, result = manager.check_combat_end(combat_state)
            >>> if ended:
            ...     print(f"Combat ended: {result}")
        """
        # Check if any combatant is dead
        player = next(
            (c for c in combat_state.combatants if c.type == CombatantType.PLAYER),
            None,
        )
        enemy = next(
            (c for c in combat_state.combatants if c.type == CombatantType.ENEMY),
            None,
        )

        if enemy and not enemy.is_alive:
            return True, "victory"

        if player and not player.is_alive:
            return True, "defeat"

        return False, None

    def end_combat(self, combat_state: CombatState, result: str) -> None:
        """Clean up combat state after resolution.

        - Set is_active = False
        - Set phase = RESOLUTION
        - Add final log entry

        Args:
            combat_state: Combat state to end
            result: "victory" or "defeat"

        Examples:
            >>> manager = CombatManager()
            >>> manager.end_combat(combat_state, "victory")
            >>> combat_state.is_active
            False
        """
        combat_state.is_active = False
        combat_state.phase = CombatPhaseEnum.RESOLUTION

        # Add final log entry
        if result == "victory":
            log_entry = "Combat ended: Victory! The enemy has been defeated."
        else:
            log_entry = "Combat ended: Defeat. You have fallen in battle."

        combat_state.combat_log.append(log_entry)

    def execute_defend(
        self, combat_state: CombatState, character_sheet: CharacterSheet
    ) -> dict:
        """Execute defend action.

        Effect: Enemy's next attack has disadvantage.

        Args:
            combat_state: Current combat state
            character_sheet: Player's character sheet

        Returns:
            {
                "action": "defend",
                "success": True,
                "log_entry": "Hero takes a defensive stance."
            }

        Examples:
            >>> manager = CombatManager()
            >>> result = manager.execute_defend(combat_state, character_sheet)
            >>> result["success"]
            True
        """
        # Set defending flag
        combat_state.player_defending = True

        # Create log entry
        log_entry = (
            f"Round {combat_state.round_number}: {character_sheet.name} "
            f"takes a defensive stance."
        )

        # Add to combat log
        combat_state.combat_log.append(log_entry)

        return {
            "action": "defend",
            "success": True,
            "log_entry": log_entry,
        }

    def execute_flee(
        self, combat_state: CombatState, character_sheet: CharacterSheet
    ) -> dict:
        """Execute flee action.

        Roll: 1d20 + DEX modifier vs DC 12
        Success: Combat ends, player escapes
        Failure: Enemy gets free attack with advantage

        Args:
            combat_state: Current combat state
            character_sheet: Player's character sheet

        Returns:
            {
                "action": "flee",
                "success": bool,
                "roll": DiceRoll,
                "dc": 12,
                "log_entry": str,
                "free_attack": dict | None  # Enemy attack if flee failed
            }

        Examples:
            >>> manager = CombatManager()
            >>> result = manager.execute_flee(combat_state, character_sheet)
            >>> result["dc"] == 12
            True
        """
        # Roll 1d20 + DEX modifier
        dex_modifier = character_sheet.stats.modifier("dexterity")
        flee_roll = DiceRoller.roll(f"1d20+{dex_modifier}")

        dc = 12
        success = flee_roll.total >= dc

        free_attack = None

        if success:
            # Successful flee - end combat
            combat_state.is_active = False

            log_entry = (
                f"Round {combat_state.round_number}: {character_sheet.name} attempts to flee. "
                f"1d20+{dex_modifier}={flee_roll.total} vs DC {dc}. Escaped!"
            )
        else:
            # Failed flee - enemy gets free attack with advantage
            enemy_name = (
                combat_state.enemy_template.name
                if combat_state.enemy_template
                else "Enemy"
            )
            log_entry = (
                f"Round {combat_state.round_number}: {character_sheet.name} attempts to flee. "
                f"1d20+{dex_modifier}={flee_roll.total} vs DC {dc}. Failed! "
                f"{enemy_name} attacks with advantage."
            )

            # Get combatants
            enemy = next(
                (c for c in combat_state.combatants if c.type == CombatantType.ENEMY),
                None,
            )
            player = next(
                (c for c in combat_state.combatants if c.type == CombatantType.PLAYER),
                None,
            )

            if enemy and player and combat_state.enemy_template:
                # Execute free attack with advantage
                free_attack = self.resolve_attack(
                    attacker=enemy,
                    defender=player,
                    attack_bonus=combat_state.enemy_template.attack_bonus,
                    damage_dice=combat_state.enemy_template.damage_dice,
                    combat_state=combat_state,
                    has_advantage=True,
                )

        # Add flee attempt to combat log
        combat_state.combat_log.append(log_entry)

        return {
            "action": "flee",
            "success": success,
            "roll": flee_roll,
            "dc": dc,
            "log_entry": log_entry,
            "free_attack": free_attack,
        }
