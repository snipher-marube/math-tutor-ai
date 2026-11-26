"""Local SQLite database for learners, problems and answers.

Everything stays in one file on the device (DATABASE_PATH). Nothing is ever sent
anywhere. See the data and privacy rules in docs/CHILD_SAFETY.md.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (
    id          INTEGER PRIMARY KEY,
    nickname    TEXT NOT NULL UNIQUE COLLATE NOCASE,
    avatar      TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problems (
    id          TEXT PRIMARY KEY,
    -- learner_id is NULL for practice without a learner
    learner_id  INTEGER REFERENCES learners(id) ON DELETE CASCADE,
    skill_id    TEXT NOT NULL,
    kind        TEXT NOT NULL,
    question    TEXT NOT NULL,
    operands    TEXT NOT NULL,   -- JSON list of integers
    answer      INTEGER NOT NULL,
    seed        INTEGER NOT NULL,
    solved      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS problems_learner_skill ON problems(learner_id, skill_id);

CREATE TABLE IF NOT EXISTS attempts (
    id             INTEGER PRIMARY KEY,
    problem_id     TEXT NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    given          INTEGER NOT NULL,
    correct        INTEGER NOT NULL,
    misconception  TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS attempts_problem ON attempts(problem_id);
"""


def now() -> str:
    """Current time in UTC, as an ISO string."""
    return datetime.now(UTC).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def init(self) -> None:
        """Create the file and tables if they don't exist yet. Safe to run every startup."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(SCHEMA)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits on success and rolls back on error."""
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
