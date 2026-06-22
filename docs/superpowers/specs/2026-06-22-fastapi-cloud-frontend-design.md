# Minimal FastAPI Cloud app using `app.frontend()` — Design

**Date:** 2026-06-22
**Status:** Approved (pending spec review)

## Goal

Build the smallest possible FastAPI app that uses the new `app.frontend()` feature
(added in FastAPI **0.138.0**, released 2026-06-20) to serve a frontend and a JSON API
from a **single ASGI app**, then deploy it to **FastAPI Cloud** to confirm the platform
hosts the frontend automatically alongside the API.

## Core finding (the "can I host it?" answer)

Yes. `app.frontend()` does not start a separate server — it registers routes inside the
FastAPI app (backed by `StaticFiles` with SPA-style fallback). FastAPI Cloud runs that
same ASGI app via `fastapi deploy`, so the one deployed process serves both the API and
the frontend on one URL. No separate static host is required.

**Caveat:** FastAPI Cloud runs Python only — it does **not** run a JS build step. The
served directory must already exist in the uploaded bundle, and `app.frontend()` defaults
to `check_dir=True`, so a missing directory crashes the app at startup. We therefore avoid
any build step and avoid gitignored directories (see below).

## Approach

Hand-written static frontend (no Node, no npm, no build step), served from a directory
that is **not** gitignored.

### Project structure
```
fastapi-cloud-test/
├── main.py              # entire backend
├── web/                 # hand-written frontend — NOT gitignored
│   ├── index.html       # fetches /api/hello and renders the result
│   └── style.css
├── pyproject.toml       # dependency: fastapi[standard] >= 0.138.0 (uv-managed)
├── .gitignore           # existing (standard Python; ignores dist/ and build/)
├── LICENSE              # existing
└── README.md            # existing
```

### `main.py`
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/hello")          # API route FIRST — takes precedence
def hello():
    return {"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}

app.frontend("/", directory="web")   # frontend LAST — matched only if no API route did
```

### Frontend (`web/index.html`)
A minimal page that calls `fetch("/api/hello")` on load and renders the returned message,
visibly proving the API and frontend are served by the same app on the same origin.
Plain HTML/CSS/JS, no framework, no build.

## Key design decisions

1. **Serve from `web/`, not `dist/`.** `app.frontend()` accepts any directory name. The
   repo's standard Python `.gitignore` ignores `dist/` (line 13) and `build/`. If
   `fastapi deploy` honors gitignore, a `dist/` frontend would be silently excluded and the
   app would crash on boot (`check_dir=True`). `web/` is untracked by gitignore, so it
   commits and uploads reliably.
2. **No build step.** A hand-written `index.html` is a valid frontend for `app.frontend()`,
   which serves pre-built static files only. This removes the Node toolchain and the
   "build before deploy" failure mode entirely.
3. **Route ordering.** `app.frontend()` is declared after all `/api/...` path operations.
   FastAPI checks path operations first; frontend files are only checked if no route matched.

## Verification plan

1. Create a `uv` virtual environment and install `fastapi[standard]>=0.138.0`; confirm the
   installed FastAPI version is ≥ 0.138.0 (required for `app.frontend`).
2. Run `fastapi dev main.py` and confirm:
   - `GET /api/hello` returns the JSON message.
   - `GET /` returns the `web/index.html` page (frontend served by the same app).
3. Confirm the dependency manifest format FastAPI Cloud expects (pyproject vs requirements)
   against the FastAPI Cloud docs before deploying.

## Deployment plan

1. User runs `fastapi login` interactively (via the `!` prefix) — it targets their own
   FastAPI Cloud account and provisions a real, billable app.
2. Run `fastapi deploy`.
3. Confirm the live URL serves both `/api/hello` (JSON) and `/` (frontend).
4. **Risk to watch:** verify the uploaded bundle actually contains `web/index.html` so the
   deployed app boots (guards against any gitignore-based file exclusion).

## Out of scope (YAGNI)

- JS frameworks / build tooling (React, Vite, etc.).
- Databases, auth, multiple endpoints, environment config.
- Custom domains, CI/CD.

## References

- FastAPI 0.138.0 release notes: https://fastapi.tiangolo.com/release-notes/
- `app.frontend()` tutorial: https://fastapi.tiangolo.com/tutorial/frontend/
- PR #15800: https://github.com/fastapi/fastapi/pull/15800
- FastAPI Cloud getting-started: https://fastapicloud.com/docs/getting-started/
