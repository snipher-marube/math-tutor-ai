"""Lesson API: the teaching engine over HTTP.

Flow for one problem:
  1. POST /api/lesson/problems            {"skill_id": ...}  -> a problem, without its answer
  2. POST /api/lesson/problems/{id}/answer {"answer": ...}   -> correct? feedback, hint step
  3. GET  /api/lesson/problems/{id}/hints?start=...          -> the hint ladder

No AI is used. See docs/PEDAGOGY.md and docs/API.md.
"""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.answer_checker import HintStep, check_answer
from services.hints import hint_ladder
from services.problem_store import ProblemStore, StoredProblem
from services.problems import generate_problem, has_generator
from services.skill_map import SkillMap, load_skill_map

router = APIRouter(prefix="/api/lesson", tags=["lesson"])


# --- Dependencies (overridden in tests) -------------------------------------------


@lru_cache
def get_skill_map() -> SkillMap:
    return load_skill_map()


_store = ProblemStore()


def get_store() -> ProblemStore:
    return _store


SkillMapDep = Annotated[SkillMap, Depends(get_skill_map)]
StoreDep = Annotated[ProblemStore, Depends(get_store)]


# --- Models -----------------------------------------------------------------------


class SkillOut(BaseModel):
    id: str
    name: str
    grade: int
    strand: str
    substrand: str
    requires: list[str]
    description: str
    examples: list[str]


class NewProblemIn(BaseModel):
    skill_id: str = Field(examples=["add-within-10"])


class ProblemOut(BaseModel):
    id: str
    skill_id: str
    kind: str
    question: str
    operands: list[int] = Field(
        description="The numbers the screen shows (for visuals). The answer is never included."
    )


class AnswerIn(BaseModel):
    answer: int = Field(ge=0, le=10_000)


class AnswerOut(BaseModel):
    correct: bool
    feedback: str = Field(description="Short, kind words to show and read aloud to the child")
    misconception: str | None = Field(
        description="Id of the recognised mistake, if any (for teachers, not shown to the child)"
    )
    next_hint: HintStep | None = Field(
        description="Hint-ladder step to offer next. None when the answer is correct."
    )
    attempts: int


class VisualOut(BaseModel):
    type: str
    params: dict[str, int]


class WorkedExampleOut(BaseModel):
    question: str
    steps: list[str]


class HintOut(BaseModel):
    step: HintStep
    text: str
    visual: VisualOut | None
    example: WorkedExampleOut | None


# --- Feedback when no specific mistake is recognised -------------------------------

PRAISE_FIRST_TRY = "Well done! You worked it out."
PRAISE_AFTER_TRYING = "You kept trying and you got it. Well done!"
NOT_YET = "Not quite yet. Let's look at a hint together."


# --- Routes -----------------------------------------------------------------------


@router.get("/skills", response_model=list[SkillOut])
async def list_skills(skill_map: SkillMapDep) -> list[SkillOut]:
    """All skills, in teaching order (prerequisites first)."""
    return [
        SkillOut(
            id=s.id,
            name=s.name,
            grade=s.grade,
            strand=s.strand,
            substrand=s.substrand,
            requires=list(s.requires),
            description=s.description,
            examples=list(s.examples),
        )
        for s in skill_map
    ]


@router.post(
    "/problems",
    response_model=ProblemOut,
    status_code=201,
    responses={404: {"description": "Unknown skill, or no problems for this skill yet"}},
)
async def new_problem(body: NewProblemIn, skill_map: SkillMapDep, store: StoreDep) -> ProblemOut:
    """A new problem for a skill. The answer stays on the server."""
    if body.skill_id not in skill_map:
        raise HTTPException(404, f"Unknown skill: {body.skill_id}")
    if not has_generator(body.skill_id):
        raise HTTPException(404, f"No problems for skill {body.skill_id} yet")

    stored = store.add(generate_problem(skill_map.get(body.skill_id)))
    p = stored.problem
    return ProblemOut(
        id=stored.id,
        skill_id=p.skill_id,
        kind=p.kind,
        question=p.question,
        operands=list(p.operands),
    )


@router.post(
    "/problems/{problem_id}/answer",
    response_model=AnswerOut,
    responses={404: {"description": "Problem not found (or forgotten after a restart)"}},
)
async def answer_problem(problem_id: str, body: AnswerIn, store: StoreDep) -> AnswerOut:
    """Check the child's answer. Wrong answers get kind feedback and a hint step."""
    stored = _get_or_404(store, problem_id)
    stored.attempts += 1
    stored.given_answers.append(body.answer)

    result = check_answer(stored.problem, body.answer)
    if result.correct:
        stored.solved = True
        praise = PRAISE_FIRST_TRY if stored.attempts == 1 else PRAISE_AFTER_TRYING
        return AnswerOut(
            correct=True,
            feedback=praise,
            misconception=None,
            next_hint=None,
            attempts=stored.attempts,
        )

    m = result.misconception
    return AnswerOut(
        correct=False,
        feedback=m.feedback if m else NOT_YET,
        misconception=m.id if m else None,
        next_hint=m.hint if m else "nudge",
        attempts=stored.attempts,
    )


@router.get(
    "/problems/{problem_id}/hints",
    response_model=list[HintOut],
    responses={404: {"description": "Problem not found (or forgotten after a restart)"}},
)
async def get_hints(
    problem_id: str,
    store: StoreDep,
    skill_map: SkillMapDep,
    start: HintStep = "nudge",
) -> list[HintOut]:
    """The hint ladder for a problem, from `start` onwards. Same hints every time."""
    stored = _get_or_404(store, problem_id)
    skill = skill_map.get(stored.problem.skill_id)
    ladder = hint_ladder(stored.problem, skill, random.Random(stored.seed), start=start)
    return [
        HintOut(
            step=h.step,
            text=h.text,
            visual=VisualOut(type=h.visual.type, params=h.visual.params) if h.visual else None,
            example=(
                WorkedExampleOut(question=h.example.problem.question, steps=list(h.example.steps))
                if h.example
                else None
            ),
        )
        for h in ladder
    ]


def _get_or_404(store: ProblemStore, problem_id: str) -> StoredProblem:
    stored = store.get(problem_id)
    if stored is None:
        raise HTTPException(404, "Problem not found. Ask for a new problem.")
    return stored
