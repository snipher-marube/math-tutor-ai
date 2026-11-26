"""Tests for how Ollama failures are surfaced. No real model is called."""

import pytest
from fastapi.testclient import TestClient
from ollama import ResponseError

import routers.tutor
import services.ollama_client as ollama_client
from main import app
from services.ollama_client import TutorUnavailableError, generate_tutor_response


class _FailingClient:
    def __init__(self, error: Exception):
        self._error = error

    def chat(self, **kwargs):
        raise self._error


def _use_failing_client(monkeypatch, error: Exception):
    monkeypatch.setattr(ollama_client, "Client", lambda host: _FailingClient(error))


def test_connection_error_becomes_unavailable(monkeypatch):
    _use_failing_client(monkeypatch, ConnectionError("refused"))
    with pytest.raises(TutorUnavailableError, match="Cannot reach Ollama"):
        generate_tutor_response("What is 1 + 1?")


def test_missing_model_becomes_unavailable(monkeypatch):
    _use_failing_client(monkeypatch, ResponseError("model not found", status_code=404))
    with pytest.raises(TutorUnavailableError, match="ollama pull"):
        generate_tutor_response("What is 1 + 1?")


def test_other_ollama_errors_are_not_hidden(monkeypatch):
    _use_failing_client(monkeypatch, ResponseError("boom", status_code=500))
    with pytest.raises(ResponseError):
        generate_tutor_response("What is 1 + 1?")


def test_ask_returns_503_when_tutor_unavailable(monkeypatch):
    def unavailable(question: str, grade: int = 2) -> str:
        raise TutorUnavailableError("Cannot reach Ollama")

    monkeypatch.setattr(routers.tutor, "generate_tutor_response", unavailable)
    res = TestClient(app).post("/api/tutor/ask", json={"question": "What is 1 + 1?"})
    assert res.status_code == 503
    assert res.json() == {"detail": "Cannot reach Ollama"}
