"""Serve the built web app from FastAPI, so the whole tutor runs as one process.

After `npm run build` (or `make start`), the app is in `frontend/dist`. When that
folder has an `index.html`, the app is served at `/`, next to the API at `/api`.
Without a build, nothing changes: run Vite for development as usual.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def has_build(dist: Path) -> bool:
    return (dist / "index.html").is_file()


def serve_frontend(app: FastAPI, dist: Path) -> bool:
    """Serve the built app at `/`. Returns False (and does nothing) without a build.

    Call this after adding every API route: the app is mounted last, so `/api`,
    `/docs` and `/health` are matched first.
    """
    if not has_build(dist):
        return False
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return True
