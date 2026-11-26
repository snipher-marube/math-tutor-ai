"""Request validation for /api/tutor/ask. The model is faked."""

import pytest
from fastapi.testclient import TestClient

import routers.tutor
from config import settings
from main import app
from routers.tutor import MAX_QUESTION_LENGTH

client = TestClient(app)


@pytest.fixture
def received(monkeypatch):
    """Fake the model and record what it was called with."""
    calls: list[tuple[str, int]] = []

    async def fake_generate(question: str, grade: int = 2) -> str:
        calls.append((question, grade))
        return "= 2"

    monkeypatch.setattr(routers.tutor, "generate_tutor_response", fake_generate)
    return calls


def _ask(**body):
    return client.post("/api/tutor/ask", json=body)


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_rejects_empty_question(received, question):
    assert _ask(question=question).status_code == 422
    assert received == []


def test_rejects_too_long_question(received):
    assert _ask(question="a" * (MAX_QUESTION_LENGTH + 1)).status_code == 422
    assert received == []


def test_accepts_question_at_max_length(received):
    assert _ask(question="a" * MAX_QUESTION_LENGTH).status_code == 200


def test_trims_surrounding_whitespace(received):
    _ask(question="  What is 1 + 1?  ")
    assert received[0][0] == "What is 1 + 1?"


@pytest.mark.parametrize("grade", [0, 4, -1])
def test_rejects_grade_out_of_range(received, grade):
    assert _ask(question="What is 1 + 1?", grade=grade).status_code == 422
    assert received == []


def test_grade_defaults_to_setting(received, monkeypatch):
    monkeypatch.setattr(settings, "GRADE_LEVEL", 3)
    _ask(question="What is 1 + 1?")
    assert received[0][1] == 3
