"""
Supabase-backed implementation of the CareConfide data-access layer.

Every method here performs a REAL read/write against the Supabase
PostgreSQL tables created by database/schema.sql — there is no
in-memory fallback inside this class. If a Supabase/Postgrest call
fails, the method raises DatabaseError, which app/main.py turns into a
clear HTTP 503 response (see the `database_error_handler`). We never
catch a failure here and silently write to memory instead: a 200/201
response from this class always means the row genuinely exists in
Supabase.

Column names and enum values below are taken directly from
database/schema.sql — no schema changes were made or required for
this implementation. One deliberate exception is documented at
`_availability_for`: the `professionals` table has no `availability`
column, so that display-only field is derived instead of stored (see
that method for the full explanation).
"""
from __future__ import annotations

from typing import Any

from app.services.db_errors import DatabaseError
from app.services.supabase_client import get_supabase_client


def _run(operation: str, builder):
    """Execute a Postgrest query builder, converting any failure into a
    DatabaseError so callers never mistake a failed write for a
    successful one."""
    try:
        response = builder.execute()
    except Exception as exc:  # noqa: BLE001 - we deliberately want to catch everything Postgrest/httpx can raise
        raise DatabaseError(operation, exc) from exc
    return response.data


class SupabaseDatabase:
    """Implements the same method surface as MemoryDatabase, backed by
    real Supabase tables. See database/schema.sql for the table
    definitions this class reads and writes."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    def get_user_by_email(self, email: str) -> dict | None:
        rows = _run(
            "get_user_by_email",
            self.client.table("users").select("*").eq("email", email).limit(1),
        )
        return rows[0] if rows else None

    def get_user_by_id(self, user_id: str) -> dict | None:
        rows = _run(
            "get_user_by_id",
            self.client.table("users").select("*").eq("id", user_id).limit(1),
        )
        return rows[0] if rows else None

    def create_user(self, email: str, role: str) -> dict:
        rows = _run(
            "create_user",
            self.client.table("users").insert({"email": email, "role": role}),
        )
        return rows[0]

    # ------------------------------------------------------------------
    # patients
    # ------------------------------------------------------------------
    def create_patient(self, user_id: str, display_id: str, preferred_language: str = "en") -> dict:
        rows = _run(
            "create_patient",
            self.client.table("patients").insert({
                "user_id": user_id,
                "display_id": display_id,
                "preferred_language": preferred_language,
            }),
        )
        return rows[0]

    def get_patient_by_user_id(self, user_id: str) -> dict | None:
        rows = _run(
            "get_patient_by_user_id",
            self.client.table("patients").select("*").eq("user_id", user_id).limit(1),
        )
        return rows[0] if rows else None

    def get_patient_by_id(self, patient_id: str) -> dict | None:
        rows = _run(
            "get_patient_by_id",
            self.client.table("patients").select("*").eq("id", patient_id).limit(1),
        )
        return rows[0] if rows else None

    def get_any_patient(self) -> dict | None:
        rows = _run("get_any_patient", self.client.table("patients").select("*").limit(1))
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # identity_vault
    # ------------------------------------------------------------------
    def create_identity_vault(self, user_id: str, full_name: str, date_of_birth: str | None,
                               phone: str | None, identity_verified: bool,
                               verification_method: str | None) -> dict:
        rows = _run(
            "create_identity_vault",
            self.client.table("identity_vault").insert({
                "user_id": user_id,
                "full_name": full_name,
                "date_of_birth": date_of_birth,
                "phone": phone,
                "identity_verified": identity_verified,
                "verification_method": verification_method,
            }),
        )
        return rows[0]

    def get_identity_vault(self, user_id: str) -> dict | None:
        rows = _run(
            "get_identity_vault",
            self.client.table("identity_vault").select("*").eq("user_id", user_id).limit(1),
        )
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # professionals
    # ------------------------------------------------------------------
    @staticmethod
    def _availability_for(professional_row: dict) -> str:
        """
        `professionals.availability` does not exist in database/schema.sql
        (see the SCOPE NOTE in this project's README/limitations). Rather
        than modify the schema for a display-only convenience field, we
        derive a reasonable value here: seeded demo professionals show a
        fixed office-hours string, real registered professionals show
        'By request'. This mirrors the original in-memory prototype's
        behavior without requiring a schema change.
        """
        return "Weekdays 10am – 4pm" if professional_row.get("is_demo") else "By request"

    def create_professional(self, user_id: str, full_name: str, specialty: str,
                             languages: list[str], consultation_modes: list[str],
                             bio: str | None, is_demo: bool = False) -> dict:
        rows = _run(
            "create_professional",
            self.client.table("professionals").insert({
                "user_id": user_id,
                "full_name": full_name,
                "specialty": specialty,
                "languages": languages,
                "consultation_modes": consultation_modes,
                "bio": bio,
                "is_demo": is_demo,
            }),
        )
        row = rows[0]
        row["availability"] = self._availability_for(row)
        return row

    def get_professional_by_user_id(self, user_id: str) -> dict | None:
        rows = _run(
            "get_professional_by_user_id",
            self.client.table("professionals").select("*").eq("user_id", user_id).limit(1),
        )
        if not rows:
            return None
        row = rows[0]
        row["availability"] = self._availability_for(row)
        return row

    def get_professional_by_id(self, professional_id: str) -> dict | None:
        rows = _run(
            "get_professional_by_id",
            self.client.table("professionals").select("*").eq("id", professional_id).limit(1),
        )
        if not rows:
            return None
        row = rows[0]
        row["availability"] = self._availability_for(row)
        return row

    def list_professionals(self) -> list[dict]:
        rows = _run("list_professionals", self.client.table("professionals").select("*"))
        for row in rows:
            row["availability"] = self._availability_for(row)
        return rows

    # ------------------------------------------------------------------
    # intake_sessions / intake_messages
    # ------------------------------------------------------------------
    def create_intake_session(self, patient_id: str, status: str = "in_progress",
                               concern_category: str | None = None, ai_mode: str = "live") -> dict:
        rows = _run(
            "create_intake_session",
            self.client.table("intake_sessions").insert({
                "patient_id": patient_id,
                "status": status,
                "concern_category": concern_category,
                "ai_mode": ai_mode,
            }),
        )
        return rows[0]

    def get_intake_session(self, session_id: str) -> dict | None:
        rows = _run(
            "get_intake_session",
            self.client.table("intake_sessions").select("*").eq("id", session_id).limit(1),
        )
        return rows[0] if rows else None

    def update_intake_session(self, session_id: str, **fields: Any) -> dict:
        rows = _run(
            "update_intake_session",
            self.client.table("intake_sessions").update(fields).eq("id", session_id),
        )
        return rows[0]

    def add_intake_message(self, session_id: str, sender: str, content: str,
                            structured_json: dict | None = None) -> dict:
        rows = _run(
            "add_intake_message",
            self.client.table("intake_messages").insert({
                "session_id": session_id,
                "sender": sender,
                "content": content,
                "structured_json": structured_json,
            }),
        )
        return rows[0]

    def list_intake_messages(self, session_id: str) -> list[dict]:
        return _run(
            "list_intake_messages",
            self.client.table("intake_messages").select("*").eq("session_id", session_id).order("created_at"),
        )

    def get_last_structured_intake(self, session_id: str) -> dict:
        """Returns the structured_json of the most recent AI message for
        this session, so the review/confirm step works even after a
        backend restart (nothing about it is kept in process memory)."""
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
        rows = _run(
            "create_clinical_profile",
            self.client.table("clinical_profiles").insert({
                "intake_session_id": intake_session_id,
                "patient_id": patient_id,
                "concern_category": concern_category,
                "symptoms": symptoms,
                "duration": duration,
                "medical_history": medical_history,
                "medications": medications,
                "allergies": allergies,
                "additional_notes": additional_notes,
                "ai_summary": ai_summary,
                "confirmed_by_patient": confirmed_by_patient,
            }),
        )
        return rows[0]

    def get_clinical_profile(self, profile_id: str) -> dict | None:
        rows = _run(
            "get_clinical_profile",
            self.client.table("clinical_profiles").select("*").eq("id", profile_id).limit(1),
        )
        return rows[0] if rows else None

    def list_clinical_profiles_by_patient(self, patient_id: str) -> list[dict]:
        return _run(
            "list_clinical_profiles_by_patient",
            self.client.table("clinical_profiles").select("*").eq("patient_id", patient_id),
        )

    # ------------------------------------------------------------------
    # consultations / consultation_messages
    # ------------------------------------------------------------------
    def create_consultation(self, patient_id: str, professional_id: str,
                             clinical_profile_id: str, mode: str, status: str = "requested") -> dict:
        rows = _run(
            "create_consultation",
            self.client.table("consultations").insert({
                "patient_id": patient_id,
                "professional_id": professional_id,
                "clinical_profile_id": clinical_profile_id,
                "mode": mode,
                "status": status,
            }),
        )
        return rows[0]

    def get_consultation(self, consultation_id: str) -> dict | None:
        rows = _run(
            "get_consultation",
            self.client.table("consultations").select("*").eq("id", consultation_id).limit(1),
        )
        return rows[0] if rows else None

    def list_consultations_by_patient(self, patient_id: str) -> list[dict]:
        return _run(
            "list_consultations_by_patient",
            self.client.table("consultations").select("*").eq("patient_id", patient_id),
        )

    def list_consultations_by_professional(self, professional_id: str) -> list[dict]:
        return _run(
            "list_consultations_by_professional",
            self.client.table("consultations").select("*").eq("professional_id", professional_id),
        )

    def update_consultation_status(self, consultation_id: str, status: str) -> dict:
        rows = _run(
            "update_consultation_status",
            self.client.table("consultations").update({"status": status}).eq("id", consultation_id),
        )
        return rows[0]

    def add_consultation_message(self, consultation_id: str, sender_role: str, content: str) -> dict:
        rows = _run(
            "add_consultation_message",
            self.client.table("consultation_messages").insert({
                "consultation_id": consultation_id,
                "sender_role": sender_role,
                "content": content,
            }),
        )
        return rows[0]

    def list_consultation_messages(self, consultation_id: str) -> list[dict]:
        return _run(
            "list_consultation_messages",
            self.client.table("consultation_messages").select("*").eq("consultation_id", consultation_id).order("created_at"),
        )

    # ------------------------------------------------------------------
    # consents
    # ------------------------------------------------------------------
    def create_consent(self, patient_id: str, professional_id: str, consultation_id: str,
                        scope: str, granted: bool, granted_at: str | None) -> dict:
        rows = _run(
            "create_consent",
            self.client.table("consents").insert({
                "patient_id": patient_id,
                "professional_id": professional_id,
                "consultation_id": consultation_id,
                "scope": scope,
                "granted": granted,
                "granted_at": granted_at,
            }),
        )
        return rows[0]

    def get_consent(self, consultation_id: str, scope: str, patient_id: str | None = None) -> dict | None:
        query = self.client.table("consents").select("*").eq("consultation_id", consultation_id).eq("scope", scope)
        if patient_id:
            query = query.eq("patient_id", patient_id)
        rows = _run("get_consent", query.limit(1))
        return rows[0] if rows else None

    def update_consent(self, consent_id: str, granted: bool, granted_at: str | None,
                        revoked_at: str | None = None) -> dict:
        fields: dict[str, Any] = {"granted": granted, "granted_at": granted_at}
        if revoked_at is not None:
            fields["revoked_at"] = revoked_at
        rows = _run(
            "update_consent",
            self.client.table("consents").update(fields).eq("id", consent_id),
        )
        return rows[0]

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    def log_audit(self, actor_user_id: str | None, actor_role: str | None, action: str,
                  target_type: str | None = None, target_id: str | None = None,
                  metadata: dict | None = None) -> dict:
        rows = _run(
            "log_audit",
            self.client.table("audit_logs").insert({
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "metadata": metadata or {},
            }),
        )
        return rows[0]
