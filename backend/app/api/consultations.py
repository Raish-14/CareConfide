from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_role
from app.services.db import db
from app.schemas.schemas import (
    ConsentUpdateRequest,
    ConsultationMessageIn,
    ConsultationMessageOut,
    ConsultationOut,
    CreateConsultationRequest,
)

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _patient_for(user: dict) -> dict:
    patient = db.get_patient_by_user_id(user["id"])
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient


def _professional_for(user: dict) -> dict:
    prof = db.get_professional_by_user_id(user["id"])
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
    return prof


def _authorized_for_consultation(user: dict, consultation: dict) -> bool:
    if user["role"] == "patient":
        patient = _patient_for(user)
        return consultation["patient_id"] == patient["id"]
    if user["role"] == "professional":
        prof = _professional_for(user)
        return consultation["professional_id"] == prof["id"]
    return False


@router.post("", response_model=ConsultationOut, status_code=status.HTTP_201_CREATED)
def create_consultation(payload: CreateConsultationRequest, user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _patient_for(user)

    profile = db.get_clinical_profile(payload.clinical_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical profile not found")
    professional = db.get_professional_by_id(payload.professional_id)
    if not professional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found")

    consultation = db.create_consultation(
        patient_id=patient["id"],
        professional_id=payload.professional_id,
        clinical_profile_id=payload.clinical_profile_id,
        mode=payload.mode,
        status="requested",
    )

    # Default consent: clinical data shared, identity withheld until the
    # patient explicitly grants it.
    db.create_consent(
        patient_id=patient["id"], professional_id=payload.professional_id,
        consultation_id=consultation["id"], scope="clinical_data", granted=True, granted_at=_now(),
    )
    db.create_consent(
        patient_id=patient["id"], professional_id=payload.professional_id,
        consultation_id=consultation["id"], scope="identity_data", granted=False, granted_at=None,
    )

    db.log_audit(user["id"], "patient", "REQUEST_CONSULTATION", "consultation", consultation["id"])

    return ConsultationOut(
        id=consultation["id"], patient_display_id=patient["display_id"], professional_name=professional["full_name"],
        concern_category=profile.get("concern_category"), mode=payload.mode, status="requested",
        created_at=consultation["created_at"],
    )


@router.get("/{consultation_id}/messages", response_model=list[ConsultationMessageOut])
def get_messages(consultation_id: str, user: dict = Depends(get_current_user)):
    consultation = db.get_consultation(consultation_id)
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    if not _authorized_for_consultation(user, consultation):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this consultation")
    return db.list_consultation_messages(consultation_id)


@router.post("/{consultation_id}/messages", response_model=ConsultationMessageOut, status_code=status.HTTP_201_CREATED)
def post_message(consultation_id: str, payload: ConsultationMessageIn, user: dict = Depends(get_current_user)):
    consultation = db.get_consultation(consultation_id)
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
    if not _authorized_for_consultation(user, consultation):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this consultation")

    sender_role = "patient" if user["role"] == "patient" else "professional"
    message = db.add_consultation_message(consultation_id, sender_role=sender_role, content=payload.content)

    if consultation["status"] == "requested":
        db.update_consultation_status(consultation_id, "active")

    return ConsultationMessageOut(sender_role=message["sender_role"], content=message["content"], created_at=message["created_at"])


@router.post("/consent", status_code=status.HTTP_200_OK)
def update_consent(payload: ConsentUpdateRequest, user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _patient_for(user)

    consent = db.get_consent(payload.consultation_id, payload.scope, patient_id=patient["id"])
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found")

    db.update_consent(
        consent["id"],
        granted=payload.granted,
        granted_at=_now() if payload.granted else None,
        revoked_at=_now() if not payload.granted else None,
    )

    db.log_audit(
        user["id"], "patient",
        "GRANT_CONSENT" if payload.granted else "REVOKE_CONSENT",
        "consent", consent["id"], {"scope": payload.scope, "consultation_id": payload.consultation_id},
    )
    return {"scope": payload.scope, "granted": payload.granted}
