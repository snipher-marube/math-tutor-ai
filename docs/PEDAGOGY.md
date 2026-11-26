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

A child moves to the next skill only after **showing mastery**. The rule, simple enough to explain to a teacher in one sentence:

> **A skill is mastered when at least 4 of the learner's last 5 problems were answered correctly on the first try, on at least 2 different days.**

- **Only the first answer to each problem counts.** Getting it right after a hint or a second try is good learning, but it doesn't show mastery yet.
- **Two different days** shows the skill has stuck, not just been remembered for one session. Days are counted in **local time** (`TIMEZONE`, `Africa/Nairobi` by default).
- **Only the latest 5 problems count**, so if a child starts getting a skill wrong again, it goes back to *practising*.
- The tutor then offers the **next skill**: the first one in teaching order that isn't mastered yet and whose prerequisites all are. A new learner starts at the first skill. A placement check is planned, so that learners can start at their real level.

Mastery is per skill, not per grade. The rule is in `backend/services/mastery.py`.

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

For example, a child stuck on `9 + 4 = ?`:

| Step | The child hears | The screen shows |
| --- | --- | --- |
| Nudge | "Make 10 first. How many more does 9 need to make 10?" | — |
| Picture | "Fill the ten-frame first. Then count the dots that are left over." | A ten-frame with 9 dots, plus 4 more |
| Worked example | "Here's one I solved. Now you try yours the same way." | `8 + 7`: 8 needs 2 more to make 10. Take 2 from 7, that leaves 5. 10 + 5 = 15 |

Rules the code enforces, with tests:
- Hints use the problem's **own numbers** ("Start at 6…", not "Start at the first number…").
- The nudge and picture **never say the answer**.
- The worked example is a **different problem of the same kind, using the same strategy, with a different answer**. Showing `8 + 4 = 12` to a child stuck on `7 + 5` would give their answer away.
- When the answer checker recognises a mistake, the ladder **starts at the step it suggests**, often the picture.

The ladder is built in `backend/services/hints.py`.

### 5. Learn from wrong answers (misconceptions)
A wrong answer tells us *what* the child doesn't understand yet. The answer checker recognises common patterns and responds to the actual mistake:

| Problem | Wrong answer | Likely misconception | Response | Status |
| --- | --- | --- | --- | --- |
| 7 + 5 | 75 | Joins the digits instead of adding | Count objects. Revisit what "+" means | Built |
| 6 + 3 | 8 | Counts the starting number when counting on | Number line: start *on* 6, then jump 3 | Built |
| 27 + 15 | 32 | Forgets the ten made by the ones | Base-ten blocks: swap 10 ones for 1 ten | Built |
| 27 + 15 | 312 | Writes the ones total without regrouping | Base-ten blocks: swap 10 ones for 1 ten | Built |
| 23 + 14 | 10 | Adds every digit as ones | Place-value chart: tens under tens | Built |
| 23 + 14 | 73 | Writes the digits of the answer backwards | Point to the tens place and the ones place | Built |
| 4 + ? = 10 | 14 | Adds the numbers shown instead of finding the missing part | Ten-frame: show the gap | Built |
| 52 − 17 | 45 | Subtracts the smaller digit from the bigger one in each column | Base-ten blocks: break a ten into ones | Planned |
| ½ of 8 | 2 | Confuses "half" with "quarter" | Share 8 mangoes between 2 children | Planned |

The built rules, with their feedback, are in `backend/services/answer_checker.py`, alongside rules for counting, number order and place value. This list will grow, and teachers are the best people to add to it.

**How a mistake is matched:** the checker only looks at the problem and the child's answer. Rules are tried in order, and the first match wins. If no rule matches, the answer is simply marked wrong, and the tutor moves to the next hint-ladder step. A rule must recognise a mistake children really make, so "one less than the answer" only means *counted the starting number* for small, single-digit sums. In `58 + 18`, an answer of 75 is just a slip.

### 6. Short sessions, quick feedback, regular review
- Sessions of **10–15 minutes**.
- Feedback **immediately** after each answer.
- **Spaced review:** skills already mastered come back every few days, so they aren't forgotten.
- **Praise effort and strategy** ("You kept trying!", "You used the number line!"), not ability ("You're so smart").

