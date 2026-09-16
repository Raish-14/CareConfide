from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["patient", "professional"] = "patient"
    full_name: str
    date_of_birth: Optional[str] = None
    specialty: Optional[str] = None  # required if role == professional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    role: str
    user_id: str
    display_name: str


# ---------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------
class PatientProfile(BaseModel):
    patient_id: str
    display_id: str
    preferred_language: str
    identity_verified: bool


# ---------------------------------------------------------------------
# AI Intake
# ---------------------------------------------------------------------
class IntakeStartRequest(BaseModel):
    description: str = Field(min_length=3)


class IntakeReplyRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)


class IntakeStructuredResult(BaseModel):
    concern_category: str = ""
    symptoms: list[str] = []
    duration: str = ""
    medical_history: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []
    follow_up_question: str = ""
    summary: str = ""
    ready_for_review: bool = False


class IntakeResponse(BaseModel):
    session_id: str
    ai_mode: Literal["live", "demo"]
    structured: IntakeStructuredResult
    disclaimer: str = "AI-assisted intake — not a medical diagnosis."


# ---------------------------------------------------------------------
# Review / Clinical Profile
# ---------------------------------------------------------------------
class ClinicalProfileOut(BaseModel):
    id: str
    concern_category: Optional[str] = None
    symptoms: list[str] = []
    duration: Optional[str] = None
    medical_history: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []
    additional_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    confirmed_by_patient: bool = False


class ConfirmProfileRequest(BaseModel):
    session_id: str
    additional_notes: Optional[str] = None


# ---------------------------------------------------------------------
# Professionals / Matching
# ---------------------------------------------------------------------
class ProfessionalOut(BaseModel):
    id: str
    full_name: str
    specialty: str
    languages: list[str]
    consultation_modes: list[str]
    availability: Optional[str] = None
    bio: Optional[str] = None


# ---------------------------------------------------------------------
# Consultations
# ---------------------------------------------------------------------
class CreateConsultationRequest(BaseModel):
    professional_id: str
    clinical_profile_id: str
    mode: Literal["chat", "video", "audio"] = "chat"


class ConsultationOut(BaseModel):
    id: str
    patient_display_id: Optional[str] = None
    professional_name: Optional[str] = None
    concern_category: Optional[str] = None
    mode: str
    status: str
    created_at: str


class ConsultationMessageIn(BaseModel):
    content: str = Field(min_length=1)


class ConsultationMessageOut(BaseModel):
    sender_role: str
    content: str
    created_at: str


class ConsentUpdateRequest(BaseModel):
    consultation_id: str
    scope: Literal["clinical_data", "identity_data"]
    granted: bool


# ---------------------------------------------------------------------
# Doctor case view
# ---------------------------------------------------------------------
class DoctorCaseView(BaseModel):
    consultation_id: str
    patient_display_id: str
    status: str
    clinical_profile: Optional[ClinicalProfileOut] = None
    ai_summary: Optional[str] = None
    identity_access_granted: bool
    identity: Optional[dict] = None
