#!/usr/bin/env python3
"""
End-to-end persistence verification for CareConfide, run against a
LIVE backend (with real Supabase credentials in backend/.env).

This exercises the full requirement-#12 checklist over real HTTP calls
to your running `uvicorn app.main:app` instance:

  1. register a new patient user            -> users, patients, identity_vault
  2. run an AI intake conversation          -> intake_sessions, intake_messages
  3. confirm the intake                     -> clinical_profiles
  4. request a consultation                 -> consultations, consents
  5. send a consultation message            -> consultation_messages
  6. (you restart the backend process)
  7. re-run in `check` mode                 -> confirms everything above
                                                is still readable, i.e. it
                                                really came from Supabase
                                                and not process memory.

No third-party packages required — uses only the Python standard
library, so it runs the same whether or not you've pip-installed the
backend's own dependencies.

USAGE
-----
    # 1. Start the backend in one terminal:
    cd backend && uvicorn app.main:app --reload --port 8000

    # 2. In another terminal, seed data:
    python3 scripts/verify_persistence.py seed

    # 3. Open the Supabase Table Editor and confirm the rows described
    #    in the script's output exist in `users`, `patients`,
    #    `identity_vault`, `intake_sessions`, `intake_messages`,
    #    `clinical_profiles`, `consultations`, `consents`,
    #    `consultation_messages`, and `audit_logs`.

    # 4. Stop the backend (Ctrl+C) and start it again:
    uvicorn app.main:app --reload --port 8000

    # 5. Confirm the data survived the restart:
    python3 scripts/verify_persistence.py check
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"
STATE_FILE = Path(__file__).resolve().parent / "verify_state.json"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach {url} ({exc}). Is `uvicorn app.main:app --port 8000` running?"
        ) from exc


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


FAILURES: list[str] = []


def seed():
    email = f"verify.{int(time.time())}@example.com"
    password = "verify-password-123"

    health = call("GET", "/api/health")
    print(f"Backend health: data_mode={health.get('data_mode')} ai_mode={health.get('ai_mode')}")
    if health.get("data_mode") != "supabase":
        print(
            "WARNING: backend is running in 'in_memory_demo' mode (Supabase env "
            "vars not detected by the backend process). This script will still "
            "run, but it will NOT be testing real Supabase persistence. Set "
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in backend/.env and restart "
            "the backend, then re-run this script."
        )

    print(f"\n1) Registering patient {email} ...")
    auth = call("POST", "/api/auth/register", {
        "email": email, "password": password, "role": "patient",
        "full_name": "Verification Patient",
    })
    token = auth["access_token"]
    user_id = auth["user_id"]
    print(f"   -> user_id={user_id}  (check Supabase 'users' + 'patients' + 'identity_vault' tables)")

    print("\n2) Starting AI intake ...")
    intake = call("POST", "/api/ai/intake", {"description": "I've had a persistent cough for two weeks."}, token=token)
    session_id = intake["session_id"]
    print(f"   -> intake_session_id={session_id} (ai_mode={intake['ai_mode']})")

    turns = 0
    while not intake["structured"]["ready_for_review"] and turns < 5:
        intake = call("POST", "/api/ai/intake/reply", {
            "session_id": session_id, "message": "No other symptoms, no known allergies.",
        }, token=token)
        turns += 1
    print(f"   -> ready_for_review={intake['structured']['ready_for_review']} after {turns} extra turn(s)")
    print("   (check Supabase 'intake_messages' table for this session_id)")

    print("\n3) Confirming intake (creates a clinical profile) ...")
    profile = call("POST", "/api/patient/intake/confirm", {"session_id": session_id}, token=token)
    clinical_profile_id = profile["id"]
    print(f"   -> clinical_profile_id={clinical_profile_id} (check 'clinical_profiles' table)")

    print("\n4) Finding a professional and requesting a consultation ...")
    professionals = call("GET", "/api/professionals", token=token)
    if not professionals:
        raise RuntimeError("No professionals available — check 'professionals' table has seed data.")
    professional_id = professionals[0]["id"]
    consultation = call("POST", "/api/consultations", {
        "professional_id": professional_id, "clinical_profile_id": clinical_profile_id, "mode": "chat",
    }, token=token)
    consultation_id = consultation["id"]
    print(f"   -> consultation_id={consultation_id} (check 'consultations' + 'consents' tables)")

    print("\n5) Sending a consultation message ...")
    message = call("POST", f"/api/consultations/{consultation_id}/messages", {
        "content": "Hello, I wanted to follow up on my intake.",
    }, token=token)
    print(f"   -> message stored at {message['created_at']} (check 'consultation_messages' table)")

    STATE_FILE.write_text(json.dumps({
        "email": email, "password": password, "user_id": user_id,
        "session_id": session_id, "clinical_profile_id": clinical_profile_id,
        "consultation_id": consultation_id, "message_content": message["content"],
    }, indent=2))
    print(f"\nSaved verification state to {STATE_FILE}")
    print("\nNext steps:")
    print("  1. Open the Supabase Table Editor and spot-check the tables named above.")
    print("  2. Stop the backend (Ctrl+C) and start it again: uvicorn app.main:app --port 8000")
    print("  3. Run: python3 scripts/verify_persistence.py check")


def check_persistence():
    if not STATE_FILE.exists():
        print("No verify_state.json found — run `python3 scripts/verify_persistence.py seed` first.")
        sys.exit(1)
    state = json.loads(STATE_FILE.read_text())

    health = call("GET", "/api/health")
    print(f"Backend health after restart: data_mode={health.get('data_mode')}")

    print("\nLogging in with the credentials created before the restart ...")
    auth = call("POST", "/api/auth/login", {"email": state["email"], "password": state["password"]})
    check("Login still succeeds after restart", auth["user_id"] == state["user_id"])
    token = auth["access_token"]

    profile = call("GET", "/api/patient/profile", token=token)
    check("Patient profile still resolvable", bool(profile.get("patient_id")))

    profiles = call("GET", "/api/patient/clinical-profiles", token=token)
    found_profile = next((p for p in profiles if p["id"] == state["clinical_profile_id"]), None)
    check("Confirmed clinical profile survived restart", found_profile is not None)

    consultations = call("GET", "/api/patient/consultations", token=token)
    found_consultation = next((c for c in consultations if c["id"] == state["consultation_id"]), None)
    check("Consultation survived restart", found_consultation is not None)

    messages = call("GET", f"/api/consultations/{state['consultation_id']}/messages", token=token)
    check(
        "Consultation message survived restart",
        any(m["content"] == state["message_content"] for m in messages),
    )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        sys.exit(1)
    print("All persistence checks PASSED — data survived a backend restart.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("seed", "check"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "seed":
        seed()
    else:
        check_persistence()
