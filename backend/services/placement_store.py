"""Placement checks, stored only on this device.

A placement check is a row in `placements` plus its problems (linked through
`placement_problems`). Problems and answers use the normal `problems` and
`attempts` tables, so deleting a learner or resetting progress removes them too.
See services/placement.py for how the check decides what to ask.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass

from services.db import Database, now
from services.placement import PlacementAnswer


@dataclass(frozen=True)
class Placement:
    id: int
    learner_id: int
    started_at: str
    finished_at: str | None
    stop_reason: str | None
    known_skills: tuple[str, ...]  # empty until finished


@dataclass(frozen=True)
class PlacementItem:
    problem_id: str
    skill_id: str
    correct: bool | None  # the first answer; None while not answered yet


class PlacementStore:
    def __init__(self, db: Database):
        self._db = db

    def start(self, learner_id: int) -> Placement:
        started_at = now()
        with self._db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO placements (learner_id, started_at) VALUES (?, ?)",
                (learner_id, started_at),
            )
        return Placement(cur.lastrowid, learner_id, started_at, None, None, ())

    def get(self, placement_id: int) -> Placement | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM placements WHERE id = ?", (placement_id,)).fetchone()
        return _placement(row) if row else None

    def latest_finished(self, learner_id: int) -> Placement | None:
        """The learner's most recent finished check. A re-run replaces the one before."""
        with self._db.connect() as conn:
            row = conn.execute(
                """SELECT * FROM placements
                   WHERE learner_id = ? AND finished_at IS NOT NULL
                   ORDER BY finished_at DESC, id DESC LIMIT 1""",
                (learner_id,),
            ).fetchone()
        return _placement(row) if row else None

    def items(self, placement_id: int) -> list[PlacementItem]:
        """The check's problems in the order they were asked, with their first answers."""
        with self._db.connect() as conn:
            rows = conn.execute(
                """SELECT p.id, p.skill_id,
                          (SELECT correct FROM attempts WHERE problem_id = p.id
                           ORDER BY id LIMIT 1) AS correct
                   FROM placement_problems pp JOIN problems p ON p.id = pp.problem_id
                   WHERE pp.placement_id = ?
                   ORDER BY pp.position""",
                (placement_id,),
            )
            return [
                PlacementItem(r["id"], r["skill_id"], _bool_or_none(r["correct"])) for r in rows
            ]

    def finish(self, placement_id: int, stop_reason: str, known_skills: Iterable[str]) -> None:
        with self._db.connect() as conn:
            conn.execute(
                """UPDATE placements SET finished_at = ?, stop_reason = ?, known_skills = ?
                   WHERE id = ?""",
                (now(), stop_reason, json.dumps(sorted(known_skills)), placement_id),
            )


def answered(items: Iterable[PlacementItem]) -> list[PlacementAnswer]:
    """The answers so far, in the form services.placement.placement_state expects."""
    return [PlacementAnswer(i.skill_id, i.correct) for i in items if i.correct is not None]


def _bool_or_none(value: int | None) -> bool | None:
    return None if value is None else bool(value)


def _placement(row: sqlite3.Row) -> Placement:
    return Placement(
        id=row["id"],
        learner_id=row["learner_id"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        stop_reason=row["stop_reason"],
        known_skills=tuple(json.loads(row["known_skills"] or "[]")),
    )
