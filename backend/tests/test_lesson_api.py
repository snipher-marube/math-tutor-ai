"""Tests for the lesson API. No AI is involved."""

import pytest
from fastapi.testclient import TestClient

from main import app
from services.learners import LearnerStore
from services.problem_store import ProblemStore
from services.problems import Problem


@pytest.fixture
def store(db):
    return ProblemStore(db)


@pytest.fixture
def client():
    return TestClient(app)


def _plant(store: ProblemStore, problem: Problem) -> str:
    """Put a known problem in the store, so tests can answer it."""
    return store.add(problem).id


SEVEN_PLUS_FIVE = Problem("add-within-20", "add", "7 + 5 = ?", (7, 5), 12)


# --- Skills ---------------------------------------------------------------------


def test_lists_skills_in_teaching_order(client):
    skills = client.get("/api/lesson/skills").json()
    ids = [s["id"] for s in skills]
    assert ids[0] == "count-to-20"
    assert ids.index("add-within-10") < ids.index("make-10") < ids.index("add-within-20")
    assert {"id", "name", "grade", "requires", "examples"} <= skills[0].keys()


# --- New problems ---------------------------------------------------------------


def test_new_problem_never_includes_the_answer(client, store):
    res = client.post("/api/lesson/problems", json={"skill_id": "add-within-10"})
    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"id", "skill_id", "kind", "question", "operands"}
    assert body["skill_id"] == "add-within-10"
    assert body["kind"] == "add"
    assert store.get(body["id"]) is not None


def test_every_skill_can_give_a_problem(client):
    for skill in client.get("/api/lesson/skills").json():
        res = client.post("/api/lesson/problems", json={"skill_id": skill["id"]})
        assert res.status_code == 201, skill["id"]


def test_unknown_skill_is_404(client):
    res = client.post("/api/lesson/problems", json={"skill_id": "fly-to-the-moon"})
    assert res.status_code == 404
    assert "Unknown skill" in res.json()["detail"]


# --- Answers --------------------------------------------------------------------


def _answer(client, problem_id, answer):
    return client.post(f"/api/lesson/problems/{problem_id}/answer", json={"answer": answer})


def test_correct_first_try(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    body = _answer(client, pid, 12).json()
    assert body == {
        "correct": True,
        "feedback": "Well done! You worked it out.",
        "misconception": None,
        "next_hint": None,
        "attempts": 1,
    }
    assert store.get(pid).solved


def test_recognised_mistake_gets_specific_feedback_and_hint(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    body = _answer(client, pid, 75).json()
    assert body["correct"] is False
    assert body["misconception"] == "joined-digits"
    assert "side by side" in body["feedback"]
    assert body["next_hint"] == "picture"


def test_unknown_mistake_starts_with_a_nudge(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    body = _answer(client, pid, 40).json()
    assert body["correct"] is False
    assert body["misconception"] is None
    assert body["next_hint"] == "nudge"
    assert "hint" in body["feedback"]


def test_praises_effort_after_mistakes(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    _answer(client, pid, 75)
    body = _answer(client, pid, 12).json()
    assert body["correct"] is True
    assert body["attempts"] == 2
    assert "kept trying" in body["feedback"]
    assert store.get(pid).given_answers == (75, 12)


def test_unknown_problem_is_404(client):
    res = _answer(client, "does-not-exist", 3)
    assert res.status_code == 404
    assert "new problem" in res.json()["detail"]


@pytest.mark.parametrize("answer", [-1, 10_001, "seven", None])
def test_invalid_answer_is_422(client, store, answer):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    assert _answer(client, pid, answer).status_code == 422


# --- Hints ----------------------------------------------------------------------


def _hints(client, problem_id, **params):
    return client.get(f"/api/lesson/problems/{problem_id}/hints", params=params)


def test_hint_ladder(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    hints = _hints(client, pid).json()
    assert [h["step"] for h in hints] == ["nudge", "picture", "worked-example"]
    assert hints[0]["text"].startswith("Make 10 first")
    assert hints[1]["visual"] == {
        "type": "ten-frame",
        "params": {"filled": 7, "size": 10, "extra": 5},
    }
    example = hints[2]["example"]
    assert example["kind"] == "add" and len(example["operands"]) == 2
    assert example["question"] != "7 + 5 = ?"
    assert "12" not in example["steps"][-1], "example must not share the answer"


def test_hints_start_where_the_answer_suggested(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    start = _answer(client, pid, 75).json()["next_hint"]
    hints = _hints(client, pid, start=start).json()
    assert [h["step"] for h in hints] == ["picture", "worked-example"]


def test_hints_are_the_same_every_time(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    assert _hints(client, pid).json() == _hints(client, pid).json()


def test_invalid_hint_start_is_422(client, store):
    pid = _plant(store, SEVEN_PLUS_FIVE)
    assert _hints(client, pid, start="give-me-the-answer").status_code == 422


def test_hints_for_unknown_problem_is_404(client):
    assert _hints(client, "does-not-exist").status_code == 404


# --- Full flow through the API only ---------------------------------------------


def test_full_flow_for_every_skill(client, store):
    """New problem -> wrong answer -> hints -> right answer, using only the API."""
    for skill in client.get("/api/lesson/skills").json():
        problem = client.post("/api/lesson/problems", json={"skill_id": skill["id"]}).json()
        right = store.get(problem["id"]).problem.answer  # the test peeks; the browser can't
        wrong = right + 37

        first = _answer(client, problem["id"], wrong).json()
        assert first["correct"] is False and first["next_hint"]

        hints = _hints(client, problem["id"], start=first["next_hint"]).json()
        assert hints and hints[-1]["step"] == "worked-example"

        last = _answer(client, problem["id"], right).json()
        assert last["correct"] is True and last["attempts"] == 2


# --- Learners -------------------------------------------------------------------


def test_problem_for_a_learner_is_recorded(client, store, db):
    learner = LearnerStore(db).create("Simba")
    res = client.post(
        "/api/lesson/problems", json={"skill_id": "add-within-10", "learner_id": learner.id}
    )
    assert res.status_code == 201
    assert store.get(res.json()["id"]).learner_id == learner.id


def test_problem_without_a_learner_is_anonymous(client, store):
    res = client.post("/api/lesson/problems", json={"skill_id": "add-within-10"})
    assert store.get(res.json()["id"]).learner_id is None


def test_unknown_learner_is_404(client):
    res = client.post("/api/lesson/problems", json={"skill_id": "add-within-10", "learner_id": 999})
    assert res.status_code == 404
    assert "Unknown learner" in res.json()["detail"]


# --- Store ----------------------------------------------------------------------


def test_problems_and_answers_survive_a_restart(db):
    """A new store on the same file (like a server restart) still knows the problem."""
    pid = ProblemStore(db).add(SEVEN_PLUS_FIVE).id
    ProblemStore(db).record_attempt(pid, 75, False, "joined-digits")

    after_restart = ProblemStore(type(db)(db.path)).get(pid)
    assert after_restart.problem == SEVEN_PLUS_FIVE
    assert after_restart.given_answers == (75,)
    assert not after_restart.solved


def test_store_ids_are_unique(store):
    ids = {store.add(SEVEN_PLUS_FIVE).id for _ in range(500)}
    assert len(ids) == 500
