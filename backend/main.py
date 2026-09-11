import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from app.core import settings
from app.core.database import SessionLocal, get_db
from app.core.init_db import init_default_users
from app.services import SchedulerService
from app.api import (
    auth_router,
    user_router,
    member_router,
    product_router,
    category_router,
    deckel_router,
    transaction_router,
    voucher_admin_router,
    voucher_kasse_router,
    app_settings_router,
    data_maintenance_router,
    import_export_router,
    audit_log_router,
    hardware_agent_router,
    guest_list_router,
)

import logging
logger = logging.getLogger(__name__)
settings.validate_runtime_configuration()
from app.core.database import engine
from app.core.db_migration import run_migrations
if not run_migrations(engine):
    raise RuntimeError("Database migration or schema verification failed; application startup stopped")

db = SessionLocal()
try:
    from app.core.maintenance_lock import maintenance_gate
    from app.services.backup_media import recover_media, recovery_pending
    if recovery_pending():
        with maintenance_gate(engine, exclusive=True):
            recover_media(db)
            db.rollback()
    with maintenance_gate(engine):
        init_default_users(db)
finally:
    db.close()

app = FastAPI(
    title="Kassensoftware API",
    description="Webbasierte Kassensoftware für Vereine",
    version="2.7.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_COOKIE_MAX_AGE,
    same_site="lax",
    https_only=settings.COOKIE_SECURE,
)

if not settings.PRODUCTION:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api") and not request.url.path.endswith("/"):
            path_parts = request.url.path.split("/")
            last_part = path_parts[-1] if path_parts else ""
            if "." not in last_part:
                request.scope["path"] = request.url.path + "/"
        return await call_next(request)


app.add_middleware(TrailingSlashMiddleware)
from app.core.maintenance_lock import MaintenanceMiddleware
app.add_middleware(MaintenanceMiddleware, engine=engine)


@app.on_event("startup")
async def startup_scheduler():
    try:
        SchedulerService.start_scheduler()
    except Exception as e:
        print(f"Warning: Failed to start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_scheduler():
    SchedulerService.stop_scheduler()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(member_router)
app.include_router(product_router)
app.include_router(category_router)
app.include_router(deckel_router)
app.include_router(transaction_router)
app.include_router(voucher_admin_router)
app.include_router(voucher_kasse_router)
app.include_router(app_settings_router)
app.include_router(data_maintenance_router)
app.include_router(import_export_router)
app.include_router(audit_log_router)
app.include_router(hardware_agent_router)
app.include_router(guest_list_router)


@app.get("/api/health")
@app.get("/api/health/")
async def health():
    return {"status": "healthy"}


frontend_dist = Path(__file__).parent / "app" / "frontend" / "dist"

if frontend_dist.exists():
    from starlette.responses import FileResponse
    frontend_static = StaticFiles(directory=str(frontend_dist), html=False, check_dir=False)

    def _get_frontend_cache_headers(file_path: Path) -> dict[str, str]:
        if file_path.name in {"index.html", "sw.js"}:
            return {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        if file_path.name.endswith(".webmanifest") or file_path.name == "manifest.json":
            return {"Cache-Control": "no-cache"}
        if "assets" in file_path.parts:
            return {"Cache-Control": "public, max-age=31536000, immutable"}
        return {"Cache-Control": "public, max-age=3600"}

    def _frontend_file_response(file_path: Path, media_type: str | None = None) -> FileResponse:
        return FileResponse(
            str(file_path),
            media_type=media_type,
            headers=_get_frontend_cache_headers(file_path),
        )

    def _lookup_frontend_file(path_name: str) -> Path | None:
        full_path, stat_result = frontend_static.lookup_path(path_name)
        if not stat_result:
            return None
        return Path(full_path)

    @app.get("/")
    async def serve_root():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return _frontend_file_response(index_path, media_type="text/html")
        return {"status": "ok"}

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        if exc.status_code == 404:
            if request.url.path.startswith("/api/"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})

            path = request.url.path.lstrip("/")
            file_path = _lookup_frontend_file(path)
            if file_path and file_path.exists() and file_path.is_file():
                return _frontend_file_response(file_path)

            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return _frontend_file_response(index_path, media_type="text/html")

        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/{path_name:path}")
    async def serve_spa(path_name: str):
        file_path = _lookup_frontend_file(path_name)
        if file_path and file_path.exists() and file_path.is_file():
            return _frontend_file_response(file_path)

        if not path_name.startswith("api"):
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return _frontend_file_response(index_path, media_type="text/html")

        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        return {"status": "ok", "message": "Frontend not found, API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
