"""Check a learner's answer and recognise common mistakes (misconceptions).

A wrong answer tells us *what* the child doesn't understand yet. Each rule below
recognises one common mistake from the answer alone and gives short, kind feedback
plus the hint-ladder step to show next. Everything is computed in code. See the
misconceptions section of docs/PEDAGOGY.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from services.problems import Problem

HintStep = Literal["nudge", "picture", "worked-example"]


@dataclass(frozen=True)
class Misconception:
    id: str
    feedback: str  # said to the child: short, kind, never shaming
    hint: HintStep  # which hint-ladder step to show next
    teacher_note: str  # what the mistake means, for the teacher view later


@dataclass(frozen=True)
class CheckResult:
    correct: bool
    misconception: Misconception | None = None  # None when correct, or wrong for an unknown reason


# A rule looks at the problem and the given answer, and says whether the mistake matches.
Rule = tuple[Misconception, Callable[[Problem, int], bool]]


def check_answer(problem: Problem, given: int) -> CheckResult:
    """Mark `given` and, if it's wrong, name the most likely mistake."""
    if given == problem.answer:
        return CheckResult(correct=True)
    for misconception, matches in RULES.get(problem.kind, []):
        if matches(problem, given):
            return CheckResult(correct=False, misconception=misconception)
    return CheckResult(correct=False)


# --- Helpers ----------------------------------------------------------------------


def _reversed_digits(n: int) -> int | None:
    """37 -> 73. None when reversing changes nothing useful (single digits, 40 -> 04)."""
    if n < 10 or n % 10 == 0:
        return None
    flipped = int(str(n)[::-1])
    return flipped if flipped != n else None


def _both_two_digit(p: Problem) -> bool:
    return all(10 <= n <= 99 for n in p.operands)


def _ones_sum(p: Problem) -> int:
    return sum(n % 10 for n in p.operands)


