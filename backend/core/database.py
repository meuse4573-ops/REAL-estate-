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
        logger.info(f"=== DATABASE CONFIGURATION ===")
        logger.info(f"FULL DATABASE_URL: {raw_url[:50]}...{'(password hidden)' if '@' in raw_url else ''}")
        
        url = raw_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
        
        if "@" in url:
            user_pass, host_db = url.split("@")
            user, password = user_pass.split(":") if ":" in user_pass else ("postgres", "")
            host, db = host_db.split("/") if "/" in host_db else (host_db, "postgres")
            port = int(host.split(":")[-1]) if ":" in host else 5432
            host = host.split(":")[0] if ":" in host else host
        else:
            user, password, host, port, db = "postgres", "postgres", "localhost", 5432, "postgres"
        
        logger.info(f"PARSED - Host: {host}, Port: {port}, DB: {db}, User: {user}")
        logger.info(f"================================")
        
        return {"host": host, "port": port, "user": user, "password": password, "database": db}
    
    @classmethod
    async def _create_pool_with_retry(cls) -> asyncpg.Pool:
        """Create pool with retry logic for connection failures."""
        params = cls._parse_db_url()
        
        last_error = None
        for attempt in range(cls._max_retries):
            try:
                logger.info(f"Database connection attempt {attempt + 1}/{cls._max_retries}")
                logger.info(f"Connecting to: {params['host']}:{params['port']}, db: {params['database']}, user: {params['user']}")
                
                # Try with ssl mode - Supabase might need different SSL settings
                ssl_modes = ["prefer", "require", True]
                
                for ssl_mode in ssl_modes:
                    try:
                        logger.info(f"Trying SSL mode: {ssl_mode}")
                        pool = await asyncpg.create_pool(
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
                            ssl=ssl_mode,
                        )
                        
                        async with pool.acquire() as conn:
                            await conn.fetchval("SELECT 1")
                        
                        logger.info(f"Database connection successful with SSL mode: {ssl_mode}")
                        return pool
                    except Exception as ssl_error:
                        logger.warning(f"SSL mode {ssl_mode} failed: {str(ssl_error)}")
                        if pool:
                            try:
                                await pool.close()
                            except:
                                pass
                
                # If all SSL modes fail, try without SSL
                logger.info("Trying connection without SSL...")
                pool = await asyncpg.create_pool(
                    host=params["host"],
                    port=params["port"],
                    user=params["user"],
                    password=params["password"],
                    database=params["database"],
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    ssl=False,
                )
                
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                logger.info("Database connection successful (no SSL)")
                return pool
                
            except Exception as e:
                last_error = e
                logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < cls._max_retries - 1:
                    logger.info(f"Retrying in {cls._retry_delay} seconds...")
                    await asyncio.sleep(cls._retry_delay)
        
        raise ConnectionError(f"Failed to connect to database after {cls._max_retries} attempts: {str(last_error)}")
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """
        Get or create the database connection pool.
        Uses singleton pattern to ensure one pool per application.
        Includes retry logic for connection failures.
        """
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
    """Check database connection health with detailed error reporting."""
    try:
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "pool_size": pool.get_size() if hasattr(pool, 'get_size') else "N/A"
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database health check failed: {error_msg}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": error_msg,
            "error_type": type(e).__name__
        }