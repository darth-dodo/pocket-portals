"""Quest Designer agent for generating contextual quests."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings
from src.state.character import CharacterSheet
from src.state.models import Quest, QuestObjective, QuestStatus

logger = logging.getLogger(__name__)


class QuestDesignerAgent:
    """Agent that generates contextual quests for characters."""

    def __init__(self) -> None:
        """Initialize the Quest Designer agent from YAML config."""
        config = load_agent_config("quest_designer")

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
            memory=config.memory,
        )

    def generate_quest(
        self,
        character_sheet: CharacterSheet,
        quest_history: str = "",
        game_context: str = "",
    ) -> Quest:
        """Generate a contextual quest based on character and game state.

        Args:
            character_sheet: Character information for context
            quest_history: Summary of previously completed quests
            game_context: Current game state and location information

        Returns:
            Quest instance with objectives and rewards

        Raises:
            ValueError: If quest generation fails or returns invalid data
        """
        # Build character context
        character_info = self._build_character_context(character_sheet)

        # Create task with formatted inputs
        task_config = load_task_config("generate_quest")
        task_description = task_config.description.format(
            character_info=character_info,
            quest_history=quest_history or "No previous quests completed.",
            game_context=game_context
            or "Character has just finished creation and is at the Rusty Tankard tavern.",
        )

        task = Task(
            description=task_description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        try:
            # Execute task synchronously
            result = task.execute_sync()

            # Parse result as JSON
            quest_data = self._parse_quest_result(result)

            # Convert to Quest model
            return self._create_quest_from_data(quest_data)

        except Exception as e:
            logger.error(f"Failed to generate quest: {e}", exc_info=True)
            # Return fallback quest
            return self._create_fallback_quest(character_sheet)

    def check_quest_progress(
        self, active_quest: Quest, action: str, narrative: str
    ) -> dict[str, Any]:
        """Check if player action completed any quest objectives.

        Args:
            active_quest: The currently active quest
            action: Player's action text
            narrative: Narrative response from the game

        Returns:
            Dictionary with:
                - objectives_completed: List of objective IDs completed
                - quest_completed: Boolean indicating if quest is now complete
                - completion_narrative: Optional narrative for completion
        """
        if not active_quest or active_quest.status != QuestStatus.ACTIVE:
            return {
                "objectives_completed": [],
                "quest_completed": False,
                "completion_narrative": None,
            }

        objectives_completed = []

        # Check each objective
        for objective in active_quest.objectives:
            if objective.is_completed:
                continue

            # Simple keyword matching for objective completion
            # More sophisticated LLM-based checking could be added here
            if self._matches_objective(objective, action, narrative):
                objective.is_completed = True
                objectives_completed.append(objective.id)
                logger.info(
                    f"Objective completed: {objective.description} (Quest: {active_quest.title})"
                )

        # Check if quest is now complete
        quest_completed = active_quest.is_complete
        completion_narrative = None

        if quest_completed:
            active_quest.status = QuestStatus.COMPLETED
            completion_narrative = self._generate_completion_narrative(active_quest)
            logger.info(f"Quest completed: {active_quest.title}")

        return {
            "objectives_completed": objectives_completed,
            "quest_completed": quest_completed,
            "completion_narrative": completion_narrative,
        }

    def _build_character_context(self, character_sheet: CharacterSheet) -> str:
        """Build character context string for quest generation.

        Args:
            character_sheet: Character information

        Returns:
            Formatted character context string
        """
        context = f"""Character: {character_sheet.name}
