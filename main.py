from fastapi import FastAPI

app = FastAPI()


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI 0.138 · app.frontend 🎉"}


# Frontend LAST: matched only when no /api route handled the request.
app.frontend("/", directory="web")
