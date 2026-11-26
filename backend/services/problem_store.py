"""Remember the problems handed out, so answers are checked on the server.

The answer never goes to the browser. The frontend gets a problem id, and sends
the child's answer back with it.

This store is in memory: problems are lost when the server restarts. That's fine
until learner progress is stored locally (see docs/ROADMAP.md).
"""

from __future__ import annotations

import random
import secrets
from collections import OrderedDict
from dataclasses import dataclass, field

from services.problems import Problem

MAX_STORED_PROBLEMS = 10_000  # oldest problems are forgotten first


@dataclass
class StoredProblem:
    id: str
    problem: Problem
    seed: int  # makes the hint ladder the same every time it's asked for
    attempts: int = 0
    solved: bool = False
    given_answers: list[int] = field(default_factory=list)


class ProblemStore:
    def __init__(self, max_size: int = MAX_STORED_PROBLEMS):
        self._items: OrderedDict[str, StoredProblem] = OrderedDict()
        self._max_size = max_size

    def __len__(self) -> int:
        return len(self._items)

    def add(self, problem: Problem) -> StoredProblem:
        stored = StoredProblem(
            id=secrets.token_hex(8),
            problem=problem,
            seed=random.randrange(2**32),
        )
        self._items[stored.id] = stored
        while len(self._items) > self._max_size:
            self._items.popitem(last=False)
        return stored

    def get(self, problem_id: str) -> StoredProblem | None:
        return self._items.get(problem_id)
