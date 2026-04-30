"""
Database connection pool and utilities using asyncpg.
Provides connection management for PostgreSQL.
"""
import asyncpg
from typing import Optional
from .config import settings
import os


class Database:
    """Async PostgreSQL database connection manager."""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    def _parse_db_url(cls) -> dict:
        """Parse DATABASE_URL to extract connection parameters."""
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
        
        if "@" in url:
            user_pass, host_db = url.split("@")
            user, password = user_pass.split(":") if ":" in user_pass else ("postgres", "")
            host, db = host_db.split("/") if "/" in host_db else (host_db, "dealmind")
            port = int(host.split(":")[-1]) if ":" in host else 5432
            host = host.split(":")[0] if ":" in host else host
        else:
            user, password, host, port, db = "postgres", "postgres", "localhost", 5432, "dealmind"
        
        return {"host": host, "port": port, "user": user, "password": password, "database": db}
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """
        Get or create the database connection pool.
        Uses singleton pattern to ensure one pool per application.
        """
        if cls._pool is None:
            params = cls._parse_db_url()
            cls._pool = await asyncpg.create_pool(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=params["database"],
                min_size=2,
                max_size=10,
                command_timeout=60,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
            )
        return cls._pool
    
    @classmethod
    async def close_pool(cls):
        """Close the database connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
    
    @classmethod
    async def execute_query(cls, query: str, *args):
        """Execute a query without returning rows (INSERT, UPDATE, DELETE)."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    @classmethod
    async def fetch_rows(cls, query: str, *args):
        """Execute a query and return all rows."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    @classmethod
    async def fetch_one(cls, query: str, *args):
        """Execute a query and return one row."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    @classmethod
    async def fetch_val(cls, query: str, *args):
        """Execute a query and return a single value."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)


async def get_db_pool() -> asyncpg.Pool:
    """FastAPI dependency to get database pool."""
    return await Database.get_pool()


async def check_db_connection() -> dict:
    """Check database connection health."""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "pool_size": pool.get_size() if hasattr(pool, 'get_size') else "N/A"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }