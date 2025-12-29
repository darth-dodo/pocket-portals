#!/usr/bin/env python
"""Demo script for the Adventure Pacing System.

This script demonstrates the 50-turn adventure pacing with:
- Turn tracking and phase progression
- Pacing context for agents
- Closure triggers (quest completion or hard cap)
- EpilogueAgent for personalized conclusions

Usage:
    uv run python scripts/demo_adventure_pacing.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.epilogue import generate_fallback_epilogue
from src.engine.pacing import (
    build_pacing_context,
    check_closure_triggers,
    format_pacing_hint,
)
from src.state.character import (
    CharacterClass,
    CharacterRace,
    CharacterSheet,
    CharacterStats,
)
from src.state.models import (
    AdventurePhase,
    GamePhase,
    GameState,
    Quest,
    QuestObjective,
    QuestStatus,
)


def create_demo_character() -> CharacterSheet:
    """Create a demo character for testing."""
    return CharacterSheet(
        name="Theron Brightblade",
        race=CharacterRace.HUMAN,
        character_class=CharacterClass.FIGHTER,
        backstory="A former soldier seeking redemption after a battlefield tragedy.",
        stats=CharacterStats(
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=13,
            charisma=11,
        ),
        equipment=["Longsword", "Shield", "Chain mail", "Adventurer's pack"],
    )


def demo_phase_progression() -> None:
    """Demonstrate phase progression through adventure turns."""
    print("=" * 60)
    print("DEMO: Adventure Phase Progression")
    print("=" * 60)

    state = GameState(
        session_id="demo-session",
        phase=GamePhase.EXPLORATION,
        adventure_turn=0,
        adventure_phase=AdventurePhase.SETUP,
        max_turns=50,
    )

    # Key turns to demonstrate
    key_turns = [1, 5, 6, 15, 20, 21, 30, 31, 40, 42, 43, 49, 50]

    for turn in key_turns:
        state.adventure_turn = turn

        # Calculate phase based on turn
        if turn <= 5:
            state.adventure_phase = AdventurePhase.SETUP
        elif turn <= 20:
            state.adventure_phase = AdventurePhase.RISING_ACTION
        elif turn <= 30:
            state.adventure_phase = AdventurePhase.MID_POINT
        elif turn <= 42:
            state.adventure_phase = AdventurePhase.CLIMAX
        else:
            state.adventure_phase = AdventurePhase.DENOUEMENT

        context = build_pacing_context(state)
        print(
            f"\nTurn {turn:2d} | Phase: {state.adventure_phase.value:15} | "
            f"Urgency: {context.urgency_level:.1%}"
        )

    print("\n")


def demo_pacing_hints() -> None:
    """Demonstrate pacing hints for narrators at different phases."""
    print("=" * 60)
    print("DEMO: Pacing Hints for Narrator")
    print("=" * 60)

    phases = [
        (AdventurePhase.SETUP, 3),
        (AdventurePhase.RISING_ACTION, 12),
        (AdventurePhase.MID_POINT, 25),
        (AdventurePhase.CLIMAX, 38),
        (AdventurePhase.DENOUEMENT, 48),
    ]

    for phase, turn in phases:
        state = GameState(
            session_id="demo-session",
            phase=GamePhase.EXPLORATION,
            adventure_turn=turn,
            adventure_phase=phase,
            max_turns=50,
        )

        context = build_pacing_context(state)
        hint = format_pacing_hint(context)

        print(f"\n[{phase.value.upper()}] Turn {turn}")
        print("-" * 40)
        print(hint)

    print("\n")


def demo_closure_triggers() -> None:
    """Demonstrate closure trigger conditions."""
    print("=" * 60)
    print("DEMO: Closure Triggers")
    print("=" * 60)

    # Scenario 1: Quest complete after turn 25
    print("\n📜 Scenario 1: Quest completed at turn 30")
    state1 = GameState(
        session_id="demo-1",
        phase=GamePhase.EXPLORATION,
        adventure_turn=30,
        adventure_phase=AdventurePhase.CLIMAX,
        max_turns=50,
        active_quest=Quest(
            id="main-quest",
            title="Break the Curse",
            description="Defeat the dark lord",
            objectives=[
                QuestObjective(
                    id="obj1", description="Find the sword", is_completed=True
                )
            ],
            status=QuestStatus.COMPLETED,
        ),
    )
    closure1 = check_closure_triggers(state1)
    print(f"   Should trigger epilogue: {closure1.should_trigger_epilogue}")
    print(f"   Reason: {closure1.reason}")
    print(f"   Turns remaining: {closure1.turns_remaining}")

    # Scenario 2: Quest complete before turn 25 (no trigger yet)
    print("\n📜 Scenario 2: Quest completed at turn 20 (too early)")
    state2 = GameState(
        session_id="demo-2",
        phase=GamePhase.EXPLORATION,
        adventure_turn=20,
        adventure_phase=AdventurePhase.RISING_ACTION,
        max_turns=50,
        active_quest=Quest(
            id="main-quest",
            title="Break the Curse",
            description="Defeat the dark lord",
            objectives=[
                QuestObjective(
                    id="obj1", description="Find the sword", is_completed=True
                )
            ],
            status=QuestStatus.COMPLETED,
        ),
    )
    closure2 = check_closure_triggers(state2)
    print(f"   Should trigger epilogue: {closure2.should_trigger_epilogue}")
    print(f"   Reason: {closure2.reason}")
    print(f"   Turns remaining: {closure2.turns_remaining}")

    # Scenario 3: Hard cap at turn 50
    print("\n📜 Scenario 3: Hard cap reached at turn 50")
    state3 = GameState(
        session_id="demo-3",
        phase=GamePhase.EXPLORATION,
        adventure_turn=50,
        adventure_phase=AdventurePhase.DENOUEMENT,
        max_turns=50,
    )
    closure3 = check_closure_triggers(state3)
    print(f"   Should trigger epilogue: {closure3.should_trigger_epilogue}")
    print(f"   Reason: {closure3.reason}")
    print(f"   Turns remaining: {closure3.turns_remaining}")

    print("\n")


def demo_epilogue_generation() -> None:
    """Demonstrate epilogue generation for different scenarios."""
    print("=" * 60)
    print("DEMO: Epilogue Generation (Fallback Mode)")
    print("=" * 60)

    character = create_demo_character()

    # Create states with character
    state_quest = GameState(
        session_id="demo-epilogue-1",
        phase=GamePhase.EXPLORATION,
        adventure_turn=40,
        adventure_phase=AdventurePhase.DENOUEMENT,
        max_turns=50,
        character_sheet=character,
    )

    state_hardcap = GameState(
        session_id="demo-epilogue-2",
        phase=GamePhase.EXPLORATION,
        adventure_turn=50,
        adventure_phase=AdventurePhase.DENOUEMENT,
        max_turns=50,
        character_sheet=character,
    )

    state_no_char = GameState(
        session_id="demo-epilogue-3",
        phase=GamePhase.EXPLORATION,
        adventure_turn=40,
        adventure_phase=AdventurePhase.DENOUEMENT,
        max_turns=50,
    )

    # Quest complete epilogue
    print("\n🎭 Quest Complete Epilogue:")
    print("-" * 40)
    epilogue1 = generate_fallback_epilogue("quest_complete", state_quest)
    print(epilogue1)

    # Hard cap epilogue
    print("\n🎭 Hard Cap Epilogue:")
    print("-" * 40)
    epilogue2 = generate_fallback_epilogue("hard_cap", state_hardcap)
    print(epilogue2)

    # No character epilogue
    print("\n🎭 Generic Epilogue (no character):")
    print("-" * 40)
    epilogue3 = generate_fallback_epilogue("quest_complete", state_no_char)
    print(epilogue3)

    print("\n")


def demo_full_adventure_simulation() -> None:
    """Simulate a full adventure with pacing updates."""
    print("=" * 60)
    print("DEMO: Full Adventure Simulation")
    print("=" * 60)

    character = create_demo_character()

    # Simulate adventure with key events
    events = [
        (5, "Character enters the haunted forest", AdventurePhase.SETUP),
        (12, "Discovers ancient ruins", AdventurePhase.RISING_ACTION),
        (20, "Confronts a mysterious guardian", AdventurePhase.RISING_ACTION),
        (25, "Learns the truth about the curse", AdventurePhase.MID_POINT),
        (35, "Final battle with the dark lord", AdventurePhase.CLIMAX),
        (38, "Breaks the curse, quest complete!", AdventurePhase.CLIMAX),
    ]

    print(f"\n⚔️ Adventure: The Quest of {character.name}")
    print("-" * 40)

    for turn, event, phase in events:
        # Create state for this turn
        state = GameState(
            session_id="demo-full",
            phase=GamePhase.EXPLORATION,
            adventure_turn=turn,
            adventure_phase=phase,
            max_turns=50,
            character_sheet=character,
        )

        context = build_pacing_context(state)

        print(f"\nTurn {turn:2d} [{phase.value}]")
        print(f"   📖 {event}")
        print(f"   ⚡ Urgency: {context.urgency_level:.0%}")

        # Check for quest completion trigger at turn 38
        if turn == 38:
            # Add completed quest to simulate quest completion
            quest = Quest(
                id="main-quest",
                title="Break the Curse",
                description="Defeat the dark lord",
                objectives=[
                    QuestObjective(id="obj1", description="Win", is_completed=True)
                ],
                status=QuestStatus.COMPLETED,
            )
            state_with_quest = GameState(
                session_id="demo-full",
                phase=GamePhase.EXPLORATION,
                adventure_turn=turn,
                adventure_phase=phase,
                max_turns=50,
                character_sheet=character,
                completed_quests=[quest],
            )
            closure = check_closure_triggers(state_with_quest)
            if closure.should_trigger_epilogue:
                print(f"\n   🏆 CLOSURE TRIGGERED: {closure.reason}")

    # Generate epilogue
    print("\n" + "=" * 40)
    print("📜 EPILOGUE")
    print("=" * 40)
    final_state = GameState(
        session_id="demo-final",
        phase=GamePhase.EXPLORATION,
        adventure_turn=45,
        adventure_phase=AdventurePhase.DENOUEMENT,
        max_turns=50,
        character_sheet=character,
    )
    epilogue = generate_fallback_epilogue("quest_complete", final_state)
    print(epilogue)
    print("\n")


if __name__ == "__main__":
    print("\n" + "🎮 " * 20)
    print("     POCKET PORTALS - Adventure Pacing System Demo")
    print("🎮 " * 20 + "\n")

    demo_phase_progression()
    demo_pacing_hints()
    demo_closure_triggers()
    demo_epilogue_generation()
    demo_full_adventure_simulation()

    print("=" * 60)
    print("✅ Demo complete! All adventure pacing features demonstrated.")
    print("=" * 60)
