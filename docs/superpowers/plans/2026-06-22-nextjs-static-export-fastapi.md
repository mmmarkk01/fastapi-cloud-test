# Next.js (static export) + FastAPI single-app — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve a Next.js static-export frontend and a FastAPI API from one ASGI app via `app.frontend()`, verified locally and deploy-ready (no deploy).

**Architecture:** A `frontend/` Next.js App Router project builds to static files (`output: 'export'` → `frontend/out`). `main.py` exposes `/api/hello` and serves `frontend/out` via `app.frontend("/", directory="frontend/out")`. A root `.fastapicloudignore` re-includes the build that Next's gitignore drops, so `fastapi deploy` would work.

**Tech Stack:** Python 3.12 + FastAPI ≥ 0.138.0 (`fastapi[standard]`), `uv`; Next.js (App Router, TypeScript, static export) on Node 20 / npm; `pytest` + `TestClient`.

## Global Constraints

- Branch: `feat/nextjs-frontend`.
- FastAPI dependency unchanged: `fastapi[standard]>=0.138.0` (already in `pyproject.toml`).
- Next.js must be configured with `output: 'export'` (pure static; no SSR/Node runtime — FastAPI Cloud runs Python only).
- Serve the build from `frontend/out` (where Next exports). `app.frontend(...)` is declared **after** the `/api/...` route.
- Exact API response: `{"message": "Hello from FastAPI + Next.js (static export) 🚀"}`
- Stable marker string present in the rendered page (asserted by tests/curl): `FastAPI + Next.js static export`
- `web/` is removed on this branch.
- Build + local verification only. **No deploy.**

---

### Task 1: Scaffold the Next.js static-export frontend

**Files:**
- Create: `frontend/` (via `create-next-app`)
- Modify: the generated Next config (`frontend/next.config.ts` or `.js`) → add `output: 'export'`
- Replace: `frontend/app/page.tsx`, `frontend/app/layout.tsx`

**Interfaces:**
- Produces: `frontend/out/index.html` (static build) containing the marker `FastAPI + Next.js static export`; consumed by Tasks 2 and 4. `frontend/out` is gitignored by `frontend/.gitignore` (relevant to Task 3).

- [ ] **Step 1: Scaffold a minimal Next.js app (non-interactive)**

Run from repo root:
```bash
npx create-next-app@latest frontend --ts --app --no-eslint --no-tailwind --no-src-dir --use-npm --yes
```
Expected: creates `frontend/` with `package.json`, a Next config file, `tsconfig.json`, `app/`, and installs dependencies (`node_modules/`). Takes a few minutes; needs network.

- [ ] **Step 2: Enable static export in the Next config**

Find the generated config (`frontend/next.config.ts` or `frontend/next.config.js`) and set its config object to exactly:
```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
```
(If the generated file is `next.config.js` (CommonJS), instead write:)
```js
/** @type {import('next').NextConfig} */
const nextConfig = { output: "export" };
module.exports = nextConfig;
```

- [ ] **Step 3: Replace `frontend/app/layout.tsx` with a minimal layout (no `next/font` network dependency)**

```tsx
export const metadata = { title: "FastAPI + Next.js" };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 4: Replace `frontend/app/page.tsx` with the minimal client page**

```tsx
"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [msg, setMsg] = useState("loading /api/hello …");

  useEffect(() => {
    fetch("/api/hello")
      .then((r) => r.json())
      .then((d) => setMsg(JSON.stringify(d)))
      .catch((e) => setMsg("error: " + e));
  }, []);

  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        padding: "2rem",
        maxWidth: "36rem",
        margin: "0 auto",
      }}
    >
      <h1>FastAPI + Next.js static export</h1>
      <p>
        This static Next.js page is served by FastAPI via <code>app.frontend()</code>{" "}
        and calls the API:
      </p>
      <pre>{msg}</pre>
    </main>
  );
}
```

- [ ] **Step 5: Build the static export**

Run:
```bash
cd frontend && npm run build && cd ..
```
Expected: build succeeds and `frontend/out/` is generated.

- [ ] **Step 6: Verify the build output contains the marker**

Run:
```bash
test -f frontend/out/index.html && grep -q "FastAPI + Next.js static export" frontend/out/index.html && echo "build OK"
```
Expected: `build OK`.

- [ ] **Step 7: Commit the frontend source** (node_modules/.next/out are gitignored by `frontend/.gitignore`)

```bash
git add frontend
git commit -m "feat: scaffold Next.js static-export frontend"
```

---

### Task 2: Serve the export from FastAPI + tests (TDD)

**Files:**
- Modify: `main.py`
- Modify: `tests/test_app.py` (rewrite for the new message + marker)
- Delete: `web/` (replaced by the Next build on this branch)

**Interfaces:**
- Consumes: `frontend/out` from Task 1; `app` from `main.py`.
- Produces: `GET /api/hello` → `{"message": "Hello from FastAPI + Next.js (static export) 🚀"}`; `GET /` serves `frontend/out/index.html`.

- [ ] **Step 1: Rewrite `tests/test_app.py` with the new expectations**

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_api_hello_returns_message():
    resp = client.get("/api/hello")
    assert resp.status_code == 200
    assert resp.json() == {
        "message": "Hello from FastAPI + Next.js (static export) 🚀"
    }


def test_root_serves_nextjs_export():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "FastAPI + Next.js static export" in resp.text


def test_api_route_takes_precedence_over_frontend():
    resp = client.get("/api/hello")
    assert "application/json" in resp.headers["content-type"]
```

