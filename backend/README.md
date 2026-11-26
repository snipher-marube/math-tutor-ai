# Backend

FastAPI service that sends learner questions to a local model through Ollama.

```bash
uv sync
cp .env.example .env
uv run fastapi dev main.py   # http://localhost:8000/docs
uv run pytest                # tests (model is mocked)
uv run ruff check . && uv run ruff format .
```

See [../docs/API.md](../docs/API.md) for endpoints and configuration, and [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for how the code is organised.
