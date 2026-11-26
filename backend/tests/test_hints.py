"""Tests for the hint ladder.

The most important rule: hints help the child think, they never give the answer away.
"""

import random
import re

import pytest

from services.answer_checker import check_answer
from services.hints import STEPS, hint_ladder
from services.problems import Problem, generate_problem
from services.skill_map import load_skill_map

SKILL_MAP = load_skill_map()
VISUAL_TYPES = {"objects", "ten-frame", "number-line", "base-ten"}


def _numbers_in(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"\d+", text)}


def _ladders(skill, runs=300):
    rng = random.Random(11)
    for _ in range(runs):
        problem = generate_problem(skill, rng)
        yield problem, hint_ladder(problem, skill, rng)


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_ladder_has_three_steps_in_order(skill):
    for _, ladder in _ladders(skill, runs=50):
        assert [h.step for h in ladder] == list(STEPS)
        assert all(h.text.strip() for h in ladder)


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_nudge_and_picture_never_say_the_answer(skill):
    for problem, ladder in _ladders(skill):
        already_shown = _numbers_in(problem.question) | set(problem.operands)
        if problem.answer in already_shown:
            continue  # e.g. "5 + ? = 10": the 5 is in the question anyway
        for hint in ladder[:2]:
            assert problem.answer not in _numbers_in(hint.text), (problem, hint.text)


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_picture_has_a_known_visual(skill):
    for _, ladder in _ladders(skill, runs=50):
        visual = ladder[1].visual
        assert visual is not None and visual.type in VISUAL_TYPES
        assert all(isinstance(v, int) and v >= 0 for v in visual.params.values())


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_worked_example_is_a_different_problem_of_the_same_kind(skill):
    for problem, ladder in _ladders(skill):
        example = ladder[2].example
        assert example is not None
        assert example.problem.skill_id == problem.skill_id
        assert example.problem.kind == problem.kind
        assert example.problem.answer != problem.answer, "would give the answer away"
        assert str(example.problem.answer) in example.steps[-1], "example should finish solved"


def test_worked_example_uses_the_same_strategy():
    """A child stuck on a make-10 sum should see a make-10 example, not counting on."""
    skill = SKILL_MAP.get("add-within-20")
    problem = Problem(skill.id, "add", "8 + 5 = ?", (8, 5), 13)
    example = hint_ladder(problem, skill, random.Random(1))[2].example
    assert "make 10" in example.steps[0]


def test_start_skips_earlier_steps():
    skill = SKILL_MAP.get("add-within-10")
    problem = generate_problem(skill, random.Random(1))
    assert [h.step for h in hint_ladder(problem, skill, start="picture")] == [
        "picture",
        "worked-example",
    ]
    assert [h.step for h in hint_ladder(problem, skill, start="worked-example")] == [
        "worked-example"
    ]


def test_answer_checker_suggestion_sets_the_start():
    skill = SKILL_MAP.get("add-within-100-with-regrouping")
    problem = Problem(skill.id, "add", "27 + 15 = ?", (27, 15), 42)
    mistake = check_answer(problem, 32).misconception  # forgot to regroup
    ladder = hint_ladder(problem, skill, random.Random(1), start=mistake.hint)
    assert ladder[0].step == "picture"
    assert ladder[0].visual.type == "base-ten"


def test_same_seed_gives_same_ladder():
    skill = SKILL_MAP.get("make-10")
    problem = generate_problem(skill, random.Random(1))
    assert hint_ladder(problem, skill, random.Random(9)) == hint_ladder(
        problem, skill, random.Random(9)
    )


@pytest.mark.parametrize(
    ("problem", "nudge"),
    [
        (Problem("add-within-10", "add", "", (6, 3), 9), "Start at 6. Count on 3 more."),
        (Problem("add-within-10", "add", "", (2, 7), 9), "Start at 7. Count on 2 more."),
        (Problem("make-10", "missing-addend", "", (4, 10), 6), "Start at 4. Count up to 10."),
        (Problem("count-to-100", "number-after", "", (39,), 40), "Say 39, then count up"),
    ],
)
def test_nudges_use_the_problems_own_numbers(problem, nudge):
    skill = SKILL_MAP.get(problem.skill_id)
    assert hint_ladder(problem, skill, random.Random(1))[0].text.startswith(nudge)
