"""Learners: nicknames and progress, stored only on this device.

There are no accounts or passwords. Anyone using the device can view or reset
progress, which suits a shared family or classroom device. See docs/CHILD_SAFETY.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, StringConstraints

from config import settings
from dependencies import LearnerStoreDep, PlacementStoreDep, SkillMapDep
from services import review
from services.learners import AVATARS, Learner, LearnerStore, NicknameTakenError
from services.mastery import (
    RECENT_PROBLEMS,
    REQUIRED_CORRECT,
    REQUIRED_DAYS,
    FirstAnswer,
    SkillMastery,
    Status,
    next_skill,
    skill_mastery,
)
from services.placement_store import PlacementStore
from services.problems import has_generator
from services.review import GAPS_DAYS, ReviewPlan, review_plans
from services.skill_map import SkillMap

router = APIRouter(prefix="/api/learners", tags=["learners"])

# Letters only (any language), with single spaces, hyphens or apostrophes between words.
# No digits or symbols, so phone numbers and email addresses can't be used as nicknames.
Nickname = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$",
    ),
]
Avatar = Literal[AVATARS]  # type: ignore[valid-type]


class NewLearnerIn(BaseModel):
    nickname: Nickname = Field(
        description="A nickname, never a real full name. Letters only, up to 20 characters.",
        examples=["Simba"],
    )
    avatar: Avatar | None = Field(default=None, description=f"One of: {', '.join(AVATARS)}")


class LearnerOut(BaseModel):
    id: int
    nickname: str
    avatar: str | None
    created_at: str


MASTERY_RULE = (
    f"Mastered when at least {REQUIRED_CORRECT} of the last {RECENT_PROBLEMS} problems "
    f"were right on the first try, on at least {REQUIRED_DAYS} different days."
)


class SkillProgressOut(BaseModel):
    skill_id: str
    status: Status = Field(description=MASTERY_RULE)
    problems: int = Field(description="Problems started")
    attempts: int = Field(description="Answers given, including retries")
    correct: int = Field(description="Correct answers, including retries")
    recent_total: int = Field(description=f"First answers counted (up to {RECENT_PROBLEMS})")
    recent_correct: int = Field(description="Of those, how many were right on the first try")
    correct_days: int = Field(description="Different days those right answers were on")
    last_practised: str


class NextSkillOut(BaseModel):
    skill_id: str | None = Field(description="None when every skill is mastered")
    name: str | None
    grade: int | None
    status: Status | None
    review: bool = Field(
        default=False, description="True for a quick review of a mastered skill that is due"
    )
    reason: str = Field(description="Why this skill, for teachers and parents")


REVIEW_RULE = (
    "Mastered skills come back for one quick problem after "
    + ", then ".join(f"{d}" for d in GAPS_DAYS)
    + " days. A wrong first answer starts again from 1 day."
)


class ReviewOut(BaseModel):
    skill_id: str
    name: str
    last_seen: date = Field(description="Local day the skill was last answered, or placed")
    streak_days: int = Field(description="Days in a row (of practice) with right first answers")
    due_on: date
    due: bool = Field(description=REVIEW_RULE)


def _out(learner: Learner) -> LearnerOut:
    return LearnerOut(**learner.__dict__)


def _mastery(store: LearnerStore, learner_id: int) -> dict[str, SkillMastery]:
    return {
        skill_id: skill_mastery(answers, settings.TIMEZONE)
        for skill_id, answers in store.first_answers(learner_id).items()
    }


@dataclass(frozen=True)
class _Learning:
    answers: dict[str, list[FirstAnswer]]  # first answers to practice problems, by skill
    statuses: dict[str, Status]
    placed: dict[str, str]  # skills trusted from the placement check -> when it finished


def _learning(store: LearnerStore, placements: PlacementStore, learner_id: int) -> _Learning:
    """Everything the mastery and review rules need about one learner.

    Skills the latest placement check found known count as mastered, until the
    learner gets one of them wrong (first try) after the check. From then on, the
    normal mastery rule decides, as for any other skill.
    """
    answers = store.first_answers(learner_id)
    statuses = {sid: skill_mastery(a, settings.TIMEZONE).status for sid, a in answers.items()}
    placed: dict[str, str] = {}
    placement = placements.latest_finished(learner_id)
    if placement is not None and placement.finished_at is not None:
        for sid in placement.known_skills:
            after = [a for a in answers.get(sid, []) if a.answered_at >= placement.finished_at]
            if all(a.correct for a in after):
                statuses[sid] = "mastered"
                placed[sid] = placement.finished_at
    return _Learning(answers, statuses, placed)


def learner_statuses(
    store: LearnerStore, placements: PlacementStore, learner_id: int
) -> dict[str, Status]:
    """Each skill's status from practice and the latest placement check."""
    return _learning(store, placements, learner_id).statuses


def _plans(learning: _Learning, skill_map: SkillMap) -> list[ReviewPlan]:
    plans = review_plans(
        skill_map, learning.statuses, learning.answers, settings.TIMEZONE, learning.placed
    )
    return [p for p in plans if has_generator(p.skill_id)]


