"""Shared FastAPI dependencies. Tests override `get_db` to use a temporary database."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from config import settings
from services.db import Database
from services.learners import LearnerStore
from services.problem_store import ProblemStore


@lru_cache
def get_db() -> Database:
    db = Database(settings.DATABASE_PATH)
    db.init()
    return db


def get_problem_store(db: Annotated[Database, Depends(get_db)]) -> ProblemStore:
    return ProblemStore(db)


def get_learner_store(db: Annotated[Database, Depends(get_db)]) -> LearnerStore:
    return LearnerStore(db)


ProblemStoreDep = Annotated[ProblemStore, Depends(get_problem_store)]
LearnerStoreDep = Annotated[LearnerStore, Depends(get_learner_store)]