Race: {character_sheet.race.value}
Class: {character_sheet.character_class.value}
Level: {character_sheet.level}
"""
        if character_sheet.backstory:
            context += f"Backstory: {character_sheet.backstory}\n"

        return context

    def _parse_quest_result(self, result: str) -> dict[str, Any]:
        """Parse quest result from agent output.

        Args:
            result: Raw result string from agent

        Returns:
            Parsed quest data dictionary

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Try to extract JSON from result
            # Agent might wrap JSON in markdown code blocks
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]

            return json.loads(result.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quest JSON: {e}")
            logger.debug(f"Raw result: {result}")
            raise ValueError(f"Invalid quest JSON: {e}") from e

    def _create_quest_from_data(self, quest_data: dict[str, Any]) -> Quest:
        """Create Quest model from parsed data.

        Args:
            quest_data: Parsed quest data dictionary

        Returns:
            Quest model instance

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ["title", "description", "objectives"]
        missing = [f for f in required_fields if f not in quest_data]
        if missing:
            raise ValueError(f"Missing required quest fields: {missing}")

        # Create quest ID if not provided
        quest_id = quest_data.get("id", str(uuid.uuid4()))

        # Parse objectives
        objectives = []
        for obj_data in quest_data["objectives"]:
            obj_id = obj_data.get("id", str(uuid.uuid4()))
            objectives.append(
                QuestObjective(
                    id=obj_id,
                    description=obj_data["description"],
                    is_completed=obj_data.get("is_completed", False),
                    target_count=obj_data.get("target_count"),
                    current_count=obj_data.get("current_count", 0),
                )
            )

        return Quest(
            id=quest_id,
            title=quest_data["title"],
            description=quest_data["description"],
            objectives=objectives,
            rewards=quest_data.get("rewards"),
            status=QuestStatus(quest_data.get("status", "active")),
            given_by=quest_data.get("given_by", "Innkeeper Theron"),
            location_hint=quest_data.get("location_hint"),
        )

    def _create_fallback_quest(self, character_sheet: CharacterSheet) -> Quest:
        """Create a fallback quest when generation fails.

        Args:
            character_sheet: Character information for context

        Returns:
            Simple fallback quest
        """
        quest_id = str(uuid.uuid4())
        objective_id = str(uuid.uuid4())

        return Quest(
            id=quest_id,
            title="The Missing Shipment",
            description="Innkeeper Theron asks you to investigate bandits who attacked a merchant caravan on the road nearby.",
            objectives=[
                QuestObjective(
                    id=objective_id,
                    description="Find the bandit camp and recover the stolen goods",
                    is_completed=False,
                )
            ],
            rewards="50 gold pieces and the gratitude of local merchants",
            status=QuestStatus.ACTIVE,
            given_by="Innkeeper Theron",
            location_hint="The old forest road, about an hour's walk north of town",
        )

    def _matches_objective(
        self, objective: QuestObjective, action: str, narrative: str
    ) -> bool:
        """Check if action and narrative indicate objective completion.

        This is a simple keyword-based matcher. Could be enhanced with LLM analysis.

        Args:
            objective: Objective to check
            action: Player's action text
            narrative: Game narrative response

        Returns:
            True if objective appears to be completed
        """
        # Extract key terms from objective description
        objective_lower = objective.description.lower()
        action_lower = action.lower()
        narrative_lower = narrative.lower()

        # Keywords that indicate completion
        completion_keywords = [
            "found",
            "defeated",
            "recovered",
            "delivered",
            "completed",
            "finished",
            "solved",
            "rescued",
            "killed",
            "destroyed",
        ]

        # Check if action or narrative contains objective keywords and completion indicators
        has_completion_indicator = any(
            keyword in narrative_lower for keyword in completion_keywords
        )

        # Extract potential target nouns from objective
        # Simple approach: look for key nouns in the objective
        objective_nouns = [
            word
            for word in objective_lower.split()
            if len(word) > 4 and word not in ["find", "defeat", "recover", "deliver"]
        ]

        has_objective_match = any(
            noun in action_lower or noun in narrative_lower for noun in objective_nouns
        )

        return has_completion_indicator and has_objective_match

    def _generate_completion_narrative(self, quest: Quest) -> str:
        """Generate completion narrative for a completed quest.

        Args:
            quest: The completed quest

        Returns:
            Narrative text describing quest completion
        """
        return f"""🎉 **Quest Completed: {quest.title}**

You have successfully completed all objectives! {quest.given_by} is pleased with your work.

**Rewards:** {quest.rewards or "Experience and satisfaction"}

A sense of accomplishment fills you. What will you do next?"""