def _review_reason(plan: ReviewPlan, today: date) -> str:
    days = (today - plan.last_seen).days
    when = "yesterday" if days == 1 else f"{days} days ago"
    return f"Quick review: last seen {when}, so it stays strong."


def next_skill_out(skill_map: SkillMap, statuses: dict[str, Status]) -> NextSkillOut:
    nxt = next_skill(skill_map, statuses)
    return NextSkillOut(
        skill_id=nxt.skill.id if nxt.skill else None,
        name=nxt.skill.name if nxt.skill else None,
        grade=nxt.skill.grade if nxt.skill else None,
        status=nxt.status,
        reason=nxt.reason,
    )


def _get_or_404(store: LearnerStore, learner_id: int) -> Learner:
    learner = store.get(learner_id)
    if learner is None:
        raise HTTPException(404, "Learner not found")
    return learner


@router.post(
    "",
    response_model=LearnerOut,
    status_code=201,
    responses={409: {"description": "That nickname is already used on this device"}},
)
def create_learner(body: NewLearnerIn, store: LearnerStoreDep) -> LearnerOut:
    try:
        return _out(store.create(body.nickname, body.avatar))
    except NicknameTakenError:
        raise HTTPException(409, "That nickname is already used. Try another one.") from None


@router.get("", response_model=list[LearnerOut])
def list_learners(store: LearnerStoreDep) -> list[LearnerOut]:
    return [_out(learner) for learner in store.list()]


@router.get("/{learner_id}", response_model=LearnerOut)
def get_learner(learner_id: int, store: LearnerStoreDep) -> LearnerOut:
    return _out(_get_or_404(store, learner_id))


@router.get("/{learner_id}/progress", response_model=list[SkillProgressOut])
def get_progress(learner_id: int, store: LearnerStoreDep) -> list[SkillProgressOut]:
    """Totals and mastery for each skill practised, most recent first."""
    _get_or_404(store, learner_id)
    mastery = _mastery(store, learner_id)
    none_answered = skill_mastery([], settings.TIMEZONE)
    out = []
    for p in store.progress(learner_id):
        m = mastery.get(p.skill_id, none_answered)
        # Started a problem but not answered anything yet: still practising.
        status: Status = "practising" if m.status == "not-started" else m.status
        out.append(
            SkillProgressOut(
                **p.__dict__,
                status=status,
                recent_total=m.recent_total,
                recent_correct=m.recent_correct,
                correct_days=m.correct_days,
            )
        )
    return out


@router.get("/{learner_id}/next-skill", response_model=NextSkillOut)
def get_next_skill(
    learner_id: int,
    store: LearnerStoreDep,
    placements: PlacementStoreDep,
    skill_map: SkillMapDep,
) -> NextSkillOut:
    """The skill this learner should work on next.

    The first skill in teaching order that isn't mastered yet and whose
    prerequisites are all mastered. Skills the latest placement check found known
    count as mastered. A new learner with no placement check starts at the first skill.
    """
    _get_or_404(store, learner_id)
    learning = _learning(store, placements, learner_id)
    today = review.today(settings.TIMEZONE)
    due = [p for p in _plans(learning, skill_map) if p.is_due(today)]
    if due:
        skill = skill_map.get(due[0].skill_id)
        return NextSkillOut(
            skill_id=skill.id,
            name=skill.name,
            grade=skill.grade,
            status="mastered",
            review=True,
            reason=_review_reason(due[0], today),
        )
    return next_skill_out(skill_map, learning.statuses)


@router.get("/{learner_id}/reviews", response_model=list[ReviewOut])
def get_reviews(
    learner_id: int,
    store: LearnerStoreDep,
    placements: PlacementStoreDep,
    skill_map: SkillMapDep,
) -> list[ReviewOut]:
    """The review schedule for every mastered skill, soonest first. For teachers and parents."""
    _get_or_404(store, learner_id)
    today = review.today(settings.TIMEZONE)
    return [
        ReviewOut(
            skill_id=p.skill_id,
            name=skill_map.get(p.skill_id).name,
            last_seen=p.last_seen,
            streak_days=p.streak_days,
            due_on=p.due_on,
            due=p.is_due(today),
        )
        for p in _plans(_learning(store, placements, learner_id), skill_map)
    ]


@router.delete("/{learner_id}/progress", status_code=204)
def reset_progress(learner_id: int, store: LearnerStoreDep) -> Response:
    """Delete all of a learner's problems, answers and placement checks, but keep the learner."""
    _get_or_404(store, learner_id)
    store.reset_progress(learner_id)
    return Response(status_code=204)


@router.delete("/{learner_id}", status_code=204)
def delete_learner(learner_id: int, store: LearnerStoreDep) -> Response:
    """Delete a learner and everything stored about them."""
    if not store.delete(learner_id):
        raise HTTPException(404, "Learner not found")
    return Response(status_code=204)
