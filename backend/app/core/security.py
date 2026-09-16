"""
Authentication for the hackathon prototype.

Production path: Supabase Auth issues a JWT on the frontend; the backend
verifies that JWT (Supabase's public JWKS) on every request and reads
`role` out of the `users` table.

Demo path (used here so the prototype runs without wiring up full
Supabase Auth): the backend issues an opaque session token equal to the
user's id on login/register, and every request presents it as
`Authorization: Bearer <token>`. This is clearly a simplification and is
called out in the README; it is not intended to be production auth. It
is independent of which data backend (Supabase or in-memory) is active —
`db.get_user_by_id` resolves the token against whichever backend is
configured.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.services.db import db


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    user = db.get_user_by_id(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


def require_role(user: dict, role: str) -> None:
    if user.get("role") != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"This action requires the '{role}' role")
