import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from app.core import settings, engine
from app.core.database import SessionLocal, get_db
from app.core.init_db import init_default_users
from app.models import Base, User
from app.api import (
    auth_router,
    user_router,
    member_router,
    product_router,
    transaction_router,
)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize default users
db = SessionLocal()
try:
    init_default_users(db)
finally:
    db.close()

# Create app
app = FastAPI(
    title="Kassensoftware API",
    description="Webbasierte Kassensoftware für Vereine",
    version="1.0.0",
)

# Middleware stack (order matters - added in reverse order)
# SessionMiddleware should be first (added last)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",  # Allow cross-site session cookies
    https_only=False,  # Allow in development (http://localhost)
)

# CORS middleware - should be second
if not os.getenv("PRODUCTION"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Custom middleware to handle trailing slash redirects for API routes
class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Rewrite URL to add trailing slash for all API routes (GET, POST, PUT, DELETE)
        if request.url.path.startswith("/api") and not request.url.path.endswith("/"):
            # Check if it ends with a "filename-like" pattern (has a dot)
            path_parts = request.url.path.split("/")
            last_part = path_parts[-1] if path_parts else ""
            
            # Don't add trailing slash to files (w/extension)
            if "." not in last_part:
                # URL rewrite: modify the scope to add trailing slash
                # This works for GET, POST, PUT, DELETE without redirect
                request.scope["path"] = request.url.path + "/"
        
        return await call_next(request)

app.add_middleware(TrailingSlashMiddleware)

# Include routers FIRST - they have priority over catch-all
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(member_router)
app.include_router(product_router)
app.include_router(transaction_router)


@app.get("/api/health")
@app.get("/api/health/")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/debug/users-count")
@app.get("/api/debug/users-count/")
async def debug_users_count(db: Session = Depends(get_db)):
    """Debug endpoint - count users in DB"""
    count = db.query(User).count()
    return {"user_count": count}


# Frontend SPA serving (at the very end)
frontend_dist = Path(__file__).parent / "app" / "frontend" / "dist"

if frontend_dist.exists():
    from starlette.responses import FileResponse
    
    @app.get("/")
    async def serve_root():
        """Serve SPA index.html at root"""
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"status": "ok"}
    
    # Exception handler for 404 - serve index.html for SPA routing
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        """Custom 404 handler - serve SPA index.html instead"""
        if exc.status_code == 404:
            # Check if this is an API route - don't serve index.html for API 404s
            if request.url.path.startswith("/api/"):
                # Return JSON 404 for API
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            
            # For non-API routes, check if it's a static file
            path = request.url.path.lstrip("/")
            file_path = frontend_dist / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            
            # Serve index.html for SPA client-side routing
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path), media_type="text/html")
        
        # For other status codes (401, 403, 500, etc), return JSON response
        # This allows API errors to return proper status codes
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    
    @app.get("/{path_name:path}")
    async def serve_spa(path_name: str):
        """Serve static files and SPA routes"""
        # Try to serve static file first
        file_path = frontend_dist / path_name
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # For non-API routes, default to index.html for SPA routing
        if not path_name.startswith("api"):
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
        
        # Raise 404 for API routes - will be handled by exception handler
        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        """Fallback if frontend not found"""
        return {"status": "ok", "message": "Frontend not found, API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
