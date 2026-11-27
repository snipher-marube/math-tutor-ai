"""Placement check API: a short adaptive check that finds a learner's starting level.

Flow:
  1. POST /api/learners/{id}/placement          -> the first problem
  2. POST /api/placement/{id}/answer            -> the next problem, or the result
     {"problem_id": ..., "answer": ...}
  3. GET  /api/learners/{id}/placement          -> the latest result (for teachers)

The child is not told whether each answer was right: a placement check is about
finding the right level, not marking. No hints, no AI. Teachers can re-run the
check at any time, and the newest result replaces the one before.
See services/placement.py and docs/PEDAGOGY.md.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dependencies import LearnerStoreDep, PlacementStoreDep, ProblemStoreDep, SkillMapDep
from routers.learners import NextSkillOut, learner_statuses, next_skill_out
from services.answer_checker import check_answer
from services.learners import LearnerStore
from services.placement import MAX_PROBLEMS, PlacementAnswer, StopReason, placement_state
from services.placement_store import Placement, PlacementStore, answered
from services.problem_store import ProblemStore
from services.problems import generate_problem, has_generator
from services.skill_map import SkillMap

router = APIRouter(prefix="/api", tags=["placement"])

THANKS = "Thank you! Here is the next one."
ALL_DONE = "All done. Thank you! Now let's start learning."


# --- Models -----------------------------------------------------------------------


class PlacementProblemOut(BaseModel):
    id: str
    skill_id: str
    kind: str
    question: str
    operands: list[int] = Field(description="The numbers the screen shows. Never the answer.")


class PlacementResultOut(BaseModel):
    placement_id: int
    finished_at: str
    stop_reason: StopReason = Field(
        description="all-decided, enough-problems, or struggling (stopped early: too many wrong)"
    )
    known_skills: list[str] = Field(description="Skills shown to be known. They count as mastered.")
    next_skill: NextSkillOut


class PlacementStepOut(BaseModel):
    placement_id: int
    finished: bool
    message: str = Field(description="Short, kind words to show and read aloud to the child")
    problem: PlacementProblemOut | None = Field(description="The next problem. None when finished.")
    problem_number: int | None = Field(description="1 for the first problem, and so on")
    max_problems: int = MAX_PROBLEMS
    result: PlacementResultOut | None = Field(description="Set when the check is finished")


class PlacementAnswerIn(BaseModel):
    problem_id: str = Field(description="The problem being answered (must be the current one)")
    answer: int = Field(ge=0, le=10_000)


# --- Routes -----------------------------------------------------------------------


@router.post(
    "/learners/{learner_id}/placement",
    response_model=PlacementStepOut,
    status_code=201,
    responses={404: {"description": "Learner not found"}},
)
def start_placement(
    learner_id: int,
    learners: LearnerStoreDep,
    placements: PlacementStoreDep,
    problems: ProblemStoreDep,
    skill_map: SkillMapDep,
) -> PlacementStepOut:
    """Start a new placement check. Any unfinished check for this learner is left behind."""
    if learners.get(learner_id) is None:
        raise HTTPException(404, "Learner not found")
    placement = placements.start(learner_id)
    return _next_step(placement, [], placements, problems, learners, skill_map, message="")


@router.post(
    "/placement/{placement_id}/answer",
    response_model=PlacementStepOut,
    responses={
        404: {"description": "Placement check not found"},
        409: {"description": "The check is finished, or this isn't the current problem"},
    },
)
def answer_placement(
    placement_id: int,
    body: PlacementAnswerIn,
    learners: LearnerStoreDep,
    placements: PlacementStoreDep,
    problems: ProblemStoreDep,
    skill_map: SkillMapDep,
) -> PlacementStepOut:
    """Record one answer and get the next problem, or the result when the check is done."""
    placement = placements.get(placement_id)
    if placement is None:
        raise HTTPException(404, "Placement check not found. Start a new one.")
    if placement.finished_at is not None:
        raise HTTPException(409, "This placement check is already finished.")

    items = placements.items(placement_id)
    current = items[-1] if items else None
    if current is None or current.correct is not None or current.problem_id != body.problem_id:
        raise HTTPException(409, "That isn't the current problem of this placement check.")

    stored = problems.get(current.problem_id)
    assert stored is not None  # placement_problems rows always point at a problem
    result = check_answer(stored.problem, body.answer)
    m = result.misconception
    problems.record_attempt(current.problem_id, body.answer, result.correct, m.id if m else None)

    return _next_step(
        placement,
        answered(placements.items(placement_id)),
        placements,
        problems,
        learners,
        skill_map,
        message=THANKS,
    )


@router.get(
    "/learners/{learner_id}/placement",
    response_model=PlacementResultOut,
    responses={404: {"description": "Learner not found, or no finished placement check yet"}},
)
def get_placement(
    learner_id: int,
    learners: LearnerStoreDep,
    placements: PlacementStoreDep,
    skill_map: SkillMapDep,
) -> PlacementResultOut:
    """The learner's latest finished placement check."""
    if learners.get(learner_id) is None:
        raise HTTPException(404, "Learner not found")
    placement = placements.latest_finished(learner_id)
    if placement is None:
        raise HTTPException(404, "No finished placement check for this learner yet.")
    return _result(placement, placements, learners, skill_map)


# --- Helpers ----------------------------------------------------------------------


def _next_step(
    placement: Placement,
    answers: list[PlacementAnswer],
    placements: PlacementStore,
    problems: ProblemStore,
    learners: LearnerStore,
    skill_map: SkillMap,
    message: str,
) -> PlacementStepOut:
    state = placement_state(skill_map, answers, can_ask=has_generator)

    if state.stop_reason is not None:
        placements.finish(placement.id, state.stop_reason, state.known)
        finished = placements.get(placement.id)
        assert finished is not None
        return PlacementStepOut(
            placement_id=placement.id,
            finished=True,
            message=ALL_DONE,
            problem=None,
            problem_number=None,
            result=_result(finished, placements, learners, skill_map),
        )

    assert state.next_skill_id is not None
    problem = generate_problem(skill_map.get(state.next_skill_id))
    stored = problems.add(problem, learner_id=placement.learner_id, placement_id=placement.id)
    return PlacementStepOut(
        placement_id=placement.id,
        finished=False,
        message=message,
        problem=PlacementProblemOut(
            id=stored.id,
            skill_id=problem.skill_id,
            kind=problem.kind,
            question=problem.question,
            operands=list(problem.operands),
        ),
        problem_number=state.problems + 1,
        result=None,
    )


def _result(
    placement: Placement,
    placements: PlacementStore,
    learners: LearnerStore,
    skill_map: SkillMap,
) -> PlacementResultOut:
    assert placement.finished_at is not None and placement.stop_reason is not None
    statuses = learner_statuses(learners, placements, placement.learner_id)
    return PlacementResultOut(
        placement_id=placement.id,
        finished_at=placement.finished_at,
        stop_reason=placement.stop_reason,  # type: ignore[arg-type]
        known_skills=list(placement.known_skills),
        next_skill=next_skill_out(skill_map, statuses),
    )
