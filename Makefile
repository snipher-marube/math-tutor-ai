# Common developer tasks. Run `make help` to list them.
.PHONY: help setup model backend frontend start test lint format build skills problems

OLLAMA_MODEL ?= qwen2.5:1.5b

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend and frontend dependencies
	cd backend && uv sync
	cd frontend && npm ci
	@test -f backend/.env || cp backend/.env.example backend/.env

model: ## Download the default local model with Ollama
	ollama pull $(OLLAMA_MODEL)

backend: ## Run the API on http://localhost:8000 (auto-reload)
	cd backend && uv run fastapi dev main.py

frontend: ## Run the web app on http://localhost:5173
	cd frontend && npm run dev

test: ## Run backend and frontend tests
	cd backend && uv run pytest
	cd frontend && npm test

lint: ## Check backend code style
	cd backend && uv run ruff check . && uv run ruff format --check .

format: ## Auto-format backend code
	cd backend && uv run ruff check --fix . && uv run ruff format .

skills: ## Check the skill map files and list skills in teaching order
	cd backend && uv run python -m services.skill_map

problems: ## Print sample problems for every skill
	cd backend && uv run python -m services.problems

build: ## Build the frontend for production
	cd frontend && npm run build

start: build ## Build the app and run everything on http://localhost:8000 (one process)
	cd backend && uv run fastapi run main.py --host 127.0.0.1 --port 8000
