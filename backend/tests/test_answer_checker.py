"""Tests for the answer checker and its misconception rules."""

import random

import pytest

from services.answer_checker import RULES, check_answer
from services.problems import Problem, generate_problem
from services.skill_map import load_skill_map

SKILL_MAP = load_skill_map()


def _p(kind: str, operands: tuple[int, ...], answer: int) -> Problem:
    return Problem("test-skill", kind, "?", operands, answer)


def _mistake(problem: Problem, given: int) -> str | None:
    result = check_answer(problem, given)
    assert not result.correct
    return result.misconception.id if result.misconception else None


# --- Each mistake is recognised from a real example -----------------------------


@pytest.mark.parametrize(
    ("problem", "given", "expected"),
    [
        # Addition
        (_p("add", (7, 5), 12), 75, "joined-digits"),
        (_p("add", (27, 15), 42), 32, "forgot-to-regroup"),
        (_p("add", (27, 15), 42), 312, "wrote-ones-sum"),
        (_p("add", (23, 14), 37), 10, "added-all-digits"),
        (_p("add", (23, 14), 37), 73, "reversed-digits"),
        (_p("add", (6, 3), 9), 8, "counted-start"),
        (_p("add", (6, 3), 9), 10, "counted-extra"),
        (_p("add", (30, 40), 70), 7, "added-all-digits"),  # tens treated as ones
        # Make 10 (missing addend)
        (_p("missing-addend", (4, 10), 6), 14, "missing-added-instead"),
        (_p("missing-addend", (4, 10), 6), 10, "missing-gave-total"),
        (_p("missing-addend", (4, 10), 6), 4, "missing-gave-part"),
        (_p("missing-addend", (4, 10), 6), 5, "counted-start"),
        # Counting
        (_p("count", (7,), 7), 8, "miscounted"),
        (_p("count", (7,), 7), 6, "miscounted"),
        (_p("number-after", (39,), 40), 38, "wrong-direction"),
        (_p("number-after", (39,), 40), 39, "repeated-number"),
        (_p("number-before", (24,), 23), 25, "wrong-direction"),
        (_p("number-before", (24,), 23), 32, "reversed-digits"),
        # Place value
        (_p("count-tens", (47,), 4), 7, "swapped-tens-ones"),
        (_p("count-tens", (47,), 4), 47, "gave-whole-number"),
        (_p("count-ones", (47,), 7), 4, "swapped-tens-ones"),
        (_p("compose-number", (3, 4), 34), 7, "added-tens-and-ones"),
        (_p("compose-number", (3, 4), 34), 43, "reversed-digits"),
    ],
)
def test_recognises_mistake(problem, given, expected):
    assert _mistake(problem, given) == expected


# --- Wrong for an unknown reason ------------------------------------------------


@pytest.mark.parametrize(
    ("problem", "given"),
    [
        (_p("add", (7, 5), 12), 40),
        (_p("add", (58, 18), 76), 75),  # a slip in a big sum, not counting on
        (_p("add", (40, 10), 50), 51),
        (_p("missing-addend", (4, 10), 6), 9),
    ],
)
def test_unknown_mistakes_have_no_misconception(problem, given):
    assert _mistake(problem, given) is None


def test_reversed_digits_ignores_single_digits_and_round_tens():
    assert _mistake(_p("add", (2, 3), 5), 50) is None  # 5 can't be reversed
    assert _mistake(_p("number-after", (39,), 40), 4) is None  # 40 -> 04 is not a reversal


def test_unknown_kind_is_still_marked():
    assert check_answer(_p("not-a-kind", (1,), 1), 1).correct
    assert check_answer(_p("not-a-kind", (1,), 1), 2).misconception is None


# --- Safety properties over every generated problem -----------------------------


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_correct_answers_are_always_correct(skill):
    rng = random.Random(3)
    for _ in range(1000):
        problem = generate_problem(skill, rng)
        result = check_answer(problem, problem.answer)
        assert result.correct and result.misconception is None


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_wrong_answers_are_always_wrong(skill):
    rng = random.Random(4)
    for _ in range(100):
        problem = generate_problem(skill, rng)
        for given in range(0, 120):
            if given != problem.answer:
                assert not check_answer(problem, given).correct


def test_every_problem_kind_has_rules():
    rng = random.Random(5)
    kinds = {generate_problem(s, rng).kind for s in SKILL_MAP for _ in range(50)}
    assert kinds <= RULES.keys(), f"no rules for: {kinds - RULES.keys()}"


# --- Feedback quality -----------------------------------------------------------

ALL_MISCONCEPTIONS = {m.id: m for rules in RULES.values() for m, _ in rules}


@pytest.mark.parametrize("m", ALL_MISCONCEPTIONS.values(), ids=lambda m: m.id)
def test_feedback_is_short_and_kind(m):
    words = m.feedback.split()
    assert len(words) <= 20, "a 6-9 year old should hear one or two short sentences"
    assert m.teacher_note
    for harsh in ("wrong", "no!", "bad", "silly", "careless"):
        assert harsh not in m.feedback.lower()
