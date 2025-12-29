# The Last Bridge

**Genre:** Heroic Fantasy
**Tone:** Epic, sacrifice, triumph against odds
**Adventure Length:** ~35-45 turns (quest-driven ending)

---

## Adventure Pacing Guide

This script demonstrates a complete adventure arc using the 50-turn pacing system.

| Phase | Turns | Focus |
|-------|-------|-------|
| **SETUP** | 1-5 | Quest hook, meet allies, reach the bridge |
| **RISING_ACTION** | 6-20 | Prepare defenses, first skirmishes, build tension |
| **MID_POINT** | 21-30 | Major battle, allies fall, stakes escalate |
| **CLIMAX** | 31-42 | Grukk's challenge, final confrontation |
| **DENOUEMENT** | 43+ | Victory aftermath, epilogue |

---

## SETUP PHASE (Turns 1-5)

### Opening — Turn 1

**Innkeeper Theron:**
> Orc warband hit the valley. Three hundred strong, moving fast. They'll reach Millbrook by nightfall.

> There's one bridge over the Gorge. If someone holds it long enough for the villagers to evacuate...

> I'm not going to lie. This might be a one-way trip. But those are good people. Kids. Families.

> The garrison's a day out. You'd need to hold for maybe an hour.

> You in?

*[PACING: ESTABLISH - Introduce the stakes and the quest]*

---

### NPCs

**Warden Kess (she/her):** Militia leader. Tough, practical. Will fight beside you.

**Old Tam (he/him):** Retired soldier. Knows the bridge. Knows he's too old, offers anyway.

**Grukk (they/them):** Orc warleader. Respects strength. Might parley if impressed.

---

### Scene 1: The Bridge — Turns 2-5

**Narrator:**
> The bridge spans the Gorge like a dare, twenty feet of ancient stone over three hundred feet of nothing. Wind howls up from the river below, carrying spray and the promise of a long fall.

> Kess arrives with twelve militia. Farmers holding spears they've never used, fear in their eyes and something harder underneath. They're not running.

> Old Tam rests a hand on the weathered railing. "Could collapse it," he says. "Drop the whole thing into the Gorge. But not while anyone's still on it."

> Behind you, the sounds of a village emptying. Ahead, dust rises on the horizon like a stormcloud with teeth.

*[PACING: Build anticipation, establish environment and allies]*

---

## RISING_ACTION PHASE (Turns 6-20)

### Scene 2: First Wave — Turns 6-12

**Narrator:**
> Twenty orcs crest the hill, their war cries rolling across the valley like thunder. Arrows first, dark shapes arcing against the sky. Then the charge, boots shaking the earth.

> But the bridge is narrow. They can only come three at a time.

**Keeper:**
> Waves of 3. Hold the line: 10. Push back: 12. Each miss costs one militia.

**Narrator:**
> The first orc reaches you, axe raised, mouth open in a scream that ends suddenly. Bodies tumble into the abyss. The second wave hesitates.

> Across the gap, Grukk watches. They haven't moved. They're measuring you.

*[PACING: ESCALATE - First combat, establish the pattern, show the enemy leader observing]*

---

### Scene 2b: Holding the Line — Turns 13-20

**Narrator:**
> Wave after wave crashes against your defense. The militia learns to fight or falls trying. Blood stains the ancient stones. Each victory costs a little more.

> Old Tam takes an arrow meant for Kess. He doesn't get up.

> "Keep fighting," he whispers. "Make it count."

*[PACING: Increasing stakes, losses mount, emotional weight builds]*

---

## MID_POINT PHASE (Turns 21-30)

### Scene 3: The Revelation — Turns 21-25

**Narrator:**
> Third wave, and you're painting the stones red, yours and theirs. Half the militia is down or dying. But behind you, Kess signals: the villagers are almost clear.

> A horn sounds from the orc lines. The attack pauses.

> Grukk steps onto the bridge. Alone. The warband falls silent.

*[PACING: REVEAL - Major shift as the enemy leader enters directly]*

---

### Scene 3b: The Challenge — Turns 26-30

**Narrator:**
> "You fight well." Their voice carries over the wind. "My warriors speak of the demon on the bridge. I came to see for myself."

> They plant their axe in the stone. "Single combat. You win, we leave. I win, we walk over what's left of you."

> The warband waits. The militia waits. The wind waits.

**Player choices:**

1. Accept the duel
2. Refuse, keep fighting
3. Try to negotiate

*[PACING: The twist—a chance to end this without more death, but at great risk]*

---

## CLIMAX PHASE (Turns 31-42)

### Scene 4: The Duel — Turns 31-38

**If duel accepted:**

**Keeper:**
> Three rounds. You swing, they swing. Best of three. Grukk's tough but fair.

**Narrator:**
> Steel meets steel over the abyss, each blow echoing off the canyon walls. Grukk is strong, faster than they look, but you've been fighting for an hour and you're still standing.

> The first clash. The second. Blood on both blades now.

*[PACING: INTENSIFY - Maximum tension, everything on the line]*

---

### Scene 4b: Victory or Defeat — Turns 39-42

*Win:*

**Narrator:**
> Grukk falls to one knee, blood streaming from a wound they didn't see coming. They look up at you, and there's something like a smile on their face.

> "Well fought."

> The warband withdraws. The bridge holds.

*[PACING: The decisive moment—quest completion triggers epilogue]*

---

## DENOUEMENT PHASE (Turns 43-50)

### Epilogue — Turns 43+

**Narrator:**
> Millbrook survives. They name a feast day after you, carve your likeness into the bridge stone, tell stories that grow taller with each telling.

> Kess finds you at the tavern a week later, slides a drink across the bar.

> "The Warden position's open," she says. "If you're tired of adventures."

> Outside, the bridge stands. It'll stand for a hundred years, they say. And they'll tell your story the whole time.

*[PACING: RESOLVE - Honor the sacrifice, celebrate victory, hint at future]*

---

## Jester Moments

*Turn 8:*
> "One bridge. Three hundred orcs. Twelve farmers. This is fine."

*Turn 32:*
> "The orc warleader just challenged you to single combat. Your left leg is bleeding pretty good. No pressure."

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
- SETUP: Paint the desperate situation vividly, make allies memorable
- RISING: Combat should feel exhausting, each wave harder than the last
- MIDPOINT: Grukk's arrival should feel like a turning point
- CLIMAX: Every blow matters, describe with intensity
- DENOUEMENT: Earned rest, celebration, legacy

**Keeper Notes:**
- Early combat: DC 10-12, manageable
- Mid combat: DC 12-14, challenging
- Duel: DC 14-16, dramatic
- Track militia losses to raise stakes

**Jester Timing:**
- Appears during tense buildups (15% chance)
- Never during the actual duel
- Can appear in aftermath for comic relief