### 7. Built for children who can't read well yet
- **Read everything aloud** with offline text-to-speech. The question is read when it appears, feedback after each answer, and each hint as it opens. A 🔊 button repeats the question, and maths is spoken as a teacher would say it ("6 plus what equals 10").
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
- **"Ask me a maths question" mode:** the existing free-question chat (`/api/tutor/ask`). This stays as a secondary mode, kept on maths topics. The AI turns the question into a sum and explains it, and code calculates and checks the answer where possible (see the [FAQ](#what-happens-if-a-child-asks-a-question-the-system-doesnt-know)).

## How we will know it works

- **Automated:** tests for every skill's generator, checker and misconception rules. An evaluation set to measure how well the AI's wording follows the rules.
- **With learners:** short pre- and post-checks per skill during field testing with real classrooms. The question is always "did the child learn?", not "did the child enjoy chatting?"

## Frequently asked questions

### Are the answers already stored somewhere?
No. Each skill holds a **recipe**, not a list of questions. For "add within 20", the recipe is: pick two numbers whose sum is 20 or less, and the answer is their sum. Each time a problem is needed, the code picks new numbers (say 8 and 5) and calculates the answer (13). The variety is effectively endless, and every answer is correct because it was calculated, not guessed.

### What happens if a child asks a question the system doesn't know?
That depends on the mode:

- **Lesson mode (the main experience):** the tutor asks the questions and the child answers. Every question comes from the engine, so there are no "unknown" questions.
- **"Ask a question" mode:** the child types or says their own question. This mode **uses the AI model**, so open questions still get a helpful answer. The work is split:
  1. **The AI translates.** It turns a word problem ("Wanjiru has 5 mangoes and buys 3 more") into a sum: `5 + 3`.
  2. **The code calculates.** It works out `8` and checks the AI's explanation against it.
  3. **If the code can't check it** (for example, a "why" question about shapes), the AI still answers, and the answer is marked as unchecked.
  4. **If the question is above Grade 3, or not about maths,** the tutor gently says so and steers back.

Today the verifier only checks questions written with symbols ("What is 14 + 5?"). Having the AI turn word problems into sums is on the [roadmap](ROADMAP.md).

### So is the AI being removed?
No. The AI is given the job it's good at, **language**, and kept away from the job it's bad at, **reliable arithmetic**.

### Will the tutor keep learning over time?
Yes, in three different ways:

| Kind of learning | How it happens | Where |
| --- | --- | --- |
| **It learns each child** | The engine records what each child has mastered, which mistakes they repeat, and what needs review, and picks tomorrow's problems from that | On the device. No model training |
| **The project gets better** | Teachers add skills, common mistakes, hints and explanations as data files | In this repository. Every learner benefits from the next update |
| **The AI model gets better** | Fine-tuning a small model on teacher-reviewed examples, so its wording is simpler, warmer and more Kenyan | Done by maintainers, offline, and shipped as a normal update |

### Will the model be fine-tuned on what children type?
No. The model **never learns live from children**:

- **Safety.** Children's input could teach it wrong or unsafe things.
- **Privacy.** Training on children's data would mean sending it off the device, which breaks our [privacy rules](CHILD_SAFETY.md#data-and-privacy).
- **Hardware.** The laptops we target can't train models.

Fine-tuning data will come from examples written or approved by teachers. Two more rules apply:

- **It needs a test first.** We'll fine-tune only after the evaluation set exists, so we can prove the new model is actually better.
- **The maths stays in code.** Fine-tuning improves wording, not arithmetic. Even a fine-tuned small model can get sums wrong.

## Checklist for contributors

Before opening a PR that affects learning, ask:

- [ ] Does this help a child **understand**, or just give them an answer?
- [ ] Is every correct answer computed in **code**?
- [ ] Does it work for a child who **can't read well**?
- [ ] Does it follow the **hint ladder** instead of revealing answers?
- [ ] Is the content **CBE-aligned** (see [CURRICULUM.md](CURRICULUM.md)) and **child safe** (see [CHILD_SAFETY.md](CHILD_SAFETY.md))?
- [ ] Does it still work **fully offline**?
