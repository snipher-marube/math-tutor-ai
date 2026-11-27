"""Tests for the placement check: the adaptive engine, its storage and its API."""

import pytest
from fastapi.testclient import TestClient

from main import app
from services.placement import (
    MAX_PROBLEMS,
    MAX_WRONG,
    PlacementAnswer,
    placement_state,
)
from services.problem_store import ProblemStore
from services.skill_map import load_skill_map

client = TestClient(app)
SKILL_MAP = load_skill_map()
ALL = {s.id for s in SKILL_MAP}


def _run(knows: set[str]):
    """Play a whole check as a learner who knows exactly the skills in `knows`."""
    answers: list[PlacementAnswer] = []
    state = placement_state(SKILL_MAP, answers)
    while not state.finished:
        answers.append(PlacementAnswer(state.next_skill_id, state.next_skill_id in knows))
        state = placement_state(SKILL_MAP, answers)
    return state, answers


# --- The engine -----------------------------------------------------------------


def _with_prerequisites(skill_id: str) -> set[str]:
    out, todo = set(), [skill_id]
    while todo:
        sid = todo.pop()
        if sid not in out:
            out.add(sid)
            todo.extend(SKILL_MAP.get(sid).requires)
    return out


def test_starts_in_the_middle_not_at_either_end():
    order = [s.id for s in SKILL_MAP]
    first = placement_state(SKILL_MAP, []).next_skill_id
    assert first == "make-10"  # settles 3 skills if right, 4 if wrong
    assert first not in (order[0], order[-1])


@pytest.mark.parametrize("top_skill", [s.id for s in SKILL_MAP])
def test_never_places_a_learner_too_high(top_skill):
    knows = _with_prerequisites(top_skill)
    state, answers = _run(knows)
    assert state.known <= knows
    assert len(answers) <= MAX_PROBLEMS
    if state.stop_reason == "all-decided":
        assert state.known == knows


def test_a_learner_who_knows_everything_is_placed_at_the_top():
    state, answers = _run(ALL)
    assert state.known == ALL
    assert state.stop_reason == "all-decided"
    assert len(answers) <= MAX_PROBLEMS


def test_a_beginner_stops_early_and_knows_nothing():
    state, answers = _run(set())
    assert state.known == frozenset()
    assert state.stop_reason == "struggling"
    assert len(answers) == MAX_WRONG  # every answer was wrong, so it stops quickly


def test_a_grade_1_learner_is_placed_at_grade_2():
    grade_1 = {s.id for s in SKILL_MAP if s.grade == 1}
    state, _ = _run(grade_1)
    assert state.known == grade_1
    assert not state.known & {s.id for s in SKILL_MAP if s.grade == 2}


def test_two_right_answers_mark_the_skill_and_its_prerequisites_known():
    first = placement_state(SKILL_MAP, []).next_skill_id
    one_right = placement_state(SKILL_MAP, [PlacementAnswer(first, True)])
    assert one_right.next_skill_id == first  # asks the same skill again
    assert one_right.known == frozenset()

    two_right = placement_state(SKILL_MAP, [PlacementAnswer(first, True)] * 2)
    assert first in two_right.known
    for req in SKILL_MAP.get(first).requires:
        assert req in two_right.known


def test_one_wrong_answer_marks_the_skill_and_what_builds_on_it_not_known():
    first = placement_state(SKILL_MAP, []).next_skill_id
    state = placement_state(SKILL_MAP, [PlacementAnswer(first, False)])
    assert first in state.not_known
    for skill in SKILL_MAP:
        if first in skill.requires:
            assert skill.id in state.not_known
    assert state.next_skill_id != first


def test_never_asks_more_than_the_maximum():
    # Right once, then wrong, on every skill: the slowest way through.
    answers: list[PlacementAnswer] = []
    state = placement_state(SKILL_MAP, answers)
    while not state.finished:
        repeat = answers and answers[-1].skill_id == state.next_skill_id
        answers.append(PlacementAnswer(state.next_skill_id, not repeat))
        state = placement_state(SKILL_MAP, answers)
    assert len(answers) <= MAX_PROBLEMS


def test_skips_skills_it_cannot_ask_about():
    no_problems = "add-within-20"
    state = placement_state(SKILL_MAP, [], can_ask=lambda sid: sid != no_problems)
    assert state.next_skill_id != no_problems


