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

logger = logging.getLogger(__name__)


class Database:
    """Async PostgreSQL database connection manager."""
    
    _pool: Optional[asyncpg.Pool] = None
    _max_retries = 3
    _retry_delay = 2
    
    @classmethod
    def _parse_db_url(cls) -> dict:
        """Parse DATABASE_URL to extract connection parameters."""
        raw_url = settings.DATABASE_URL
        
        # Log what we're reading
        logger.info("=" * 50)
        logger.info(f"READING DATABASE_URL from settings...")
        logger.info(f"settings.DATABASE_URL = {raw_url[:80]}...")
        logger.info(f"os.environ.get('DATABASE_URL') = {os.environ.get('DATABASE_URL', 'NOT SET')[:80] if os.environ.get('DATABASE_URL') else 'NOT SET'}...")
        logger.info("=" * 50)
        
        url = raw_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
        
        if "@" in url:
            user_pass, host_db = url.split("@")
            if ":" in user_pass:
                parts = user_pass.split(":")
                user = parts[0]
                password = ":".join(parts[1:])  # Handle password with colons
            else:
                user = user_pass
                password = ""
            
            if "/" in host_db:
                host_port, db = host_db.split("/", 1)
            else:
                host_port = host_db
                db = "postgres"
            
            if ":" in host_port:
                host_parts = host_port.rsplit(":", 1)
                host = host_parts[0]
                port = int(host_parts[1]) if host_parts[1].isdigit() else 5432
            else:
                host = host_port
                port = 5432
        else:
            user, password, host, port, db = "postgres", "postgres", "localhost", 5432, "postgres"
        
        logger.info(f"FINAL PARSED VALUES:")
        logger.info(f"  Host: {host}")
        logger.info(f"  Port: {port}")
        logger.info(f"  DB: {db}")
        logger.info(f"  User: {user}")
        logger.info(f"  Password: {'*' * len(password) if password else 'EMPTY'}")
        logger.info("=" * 50)
        
        return {"host": host, "port": port, "user": user, "password": password, "database": db}
    
    @classmethod
    async def _create_pool_with_retry(cls) -> asyncpg.Pool:
        """Create pool with retry logic for connection failures."""
        params = cls._parse_db_url()
        
        last_error = None
        
        # Try multiple approaches
        approaches = [
            {"ssl": "prefer", "description": "SSL prefer"},
            {"ssl": "require", "description": "SSL require"},
            {"ssl": True, "description": "SSL True"},
            {"ssl": False, "description": "No SSL"},
        ]
        
        for approach in approaches:
            ssl_val = approach["ssl"]
            for attempt in range(cls._max_retries):
                try:
                    logger.info(f"Attempting connection (attempt {attempt+1}/3, SSL={ssl_val})...")
                    
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
                    
                    # Test the connection
                    async with pool.acquire() as conn:
                        result = await conn.fetchval("SELECT 1")
                    
                    logger.info(f"SUCCESS! Connected with SSL={ssl_val}")
                    return pool
                    
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    logger.warning(f"Failed (SSL={ssl_val}, attempt {attempt+1}): {error_str[:100]}")
                    
                    if attempt < cls._max_retries - 1:
                        await asyncio.sleep(1)
        
        logger.error(f"All connection attempts failed. Last error: {str(last_error)[:200]}")
        raise ConnectionError(f"Database connection failed: {str(last_error)}")
    
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
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database health check failed: {error_msg}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": error_msg[:200],
            "error_type": type(e).__name__
        }