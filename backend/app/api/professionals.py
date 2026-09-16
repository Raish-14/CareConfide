from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user, require_role
from app.services.db import db
from app.schemas.schemas import ProfessionalOut

router = APIRouter(prefix="/api/professionals", tags=["professionals"])


@router.get("", response_model=list[ProfessionalOut])
def list_professionals(
    specialty: str | None = Query(default=None),
    language: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    require_role(user, "patient")
    results = []
    for p in db.list_professionals():
        if specialty and specialty.lower() not in p["specialty"].lower():
            continue
        if language and language.lower() not in [l.lower() for l in p["languages"]]:
            continue
        if mode and mode.lower() not in [m.lower() for m in p["consultation_modes"]]:
            continue
        results.append(ProfessionalOut(
            id=p["id"],
            full_name=p["full_name"],
            specialty=p["specialty"],
            languages=p["languages"],
            consultation_modes=p["consultation_modes"],
            availability=p.get("availability"),
            bio=p.get("bio"),
        ))
    return results
