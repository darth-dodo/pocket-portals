"""Pydantic schemas for structured agent outputs.

These schemas enforce valid LLM responses using CrewAI's output_pydantic feature,
reducing JSON parse failures from ~15% to near zero.
"""

from pydantic import BaseModel, Field, field_validator


class InterviewResponse(BaseModel):
    """Structured response from the interviewer agent during character creation.

    Used to gather character details through interactive Q&A, where each turn
    presents a question/response and exactly 3 choices for the player.
    """

    content_safe: bool = Field(
        default=True,
        description="Set to false ONLY if the player's input contains genuinely "
        "inappropriate content: self-harm, explicit sexual content, graphic torture, "
        "or hate speech. Use semantic understanding - 'assassin', 'therapist' are "
        "safe words. Fantasy violence is allowed. When in doubt, it's safe.",
    )
    narrative: str = Field(
        description="The interviewer's question or response to the player's previous "
        "answer. Should feel conversational and guide character development. "
        "Keep it focused and engaging. If content_safe is false, write a gentle "
        "redirection like 'Let's focus on your character's heroic qualities.'",
        min_length=10,
        max_length=500,
    )
    choices: list[str] = Field(
        description="Exactly 3 distinct choices for the player to select from. "
        "Each choice should represent a meaningful character trait, background "
        "element, or personality aspect. Be specific and evocative.",
        min_length=3,
        max_length=3,
    )

    @field_validator("choices")
    @classmethod
    def validate_choices_count(cls, v: list[str]) -> list[str]:
        """Ensure exactly 3 choices are provided."""
        if len(v) < 3:
            raise ValueError("InterviewResponse requires at least 3 choices")
        return v


class StarterChoicesResponse(BaseModel):
    """Structured response for initial character concept choices.

    Used at the start of character creation to present diverse character
    archetypes or concepts for the player to choose from.
    """

    choices: list[str] = Field(
        description="A list of 3-9 diverse character concepts or archetypes. "
        "Each should be a brief, evocative description that sparks imagination. "
        "Include a mix of classic fantasy roles and unique twists.",
        min_length=3,
        max_length=9,
    )

    @field_validator("choices")
    @classmethod
    def validate_minimum_choices(cls, v: list[str]) -> list[str]:
        """Ensure at least 3 choices are provided."""
        if len(v) < 3:
            raise ValueError("StarterChoicesResponse requires at least 3 choices")
        return v


class AdventureHooksResponse(BaseModel):
    """Structured response for adventure hook choices.

    Used after character creation to present tailored adventure openings
    that connect to the character's background, traits, and motivations.
    """

    choices: list[str] = Field(
        description="Exactly 3 adventure hooks tailored to the character. "
        "Each hook should reference specific character traits or backstory "
        "elements and present an intriguing situation or call to action. "
        "Be specific and create immediate narrative tension.",
        min_length=3,
        max_length=3,
    )

    @field_validator("choices")
    @classmethod
    def validate_hooks_count(cls, v: list[str]) -> list[str]:
        """Ensure exactly 3 adventure hooks are provided."""
        if len(v) < 3:
            raise ValueError("AdventureHooksResponse requires at least 3 choices")
        return v
