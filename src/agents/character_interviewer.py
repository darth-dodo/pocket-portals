"""Character Interviewer agent - conducts dynamic character creation interviews."""

import logging
import random
import time
from typing import Any

from crewai import LLM, Agent, Task

from src.agents.schemas import (
    AdventureHooksResponse,
    InterviewResponse,
    StarterChoicesResponse,
)
from src.config.loader import load_agent_config, load_task_config
from src.settings import settings

logger = logging.getLogger(__name__)


class CharacterInterviewerAgent:
    """Agent that interviews players to create their character dynamically."""

    # Fallback choices if LLM response parsing fails (genre-flexible)
    DEFAULT_STARTER_CHOICES = [
        "I am a seasoned warrior seeking glory",
        "I am a scholar of mysterious arts",
        "I am a wanderer with a hidden past",
    ]

    def __init__(self) -> None:
        """Initialize the Character Interviewer agent from YAML config."""
        config = load_agent_config("character_interviewer")

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

    def generate_starter_choices(self) -> list[str]:
        """Generate initial character concept choices for a new player.

        Uses CrewAI's output_pydantic for structured LLM output, significantly
        reducing JSON parse failures compared to manual parsing.

        Returns:
            List of 3 character concept strings
        """
        start_time = time.perf_counter()
        used_fallback = False

        logger.info("generate_starter_choices: Starting dynamic generation")
        try:
            task_config = load_task_config("generate_starter_choices")

            task = Task(
                description=task_config.description,
                expected_output=task_config.expected_output,
                agent=self.agent,
                output_pydantic=StarterChoicesResponse,
            )

            logger.info("generate_starter_choices: Executing LLM task...")
            result = task.execute_sync()

            # Handle Pydantic structured output
            if hasattr(result, "pydantic") and result.pydantic:
                pydantic_result = result.pydantic
                if isinstance(pydantic_result, StarterChoicesResponse):
                    all_choices = pydantic_result.choices
                else:
                    # Unexpected type - try to extract choices
                    logger.warning(
                        "generate_starter_choices: Unexpected pydantic type: %s",
                        type(pydantic_result),
                    )
                    used_fallback = True
                    all_choices = self.DEFAULT_STARTER_CHOICES
            elif isinstance(result, StarterChoicesResponse):
                all_choices = result.choices
            else:
                # Fallback to raw parsing if structured output failed
                logger.warning(
                    "generate_starter_choices: No pydantic output, using fallback"
                )
                used_fallback = True
                all_choices = self.DEFAULT_STARTER_CHOICES

            if not used_fallback and len(all_choices) >= 3:
                random.shuffle(all_choices)
                selected = all_choices[:3]

                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "generate_starter_choices: SUCCESS",
                    extra={
                        "total_choices": len(all_choices),
                        "selected": selected,
                        "used_fallback": False,
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return selected

        except Exception as e:
            logger.exception("generate_starter_choices: Exception occurred: %s", str(e))
            used_fallback = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "generate_starter_choices: Using fallback",
            extra={
                "used_fallback": True,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return self.DEFAULT_STARTER_CHOICES

    def generate_adventure_hooks(self, character_info: str) -> list[str]:
        """Generate adventure hooks tailored to the character.

        Uses CrewAI's output_pydantic for structured LLM output, significantly
        reducing JSON parse failures compared to manual parsing.

        Args:
            character_info: Formatted string with character details
                           (name, race, class, background)

        Returns:
            List of 3 adventure hook strings tailored to the character
        """
        start_time = time.perf_counter()
        # Fallback adventure hooks if LLM fails
        default_hooks = [
            "A hooded figure beckons you to a shadowy corner",
            "The innkeeper mentions trouble in the nearby village",
            "A mysterious map falls from a traveler's pocket",
        ]

        try:
            task_config = load_task_config("generate_adventure_hooks")
            description = task_config.description.format(character_info=character_info)

            task = Task(
                description=description,
                expected_output=task_config.expected_output,
                agent=self.agent,
                output_pydantic=AdventureHooksResponse,
            )

            result = task.execute_sync()

            # Handle Pydantic structured output
            if hasattr(result, "pydantic") and result.pydantic:
                pydantic_result = result.pydantic
                if isinstance(pydantic_result, AdventureHooksResponse):
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        "generate_adventure_hooks: SUCCESS",
                        extra={
                            "hooks": pydantic_result.choices,
                            "used_fallback": False,
                            "elapsed_ms": round(elapsed_ms, 2),
                        },
                    )
                    return pydantic_result.choices[:3]
            elif isinstance(result, AdventureHooksResponse):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "generate_adventure_hooks: SUCCESS",
                    extra={
                        "hooks": result.choices,
                        "used_fallback": False,
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return result.choices[:3]

            logger.warning(
                "generate_adventure_hooks: No pydantic output, using fallback"
            )

        except Exception as e:
            logger.exception("generate_adventure_hooks: Exception occurred: %s", str(e))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "generate_adventure_hooks: Using fallback",
            extra={
                "used_fallback": True,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return default_hooks

    def interview_turn(
        self, turn_number: int, conversation_history: str
    ) -> dict[str, Any]:
        """Conduct one turn of the character interview.

        Uses CrewAI's output_pydantic for structured LLM output, significantly
        reducing JSON parse failures compared to manual parsing.

        Args:
            turn_number: Current turn (1-5)
            conversation_history: Formatted history of previous exchanges

        Returns:
            Dict with 'narrative' and 'choices' keys
        """
        start_time = time.perf_counter()

        try:
            task_config = load_task_config("interview_character")

            description = task_config.description.format(
                turn_number=turn_number,
                conversation_history=conversation_history
                or "No previous conversation.",
            )

            task = Task(
                description=description,
                expected_output=task_config.expected_output,
                agent=self.agent,
                output_pydantic=InterviewResponse,
            )

            result = task.execute_sync()

            # Handle Pydantic structured output
            if hasattr(result, "pydantic") and result.pydantic:
                pydantic_result = result.pydantic
                if isinstance(pydantic_result, InterviewResponse):
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        "interview_turn: SUCCESS",
                        extra={
                            "turn": turn_number,
                            "narrative_length": len(pydantic_result.narrative),
                            "choices": pydantic_result.choices,
                            "used_fallback": False,
                            "elapsed_ms": round(elapsed_ms, 2),
                        },
                    )
                    return {
                        "narrative": pydantic_result.narrative,
                        "choices": pydantic_result.choices[:3],
                    }
            elif isinstance(result, InterviewResponse):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "interview_turn: SUCCESS",
                    extra={
                        "turn": turn_number,
                        "narrative_length": len(result.narrative),
                        "choices": result.choices,
                        "used_fallback": False,
                        "elapsed_ms": round(elapsed_ms, 2),
                    },
                )
                return {
                    "narrative": result.narrative,
                    "choices": result.choices[:3],
                }

            logger.warning(
                "interview_turn: No pydantic output, using fallback",
                extra={"turn": turn_number},
            )

        except Exception as e:
            logger.exception(
                "interview_turn: Exception occurred: %s",
                str(e),
                extra={"turn": turn_number},
            )

        # Fallback response
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "interview_turn: Using fallback",
            extra={
                "turn": turn_number,
                "used_fallback": True,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return {
            "narrative": self._get_fallback_narrative(turn_number),
            "choices": self._get_fallback_choices(turn_number),
        }

    def _get_fallback_narrative(self, turn_number: int) -> str:
        """Get fallback narrative for a given turn."""
        fallbacks = {
            1: "The innkeeper looks you over. 'So, stranger - what brings you to my tavern? Who are you?'",
            2: "He nods slowly. 'And what skills do you bring to the table? Sword? Magic? Something else?'",
            3: "'Every adventurer has a reason,' he says. 'What drives you down this dangerous path?'",
            4: "His eyes drift to your pack. 'What tools of the trade do you carry?'",
            5: "'I think I understand who you are now,' the innkeeper says with a knowing smile.",
        }
        return fallbacks.get(turn_number, "The innkeeper waits for your response.")

    def _get_fallback_choices(self, turn_number: int) -> list[str]:
        """Get fallback choices for a given turn (genre-flexible)."""
        fallbacks = {
            1: [
                "I am a warrior seeking glory",
                "I am a scholar of hidden knowledge",
                "I am a wanderer with quick wits",
            ],
            2: [
                "I fight with strength and skill",
                "I wield mysterious powers",
                "I prefer cunning and stealth",
            ],
            3: [
                "I seek fortune and adventure",
                "I'm searching for answers",
                "I want to prove myself",
            ],
            4: [
                "Weapons and armor",
                "Books and strange artifacts",
                "Tools of the trade",
            ],
            5: [
                "I'm ready for adventure",
                "What opportunities await?",
                "Tell me about the dangers here",
            ],
        }
        return fallbacks.get(turn_number, self.DEFAULT_STARTER_CHOICES)
