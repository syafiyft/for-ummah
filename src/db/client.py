"""
Supabase client singleton.
Provides a single reusable connection to Supabase.
"""

import logging
from functools import lru_cache

from supabase import create_client, Client

from src.core import settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Get or create the Supabase client singleton.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    global _client

    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )

        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized")

    return _client


def is_supabase_configured() -> bool:
    """Check if Supabase credentials are configured."""
    return bool(settings.supabase_url and settings.supabase_key)
