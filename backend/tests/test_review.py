"""Tests for spaced review: the schedule, and reviews coming up in lessons."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

import services.problem_store as problem_store_module
import services.review as review_module
from main import app
from services.mastery import FirstAnswer
from services.placement_store import PlacementStore
from services.problem_store import ProblemStore
from services.review import GAPS_DAYS, review_plan, review_plans
from services.skill_map import load_skill_map

client = TestClient(app)
SKILL_MAP = load_skill_map()
NAIROBI = "Africa/Nairobi"


def _day(d: int, hour: int = 8) -> str:
    """A UTC timestamp on 2026-11-<d>. 08:00 UTC is 11:00 in Nairobi."""
    return f"2026-11-{d:02d}T{hour:02d}:00:00+00:00"


def _answers(*spec):
    return [FirstAnswer(correct, at) for correct, at in spec]


# --- The schedule ---------------------------------------------------------------


def test_nothing_to_go_on_means_no_plan():
    assert review_plan("count-to-20", [], NAIROBI) is None


def test_just_mastered_over_two_days_comes_back_after_three_days():
    plan = review_plan(
        "count-to-20",
        _answers((True, _day(1)), (True, _day(1)), (True, _day(2)), (True, _day(2))),
        NAIROBI,
    )
    assert plan.last_seen == date(2026, 11, 2)
    assert plan.streak_days == 2
    assert plan.due_on == date(2026, 11, 5)


def test_gaps_grow_with_each_day_of_right_answers():
    days = [1, 2, 5, 12, 26, 56]
    for n in range(1, len(days) + 1):
        answers = _answers(
            *[
                (True, _day(d) if d <= 30 else f"2026-12-{d - 30:02d}T08:00:00+00:00")
                for d in days[:n]
            ]
        )
        plan = review_plan("count-to-20", answers, NAIROBI)
        assert plan.streak_days == n
        expected_gap = GAPS_DAYS[min(n - 1, len(GAPS_DAYS) - 1)]
        assert (plan.due_on - plan.last_seen).days == expected_gap


def test_many_right_answers_on_one_day_count_as_one_day():
    plan = review_plan("count-to-20", _answers(*[(True, _day(3))] * 5), NAIROBI)
    assert plan.streak_days == 1
    assert (plan.due_on - plan.last_seen).days == 1


def test_a_wrong_first_answer_starts_the_gaps_again():
    plan = review_plan(
        "count-to-20",
        _answers((True, _day(1)), (True, _day(2)), (True, _day(5)), (False, _day(12))),
        NAIROBI,
    )
    assert plan.streak_days == 0
    assert plan.due_on == date(2026, 11, 13)


def test_days_are_local_days():
    # 22:00 UTC on the 1st is 01:00 on the 2nd in Nairobi.
    plan = review_plan("count-to-20", _answers((True, _day(1, hour=22))), NAIROBI)
    assert plan.last_seen == date(2026, 11, 2)


def test_a_placed_skill_is_reviewed_the_day_after_the_check():
    plan = review_plan("count-to-20", [], NAIROBI, placed_at=_day(10))
    assert plan.due_on == date(2026, 11, 11)


def test_answers_from_before_the_placement_check_are_ignored():
    old = _answers((True, _day(1)), (True, _day(2)), (True, _day(5)))
    plan = review_plan("count-to-20", old, NAIROBI, placed_at=_day(10))
    assert plan.last_seen == date(2026, 11, 10) and plan.streak_days == 0


def test_only_mastered_skills_get_plans_soonest_first():
    statuses = {"count-to-20": "mastered", "add-within-10": "mastered", "make-10": "practising"}
    answers = {
        "count-to-20": _answers((True, _day(1)), (True, _day(2))),  # due on the 5th
        "add-within-10": _answers((True, _day(3))),  # due on the 4th
        "make-10": _answers((True, _day(1))),
    }
    plans = review_plans(SKILL_MAP, statuses, answers, NAIROBI)
    assert [p.skill_id for p in plans] == ["add-within-10", "count-to-20"]


def test_no_review_while_a_needed_skill_is_not_mastered():
    statuses = {"count-to-20": "practising", "add-within-10": "mastered"}
    answers = {"add-within-10": _answers((True, _day(3)))}
    assert review_plans(SKILL_MAP, statuses, answers, NAIROBI) == []


def test_equal_due_dates_keep_teaching_order():
    statuses = {"count-to-20": "mastered", "add-within-10": "mastered"}
    placed = {"add-within-10": _day(10), "count-to-20": _day(10)}
    plans = review_plans(SKILL_MAP, statuses, {}, NAIROBI, placed)
    assert [p.skill_id for p in plans] == ["count-to-20", "add-within-10"]


# --- Reviews in lessons (API) ---------------------------------------------------


@pytest.fixture
def clock(monkeypatch):
    """Control when answers are saved, and what day the review rule thinks it is."""
    current = {"now": _day(1)}
    monkeypatch.setattr(problem_store_module, "now", lambda: current["now"])
    monkeypatch.setattr(
        review_module, "today", lambda tz: review_module.local_day(current["now"], tz)
    )
    return current


def _learner(nickname="Simba"):
    return client.post("/api/learners", json={"nickname": nickname}).json()["id"]


def _solve(db, learner_id, skill_id, right=True):
    problem = client.post(
        "/api/lesson/problems", json={"skill_id": skill_id, "learner_id": learner_id}
    ).json()
    answer = ProblemStore(db).get(problem["id"]).problem.answer
    client.post(
        f"/api/lesson/problems/{problem['id']}/answer",
        json={"answer": answer if right else answer + 50},
    )


def _master_count_to_20(db, clock, lid):
    for d in (1, 2):
        clock["now"] = _day(d)
        _solve(db, lid, "count-to-20")
        _solve(db, lid, "count-to-20")


def _next(lid):
    return client.get(f"/api/learners/{lid}/next-skill").json()


def test_a_due_review_comes_before_new_learning(db, clock):
    lid = _learner()
    _master_count_to_20(db, clock, lid)
    assert _next(lid)["skill_id"] == "add-within-10"

    clock["now"] = _day(4)  # not due yet: the gap is 3 days
    assert _next(lid)["review"] is False

    clock["now"] = _day(5)
    nxt = _next(lid)
    assert nxt["skill_id"] == "count-to-20" and nxt["review"] is True
    assert nxt["status"] == "mastered"
    assert nxt["reason"] == "Quick review: last seen 3 days ago, so it stays strong."

    _solve(db, lid, "count-to-20")  # one review problem is enough
    assert _next(lid) == {**_next(lid), "skill_id": "add-within-10", "review": False}

    reviews = client.get(f"/api/learners/{lid}/reviews").json()
    assert reviews == [
        {
            "skill_id": "count-to-20",
            "name": "Count objects to 20",
            "last_seen": "2026-11-05",
            "streak_days": 3,
            "due_on": "2026-11-12",
            "due": False,
        }
    ]


def test_a_slip_in_a_review_brings_it_back_tomorrow(db, clock):
    lid = _learner()
    _master_count_to_20(db, clock, lid)
    clock["now"] = _day(5)
    _solve(db, lid, "count-to-20", right=False)

    # Still mastered (4 of the last 5), so learning goes on today...
    assert _next(lid)["skill_id"] == "add-within-10"
    # ...and the review comes back tomorrow.
    clock["now"] = _day(6)
    assert _next(lid)["review"] is True and _next(lid)["skill_id"] == "count-to-20"


def _place(db, lid, known, finished_at):
    store = PlacementStore(db)
    placement = store.start(lid)
    store.finish(placement.id, "all-decided", known)
    with db.connect() as conn:
        conn.execute(
            "UPDATE placements SET finished_at = ? WHERE id = ?", (finished_at, placement.id)
        )


def test_skills_from_the_placement_check_are_reviewed_the_next_day(db, clock):
    lid = _learner()
    _place(db, lid, ["count-to-20", "add-within-10"], _day(10))

    clock["now"] = _day(10)
    assert _next(lid) == {**_next(lid), "skill_id": "make-10", "review": False}

    clock["now"] = _day(11)
    nxt = _next(lid)
    assert nxt["skill_id"] == "count-to-20" and nxt["review"] is True
    assert nxt["reason"] == "Quick review: last seen yesterday, so it stays strong."


def test_a_wrong_review_of_a_placed_skill_means_practising_it(db, clock):
    lid = _learner()
    _place(db, lid, ["count-to-20", "add-within-10"], _day(10))
    clock["now"] = _day(11)
    _solve(db, lid, "count-to-20", right=False)

    nxt = _next(lid)
    assert nxt["skill_id"] == "count-to-20"
    assert nxt["review"] is False and nxt["status"] == "practising"


def test_reviews_for_unknown_learner_is_404():
    assert client.get("/api/learners/999/reviews").status_code == 404
