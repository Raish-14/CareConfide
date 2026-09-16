"""
Sanity tests for the in-memory demo fallback (app/services/memory_db.py),
to confirm the existing demo experience still works after the refactor:
seeded professionals/patient are present, and basic CRUD round-trips.

Run directly with: python3 tests/test_memory_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.memory_db import MemoryDatabase  # noqa: E402


def test_seed_data_present():
    db = MemoryDatabase()
    professionals = db.list_professionals()
    assert len(professionals) == 3
    patient = db.get_any_patient()
    assert patient is not None
    assert patient["display_id"] == "Patient #A19F2"


def test_register_style_flow():
    db = MemoryDatabase()
    user = db.create_user(email="new.patient@example.com", role="patient")
    patient = db.create_patient(user_id=user["id"], display_id="Patient #NEW01")
    db.create_identity_vault(user["id"], "New Patient", None, None, False, None)

    assert db.get_user_by_email("new.patient@example.com")["id"] == user["id"]
    assert db.get_patient_by_user_id(user["id"])["id"] == patient["id"]


def test_intake_and_confirm_flow():
    db = MemoryDatabase()
    user = db.create_user(email="flow@example.com", role="patient")
    patient = db.create_patient(user["id"], "Patient #FLOW1")

    session = db.create_intake_session(patient["id"], ai_mode="demo")
    db.add_intake_message(session["id"], "patient", "I have a headache.")
    structured = {"concern_category": "General", "symptoms": ["headache"], "ready_for_review": True}
    db.add_intake_message(session["id"], "ai", "Got it.", structured_json=structured)

    last = db.get_last_structured_intake(session["id"])
    assert last["concern_category"] == "General"

    profile = db.create_clinical_profile(
        session["id"], patient["id"], "General", ["headache"], "1 day", [], [], [],
        None, "summary", True,
    )
    assert db.get_clinical_profile(profile["id"])["ai_summary"] == "summary"


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
