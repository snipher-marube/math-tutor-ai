"""Tests for the Ollama service layer. No real model is called."""

import asyncio
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from ollama import ResponseError

import routers.tutor
import services.ollama_client as ollama_client
from config import settings
from main import app
from services.ollama_client import (
    TutorTimeoutError,
    TutorUnavailableError,
    generate_tutor_response,
)


class _FakeAsyncClient:
    """Stands in for ollama.AsyncClient. Either raises `error` or replies after `delay`."""

    instances: list["_FakeAsyncClient"] = []

    def __init__(self, error: Exception | None = None, delay: float = 0.0):
        self._error = error
        self._delay = delay
        self.closed = False
        _FakeAsyncClient.instances.append(self)

    async def chat(self, **kwargs):
        self.messages = kwargs["messages"]
        if self._error:
            raise self._error
        await asyncio.sleep(self._delay)
        message = type("Message", (), {"content": "1 + 1 = 2"})()
        return type("Response", (), {"message": message})()

    async def close(self):
        self.closed = True


def _use_fake_client(monkeypatch, **kwargs):
    _FakeAsyncClient.instances = []
    monkeypatch.setattr(ollama_client, "AsyncClient", lambda host: _FakeAsyncClient(**kwargs))


def _generate():
    return asyncio.run(generate_tutor_response("What is 1 + 1?"))


def test_returns_model_content_and_closes_client(monkeypatch):
    _use_fake_client(monkeypatch)
    assert _generate() == "1 + 1 = 2"
    assert _FakeAsyncClient.instances[0].closed


def test_connection_error_becomes_unavailable(monkeypatch):
    _use_fake_client(monkeypatch, error=ConnectionError("refused"))
    with pytest.raises(TutorUnavailableError, match="Cannot reach Ollama"):
        _generate()
    assert _FakeAsyncClient.instances[0].closed


def test_missing_model_becomes_unavailable(monkeypatch):
    _use_fake_client(monkeypatch, error=ResponseError("model not found", status_code=404))
    with pytest.raises(TutorUnavailableError, match="ollama pull"):
        _generate()


def test_other_ollama_errors_are_not_hidden(monkeypatch):
    _use_fake_client(monkeypatch, error=ResponseError("boom", status_code=500))
    with pytest.raises(ResponseError):
        _generate()


def test_ask_returns_503_when_tutor_unavailable(monkeypatch):
    async def unavailable(question: str, grade: int = 2) -> str:
        raise TutorUnavailableError("Cannot reach Ollama")

    monkeypatch.setattr(routers.tutor, "generate_tutor_response", unavailable)
    res = TestClient(app).post("/api/tutor/ask", json={"question": "What is 1 + 1?"})
    assert res.status_code == 503
    assert res.json() == {"detail": "Cannot reach Ollama"}


def test_slow_model_does_not_block_other_requests(monkeypatch):
    """Three requests that each wait 0.5s should finish together, not one after another."""
    _use_fake_client(monkeypatch, delay=0.5)

    async def three_requests():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            body = {"question": "What is 1 + 1?"}
            return await asyncio.gather(
                *(client.post("/api/tutor/ask", json=body) for _ in range(3))
            )

    start = time.perf_counter()
    responses = asyncio.run(three_requests())
    elapsed = time.perf_counter() - start

    assert all(r.status_code == 200 for r in responses)
    assert elapsed < 1.0, f"requests ran one after another ({elapsed:.2f}s)"


def test_slow_model_times_out_and_closes_client(monkeypatch):
    _use_fake_client(monkeypatch, delay=0.5)
    monkeypatch.setattr(settings, "OLLAMA_TIMEOUT", 0.05)
    with pytest.raises(TutorTimeoutError, match="longer than 0.05 seconds"):
        _generate()
    assert _FakeAsyncClient.instances[0].closed


def test_ask_returns_504_when_model_times_out(monkeypatch):
    _use_fake_client(monkeypatch, delay=0.5)
    monkeypatch.setattr(settings, "OLLAMA_TIMEOUT", 0.05)
    res = TestClient(app).post("/api/tutor/ask", json={"question": "What is 1 + 1?"})
    assert res.status_code == 504
    assert "OLLAMA_TIMEOUT" in res.json()["detail"]


def test_sends_the_prompt_file_for_the_learners_grade(monkeypatch):
    _use_fake_client(monkeypatch)
    asyncio.run(generate_tutor_response("What is 1 + 1?", grade=3))
    system, user = _FakeAsyncClient.instances[0].messages
    assert system["role"] == "system" and "Grade 3" in system["content"]
    assert user == {"role": "user", "content": "What is 1 + 1?"}