def test_rejects_an_answer_for_the_wrong_skill():
    first = placement_state(SKILL_MAP, []).next_skill_id
    other = next(s.id for s in SKILL_MAP if s.id != first)
    with pytest.raises(ValueError, match="asked about"):
        placement_state(SKILL_MAP, [PlacementAnswer(other, True)])


# --- The API --------------------------------------------------------------------


def _learner(nickname="Simba"):
    return client.post("/api/learners", json={"nickname": nickname}).json()["id"]


def _answer_for(db, problem_id):
    return ProblemStore(db).get(problem_id).problem.answer


def _play(db, learner_id, knows: set[str]):
    """Take the check through the API, answering right only for skills in `knows`."""
    step = client.post(f"/api/learners/{learner_id}/placement")
    assert step.status_code == 201
    step = step.json()
    numbers = []
    while not step["finished"]:
        problem = step["problem"]
        numbers.append(step["problem_number"])
        right = _answer_for(db, problem["id"])
        answer = right if problem["skill_id"] in knows else right + 1
        res = client.post(
            f"/api/placement/{step['placement_id']}/answer",
            json={"problem_id": problem["id"], "answer": answer},
        )
        assert res.status_code == 200
        step = res.json()
    return step, numbers


def test_first_problem_never_includes_the_answer():
    step = client.post(f"/api/learners/{_learner()}/placement").json()
    assert step["finished"] is False and step["problem_number"] == 1
    assert "answer" not in step["problem"]


def test_full_check_places_the_learner_and_sets_the_next_skill(db):
    learner_id = _learner()
    grade_1 = {s.id for s in SKILL_MAP if s.grade == 1}
    step, numbers = _play(db, learner_id, grade_1)

    assert numbers == list(range(1, len(numbers) + 1))
    result = step["result"]
    assert set(result["known_skills"]) == grade_1
    assert result["next_skill"]["skill_id"] == "place-value-tens-ones"
    next_skill = client.get(f"/api/learners/{learner_id}/next-skill").json()
    assert next_skill["skill_id"] == "place-value-tens-ones"
    assert client.get(f"/api/learners/{learner_id}/placement").json() == result


def test_placement_problems_do_not_count_as_practice(db):
    learner_id = _learner()
    _play(db, learner_id, ALL)
    assert client.get(f"/api/learners/{learner_id}/progress").json() == []


def test_a_rerun_replaces_the_earlier_result(db):
    learner_id = _learner()
    _play(db, learner_id, ALL)
    _play(db, learner_id, set())
    result = client.get(f"/api/learners/{learner_id}/placement").json()
    assert result["known_skills"] == []
    assert result["stop_reason"] == "struggling"
    assert client.get(f"/api/learners/{learner_id}/next-skill").json()["skill_id"] == "count-to-20"


def test_must_answer_the_current_problem(db):
    step = client.post(f"/api/learners/{_learner()}/placement").json()
    url = f"/api/placement/{step['placement_id']}/answer"
    problem_id = step["problem"]["id"]

    assert client.post(url, json={"problem_id": "nope", "answer": 1}).status_code == 409
    assert client.post(url, json={"problem_id": problem_id, "answer": 1}).status_code == 200
    # The same problem can't be answered twice.
    assert client.post(url, json={"problem_id": problem_id, "answer": 1}).status_code == 409


def test_cannot_answer_a_finished_check(db):
    learner_id = _learner()
    step, _ = _play(db, learner_id, set())
    res = client.post(
        f"/api/placement/{step['placement_id']}/answer", json={"problem_id": "x", "answer": 1}
    )
    assert res.status_code == 409


def test_not_found_cases():
    assert client.post("/api/learners/999/placement").status_code == 404
    assert client.get("/api/learners/999/placement").status_code == 404
    assert client.get(f"/api/learners/{_learner()}/placement").status_code == 404  # none yet
    res = client.post("/api/placement/999/answer", json={"problem_id": "x", "answer": 1})
    assert res.status_code == 404


def test_reset_progress_removes_placement_checks(db):
    learner_id = _learner()
    _play(db, learner_id, ALL)
    assert client.delete(f"/api/learners/{learner_id}/progress").status_code == 204
    assert client.get(f"/api/learners/{learner_id}/placement").status_code == 404
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM placement_problems").fetchone()[0] == 0


def test_deleting_the_learner_removes_placement_checks(db):
    learner_id = _learner()
    _play(db, learner_id, ALL)
    assert client.delete(f"/api/learners/{learner_id}").status_code == 204
    with db.connect() as conn:
        for table in ("placements", "placement_problems", "problems", "attempts"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
