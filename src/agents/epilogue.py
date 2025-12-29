"""Epilogue agent - generates personalized adventure conclusions."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings
from src.state.models import GameState


class EpilogueAgent:
    """Agent that generates personalized adventure epilogues.

    This agent creates memorable conclusions that honor the player's
    unique journey through the adventure, referencing specific moments
    and providing satisfying narrative closure.
    """

    def __init__(self) -> None:
        """Initialize the epilogue agent from YAML config."""
        config = load_agent_config("epilogue")

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

    def generate_epilogue(
        self,
        state: GameState,
        reason: str,
        context: str = "",
    ) -> str:
        """Generate personalized epilogue based on adventure journey.

        Args:
            state: Current game state with adventure history
            reason: Closure reason ("quest_complete" or "hard_cap")
            context: Optional additional context for the epilogue

        Returns:
            Personalized epilogue narrative (150-200 words)
        """
        task_config = load_task_config("generate_epilogue")

        # Build character summary
        character_summary = self._build_character_summary(state)

        # Format adventure moments
        adventure_moments = self._format_adventure_moments(state)

        # Get character name
        character_name = "Adventurer"
        if state.character_sheet:
            character_name = state.character_sheet.name

        # Format task description
        description = task_config.description.format(
            character_name=character_name,
            reason=reason,
            turn_count=state.adventure_turn,
            adventure_moments=adventure_moments,
            character_summary=character_summary,
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

    def _build_character_summary(self, state: GameState) -> str:
        """Build a summary of the character for epilogue context.

        Args:
            state: Game state with character information

        Returns:
            Formatted character summary string
        """
        if not state.character_sheet:
            return "A brave adventurer whose story is now complete."

        sheet = state.character_sheet
        lines = [
            f"Name: {sheet.name}",
            f"Race: {sheet.race.value}",
            f"Class: {sheet.character_class.value}",
        ]

        if hasattr(sheet, "backstory") and sheet.backstory:
            lines.append(f"Backstory: {sheet.backstory}")

        # Include quest info if available
        if state.active_quest:
            quest = state.active_quest
            lines.append(f"Quest: {quest.title}")
            completed_objectives = sum(
                1 for obj in quest.objectives if obj.is_completed
            )
            total_objectives = len(quest.objectives)
            lines.append(
                f"Objectives completed: {completed_objectives}/{total_objectives}"
            )

        return "\n".join(lines)

    def _format_adventure_moments(self, state: GameState) -> str:
        """Format significant adventure moments for epilogue generation.

        Selects the most significant moments (up to 5) to include
        in the epilogue context.

        Args:
            state: Game state with adventure moments

        Returns:
            Formatted string of key adventure moments
        """
        if not state.adventure_moments:
            # Fallback to conversation history highlights
            return self._extract_moments_from_history(state)

        # Sort by significance and select top moments
        sorted_moments = sorted(
            state.adventure_moments,
            key=lambda m: m.significance,
            reverse=True,
        )
        top_moments = sorted_moments[:5]

        # Format moments for the agent
        lines = []
        for moment in top_moments:
            lines.append(f"- Turn {moment.turn} ({moment.type}): {moment.summary}")

        return "\n".join(lines) if lines else "The adventure was filled with discovery."

    def _extract_moments_from_history(self, state: GameState) -> str:
        """Extract key moments from conversation history as fallback.

        Args:
            state: Game state with conversation history

        Returns:
            Formatted string of inferred moments
        """
        if not state.conversation_history:
            return "A journey of discovery and courage."

        # Sample from early, middle, and late adventure
        history = state.conversation_history
        moments = []

        # Get samples from different parts of the adventure
        if len(history) >= 1:
            # Early moment
            early = history[0]
            if early.get("narrative"):
                moments.append(f"- Beginning: {early['narrative'][:100]}...")

        if len(history) >= 3:
            # Middle moment
            mid_idx = len(history) // 2
            mid = history[mid_idx]
            if mid.get("narrative"):
                moments.append(f"- Journey: {mid['narrative'][:100]}...")

        if len(history) >= 2:
            # Recent moment
            recent = history[-1]
            if recent.get("narrative"):
                moments.append(f"- Recent: {recent['narrative'][:100]}...")

        return "\n".join(moments) if moments else "A tale worth remembering."


def generate_fallback_epilogue(reason: str, state: GameState) -> str:
    """Generate a static fallback epilogue when the agent is unavailable.

    Args:
        reason: Closure reason ("quest_complete" or "hard_cap")
        state: Current game state

    Returns:
        Static epilogue text appropriate for the closure reason
    """
    character_name = "Adventurer"
    if state.character_sheet:
        character_name = state.character_sheet.name

    if reason == "quest_complete":
        return (
            f"With the quest complete, {character_name}'s adventure draws to a "
            f"satisfying close. The tales of their deeds will be sung for "
            f"generations to come. Though new horizons beckon, this chapter "
            f"ends in triumph."
        )
    else:  # hard_cap
        return (
            f"As the sun sets on this chapter of {character_name}'s journey, "
            f"they reflect on all that has transpired. Though there is always "
            f"more to discover, this adventure has reached its natural conclusion. "
            f"The road continues, but this tale is told."
        )
