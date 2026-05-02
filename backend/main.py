"""DealMind AI - Main FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.database import get_supabase, check_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import auth
app.include_router(auth.router)


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    return JSONResponse(content={
        "status": "healthy" if db_ok else "degraded",
        "app": "running",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0"
    })


@app.get("/")
async def root():
    return {
        "message": "Welcome to DealMind AI API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)