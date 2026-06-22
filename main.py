from fastapi import FastAPI

app = FastAPI()


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI + Next.js (static export) 🚀"}


# Frontend LAST: serve the Next.js static export; matched only when no /api route did.
app.frontend("/", directory="frontend/out")
