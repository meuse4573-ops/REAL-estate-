"""
Database connection using Supabase Python client.
All database operations use the Supabase client - NO raw SQL.
"""
from supabase import create_client, Client
import os
import logging

logger = logging.getLogger(__name__)

# Supabase client singleton
supabase: Client = None


def get_supabase() -> Client:
    """Get or create Supabase client singleton."""
    global supabase
    if supabase is None:
        from core.config import settings
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase client created successfully")
    return supabase


async def check_db_connection() -> dict:
    """Check database connection health."""
    try:
        client = get_supabase()
        # Simple test query
        result = client.table("agents").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)[:200],
        }