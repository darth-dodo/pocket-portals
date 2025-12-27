"""Character Interviewer agent - conducts dynamic character creation interviews."""

import json
import re
from typing import Any

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


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

        Returns:
            List of 3 character concept strings
        """
        try:
            task_config = load_task_config("generate_starter_choices")

            task = Task(
                description=task_config.description,
                expected_output=task_config.expected_output,
                agent=self.agent,
            )

            result = task.execute_sync()
            parsed = self._parse_json_response(str(result))

            if parsed and "choices" in parsed and len(parsed["choices"]) >= 3:
                return parsed["choices"][:3]

        except Exception:
            pass

        return self.DEFAULT_STARTER_CHOICES

    def generate_adventure_hooks(self, character_info: str) -> list[str]:
        """Generate adventure hooks tailored to the character.

        Called after character creation to provide contextually relevant
        adventure options based on the character's race, class, and background.

        Args:
            character_info: Formatted string with character details
                           (name, race, class, background)

        Returns:
            List of 3 adventure hook strings tailored to the character
        """
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
            )

            result = task.execute_sync()
            parsed = self._parse_json_response(str(result))

            if parsed and "choices" in parsed and len(parsed["choices"]) >= 3:
                return parsed["choices"][:3]

        except Exception:
            pass

        return default_hooks

    def interview_turn(
        self, turn_number: int, conversation_history: str
    ) -> dict[str, Any]:
        """Conduct one turn of the character interview.

        Args:
            turn_number: Current turn (1-5)
            conversation_history: Formatted history of previous exchanges

        Returns:
            Dict with 'narrative' and 'choices' keys
        """
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
            )

            result = task.execute_sync()
            parsed = self._parse_json_response(str(result))

            if parsed and "narrative" in parsed and "choices" in parsed:
                return {
                    "narrative": parsed["narrative"],
                    "choices": parsed["choices"][:3]
                    if len(parsed["choices"]) >= 3
                    else self._get_fallback_choices(turn_number),
                }

        except Exception:
            pass

        # Fallback response
        return {
            "narrative": self._get_fallback_narrative(turn_number),
            "choices": self._get_fallback_choices(turn_number),
        }

    def _parse_json_response(self, response: str) -> dict | None:
        """Parse JSON from LLM response, handling various formats.

        Args:
            response: Raw LLM response string

        Returns:
            Parsed dict or None if parsing fails
        """
        # Try direct JSON parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in response (may be wrapped in text)
        json_match = re.search(r'\{[^{}]*"narrative"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try to find JSON with choices only
        json_match = re.search(r'\{[^{}]*"choices"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

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
