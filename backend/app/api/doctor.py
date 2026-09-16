from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_role
from app.services.db import db
from app.schemas.schemas import ClinicalProfileOut, ConsultationOut, DoctorCaseView

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


def _professional_for(user: dict) -> dict:
    prof = db.get_professional_by_user_id(user["id"])
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional profile not found")
    return prof


@router.get("/consultations", response_model=list[ConsultationOut])
def list_consultations(user: dict = Depends(get_current_user)):
    require_role(user, "professional")
    prof = _professional_for(user)
    results = []
    for c in db.list_consultations_by_professional(prof["id"]):
        patient = db.get_patient_by_id(c["patient_id"]) or {}
        profile = db.get_clinical_profile(c["clinical_profile_id"]) or {}
        results.append(ConsultationOut(
            id=c["id"],
            patient_display_id=patient.get("display_id"),
            professional_name=prof["full_name"],
            concern_category=profile.get("concern_category"),
            mode=c["mode"],
            status=c["status"],
            created_at=c["created_at"],
        ))
    return results


@router.get("/consultations/{consultation_id}", response_model=DoctorCaseView)
def get_case(consultation_id: str, user: dict = Depends(get_current_user)):
    require_role(user, "professional")
    prof = _professional_for(user)

    consultation = db.get_consultation(consultation_id)
    if not consultation or consultation["professional_id"] != prof["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")

    patient = db.get_patient_by_id(consultation["patient_id"]) or {}
    profile = db.get_clinical_profile(consultation["clinical_profile_id"])

    identity_consent = db.get_consent(consultation_id, "identity_data")
    identity_granted = bool(identity_consent and identity_consent["granted"])

    identity = None
    if identity_granted:
        identity_record = db.get_identity_vault(patient.get("user_id"))
        if identity_record:
            identity = {
                "full_name": identity_record["full_name"],
                "date_of_birth": identity_record.get("date_of_birth"),
                "phone": identity_record.get("phone"),
                "identity_verified": identity_record.get("identity_verified", False),
            }
        db.log_audit(user["id"], "professional", "VIEW_IDENTITY", "patient", consultation["patient_id"])

    db.log_audit(user["id"], "professional", "VIEW_CLINICAL", "clinical_profile",
                 profile["id"] if profile else None)

    return DoctorCaseView(
        consultation_id=consultation_id,
        patient_display_id=patient.get("display_id", "Unknown"),
        status=consultation["status"],
        clinical_profile=ClinicalProfileOut(**profile) if profile else None,
        ai_summary=profile.get("ai_summary") if profile else None,
        identity_access_granted=identity_granted,
        identity=identity,
    )
