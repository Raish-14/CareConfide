"""
Lightweight in-process data store used as a fallback when Supabase is not
configured, so the hackathon demo works out of the box with zero setup.

When SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are both set, the
services in app/services/ talk to Supabase instead (see
app/services/db.py). This module's shape intentionally mirrors
database/schema.sql so swapping the backing store is mechanical.

This is a demo convenience, not a production data layer: data resets
whenever the process restarts.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


class InMemoryStore:
    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {}
        self.patients: dict[str, dict[str, Any]] = {}
        self.professionals: dict[str, dict[str, Any]] = {}
        self.identity_vault: dict[str, dict[str, Any]] = {}  # keyed by user_id
        self.intake_sessions: dict[str, dict[str, Any]] = {}
        self.intake_messages: dict[str, list[dict[str, Any]]] = {}  # by session_id
        self.clinical_profiles: dict[str, dict[str, Any]] = {}
        self.consultations: dict[str, dict[str, Any]] = {}
        self.consultation_messages: dict[str, list[dict[str, Any]]] = {}  # by consultation_id
        self.consents: list[dict[str, Any]] = []
        self.audit_logs: list[dict[str, Any]] = []
        self._seed()

    # ------------------------------------------------------------------
    # Seed demo data (mirrors database/seed.sql)
    # ------------------------------------------------------------------
    def _seed(self) -> None:
        demo_docs = [
            {
                "full_name": "Dr. Amara Owens",
                "specialty": "Sexual & Reproductive Health",
                "languages": ["English", "French"],
                "consultation_modes": ["chat", "video"],
                "bio": "Focuses on confidential, judgment-free reproductive health consultations.",
            },
            {
                "full_name": "Dr. Rajesh Menon",
                "specialty": "Mental Health & Counseling",
                "languages": ["English", "Hindi", "Tamil"],
                "consultation_modes": ["chat", "audio"],
                "bio": "Specializes in anxiety, stress, and sensitive personal concerns.",
            },
            {
                "full_name": "Dr. Lucia Ferreira",
                "specialty": "General & Sensitive Health",
                "languages": ["English", "Portuguese", "Spanish"],
                "consultation_modes": ["chat", "video", "audio"],
                "bio": "General practitioner with a focus on stigmatized health topics.",
            },
        ]
        prof_ids = []
        for doc in demo_docs:
            uid = new_id()
            pid = new_id()
            self.users[uid] = {"id": uid, "email": doc["full_name"].lower().replace(" ", ".") + "@demo.careconfide.app", "role": "professional"}
            self.professionals[pid] = {
                "id": pid,
                "user_id": uid,
                "is_demo": True,
                "availability": "Weekdays 10am - 4pm",
                **doc,
            }
            prof_ids.append(pid)

        # Demo patient with a pre-populated case, so the doctor dashboard
        # is never empty during a demo.
        patient_uid = new_id()
        patient_id = new_id()
        self.users[patient_uid] = {"id": patient_uid, "email": "demo.patient1@demo.careconfide.app", "role": "patient"}
        self.patients[patient_id] = {
            "id": patient_id,
            "user_id": patient_uid,
            "display_id": "Patient #A19F2",
            "preferred_language": "en",
        }
        self.identity_vault[patient_uid] = {
            "user_id": patient_uid,
            "full_name": "Jordan Ellis",
            "date_of_birth": "1996-04-12",
            "phone": "+1-555-0100",
            "identity_verified": True,
            "verification_method": "demo",
        }

        session_id = new_id()
        self.intake_sessions[session_id] = {
            "id": session_id,
            "patient_id": patient_id,
            "status": "shared",
            "concern_category": "Anxiety & Stress",
            "ai_mode": "demo",
            "created_at": now(),
        }
        self.intake_messages[session_id] = [
            {"sender": "patient", "content": "I have been feeling constantly anxious for the past three weeks and it is affecting my sleep.", "created_at": now()},
            {"sender": "ai", "content": "Thank you for sharing that. Can you tell me if anything specific triggers the anxiety, and whether you have experienced this before?", "created_at": now()},
        ]

        profile_id = new_id()
        self.clinical_profiles[profile_id] = {
            "id": profile_id,
            "intake_session_id": session_id,
            "patient_id": patient_id,
            "concern_category": "Anxiety & Stress",
            "symptoms": ["persistent worry", "difficulty sleeping", "racing thoughts"],
            "duration": "3 weeks",
            "medical_history": ["no prior diagnosed mental health condition"],
            "medications": ["none currently"],
            "allergies": ["none reported"],
            "additional_notes": "Symptoms appear linked to a recent job change.",
            "ai_summary": (
                "Patient reports a 3-week history of persistent anxiety and sleep "
                "disruption, with no prior diagnosis, possibly linked to a recent "
                "life change. Recommend professional follow-up; this is not a diagnosis."
            ),
            "confirmed_by_patient": True,
            "created_at": now(),
        }

        consult_id = new_id()
        demo_doc_id = prof_ids[1]  # Dr. Rajesh Menon - mental health
        self.consultations[consult_id] = {
            "id": consult_id,
            "patient_id": patient_id,
            "professional_id": demo_doc_id,
            "clinical_profile_id": profile_id,
            "mode": "chat",
            "status": "active",
            "created_at": now(),
        }
        self.consultation_messages[consult_id] = [
            {"sender_role": "professional", "content": "Hello, I have reviewed your intake summary. How have you been sleeping the last couple of nights?", "created_at": now()},
            {"sender_role": "patient", "content": "A little better, but I still wake up around 3am most nights.", "created_at": now()},
        ]

        self.consents.append({
            "id": new_id(), "patient_id": patient_id, "professional_id": demo_doc_id,
            "consultation_id": consult_id, "scope": "clinical_data", "granted": True, "granted_at": now(),
        })
        self.consents.append({
            "id": new_id(), "patient_id": patient_id, "professional_id": demo_doc_id,
            "consultation_id": consult_id, "scope": "identity_data", "granted": False, "granted_at": None,
        })

        # Keep handles for the demo login helper.
        self.demo_patient_user_id = patient_uid
        self.demo_patient_id = patient_id
        self.demo_professional_user_ids = [self.professionals[pid]["user_id"] for pid in prof_ids]

    def log_audit(self, actor_user_id: str | None, actor_role: str | None, action: str,
                  target_type: str | None = None, target_id: str | None = None,
                  metadata: dict | None = None) -> None:
        self.audit_logs.append({
            "id": new_id(),
            "actor_user_id": actor_user_id,
            "actor_role": actor_role,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "metadata": metadata or {},
            "created_at": now(),
        })


# NOTE: no module-level singleton is created here anymore. The active
# data backend (Supabase or in-memory) is selected once, in
# app/services/db.py, and MemoryDatabase (app/services/memory_db.py)
# is what actually instantiates InMemoryStore() when Supabase is not
# configured. This avoids seeding an unused, duplicate in-memory store
# on every import of this module.
