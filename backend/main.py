import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.core import settings, engine
from app.core.database import SessionLocal
from app.core.init_db import init_default_users
from app.models import Base
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

# Middleware - CORS nur im Dev-Mode
if not os.getenv("PRODUCTION"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(member_router)
app.include_router(product_router)
app.include_router(transaction_router)


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "Kassensoftware API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Mount frontend static files (at the end!)
frontend_dist = Path(__file__).parent / "app" / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
