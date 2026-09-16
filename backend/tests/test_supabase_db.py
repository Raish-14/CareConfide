"""
Tests for the Supabase persistence layer (app/services/supabase_db.py).

These run against `tests/fake_supabase.py`, a tiny in-process stand-in
for the real Postgrest client — so they exercise the EXACT same code
paths and column names that will run against a real Supabase project,
without needing network access or real credentials.

Run directly with:  python3 tests/test_supabase_db.py
Also collectible by pytest if it's installed:  pytest tests/
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.fake_supabase import make_supabase_database  # noqa: E402
from app.services.db_errors import DatabaseError  # noqa: E402


def test_create_and_get_user():
    db, _ = make_supabase_database()
    created = db.create_user(email="alice@example.com", role="patient")
    assert created["email"] == "alice@example.com"
    assert created["role"] == "patient"
    assert "id" in created

    fetched_by_email = db.get_user_by_email("alice@example.com")
    assert fetched_by_email["id"] == created["id"]

    fetched_by_id = db.get_user_by_id(created["id"])
    assert fetched_by_id["email"] == "alice@example.com"

    assert db.get_user_by_email("nobody@example.com") is None


def test_full_patient_registration_workflow():
    db, _ = make_supabase_database()

    user = db.create_user(email="bob@example.com", role="patient")
    patient = db.create_patient(user_id=user["id"], display_id="Patient #BOB01", preferred_language="en")
    assert patient["user_id"] == user["id"]

    identity = db.create_identity_vault(
        user_id=user["id"], full_name="Bob Example", date_of_birth="1990-01-01",
        phone="+1-555-0000", identity_verified=False, verification_method=None,
    )
    assert identity["full_name"] == "Bob Example"

    fetched_patient = db.get_patient_by_user_id(user["id"])
    assert fetched_patient["id"] == patient["id"]

    fetched_identity = db.get_identity_vault(user["id"])
    assert fetched_identity["date_of_birth"] == "1990-01-01"


def test_professional_registration_and_listing():
    db, _ = make_supabase_database()
    user = db.create_user(email="dr.who@example.com", role="professional")
    prof = db.create_professional(
        user_id=user["id"], full_name="Dr. Who", specialty="General & Sensitive Health",
        languages=["English"], consultation_modes=["chat"], bio=None, is_demo=False,
    )
    assert prof["specialty"] == "General & Sensitive Health"
    # availability is derived, not a real column — confirm it's present anyway
    assert prof["availability"] == "By request"

    listed = db.list_professionals()
    assert any(p["id"] == prof["id"] for p in listed)


def test_intake_flow_persists_structured_json_and_survives_new_instance():
    backing: dict = {}
    db, _ = make_supabase_database(backing)

    user = db.create_user(email="carol@example.com", role="patient")
    patient = db.create_patient(user_id=user["id"], display_id="Patient #CAR01")

    session = db.create_intake_session(patient_id=patient["id"], status="in_progress", ai_mode="demo")
    db.add_intake_message(session["id"], sender="patient", content="I've had a persistent cough for two weeks.")
    structured = {
        "concern_category": "Respiratory",
        "symptoms": ["cough"],
        "duration": "2 weeks",
        "medical_history": [],
        "medications": [],
        "allergies": [],
        "follow_up_question": "",
        "summary": "Patient reports a 2-week cough.",
        "ready_for_review": True,
    }
    db.add_intake_message(session["id"], sender="ai", content=structured["summary"], structured_json=structured)
    db.update_intake_session(session["id"], status="ready_for_review", concern_category="Respiratory")

    profile = db.create_clinical_profile(
        intake_session_id=session["id"], patient_id=patient["id"],
        concern_category=structured["concern_category"], symptoms=structured["symptoms"],
        duration=structured["duration"], medical_history=[], medications=[], allergies=[],
        additional_notes=None, ai_summary=structured["summary"], confirmed_by_patient=True,
    )

    # --- simulate a full backend restart: throw away `db` entirely and
    # build a brand new SupabaseDatabase instance. It only shares the
    # `backing` dict, which stands in for the real, durable Postgres data. ---
    del db
    db2, _ = make_supabase_database(backing)

    reloaded_session = db2.get_intake_session(session["id"])
    assert reloaded_session["status"] == "ready_for_review"

    last_structured = db2.get_last_structured_intake(session["id"])
    assert last_structured["concern_category"] == "Respiratory"
    assert last_structured["symptoms"] == ["cough"]

    reloaded_profiles = db2.list_clinical_profiles_by_patient(patient["id"])
    assert len(reloaded_profiles) == 1
    assert reloaded_profiles[0]["id"] == profile["id"]
    assert reloaded_profiles[0]["ai_summary"] == "Patient reports a 2-week cough."


def test_consultation_and_messages_survive_new_instance():
    backing: dict = {}
    db, _ = make_supabase_database(backing)

    patient_user = db.create_user(email="dana@example.com", role="patient")
    patient = db.create_patient(user_id=patient_user["id"], display_id="Patient #DAN01")
    prof_user = db.create_user(email="dr.jones@example.com", role="professional")
    professional = db.create_professional(
        user_id=prof_user["id"], full_name="Dr. Jones", specialty="Mental Health & Counseling",
        languages=["English"], consultation_modes=["chat"], bio=None, is_demo=False,
    )
    session = db.create_intake_session(patient_id=patient["id"], ai_mode="demo")
    profile = db.create_clinical_profile(
        intake_session_id=session["id"], patient_id=patient["id"], concern_category="Anxiety",
        symptoms=["worry"], duration="1 week", medical_history=[], medications=[], allergies=[],
        additional_notes=None, ai_summary="summary", confirmed_by_patient=True,
    )

    consultation = db.create_consultation(
        patient_id=patient["id"], professional_id=professional["id"],
        clinical_profile_id=profile["id"], mode="chat", status="requested",
    )
    db.create_consent(patient["id"], professional["id"], consultation["id"], "clinical_data", True, "2026-01-01T00:00:00")
    db.create_consent(patient["id"], professional["id"], consultation["id"], "identity_data", False, None)

    db.add_consultation_message(consultation["id"], "patient", "Hello doctor")
    db.add_consultation_message(consultation["id"], "professional", "Hello, how can I help?")
    db.update_consultation_status(consultation["id"], "active")

    # Simulate restart again.
    del db
    db2, _ = make_supabase_database(backing)

    reloaded = db2.get_consultation(consultation["id"])
    assert reloaded["status"] == "active"

    messages = db2.list_consultation_messages(consultation["id"])
    assert [m["content"] for m in messages] == ["Hello doctor", "Hello, how can I help?"]

    identity_consent = db2.get_consent(consultation["id"], "identity_data")
    assert identity_consent["granted"] is False

    db2.update_consent(identity_consent["id"], granted=True, granted_at="2026-01-02T00:00:00")
    reconfirmed = db2.get_consent(consultation["id"], "identity_data")
    assert reconfirmed["granted"] is True


def test_audit_log_written():
    db, client = make_supabase_database()
    db.log_audit("user-1", "patient", "LOGIN", "user", "user-1")
    assert len(client.data["audit_logs"]) == 1
    assert client.data["audit_logs"][0]["action"] == "LOGIN"


def test_database_error_surfaces_on_failure():
    db, client = make_supabase_database()
    client.fail_tables["users"] = True
    try:
        db.create_user(email="fails@example.com", role="patient")
        raise AssertionError("expected DatabaseError to be raised")
    except DatabaseError as exc:
        assert exc.operation == "create_user"
        assert "simulated failure" in str(exc.original)


def _run_all():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    passed, failed = 0, 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {test.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    _run_all()
