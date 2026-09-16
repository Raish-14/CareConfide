from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_role
from app.services.db import db
from app.schemas.schemas import (
    IntakeReplyRequest,
    IntakeResponse,
    IntakeStartRequest,
    IntakeStructuredResult,
)
from app.services.ai_intake import run_intake_turn

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _get_patient(user: dict) -> dict:
    patient = db.get_patient_by_user_id(user["id"])
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return patient


@router.post("/intake", response_model=IntakeResponse)
async def start_intake(payload: IntakeStartRequest, user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _get_patient(user)

    session = db.create_intake_session(patient_id=patient["id"], status="in_progress", ai_mode="live")
    db.add_intake_message(session["id"], sender="patient", content=payload.description)

    conversation = [{"sender": "patient", "content": payload.description}]
    structured, mode = await run_intake_turn(conversation)

    update_fields = {"ai_mode": mode, "concern_category": structured.get("concern_category")}
    if structured.get("ready_for_review"):
        update_fields["status"] = "ready_for_review"
    db.update_intake_session(session["id"], **update_fields)

    db.add_intake_message(
        session["id"],
        sender="ai",
        content=structured.get("follow_up_question") or structured.get("summary", ""),
        structured_json=structured,
    )

    db.log_audit(user["id"], "patient", "START_INTAKE", "intake_session", session["id"])

    return IntakeResponse(session_id=session["id"], ai_mode=mode, structured=IntakeStructuredResult(**structured))


@router.post("/intake/reply", response_model=IntakeResponse)
async def reply_intake(payload: IntakeReplyRequest, user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    patient = _get_patient(user)

    session = db.get_intake_session(payload.session_id)
    if not session or session["patient_id"] != patient["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intake session not found")

    db.add_intake_message(payload.session_id, sender="patient", content=payload.message)

    conversation = [
        {"sender": m["sender"], "content": m["content"]}
        for m in db.list_intake_messages(payload.session_id)
    ]
    structured, mode = await run_intake_turn(conversation)

    update_fields = {
        "ai_mode": mode,
        "concern_category": structured.get("concern_category") or session.get("concern_category"),
    }
    if structured.get("ready_for_review"):
        update_fields["status"] = "ready_for_review"
    db.update_intake_session(payload.session_id, **update_fields)

    db.add_intake_message(
        payload.session_id,
        sender="ai",
        content=structured.get("follow_up_question") or structured.get("summary", ""),
        structured_json=structured,
    )

    return IntakeResponse(session_id=payload.session_id, ai_mode=mode, structured=IntakeStructuredResult(**structured))


@router.get("/intake/{session_id}/messages")
def get_intake_messages(session_id: str, user: dict = Depends(get_current_user)):
    require_role(user, "patient")
    session = db.get_intake_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"messages": db.list_intake_messages(session_id)}
