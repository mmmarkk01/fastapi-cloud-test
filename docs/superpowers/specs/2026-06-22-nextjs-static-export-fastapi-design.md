# Next.js (static export) + FastAPI single-app — Design

**Date:** 2026-06-22
**Branch:** `feat/nextjs-frontend`
**Status:** Approved (pending spec review)

## Goal

Serve a Next.js frontend and a FastAPI API from a **single FastAPI app** using
`app.frontend()` (FastAPI ≥ 0.138.0), deployable to FastAPI Cloud. No database.
Next.js runs in **static-export mode** (`output: 'export'`) so the build is pure
static files that `app.frontend()` can serve — FastAPI Cloud runs Python only and
cannot run a Node server, so SSR Next.js is explicitly out of scope.

## Why static export

`app.frontend()` serves pre-built static files only (no SSR). FastAPI Cloud has no
Node runtime. Next.js static export (`output: 'export'`) emits a static `out/` dir
(HTML/CSS/JS) with no server dependency. Because the backend is FastAPI and there is
no database, none of Next's server features (SSR, ISR, Route Handlers, middleware,
server-side `next/image`) are needed — FastAPI is the server.

## Architecture & layout (branch `feat/nextjs-frontend`)

```
frontend/                 # Next.js App Router project (create-next-app)
  app/
    page.tsx              # client component: fetch("/api/hello") + render
    layout.tsx
  next.config.js          # output: 'export'  → builds to frontend/out/
  package.json
  .gitignore              # written by create-next-app; ignores /out, /.next, node_modules
  out/                    # next build output (static) — NOT committed
main.py                   # /api/hello + app.frontend("/", directory="frontend/out")
pyproject.toml            # fastapi[standard]>=0.138.0 (unchanged from main)
.fastapicloudignore       # !frontend/out/  — re-include the build for deploys
tests/test_app.py         # API + frontend-served tests
# web/ is removed on this branch
```

One ASGI app: API path operations are matched first; all other paths fall through to
the Next static build. The frontend is served directly from `frontend/out` (where Next
exports) — no copy-to-root step.

## Components

### `main.py`
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI + Next.js (static export) 🚀"}

app.frontend("/", directory="frontend/out")   # after the API route
```

### `frontend/` Next.js app
- **App Router + TypeScript**, minimal (no Tailwind, no ESLint).
- `next.config.js`: `{ output: 'export' }`.
- `app/page.tsx`: a **client component** (`'use client'`) that on mount fetches
  `/api/hello` and renders the message. Contains a stable marker string
  `FastAPI + Next.js static export` used by tests and curl checks.
- Client-side fetch means the static HTML shows a "loading…" state; the live message
  appears in a browser. The API itself is verified directly via `/api/hello`.

### `.fastapicloudignore`
```
!frontend/out/
!frontend/out/**
```
`create-next-app` ignores `/out` in `frontend/.gitignore`; `fastapi deploy` honors
gitignore, so without this the build is dropped and the deployed app crashes on
startup (`app.frontend` `check_dir=True`). This file re-includes only the build, while
`node_modules`/`.next` stay excluded from the upload.

## Verification plan (local)

1. `cd frontend && npm install && npm run build` → produces `frontend/out`.
2. From repo root: `uv run fastapi dev main.py`.
3. Confirm:
   - `GET /api/hello` → the JSON message.
   - `GET /` → Next static shell containing the marker `FastAPI + Next.js static export`.
   - `GET /_next/...` (a built asset) → `200`.
4. `uv run pytest` — `tests/test_app.py` covers `/api/hello` and `/` serving the HTML.
   Tests require `frontend/out` to exist (built in step 1) because `check_dir=True`.

## Scope / non-goals

- **Build + local verification only. No deploy.** The user manages their own FastAPI
  Cloud deploys; this branch will be deploy-ready via `.fastapicloudignore` but not
  deployed by the assistant.
- No SSR / ISR / Next API routes / middleware / database / auth.
- No custom domains, CI/CD.

## Risks / notes

- `frontend/out` must exist before the app imports (tests and `fastapi dev`). The
  implementation plan builds the frontend before the test task.
- Default Next asset base path `/` matches the root mount (`app.frontend("/", ...)`),
  so `/_next/...` assets resolve correctly.
- `node_modules` is large but gitignored, so it is excluded from any future deploy
  upload automatically.

## References

- `app.frontend()` tutorial: https://fastapi.tiangolo.com/tutorial/frontend/
- Next.js static exports: https://nextjs.org/docs/app/guides/static-exports
- Skill: `deploying-to-fastapi-cloud` (gitignore/`.fastapicloudignore`, check_dir, CI)
