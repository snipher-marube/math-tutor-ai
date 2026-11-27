"""Tests for prompt files: the shipped tutor prompt and the loader's checks."""

import pytest

from services.prompts import PromptError, load_prompt


def test_shipped_tutor_prompt_loads_for_every_grade():
    for grade in (1, 2, 3):
        prompt = load_prompt("tutor_system", grade=grade)
        assert f"Grade {grade}" in prompt
        assert "{" not in prompt  # every placeholder filled
        assert not any(line.lstrip().startswith("#") for line in prompt.splitlines())


def test_shipped_tutor_prompt_asks_for_the_answer_after_equals():
    # The app reads the model's answer after "=" and checks it in code.
    assert "'= <answer>'" in load_prompt("tutor_system", grade=2)


def test_shipped_tutor_prompt_is_unchanged_from_the_code_version():
    # Moving the prompt into a file must not change what the model is told.
    assert load_prompt("tutor_system", grade=2) == (
        "You are a friendly math tutor for a Kenyan Grade 2 student using the CBE curriculum. "
        "Use simple English and real-life examples like mangoes or shillings. "
        "Show your steps, then end with '= <answer>'."
    )


def _write(tmp_path, text):
    (tmp_path / "p.txt").write_text(text, encoding="utf-8")


def test_note_lines_are_removed_and_placeholders_filled(tmp_path):
    _write(tmp_path, "# a note for editors\nHello Grade {grade}.\n  # an indented note\nBye.")
    assert load_prompt("p", directory=tmp_path, grade=3) == "Hello Grade 3.\nBye."


def test_unknown_placeholder_is_an_error(tmp_path):
    _write(tmp_path, "Hello Grade {grde}.")
    with pytest.raises(PromptError, match=r"\{grde\}"):
        load_prompt("p", directory=tmp_path, grade=2)


def test_missing_or_empty_files_are_errors(tmp_path):
    with pytest.raises(PromptError, match="not found"):
        load_prompt("nope", directory=tmp_path)
    _write(tmp_path, "# only notes\n\n")
    with pytest.raises(PromptError, match="no instructions"):
        load_prompt("p", directory=tmp_path)


def test_edits_are_used_straight_away(tmp_path):
    _write(tmp_path, "First.")
    assert load_prompt("p", directory=tmp_path) == "First."
    _write(tmp_path, "Second.")
    assert load_prompt("p", directory=tmp_path) == "Second."
