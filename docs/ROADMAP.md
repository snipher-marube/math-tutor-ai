# Roadmap

This is a living plan. Each item should become a GitHub issue. Items marked 🟢 are good first issues.

## v0.2: Usable MVP
- [ ] Child-friendly chat UI in `frontend/` that replaces the Vite starter page (big buttons, large fonts, colourful)
- [ ] 🟢 Frontend: call `POST /api/tutor/ask` and show a loading state
- [x] 🟢 Backend: return a friendly `503` when Ollama is unreachable, instead of a 500
- [x] 🟢 Backend: use `ollama.AsyncClient` so requests don't block the event loop
- [ ] 🟢 Validate input: limit question length and reject empty strings
- [ ] Move the system prompt into its own file (`backend/prompts/`) so non-developers can edit it

## v0.3: Correctness and curriculum
- [ ] Evaluation set: 100+ Grade 2 questions with answers across all strands (`backend/eval/`)
- [ ] 🟢 Script to run the eval set against a model and report accuracy
- [ ] Verify arithmetic answers in Python and correct or flag the model
- [ ] Practice mode: the tutor generates questions per sub-strand and checks the learner's answers
- [ ] Hints mode: give a hint first, then the full solution on request
- [ ] Compare small models (qwen2.5 0.5b/1.5b, llama3.2:1b, gemma3:1b) and document the results

## v0.4: Reach
- [ ] Kiswahili prompts and UI
- [ ] Text-to-speech for learners who are still learning to read (offline TTS)
- [ ] Simple local progress tracking per sub-strand (stays on the device)
- [ ] Teacher or parent view

## v1.0: Deployable
- [ ] One-command install (Docker Compose and/or packaged installers)
- [ ] Run on low-cost hardware (Raspberry Pi 5 / old laptops) and document the performance
- [ ] Serve the built frontend from FastAPI, so there's only one process to run
- [ ] Field testing with real Grade 2 classrooms and teachers

Have an idea? Open a [feature request](https://github.com/snipher-marube/math-tutor-ai/issues/new/choose).
