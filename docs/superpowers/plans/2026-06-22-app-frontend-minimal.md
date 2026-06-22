# Minimal `app.frontend()` + FastAPI Cloud App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest FastAPI app that serves a JSON API and a hand-written frontend from one ASGI app via `app.frontend()` (new in 0.138.0), verify locally, then deploy to FastAPI Cloud.

**Architecture:** A single `main.py` defines one `/api/hello` JSON route, then calls `app.frontend("/", directory="web")` to serve a no-build static frontend from `web/`. The frontend page fetches `/api/hello` and renders it, proving API + UI are served by the same process on one origin. FastAPI Cloud runs this ASGI app directly, so it hosts the frontend automatically.

**Tech Stack:** Python 3.12, FastAPI ≥ 0.138.0 (`fastapi[standard]`), `uv` for env/deps, `pytest` + `TestClient` (httpx, bundled with `[standard]`), plain HTML/CSS/JS frontend.

## Global Constraints

- Dependency: `fastapi[standard]>=0.138.0` (the version that adds `app.frontend`). Verify the installed version is ≥ 0.138.0.
- Python: `>=3.12`.
- Serve the frontend from `web/` — **never `dist/` or `build/`** (both are gitignored by the repo's `.gitignore`; a missing dir crashes the app because `app.frontend` defaults to `check_dir=True`).
- `app.frontend(...)` must be declared **after** all `/api/...` path operations (FastAPI checks routes first).
- Exact API response (used verbatim in tests and frontend): `{"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}`
- Frontend `web/index.html` must contain the literal marker text `FastAPI Cloud` (asserted by tests).
- Work happens on branch `feat/app-frontend-minimal`.

---

### Task 1: Project setup & dependency manifest

**Files:**
- Create: `pyproject.toml`

**Interfaces:**
- Produces: a `uv`-managed environment with `fastapi[standard]>=0.138.0` and `pytest`; a `pyproject.toml` whose `[tool.pytest.ini_options].pythonpath = ["."]` lets tests `from main import app`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "fastapi-cloud-test"
version = "0.1.0"
description = "Minimal FastAPI app using app.frontend(), deployed on FastAPI Cloud"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.138.0",
]

[dependency-groups]
dev = [
    "pytest>=8",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

- [ ] **Step 2: Create the environment and install**

Run: `uv sync`
Expected: creates `.venv/`, resolves and installs `fastapi[standard]` and `pytest`. (`uv.lock` is generated.)

- [ ] **Step 3: Verify the FastAPI version supports `app.frontend`**

Run:
```bash
uv run python -c "import fastapi; from fastapi import FastAPI; print(fastapi.__version__); assert hasattr(FastAPI(), 'frontend'), 'no app.frontend'; print('frontend OK')"
```
Expected: prints a version `>= 0.138.0` and `frontend OK`. If the version is lower, run `uv add 'fastapi[standard]>=0.138.0'` and re-check.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: project setup with fastapi[standard]>=0.138.0"
```

---

### Task 2: Hand-written static frontend

**Files:**
- Create: `web/index.html`
- Create: `web/style.css`

**Interfaces:**
- Produces: a `web/` directory containing `index.html` (with marker text `FastAPI Cloud` and a `fetch("/api/hello")` call) — required by Task 3 both at import time (`check_dir`) and by the serving test.

- [ ] **Step 1: Write `web/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FastAPI Cloud · app.frontend demo</title>
    <link rel="stylesheet" href="/style.css" />
  </head>
  <body>
    <main>
      <h1>FastAPI Cloud · <code>app.frontend</code></h1>
      <p>One FastAPI app serves this page <em>and</em> the API below.</p>
      <pre id="out">loading /api/hello …</pre>
    </main>
    <script>
      fetch("/api/hello")
        .then((r) => r.json())
        .then((data) => {
          document.getElementById("out").textContent = JSON.stringify(data, null, 2);
        })
        .catch((err) => {
          document.getElementById("out").textContent = "error: " + err;
        });
    </script>
  </body>
</html>
```

- [ ] **Step 2: Write `web/style.css`**

```css
:root { color-scheme: light dark; }
body {
  margin: 0;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  font: 16px/1.5 system-ui, sans-serif;
}
main { max-width: 36rem; padding: 2rem; }
h1 { margin: 0 0 0.5rem; font-size: 1.5rem; }
code { background: rgba(127, 127, 127, 0.2); padding: 0 0.25rem; border-radius: 4px; }
pre {
  background: rgba(127, 127, 127, 0.12);
  padding: 1rem;
  border-radius: 8px;
  overflow: auto;
}
```

- [ ] **Step 3: Verify the marker and fetch call are present**

Run: `grep -l "FastAPI Cloud" web/index.html && grep -q 'fetch("/api/hello")' web/index.html && echo "markers OK"`
Expected: prints `web/index.html` and `markers OK`.

- [ ] **Step 4: Commit**

```bash
git add web/index.html web/style.css
git commit -m "feat: hand-written static frontend in web/"
```

---

### Task 3: Backend — API route + `app.frontend`, with tests

**Files:**
- Create: `main.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `web/index.html` from Task 2 (served at `/`); environment from Task 1.
- Produces: `app` (a `FastAPI` instance) importable as `from main import app`; route `GET /api/hello` returning `{"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_app.py
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_api_hello_returns_message():
    resp = client.get("/api/hello")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}


def test_root_serves_frontend_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "FastAPI Cloud" in resp.text


def test_api_route_takes_precedence_over_frontend():
    resp = client.get("/api/hello")
    assert "application/json" in resp.headers["content-type"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'main'` (main.py not created yet).

- [ ] **Step 3: Write `main.py`**

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}


