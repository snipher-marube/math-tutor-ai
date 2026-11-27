"""Tests for the mastery rule and choosing the next skill."""

import pytest
from fastapi.testclient import TestClient

import services.problem_store as problem_store_module
import services.review as review_module
from main import app
from services.mastery import FirstAnswer, next_skill, skill_mastery
from services.problem_store import ProblemStore
from services.skill_map import load_skill_map

NAIROBI = "Africa/Nairobi"
SKILL_MAP = load_skill_map()


def _answers(*spec: tuple[bool, str]) -> list[FirstAnswer]:
    return [FirstAnswer(correct, at) for correct, at in spec]


DAY1 = "2026-11-24T08:00:00+00:00"
DAY2 = "2026-11-25T08:00:00+00:00"


def _at(day: str, minute: int) -> str:
    return day.replace(":00:00", f":{minute:02d}:00")


# --- The rule -------------------------------------------------------------------


def test_no_answers_is_not_started():
    assert skill_mastery([], NAIROBI).status == "not-started"


def test_four_of_five_over_two_days_is_mastered():
    m = skill_mastery(
        _answers(
            (True, _at(DAY1, 1)),
            (True, _at(DAY1, 2)),
            (False, _at(DAY2, 1)),
            (True, _at(DAY2, 2)),
            (True, _at(DAY2, 3)),
        ),
        NAIROBI,
    )
    assert (m.status, m.recent_total, m.recent_correct, m.correct_days) == ("mastered", 5, 4, 2)


def test_all_correct_on_one_day_is_not_mastered_yet():
    m = skill_mastery(_answers(*[(True, _at(DAY1, i)) for i in range(5)]), NAIROBI)
    assert m.status == "practising"
    assert m.correct_days == 1


def test_three_of_five_is_practising():
    m = skill_mastery(
        _answers(
            (True, _at(DAY1, 1)),
            (False, _at(DAY1, 2)),
            (True, _at(DAY2, 1)),
            (False, _at(DAY2, 2)),
            (True, _at(DAY2, 3)),
        ),
        NAIROBI,
    )
    assert (m.status, m.recent_correct) == ("practising", 3)


def test_wrong_answers_on_another_day_dont_count_as_a_day():
    m = skill_mastery(
        _answers(*[(True, _at(DAY1, i)) for i in range(4)], (False, _at(DAY2, 1))),
        NAIROBI,
    )
    assert m.status == "practising"
    assert m.correct_days == 1


def test_only_the_latest_five_count_so_mastery_can_be_lost():
    earlier = [(True, _at(DAY1, i)) for i in range(3)] + [(True, _at(DAY2, i)) for i in range(2)]
    assert skill_mastery(_answers(*earlier), NAIROBI).status == "mastered"
    later = earlier + [(False, _at(DAY2, 10)), (False, _at(DAY2, 11))]
    m = skill_mastery(_answers(*later), NAIROBI)
    assert (m.status, m.recent_total, m.recent_correct) == ("practising", 5, 3)


def test_order_of_answers_does_not_matter():
    spec = [(True, _at(DAY1, 1)), (True, _at(DAY2, 1)), (True, _at(DAY1, 2)), (True, _at(DAY2, 2))]
    assert skill_mastery(_answers(*spec), NAIROBI) == skill_mastery(
        _answers(*reversed(spec)), NAIROBI
    )


def test_days_are_counted_in_local_time():
    """23:00 and 01:30 Nairobi time are different days, even on the same UTC date."""
    spec = [
        (True, "2026-11-26T20:00:00+00:00"),  # 23:00 on the 26th in Nairobi
        (True, "2026-11-26T20:10:00+00:00"),
        (True, "2026-11-26T22:30:00+00:00"),  # 01:30 on the 27th in Nairobi
        (True, "2026-11-26T22:40:00+00:00"),
    ]
    assert skill_mastery(_answers(*spec), NAIROBI).status == "mastered"
    assert skill_mastery(_answers(*spec), "UTC").status == "practising"


# --- Next skill -----------------------------------------------------------------


def test_new_learner_starts_at_the_first_skill():
    nxt = next_skill(SKILL_MAP, {})
    assert nxt.skill.id == "count-to-20"
    assert nxt.status == "not-started"
    assert nxt.reason.startswith("Start here")


def test_moves_on_once_prerequisites_are_mastered():
    nxt = next_skill(SKILL_MAP, {"count-to-20": "mastered"})
    assert nxt.skill.id == "add-within-10"
    assert nxt.reason.startswith("Ready to start")


def test_keeps_practising_an_unmastered_skill():
    nxt = next_skill(SKILL_MAP, {"count-to-20": "mastered", "add-within-10": "practising"})
    assert nxt.skill.id == "add-within-10"
    assert nxt.reason.startswith("Keep practising")


