"""
Supabase client factory.
All data access goes through app/query/*.py — no raw SQL strings here.
"""
from functools import lru_cache

from supabase import create_client, Client

from app.config import settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


def init_db() -> None:
    """Schema is managed via supabase/schema.sql — nothing to do at runtime."""
    pass
