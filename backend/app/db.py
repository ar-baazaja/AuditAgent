"""Supabase client factory (server-side, service_role).

The backend is a trusted server, so it uses the service_role key and bypasses
RLS. This is the ONLY place that key is used. Frontend never sees it.
"""
from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache
def get_supabase() -> Client:
    """Return a cached service-role Supabase client."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
