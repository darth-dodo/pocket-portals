"""Keeper agent - handles game mechanics without slowing the story."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.engine.combat_manager import CombatManager
from src.settings import settings
from src.state.character import CharacterSheet
from src.state.models import Combatant, CombatState


class KeeperAgent:
    """Keeper agent that handles game mechanics with terse, numbers-first language."""

    def __init__(self) -> None:
        """Initialize the Keeper agent from YAML config."""
        config = load_agent_config("keeper")

        # CrewAI's native LLM class - config-driven
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

        # Combat manager for mechanical resolution
        self.combat_manager = CombatManager()

    def respond(self, action: str, context: str = "") -> str:
        """Generate keeper response to player action.

        Provides the standard interface expected by the conversation flow.

        Args:
            action: The player's action
            context: Optional conversation history

        Returns:
            Mechanical resolution of the action
        """
        return self.resolve_action(action=action, context=context)

    def resolve_action(
        self, action: str, context: str = "", difficulty: int = 12
    ) -> str:
        """Resolve a game action mechanically.

        Args:
            action: The action being attempted
            context: Optional context from previous conversation
            difficulty: Target number to succeed (default 12)

        Returns:
            Brief mechanical resolution
        """
        task_config = load_task_config("resolve_action")

        description = task_config.description.format(
            action=action,
            difficulty=difficulty,
        )

        if context:
            description = f"{context}\n\n{description}"

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)

    def format_initiative_result(self, results: list[dict]) -> str:
        """Format initiative results for display.

        Creates a narrative description of initiative rolls showing each combatant's
        roll, modifier, total, and who goes first.

        Args:
            results: List of initiative result dicts with keys:
                - id: combatant identifier
                - roll: raw d20 roll
                - modifier: DEX modifier
                - total: roll + modifier

        Returns:
            Formatted string describing initiative results

        Examples:
            >>> keeper = KeeperAgent()
            >>> results = [
            ...     {"id": "player", "roll": 15, "modifier": 2, "total": 17},
            ...     {"id": "enemy", "roll": 10, "modifier": 1, "total": 11}
            ... ]
            >>> keeper.format_initiative_result(results)
            'Initiative! Player: 1d20+2 = 17 (rolled 15). Enemy: 1d20+1 = 11 (rolled 10). Player goes first!'
        """
        if not results:
            return "No initiative results to display."

        # Sort by total (descending) to show who goes first
        sorted_results = sorted(results, key=lambda x: x["total"], reverse=True)

        # Build description for each combatant
        parts = []
        for result in sorted_results:
            combatant_name = result["id"].replace("_", " ").title()
            roll = result["roll"]
            modifier = result["modifier"]
            total = result["total"]

            # Format modifier with + or - sign
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)

            parts.append(f"{combatant_name}: 1d20{mod_str} = {total} (rolled {roll})")

        # Determine who goes first
        first_combatant = sorted_results[0]["id"].replace("_", " ").title()

        # Combine into narrative
        initiative_text = ". ".join(parts)
        return f"Initiative! {initiative_text}. {first_combatant} goes first!"

    def start_combat(
        self, character_sheet: CharacterSheet, enemy_type: str
    ) -> tuple[CombatState, list[dict]]:
        """Start a new combat encounter.

        Delegates to CombatManager for mechanical resolution.

        Args:
            character_sheet: Player's character sheet
            enemy_type: Key from ENEMY_TEMPLATES

        Returns:
            (CombatState, initiative_results)

        Raises:
            ValueError: If enemy_type not found in templates

        Examples:
            >>> keeper = KeeperAgent()
            >>> sheet = CharacterSheet(name="Hero", ...)
            >>> combat, results = keeper.start_combat(sheet, "goblin")
            >>> combat.is_active
            True
        """
        return self.combat_manager.start_combat(character_sheet, enemy_type)

    def roll_initiative(
        self, combatants: list[Combatant], dex_modifiers: dict[str, int]
    ) -> list[dict]:
        """Roll initiative for all combatants using DiceRoller.

        Args:
            combatants: List of combatants to roll initiative for
            dex_modifiers: Dict mapping combatant_id to dex modifier

        Returns:
            List of dicts: {"id": str, "roll": int, "modifier": int, "total": int}

        Examples:
            >>> keeper = KeeperAgent()
            >>> combatants = [player, enemy]
            >>> modifiers = {"player": 2, "enemy": 0}
            >>> results = keeper.roll_initiative(combatants, modifiers)
            >>> len(results) == 2
            True
        """
        return self.combat_manager.roll_initiative(combatants, dex_modifiers)

    def get_current_turn_combatant(self, combat_state: CombatState) -> Combatant | None:
        """Get the combatant whose turn it is.

        Args:
            combat_state: Current combat state

        Returns:
            Combatant whose turn it is, or None if combat state is empty

        Examples:
            >>> keeper = KeeperAgent()
            >>> current = keeper.get_current_turn_combatant(combat_state)
            >>> current.id == combat_state.turn_order[0]
            True
        """
        return self.combat_manager.get_current_turn_combatant(combat_state)

    def resolve_player_attack(
        self, combat_state: CombatState, character_sheet: CharacterSheet
    ) -> dict:
        """Resolve player's attack action.

        Args:
            combat_state: Current combat state
            character_sheet: Player's character sheet

        Returns:
            Attack result dict from CombatManager

        Examples:
            >>> keeper = KeeperAgent()
            >>> result = keeper.resolve_player_attack(combat_state, fighter_sheet)
            >>> "hit" in result
            True
        """
        return self.combat_manager.execute_player_attack(combat_state, character_sheet)

    def resolve_enemy_attack(self, combat_state: CombatState) -> dict:
        """Resolve enemy's attack action.

        Args:
            combat_state: Current combat state

        Returns:
            Attack result dict from CombatManager

        Examples:
            >>> keeper = KeeperAgent()
            >>> result = keeper.resolve_enemy_attack(combat_state)
            >>> "hit" in result
            True
        """
        return self.combat_manager.execute_enemy_turn(combat_state)
