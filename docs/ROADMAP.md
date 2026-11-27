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
- [x] Move the system prompt into its own file (`backend/prompts/tutor_system.txt`) so non-developers can edit it
- [ ] Keep free questions on maths in code: questions with no numbers get a friendly redirect without calling the model, and replies are kept short

## v0.3: Teaching engine (no AI needed)
- [x] Skill map format (data files) with prerequisites, plus the first skills: Grade 1–2 addition ([SKILLS.md](SKILLS.md))
- [x] Problem generator per skill. Every problem has a correct answer computed in code
- [x] Answer checker with misconception detection for addition (see the table in [PEDAGOGY.md](PEDAGOGY.md#5-learn-from-wrong-answers-misconceptions))
- [x] Hint ladder per problem kind: nudge, picture, worked example
- [x] Lesson API: new problem, check answer, get hints ([API.md](API.md#lesson-api))
- [x] Learners and progress stored locally (SQLite), with view, reset and delete
- [x] Mastery rules, and choosing each learner's next skill
- [x] Placement check to find each learner's starting level
- [x] Spaced review of mastered skills
- [x] Subtraction skills (Grades 1–2), misconceptions, hints and take-away pictures
- [ ] 🟢 Add skills for other sub-strands (money, time, shapes, ...)

## v0.4: Child-friendly app
- [x] Replace the Vite starter page with the lesson screen: one problem, big number buttons, instant feedback
- [x] Visual tools: counters, ten-frames, number line, base-ten blocks
- [x] Friendly emoji to count (mangoes, goats, balls...), tapped one by one to count them
- [ ] Visual tools: Kenyan coins, and moving counters (not just tapping)
- [x] Hint ladder in the UI
- [x] Frontend test setup (Vitest), with tests for read-aloud text and focus handling
- [x] Component tests (Vue Test Utils, happy-dom) for the number pad, visuals, lesson, placement and learner screens
- [x] Read-aloud with on-device text-to-speech (question, feedback and hints)
- [ ] Read-aloud in Kiswahili
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
- [x] Serve the built frontend from FastAPI, so there's only one process to run (`make start`)
- [ ] Field testing in real Grade 1–3 classrooms, with pre- and post-checks per skill

Have an idea? Open a [feature request](https://github.com/snipher-marube/math-tutor-ai/issues/new/choose).