def test_follows_teaching_order_across_sub_strands():
    addition = ["count-to-20", "add-within-10", "make-10", "add-within-20"]
    done = {s: "mastered" for s in addition}
    assert next_skill(SKILL_MAP, done).skill.id == "subtract-within-10"
    done |= {"subtract-within-10": "mastered", "subtract-within-20": "mastered"}
    assert next_skill(SKILL_MAP, done).skill.id == "count-to-100"


def test_goes_back_when_a_prerequisite_is_no_longer_mastered():
    nxt = next_skill(SKILL_MAP, {"count-to-20": "practising", "add-within-10": "mastered"})
    assert nxt.skill.id == "count-to-20"


def test_everything_mastered():
    nxt = next_skill(SKILL_MAP, {s.id: "mastered" for s in SKILL_MAP})
    assert nxt.skill is None
    assert "Every skill is mastered" in nxt.reason


def test_next_skill_always_has_its_prerequisites_mastered():
    statuses = {}
    for _ in SKILL_MAP:
        nxt = next_skill(SKILL_MAP, statuses)
        assert all(statuses.get(r) == "mastered" for r in nxt.skill.requires)
        statuses[nxt.skill.id] = "mastered"
    assert next_skill(SKILL_MAP, statuses).skill is None


# --- Through the API ------------------------------------------------------------

client = TestClient(app)


@pytest.fixture
def clock(monkeypatch):
    """Control the time answers are saved at, and what day reviews think it is."""
    current = {"now": DAY1}
    monkeypatch.setattr(problem_store_module, "now", lambda: current["now"])
    monkeypatch.setattr(
        review_module, "today", lambda tz: review_module.local_day(current["now"], tz)
    )
    return current


def _solve(db, learner_id, skill_id, answers):
    problem = client.post(
        "/api/lesson/problems", json={"skill_id": skill_id, "learner_id": learner_id}
    ).json()
    right = ProblemStore(db).get(problem["id"]).problem.answer
    for answer in answers:
        given = right if answer == "right" else right + 50
        client.post(f"/api/lesson/problems/{problem['id']}/answer", json={"answer": given})


def test_full_journey_to_mastery_and_the_next_skill(db, clock):
    learner = client.post("/api/learners", json={"nickname": "Simba"}).json()
    lid = learner["id"]
    next_url = f"/api/learners/{lid}/next-skill"
    assert client.get(next_url).json()["skill_id"] == "count-to-20"

    # Day 1: three right on the first try.
    for _ in range(3):
        _solve(db, lid, "count-to-20", ["right"])
    assert client.get(next_url).json()["reason"].startswith("Keep practising")

    # Day 2: one right after a retry (doesn't count), then one right first time.
    clock["now"] = DAY2
    _solve(db, lid, "count-to-20", ["wrong", "right"])
    _solve(db, lid, "count-to-20", ["right"])

    progress = client.get(f"/api/learners/{lid}/progress").json()[0]
    assert progress["skill_id"] == "count-to-20"
    assert progress["status"] == "mastered"
    assert (progress["recent_total"], progress["recent_correct"]) == (5, 4)
    assert progress["correct_days"] == 2
    assert progress["attempts"] == 6  # retries are still counted in the totals

    nxt = client.get(next_url).json()
    assert nxt == {
        "skill_id": "add-within-10",
        "name": "Add within 10",
        "grade": 1,
        "status": "not-started",
        "review": False,
        "reason": "Ready to start: all the skills it needs are mastered.",
    }


def test_a_right_answer_after_a_retry_does_not_count(db, clock):
    lid = client.post("/api/learners", json={"nickname": "Amina"}).json()["id"]
    for day in (DAY1, DAY2):
        clock["now"] = day
        for _ in range(3):
            _solve(db, lid, "count-to-20", ["wrong", "right"])
    progress = client.get(f"/api/learners/{lid}/progress").json()[0]
    assert progress["status"] == "practising"
    assert progress["recent_correct"] == 0


def test_started_but_unanswered_skill_shows_as_practising(db):
    lid = client.post("/api/learners", json={"nickname": "Kiprop"}).json()["id"]
    client.post("/api/lesson/problems", json={"skill_id": "make-10", "learner_id": lid})
    progress = client.get(f"/api/learners/{lid}/progress").json()[0]
    assert progress["status"] == "practising"
    assert progress["recent_total"] == 0


def test_next_skill_for_unknown_learner_is_404():
    assert client.get("/api/learners/999/next-skill").status_code == 404


def test_unknown_timezone_fails_at_startup():
    from pydantic import ValidationError

    from config import Settings

    with pytest.raises(ValidationError, match="Unknown time zone"):
        Settings(TIMEZONE="Mars/Olympus_Mons")
    assert Settings(TIMEZONE="Africa/Nairobi").TIMEZONE == "Africa/Nairobi"
