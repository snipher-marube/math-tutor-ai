# Roadmap

This is a living plan. Each item should become a GitHub issue. Items marked 🟢 are good first issues.

The plan follows [PEDAGOGY.md](PEDAGOGY.md): a **teaching engine** (written in code) drives learning, and the **AI model** helps with language. The free-question chat that exists today stays as a secondary "ask a question" mode.

## v0.2: Foundations
- [x] Project setup, contributor docs and CI
- [x] Free-question endpoint (`POST /api/tutor/ask`) with answer verification in code
- [x] 🟢 Backend: return a friendly `503` when Ollama is unreachable, instead of a 500
- [x] 🟢 Backend: use `ollama.AsyncClient` so requests don't block the event loop
- [x] 🟢 Backend: configurable `OLLAMA_TIMEOUT` that returns a friendly `504`
- [x] 🟢 Validate input: limit question length and reject empty strings
- [x] Document the teaching approach ([PEDAGOGY.md](PEDAGOGY.md)) and widen scope to Grades 1–3
- [ ] Move the system prompt into its own file (`backend/prompts/`) so non-developers can edit it

## v0.3: Teaching engine (no AI needed)
- [x] Skill map format (data files) with prerequisites, plus the first skills: Grade 1–2 addition ([SKILLS.md](SKILLS.md))
- [x] Problem generator per skill. Every problem has a correct answer computed in code
- [x] Answer checker with misconception detection for addition (see the table in [PEDAGOGY.md](PEDAGOGY.md#5-learn-from-wrong-answers-misconceptions))
- [x] Hint ladder per problem kind: nudge, picture, worked example
- [x] Lesson API: new problem, check answer, get hints ([API.md](API.md#lesson-api))
- [x] Learners and progress stored locally (SQLite), with view, reset and delete
- [x] Mastery rules, and choosing each learner's next skill
- [ ] Placement check to find each learner's starting level
- [ ] Spaced review of mastered skills
- [ ] 🟢 Add subtraction skills and misconceptions
- [ ] 🟢 Add skills for other sub-strands (money, time, shapes, ...)

## v0.4: Child-friendly app
- [ ] Replace the Vite starter page with the lesson screen: one problem, big number buttons, instant feedback
- [ ] Visual tools: counters, ten-frames, number line, base-ten blocks, Kenyan coins
- [ ] Hint ladder in the UI
- [ ] Read-aloud with offline text-to-speech
- [ ] Rewards for effort and progress (stars, a skill path)
- [ ] 🟢 "Ask a question" screen that uses `POST /api/tutor/ask`, with a loading state

## v0.5: AI language layer and reach
- [ ] AI writes Kenyan word problems from generated sums. Code checks the numbers
- [ ] AI re-explains in simpler words. Varied, warm feedback
- [ ] Kiswahili prompts, audio and UI
- [ ] Teacher and parent view: progress per skill, suggested groups
- [ ] Evaluation set: 100+ problems with answers across all strands and grades (`backend/eval/`)
- [ ] 🟢 Script to run the eval set against a model and report how well it follows the rules
- [ ] "Ask a question" mode: AI turns word problems into a sum, code calculates and checks the answer
- [ ] Compare small models (qwen2.5 0.5b/1.5b, llama3.2:1b, gemma3:1b) and document the results
- [ ] Fine-tune a small model on teacher-reviewed explanations (only after the evaluation set exists, and never on learner data). See the [FAQ](PEDAGOGY.md#will-the-model-be-fine-tuned-on-what-children-type)

## v1.0: Deployable and proven
- [ ] One-command install (Docker Compose and/or packaged installers)
- [ ] Run on low-cost hardware (Raspberry Pi 5 / old laptops) and document the performance
- [ ] Serve the built frontend from FastAPI, so there's only one process to run
- [ ] Field testing in real Grade 1–3 classrooms, with pre- and post-checks per skill

Have an idea? Open a [feature request](https://github.com/snipher-marube/math-tutor-ai/issues/new/choose).
