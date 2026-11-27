"""Placement check: a short, adaptive check that finds where a new learner really is.

This is "teach at the right level, not the right grade" from docs/PEDAGOGY.md.
It works on the skill map like a friendly game of "higher or lower":

1. Ask about a skill near the **middle** of the skills not decided yet: the one
   whose answer settles the most skills, whether the child gets it right or wrong.
   On a tie, the easier skill (earlier in teaching order) is asked first.
2. **Two right answers** in a row: the learner knows that skill, and every skill it
   needs (its prerequisites, all the way down). Move up.
3. **One wrong answer**: they don't know it yet, nor any skill that builds on it.
   Move down. One wrong answer is enough, so a child is never stuck on a skill
   that is too hard.
4. Stop when every skill is decided, after MAX_PROBLEMS problems, or early after
   MAX_WRONG wrong answers, so a child who is struggling isn't put off.

Skills marked as known count as mastered. Everything else is taught as usual,
starting from the first skill that isn't known. If a skill was not decided, the
learner simply practises it. Nothing is skipped by guessing.

The function here is pure: give it the answers so far, and it says what to ask
next. Storage and the API are in services/placement_store.py and routers/placement.py.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

from services.skill_map import SkillMap

MAX_PROBLEMS = 8  # never more than this many problems
MAX_WRONG = 3  # stop early after this many wrong answers
RIGHT_TO_KNOW = 2  # right answers in a row that show a skill is known

StopReason = Literal["all-decided", "enough-problems", "struggling"]


@dataclass(frozen=True)
class PlacementAnswer:
    skill_id: str
    correct: bool


@dataclass(frozen=True)
class PlacementState:
    next_skill_id: str | None  # the skill to ask about next; None when finished
    known: frozenset[str]  # skills shown to be known (count as mastered)
    not_known: frozenset[str]  # skills shown not to be known yet
    problems: int  # problems answered so far
    stop_reason: StopReason | None  # why it finished; None while still running

    @property
    def finished(self) -> bool:
        return self.stop_reason is not None


def placement_state(
    skill_map: SkillMap,
    answers: Sequence[PlacementAnswer],
    can_ask: Callable[[str], bool] = lambda _skill_id: True,
) -> PlacementState:
    """Replay the answers so far and decide what happens next.

    `can_ask` says which skills have problems to ask (skills without a problem
    generator are never asked about). Raises ValueError if an answer is for a
    different skill than the check would have asked about.
    """
    order = [s.id for s in skill_map]
    below = _closure(skill_map, lambda sid: skill_map.get(sid).requires)
    above = _closure(skill_map, lambda sid: _dependants(skill_map, sid))

    known: set[str] = set()
    not_known: set[str] = set()
    wrong = 0
    asking: str | None = None  # the skill being checked right now
    right_in_a_row = 0

    def undecided() -> list[str]:
        return [s for s in order if s not in known and s not in not_known]

    def choose() -> str | None:
        """The askable skill whose answer settles the most undecided skills either way."""
        open_ = set(undecided())

        def settles(sid: str) -> int:
            if_right = 1 + len(below[sid] & open_)
            if_wrong = 1 + len(above[sid] & open_)
            return min(if_right, if_wrong)

        candidates = [s for s in order if s in open_ and can_ask(s)]
        # max() keeps the first of equal scores, so ties go to the easier skill.
        return max(candidates, key=settles) if candidates else None

    for i, answer in enumerate(answers):
        expected = asking or choose()
        if expected is None or answer.skill_id != expected:
            raise ValueError(
                f"Answer {i + 1} is for {answer.skill_id!r}, but the check asked about {expected!r}"
            )
        if answer.correct:
            right_in_a_row += 1
            asking = expected
            if right_in_a_row >= RIGHT_TO_KNOW:
                known.update({expected, *below[expected]})
                asking, right_in_a_row = None, 0
        else:
            wrong += 1
            not_known.update({expected, *above[expected]})
            asking, right_in_a_row = None, 0

    def state(next_skill_id: str | None, stop: StopReason | None) -> PlacementState:
        return PlacementState(
            next_skill_id, frozenset(known), frozenset(not_known), len(answers), stop
        )

    if wrong >= MAX_WRONG:
        return state(None, "struggling")
    nxt = asking or choose()
    if nxt is None:
        return state(None, "all-decided")
    if len(answers) >= MAX_PROBLEMS:
        return state(None, "enough-problems")
    return state(nxt, None)


def _dependants(skill_map: SkillMap, skill_id: str) -> Iterable[str]:
    return (s.id for s in skill_map if skill_id in s.requires)


def _closure(skill_map: SkillMap, step: Callable[[str], Iterable[str]]) -> dict[str, set[str]]:
    """For each skill, every skill reachable by repeating `step` (not including itself)."""
    out: dict[str, set[str]] = {}
    for skill in skill_map:
        seen: set[str] = set()
        todo = list(step(skill.id))
        while todo:
            sid = todo.pop()
            if sid not in seen:
                seen.add(sid)
                todo.extend(step(sid))
        out[skill.id] = seen
    return out
