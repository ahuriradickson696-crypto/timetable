"""AVIU Timetable — FastAPI + MongoDB + served React frontend."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
from app.api.routes import generation_mongo
from app.api.routes import publishing_mongo
from app.api.routes import admin_api_keys_mongo


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

# ─── CORS ───
import os as _os
_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# Add any origins from CORS_ORIGINS env var (comma-separated)
_extra = _os.environ.get("CORS_ORIGINS", "")
if _extra:
    _origins.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── CORS ── allow LAN + localhost + deployed domains
import os as _os
_allowed = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra = _os.environ.get("CORS_ORIGINS", "")
if _extra:
    _allowed.extend([o.strip() for o in _extra.split(",") if o.strip()])
# Allow any private-LAN IP on ports 5173



# ---------- API routers ----------
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
app.include_router(generation_mongo.router)
app.include_router(publishing_mongo.router)
app.include_router(admin_api_keys_mongo.router)


@app.get("/health")
async def health():
    return {"status": "ok", "db": "mongodb"}


# ---------- Serve React frontend ----------
# The build folder is expected at: backend/app/static/  (we copy it there at build time)
STATIC_DIR = Path(__file__).resolve().parent / "static"

if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    # Serve /assets/* etc. as real files
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Catch-all for SPA routes: /login, /my-timetable, etc. → serve index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Never intercept API paths (they're registered above and win by order)
        if full_path.startswith("api/") or full_path in ("health", "docs", "redoc", "openapi.json"):
            return {"detail": "Not Found"}
        # Serve real files if they exist (favicon.ico, robots.txt, etc.)
        file_path = STATIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for React Router
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "AVIU Timetable",
            "version": "2.0.0",
            "db": "mongodb",
            "note": "Frontend not built yet — only /api/* and /docs are available",
        }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)