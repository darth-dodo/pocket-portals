# High Noon at Dustwater

**Genre:** Fantasy Western
**Tone:** Gritty, tense, frontier justice
**Adventure Length:** ~35-45 turns (building to showdown)

---

## Adventure Pacing Guide

Western stories build tension toward an inevitable confrontation. The pacing mirrors classic showdown structure.

| Phase | Turns | Focus |
|-------|-------|-------|
| **SETUP** | 1-5 | Ride into town, meet the oppressed, survey the enemy |
| **RISING_ACTION** | 6-20 | Gather allies, weaken the gang, earn trust |
| **MID_POINT** | 21-30 | Confrontation escalates, point of no return |
| **CLIMAX** | 31-42 | The showdown, high noon |
| **DENOUEMENT** | 43+ | Town saved, new dawn |

---

## SETUP PHASE (Turns 1-5)

### Opening — Turn 1

**Innkeeper Theron:**
> Mining town called Dustwater, three days' ride east. Silver strike brought people in. The Vance gang followed.

> They've been bleeding the town dry for months. Protection money. Beatings. Last week they killed the sheriff.

> The townsfolk pooled everything they have. Eighty gold for whoever drives the Vances out.

> Six gang members. One of you. Interested?

*[PACING: ESTABLISH - Classic western setup, lone hero against many]*

---

### NPCs

**Doc Mira (she/her):** Town healer. Lost her husband to the gang. Steady hands, cold eyes.

**Silas Vance (he/him):** Gang leader. Fast draw. Enjoys making examples.

**Coyote (they/them):** Vance's second. Having doubts. Might turn with the right push.

---

### Scene 1: Dustwater — Turns 2-5

**Narrator:**
> Dust coats everything here—your clothes, your teeth, the memories of better days. The sun beats down like it's got a grudge, and the main street stretches empty except for tumbleweeds and ghosts.

> Laughter drifts from the saloon. The Vances, taking what they want because no one's left to stop them.

> Doc Mira meets you behind the general store, checking over her shoulder with every word. "They killed my husband for looking at Silas wrong. They'll kill you for coming here at all."

> She shows you the layout: back door to the saloon, water tower with a clear shot, dynamite in the mine shed if you're feeling dramatic.

> How do you want this to go?

*[PACING: Survey the battlefield, establish stakes and options]*

---

## RISING_ACTION PHASE (Turns 6-20)

### Scene 2: Building Pressure — Turns 6-12

**Narrator:**
> The town watches from behind shuttered windows. They've learned to be invisible. But you see curtains twitch, eyes following as you move through empty streets.

> A miner catches your arm in the general store. "Coyote's been talking," he whispers. "Says Silas is getting reckless. Says maybe it's time for a change."

> Could be useful. Could be a trap.

**Keeper:**
> Read Coyote's intent: DC 14. Success reveals they're genuine.

*[PACING: ESCALATE - Weaken the enemy, build alliances]*

---

### Scene 2b: Drawing Lines — Turns 13-20

**If approaching Coyote:**

**Narrator:**
> You find them at the well at midnight, filling canteens. Their hand drops to their iron, then stops.

> "You're either brave or stupid," Coyote says. "Silas killed the last person who tried to take him. Made us all watch."

> They look toward the saloon. "But I've been watching him too. Getting sloppy. Getting cruel for cruel's sake."

> "When it goes down, I won't be standing with him. That's all I'm promising."

*[PACING: Recruiting, shifting the odds]*

---

## MID_POINT PHASE (Turns 21-30)

### Scene 3: Confrontation — Turns 21-27

**If direct approach:**

**Narrator:**
> The saloon doors swing open and the laughter dies. Six faces turn toward you, cards frozen mid-deal, bottles halfway to lips. Silas Vance sits in the back, boots on the table, a smile spreading across his face like an oil slick.

> "New meat." He doesn't bother standing. "You here to pay tribute or to bleed?"

> His hand rests near his iron. So do the others.

**Keeper:**
> Stare them down: 14. One folds. Otherwise, it gets loud.

*[PACING: REVEAL - Declaring your intentions, point of no return]*

---

### Scene 3b: Bodies Fall — Turns 28-30

**If stealth approach:**

**Keeper:**
> Stay quiet: 12. Miss and they hear you coming.

**Narrator:**
> Three down before anyone realizes death's come to Dustwater. But Silas finds you near the stables, gun already drawn, that smile still in place.

> "Clever. I've killed clever before."

*[PACING: Thinning the herd, building toward the inevitable]*

---

## CLIMAX PHASE (Turns 31-42)

### Scene 4: High Noon — Turns 31-38

**Narrator:**
> Just you and Silas now. Main street. Noon sun hammering down like a judgment. The town watches from behind shuttered windows, holding its breath.

> He spits tobacco into the dust. "I'll give you one chance. Walk away. Tell people the Vance gang can't be touched."

> His fingers twitch.

**Keeper:**
> Speed counts. Highest roll draws first.
> Win: you're faster.
> Tie: both hit.
> Lose: he's faster. One shot left.

*[PACING: INTENSIFY - The classic showdown, everything on the line]*

---

### Scene 4b: The Draw — Turns 39-42

*If Coyote was turned:*

**Narrator:**
> A shadow moves in the alley behind Silas. Coyote steps into the light, gun leveled at their former boss.

> "It's over, Silas."

> He turns. That's all the opening you need.

*Success:*

**Narrator:**
> The gunshot echoes off the buildings, rolling out across the desert like a final word. Silas Vance falls in the dust, staring at the sky, that smile finally gone.

> Silence. Then a door opens. Then another. The town emerges, blinking in the sunlight, like they're seeing it for the first time.

*[PACING: Quest complete—the villain falls, epilogue triggers]*

---

## DENOUEMENT PHASE (Turns 43-50)

### Epilogue — Turns 43+

**Narrator:**
> They bury Silas outside town, unmarked. Nobody wants to remember where.

> Doc Mira presses the gold into your hand, her grip stronger than you expected. "Stay awhile," she says. "We could use a sheriff."

> The sun sets red over the desert. The town is quiet.

> First peace it's had in months.

> Maybe you'll stay. Maybe you'll ride on. Either way, Dustwater remembers.

*[PACING: RESOLVE - Justice served, town saved, choice of what comes next]*

---

## Jester Moments

*Turn 3:*
> "Six gang members. One of you. The math is definitely mathing here."

*Turn 26:*
> "Silas Vance has killed eleven people. You're supposed to be number twelve. Just contextualizing."

*Turn 35:*
> "This is a classic standoff. Two gunslingers. One street. Zero cover. Who designed this town?"

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
- SETUP: Dry, dusty, oppressive atmosphere
- RISING: Tension building, small victories
- MIDPOINT: Lines drawn, no going back
- CLIMAX: Sparse description, every second counts
- DENOUEMENT: Relief, gratitude, earned rest

**Keeper Notes:**
- Combat should be lethal and quick
- Single rolls decide fate (western genre)
- Coyote turn should feel earned
- High noon showdown: one dramatic roll

**Jester Timing:**
- Gallows humor only
- Comments on ridiculous odds
- Never during the actual showdown
- Can appear in aftermath
