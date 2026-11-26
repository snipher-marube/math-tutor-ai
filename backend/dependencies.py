"""Shared FastAPI dependencies. Tests override `get_db` to use a temporary database."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from config import settings
from services.db import Database
from services.learners import LearnerStore
from services.problem_store import ProblemStore
from services.skill_map import SkillMap, load_skill_map


@lru_cache
def get_db() -> Database:
    db = Database(settings.DATABASE_PATH)
    db.init()
    return db


@lru_cache
def get_skill_map() -> SkillMap:
    return load_skill_map()


def get_problem_store(db: Annotated[Database, Depends(get_db)]) -> ProblemStore:
    return ProblemStore(db)


def get_learner_store(db: Annotated[Database, Depends(get_db)]) -> LearnerStore:
    return LearnerStore(db)


SkillMapDep = Annotated[SkillMap, Depends(get_skill_map)]
ProblemStoreDep = Annotated[ProblemStore, Depends(get_problem_store)]
LearnerStoreDep = Annotated[LearnerStore, Depends(get_learner_store)]
