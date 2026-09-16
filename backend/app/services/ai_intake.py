"""
AI-assisted intake service.

- Live mode: calls the Anthropic Messages API using AI_API_KEY, asking
  the model to behave strictly as an intake assistant (never a
  diagnosing doctor) and to return structured JSON.
- Demo mode: a deterministic, rule-based mock that never calls out to
  the network. Used automatically whenever AI_API_KEY is not set, or if
  the live call fails for any reason, so the demo never crashes.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings

SYSTEM_PROMPT = """You are the CareConfide AI Intake Assistant.

You help a patient describe a sensitive health concern before they see a
human healthcare professional. You are NOT a doctor.

Rules you must always follow:
- Never diagnose a condition.
- Never suggest or name medications/prescriptions.
- Never claim certainty about what the patient has.
- Always make clear a licensed professional must be involved for actual care.
- Ask at most one clear, relevant follow-up question at a time.
- Be warm, non-judgmental, and brief.

Respond with ONLY a JSON object (no markdown fences, no prose outside the
JSON) matching exactly this shape:
{
  "concern_category": string,
  "symptoms": string[],
  "duration": string,
  "medical_history": string[],
  "medications": string[],
  "allergies": string[],
  "follow_up_question": string,
  "summary": string,
  "ready_for_review": boolean
}

Set "ready_for_review" to true only once you have enough information
(concern category, symptoms, duration, and any relevant history) to
produce a useful summary for a professional. When ready_for_review is
true, "follow_up_question" should be an empty string.
"""

CATEGORY_KEYWORDS = {
    "Sexual & Reproductive Health": ["std", "sti", "pregnan", "period", "menstru", "discharge", "contracept", "sexual"],
    "Mental Health & Counseling": ["anxious", "anxiety", "depress", "stress", "panic", "sad", "mental", "sleep"],
    "Skin & Dermatology": ["rash", "skin", "acne", "itch", "mole"],
    "General & Sensitive Health": [],
}


def _guess_category(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return category
    return "General & Sensitive Health"


def _mock_turn(conversation: list[dict[str, str]]) -> dict[str, Any]:
    """Deterministic fallback used when live AI is unavailable."""
    patient_turns = [m["content"] for m in conversation if m["sender"] == "patient"]
    combined = " ".join(patient_turns)
    category = _guess_category(combined)
    turn_count = len(patient_turns)

    if turn_count == 1:
        return {
            "concern_category": category,
            "symptoms": [],
            "duration": "",
            "medical_history": [],
            "medications": [],
            "allergies": [],
            "follow_up_question": "Thanks for sharing that. How long have you been experiencing this, and has it happened before?",
            "summary": "",
            "ready_for_review": False,
        }
    if turn_count == 2:
        return {
            "concern_category": category,
            "symptoms": [combined.split(".")[0][:80]],
            "duration": "Recent (as described)",
            "medical_history": [],
            "medications": [],
            "allergies": [],
            "follow_up_question": "Are you currently taking any medications, and do you have any known allergies?",
            "summary": "",
            "ready_for_review": False,
        }

    return {
        "concern_category": category,
        "symptoms": [combined.split(".")[0][:80]] if combined else [],
        "duration": "Recent (as described)",
        "medical_history": ["No additional history reported"],
        "medications": ["None reported"],
        "allergies": ["None reported"],
        "follow_up_question": "",
        "summary": (
            f"Patient describes a concern in the '{category}' category. "
            "Details were gathered through AI-assisted intake and confirmed "
            "by the patient. This is not a diagnosis; a licensed professional "
            "should review before any care decision."
        ),
        "ready_for_review": True,
    }


def _extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in AI response")
    return json.loads(match.group(0))


async def run_intake_turn(conversation: list[dict[str, str]]) -> tuple[dict[str, Any], str]:
    """
    conversation: list of {"sender": "patient"|"ai", "content": str}, in order.
    Returns (structured_dict, mode) where mode is "live" or "demo".
    """
    settings = get_settings()

    if not settings.ai_configured:
        return _mock_turn(conversation), "demo"

    try:
        messages = [
            {"role": "user" if m["sender"] == "patient" else "assistant", "content": m["content"]}
            for m in conversation
        ]
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ai_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.ai_model,
                    "max_tokens": 800,
                    "system": SYSTEM_PROMPT,
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            structured = _extract_json("\n".join(text_blocks))
            return structured, "live"
    except Exception:
        # Never let an AI outage break the demo.
        return _mock_turn(conversation), "demo"
