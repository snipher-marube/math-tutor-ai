"""The hint ladder: help a stuck child one step at a time, without giving the answer.

1. nudge:          a short spoken prompt that uses the problem's own numbers
2. picture:        a visual for the frontend to draw (counters, ten-frame, ...)
3. worked-example: a *different* problem of the same kind, solved step by step

The child then solves their own problem. Nudge and picture text never say the
answer, and the worked example always has a different answer. See the hint
ladder section of docs/PEDAGOGY.md.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from services.answer_checker import HintStep
from services.problems import Problem, generate_problem
from services.skill_map import Skill

STEPS: tuple[HintStep, ...] = ("nudge", "picture", "worked-example")


@dataclass(frozen=True)
class Visual:
    """What the frontend should draw. `params` keys depend on `type`.

    - objects:      count, or first and second (two groups to put together).
                    With take: the last `take` of `count` are crossed out (take away).
    - ten-frame:    filled (dots shown), size (frame size, usually 10).
                    With take: the last `take` dots are crossed out.
    - number-line:  start, end (labels shown), blank (the position left empty for the child)
    - base-ten:     tens, ones, or a_tens, a_ones, b_tens, b_ones for two numbers.
                    With take_tens and take_ones: that many are crossed out.
    """

    type: str
    params: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkedExample:
    problem: Problem
    steps: tuple[str, ...]


@dataclass(frozen=True)
class Hint:
    step: HintStep
    text: str  # said to the child
    visual: Visual | None = None
    example: WorkedExample | None = None


def hint_ladder(
    problem: Problem,
    skill: Skill,
    rng: random.Random | None = None,
    start: HintStep = "nudge",
) -> list[Hint]:
    """The hints for `problem`, in order, beginning at `start`.

    Use the answer checker's suggested step as `start` when a mistake was recognised.
    """
    rng = rng or random.Random()
    builders = {
        "nudge": lambda: Hint("nudge", _nudge(problem)),
        "picture": lambda: Hint("picture", _picture_text(problem), visual=_visual(problem)),
        "worked-example": lambda: _worked_example_hint(problem, skill, rng),
    }
    return [builders[step]() for step in STEPS[STEPS.index(start) :]]


# --- Which strategy fits an addition problem --------------------------------------


def _add_strategy(p: Problem) -> str:
    a, b = p.operands
    if a >= 10 and b >= 10:
        if a % 10 == 0 and b % 10 == 0:
            return "tens"
        return "regroup" if a % 10 + b % 10 >= 10 else "tens-and-ones"
    if p.answer > 10:
        return "make-10"
    return "count-on"


def _subtract_strategy(p: Problem) -> str:
    a, b = p.operands
    if a <= 10:
        return "count-back"
    if b < 10:
        return "back-through-10"
    if a % 10 == 0 and b % 10 == 0:
        return "tens"
    return "regroup" if a % 10 < b % 10 else "tens-and-ones"


def _strategy(p: Problem) -> str | None:
    if p.kind == "add":
        return _add_strategy(p)
    if p.kind == "subtract":
        return _subtract_strategy(p)
    return None


# --- Step 1: nudge ----------------------------------------------------------------


def _nudge(p: Problem) -> str:
    match p.kind:
        case "add":
            a, b = p.operands
            big, small = max(a, b), min(a, b)
            match _add_strategy(p):
                case "count-on":
                    return f"Start at {big}. Count on {small} more."
                case "make-10":
                    return f"Make 10 first. How many more does {big} need to make 10?"
                case "tens":
                    return f"Think in tens: {a // 10} tens and {b // 10} tens."
                case "tens-and-ones":
                    return "Add the tens together. Then add the ones together."
                case _:
                    return "Add the ones first. If they make 10 or more, swap 10 ones for 1 ten."
        case "subtract":
            a, b = p.operands
            match _subtract_strategy(p):
                case "count-back":
                    return f"Start at {a}. Count back {b}."
                case "back-through-10":
                    return f"Go back to 10 first. How many do you take from {a} to get to 10?"
                case "tens":
                    return f"Think in tens: {a // 10} tens take away {b // 10} tens."
                case "tens-and-ones":
                    return "Take away the tens. Then take away the ones."
                case _:
                    return "Are there enough ones to take away? If not, break 1 ten into 10 ones."
        case "missing-addend":
            a, target = p.operands
            return f"Start at {a}. Count up to {target}. How many jumps did you make?"
        case "count":
            return "Touch each one as you count. The last number you say is how many."
        case "number-after":
            return f"Say {p.operands[0]}, then count up one more."
        case "number-before":
            return f"Count back one from {p.operands[0]}."
        case "count-tens":
            return f"In {p.operands[0]}, the digit on the left tells you the tens."
        case "count-ones":
            return f"In {p.operands[0]}, the digit on the right tells you the ones."
        case "compose-number":
            return "Count the tens in tens, then count on the ones."
    return "Let's try it together, one small step at a time."


# --- Step 2: picture --------------------------------------------------------------


def _visual(p: Problem) -> Visual | None:
    match p.kind:
        case "add":
            a, b = p.operands
            match _add_strategy(p):
                case "count-on":
                    return Visual("objects", {"first": a, "second": b})
                case "make-10":
                    big, small = max(a, b), min(a, b)
                    return Visual("ten-frame", {"filled": big, "size": 10, "extra": small})
                case _:
                    return Visual(
                        "base-ten",
                        {"a_tens": a // 10, "a_ones": a % 10, "b_tens": b // 10, "b_ones": b % 10},
                    )
        case "subtract":
            a, b = p.operands
            match _subtract_strategy(p):
                case "count-back":
                    return Visual("objects", {"count": a, "take": b})
                case "back-through-10":
                    return Visual("ten-frame", {"filled": a, "size": 10, "take": b})
                case _:
                    return _take_away_blocks(a, b)
        case "missing-addend":
            a, target = p.operands
            return Visual("ten-frame", {"filled": a, "size": target})
        case "count":
            return Visual("objects", {"count": p.operands[0]})
        case "number-after":
            n = p.operands[0]
            return Visual("number-line", {"start": max(0, n - 3), "end": n, "blank": n + 1})
        case "number-before":
            n = p.operands[0]
            return Visual("number-line", {"start": n, "end": n + 3, "blank": n - 1})
        case "count-tens" | "count-ones":
            n = p.operands[0]
            return Visual("base-ten", {"tens": n // 10, "ones": n % 10})
        case "compose-number":
            tens, ones = p.operands
            return Visual("base-ten", {"tens": tens, "ones": ones})
    return None


def _take_away_blocks(a: int, b: int) -> Visual:
    """Base-ten blocks for `a`, with the tens and ones of `b` crossed out."""
    return Visual(
        "base-ten",
        {"tens": a // 10, "ones": a % 10, "take_tens": b // 10, "take_ones": b % 10},
    )


def _picture_text(p: Problem) -> str:
    match p.kind:
        case "add":
            match _add_strategy(p):
                case "count-on":
                    return "Here are both groups. Count them all together."
                case "make-10":
                    return "Fill the ten-frame first. Then count the dots that are left over."
                case "regroup":
                    return "Put the ones together. Can you make a new ten?"
                case _:
                    return "Look at the tens and the ones. Add each kind together."
        case "subtract":
            match _subtract_strategy(p):
                case "count-back":
                    return "Cross out the ones we take away. Count the ones that are left."
                case "back-through-10":
                    return "Take away the dots outside the full ten first. Then take the rest."
                case "regroup":
                    return "There aren't enough cubes. Break one stick into 10 cubes."
                case _:
                    return "Take away the sticks, then the cubes. Count what is left."
        case "missing-addend":
            return "Count the empty boxes. That's how many more you need."
        case "count":
            return "Point to each one and count."
        case "number-after" | "number-before":
            return "Look at the number line. Which number goes in the empty box?"
        case "count-tens":
            return "Count the long sticks. Each stick is one ten."
        case "count-ones":
            return "Count the small cubes. Each cube is one."
        case "compose-number":
            return "Count the long sticks in tens, then count on the small cubes."
    return "Look at the picture and try again."


# --- Step 3: worked example -------------------------------------------------------


def _worked_example_hint(problem: Problem, skill: Skill, rng: random.Random) -> Hint:
    example = _example_problem(problem, skill, rng)
    return Hint(
        "worked-example",
        "Here's one I solved. Now you try yours the same way.",
        example=WorkedExample(example, _steps(example)),
    )


def _example_problem(problem: Problem, skill: Skill, rng: random.Random) -> Problem:
    """A different problem of the same kind, with a different answer.

    A different answer matters: showing "8 + 4 = 12" to a child stuck on "7 + 5"
    would give their answer away.
    """
    for _ in range(200):
        candidate = generate_problem(skill, rng)
        if (
            candidate.kind == problem.kind
            and candidate.answer != problem.answer
            and _strategy(candidate) == _strategy(problem)
        ):
            return candidate
    raise RuntimeError(f"Could not find a worked example for {problem}")


def _steps(p: Problem) -> tuple[str, ...]:
    match p.kind:
        case "add":
            a, b = p.operands
            big, small = max(a, b), min(a, b)
            match _add_strategy(p):
                case "count-on":
                    counted = ", ".join(str(n) for n in range(big + 1, big + small + 1))
                    return (f"Start at {big}.", f"Count on {small}: {counted}.", _equals(p))
                case "make-10":
                    to_ten = 10 - big
                    return (
                        f"{big} needs {to_ten} more to make 10.",
                        f"Take {to_ten} from {small}. That leaves {small - to_ten}.",
                        f"10 + {small - to_ten} = {p.answer}.",
                        _equals(p),
                    )
                case "tens":
                    tens = a // 10 + b // 10
                    return (f"{a // 10} tens + {b // 10} tens = {tens} tens.", _equals(p))
                case "tens-and-ones":
                    tens, ones = a // 10 + b // 10, a % 10 + b % 10
                    return (
                        f"Tens: {a // 10} + {b // 10} = {tens} tens. That's {tens * 10}.",
                        f"Ones: {a % 10} + {b % 10} = {ones}.",
                        f"{tens * 10} + {ones} = {p.answer}.",
                        _equals(p),
                    )
                case _:
                    ones = a % 10 + b % 10
                    tens = a // 10 + b // 10
                    return (
                        f"Ones: {a % 10} + {b % 10} = {ones}. That's 1 ten and {ones - 10} ones.",
                        f"Tens: {a // 10} + {b // 10} = {tens}, plus the new ten is {tens + 1}.",
                        f"{tens + 1} tens and {ones - 10} ones is {p.answer}.",
                        _equals(p),
                    )
        case "subtract":
            a, b = p.operands
            match _subtract_strategy(p):
                case "count-back":
                    counted = ", ".join(str(n) for n in range(a - 1, a - b - 1, -1))
                    return (f"Start at {a}.", f"Count back {b}: {counted}.", _equals(p))
                case "back-through-10":
                    to_ten = a - 10
                    rest = b - to_ten
                    return (
                        f"Take {to_ten} from {a} to get to 10.",
                        f"We need to take {b} in all, so {rest} more to take.",
                        f"10 − {rest} = {p.answer}.",
                        _equals(p),
                    )
                case "tens":
                    tens = a // 10 - b // 10
                    return (f"{a // 10} tens − {b // 10} tens = {tens} tens.", _equals(p))
                case "tens-and-ones":
                    tens, ones = a // 10 - b // 10, a % 10 - b % 10
                    return (
                        f"Tens: {a // 10} − {b // 10} = {tens} tens. That's {tens * 10}.",
                        f"Ones: {a % 10} − {b % 10} = {ones}.",
                        f"{tens * 10} + {ones} = {p.answer}.",
                        _equals(p),
                    )
                case _:
                    tens, ones = a // 10 - 1, a % 10 + 10
                    return (
                        f"Only {a % 10} ones, and we need to take {b % 10}. Not enough!",
                        f"Break 1 ten into 10 ones: {tens} tens and {ones} ones.",
                        f"Ones: {ones} − {b % 10} = {ones - b % 10}.",
                        f"Tens: {tens} − {b // 10} = {tens - b // 10}.",
                        f"{tens - b // 10} tens and {ones - b % 10} ones is {p.answer}.",
                        _equals(p),
                    )
        case "missing-addend":
            a, target = p.operands
            counted = ", ".join(str(n) for n in range(a + 1, target + 1))
            return (
                f"Start at {a}.",
                f"Count up to {target}: {counted}.",
                f"That's {p.answer} jumps, so {a} + {p.answer} = {target}.",
            )
        case "count":
            n = p.operands[0]
            counted = ", ".join(str(i) for i in range(1, n + 1))
            return (f"Touch each one and count: {counted}.", f"The last number is {n}.")
        case "number-after":
            n = p.operands[0]
            return (f"Count up: {n}, {n + 1}.", f"So {n + 1} comes after {n}.")
        case "number-before":
            n = p.operands[0]
            return (f"Count back: {n}, {n - 1}.", f"So {n - 1} comes before {n}.")
        case "count-tens":
            n = p.operands[0]
            return (f"In {n}, the digit on the left is {n // 10}.", f"So {n} has {n // 10} tens.")
        case "count-ones":
            n = p.operands[0]
            return (f"In {n}, the digit on the right is {n % 10}.", f"So {n} has {n % 10} ones.")
        case "compose-number":
            tens, ones = p.operands
            return (f"{tens} tens is {tens * 10}.", f"{tens * 10} and {ones} ones is {p.answer}.")
    return (_equals(p),)


def _equals(p: Problem) -> str:
    return f"So {p.question.replace('?', str(p.answer))}."
