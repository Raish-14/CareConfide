"""
Selects and exposes the single active data-access backend for the whole
backend.

- If SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are both set, `db` is a
  SupabaseDatabase and every read/write goes to the real Postgres tables
  created by database/schema.sql.
- Otherwise `db` is a MemoryDatabase — the explicit, documented demo
  fallback (see app/services/memory_db.py).

Once selected, the backend is NOT swapped mid-request: if Supabase is
configured but a call fails, SupabaseDatabase raises DatabaseError
(app/services/db_errors.py), which app/main.py turns into a clear HTTP
503 — we never quietly fall back to memory after startup.
"""
from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger("careconfide.db")

settings = get_settings()

if settings.supabase_configured:
    from app.services.supabase_db import SupabaseDatabase

    try:
        db = SupabaseDatabase()
        DATA_MODE = "supabase"
        logger.info("CareConfide backend: using Supabase persistence at %s", settings.supabase_url)
    except Exception as exc:  # noqa: BLE001
        # Fail loudly at startup rather than quietly falling back — a
        # misconfigured Supabase project should be obvious immediately,
        # not discovered on the first API call.
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are set but the Supabase "
            f"client could not be initialized: {exc}"
        ) from exc
else:
    from app.services.memory_db import MemoryDatabase

    db = MemoryDatabase()
    DATA_MODE = "in_memory_demo"
    logger.warning(
        "CareConfide backend: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — "
        "using in-memory demo store. Data will NOT persist across restarts."
    )
