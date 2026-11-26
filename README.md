# Math Tutor AI 🇰🇪

**An open-source, offline AI math tutor for Grade 2 learners in Kenya, aligned to the Competency Based Education (CBE) curriculum.**

[![CI](https://github.com/snipher-marube/math-tutor-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/snipher-marube/math-tutor-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

Many Kenyan schools and homes have little or no internet. Math Tutor AI runs a small language model **locally** (through [Ollama](https://ollama.com)), so a learner can get patient, step-by-step help with Grade 2 maths on a modest laptop, with no data bundle and no cloud account.

> **Status: early stage (v0.1).** The backend can answer questions with a local model, and the frontend is still the Vite starter page. This is a great time to get involved. See the [Roadmap](docs/ROADMAP.md).

---

## Features

- 📴 **Fully offline.** The model runs on the learner's device.
- 🧒 **Made for 7–8 year olds.** Simple English, short steps, familiar Kenyan examples (mangoes, shillings, matatus).
- 📚 **CBE-aligned.** Covers the Grade 2 Mathematics strands: Numbers, Measurement and Geometry. See [docs/CURRICULUM.md](docs/CURRICULUM.md).
- 🪶 **Lightweight.** The default model is `qwen2.5:1.5b` (about 1 GB), and you can swap in a different one.
- 🔌 **Simple API.** A FastAPI backend that any frontend (web, desktop, kiosk) can call.

## How it works

```
┌──────────────┐   HTTP    ┌──────────────────┐   HTTP   ┌──────────────┐
│ Vue frontend │ ────────▶ │ FastAPI backend  │ ───────▶ │ Ollama + LLM │
│  :5173       │ ◀──────── │  :8000           │ ◀─────── │  :11434      │
└──────────────┘   JSON    └──────────────────┘          └──────────────┘
                     all on the same machine, no internet needed
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

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

# 4. Run the backend and frontend (two terminals)
make backend     # http://localhost:8000  (API docs at /docs)
make frontend    # http://localhost:5173
```

Try it:

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
| `make backend`  | Run the API with auto-reload         |
| `make frontend` | Run the web app                      |
| `make test`     | Run backend tests (no model needed)  |
| `make lint`     | Check code style                     |
| `make format`   | Auto-format code                     |
| `make build`    | Production build of the frontend     |

## Project structure

```
math-tutor-ai/
├── backend/                 FastAPI app (Python, managed with uv)
│   ├── main.py              App entry point, CORS, health routes
│   ├── config.py            Settings (env vars / .env)
│   ├── routers/tutor.py     /api/tutor endpoints
│   ├── services/            Ollama client and prompt
│   └── tests/               Pytest tests (Ollama is mocked)
├── frontend/                Vue 3 + Vite web app
├── docs/                    Contributor and project documentation
└── .github/                 CI, issue and PR templates
```

## Documentation

| Doc | For |
| --- | --- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute: workflow, branches, commits, PRs |
| [docs/SETUP.md](docs/SETUP.md) | Detailed dev setup on Linux, macOS and Windows, plus troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the pieces fit together, and the design principles |
| [docs/API.md](docs/API.md) | Backend endpoints and configuration |
| [docs/CURRICULUM.md](docs/CURRICULUM.md) | CBE Grade 2 Mathematics scope |
| [docs/CHILD_SAFETY.md](docs/CHILD_SAFETY.md) | Rules for content, prompts and learner data |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What's planned, plus good first issues |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [SECURITY.md](SECURITY.md) | Reporting vulnerabilities |

## Contributing

You don't have to write code to help. We need:

- 👩‍🏫 **Teachers and parents** to review explanations and suggest questions.
- 🐍 **Python developers** for the backend, prompts and evaluation.
- 🎨 **Frontend developers and designers** for a child-friendly UI.
- 🌍 **Translators** for Kiswahili support.

Start with [CONTRIBUTING.md](CONTRIBUTING.md), then pick an issue labelled [`good first issue`](https://github.com/snipher-marube/math-tutor-ai/labels/good%20first%20issue).

## License

[MIT](LICENSE) © Math Tutor AI contributors.

*This project is community-built and is not affiliated with or endorsed by the Kenya Institute of Curriculum Development (KICD) or the Ministry of Education.*