# Frontend LAST: matched only when no /api route handled the request.
app.frontend("/", directory="web")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS — all 3 tests green.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_app.py
git commit -m "feat: FastAPI app serving /api/hello + frontend via app.frontend"
```

---

### Task 4: Local runtime smoke test

**Files:** none (verification only)

**Interfaces:**
- Consumes: `main.py`, `web/`, environment from Tasks 1–3.

- [ ] **Step 1: Start the dev server in the background**

Run: `uv run fastapi dev main.py --port 8000` (run in background; wait until it logs `Application startup complete`).

- [ ] **Step 2: Verify the API responds**

Run: `curl -s http://127.0.0.1:8000/api/hello`
Expected: `{"message":"Hello from FastAPI 0.138 · app.frontend 🎉"}`

- [ ] **Step 3: Verify the frontend is served at root**

Run: `curl -s http://127.0.0.1:8000/ | grep -q "FastAPI Cloud" && echo "frontend served OK"`
Expected: `frontend served OK`

- [ ] **Step 4: Verify the CSS asset is served**

Run: `curl -s -o /dev/null -w "%{http_code} %{content_type}\n" http://127.0.0.1:8000/style.css`
Expected: `200 text/css; charset=utf-8` (a `200` with a `text/css` content-type).

- [ ] **Step 5: Stop the dev server**

Stop the background `fastapi dev` process. No commit (verification only).

---

### Task 5: Deploy to FastAPI Cloud

**Files:** possibly `requirements.txt` (only if the docs check in Step 1 says it's required)

**Interfaces:**
- Consumes: the committed project (Tasks 1–4). All app files, especially `web/`, must be committed so they upload.

- [ ] **Step 1: Confirm the dependency-manifest format FastAPI Cloud expects**

Check the FastAPI Cloud docs (https://fastapicloud.com/docs/getting-started/) for how `fastapi deploy` reads dependencies. If it requires `requirements.txt` rather than `pyproject.toml`, create one:
```
fastapi[standard]>=0.138.0
```
and commit it. If `pyproject.toml` is accepted, skip this file.

- [ ] **Step 2: Confirm `web/` is tracked by git (not excluded)**

Run: `git ls-files web/`
Expected: lists `web/index.html` and `web/style.css`. (Guards against the gitignore/upload trap — if empty, the deployed app would crash on boot via `check_dir`.)

- [ ] **Step 3: Authenticate (human-run, interactive)**

The user runs this themselves in the session via the `!` prefix: `! fastapi login`
Expected: browser-based login completes; CLI reports authenticated. (Targets the user's own FastAPI Cloud account.)

- [ ] **Step 4: Deploy**

Run: `uv run fastapi deploy`
Expected: the CLI uploads the project, builds, and prints a live app URL. Note the URL.

- [ ] **Step 5: Verify the live deployment serves both API and frontend**

Run (substitute the deployed URL for `$URL`):
```bash
curl -s "$URL/api/hello"
curl -s "$URL/" | grep -q "FastAPI Cloud" && echo "live frontend OK"
```
Expected: the JSON message from `/api/hello`, and `live frontend OK` from `/`. This confirms FastAPI Cloud hosts the `app.frontend` content alongside the API.

---

## Notes for the implementer

- If `uv run fastapi dev` can't find the `fastapi` command, the env didn't sync — re-run `uv sync` (Task 1).
- The API message string contains a middle dot (`·`) and an emoji; keep the file UTF-8 encoded and copy the string verbatim so the equality test passes.
- Run all commands from the repo root so `pythonpath = ["."]` makes `from main import app` resolve.
