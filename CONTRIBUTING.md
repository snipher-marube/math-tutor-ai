# Contributing to Math Tutor AI

Thank you for helping Kenyan learners! 🎉 Every contribution counts, whether it's a typo fix, a better explanation of subtraction, or a new feature.

By taking part you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| You are… | You can… |
| --- | --- |
| A teacher or parent | Break CBE topics into small skills, list common mistakes children make and how you respond, check [docs/CURRICULUM.md](docs/CURRICULUM.md) against the KICD designs, and report bad tutor answers. Use the **Curriculum / learning content** issue template. No coding needed |
| A developer | Fix bugs, build features from the [Roadmap](docs/ROADMAP.md), and add tests |
| A designer | Design a simple, colourful UI for children aged 6–9, including visual tools like counters, ten-frames and number lines |
| A translator | Help add Kiswahili prompts and UI text |
| Anyone | Improve the docs, triage issues, and share the project |

## Ground rules

Read [docs/PEDAGOGY.md](docs/PEDAGOGY.md) first. It explains how the tutor teaches, and every feature should fit it.

1. **Teach, don't just answer.** Features should help a child understand, not just hand them an answer. Use the hint ladder instead of revealing answers.
2. **Maths in code.** Correct answers, mistake detection and mastery are computed in code. The AI model only handles wording, and never decides whether an answer is correct.
3. **Offline first.** Features must work without internet. Don't add calls to cloud APIs, CDNs, analytics or telemetry.
4. **Child safe.** All content and prompts must follow [docs/CHILD_SAFETY.md](docs/CHILD_SAFETY.md).
5. **Curriculum aligned.** Maths content should map to the Grades 1–3 scope in [docs/CURRICULUM.md](docs/CURRICULUM.md).
6. **Runs on modest hardware.** Assume a laptop with 4–8 GB of RAM and no GPU. Raise any new dependency or bigger model in an issue first.
7. **Small PRs.** One change per pull request. Small PRs get reviewed faster.

## Getting set up

Follow the [Quick start](README.md#quick-start) or the detailed [docs/SETUP.md](docs/SETUP.md). You don't need the model to run the tests, because Ollama is mocked.

## Workflow

1. **Find or open an issue.** Comment "I'd like to work on this" so others know. For anything large, discuss the approach in the issue before writing code.
2. **Fork** the repo and clone your fork.
3. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/short-description
   ```
   Branch prefixes: `feat/`, `fix/`, `docs/`, `content/`, `chore/`, `test/`.
4. **Make your change.** Add or update tests and docs.
5. **Check it locally:**
   ```bash
   make lint
   make test
   make build   # if you touched the frontend
   ```
6. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(tutor): add hint mode for word problems
   fix(api): return 503 when Ollama is not running
   docs: add Windows setup steps
   content(prompt): use shillings in money examples
   ```
7. **Push and open a pull request** against `main`. Fill in the PR template and link the issue (`Closes #12`).
8. **Review.** A maintainer will review, usually within a few days. CI must pass before merging.

## Coding standards

### Backend (Python)

- Python 3.12. Dependencies are managed with **uv** (`uv add <pkg>`, `uv add --dev <pkg>`). Commit `uv.lock`.
- Format and lint with **ruff** (`make format`). Config lives in `backend/pyproject.toml`.
- Use type hints on all functions. Use Pydantic models for request and response bodies.
- Keep the layers separate: `routers/` handle HTTP, `services/` hold the logic and model calls, and `config.py` holds settings.
- Tests go in `backend/tests/`. **Never call a real model in tests.** Mock `generate_tutor_response` or the Ollama client instead (see `tests/test_api.py`).

### Frontend (Vue)

- Vue 3 with `<script setup>` and Vite. Use npm and commit `package-lock.json`.
- No external fonts, CDNs or remote images. Bundle every asset so the app works offline.
- Design for children: large touch targets, high contrast, minimal text, and no ads or links to the internet.

### Teaching engine, skills and misconceptions

- Follow [docs/PEDAGOGY.md](docs/PEDAGOGY.md) and go through its contributor checklist.
- Skills live in `backend/skills/*.yaml`. See [docs/SKILLS.md](docs/SKILLS.md) for the format, and run `make skills` to check your changes.
- Every skill needs a problem generator in `backend/services/problems.py`. Run `make problems` to see samples.
- Every skill needs tests for its problem generator (answers are correct and within the skill's range) and its answer checker.
- Every misconception rule (in `backend/services/answer_checker.py`) needs a test showing the wrong answer it recognises. Feedback must be at most 20 words and kind. A test checks this.
- Hints (in `backend/services/hints.py`) must never give the answer away. Tests check that nudges and pictures never say it, and that worked examples always have a different answer.
- Mastery and review rules must be simple enough to explain to a teacher in one sentence.

### Prompts and learning content

- Prompt changes can change the tutor's behaviour a lot. In the PR, include **before and after examples** for at least 3 questions from different strands and grades.
- The AI model handles wording only. Never rely on it to produce or check a correct answer.
- Use Kenyan context: names (Wanjiru, Otieno, Kiprop, Amina), shillings (KSh), local foods, objects and places.
- Check that the maths is correct. A wrong answer is worse than no answer.

## Reporting bugs and requesting features

Use the [issue templates](https://github.com/snipher-marube/math-tutor-ai/issues/new/choose). For security problems, follow [SECURITY.md](SECURITY.md) and **don't** open a public issue.

## Labels

| Label | Meaning |
| --- | --- |
| `good first issue` | Small and well defined, a good place to start |
| `help wanted` | Maintainers would love help with this |
| `curriculum` | Maths content, prompts, or CBE alignment |
| `bug` / `enhancement` / `docs` | Type of work |

## Questions?

Open a [Discussion](https://github.com/snipher-marube/math-tutor-ai/discussions) or ask in your issue. No question is too basic.
