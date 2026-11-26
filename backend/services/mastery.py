"""Mastery: has a learner really got a skill, and what should they learn next?

The rule, simple enough to explain to a teacher in one sentence:

    A skill is mastered when at least 4 of the learner's last 5 problems were
    answered correctly on the first try, on at least 2 different days.

- Only the **first answer** to each problem counts. Getting it right after a hint
  is good learning, but it doesn't show mastery yet.
- Days are **local days** (TIMEZONE, Africa/Nairobi by default), so an answer at
  01:00 in Nairobi counts for that morning, not the day before in UTC.
- Mastery is based on the **most recent** problems, so a learner who starts
  getting a skill wrong again goes back to practising it.

See the skill map and mastery section of docs/PEDAGOGY.md.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from services.skill_map import Skill, SkillMap

RECENT_PROBLEMS = 5  # look at this many of the latest problems
REQUIRED_CORRECT = 4  # this many must be right on the first try
REQUIRED_DAYS = 2  # ...and the right answers must fall on this many different days

Status = Literal["not-started", "practising", "mastered"]


@dataclass(frozen=True)
class FirstAnswer:
    correct: bool
    answered_at: str  # ISO timestamp in UTC, as stored in the database


@dataclass(frozen=True)
class SkillMastery:
    status: Status
    recent_total: int  # first answers looked at (up to RECENT_PROBLEMS)
    recent_correct: int  # how many of those were correct
    correct_days: int  # different local days those correct answers fall on


@dataclass(frozen=True)
class NextSkill:
    skill: Skill | None  # None when every skill is mastered
    status: Status | None
    reason: str  # for teachers and parents


def skill_mastery(first_answers: Iterable[FirstAnswer], timezone: str) -> SkillMastery:
    """Apply the mastery rule to one skill's first answers (any order)."""
    answers = sorted(first_answers, key=lambda a: a.answered_at)
    if not answers:
        return SkillMastery("not-started", 0, 0, 0)

    tz = ZoneInfo(timezone)
    recent = answers[-RECENT_PROBLEMS:]
    correct = [a for a in recent if a.correct]
    days = {datetime.fromisoformat(a.answered_at).astimezone(tz).date() for a in correct}

    mastered = len(correct) >= REQUIRED_CORRECT and len(days) >= REQUIRED_DAYS
    return SkillMastery(
        status="mastered" if mastered else "practising",
        recent_total=len(recent),
        recent_correct=len(correct),
        correct_days=len(days),
    )


def next_skill(skill_map: SkillMap, statuses: Mapping[str, Status]) -> NextSkill:
    """The first skill, in teaching order, that isn't mastered and whose prerequisites are.

    `statuses` maps skill ids to their status. Missing skills count as not started.
    """
    for skill in skill_map:
        status = statuses.get(skill.id, "not-started")
        if status == "mastered":
            continue
        if all(statuses.get(req) == "mastered" for req in skill.requires):
            return NextSkill(skill, status, _reason(skill, status))
    return NextSkill(None, None, "Every skill is mastered. Well done!")


def _reason(skill: Skill, status: Status) -> str:
    if status == "practising":
        return "Keep practising: not mastered yet."
    if not skill.requires:
        return "Start here: this skill doesn't need any other skills first."
    return "Ready to start: all the skills it needs are mastered."
