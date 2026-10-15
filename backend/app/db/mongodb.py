"""Async MongoDB connection via Motor."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def init_mongodb() -> None:
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _database = _client[settings.MONGODB_DB_NAME]
    await _client.admin.command("ping")
    print(f"[MongoDB] Connected to {settings.MONGODB_DB_NAME}")


async def close_mongodb() -> None:
    global _client
    if _client:
        _client.close()
        print("[MongoDB] Connection closed")


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("MongoDB not initialized")
    return _database


# Collection shortcuts
def users_col():
    return get_database()["users"]

def programmes_col():
    return get_database()["programmes"]

def cohorts_col():
    return get_database()["cohorts"]

def course_units_col():
    return get_database()["course_units"]

def lecturers_col():
    return get_database()["lecturers"]

def rooms_col():
    return get_database()["rooms"]

def time_periods_col():
    return get_database()["time_periods"]

def activities_col():
    return get_database()["activities"]

def enrollments_col():
    return get_database()["enrollments"]

def timetable_runs_col():
    return get_database()["timetable_runs"]

def timetable_assignments_col():
    return get_database()["timetable_assignments"]

def api_keys_col():
    return get_database()["api_keys"]