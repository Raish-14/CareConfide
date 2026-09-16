from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.services.db import db
from app.services.db_errors import DatabaseError
from app.schemas.schemas import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Demo password store. Passwords are intentionally NOT written to the
# `users` table (database/schema.sql notes "Do not store passwords
# manually. Use Supabase Auth."), so real password verification is out
# of scope for this prototype's persistence layer. This in-memory map is
# a process-local convenience matching the original demo behavior; it is
# documented as a known limitation in the README (passwords for
# accounts created before a backend restart are not re-checked after
# that restart, same as before this change).
_passwords: dict[str, str] = {}


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    if db.get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    try:
        user = db.create_user(email=payload.email, role=payload.role)
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001 - unique-constraint race, etc.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from exc

    _passwords[payload.email] = payload.password

    if payload.role == "patient":
        display_id = f"Patient #{user['id'][:5].upper()}"
        patient = db.create_patient(user_id=user["id"], display_id=display_id, preferred_language="en")
        db.create_identity_vault(
            user_id=user["id"],
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            phone=None,
            identity_verified=False,
            verification_method=None,
        )
        display_name = patient["display_id"]
    else:
        professional = db.create_professional(
            user_id=user["id"],
            full_name=payload.full_name,
            specialty=payload.specialty or "General & Sensitive Health",
            languages=["English"],
            consultation_modes=["chat"],
            bio=None,
            is_demo=False,
        )
        display_name = professional["full_name"]

    db.log_audit(user["id"], payload.role, "REGISTER", "user", user["id"])

    # Demo token == user_id. See app/core/security.py for why.
    return AuthResponse(access_token=user["id"], role=payload.role, user_id=user["id"], display_name=display_name)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user = db.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Pre-seeded demo accounts have no password on file — accept any
    # password for them so judges can explore quickly. Accounts created
    # via /register during this process's lifetime must match their
    # real password.
    if payload.email in _passwords and _passwords[payload.email] != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    display_name = user["email"]
    if user["role"] == "patient":
        patient = db.get_patient_by_user_id(user["id"])
        display_name = patient["display_id"] if patient else display_name
    elif user["role"] == "professional":
        professional = db.get_professional_by_user_id(user["id"])
        display_name = professional["full_name"] if professional else display_name

    db.log_audit(user["id"], user["role"], "LOGIN", "user", user["id"])

    return AuthResponse(access_token=user["id"], role=user["role"], user_id=user["id"], display_name=display_name)


@router.get("/demo-accounts")
def demo_accounts():
    """Helper endpoint so the frontend can offer one-click demo logins."""
    accounts = []
    patient = db.get_any_patient()
    if patient:
        user = db.get_user_by_id(patient["user_id"])
        if user:
            accounts.append({"role": "patient", "email": user["email"], "label": patient["display_id"]})
    for professional in db.list_professionals():
        user = db.get_user_by_id(professional["user_id"])
        if user:
            accounts.append({"role": "professional", "email": user["email"], "label": professional["full_name"]})
    return {"accounts": accounts, "note": "Any password works for pre-seeded demo accounts."}
