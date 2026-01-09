"""Tests for structured output schemas in src/agents/schemas.py.

This module provides comprehensive tests for Pydantic schemas used
in structured LLM outputs for the character interviewer agent.
"""

import pytest
from pydantic import ValidationError

from src.agents.schemas import (
    AdventureHooksResponse,
    InterviewResponse,
    StarterChoicesResponse,
)


class TestInterviewResponse:
    """Test suite for InterviewResponse schema."""

    def test_interview_response_valid_data(self) -> None:
        """Test that InterviewResponse accepts valid data with narrative and 3 choices."""
        response = InterviewResponse(
            narrative="The innkeeper leans forward, his weathered hands wrapped around a mug.",
            choices=[
                "I am a warrior seeking glory",
                "I am a scholar of ancient lore",
                "I am a wanderer with a troubled past",
            ],
        )

        assert (
            response.narrative
            == "The innkeeper leans forward, his weathered hands wrapped around a mug."
        )
        assert len(response.choices) == 3
        assert response.choices[0] == "I am a warrior seeking glory"

    def test_interview_response_exactly_three_choices_required(self) -> None:
        """Test that InterviewResponse requires exactly 3 choices."""
        response = InterviewResponse(
            narrative="The innkeeper nods slowly at your words.",
            choices=["Choice one", "Choice two", "Choice three"],
        )

        assert len(response.choices) == 3

    def test_interview_response_less_than_three_choices_raises_error(self) -> None:
        """Test that InterviewResponse with less than 3 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative="The innkeeper waits patiently for your response.",
                choices=["Choice one", "Choice two"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        # Check that the error is related to the choices field and length
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_interview_response_more_than_three_choices_raises_error(self) -> None:
        """Test that InterviewResponse with more than 3 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative="The innkeeper waits patiently for your response.",
                choices=["One", "Two", "Three", "Four"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_interview_response_empty_narrative_raises_error(self) -> None:
        """Test that InterviewResponse with empty narrative raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative="",
                choices=["Choice one", "Choice two", "Choice three"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("narrative" in str(e.get("loc", "")) for e in errors)

    def test_interview_response_short_narrative_raises_error(self) -> None:
        """Test that InterviewResponse with narrative under min_length raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative="Hi",  # Too short - min_length is 10
                choices=["Choice one", "Choice two", "Choice three"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("narrative" in str(e.get("loc", "")) for e in errors)

    def test_interview_response_duplicate_choices_allowed(self) -> None:
        """Test that duplicate choices are allowed (dedup is separate concern)."""
        # Duplicates should be allowed at the schema level
        # Deduplication is handled elsewhere in the application
        response = InterviewResponse(
            narrative="The innkeeper speaks with gravitas.",
            choices=["Same choice", "Same choice", "Different choice"],
        )

        assert len(response.choices) == 3
        assert response.choices[0] == response.choices[1]

    def test_interview_response_json_parsing_valid(self) -> None:
        """Test that model_validate_json works with valid JSON string."""
        json_str = """{
            "narrative": "The tavern is warm and inviting as you step inside.",
            "choices": ["Approach the bar", "Find a quiet corner", "Speak to the stranger"]
        }"""

        response = InterviewResponse.model_validate_json(json_str)

        assert (
            response.narrative == "The tavern is warm and inviting as you step inside."
        )
        assert len(response.choices) == 3
        assert "Approach the bar" in response.choices

    def test_interview_response_json_parsing_invalid_raises_error(self) -> None:
        """Test that model_validate_json raises on invalid JSON."""
        invalid_json = "This is not JSON at all"

        with pytest.raises(ValidationError):
            InterviewResponse.model_validate_json(invalid_json)

    def test_interview_response_json_parsing_missing_field_raises_error(self) -> None:
        """Test that model_validate_json raises on missing required field."""
        json_missing_choices = '{"narrative": "Some narrative text here."}'

        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse.model_validate_json(json_missing_choices)

        errors = exc_info.value.errors()
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_interview_response_model_dump(self) -> None:
        """Test that model_dump produces correct dictionary output."""
        response = InterviewResponse(
            narrative="A mysterious figure enters the tavern.",
            choices=["Greet them", "Watch silently", "Prepare for trouble"],
        )

        dumped = response.model_dump()

        assert dumped["narrative"] == "A mysterious figure enters the tavern."
        assert dumped["choices"] == [
            "Greet them",
            "Watch silently",
            "Prepare for trouble",
        ]

    def test_interview_response_narrative_max_length(self) -> None:
        """Test that narrative respects max_length constraint (500 chars)."""
        # Narrative longer than 500 characters should raise an error
        long_narrative = "x" * 501

        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative=long_narrative,
                choices=["A", "B", "C"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("narrative" in str(e.get("loc", "")) for e in errors)


class TestStarterChoicesResponse:
    """Test suite for StarterChoicesResponse schema."""

    def test_starter_choices_response_valid_with_three_choices(self) -> None:
        """Test that StarterChoicesResponse accepts minimum of 3 choices."""
        response = StarterChoicesResponse(
            choices=[
                "I am a seasoned warrior",
                "I am a scholar of ancient arts",
                "I am a wanderer seeking purpose",
            ]
        )

        assert len(response.choices) == 3

    def test_starter_choices_response_valid_with_nine_choices(self) -> None:
        """Test that StarterChoicesResponse accepts maximum of 9 choices."""
        response = StarterChoicesResponse(
            choices=[
                "Choice one",
                "Choice two",
                "Choice three",
                "Choice four",
                "Choice five",
                "Choice six",
                "Choice seven",
                "Choice eight",
                "Choice nine",
            ]
        )

        assert len(response.choices) == 9

    def test_starter_choices_response_valid_with_six_choices(self) -> None:
        """Test that StarterChoicesResponse accepts 6 choices (middle of range)."""
        response = StarterChoicesResponse(
            choices=[
                "Warrior seeking glory",
                "Mage of arcane power",
                "Rogue with shadowy past",
                "Cleric of forgotten deity",
                "Ranger of wild lands",
                "Bard with silver tongue",
            ]
        )

        assert len(response.choices) == 6

    def test_starter_choices_response_less_than_three_choices_raises_error(
        self,
    ) -> None:
        """Test that StarterChoicesResponse with less than 3 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StarterChoicesResponse(
                choices=["Only one", "And two"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_starter_choices_response_more_than_nine_choices_raises_error(self) -> None:
        """Test that StarterChoicesResponse with more than 9 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StarterChoicesResponse(
                choices=[f"Choice {i}" for i in range(10)],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_starter_choices_response_empty_choices_raises_error(self) -> None:
        """Test that StarterChoicesResponse with empty list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StarterChoicesResponse(choices=[])

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_starter_choices_response_duplicate_choices_allowed(self) -> None:
        """Test that duplicate choices are allowed at schema level."""
        response = StarterChoicesResponse(
            choices=["Duplicate", "Duplicate", "Unique choice"],
        )

        assert len(response.choices) == 3

    def test_starter_choices_response_json_parsing_valid(self) -> None:
        """Test that model_validate_json works with valid JSON string."""
        json_str = """{
            "choices": [
                "A mighty warrior with a troubled past",
                "A cunning rogue seeking redemption",
                "A wise sage on a quest for knowledge"
            ]
        }"""

        response = StarterChoicesResponse.model_validate_json(json_str)

        assert len(response.choices) == 3
        assert "mighty warrior" in response.choices[0]

    def test_starter_choices_response_json_parsing_invalid_raises_error(self) -> None:
        """Test that model_validate_json raises on malformed JSON."""
        malformed_json = '{"choices": ["one", "two"'

        with pytest.raises(ValidationError):
            StarterChoicesResponse.model_validate_json(malformed_json)

    def test_starter_choices_response_model_dump(self) -> None:
        """Test that model_dump produces correct dictionary output."""
        response = StarterChoicesResponse(
            choices=["Fighter", "Mage", "Rogue", "Cleric"],
        )

        dumped = response.model_dump()

        assert dumped["choices"] == ["Fighter", "Mage", "Rogue", "Cleric"]

    def test_starter_choices_response_single_choice_raises_error(self) -> None:
        """Test that StarterChoicesResponse with single choice raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            StarterChoicesResponse(choices=["Only one choice"])

        errors = exc_info.value.errors()
        assert len(errors) >= 1


class TestAdventureHooksResponse:
    """Test suite for AdventureHooksResponse schema.

    Note: AdventureHooksResponse uses 'choices' field, not 'hooks'.
    """

    def test_adventure_hooks_response_valid_data(self) -> None:
        """Test that AdventureHooksResponse accepts valid data with 3 choices."""
        response = AdventureHooksResponse(
            choices=[
                "A hooded figure beckons from a shadowy corner",
                "The innkeeper mentions bandits on the road",
                "A mysterious map falls from a traveler's pocket",
            ]
        )

        assert len(response.choices) == 3
        assert "hooded figure" in response.choices[0]

    def test_adventure_hooks_response_exactly_three_choices_required(self) -> None:
        """Test that AdventureHooksResponse requires exactly 3 choices."""
        response = AdventureHooksResponse(
            choices=[
                "Hook one",
                "Hook two",
                "Hook three",
            ]
        )

        assert len(response.choices) == 3

    def test_adventure_hooks_response_less_than_three_choices_raises_error(
        self,
    ) -> None:
        """Test that AdventureHooksResponse with less than 3 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AdventureHooksResponse(
                choices=["Only one hook", "And a second hook"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_adventure_hooks_response_more_than_three_choices_raises_error(
        self,
    ) -> None:
        """Test that AdventureHooksResponse with more than 3 choices raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AdventureHooksResponse(
                choices=["Hook one", "Hook two", "Hook three", "Hook four"],
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_adventure_hooks_response_empty_choices_raises_error(self) -> None:
        """Test that AdventureHooksResponse with empty list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AdventureHooksResponse(choices=[])

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_adventure_hooks_response_duplicate_choices_allowed(self) -> None:
        """Test that duplicate choices are allowed at schema level."""
        response = AdventureHooksResponse(
            choices=["Same hook", "Same hook", "Different hook"],
        )

        assert len(response.choices) == 3

    def test_adventure_hooks_response_json_parsing_valid(self) -> None:
        """Test that model_validate_json works with valid JSON string."""
        json_str = """{
            "choices": [
                "A dark elf whispers of danger",
                "The town guard seeks help",
                "A merchant offers a secret job"
            ]
        }"""

        response = AdventureHooksResponse.model_validate_json(json_str)

        assert len(response.choices) == 3
        assert "dark elf" in response.choices[0]

    def test_adventure_hooks_response_json_parsing_invalid_raises_error(self) -> None:
        """Test that model_validate_json raises on invalid JSON."""
        invalid_json = "not json at all"

        with pytest.raises(ValidationError):
            AdventureHooksResponse.model_validate_json(invalid_json)

    def test_adventure_hooks_response_json_parsing_missing_field_raises_error(
        self,
    ) -> None:
        """Test that model_validate_json raises on missing choices field."""
        json_missing_choices = "{}"

        with pytest.raises(ValidationError) as exc_info:
            AdventureHooksResponse.model_validate_json(json_missing_choices)

        errors = exc_info.value.errors()
        assert any("choices" in str(e.get("loc", "")) for e in errors)

    def test_adventure_hooks_response_model_dump(self) -> None:
        """Test that model_dump produces correct dictionary output."""
        response = AdventureHooksResponse(
            choices=[
                "A dragon's shadow passes overhead",
                "The oracle speaks your name",
                "A portal flickers in the alley",
            ]
        )

        dumped = response.model_dump()

        assert dumped["choices"] == [
            "A dragon's shadow passes overhead",
            "The oracle speaks your name",
            "A portal flickers in the alley",
        ]


class TestSchemaEdgeCases:
    """Test suite for edge cases across all schemas."""

    def test_interview_response_narrative_at_min_length(self) -> None:
        """Test that narrative at exactly min_length (10) is accepted."""
        response = InterviewResponse(
            narrative="Hello now!",  # Exactly 10 characters
            choices=["A", "B", "C"],
        )

        assert len(response.narrative) == 10

    def test_interview_response_narrative_at_max_length(self) -> None:
        """Test that narrative at exactly max_length (500) is accepted."""
        narrative = "x" * 500
        response = InterviewResponse(
            narrative=narrative,
            choices=["A", "B", "C"],
        )

        assert len(response.narrative) == 500

    def test_starter_choices_special_characters_in_choices(self) -> None:
        """Test that special characters in choices are accepted."""
        response = StarterChoicesResponse(
            choices=[
                "A warrior who's lost everything",
                'A mage seeking the "Eternal Flame"',
                "A rogue with a 50/50 survival rate",
            ]
        )

        assert "who's" in response.choices[0]
        assert '"Eternal Flame"' in response.choices[1]
        assert "50/50" in response.choices[2]

    def test_adventure_hooks_unicode_characters_accepted(self) -> None:
        """Test that Unicode characters in choices are accepted."""
        response = AdventureHooksResponse(
            choices=[
                "The elven script reads: 'Danger ahead'",
                "A coin bears the mark of House Valois",
                "The rune glows with ancient power",
            ]
        )

        assert len(response.choices) == 3

    def test_interview_response_from_dict(self) -> None:
        """Test that InterviewResponse can be created from dictionary."""
        data = {
            "narrative": "The fire crackles warmly in the hearth.",
            "choices": [
                "Rest by the fire",
                "Explore the room",
                "Call for the innkeeper",
            ],
        }

        response = InterviewResponse.model_validate(data)

        assert response.narrative == data["narrative"]
        assert response.choices == data["choices"]

    def test_starter_choices_response_from_dict(self) -> None:
        """Test that StarterChoicesResponse can be created from dictionary."""
        data = {
            "choices": ["Option A", "Option B", "Option C", "Option D"],
        }

        response = StarterChoicesResponse.model_validate(data)

        assert response.choices == data["choices"]

    def test_adventure_hooks_response_from_dict(self) -> None:
        """Test that AdventureHooksResponse can be created from dictionary."""
        data = {
            "choices": ["Hook one", "Hook two", "Hook three"],
        }

        response = AdventureHooksResponse.model_validate(data)

        assert response.choices == data["choices"]

    def test_interview_response_json_round_trip(self) -> None:
        """Test that InterviewResponse survives JSON serialization round trip."""
        original = InterviewResponse(
            narrative="A test narrative with 'quotes' and special chars in it.",
            choices=["Choice 1", "Choice 2", "Choice 3"],
        )

        json_str = original.model_dump_json()
        restored = InterviewResponse.model_validate_json(json_str)

        assert restored.narrative == original.narrative
        assert restored.choices == original.choices

    def test_all_schemas_attribute_access(self) -> None:
        """Test that schema instances allow proper attribute access."""
        interview = InterviewResponse(
            narrative="Test narrative here.",
            choices=["A", "B", "C"],
        )
        starter = StarterChoicesResponse(choices=["A", "B", "C"])
        hooks = AdventureHooksResponse(choices=["A", "B", "C"])

        # Verify we can access attributes
        assert interview.narrative == "Test narrative here."
        assert starter.choices[0] == "A"
        assert hooks.choices[0] == "A"

    def test_starter_choices_response_json_round_trip(self) -> None:
        """Test that StarterChoicesResponse survives JSON serialization round trip."""
        original = StarterChoicesResponse(
            choices=["Warrior", "Mage", "Rogue", "Cleric"],
        )

        json_str = original.model_dump_json()
        restored = StarterChoicesResponse.model_validate_json(json_str)

        assert restored.choices == original.choices

    def test_adventure_hooks_response_json_round_trip(self) -> None:
        """Test that AdventureHooksResponse survives JSON serialization round trip."""
        original = AdventureHooksResponse(
            choices=["Hook A", "Hook B", "Hook C"],
        )

        json_str = original.model_dump_json()
        restored = AdventureHooksResponse.model_validate_json(json_str)

        assert restored.choices == original.choices


class TestSchemaIntegration:
    """Integration tests for schema usage patterns."""

    def test_interview_response_typical_llm_output_format(self) -> None:
        """Test parsing of typical LLM JSON output format."""
        # This mimics what an LLM might return
        llm_output = """{
            "narrative": "The old innkeeper pauses mid-pour, his eyes widening slightly as he takes in your travel-worn appearance. 'Well now,' he says, setting down the tankard with practiced care, 'you've got the look of someone with a tale to tell.'",
            "choices": [
                "Tell him about your noble heritage",
                "Deflect with a mysterious smile",
                "Ask about rumors in town first"
            ]
        }"""

        response = InterviewResponse.model_validate_json(llm_output)

        assert "innkeeper" in response.narrative
        assert len(response.choices) == 3
        assert "noble heritage" in response.choices[0]

    def test_starter_choices_typical_llm_output_format(self) -> None:
        """Test parsing of typical LLM JSON output for starter choices."""
        llm_output = """{
            "choices": [
                "I am a battle-scarred veteran seeking one last adventure",
                "I am a young mage eager to prove my worth",
                "I am a roguish merchant with a heart of gold",
                "I am a devout pilgrim following divine signs",
                "I am a mysterious stranger with a forgotten past",
                "I am a noble heir forced to flee my homeland"
            ]
        }"""

        response = StarterChoicesResponse.model_validate_json(llm_output)

        assert len(response.choices) == 6
        assert any("veteran" in choice for choice in response.choices)

    def test_adventure_hooks_typical_llm_output_format(self) -> None:
        """Test parsing of typical LLM JSON output for adventure hooks."""
        llm_output = """{
            "choices": [
                "A hooded elf at the corner table catches your eye and gestures subtly",
                "The innkeeper lowers his voice and mentions trouble on the north road",
                "A young messenger bursts in, desperately seeking someone who looks capable"
            ]
        }"""

        response = AdventureHooksResponse.model_validate_json(llm_output)

        assert len(response.choices) == 3
        assert "elf" in response.choices[0]
        assert "innkeeper" in response.choices[1]
        assert "messenger" in response.choices[2]

    def test_interview_response_field_validator_applied(self) -> None:
        """Test that the field validator on choices is applied."""
        # This tests the validate_choices_count validator
        with pytest.raises(ValidationError):
            InterviewResponse(
                narrative="Valid narrative here.",
                choices=["One", "Two"],  # Less than 3
            )

    def test_starter_choices_response_field_validator_applied(self) -> None:
        """Test that the field validator on choices is applied."""
        # This tests the validate_minimum_choices validator
        with pytest.raises(ValidationError):
            StarterChoicesResponse(choices=["One", "Two"])  # Less than 3

    def test_adventure_hooks_response_field_validator_applied(self) -> None:
        """Test that the field validator on choices is applied."""
        # This tests the validate_hooks_count validator
        with pytest.raises(ValidationError):
            AdventureHooksResponse(choices=["One", "Two"])  # Less than 3


class TestSchemaValidatorBehavior:
    """Tests specifically for validator behavior and error messages."""

    def test_interview_response_validator_error_message(self) -> None:
        """Test that InterviewResponse validator produces meaningful error."""
        with pytest.raises(ValidationError) as exc_info:
            InterviewResponse(
                narrative="Valid narrative here.",
                choices=["One"],
            )

        # Check that the error message is meaningful
        error_str = str(exc_info.value)
        assert "choices" in error_str.lower() or "3" in error_str

    def test_starter_choices_validator_error_message(self) -> None:
        """Test that StarterChoicesResponse validator produces meaningful error."""
        with pytest.raises(ValidationError) as exc_info:
            StarterChoicesResponse(choices=["One"])

        # Check that the error message is meaningful
        error_str = str(exc_info.value)
        assert "choices" in error_str.lower() or "3" in error_str

    def test_adventure_hooks_validator_error_message(self) -> None:
        """Test that AdventureHooksResponse validator produces meaningful error."""
        with pytest.raises(ValidationError) as exc_info:
            AdventureHooksResponse(choices=["One"])

        # Check that the error message is meaningful
        error_str = str(exc_info.value)
        assert "choices" in error_str.lower() or "3" in error_str

    def test_schemas_reject_wrong_types(self) -> None:
        """Test that schemas reject incorrect types for fields."""
        with pytest.raises(ValidationError):
            InterviewResponse(
                narrative=123,  # type: ignore[arg-type]  # Should be string
                choices=["A", "B", "C"],
            )

        with pytest.raises(ValidationError):
            StarterChoicesResponse(choices="not a list")  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            AdventureHooksResponse(choices={"not": "a list"})  # type: ignore[arg-type]

    def test_schemas_reject_none_values(self) -> None:
        """Test that schemas reject None for required fields."""
        with pytest.raises(ValidationError):
            InterviewResponse(
                narrative=None,  # type: ignore[arg-type]
                choices=["A", "B", "C"],
            )

        with pytest.raises(ValidationError):
            InterviewResponse(
                narrative="Valid narrative here.",
                choices=None,  # type: ignore[arg-type]
            )

        with pytest.raises(ValidationError):
            StarterChoicesResponse(choices=None)  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            AdventureHooksResponse(choices=None)  # type: ignore[arg-type]
