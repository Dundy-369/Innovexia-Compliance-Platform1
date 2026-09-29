from functools import lru_cache
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, validate_config

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    validate_config()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
