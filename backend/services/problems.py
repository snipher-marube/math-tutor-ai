"""Generate practice problems for each skill in the skill map.

Every problem is built from the skill's rules, so its answer is computed in code
and always correct. The AI model is never involved. See docs/PEDAGOGY.md.

Print sample problems for every skill from the command line:

    uv run python -m services.problems
"""

from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass

from services.skill_map import Skill, SkillMap, load_skill_map


@dataclass(frozen=True)
class Problem:
    skill_id: str
    kind: str  # what type of problem this is, e.g. "add" or "missing-addend"
    question: str  # short, read-aloud friendly text
    operands: tuple[int, ...]  # the numbers in the problem, for visuals and mistake checks
    answer: int


Generator = Callable[[Skill, random.Random], Problem]
_GENERATORS: dict[str, Generator] = {}


def generator(skill_id: str) -> Callable[[Generator], Generator]:
    """Register a function as the problem generator for a skill."""

    def register(fn: Generator) -> Generator:
        if skill_id in _GENERATORS:
            raise ValueError(f"Two generators registered for skill {skill_id!r}")
        _GENERATORS[skill_id] = fn
        return fn

    return register


def has_generator(skill_id: str) -> bool:
    return skill_id in _GENERATORS


def generate_problem(skill: Skill, rng: random.Random | None = None) -> Problem:
    """Make one new problem for `skill`. Pass a seeded `rng` for repeatable problems."""
    try:
        make = _GENERATORS[skill.id]
    except KeyError:
        raise KeyError(f"No problem generator for skill {skill.id!r}") from None
    return make(skill, rng or random.Random())


def skills_without_generators(skill_map: SkillMap) -> list[str]:
    return [s.id for s in skill_map if not has_generator(s.id)]


def _add(skill: Skill, a: int, b: int) -> Problem:
    return Problem(skill.id, "add", f"{a} + {b} = ?", (a, b), a + b)


# --- Whole numbers --------------------------------------------------------------


@generator("count-to-20")
def _count_to_20(skill: Skill, rng: random.Random) -> Problem:
    n = rng.randint(max(1, skill.numbers.min), skill.numbers.max)
    return Problem(skill.id, "count", "Count the objects. How many are there?", (n,), n)


@generator("count-to-100")
def _count_to_100(skill: Skill, rng: random.Random) -> Problem:
    lo, hi = skill.numbers.min, skill.numbers.max
    if rng.random() < 0.5:
        n = rng.randint(lo, hi - 1)
        return Problem(skill.id, "number-after", f"What number comes after {n}?", (n,), n + 1)
    n = rng.randint(lo + 1, hi)
    return Problem(skill.id, "number-before", f"What number comes before {n}?", (n,), n - 1)


@generator("place-value-tens-ones")
def _place_value(skill: Skill, rng: random.Random) -> Problem:
    n = rng.randint(max(10, skill.numbers.min), min(99, skill.numbers.max))
    tens, ones = divmod(n, 10)
    match rng.choice(["tens", "ones", "compose"]):
        case "tens":
            return Problem(skill.id, "count-tens", f"How many tens are in {n}?", (n,), tens)
        case "ones":
            return Problem(skill.id, "count-ones", f"How many ones are in {n}?", (n,), ones)
        case _:
            return Problem(
                skill.id,
                "compose-number",
                f"{tens} tens and {ones} ones make what number?",
                (tens, ones),
                n,
            )


# --- Addition -------------------------------------------------------------------


@generator("add-within-10")
def _add_within_10(skill: Skill, rng: random.Random) -> Problem:
    total = rng.randint(2, skill.numbers.max)
    a = rng.randint(1, total - 1)
    return _add(skill, a, total - a)


@generator("make-10")
def _make_10(skill: Skill, rng: random.Random) -> Problem:
    target = skill.numbers.max
    a = rng.randint(1, target - 1)
    return Problem(skill.id, "missing-addend", f"{a} + ? = {target}", (a, target), target - a)


@generator("add-within-20")
def _add_within_20(skill: Skill, rng: random.Random) -> Problem:
    # Totals above 10, so the child practises the new idea: bridging through 10.
    # Both numbers are single digits, so the biggest total is 9 + 9 = 18.
    total = rng.randint(11, min(18, skill.numbers.max))
    a = rng.randint(total - 9, 9)
    return _add(skill, a, total - a)


@generator("add-tens")
def _add_tens(skill: Skill, rng: random.Random) -> Problem:
    total_tens = rng.randint(2, skill.numbers.max // 10)
    a_tens = rng.randint(1, total_tens - 1)
    return _add(skill, a_tens * 10, (total_tens - a_tens) * 10)


@generator("add-within-100-no-regrouping")
def _add_within_100_no_regrouping(skill: Skill, rng: random.Random) -> Problem:
    # Two 2-digit numbers. Ones add to 9 or less, tens add to 9 or less.
    a_tens = rng.randint(1, 8)
    b_tens = rng.randint(1, 9 - a_tens)
    a_ones = rng.randint(0, 9)
    b_ones = rng.randint(0, 9 - a_ones)
    if a_ones == b_ones == 0:  # that would be the "add tens" skill
        a_ones = rng.randint(1, 9)
    return _add(skill, a_tens * 10 + a_ones, b_tens * 10 + b_ones)


@generator("add-within-100-with-regrouping")
def _add_within_100_with_regrouping(skill: Skill, rng: random.Random) -> Problem:
    # Two 2-digit numbers whose ones add to 10 or more, with a total of 100 or less.
    a_ones = rng.randint(1, 9)
    b_ones = rng.randint(10 - a_ones, 9)
    max_tens = (skill.numbers.max - (a_ones + b_ones)) // 10  # tens left after regrouping
    a_tens = rng.randint(1, max_tens - 1)
    b_tens = rng.randint(1, max_tens - a_tens)
    return _add(skill, a_tens * 10 + a_ones, b_tens * 10 + b_ones)


def main() -> int:
    skill_map = load_skill_map()
    missing = skills_without_generators(skill_map)
    rng = random.Random(1)

    for skill in skill_map:
        print(f"\n{skill.id}  (Grade {skill.grade}, {skill.name})")
        if not has_generator(skill.id):
            print("  ! no problem generator yet")
            continue
        for _ in range(3):
            p = generate_problem(skill, rng)
            print(f"  {p.question:<45} answer: {p.answer}")

    if missing:
        print(f"\nSkills without a generator: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
