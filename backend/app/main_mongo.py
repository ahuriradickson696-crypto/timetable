"""AVIU Timetable — FastAPI + MongoDB."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import init_mongodb, close_mongodb
from app.api.routes import auth as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongodb()
    yield
    await close_mongodb()


app = FastAPI(
    title="AVIU Timetable",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"name": "AVIU Timetable", "version": "2.0.0", "db": "mongodb"}