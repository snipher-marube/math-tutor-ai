"""Remember the problems handed out, so answers are checked on the server.

The answer never goes to the browser. The frontend gets a problem id, and sends
the child's answer back with it. Problems and every answer are saved in the local
database, so they survive a restart and build up each learner's progress.
"""

from __future__ import annotations

import json
import random
import secrets
from dataclasses import dataclass

from services.db import Database, now
from services.problems import Problem


@dataclass(frozen=True)
class StoredProblem:
    id: str
    problem: Problem
    seed: int  # makes the hint ladder the same every time it's asked for
    learner_id: int | None
    attempts: int
    solved: bool
    given_answers: tuple[int, ...]


class ProblemStore:
    def __init__(self, db: Database):
        self._db = db

    def add(
        self, problem: Problem, learner_id: int | None = None, placement_id: int | None = None
    ) -> StoredProblem:
        """Save a new problem. With `placement_id`, it is part of that placement check."""
        problem_id = secrets.token_hex(8)
        seed = random.randrange(2**32)
        with self._db.connect() as conn:
            conn.execute(
                """INSERT INTO problems
                   (id, learner_id, skill_id, kind, question, operands, answer, seed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    problem_id,
                    learner_id,
                    problem.skill_id,
                    problem.kind,
                    problem.question,
                    json.dumps(list(problem.operands)),
                    problem.answer,
                    seed,
                    now(),
                ),
            )
            if placement_id is not None:
                conn.execute(
                    """INSERT INTO placement_problems (problem_id, placement_id, position)
                       VALUES (?, ?, (SELECT COUNT(*) + 1 FROM placement_problems
                                      WHERE placement_id = ?))""",
                    (problem_id, placement_id, placement_id),
                )
        return StoredProblem(problem_id, problem, seed, learner_id, 0, False, ())

    def get(self, problem_id: str) -> StoredProblem | None:
        with self._db.connect() as conn:
            row = conn.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
            if row is None:
                return None
            given = [
                r["given"]
                for r in conn.execute(
                    "SELECT given FROM attempts WHERE problem_id = ? ORDER BY id", (problem_id,)
                )
            ]
        problem = Problem(
            skill_id=row["skill_id"],
            kind=row["kind"],
            question=row["question"],
            operands=tuple(json.loads(row["operands"])),
            answer=row["answer"],
        )
        return StoredProblem(
            id=row["id"],
            problem=problem,
            seed=row["seed"],
            learner_id=row["learner_id"],
            attempts=len(given),
            solved=bool(row["solved"]),
            given_answers=tuple(given),
        )

    def record_attempt(
        self, problem_id: str, given: int, correct: bool, misconception: str | None
    ) -> int:
        """Save one answer. Returns how many answers this problem has had so far."""
        with self._db.connect() as conn:
            conn.execute(
                """INSERT INTO attempts (problem_id, given, correct, misconception, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (problem_id, given, int(correct), misconception, now()),
            )
            if correct:
                conn.execute("UPDATE problems SET solved = 1 WHERE id = ?", (problem_id,))
            (count,) = conn.execute(
                "SELECT COUNT(*) FROM attempts WHERE problem_id = ?", (problem_id,)
            ).fetchone()
        return count
