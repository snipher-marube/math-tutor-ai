# Architecture

## Overview

```
 Learner's device (laptop / mini PC). No internet required at runtime.
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ┌──────────────┐  POST /api/tutor/ask  ┌───────────────────────────┐ │
│  │ Vue 3 + Vite │ ───────────────────▶  │ FastAPI (backend/)        │ │
│  │ frontend/    │ ◀───────────────────  │  routers/tutor.py  (HTTP) │ │
│  │ :5173        │   {"explanation"}     │  services/         (logic)│ │
│  └──────────────┘                       │  config.py      (settings)│ │
│                                         └─────────────┬─────────────┘ │
│                                                       │ ollama client │
│                                         ┌─────────────▼─────────────┐ │
│                                         │ Ollama :11434             │ │
│                                         │  qwen2.5:1.5b (default)   │ │
│                                         └───────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

## Components

### Frontend (`frontend/`)
Vue 3 single-page app built with Vite. The learner types or picks a question, and the app shows the tutor's explanation. *(Currently the Vite starter page. Building the real UI is on the [roadmap](ROADMAP.md).)*

### Backend (`backend/`)

| File | Responsibility |
| --- | --- |
| `main.py` | Creates the FastAPI app, configures CORS, registers routers, and serves `/` and `/health` |
| `config.py` | `Settings` class (pydantic-settings). Reads env vars and `.env` |
| `routers/tutor.py` | HTTP layer: request and response models, plus the `/api/tutor/*` routes |
| `services/ollama_client.py` | Builds the system prompt and calls the local model through Ollama |
| `tests/` | Pytest suite. The model is mocked |

**Rule of thumb:** routers don't talk to Ollama directly, and services don't know about HTTP. This keeps the model swappable and the logic testable.

### Model runtime (Ollama)
Ollama serves a quantised small language model over a local HTTP API. Models are downloaded once (with internet) and then run fully offline.

## Request flow

1. The frontend sends `POST /api/tutor/ask` with `{"question": "...", "grade": 2}`.
2. `routers/tutor.py` validates the body and calls `generate_tutor_response()`.
3. The service builds a Grade 2, CBE, Kenyan-context system prompt and calls `client.chat()` on Ollama.
4. The model's text comes back as `{"explanation": "..."}`.

## Design principles

1. **Offline first.** No runtime dependency on the internet: no CDNs, cloud APIs or telemetry.
2. **Small and cheap.** Target 4–8 GB RAM CPU-only machines. Prefer models of 2B parameters or fewer.
3. **Child safe by default.** See [CHILD_SAFETY.md](CHILD_SAFETY.md). No accounts, and no personal data leaves the device.
4. **Correct over clever.** Small models make arithmetic mistakes. Where possible, compute or verify answers in code rather than trusting the model (see the roadmap).
5. **Swappable parts.** The model name, URL and grade are settings, not hard-coded values.

## Known limitations (v0.1)

- The Ollama call is synchronous inside an async route, so it blocks the event loop under concurrent use.
- There's no answer verification yet, so the model can be wrong.
- There's no conversation memory. Each question stands alone.
- There's no error handling when Ollama is down (you get a 500 instead of a friendly message).

These are all tracked in [ROADMAP.md](ROADMAP.md) and are good contributor tasks.
