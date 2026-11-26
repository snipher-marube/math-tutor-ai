"""Shared test setup.

Every test gets its own temporary database, so tests never touch a real
learner database and never affect each other.
"""

import pytest

from dependencies import get_db
from main import app
from services.db import Database


@pytest.fixture(autouse=True)
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    database.init()
    app.dependency_overrides[get_db] = lambda: database
    yield database
    app.dependency_overrides.pop(get_db, None)
