"""Learners: nicknames and progress, stored only on this device.

There are no accounts or passwords. Anyone using the device can view or reset
progress, which suits a shared family or classroom device. See docs/CHILD_SAFETY.md.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, StringConstraints

from dependencies import LearnerStoreDep
from services.learners import AVATARS, Learner, NicknameTakenError

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


class SkillProgressOut(BaseModel):
    skill_id: str
    problems: int = Field(description="Problems started")
    attempts: int = Field(description="Answers given")
    correct: int = Field(description="Correct answers")
    last_practised: str


def _out(learner: Learner) -> LearnerOut:
    return LearnerOut(**learner.__dict__)


def _get_or_404(store, learner_id: int) -> Learner:
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
    """Totals per skill practised, most recent first. Mastery comes in a later PR."""
    _get_or_404(store, learner_id)
    return [SkillProgressOut(**p.__dict__) for p in store.progress(learner_id)]


@router.delete("/{learner_id}/progress", status_code=204)
def reset_progress(learner_id: int, store: LearnerStoreDep) -> Response:
    """Delete all of a learner's problems and answers, but keep the learner."""
    _get_or_404(store, learner_id)
    store.reset_progress(learner_id)
    return Response(status_code=204)


@router.delete("/{learner_id}", status_code=204)
def delete_learner(learner_id: int, store: LearnerStoreDep) -> Response:
    """Delete a learner and everything stored about them."""
    if not store.delete(learner_id):
        raise HTTPException(404, "Learner not found")
    return Response(status_code=204)
