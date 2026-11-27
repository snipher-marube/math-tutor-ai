"""Prompts for the AI model, kept in plain text files in `backend/prompts/`.

Teachers and parents can edit the wording without touching Python. Lines that
start with `#` are notes for editors and are removed. `{name}` placeholders are
filled in from the values passed to `load_prompt`; an unknown placeholder is an
error, so a typo like `{grde}` is caught instead of reaching the model.
"""

from __future__ import annotations

import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


class PromptError(Exception):
    """The prompt file is missing, empty, or has placeholders that can't be filled."""


def load_prompt(name: str, directory: Path = PROMPTS_DIR, **values: object) -> str:
    """Read `<directory>/<name>.txt`, drop `#` note lines, and fill in `{placeholders}`.

    The file is read on every call, so edits are used straight away.
    """
    path = directory / f"{name}.txt"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PromptError(f"Prompt file not found: {path}") from None

    text = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))
    text = text.strip()
    if not text:
        raise PromptError(f"Prompt file {path.name} has no instructions (only notes or blank)")

    unknown = sorted({m for m in _PLACEHOLDER.findall(text) if m not in values})
    if unknown:
        names = ", ".join(f"{{{u}}}" for u in unknown)
        raise PromptError(f"Prompt file {path.name} uses unknown placeholders: {names}")

    return _PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), text)
