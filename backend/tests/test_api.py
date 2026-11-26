"""API smoke tests. Ollama is mocked, so these run without a model installed."""

from fastapi.testclient import TestClient

import routers.tutor
from main import app

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ask_returns_explanation(monkeypatch):
    async def fake_generate(question: str, grade: int = 2) -> str:
        return f"Grade {grade}: 2 + 3 = 5"

    monkeypatch.setattr(routers.tutor, "generate_tutor_response", fake_generate)
    res = client.post("/api/tutor/ask", json={"question": "What is 2 + 3?"})
    assert res.status_code == 200
    assert res.json() == {
        "explanation": "Grade 2: 2 + 3 = 5",
        "model_answer": 5.0,
        "correct_answer": 5.0,
        "is_correct": True,
        "verification_note": "ok",
    }


def test_ask_requires_question():
    res = client.post("/api/tutor/ask", json={})
    assert res.status_code == 422
