"""Spaced review: bring mastered skills back, a little later each time.

Children forget skills they don't use. A quick review problem, at growing gaps,
keeps a skill strong for far less effort than re-teaching it later:

    1 day -> 3 days -> 7 days -> 14 days -> 30 days

- The gap grows with the number of **different days** the learner has answered
  the skill right on the first try, in a row (their latest run of right answers).
- A **wrong** first answer starts the gaps again from 1 day. If it was a slip,
  the mastery rule (4 of the last 5) keeps the skill mastered; if not, the skill
  goes back to practising, as usual.
- Skills the placement check found known come up for their first review the day
  after the check, so the check's quick judgement is soon confirmed.
- Due reviews come first in a lesson, one problem each, as a short warm-up.
  The most overdue skill comes first.
- A skill is only reviewed while the skills it needs are still mastered. If a
  learner slips back on a foundation skill, they practise that first.

Days are local days (TIMEZONE). Nothing here stores anything: the schedule is
worked out from the answers already saved. See docs/PEDAGOGY.md.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from services.mastery import FirstAnswer, Status
from services.skill_map import SkillMap

GAPS_DAYS = (1, 3, 7, 14, 30)


@dataclass(frozen=True)
class ReviewPlan:
    skill_id: str
    last_seen: date  # local day of the latest first answer (or the placement check)
    streak_days: int  # different days in the latest run of right first answers
    due_on: date

    def is_due(self, today: date) -> bool:
        return today >= self.due_on


def today(timezone: str) -> date:
    """Today's local date. Tests replace this to move the clock."""
    return datetime.now(ZoneInfo(timezone)).date()


def local_day(timestamp: str, timezone: str) -> date:
    return datetime.fromisoformat(timestamp).astimezone(ZoneInfo(timezone)).date()


def review_plan(
    skill_id: str,
    first_answers: Iterable[FirstAnswer],
    timezone: str,
    placed_at: str | None = None,
) -> ReviewPlan | None:
    """When a mastered skill should next be reviewed.

    `placed_at` is when a placement check found the skill known, if it did.
    Returns None when there is nothing to go on (no answers and no placement).
    """
    answers = sorted(first_answers, key=lambda a: a.answered_at)
    if placed_at is not None:
        # Only answers after the placement check count; the check itself is the start.
        answers = [a for a in answers if a.answered_at >= placed_at]

    if answers:
        last_seen = local_day(answers[-1].answered_at, timezone)
    elif placed_at is not None:
        last_seen = local_day(placed_at, timezone)
    else:
        return None

    run_days: set[date] = set()
    for a in reversed(answers):
        if not a.correct:
            break
        run_days.add(local_day(a.answered_at, timezone))

    streak = len(run_days)
    gap = GAPS_DAYS[min(max(streak - 1, 0), len(GAPS_DAYS) - 1)]
    return ReviewPlan(skill_id, last_seen, streak, last_seen + timedelta(days=gap))


def review_plans(
    skill_map: SkillMap,
    statuses: Mapping[str, Status],
    answers_by_skill: Mapping[str, list[FirstAnswer]],
    timezone: str,
    placed: Mapping[str, str] | None = None,
) -> list[ReviewPlan]:
    """Review plans for every mastered skill, soonest due first (ties: teaching order).

    `placed` maps skills a placement check found known to when it finished.
    """
    placed = placed or {}
    plans = []
    for skill in skill_map:  # teaching order, kept for ties by the stable sort below
        if statuses.get(skill.id) != "mastered":
            continue
        if any(statuses.get(req) != "mastered" for req in skill.requires):
            continue  # practise the foundation first
        plan = review_plan(
            skill.id, answers_by_skill.get(skill.id, []), timezone, placed.get(skill.id)
        )
        if plan is not None:
            plans.append(plan)
    return sorted(plans, key=lambda p: p.due_on)
