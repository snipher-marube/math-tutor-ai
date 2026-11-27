"""Tests for the problem generators.

Each generator makes thousands of problems, and every one is checked:
the answer is right, the numbers stay inside the skill's range from the YAML,
and the problem really practises that skill.
"""

import random

import pytest

import services.problems as problems
from services.problems import (
    Problem,
    generate_problem,
    has_generator,
    skills_without_generators,
)
from services.skill_map import load_skill_map

SKILL_MAP = load_skill_map()
RUNS = 2000


def _many(skill_id: str, runs: int = RUNS) -> list[Problem]:
    skill = SKILL_MAP.get(skill_id)
    rng = random.Random(42)
    return [generate_problem(skill, rng) for _ in range(runs)]


def _expected_answer(p: Problem) -> int:
    """Recalculate the answer independently from the problem's kind and numbers."""
    match p.kind:
        case "add":
            return sum(p.operands)
        case "subtract":
            a, b = p.operands
            return a - b
        case "missing-addend":
            a, target = p.operands
            return target - a
        case "count":
            return p.operands[0]
        case "number-after":
            return p.operands[0] + 1
        case "number-before":
            return p.operands[0] - 1
        case "count-tens":
            return p.operands[0] // 10
        case "count-ones":
            return p.operands[0] % 10
        case "compose-number":
            tens, ones = p.operands
            return tens * 10 + ones
    raise AssertionError(f"unknown kind {p.kind!r}")


# --- Every shipped skill --------------------------------------------------------


def test_every_shipped_skill_has_a_generator():
    assert skills_without_generators(SKILL_MAP) == []


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_answers_are_correct_and_in_range(skill):
    lo, hi = skill.numbers.min, skill.numbers.max
    for p in _many(skill.id):
        assert p.skill_id == skill.id
        assert p.answer == _expected_answer(p), p
        for n in (*p.operands, p.answer):
            assert lo <= n <= hi, f"{p} has {n} outside {lo}-{hi}"
        assert p.question.strip()


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_problems_vary(skill):
    distinct = {(p.question, p.operands) for p in _many(skill.id, runs=200)}
    assert len(distinct) >= 5, f"only {len(distinct)} different problems"


@pytest.mark.parametrize("skill", list(SKILL_MAP), ids=lambda s: s.id)
def test_same_seed_gives_same_problems(skill):
    first = [generate_problem(skill, random.Random(7)) for _ in range(10)]
    second = [generate_problem(skill, random.Random(7)) for _ in range(10)]
    assert first == second


# --- Each problem really practises its skill ------------------------------------


def test_add_within_10_uses_two_positive_numbers():
    for p in _many("add-within-10"):
        assert p.kind == "add"
        assert all(n >= 1 for n in p.operands)


def test_make_10_always_targets_10():
    for p in _many("make-10"):
        a, target = p.operands
        assert target == 10 and 1 <= a <= 9


def test_add_within_20_bridges_through_10_with_single_digits():
    for p in _many("add-within-20"):
        assert all(1 <= n <= 9 for n in p.operands)
        assert p.answer > 10


def test_add_tens_only_uses_whole_tens():
    for p in _many("add-tens"):
        assert all(n % 10 == 0 and n >= 10 for n in p.operands)


def test_no_regrouping_means_ones_add_to_9_or_less():
    for p in _many("add-within-100-no-regrouping"):
        a, b = p.operands
        assert 10 <= a <= 99 and 10 <= b <= 99
        assert a % 10 + b % 10 <= 9
        assert not (a % 10 == 0 and b % 10 == 0), "that's the add-tens skill"


def test_with_regrouping_means_ones_add_to_10_or_more():
    for p in _many("add-within-100-with-regrouping"):
        a, b = p.operands
        assert 10 <= a <= 99 and 10 <= b <= 99
        assert a % 10 + b % 10 >= 10


def test_subtract_within_10_always_leaves_something():
    for p in _many("subtract-within-10"):
        a, b = p.operands
        assert p.kind == "subtract" and 1 <= b < a <= 10


def test_subtract_within_20_goes_back_through_10():
    for p in _many("subtract-within-20"):
        a, b = p.operands
        assert 11 <= a <= 18 and b <= 9
        assert b > a % 10, p  # more than the ones, so it crosses 10
        assert p.answer < 10


def test_subtract_tens_only_uses_whole_tens():
    for p in _many("subtract-tens"):
        assert all(n % 10 == 0 for n in p.operands) and p.answer > 0


def test_subtract_no_regrouping_has_enough_ones():
    for p in _many("subtract-within-100-no-regrouping"):
        a, b = p.operands
        assert 10 <= b < a <= 99
        assert b % 10 <= a % 10
        assert a % 10 != 0  # otherwise it's the "subtract tens" skill


def test_subtract_with_regrouping_needs_a_ten_broken():
    for p in _many("subtract-within-100-with-regrouping"):
        a, b = p.operands
        assert 10 <= b < a <= 99
        assert a % 10 < b % 10


def test_place_value_covers_all_question_types():
    kinds = {p.kind for p in _many("place-value-tens-ones", runs=200)}
    assert kinds == {"count-tens", "count-ones", "compose-number"}


def test_count_to_100_asks_before_and_after():
    kinds = {p.kind for p in _many("count-to-100", runs=200)}
    assert kinds == {"number-after", "number-before"}


# --- Registry -------------------------------------------------------------------


def test_skill_without_generator_raises():
    skill = SKILL_MAP.get("add-within-10")
    fake = type(skill)(**{**skill.__dict__, "id": "not-a-real-skill"})
    assert not has_generator("not-a-real-skill")
    with pytest.raises(KeyError, match="No problem generator for skill 'not-a-real-skill'"):
        generate_problem(fake)


def test_registering_two_generators_for_one_skill_fails():
    with pytest.raises(ValueError, match="Two generators"):
        problems.generator("add-within-10")(lambda skill, rng: None)


def test_cli_prints_samples(capsys):
    assert problems.main() == 0
    out = capsys.readouterr().out
    assert "add-within-20" in out and "answer:" in out
