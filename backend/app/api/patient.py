from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_role
from app.services.db import db
from app.schemas.schemas import (
    ClinicalProfileOut,
    ConfirmProfileRequest,
    ConsultationOut,
    PatientProfile,
)

router = APIRouter(prefix="/api/patient", tags=["patient"])


def _get_patient_record(user: dict) -> dict:
    patient = db.get_patient_by_user_id(user["id"])
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient


@router.get("/profile", response_model=PatientProfile)
def get_profile(user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _get_patient_record(user)
    identity = db.get_identity_vault(user["id"]) or {}
    return PatientProfile(
        patient_id=patient["id"],
        display_id=patient["display_id"],
        preferred_language=patient.get("preferred_language", "en"),
        identity_verified=bool(identity.get("identity_verified")),
    )


@router.get("/consultations", response_model=list[ConsultationOut])
def list_consultations(user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _get_patient_record(user)
    results = []
    for c in db.list_consultations_by_patient(patient["id"]):
        prof = db.get_professional_by_id(c["professional_id"]) or {}
        profile = db.get_clinical_profile(c["clinical_profile_id"]) or {}
        results.append(ConsultationOut(
            id=c["id"],
            patient_display_id=patient["display_id"],
            professional_name=prof.get("full_name"),
            concern_category=profile.get("concern_category"),
            mode=c["mode"],
            status=c["status"],
            created_at=c["created_at"],
        ))
    return results


@router.get("/clinical-profiles", response_model=list[ClinicalProfileOut])
def list_clinical_profiles(user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _get_patient_record(user)
    return [ClinicalProfileOut(**cp) for cp in db.list_clinical_profiles_by_patient(patient["id"])]


@router.post("/intake/confirm", response_model=ClinicalProfileOut)
def confirm_intake(payload: ConfirmProfileRequest, user: dict = Depends(get_current_user)):
    """Patient reviews the AI-structured intake and confirms it before it
    is shared with a matched professional (the Review page)."""
    require_role(user, "patient")
    patient = _get_patient_record(user)

    session = db.get_intake_session(payload.session_id)
    if not session or session["patient_id"] != patient["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intake session not found")

    # The last AI turn's structured extraction is read back from the
    # intake_messages.structured_json column, so this works even if the
    # backend restarted between the intake conversation and this
    # confirmation step (nothing about it lives only in process memory).
    last_structured = db.get_last_structured_intake(payload.session_id)

    profile = db.create_clinical_profile(
        intake_session_id=session["id"],
        patient_id=patient["id"],
        concern_category=session.get("concern_category") or last_structured.get("concern_category"),
        symptoms=last_structured.get("symptoms", []),
        duration=last_structured.get("duration", ""),
        medical_history=last_structured.get("medical_history", []),
        medications=last_structured.get("medications", []),
        allergies=last_structured.get("allergies", []),
        additional_notes=payload.additional_notes,
        ai_summary=last_structured.get("summary", ""),
        confirmed_by_patient=True,
    )
    db.update_intake_session(session["id"], status="shared")

    db.log_audit(user["id"], "patient", "CONFIRM_CLINICAL_PROFILE", "clinical_profile", profile["id"])

    return ClinicalProfileOut(**profile)
