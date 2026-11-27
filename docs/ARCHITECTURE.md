# Architecture

This page describes the system **as it is today** and the **target design** we're building toward. The reasons behind the target design are in [PEDAGOGY.md](PEDAGOGY.md).

## Target design

A teaching engine written in code drives learning. The small AI model is a helper for language only.

```
 Learner's device (laptop / mini PC). No internet required at runtime.
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌───────────────────┐        ┌──────────────────────────────────────┐  │
│  │ Vue frontend      │  HTTP  │ FastAPI backend                      │  │
│  │ • lesson screen   │ ─────▶ │                                      │  │
│  │ • visual tools    │ ◀───── │  Lesson engine                       │  │
│  │ • read-aloud      │        │   ├─ skill map (data files)          │  │
│  │ • ask a question  │        │   ├─ problem generator   (code)      │  │
│  └───────────────────┘        │   ├─ answer checker +                │  │
│                               │   │  misconception rules (code)      │  │
│                               │   ├─ hint ladder                     │  │
│                               │   └─ mastery + review    (code)      │  │
│                               │                                      │  │
│                               │  Learner progress ── SQLite (local)  │  │
│                               │                                      │  │
│                               │  Language layer ──▶ Ollama + small   │  │
│                               │  (wording, stories,     model        │  │
│                               │   free questions)                    │  │
│                               └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Planned components

| Component | Responsibility | Status |
| --- | --- | --- |
| Skill map | Ordered skills per CBE sub-strand, with prerequisites, stored as data files teachers can review | Built: `skills/*.yaml`, `services/skill_map.py` ([SKILLS.md](SKILLS.md)) |
| Problem generator | Creates problems for a skill. The correct answer is computed in code | Built: `services/problems.py` |
| Answer checker | Marks answers and recognises common misconceptions | Built: `services/answer_checker.py` |
| Hint ladder | Nudge, then picture, then worked example, then a new try | Built: `services/hints.py` |
| Learner progress | Mastery per skill and review schedule, stored locally in SQLite | Built: `services/db.py`, `services/learners.py`, `services/mastery.py`, `services/review.py` |
| Lesson API | Next problem, submit answer, get hint | Built: `routers/lesson.py` ([API.md](API.md#lesson-api)) |
| Language layer | The AI model writes word problems, re-explains, and encourages. It never decides correctness | Partly built: `services/ollama_client.py` |
| Free-question mode | `POST /api/tutor/ask`: a secondary "ask a question" mode | Built |

See [ROADMAP.md](ROADMAP.md) for the order of work.

## Current system (v0.2)

Today the backend has two modes: the **lesson API** (the teaching engine, no AI) and the **free-question mode** (AI). The frontend has a learner picker and a lesson screen that use the lesson and learner APIs.

```
┌──────────────┐  /api/lesson/*        ┌──────────────────────────────┐
│ Vue 3 + Vite │ ───────────────────▶  │ FastAPI (backend/)           │
│ frontend/    │ ◀───────────────────  │  routers/lesson.py           │──▶ skill map, problems,
│ :5173        │                       │                              │    answer checker, hints
│              │  /api/tutor/ask       │  routers/tutor.py            │──▶ Ollama :11434
│              │ ───────────────────▶  │                              │    (qwen2.5:1.5b)
└──────────────┘                       └──────────────────────────────┘
```

### Backend files

| File | Responsibility |
| --- | --- |
| `main.py` | Creates the FastAPI app, configures CORS, registers routers, serves `/health`, and serves the built web app at `/` |
| `frontend.py` | Serves `frontend/dist` after the API routes, so the tutor runs as one process (`make start`) |
| `config.py` | `Settings` class (pydantic-settings). Reads env vars and `.env` |
| `routers/lesson.py` | HTTP layer for the teaching engine: `/api/lesson/*` (skills, problems, answers, hints) |
| `routers/learners.py` | HTTP layer for learners: `/api/learners/*` (create, list, progress, next skill, reviews, reset, delete) |
| `routers/placement.py` | HTTP layer for the placement check: start, answer, latest result |
| `dependencies.py` | Shared FastAPI dependencies (database, stores). Tests swap in a temporary database |
| `routers/tutor.py` | HTTP layer for free questions: request validation, response models, and `/api/tutor/*` |
| `services/ollama_client.py` | Calls the local model through Ollama with the system prompt, with timeout and error handling |
| `services/prompts.py` | Loads prompt files from `prompts/`: drops `#` note lines, fills `{grade}`, and rejects unknown placeholders |
| `prompts/tutor_system.txt` | The tutor's instructions to the model. Plain text that teachers can edit |
| `services/math_verifier.py` | Works out the answer to simple arithmetic questions in code and checks the model's answer |
| `services/skill_map.py` | Loads and checks the skill map in `skills/*.yaml` |
| `services/problems.py` | One problem generator per skill. Answers are computed in code |
| `services/answer_checker.py` | Marks an answer and names the likely mistake, with child feedback and a hint step |
| `services/hints.py` | Builds the hint ladder for a problem: nudge, picture (a visual for the frontend) and worked example |
| `services/db.py` | The local SQLite database: one file, created on first start. Tables: `learners`, `problems`, `attempts`, `placements`, `placement_problems` |
| `services/problem_store.py` | Saves problems handed out and every answer, so answers are checked on the server |
| `services/learners.py` | Learners (nickname and avatar only) and per-skill progress, with reset and delete |
| `services/mastery.py` | The mastery rule and choosing a learner's next skill |
| `services/review.py` | Spaced review: when each mastered skill should come back |
| `services/placement.py` | The adaptive placement check: which skill to ask next, and when to stop |
| `services/placement_store.py` | Saves placement checks and their results |
| `skills/` | Skill map data files, one per CBE sub-strand ([SKILLS.md](SKILLS.md)) |
| `tests/` | Pytest suite. The model is always faked |

**Rule of thumb:** routers don't talk to Ollama directly, and services don't know about HTTP. This keeps the model swappable and the logic testable. The lesson engine will follow the same rule.

### Request flow (free-question mode)

1. The frontend sends `POST /api/tutor/ask` with `{"question": "...", "grade": 2}`.
2. `routers/tutor.py` validates the body and calls `generate_tutor_response()`.
3. The service loads the system prompt from `prompts/tutor_system.txt` for the learner's grade and awaits `AsyncClient.chat()` on Ollama, so other requests keep being served while the model thinks.
4. `math_verifier.verify()` checks the model's final answer against a calculation in code.
5. The response contains the explanation plus the verification result.

## Design principles

1. **Teach, don't just answer.** Features should help a child understand. See [PEDAGOGY.md](PEDAGOGY.md).
2. **Maths in code, language in the model.** Correct answers, mistake detection and mastery are computed in code. The AI model only handles wording.
3. **Offline first.** No runtime dependency on the internet: no CDNs, cloud APIs or telemetry.
4. **Small and cheap.** Target 4–8 GB RAM CPU-only machines. Prefer models of 2B parameters or fewer.
5. **Child safe by default.** See [CHILD_SAFETY.md](CHILD_SAFETY.md). No accounts, and no personal data leaves the device.
6. **Swappable parts.** The model name, URL, timeout and default grade are settings, not hard-coded values.

## Known limitations (v0.2)

- The lesson screen has no Kiswahili or rewards yet. Read-aloud needs an English voice installed on the device.
- The verifier only checks questions written with symbols ("What is 14 + 5?"), not word problems.
- Free questions have no conversation memory. Each question stands alone.
- Free questions are not yet kept on maths. Tested on `qwen2.5:1.5b`, the model doesn't reliably follow prompt rules about staying on topic or not asking personal questions, and stricter wording made it refuse real maths. A check in code, before the model is called, is planned.

These are tracked in [ROADMAP.md](ROADMAP.md).
