"""DealMind AI - Main FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.database import get_supabase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Initialize Supabase client on startup
    try:
        get_supabase()
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize Supabase: {e}")
    yield


app = FastAPI(
    title="DealMind AI",
    description="AI-Accelerated Real Estate Deal-Execution Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routers import auth
app.include_router(auth.router)


@app.get("/health")
async def health_check():
    """Health check endpoint - returns database connection status."""
    try:
        get_supabase().table("agents").select("id").limit(1).execute()
        return JSONResponse(content={"status": "ok", "db": "connected"})
    except Exception as e:
        return JSONResponse(content={"status": "ok", "db": "disconnected", "error": str(e)})


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)