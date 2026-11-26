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
| Answer checker | Marks answers and recognises common misconceptions | Planned (v0.3) |
| Hint ladder | Nudge, then picture, then worked example, then a new try | Planned (v0.3) |
| Learner progress | Mastery per skill and review schedule, stored locally in SQLite | Planned (v0.3) |
| Lesson API | Next problem, submit answer, get hint | Planned (v0.3) |
| Language layer | The AI model writes word problems, re-explains, and encourages. It never decides correctness | Partly built: `services/ollama_client.py` |
| Free-question mode | `POST /api/tutor/ask`: a secondary "ask a question" mode | Built |

See [ROADMAP.md](ROADMAP.md) for the order of work.

## Current system (v0.2)

Today the backend provides the free-question mode only. The frontend is still the Vite starter page.

```
┌──────────────┐  POST /api/tutor/ask  ┌───────────────────────────┐        ┌───────────────┐
│ Vue 3 + Vite │ ───────────────────▶  │ FastAPI (backend/)        │ ─────▶ │ Ollama :11434 │
│ frontend/    │ ◀───────────────────  │  routers/tutor.py  (HTTP) │ ◀───── │ qwen2.5:1.5b  │
│ :5173        │  explanation +        │  services/  (logic, model)│        └───────────────┘
└──────────────┘  verification         │  config.py      (settings)│
                                       └───────────────────────────┘
```

### Backend files

| File | Responsibility |
| --- | --- |
| `main.py` | Creates the FastAPI app, configures CORS, registers routers, and serves `/` and `/health` |
| `config.py` | `Settings` class (pydantic-settings). Reads env vars and `.env` |
| `routers/tutor.py` | HTTP layer: request validation, response models, and the `/api/tutor/*` routes |
| `services/ollama_client.py` | Builds the system prompt and calls the local model through Ollama, with timeout and error handling |
| `services/math_verifier.py` | Works out the answer to simple arithmetic questions in code and checks the model's answer |
| `services/skill_map.py` | Loads and checks the skill map in `skills/*.yaml`. Not used by an endpoint yet |
| `services/problems.py` | One problem generator per skill. Answers are computed in code. Not used by an endpoint yet |
| `skills/` | Skill map data files, one per CBE sub-strand ([SKILLS.md](SKILLS.md)) |
| `tests/` | Pytest suite. The model is always faked |

**Rule of thumb:** routers don't talk to Ollama directly, and services don't know about HTTP. This keeps the model swappable and the logic testable. The lesson engine will follow the same rule.

### Request flow (free-question mode)

1. The frontend sends `POST /api/tutor/ask` with `{"question": "...", "grade": 2}`.
2. `routers/tutor.py` validates the body and calls `generate_tutor_response()`.
3. The service builds a CBE, Kenyan-context system prompt for the learner's grade and awaits `AsyncClient.chat()` on Ollama, so other requests keep being served while the model thinks.
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

- No teaching engine yet. The only mode is free questions, which gives answers rather than teaching.
- The verifier only checks questions written with symbols ("What is 14 + 5?"), not word problems.
- No conversation memory or learner progress. Each question stands alone.

These are tracked in [ROADMAP.md](ROADMAP.md).
