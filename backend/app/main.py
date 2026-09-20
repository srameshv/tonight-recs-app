from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.preferences.router import router as preferences_router

app = FastAPI(title="Tonight")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(preferences_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
