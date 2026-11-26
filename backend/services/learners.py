"""Learners and their progress, stored only on this device.

A learner is a nickname and an optional animal picture. Never a real full name,
and no other personal details. Teachers and parents can view and reset progress.
See docs/CHILD_SAFETY.md.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from services.db import Database, now

AVATARS = ("lion", "elephant", "giraffe", "zebra", "cheetah", "rhino", "hippo", "monkey")


class NicknameTakenError(Exception):
    pass


@dataclass(frozen=True)
class Learner:
    id: int
    nickname: str
    avatar: str | None
    created_at: str


@dataclass(frozen=True)
class SkillProgress:
    skill_id: str
    problems: int  # problems started
    attempts: int  # answers given
    correct: int  # correct answers
    last_practised: str


class LearnerStore:
    def __init__(self, db: Database):
        self._db = db

    def create(self, nickname: str, avatar: str | None = None) -> Learner:
        created_at = now()
        try:
            with self._db.connect() as conn:
                cur = conn.execute(
                    "INSERT INTO learners (nickname, avatar, created_at) VALUES (?, ?, ?)",
                    (nickname, avatar, created_at),
                )
        except sqlite3.IntegrityError as e:
            raise NicknameTakenError(nickname) from e
        return Learner(cur.lastrowid, nickname, avatar, created_at)

    def list(self) -> list[Learner]:
        with self._db.connect() as conn:
            rows = conn.execute("SELECT * FROM learners ORDER BY nickname COLLATE NOCASE")
            return [_learner(r) for r in rows]

    def get(self, learner_id: int) -> Learner | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM learners WHERE id = ?", (learner_id,)).fetchone()
        return _learner(row) if row else None

    def delete(self, learner_id: int) -> bool:
        """Remove the learner and all their problems and answers."""
        with self._db.connect() as conn:
            cur = conn.execute("DELETE FROM learners WHERE id = ?", (learner_id,))
        return cur.rowcount > 0

    def reset_progress(self, learner_id: int) -> None:
        """Remove all problems and answers, but keep the learner."""
        with self._db.connect() as conn:
            conn.execute("DELETE FROM problems WHERE learner_id = ?", (learner_id,))

    def progress(self, learner_id: int) -> list[SkillProgress]:
        """Per-skill totals for skills the learner has practised."""
        with self._db.connect() as conn:
            rows = conn.execute(
                """SELECT p.skill_id,
                          COUNT(DISTINCT p.id)             AS problems,
                          COUNT(a.id)                      AS attempts,
                          COALESCE(SUM(a.correct), 0)      AS correct,
                          MAX(COALESCE(a.created_at, p.created_at)) AS last_practised
                   FROM problems p LEFT JOIN attempts a ON a.problem_id = p.id
                   WHERE p.learner_id = ?
                   GROUP BY p.skill_id
                   ORDER BY last_practised DESC""",
                (learner_id,),
            )
            return [SkillProgress(**dict(r)) for r in rows]


def _learner(row: sqlite3.Row) -> Learner:
    return Learner(row["id"], row["nickname"], row["avatar"], row["created_at"])
