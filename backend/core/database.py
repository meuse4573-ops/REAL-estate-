"""
Database connection pool and utilities using asyncpg.
Provides connection management for PostgreSQL with SSL support.
"""
import asyncpg
import asyncio
from typing import Optional
from .config import settings
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Database:
    """Async PostgreSQL database connection manager."""
    
    _pool: Optional[asyncpg.Pool] = None
    _max_retries = 3
    _retry_delay = 2
    
    @classmethod
    def _get_connection_params(cls) -> dict:
        """Parse DATABASE_URL using urlparse for proper handling of special chars."""
        database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
        
        logger.info("=" * 50)
        logger.info(f"DATABASE_URL: {database_url[:60]}...")
        
        parsed = urlparse(database_url)
        
        params = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/") if parsed.path else "postgres",
        }
        
        logger.info(f"PARSED - Host: {params['host']}, Port: {params['port']}, DB: {params['database']}, User: {params['user']}")
        logger.info("=" * 50)
        
        return params
    
    @classmethod
    async def _create_pool_with_retry(cls) -> asyncpg.Pool:
        """Create pool with retry logic for connection failures."""
        params = cls._get_connection_params()
        
        ssl_modes = ["require", "prefer", True, False]
        
        for ssl_val in ssl_modes:
            for attempt in range(cls._max_retries):
                try:
                    logger.info(f"Connecting (SSL={ssl_val}, attempt {attempt+1}/3)...")
                    
                    pool = await asyncpg.create_pool(
                        host=params["host"],
                        port=params["port"],
                        user=params["user"],
                        password=params["password"],
                        database=params["database"],
                        min_size=1,
                        max_size=5,
                        command_timeout=30,
                        ssl=ssl_val,
                    )
                    
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    
                    logger.info(f"SUCCESS with SSL={ssl_val}")
                    return pool
                    
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    logger.warning(f"Failed (SSL={ssl_val}, attempt {attempt+1}): {error_str[:80]}")
                    
                    if attempt < cls._max_retries - 1:
                        await asyncio.sleep(1)
        
        raise ConnectionError(f"Database connection failed: {str(last_error)[:200]}")
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get or create the database connection pool."""
        if cls._pool is None:
            cls._pool = await cls._create_pool_with_retry()
        return cls._pool
    
    @classmethod
    async def close_pool(cls):
        """Close the database connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
    
    @classmethod
    async def execute_query(cls, query: str, *args):
        """Execute a query without returning rows."""
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
    """Check database connection health with detailed error reporting."""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)[:200],
        }