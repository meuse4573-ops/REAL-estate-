"""
Database connection pool and utilities using psycopg2.
Provides connection management for PostgreSQL.
"""
import psycopg2
from psycopg2 import pool
import os
import logging

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database connection manager using psycopg2."""
    
    _pool = None
    
    @classmethod
    def _get_connection_params(cls) -> dict:
        """Parse DATABASE_URL for connection."""
        DATABASE_URL = os.getenv("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
        
        # Convert postgresql+asyncpg:// to postgresql://
        if "postgresql+asyncpg://" in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        logger.info("=" * 50)
        logger.info(f"DATABASE_URL: {DATABASE_URL[:60]}...")
        
        # Parse using psycopg2's connection string parser
        conn_params = psycopg2.extensions.parse_dsn(DATABASE_URL)
        
        logger.info(f"PARSED - Host: {conn_params.get('host')}, Port: {conn_params.get('port')}, DB: {conn_params.get('dbname')}, User: {conn_params.get('user')}")
        logger.info("=" * 50)
        
        return conn_params
    
    @classmethod
    def _create_pool(cls) -> pool.ThreadedConnectionPool:
        """Create connection pool."""
        params = cls._get_connection_params()
        
        logger.info("Creating psycopg2 connection pool...")
        
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            **params
        )
        
        # Test connection
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        pool.putconn(conn)
        
        logger.info("Database connection successful!")
        return pool
    
    @classmethod
    def get_pool(cls):
        """Get or create the database connection pool."""
        if cls._pool is None:
            cls._pool = cls._create_pool()
        return cls._pool
    
    @classmethod
    def close_pool(cls):
        """Close the database connection pool."""
        if cls._pool is not None:
            cls._pool.closeall()
            cls._pool = None
    
    @classmethod
    def execute_query(cls, query: str, *args):
        """Execute a query without returning rows."""
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            result = cursor.rowcount
            cursor.close()
            conn.commit()
            return result
        finally:
            pool.putconn(conn)
    
    @classmethod
    def fetch_rows(cls, query: str, *args):
        """Execute a query and return all rows."""
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dicts
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            return result
        finally:
            pool.putconn(conn)
    
    @classmethod
    def fetch_one(cls, query: str, *args):
        """Execute a query and return one row."""
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return dict(zip(columns, row))
            return None
        finally:
            pool.putconn(conn)
    
    @classmethod
    def fetch_val(cls, query: str, *args):
        """Execute a query and return a single value."""
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        finally:
            pool.putconn(conn)


def get_db_pool():
    """FastAPI dependency to get database pool."""
    return Database.get_pool()


async def check_db_connection() -> dict:
    """Check database connection health."""
    try:
        pool = Database.get_pool()
        conn = pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        pool.putconn(conn)
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)[:200],
        }