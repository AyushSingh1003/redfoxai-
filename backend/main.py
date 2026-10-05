import os
import sys
from pathlib import Path

# Ensure backend root is always on sys.path
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import engine, Base, SessionLocal, ensure_sqlite_compat_schema
from api.routes import router as api_router
from services.assessment_service import recover_in_flight


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_compat_schema(engine)
    # Recover any orphaned assessments from prior crashes
    db = SessionLocal()
    try:
        recover_in_flight(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_SUBTITLE,
    version=settings.AGENT_VERSION,
    lifespan=lifespan,
)

# Defensive security headers on all API responses
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Strict CORS setup for development and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.AGENT_VERSION,
        "env": settings.APP_ENV,
    }


# Include core API router under /api
app.include_router(api_router, prefix="/api")

# Handle frontend asset placeholder when Vite server is not active
@app.api_route("/@vite/{path:path}", methods=["GET", "HEAD"])
async def vite_fallback(request: Request, path: str):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Frontend dev server is not active on this port. Use port 5173 or build frontend.",
            "requested": f"/@vite/{path}",
        },
    )

# Serve static build of frontend if frontend/dist exists
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path == "openapi.json":
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    reload_enabled = os.getenv("UVICORN_RELOAD", "0") == "1"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload_enabled)
