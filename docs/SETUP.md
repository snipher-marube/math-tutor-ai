# Development setup

This guide takes you from a fresh machine to a running tutor. If you have `make`, the [Quick start in the README](../README.md#quick-start) is shorter.

## 1. Prerequisites

| Tool | Version | Why | Install |
| --- | --- | --- | --- |
| Git | any | Source control | https://git-scm.com |
| Python | 3.12+ | Backend | https://www.python.org/downloads/ (uv can also install it for you) |
| uv | latest | Python package manager | https://docs.astral.sh/uv/getting-started/installation/ |
| Node.js | 20+ (22 LTS recommended) | Frontend | https://nodejs.org |
| Ollama | latest | Runs the model locally | https://ollama.com/download |
| make | any | Optional shortcuts | Preinstalled on Linux and macOS. On Windows, use WSL or the manual commands below |

**Hardware:** 4 GB of RAM minimum, 8 GB recommended, and about 2 GB of free disk space for the default model. No GPU needed.

## 2. Get the code

```bash
git clone https://github.com/<your-username>/math-tutor-ai.git   # your fork
cd math-tutor-ai
git remote add upstream https://github.com/snipher-marube/math-tutor-ai.git
```

## 3. Backend

```bash
cd backend
uv sync                    # creates .venv and installs dependencies + dev tools
cp .env.example .env       # Windows PowerShell: Copy-Item .env.example .env
uv run fastapi dev main.py # http://localhost:8000
```

Open http://localhost:8000/docs for the interactive API docs.

## 4. The model (Ollama)

```bash
ollama pull qwen2.5:1.5b   # one-time download, about 1 GB
ollama list                # check that it's installed
```

Ollama runs as a background service on port `11434`. If it isn't running, start it with `ollama serve`.

**Trying other models:** set `OLLAMA_MODEL` in `backend/.env`. Small models worth comparing include `qwen2.5:0.5b` (faster, weaker), `llama3.2:1b` and `gemma3:1b`. If you find one that works better for Lower Primary learners, open an issue with example outputs.

## 5. Frontend

```bash
cd frontend
npm ci
npm run dev                # http://localhost:5173
```

Open http://localhost:5173, make a learner card, and try a lesson. Vite sends `/api` requests to the backend on port 8000. If your backend runs elsewhere, start Vite with `VITE_API_TARGET=http://localhost:8001 npm run dev`.

## Run the tutor as one app

For a classroom or family device, you don't need two terminals. Build the web app once, and the backend serves it:

```bash
make start                 # builds the app, then http://localhost:8000
```

Without `make`:

```bash
cd frontend && npm run build
cd ../backend && uv run fastapi run main.py --host 127.0.0.1 --port 8000
```

Open http://localhost:8000. After pulling new code, run `make start` again so the app is rebuilt.

**Other devices:** the tutor only listens on this computer (`127.0.0.1`). There are no logins, so anyone who can reach it can see and reset learners' progress. Only use `--host 0.0.0.0` (for example, to let tablets in a classroom connect) on a network you trust, such as a school's own Wi-Fi with no internet guests.

## 6. Run the checks

```bash
cd backend
uv run pytest              # tests (no model needed)
uv run ruff check .        # lint
uv run ruff format .       # format
```

```bash
cd frontend
npm run build
```

These are the same checks that CI runs on every pull request.

## Keeping your fork up to date

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `503 Cannot reach Ollama` on `/api/tutor/ask` | Ollama isn't running. Run `ollama serve`, and check `OLLAMA_BASE_URL` in `.env` |
| `503 Model ... is not installed` | Run `ollama pull qwen2.5:1.5b`, or set `OLLAMA_MODEL` to a model shown by `ollama list` |
| Browser shows a CORS error | Add your frontend URL to `CORS_ORIGINS` in `backend/.env` (it takes a JSON list) |
| `ModuleNotFoundError` when running the backend | Run commands from inside `backend/` with `uv run ...` |
| `504 The tutor took longer than ... seconds` | The machine is slow or the model is still loading. Retry, raise `OLLAMA_TIMEOUT` in `.env`, or use a smaller model |
| Responses are very slow | Try a smaller model (`qwen2.5:0.5b`) and close other heavy apps. The first request is slower while the model loads |
| `uv: command not found` | Install uv (see the link above), then restart your terminal |
| Want to start fresh with no learners | Stop the backend and delete `backend/data/`. It's recreated, empty, on the next start. This deletes **all** learner data on the device |
