#!/usr/bin/env python
"""Quick spike test for the Narrator agent.

Run with: python test_narrator_spike.py

Requires ANTHROPIC_API_KEY in environment or .env file.
"""

from src.agents.narrator import NarratorAgent


def main() -> None:
    """Test the narrator agent with a simple action."""
    print("Initializing Narrator Agent (using CrewAI native LLM)...")
    narrator = NarratorAgent()

    action = "I push open the creaky wooden door and step into the tavern"
    print(f"\nPlayer: {action}")
    print("\nNarrator:")
    print("-" * 60)

    response = narrator.respond(action)
    print(response)
    print("-" * 60)


if __name__ == "__main__":
    main()
