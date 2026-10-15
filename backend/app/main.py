"""AVIU Timetable — FastAPI + MongoDB backend."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import init_mongodb, close_mongodb
from app.api.routes import auth as auth_router
from app.api.routes import programmes_mongo
from app.api.routes import cohorts_mongo
from app.api.routes import course_units_mongo
from app.api.routes import lecturers_mongo
from app.api.routes import rooms_mongo
from app.api.routes import time_periods_mongo
from app.api.routes import activities_mongo
from app.api.routes import enrollments_mongo
from app.api.routes import portal_mongo
from app.api.routes import admin_api_mongo


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
app.include_router(programmes_mongo.router)
app.include_router(cohorts_mongo.router)
app.include_router(course_units_mongo.router)
app.include_router(lecturers_mongo.router)
app.include_router(rooms_mongo.router)
app.include_router(time_periods_mongo.router)
app.include_router(activities_mongo.router)
app.include_router(enrollments_mongo.router)
app.include_router(portal_mongo.router)
app.include_router(admin_api_mongo.router)
from app.api.routes import generation_mongo
app.include_router(generation_mongo.router)
from app.api.routes import publishing_mongo
app.include_router(publishing_mongo.router)
from app.api.routes import admin_api_keys_mongo
app.include_router(admin_api_keys_mongo.router)


@app.get("/health")
async def health():
    return {"status": "ok", "db": "mongodb"}


@app.get("/")
async def root():
    return {"name": "AVIU Timetable", "version": "2.0.0", "db": "mongodb"}