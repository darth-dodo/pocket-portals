# The Tide That Remembers

**Genre:** Cosmic Horror
**Tone:** Creeping dread, unknowable forces
**Adventure Length:** ~40-50 turns (horror builds slowly)

---

## Adventure Pacing Guide

Cosmic horror requires a slow burn. The pacing system ensures dread builds properly before the terrible climax.

| Phase | Turns | Focus |
|-------|-------|-------|
| **SETUP** | 1-5 | Journey to Saltmere, wrongness established |
| **RISING_ACTION** | 6-20 | Investigation, gather clues, sanity frays |
| **MID_POINT** | 21-30 | See the truth, understand the cost |
| **CLIMAX** | 31-42 | The choice, confronting the unknowable |
| **DENOUEMENT** | 43+ | The price paid, what remains |

---

## SETUP PHASE (Turns 1-5)

### Opening — Turn 1

**Innkeeper Theron:**
> Fishing village called Saltmere sent a rider yesterday. Made it halfway here before his horse died. Made it to my door before he did.

> Last thing he said: "The tide came in wrong."

> Nobody who's gone to check has come back. Magistrate's paying a hundred gold for answers.

*[PACING: ESTABLISH - Hook with mystery, hint at wrongness without revealing]*

---

### NPCs

**Elder Maren (she/her):** Protects her village. Made a deal with something in the water, years ago.

**Finnick (he/him):** Lighthouse keeper. Counts everything. It keeps him sane.

---

### Scene 1: The Village — Turns 2-5

**Narrator:**
> The coast road winds along cliffs that plunge into churning gray nothing. Saltmere appears through the rain like a memory you can't quite place, and the silence hits you before the smell does.

> Doors hang open on empty hinges. Food rots on tables set for meals no one ate. The only sound is the waves, rhythmic and wrong, like breathing.

> Seventeen survivors huddle in the chapel, faces turned toward the altar where Elder Maren stands. None of them look at you when you enter.

> "You shouldn't have come," Maren says. Her voice is steady, but her hands aren't. "When the tide goes out, it takes things. Memories. Names. People. And when it comes back..."

> Somewhere outside, a child begins to sing. A song with no words.

**Keeper:**
> Keep your head. 13 to resist.

*Fail:* Your feet move before you decide. One step toward the door. Then another.

*[PACING: Establish the wrongness, hint at the supernatural threat]*

---

## RISING_ACTION PHASE (Turns 6-20)

### Scene 2: Investigation — Turns 6-12

**Narrator:**
> The village reveals its secrets reluctantly. Empty cribs with no children. Mirrors covered with cloth. Names scratched out of family bibles.

> "It started three weeks ago," a fisherman whispers. "Nets came up full of fish with too many eyes. Then the fog came. Then the singing."

> In the tavern cellar, you find a journal. Pages torn out, ink running like tears. One entry remains legible: "It remembers us. It remembers everything we tried to forget."

*[PACING: ESCALATE - Build mystery, each clue more disturbing]*

---

### Scene 2b: The Lighthouse — Turns 13-20

**Narrator:**
> Finnick opens on the twelfth knock. His eyes skip past you, counting the stones in the path, the drops of rain on the rail, the seconds between waves.

> "The light keeps it confused," he says, fingers tapping a rhythm on the doorframe. "Keeps it from finding the shore. But the oil..." He laughs, or maybe sobs. "I keep counting. It keeps being less."

> From the lighthouse gallery, you can see the whole bay. The water looks like water. It moves like water.

> But something beneath the surface moves differently. Something with too many angles.

**Keeper:**
> Look away. 15 to manage it. Miss and it costs you. 1d4 sanity.

*[PACING: The horror glimpsed, the countdown begins]*

---

## MID_POINT PHASE (Turns 21-30)

### Scene 3: The Truth — Turns 21-25

**Narrator:**
> In Elder Maren's cottage, a locked chest beneath the floorboards. Inside, a book bound in something that was never leather, and a contract written in ink that moves when you're not watching.

> "I was young," Maren says from the doorway. Her voice is ancient now. "The village was starving. It offered a trade—prosperity for memories. Small ones at first. Then bigger."

> "It's hungry now. It wants everything."

*[PACING: REVEAL - The twist, understanding what must be paid]*

---

### Scene 3b: The Price — Turns 26-30

**Narrator:**
> The tide rises as you speak. Not water anymore. Something thicker. Something that remembers.

> Faces appear in the waves. The missing villagers. They're still smiling.

> Maren's hands shake as she turns the pages. "There's a way to send it back. Someone has to forget. Everything. Who they are. Who they loved. All of it, fed to the tide."

> She looks toward the chapel where her people wait.

> "I made the deal. I'll pay for it. Unless you know another way."

**Player choices:**

1. Let Maren sacrifice herself
2. Find another solution
3. Try to fight it

*[PACING: The impossible choice presented]*

---

## CLIMAX PHASE (Turns 31-42)

### Scene 4: The Confrontation — Turns 31-38

**If attempting to fight:**

**Keeper:**
> It cannot be killed. Only bargained with. DC 18 to even look at it without losing yourself.

**Narrator:**
> You face the tide, and the tide faces back. A thousand eyes, a million memories, an infinite hunger. It knows your name. It knows everything you've ever forgotten.

> It offers a trade.

*[PACING: INTENSIFY - Horror at maximum, choices narrow]*

---

### Scene 4b: The Sacrifice — Turns 39-42

*If Maren chosen:*

**Narrator:**
> She walks into the water at first light, the waves parting around her like a greeting. The thing rises to meet her, and for one endless moment you see it clearly, all of it, forever.

> Then she speaks, and the world goes quiet.

> You try to remember what she said. You can't. You try to remember her face. You can't.

*[PACING: The terrible price paid—quest completion triggers epilogue]*

---

## DENOUEMENT PHASE (Turns 43-50)

### Epilogue — Turns 43+

**Narrator:**
> The survivors remember nothing of the past week. No one remembers Elder Maren at all. When you ask about her cottage, they look at you strangely. There's never been a cottage there.

> In the sand at the tideline, you find a locket with a face you don't recognize.

> You keep it anyway.

> The tide comes in normally now. Just water. Just waves.

> But sometimes, at night, you hear a song with no words. And for a moment, you remember... something.

*[PACING: RESOLVE - The cost lingers, some things lost forever]*

---

## Jester Moments

*Turn 7:*
> "Following the creepy child's voice toward dark water. This is a completely normal thing that normal people do."

*Turn 23:*
> "The eldritch book is bound in something that 'was never leather.' I'm going to think about literally anything else now."

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
- SETUP: Wrongness should be atmospheric, not explicit
- RISING: Each discovery more unsettling, build dread slowly
- MIDPOINT: The revelation should feel inevitable yet terrible
- CLIMAX: Describe the unknowable without fully defining it
- DENOUEMENT: Loss should feel permanent, questions unanswered

**Keeper Notes:**
- Sanity mechanics: Track mental toll
- Early DCs lower (10-13), climbing to impossible (18+)
- Fighting the horror should feel futile
- Make bargaining feel like the only option

**Jester Timing:**
- Nervous humor only—never break the dread
- Appears less frequently (10% in horror scenarios)
- Comments on absurdity of investigating eldritch threats
