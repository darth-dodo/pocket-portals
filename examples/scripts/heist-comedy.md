# The Duke's Underpants

**Genre:** Heist Comedy
**Tone:** Light, absurd, clever
**Adventure Length:** ~25-35 turns (fast-paced heist)

---

## Adventure Pacing Guide

Comedy heists move fast! Shorter adventure with quick scene transitions and escalating absurdity.

| Phase | Turns | Focus |
|-------|-------|-------|
| **SETUP** | 1-5 | Meet Pip, get the ridiculous job, plan the heist |
| **RISING_ACTION** | 6-15 | Infiltrate the ball, gather intel, set pieces |
| **MID_POINT** | 16-22 | Execute the distraction, things go sideways |
| **CLIMAX** | 23-30 | The pants acquisition, the escape |
| **DENOUEMENT** | 31+ | Victory lap, embarrassment achieved |

---

## SETUP PHASE (Turns 1-5)

### Opening — Turn 1

**Innkeeper Theron:**
> Got a strange one. Duke Harlan humiliated a merchant named Pip at court last week. Called him a "common rat" in front of everyone.

> Pip wants revenge. Not violence. Embarrassment.

> The Duke's throwing a masked ball tomorrow. Pip wants someone to steal his pants. While he's wearing them.

> Fifty gold. Plus whatever you can pocket on the way out.

*[PACING: ESTABLISH - Set up the absurd goal, make it clear this is comedy]*

---

### NPCs

**Pip (they/them):** Wants the Duke humiliated. Giggles when nervous. Actually has a solid plan.

**Duke Harlan (he/him):** Arrogant. Never looks down. Wearing very expensive pants.

**Coral (she/her):** The Duke's valet. Hates him. Open to negotiation.

---

### Scene 1: The Plan — Turns 2-5

**Narrator:**
> Pip's townhouse smells of lavender and barely contained rage. Maps cover every surface, annotated in at least three colors of ink.

> "The Duke is allergic to shellfish," Pip says, tracing a finger along the manor's floor plan. "Deathly allergic. He keeps a physician nearby at all times."

> They look up, grinning. "Create a distraction. Get him alone. Take the pants. Simple."

> Three ways in: servant entrance, balcony, or through the wine cellar. The Duke's bedroom is on the second floor, but he'll be in the ballroom until midnight at least.

> How do you want to play this?

*[PACING: Planning montage, player chooses approach]*

---

## RISING_ACTION PHASE (Turns 6-15)

### Scene 2: Infiltration — Turns 6-10

**Narrator:**
> The ballroom blazes with candlelight, a swirling sea of masks and silk and perfume expensive enough to drown in. A string quartet plays something elegant. The Duke holds court by the fountain, laughing too loudly at his own wit.

> You spot Coral weaving through the crowd with a wine tray. The physician hovers near the kitchen. Guards at every door, but their eyes are on the guests, not the servants.

**Keeper:**
> Blend in: 10. Win Coral over: 12.

*[PACING: ESCALATE - Build the heist, establish pieces]*

---

### Scene 2b: Setting the Stage — Turns 11-15

**Narrator:**
> Coral leans close, her smile sharp as broken glass. "You want to embarrass him? I've wanted that for years."

> She slips you a servant's uniform. "Kitchen's got oysters for the toast. The physician keeps his medicine bag by the side door. And the Duke?" She laughs softly. "He always goes to the trophy room when he's feeling ill. Private. Quiet."

> "I'll make sure he gets a bad oyster."

> The game is set. The pieces are in place.

*[PACING: Allies recruited, plan coming together]*

---

## MID_POINT PHASE (Turns 16-22)

### Scene 3: The Distraction — Turns 16-19

*If shellfish distraction:*

**Narrator:**
> The Duke's face cycles through an impressive range of colors. Red, purple, something approaching chartreuse. Guards rush him toward a private room, the physician scrambling behind.

> You have maybe two minutes.

*[PACING: REVEAL - The heist is GO, things are in motion]*

---

### Scene 3b: Complications — Turns 20-22

**Narrator:**
> A guard you didn't account for. A locked door that shouldn't be locked. The physician works faster than expected.

> From inside the trophy room, you hear the Duke groaning. "My trousers feel tight. Loosen them at once!"

> Clock's ticking.

**Keeper:**
> Quick thinking: DC 12 to adapt.

*[PACING: Things going sideways—comedy complications]*

---

## CLIMAX PHASE (Turns 23-30)

### Scene 4: The Pants — Turns 23-27

**Narrator:**
> The Duke sprawls across a chaise, wheezing dramatically while the physician works. Neither notices the door open. Neither notices you.

> His pants are extraordinary. Gold thread, pearl buttons, enough silk to upholster a small palace. They're also still very much on his body.

**Keeper:**
> Quick hands. 14. Or get creative.

*Success:*

**Narrator:**
> Later, you won't be able to explain exactly how you did it. Something about leverage and distraction and sheer audacity. But you're holding the Duke's pants, and he hasn't noticed yet.

*[PACING: INTENSIFY - The impossible moment of theft]*

---

### Scene 4b: The Escape — Turns 28-30

*Fail:*

**Keeper:**
> Run for it. Three chances: Fast feet 12, nimble 11, vanish 10. Two out of three and you're clear.

**Narrator:**
> You slip through the crowd, the world's most expensive trousers tucked under your arm. Behind you, a shriek. Then a gasp. Then laughter, building like a wave.

> The Duke stands in the ballroom doorway, searching frantically for the source of the draft.

> Everyone sees.

*[PACING: Quest complete! Maximum comedic payoff triggers epilogue]*

---

## DENOUEMENT PHASE (Turns 31+)

### Epilogue — Turns 31+

**Narrator:**
> Pip pays double, giggling so hard they can barely count the coins. The story spreads through every tavern in the city before sunrise.

> The Duke never shows his face at court again.

> You still have the pants. They're hideous. They're worth a fortune.

> Coral sends a bottle of wine. The card reads: "Worth every moment."

*[PACING: RESOLVE - Victory lap, relationships honored, loot acquired]*

---

## Jester Moments

*Turn 4:*
> "Stealing a man's pants while he's wearing them. This is peak adventuring right here."

*Turn 25:*
> "The Duke's smallclothes have little crowns on them. I thought you should know that."

*Turn 29:*
> "You're running through a ballroom clutching stolen pants while a pantless aristocrat screams behind you. Your parents would be so proud."

---

## Implementation Notes

**IMPORTANT**: The "Player choices:" sections in this script are for DESIGN REFERENCE only.

In the actual game:
- The Narrator generates ONLY the narrative text (scene description)
- Choices are generated SEPARATELY by a dedicated `generate_choices` call
- The Narrator should NEVER include numbered choices in their response

The scripts show what choices WOULD make sense at each point, but the narrator's job is just to set the scene and end with an action hook.

---

## Agent Guidelines

**Narrator Pacing Notes:**
- SETUP: Lean into the absurdity, make the goal clear
- RISING: Heist movie vibes, building pieces
- MIDPOINT: Comedy of errors, things spiral
- CLIMAX: Physical comedy, farce, timing is everything
- DENOUEMENT: Victory should feel earned and hilarious

**Keeper Notes:**
- Lower DCs overall (10-14)—we want success with style
- Failures should be funny, not devastating
- Creative solutions get bonuses
- "Rule of Funny" applies

**Jester Timing:**
- More frequent (20% chance)
- Comments on absurdity
- Breaks tension with observations
- Can appear mid-action for extra laughs
