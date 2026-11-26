# How Math Tutor AI teaches

> **Read this before building any feature.** It explains *why* the project is built the way it is. If a feature doesn't help a child understand maths better, it doesn't belong here.

## The goal

Help Kenyan learners in **Lower Primary (Grades 1–3)**, aged about 6–9, **understand** maths, not just get answers. A child should leave each session able to do something they couldn't do before, and know *why* it works.

## Why not just a chatbot?

A chatbot that answers questions *feels* helpful, but it doesn't reliably teach young children:

- **Getting an answer is not learning.** Children aged 6–9 learn by doing: handling objects, trying, getting quick feedback, and practising until it sticks. Reading a finished explanation does very little.
- **Small offline models are unreliable teachers.** A ~1.5B model makes arithmetic mistakes, drifts off the curriculum, and has no memory of what a particular child struggles with.
- **Many young learners can't read well yet.** A text chat box shuts out exactly the children who need the most help.

So Math Tutor AI is built around a **teaching engine**, and the AI model is one helper inside it.

## The core design: the engine teaches, the AI helps with language

```
 Skill map (written and reviewed by teachers, per CBE sub-strand)
        │
        ▼
 Lesson engine ── decides WHAT to teach next and HOW
   • placement check   • mastery tracking   • review of old skills
        │
        ├─▶ Problem generator (code)  → every problem has a known correct answer
        ├─▶ Answer checker (code)     → spots WHICH mistake was made, not just right or wrong
        ├─▶ Hint ladder               → nudge, then picture, then worked example
        └─▶ Small AI model (language) → child-friendly wording, Kenyan stories, encouragement
        │
        ▼
 Child's screen: tappable objects, big buttons, read-aloud audio, praise
```

| Job | Done by | Why |
| --- | --- | --- |
| Choosing the next skill and problem | Lesson engine (code) | Must follow the curriculum and the child's progress |
| Working out the correct answer | Code | Must always be right |
| Recognising the child's mistake | Code (misconception rules) | Must be consistent and testable |
| Deciding when a skill is mastered | Code (mastery rules) | Must be predictable and explainable to teachers |
| Wording, stories, encouragement, re-explaining | AI model | Language is what the model is good at |

**Rule:** the AI model never decides whether an answer is correct, and never invents the numbers in a problem without code checking them.

## Teaching principles

### 1. Skill map and mastery
Each CBE sub-strand is broken into **small skills**, each with prerequisites. For example, for addition:

```
count to 20 → add within 10 → make 10 → add within 20 → add tens → add tens and ones → add with regrouping
```

A child moves to the next skill only after **showing mastery**: for example, at least 4 of the last 5 answers correct, on at least two different days. Mastery is per skill, not per grade.

### 2. Teach at the right level, not the right grade
Many Grade 3 learners are still working at a Grade 1 level in maths. A short, friendly **placement check** finds where each child really is, and the engine starts them there. This is the idea behind **Teaching at the Right Level (TaRL)**, one of the best-evidenced approaches in education research, used widely in Kenya and across Africa.

### 3. Concrete → Pictorial → Abstract (CPA)
Show maths before writing it:

| Stage | Example for 5 + 3 |
| --- | --- |
| Concrete | Tap and move 5 mangoes, then 3 more, and count them all |
| Pictorial | A ten-frame with 5 dots and 3 dots, or jumps on a number line |
| Abstract | `5 + 3 = 8` |

Visual tools to build: counters, ten-frames, number lines, base-ten blocks (tens and ones), Kenyan coins and notes, clocks, and shapes.

### 4. Hints, not answers (the hint ladder)
When a child is stuck or wrong, the tutor **does not give the answer**. It climbs a ladder, one step at a time:

1. **Nudge:** "Start at 5. Count on 3 more."
2. **Picture:** the counters or number line appear.
3. **Worked example:** a *similar* problem is solved step by step.
4. **Try again:** a new problem of the same kind, so the child does it themselves.

### 5. Learn from wrong answers (misconceptions)
A wrong answer tells us *what* the child doesn't understand yet. The answer checker recognises common patterns and responds to the actual mistake:

| Problem | Wrong answer | Likely misconception | Response |
| --- | --- | --- | --- |
| 7 + 5 | 75 | Joins the digits instead of adding | Count objects. Revisit what "+" means |
| 52 − 17 | 45 | Subtracts the smaller digit from the bigger one in each column | Base-ten blocks: break a ten into ones |
| 6 + 3 | 8 | Counts the starting number when counting on | Number line: start *on* 6, then jump 3 |
| 23 + 14 | 127 or 64 | Mixes up tens and ones | Place-value chart: tens under tens |
| ½ of 8 | 2 | Confuses "half" with "quarter" | Share 8 mangoes between 2 children |

This list will grow. Teachers are the best people to add to it.

### 6. Short sessions, quick feedback, regular review
- Sessions of **10–15 minutes**.
- Feedback **immediately** after each answer.
- **Spaced review:** skills already mastered come back every few days, so they aren't forgotten.
- **Praise effort and strategy** ("You kept trying!", "You used the number line!"), not ability ("You're so smart").

### 7. Built for children who can't read well yet
- **Read everything aloud** with offline text-to-speech.
- **Pictures before text.** Keep words to a minimum.
- **Answer by tapping** big number buttons or objects, not typing.
- **Kiswahili** alongside English.
- Large touch targets, high contrast, and a calm design without clutter.

### 8. Kenyan context
Use names like Wanjiru, Otieno, Kiprop and Amina. Use shillings (KSh), mandazi, sukuma wiki, matatus, the market, and school items. Children understand faster when the story is familiar.

### 9. Visible progress for teachers and parents
A simple per-skill view, for example "Amina has mastered *add within 10* and is working on *make 10*," so a teacher can group learners and plan lessons.

## Where the AI model fits

The model adds value where language matters:

- **Word problems:** turning a known sum (from the generator) into a short Kenyan story. Code checks that the story uses the right numbers.
- **Re-explaining** in simpler words, or in Kiswahili.
- **Varied, warm feedback**, so the app doesn't feel robotic.
- **"Ask me a maths question" mode:** the existing free-question chat (`/api/tutor/ask`). This stays as a secondary mode, kept on maths topics, with answers verified in code where possible.

## How we will know it works

- **Automated:** tests for every skill's generator, checker and misconception rules. An evaluation set to measure how well the AI's wording follows the rules.
- **With learners:** short pre- and post-checks per skill during field testing with real classrooms. The question is always "did the child learn?", not "did the child enjoy chatting?"

## Checklist for contributors

Before opening a PR that affects learning, ask:

- [ ] Does this help a child **understand**, or just give them an answer?
- [ ] Is every correct answer computed in **code**?
- [ ] Does it work for a child who **can't read well**?
- [ ] Does it follow the **hint ladder** instead of revealing answers?
- [ ] Is the content **CBE-aligned** (see [CURRICULUM.md](CURRICULUM.md)) and **child safe** (see [CHILD_SAFETY.md](CHILD_SAFETY.md))?
- [ ] Does it still work **fully offline**?
