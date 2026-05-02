from supabase import create_client, Client
from core.config import settings

_supabase_client: Client = None

def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    return _supabase_client

async def check_db_connection() -> bool:
    try:
        client = get_supabase()
        result = client.table("agents").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"DB health check failed: {e}")
        return False