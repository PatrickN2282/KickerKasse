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
from app.core import settings, engine
from app.core.database import SessionLocal, get_db
from app.core.init_db import init_default_users
from app.core.db_migration import run_migrations
from app.models import Base, User
from app.services import SchedulerService
from app.api import (
    auth_router,
    user_router,
    member_router,
    product_router,
    category_router,
    transaction_router,
    voucher_admin_router,
    voucher_kasse_router,
    app_settings_router,
    data_maintenance_router,
)

import logging
logger = logging.getLogger(__name__)
logger.info("Starting database migration process...")
run_migrations(engine)
logger.info("Database migration completed")

db = SessionLocal()
try:
    init_default_users(db)
finally:
    db.close()

app = FastAPI(
    title="Kassensoftware API",
    description="Webbasierte Kassensoftware für Vereine",
    version="1.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)

if not os.getenv("PRODUCTION"):
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
app.include_router(transaction_router)
app.include_router(voucher_admin_router)
app.include_router(voucher_kasse_router)
app.include_router(app_settings_router)
app.include_router(data_maintenance_router)


@app.get("/api/health")
@app.get("/api/health/")
async def health():
    return {"status": "healthy"}


@app.get("/api/debug/users-count")
@app.get("/api/debug/users-count/")
async def debug_users_count(db: Session = Depends(get_db)):
    count = db.query(User).count()
    return {"user_count": count}


frontend_dist = Path(__file__).parent / "app" / "frontend" / "dist"

if frontend_dist.exists():
    from starlette.responses import FileResponse

    @app.get("/")
    async def serve_root():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"status": "ok"}

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        if exc.status_code == 404:
            if request.url.path.startswith("/api/"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})

            path = request.url.path.lstrip("/")
            file_path = frontend_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))

            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path), media_type="text/html")

        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/{path_name:path}")
    async def serve_spa(path_name: str):
        file_path = frontend_dist / path_name
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        if not path_name.startswith("api"):
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))

        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        return {"status": "ok", "message": "Frontend not found, API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
