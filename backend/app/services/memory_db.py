"""
In-memory implementation of the CareConfide data-access layer.

This is the explicit fallback/demo mode used ONLY when Supabase is not
configured (see app/services/db.py). It implements the exact same
method surface as SupabaseDatabase so the API routers do not need to
know or care which backend is active.

Data lives only in this process's memory and is lost on restart — this
is a deliberate, documented limitation of demo mode, not a bug.
"""
from __future__ import annotations

from typing import Any

from app.core.store import InMemoryStore, new_id, now


class MemoryDatabase:
    def __init__(self) -> None:
        self.store = InMemoryStore()

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    def get_user_by_email(self, email: str) -> dict | None:
        return next((u for u in self.store.users.values() if u["email"] == email), None)

    def get_user_by_id(self, user_id: str) -> dict | None:
        return self.store.users.get(user_id)

    def create_user(self, email: str, role: str) -> dict:
        user_id = new_id()
        row = {"id": user_id, "email": email, "role": role, "created_at": now()}
        self.store.users[user_id] = row
        return row

    # ------------------------------------------------------------------
    # patients
    # ------------------------------------------------------------------
    def create_patient(self, user_id: str, display_id: str, preferred_language: str = "en") -> dict:
        patient_id = new_id()
        row = {
            "id": patient_id, "user_id": user_id, "display_id": display_id,
            "preferred_language": preferred_language, "created_at": now(),
        }
        self.store.patients[patient_id] = row
        return row

    def get_patient_by_user_id(self, user_id: str) -> dict | None:
        return next((p for p in self.store.patients.values() if p["user_id"] == user_id), None)

    def get_patient_by_id(self, patient_id: str) -> dict | None:
        return self.store.patients.get(patient_id)

    def get_any_patient(self) -> dict | None:
        return next(iter(self.store.patients.values()), None)

    # ------------------------------------------------------------------
    # identity_vault
    # ------------------------------------------------------------------
    def create_identity_vault(self, user_id: str, full_name: str, date_of_birth: str | None,
                               phone: str | None, identity_verified: bool,
                               verification_method: str | None) -> dict:
        row = {
            "user_id": user_id, "full_name": full_name, "date_of_birth": date_of_birth,
            "phone": phone, "identity_verified": identity_verified,
            "verification_method": verification_method, "created_at": now(),
        }
        self.store.identity_vault[user_id] = row
        return row

    def get_identity_vault(self, user_id: str) -> dict | None:
        return self.store.identity_vault.get(user_id)

    # ------------------------------------------------------------------
    # professionals
    # ------------------------------------------------------------------
    def create_professional(self, user_id: str, full_name: str, specialty: str,
                             languages: list[str], consultation_modes: list[str],
                             bio: str | None, is_demo: bool = False) -> dict:
        prof_id = new_id()
        row = {
            "id": prof_id, "user_id": user_id, "full_name": full_name, "specialty": specialty,
            "languages": languages, "consultation_modes": consultation_modes, "bio": bio,
            "is_demo": is_demo, "availability": "Weekdays 10am – 4pm" if is_demo else "By request",
            "created_at": now(),
        }
        self.store.professionals[prof_id] = row
        return row

    def get_professional_by_user_id(self, user_id: str) -> dict | None:
        return next((p for p in self.store.professionals.values() if p["user_id"] == user_id), None)

    def get_professional_by_id(self, professional_id: str) -> dict | None:
        return self.store.professionals.get(professional_id)

    def list_professionals(self) -> list[dict]:
        return list(self.store.professionals.values())

    # ------------------------------------------------------------------
    # intake_sessions / intake_messages
    # ------------------------------------------------------------------
    def create_intake_session(self, patient_id: str, status: str = "in_progress",
                               concern_category: str | None = None, ai_mode: str = "live") -> dict:
        session_id = new_id()
        row = {
            "id": session_id, "patient_id": patient_id, "status": status,
            "concern_category": concern_category, "ai_mode": ai_mode, "created_at": now(),
        }
        self.store.intake_sessions[session_id] = row
        self.store.intake_messages[session_id] = []
        return row

    def get_intake_session(self, session_id: str) -> dict | None:
        return self.store.intake_sessions.get(session_id)

    def update_intake_session(self, session_id: str, **fields: Any) -> dict:
        session = self.store.intake_sessions[session_id]
        session.update(fields)
        return session

    def add_intake_message(self, session_id: str, sender: str, content: str,
                            structured_json: dict | None = None) -> dict:
        row = {
            "id": new_id(), "session_id": session_id, "sender": sender, "content": content,
            "structured_json": structured_json, "created_at": now(),
        }
        self.store.intake_messages.setdefault(session_id, []).append(row)
        return row

    def list_intake_messages(self, session_id: str) -> list[dict]:
        return self.store.intake_messages.get(session_id, [])

    def get_last_structured_intake(self, session_id: str) -> dict:
        messages = self.list_intake_messages(session_id)
        for message in reversed(messages):
            if message["sender"] == "ai" and message.get("structured_json"):
                return message["structured_json"]
        return {}

    # ------------------------------------------------------------------
    # clinical_profiles
    # ------------------------------------------------------------------
    def create_clinical_profile(self, intake_session_id: str, patient_id: str,
                                 concern_category: str | None, symptoms: list[str],
                                 duration: str | None, medical_history: list[str],
                                 medications: list[str], allergies: list[str],
                                 additional_notes: str | None, ai_summary: str | None,
                                 confirmed_by_patient: bool = True) -> dict:
        profile_id = new_id()
        row = {
            "id": profile_id, "intake_session_id": intake_session_id, "patient_id": patient_id,
            "concern_category": concern_category, "symptoms": symptoms, "duration": duration,
            "medical_history": medical_history, "medications": medications, "allergies": allergies,
            "additional_notes": additional_notes, "ai_summary": ai_summary,
            "confirmed_by_patient": confirmed_by_patient, "created_at": now(),
        }
        self.store.clinical_profiles[profile_id] = row
        return row

    def get_clinical_profile(self, profile_id: str) -> dict | None:
        return self.store.clinical_profiles.get(profile_id)

    def list_clinical_profiles_by_patient(self, patient_id: str) -> list[dict]:
        return [cp for cp in self.store.clinical_profiles.values() if cp["patient_id"] == patient_id]

    # ------------------------------------------------------------------
    # consultations / consultation_messages
    # ------------------------------------------------------------------
    def create_consultation(self, patient_id: str, professional_id: str,
                             clinical_profile_id: str, mode: str, status: str = "requested") -> dict:
        consult_id = new_id()
        row = {
            "id": consult_id, "patient_id": patient_id, "professional_id": professional_id,
            "clinical_profile_id": clinical_profile_id, "mode": mode, "status": status,
            "created_at": now(),
        }
        self.store.consultations[consult_id] = row
        self.store.consultation_messages[consult_id] = []
        return row

    def get_consultation(self, consultation_id: str) -> dict | None:
        return self.store.consultations.get(consultation_id)

    def list_consultations_by_patient(self, patient_id: str) -> list[dict]:
        return [c for c in self.store.consultations.values() if c["patient_id"] == patient_id]

    def list_consultations_by_professional(self, professional_id: str) -> list[dict]:
        return [c for c in self.store.consultations.values() if c["professional_id"] == professional_id]

    def update_consultation_status(self, consultation_id: str, status: str) -> dict:
        consultation = self.store.consultations[consultation_id]
        consultation["status"] = status
        return consultation

    def add_consultation_message(self, consultation_id: str, sender_role: str, content: str) -> dict:
        row = {"id": new_id(), "consultation_id": consultation_id, "sender_role": sender_role,
               "content": content, "created_at": now()}
        self.store.consultation_messages.setdefault(consultation_id, []).append(row)
        return row

    def list_consultation_messages(self, consultation_id: str) -> list[dict]:
        return self.store.consultation_messages.get(consultation_id, [])

    # ------------------------------------------------------------------
    # consents
    # ------------------------------------------------------------------
    def create_consent(self, patient_id: str, professional_id: str, consultation_id: str,
                        scope: str, granted: bool, granted_at: str | None) -> dict:
        row = {
            "id": new_id(), "patient_id": patient_id, "professional_id": professional_id,
            "consultation_id": consultation_id, "scope": scope, "granted": granted,
            "granted_at": granted_at, "revoked_at": None, "created_at": now(),
        }
        self.store.consents.append(row)
        return row

    def get_consent(self, consultation_id: str, scope: str, patient_id: str | None = None) -> dict | None:
        for c in self.store.consents:
            if c["consultation_id"] == consultation_id and c["scope"] == scope:
                if patient_id and c["patient_id"] != patient_id:
                    continue
                return c
        return None

    def update_consent(self, consent_id: str, granted: bool, granted_at: str | None,
                        revoked_at: str | None = None) -> dict:
        consent = next(c for c in self.store.consents if c["id"] == consent_id)
        consent["granted"] = granted
        consent["granted_at"] = granted_at
        if revoked_at is not None:
            consent["revoked_at"] = revoked_at
        return consent

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    def log_audit(self, actor_user_id: str | None, actor_role: str | None, action: str,
                  target_type: str | None = None, target_id: str | None = None,
                  metadata: dict | None = None) -> dict:
        row = {
            "id": new_id(), "actor_user_id": actor_user_id, "actor_role": actor_role,
            "action": action, "target_type": target_type, "target_id": target_id,
            "metadata": metadata or {}, "created_at": now(),
        }
        self.store.audit_logs.append(row)
        return row
