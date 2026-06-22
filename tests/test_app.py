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
