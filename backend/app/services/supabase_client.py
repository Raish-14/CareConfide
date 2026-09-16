"""
Lazily-constructed Supabase client using the SERVICE ROLE key.

This module is imported only by app/services/supabase_db.py (backend
code). The service role key must never reach the frontend — it is read
purely from the backend's environment (see app/core/config.py) and is
never included in any API response.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from supabase import Client


@lru_cache
def get_supabase_client() -> "Client":
    # Imported lazily (rather than at module load time) so that this
    # module — and anything that imports it — can still be imported in
    # environments/tests where the `supabase` package isn't installed
    # and Supabase isn't actually being used (e.g. pure in-memory demo
    # mode, or unit tests that inject a fake client directly).
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_configured:
        raise RuntimeError(
            "get_supabase_client() called but SUPABASE_URL / "
            "SUPABASE_SECRET_KEY are not both set."
        )
    return create_client(settings.supabase_url, settings.supabase_secret_key)
