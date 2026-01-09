"""Flow state management for conversation orchestration.

This module defines the Pydantic model for tracking conversation state across
the multi-agent orchestration system.
"""

from pydantic import BaseModel, Field


class DetectedMoment(BaseModel):
    """Moment data detected during agent execution.

    Lightweight container for moment information extracted from Keeper responses
    that will be persisted as AdventureMoment by the route layer.

    Attributes:
        type: Category of moment (combat_victory, discovery, critical_success, etc.)
        summary: Brief description of what happened (5-10 words)
        significance: Weight for epilogue inclusion (0.0-1.0)
    """

    type: str = Field(description="Moment type (combat_victory, discovery, etc.)")
    summary: str = Field(description="Brief summary of the moment")
    significance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Significance weight"
    )


class ConversationFlowState(BaseModel):
    """State container for conversation flow orchestration.

    Tracks the current state of a multi-agent conversation including context,
    phase transitions, agent invocations, and narrative progression.

    Attributes:
        session_id: Unique identifier for the conversation session
        action: Current user action or input being processed
        context: Accumulated conversation context and history
        phase: Current phase of conversation (e.g., "exploration", "decision")
        recent_agents: List of recently invoked agent names for tracking
        agents_to_invoke: Queue of agent names to invoke next
        include_jester: Whether to include the Jester agent for humor
        routing_reason: Explanation for the current routing decision
        responses: Mapping of agent names to their response content
        error: Optional error message if processing failed
        narrative: Current narrative text to present to user
        choices: List of available choice options for user selection
    """

    session_id: str = Field(
        default="default", description="Unique identifier for the conversation session"
    )

    action: str = Field(
        default="", description="Current user action or input being processed"
    )

    context: str = Field(
        default="", description="Accumulated conversation context and history"
    )

    phase: str = Field(
        default="exploration", description="Current phase of conversation flow"
    )

    recent_agents: list[str] = Field(
        default_factory=list,
        description="List of recently invoked agent names for tracking",
    )

    agents_to_invoke: list[str] = Field(
        default_factory=list, description="Queue of agent names to invoke next"
    )

    include_jester: bool = Field(
        default=False, description="Whether to include the Jester agent for humor"
    )

    routing_reason: str = Field(
        default="", description="Explanation for the current routing decision"
    )

    responses: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of agent names to their response content",
    )

    error: str | None = Field(
        default=None, description="Optional error message if processing failed"
    )

    narrative: str = Field(
        default="", description="Current narrative text to present to user"
    )

    choices: list[str] = Field(
        default_factory=list,
        description="List of available choice options for user selection",
    )

    detected_moment: DetectedMoment | None = Field(
        default=None,
        description="Significant moment detected during Keeper execution, if any",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "action": "explore the dark corridor",
                "context": "You are in a mysterious dungeon...",
                "phase": "exploration",
                "recent_agents": ["narrator", "environment"],
                "agents_to_invoke": ["consequence"],
                "include_jester": False,
                "routing_reason": "User action requires consequence evaluation",
                "responses": {
                    "narrator": "The corridor stretches before you...",
                    "environment": "Torch light flickers on damp walls...",
                },
                "error": None,
                "narrative": "You step cautiously into the darkness...",
                "choices": ["Continue forward", "Light a torch", "Turn back"],
                "detected_moment": None,
            }
        }
