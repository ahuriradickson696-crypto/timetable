"""Health and info endpoints."""
from fastapi import APIRouter
from datetime import datetime, timezone
from app.config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "api": "/api/v1",
    }
