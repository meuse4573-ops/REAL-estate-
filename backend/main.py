"""
DealMind AI - Main FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from core.config import settings
from core.database import Database, check_db_connection
from routers import auth, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup: Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Don't initialize database on startup - connect lazily
    # Database connection will be established on first request
    
    yield
    
    # Shutdown: Close database pool
    await Database.close_pool()


app = FastAPI(
    title="DealMind AI",
    description="AI-Powered Real Estate Deal Execution Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    Health check endpoint - simple status response with error details.
    """
    try:
        db_status = await check_db_connection()
        if db_status["status"] == "healthy":
            return {"status": "ok", "db": "connected"}
        else:
            return {
                "status": "ok", 
                "db": "disconnected",
                "error": db_status.get("error", "Unknown error")
            }
    except Exception as e:
        return {"status": "ok", "db": "disconnected", "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to DealMind AI API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development"
    )