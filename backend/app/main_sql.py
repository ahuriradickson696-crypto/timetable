"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import engine
from app.db.base import Base
import app.models  # noqa: F401  -- registers all models


setup_logging()

# Create tables (dev convenience -- use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health/info at root level (so /docs and /health both work)
from app.api.v1.health import router as health_router
app.include_router(health_router)


# All API routes under /api/v1
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")
from app.api.routes import cohorts as cohorts_router
app.include_router(cohorts_router.router)
from app.api.routes import auth_signup
app.include_router(auth_signup.router)
from app.api.routes import admin_link
app.include_router(admin_link.router)
from app.api.routes import notifications
app.include_router(notifications.router)
from app.api.routes import account
app.include_router(account.router)
from app.api.routes import auth_password
app.include_router(auth_password.router)
from app.api.routes import admin_link_v2
app.include_router(admin_link_v2.router)
from app.api.routes import auth_kiosk
app.include_router(auth_kiosk.router)
from app.api.admin_api import v1 as admin_api_v1
app.include_router(admin_api_v1.router)
from app.api.routes import admin_api_keys
app.include_router(admin_api_keys.router)


@app.on_event("startup")
def _startup():
    logger.info(f"{settings.APP_NAME} starting in {settings.APP_ENV} mode")
    logger.info(f"Docs: http://localhost:8000/docs")
