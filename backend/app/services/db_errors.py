"""
Exception raised when a *configured* backing database (Supabase) operation
fails. This is intentionally never caught to silently fall back to the
in-memory store — per project requirements, a configured-but-failing
Supabase must surface a clear, visible error rather than pretend the
write succeeded.

app/main.py registers a FastAPI exception handler for this class so every
route gets consistent error surfacing without repeating try/except blocks.
"""
from __future__ import annotations


class DatabaseError(Exception):
    """Raised by SupabaseDatabase when a Supabase/Postgrest call fails."""

    def __init__(self, operation: str, original: Exception | str):
        self.operation = operation
        self.original = original
        super().__init__(f"Database operation '{operation}' failed: {original}")