- [ ] **Step 2: Remove the old hand-written frontend**

```bash
git rm -r web
```
Expected: `web/` deleted.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app.py -v`
Expected: FAIL — `main.py` still serves `directory="web"` (now deleted), so importing `app` raises `RuntimeError` (frontend directory does not exist) and/or the message assertion fails.

- [ ] **Step 4: Update `main.py` to serve the Next build with the new message**

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI + Next.js (static export) 🚀"}


# Frontend LAST: serve the Next.js static export; matched only when no /api route did.
app.frontend("/", directory="frontend/out")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS — all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_app.py
git commit -m "feat: serve Next.js static export via app.frontend; drop web/"
```

---

### Task 3: Deploy-readiness — `.fastapicloudignore`

**Files:**
- Create: `.fastapicloudignore`

**Interfaces:**
- Consumes: knowledge that `frontend/out` is gitignored (Task 1).
- Produces: a deploy override re-including the build so a future `fastapi deploy` uploads it.

- [ ] **Step 1: Confirm the build dir is gitignored (the trap)**

Run: `git check-ignore frontend/out`
Expected: prints `frontend/out` (it is ignored by `frontend/.gitignore`'s `/out/`), confirming `fastapi deploy` would drop it without an override.

- [ ] **Step 2: Create `.fastapicloudignore` at the repo root**

```
# Re-include the Next.js static build that frontend/.gitignore drops.
# fastapi deploy honors gitignore; this override ships the build (not node_modules/.next).
!frontend/out/
!frontend/out/**
```

- [ ] **Step 3: Commit**

```bash
git add .fastapicloudignore
git commit -m "chore: .fastapicloudignore to ship Next.js build on deploy"
```

---

### Task 4: Local runtime smoke test

**Files:** none (verification only)

**Interfaces:**
- Consumes: `main.py`, `frontend/out` (Tasks 1–2).

- [ ] **Step 1: Start the dev server in the background**

Run: `uv run fastapi dev main.py --port 8000` (background; wait for `Application startup complete`).

- [ ] **Step 2: Verify the API responds**

Run: `curl -s http://127.0.0.1:8000/api/hello`
Expected: `{"message":"Hello from FastAPI + Next.js (static export) 🚀"}`

- [ ] **Step 3: Verify the Next.js page is served at root**

Run: `curl -s http://127.0.0.1:8000/ | grep -q "FastAPI + Next.js static export" && echo "frontend served OK"`
Expected: `frontend served OK`

- [ ] **Step 4: Verify a built Next asset is served**

Run: `curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8000/$(cd frontend/out && ls _next/static/chunks/*.js 2>/dev/null | head -1)"`
Expected: `200` (a `_next` JS chunk is served). If no chunk path resolves, instead check `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/_next/` is reachable via any asset referenced in `frontend/out/index.html`.

- [ ] **Step 5: Stop the dev server**

Stop the background `fastapi dev` process. No commit (verification only).

---

## Notes for the implementer

- Run all `uv`/`curl` commands from the repo root so `directory="frontend/out"` resolves and `from main import app` works (`pythonpath = ["."]` is set in `pyproject.toml`).
- The page fetches `/api/hello` in the browser, so `curl /` shows the static shell with the marker and `loading …`, not the fetched JSON — that's expected. The API is verified directly via `/api/hello`.
- If `npm run build` fails on `next/font` or fonts, confirm `layout.tsx` was replaced (Step 1.3) so there is no `next/font` import.
- Keep the API under `/api/...`; do not add a catch-all route — it would shadow the frontend.
