"""Database connection using Supabase Python client.
All database operations use the Supabase client - NO raw SQL."""
from supabase import create_client, Client
import os


supabase_client: Client = None


def get_supabase() -> Client:
    """Get or create Supabase client singleton."""
    global supabase_client
    if supabase_client is None:
        from core.config import settings
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return supabase_client