"""Tests for learners and their progress. Uses a temporary database (see conftest.py)."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from main import app
from services.problem_store import ProblemStore
from services.problems import Problem

client = TestClient(app)
SUM = Problem("add-within-10", "add", "3 + 4 = ?", (3, 4), 7)


def _create(nickname="Simba", **extra):
    return client.post("/api/learners", json={"nickname": nickname, **extra})


def _practise(db, learner_id, problem=SUM, answers=(7,)):
    store = ProblemStore(db)
    pid = store.add(problem, learner_id=learner_id).id
    for given in answers:
        store.record_attempt(pid, given, given == problem.answer, None)
    return pid


# --- Creating learners ----------------------------------------------------------


def test_create_and_list(db):
    res = _create("Simba", avatar="lion")
    assert res.status_code == 201
    learner = res.json()
    assert learner["nickname"] == "Simba" and learner["avatar"] == "lion"
    assert client.get("/api/learners").json() == [learner]
    assert client.get(f"/api/learners/{learner['id']}").json() == learner


@pytest.mark.parametrize("nickname", ["Simba", "Mama Pima", "Wa-Njeri", "N'Golo", "Jabali"])
def test_accepts_nicknames(nickname):
    assert _create(nickname).status_code == 201


def test_nickname_is_trimmed():
    assert _create("  Simba  ").json()["nickname"] == "Simba"


@pytest.mark.parametrize(
    "nickname",
    [
        "",
        "   ",
        "0712345678",  # phone number
        "amina@example.com",  # email address
        "Simba2",  # digits
        "A" * 21,  # too long
        "Simba  Lion",  # double space
        "<script>",
    ],
)
def test_rejects_unsafe_or_invalid_nicknames(nickname):
    assert _create(nickname).status_code == 422


def test_nickname_must_be_unique_ignoring_case():
    _create("Simba")
    res = _create("simba")
    assert res.status_code == 409
    assert "already used" in res.json()["detail"]


def test_rejects_unknown_avatar():
    assert _create("Simba", avatar="dragon").status_code == 422


def test_unknown_learner_is_404():
    assert client.get("/api/learners/999").status_code == 404
    assert client.get("/api/learners/999/progress").status_code == 404
    assert client.delete("/api/learners/999/progress").status_code == 404
    assert client.delete("/api/learners/999").status_code == 404


# --- Progress -------------------------------------------------------------------


def test_progress_counts_per_skill(db):
    learner = _create().json()
    _practise(db, learner["id"], answers=(5, 7))  # wrong, then right
    _practise(db, learner["id"], answers=(7,))
    other = Problem("make-10", "missing-addend", "4 + ? = 10", (4, 10), 6)
    _practise(db, learner["id"], problem=other, answers=())  # started, not answered

    rows = client.get(f"/api/learners/{learner['id']}/progress").json()
    progress = {p["skill_id"]: p for p in rows}
    assert progress["add-within-10"]["problems"] == 2
    assert progress["add-within-10"]["attempts"] == 3
    assert progress["add-within-10"]["correct"] == 2
    make_10 = progress["make-10"]
    assert (make_10["problems"], make_10["attempts"], make_10["correct"]) == (1, 0, 0)


def test_progress_only_counts_this_learner(db):
    amina, simba = _create("Amina").json(), _create("Simba").json()
    _practise(db, amina["id"])
    _practise(db, None)  # anonymous practice
    assert client.get(f"/api/learners/{simba['id']}/progress").json() == []
    assert len(client.get(f"/api/learners/{amina['id']}/progress").json()) == 1


def test_answering_through_the_api_builds_progress():
    learner = _create().json()
    problem = client.post(
        "/api/lesson/problems", json={"skill_id": "add-within-10", "learner_id": learner["id"]}
    ).json()
    client.post(f"/api/lesson/problems/{problem['id']}/answer", json={"answer": 999})
    progress = client.get(f"/api/learners/{learner['id']}/progress").json()
    assert progress[0]["skill_id"] == "add-within-10"
    assert progress[0]["attempts"] == 1 and progress[0]["correct"] == 0


# --- Reset and delete -----------------------------------------------------------


def _rows(db, table):
    with db.connect() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_reset_progress_keeps_the_learner(db):
    learner = _create().json()
    _practise(db, learner["id"], answers=(5, 7))
    assert client.delete(f"/api/learners/{learner['id']}/progress").status_code == 204
    assert client.get(f"/api/learners/{learner['id']}/progress").json() == []
    assert client.get(f"/api/learners/{learner['id']}").status_code == 200
    assert _rows(db, "problems") == 0 and _rows(db, "attempts") == 0


def test_delete_learner_removes_everything_about_them(db):
    amina, simba = _create("Amina").json(), _create("Simba").json()
    _practise(db, amina["id"], answers=(5, 7))
    _practise(db, simba["id"], answers=(7,))

    assert client.delete(f"/api/learners/{amina['id']}").status_code == 204
    assert client.get(f"/api/learners/{amina['id']}").status_code == 404
    with db.connect() as conn:
        left = conn.execute("SELECT DISTINCT learner_id FROM problems").fetchall()
    assert [r[0] for r in left] == [simba["id"]]
    assert _rows(db, "attempts") == 1  # only Simba's answer is left


def test_database_rejects_orphan_answers(db):
    """Foreign keys are on, so an answer can't point at a missing problem."""
    with pytest.raises(sqlite3.IntegrityError), db.connect() as conn:
        conn.execute(
            "INSERT INTO attempts (problem_id, given, correct, created_at) "
            "VALUES ('x', 1, 0, 'now')"
        )
