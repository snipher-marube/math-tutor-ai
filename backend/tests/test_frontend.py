"""Tests for serving the built web app from FastAPI (one process)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from frontend import has_build, serve_frontend
from main import app


def _build(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Math tutor</title>")
    (dist / "assets" / "index-abc123.js").write_text("console.log('hi')")
    return dist


def _app_with(dist):
    test_app = FastAPI()

    @test_app.get("/api/ping")
    def ping():
        return {"pong": True}

    served = serve_frontend(test_app, dist)
    return test_app, served


def test_serves_the_app_and_keeps_the_api(tmp_path):
    test_app, served = _app_with(_build(tmp_path))
    client = TestClient(test_app)
    assert served

    page = client.get("/")
    assert page.status_code == 200
    assert "<title>Math tutor</title>" in page.text

    asset = client.get("/assets/index-abc123.js")
    assert asset.status_code == 200
    assert "javascript" in asset.headers["content-type"]

    assert client.get("/api/ping").json() == {"pong": True}


def test_unknown_paths_are_404_not_the_app(tmp_path):
    test_app, _ = _app_with(_build(tmp_path))
    client = TestClient(test_app)
    assert client.get("/api/nope").status_code == 404
    assert client.get("/../config.py").status_code == 404


def test_without_a_build_nothing_is_served(tmp_path):
    assert not has_build(tmp_path / "missing")
    test_app, served = _app_with(tmp_path / "missing")
    assert not served
    assert TestClient(test_app).get("/").status_code == 404


def test_without_a_build_the_root_says_how_to_start():
    res = TestClient(app).get("/")
    assert res.status_code == 200
    assert "make start" in res.json()["message"]
