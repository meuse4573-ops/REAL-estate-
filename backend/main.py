"""
DealMind AI - Main FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import check_db_connection, get_supabase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Initialize Supabase client on startup
    try:
        get_supabase()
    except Exception as e:
        print(f"Warning: Could not initialize Supabase: {e}")
    
    yield


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint - returns database connection status."""
    try:
        result = get_supabase().table("agents").select("id").limit(1).execute()
        return {"status": "ok", "db": "connected"}
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