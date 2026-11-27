# Math Tutor AI 🇰🇪

**An open-source, offline math tutor that helps Kenyan children in Lower Primary (Grades 1–3) *understand* maths, aligned to the Competency Based Education (CBE) curriculum.**

[![CI](https://github.com/snipher-marube/math-tutor-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/snipher-marube/math-tutor-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

Many Kenyan schools and homes have little or no internet. Math Tutor AI runs entirely **on the learner's device**, a modest laptop with no data bundle and no cloud account.

It isn't just a chatbot. A **teaching engine** written in code decides what each child should learn next, gives problems with answers it has worked out itself, spots the specific mistake a child makes, and gives hints instead of answers. A small local AI model (through [Ollama](https://ollama.com)) helps with the language: child-friendly wording, Kenyan stories and encouragement. Read **[how it teaches](docs/PEDAGOGY.md)**.

> **Status: early stage (v0.3).** The teaching engine works end to end for counting and Grade 1–2 addition: skills, problems, mistake-aware feedback, hints, mastery and "what's next". A first lesson screen lets children practise in the browser. Read-aloud, Kiswahili, more skills and the AI language layer are next. This is a great time to get involved. See the [Roadmap](docs/ROADMAP.md).

---

## How it teaches

| Principle | What it means for a child |
| --- | --- |
| 🧭 **Right level, not right grade** | A short placement check finds where they really are, so a Grade 3 child who needs Grade 1 skills starts there |
| 🪜 **Skill by skill, until mastered** | Small steps (count → add within 10 → make 10 → ...). They move on only once a skill is secure |
| 🥭 **Objects, then pictures, then numbers** | 5 mangoes + 3 mangoes, then dots on a ten-frame, then `5 + 3 = 8` |
| 💡 **Hints, not answers** | Nudge, then a picture, then a worked example, then they try again themselves |
| 🔍 **Learning from mistakes** | `7 + 5 = 75` gets help with what "+" means, not just "wrong" |
| 🔊 **Works for early readers** | Read-aloud, pictures and big buttons. Kiswahili planned |

Full details: **[docs/PEDAGOGY.md](docs/PEDAGOGY.md)**.

## Features

- 📴 **Fully offline.** Everything runs on the learner's device.
- 🧒 **Made for ages 6–9.** Simple language, short sessions, familiar Kenyan examples (mangoes, shillings, matatus).
- 📚 **CBE-aligned.** Grades 1–3 Mathematics strands: Numbers, Measurement and Geometry. See [docs/CURRICULUM.md](docs/CURRICULUM.md).
- ✅ **Maths in code.** Correct answers are always calculated in code, never trusted to the AI.
- 🪶 **Lightweight.** The default model is `qwen2.5:1.5b` (about 1 GB), and you can swap in a different one.
- 🔌 **Simple API.** A FastAPI backend that any frontend (web, desktop, kiosk) can call.

## How it works

```
┌──────────────┐   HTTP    ┌──────────────────────────┐   HTTP   ┌──────────────┐
│ Vue frontend │ ────────▶ │ FastAPI backend          │ ───────▶ │ Ollama +     │
│  :5173       │ ◀──────── │  teaching engine (code)  │ ◀─────── │ small model  │
└──────────────┘   JSON    │  + language layer        │          │  :11434      │
                           └──────────────────────────┘          └──────────────┘
                     all on the same machine, no internet needed
```

The teaching engine is planned (see the [Roadmap](docs/ROADMAP.md)). [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) shows the current system and the target design.

## Quick start

**You need:** [Python 3.12+](https://www.python.org/), [uv](https://docs.astral.sh/uv/), [Node.js 20+](https://nodejs.org/), [Ollama](https://ollama.com/download), and `make` (optional, but it makes things easier).

```bash
# 1. Clone
git clone https://github.com/snipher-marube/math-tutor-ai.git
cd math-tutor-ai

# 2. Install dependencies and create backend/.env
make setup

# 3. Download the model (one-time, needs internet, ~1 GB)
make model

# 4. Run the tutor (one process)
make start       # http://localhost:8000  ← open this to try a lesson
```

Working on the code? Run the backend and frontend separately, so changes reload as you save:

```bash
make backend     # http://localhost:8000  (API docs at /docs)
make frontend    # http://localhost:5173  ← open this while developing
```

Try a lesson problem (no AI needed):

```bash
curl -X POST http://localhost:8000/api/lesson/problems \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "add-within-20"}'
```

Then answer it, or ask for hints, using the returned `id` (see [docs/API.md](docs/API.md#lesson-api)). Or open http://localhost:8000/docs to try every endpoint in the browser.

Ask the AI a free question:

```bash
curl -X POST http://localhost:8000/api/tutor/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Wanjiru has 5 mangoes and buys 3 more. How many does she have?"}'
```

No `make`? Platform-specific steps (including Windows) are in **[docs/SETUP.md](docs/SETUP.md)**.

## Common commands

| Command         | What it does                         |
| --------------- | ------------------------------------ |
| `make setup`    | Install all dependencies             |
| `make model`    | Pull the default Ollama model        |
| `make start`    | Build the app and run it as one process on :8000 |
| `make backend`  | Run the API with auto-reload         |
| `make frontend` | Run the web app                      |
| `make test`     | Run backend tests (no model needed)  |
| `make lint`     | Check code style                     |
| `make format`   | Auto-format code                     |
| `make skills`   | Check the skill map files            |
| `make problems` | Print sample problems for each skill |
| `make build`    | Production build of the frontend     |

## Project structure

```
math-tutor-ai/
├── backend/                 FastAPI app (Python, managed with uv)
│   ├── main.py              App entry point, CORS, health routes
│   ├── config.py            Settings (env vars / .env)
│   ├── routers/lesson.py    /api/lesson endpoints (teaching engine)
│   ├── routers/learners.py  /api/learners endpoints (nicknames and progress)
│   ├── routers/tutor.py     /api/tutor endpoints (free questions, AI)
│   ├── services/            Ollama client, verifier, skill map, problems, answer checker, hints
│   ├── skills/              Skill map: one YAML file per CBE sub-strand
│   ├── data/                Local learner database (created on first run, never committed)
│   └── tests/               Pytest tests (Ollama is mocked)
├── frontend/                Vue 3 + Vite web app (learner picker and lesson screen)
├── docs/                    Contributor and project documentation
└── .github/                 CI, issue and PR templates
```

## Documentation

| Doc | For |
| --- | --- |
| [docs/PEDAGOGY.md](docs/PEDAGOGY.md) | **Start here.** How the tutor teaches, and why, plus an FAQ |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute: workflow, branches, commits, PRs |
| [docs/SETUP.md](docs/SETUP.md) | Detailed dev setup on Linux, macOS and Windows, plus troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current system, target design, and design principles |
| [docs/API.md](docs/API.md) | Backend endpoints and configuration |
| [docs/CURRICULUM.md](docs/CURRICULUM.md) | CBE Grades 1–3 Mathematics scope and skill progression |
| [docs/SKILLS.md](docs/SKILLS.md) | How to read, add and check skills (for teachers, no coding needed) |
| [docs/CHILD_SAFETY.md](docs/CHILD_SAFETY.md) | Rules for content, prompts and learner data |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What's planned, plus good first issues |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [SECURITY.md](SECURITY.md) | Reporting vulnerabilities |

## Contributing

You don't have to write code to help. We need:

- 👩‍🏫 **Teachers and parents** to break topics into skills, list common mistakes children make, and review explanations.
- 🐍 **Python developers** for the teaching engine, prompts and evaluation.
- 🎨 **Frontend developers and designers** for a child-friendly UI.
- 🌍 **Translators** for Kiswahili support.

Start with [CONTRIBUTING.md](CONTRIBUTING.md), then pick an issue labelled [`good first issue`](https://github.com/snipher-marube/math-tutor-ai/labels/good%20first%20issue).

## License

[MIT](LICENSE) © Math Tutor AI contributors.

*This project is community-built and is not affiliated with or endorsed by the Kenya Institute of Curriculum Development (KICD) or the Ministry of Education.*