def _tens_sum(p: Problem) -> int:
    return sum(n // 10 for n in p.operands)


# --- Mistakes ---------------------------------------------------------------------

JOINED_DIGITS = Misconception(
    id="joined-digits",
    feedback="You put the numbers side by side. Let's add them by counting them all together.",
    hint="picture",
    teacher_note="Writes the two numbers next to each other (7 + 5 = 75). Revisit what '+' means.",
)
FORGOT_TO_REGROUP = Misconception(
    id="forgot-to-regroup",
    feedback="The ones made a new ten! Let's swap 10 ones for 1 ten and add it to the tens.",
    hint="picture",
    teacher_note=(
        "Drops the ten made by the ones (27 + 15 = 32). Practise regrouping with base-ten blocks."
    ),
)
WROTE_ONES_SUM = Misconception(
    id="wrote-ones-sum",
    feedback="The ones add up to more than 9. Let's swap 10 ones for 1 ten first.",
    hint="picture",
    teacher_note="Writes the ones total without regrouping (27 + 15 = 312).",
)
ADDED_ALL_DIGITS = Misconception(
    id="added-all-digits",
    feedback="Tens and ones are different. Let's add the tens together and the ones together.",
    hint="picture",
    teacher_note=(
        "Adds every digit as ones (23 + 14 = 10). Revisit place value with a tens-and-ones chart."
    ),
)
REVERSED_DIGITS = Misconception(
    id="reversed-digits",
    feedback="You found the right digits! Check which one is the tens and which is the ones.",
    hint="nudge",
    teacher_note=(
        "Writes the digits of the answer backwards (37 written as 73). "
        "Common when learning to write numbers."
    ),
)
COUNTED_START = Misconception(
    id="counted-start",
    feedback="So close! Start on the first number, then count on one jump at a time.",
    hint="picture",
    teacher_note=(
        "One less than the answer: counts the starting number when counting on (6 + 3 = 8). "
        "Use a number line."
    ),
)
COUNTED_EXTRA = Misconception(
    id="counted-extra",
    feedback="So close! Let's count again carefully, touching each one only once.",
    hint="picture",
    teacher_note="One more than the answer: counts an object or jump twice.",
)
MISSING_ADDED_INSTEAD = Misconception(
    id="missing-added-instead",
    feedback="We need the number that makes the total. How many more do we need to reach it?",
    hint="picture",
    teacher_note=(
        "Adds the two numbers shown (4 + ? = 10 answered 14). Use a ten-frame to show the gap."
    ),
)
MISSING_GAVE_TOTAL = Misconception(
    id="missing-gave-total",
    feedback="That's the total. We need the missing part. How many more do we need?",
    hint="picture",
    teacher_note="Gives the total instead of the missing part (4 + ? = 10 answered 10).",
)
MISSING_GAVE_PART = Misconception(
    id="missing-gave-part",
    feedback="That's the number we already have. How many more make the total?",
    hint="picture",
    teacher_note="Repeats the known part (4 + ? = 10 answered 4).",
)
MISCOUNTED = Misconception(
    id="miscounted",
    feedback="Nearly! Let's count again, touching each one as you say its number.",
    hint="picture",
    teacher_note="Off by one when counting objects: skipped one or counted one twice.",
)
WRONG_DIRECTION = Misconception(
    id="wrong-direction",
    feedback="Look again: do we need the number just before, or just after?",
    hint="picture",
    teacher_note="Confuses 'before' and 'after' on the number line.",
)
REPEATED_NUMBER = Misconception(
    id="repeated-number",
    feedback="That's the number we started with. Which number comes next to it?",
    hint="picture",
    teacher_note="Repeats the given number instead of the one before or after.",
)
SWAPPED_TENS_ONES = Misconception(
    id="swapped-tens-ones",
    feedback="Check again: the tens digit is on the left, the ones digit is on the right.",
    hint="picture",
    teacher_note="Swaps the tens and ones digits when naming place value.",
)
GAVE_WHOLE_NUMBER = Misconception(
    id="gave-whole-number",
    feedback="That's the whole number. Let's find just the tens or just the ones.",
    hint="picture",
    teacher_note="Gives the whole number when asked for one digit's value.",
)
ADDED_TENS_AND_ONES = Misconception(
    id="added-tens-and-ones",
    feedback="Each ten is worth 10. Let's count the tens in tens: 10, 20, 30...",
    hint="picture",
    teacher_note=(
        "Adds the number of tens and ones (3 tens and 4 ones = 7). Revisit that a ten is worth 10."
    ),
)


def _counting_sized(p: Problem) -> bool:
    """Small enough that the child is likely counting on (single-digit numbers).

    For bigger sums like 58 + 18, an answer one off is a slip, not a counting-on mistake.
    """
    if p.kind == "missing-addend":
        return p.operands[0] < 10
    return all(n < 10 for n in p.operands)


def _off_by_one_under(p: Problem, g: int) -> bool:
    return _counting_sized(p) and g == p.answer - 1


def _off_by_one_over(p: Problem, g: int) -> bool:
    return _counting_sized(p) and g == p.answer + 1


RULES: dict[str, list[Rule]] = {
    "add": [
        (JOINED_DIGITS, lambda p, g: g == int("".join(str(n) for n in p.operands))),
        (
            WROTE_ONES_SUM,
            lambda p, g: (
                _both_two_digit(p)
                and _ones_sum(p) >= 10
                and g == int(f"{_tens_sum(p)}{_ones_sum(p)}")
            ),
        ),
        (
            FORGOT_TO_REGROUP,
            lambda p, g: (
                _both_two_digit(p)
                and _ones_sum(p) >= 10
                and g == _tens_sum(p) * 10 + _ones_sum(p) % 10
            ),
        ),
        (
            ADDED_ALL_DIGITS,
            lambda p, g: _both_two_digit(p) and g == _tens_sum(p) + _ones_sum(p),
        ),
        (REVERSED_DIGITS, lambda p, g: g == _reversed_digits(p.answer)),
        (COUNTED_START, _off_by_one_under),
        (COUNTED_EXTRA, _off_by_one_over),
    ],
    "missing-addend": [
        (MISSING_ADDED_INSTEAD, lambda p, g: g == sum(p.operands)),
        (MISSING_GAVE_TOTAL, lambda p, g: g == p.operands[1]),
        (MISSING_GAVE_PART, lambda p, g: g == p.operands[0]),
        (COUNTED_START, _off_by_one_under),
        (COUNTED_EXTRA, _off_by_one_over),
    ],
    "count": [
        (MISCOUNTED, lambda p, g: abs(g - p.answer) == 1),
    ],
    "number-after": [
        (WRONG_DIRECTION, lambda p, g: g == p.operands[0] - 1),
        (REPEATED_NUMBER, lambda p, g: g == p.operands[0]),
        (REVERSED_DIGITS, lambda p, g: g == _reversed_digits(p.answer)),
    ],
    "number-before": [
        (WRONG_DIRECTION, lambda p, g: g == p.operands[0] + 1),
        (REPEATED_NUMBER, lambda p, g: g == p.operands[0]),
        (REVERSED_DIGITS, lambda p, g: g == _reversed_digits(p.answer)),
    ],
    "count-tens": [
        (SWAPPED_TENS_ONES, lambda p, g: g == p.operands[0] % 10),
        (GAVE_WHOLE_NUMBER, lambda p, g: g == p.operands[0]),
    ],
    "count-ones": [
        (SWAPPED_TENS_ONES, lambda p, g: g == p.operands[0] // 10),
        (GAVE_WHOLE_NUMBER, lambda p, g: g == p.operands[0]),
    ],
    "compose-number": [
        (ADDED_TENS_AND_ONES, lambda p, g: g == sum(p.operands)),
        (REVERSED_DIGITS, lambda p, g: g == _reversed_digits(p.answer)),
    ],
}
