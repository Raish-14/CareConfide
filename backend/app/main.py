import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai, auth, consultations, doctor, patient, professionals
from app.core.config import get_settings
from app.services.db import DATA_MODE
from app.services.db_errors import DatabaseError

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="CareConfide API",
    description="Privacy-first healthcare intake and consultation platform (hackathon prototype).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """
    Supabase IS configured but a real database call failed. Per project
    requirements this must be surfaced clearly rather than silently
    falling back to in-memory storage, so we return a 503 with the
    actual failure reason instead of a generic 500.
    """
    logging.getLogger("careconfide.db").error("Database error during %s: %s", exc.operation, exc.original)
    return JSONResponse(
        status_code=503,
        content={
            "detail": f"Database operation '{exc.operation}' failed.",
            "error": str(exc.original),
        },
    )


app.include_router(auth.router)
app.include_router(patient.router)
app.include_router(ai.router)
app.include_router(professionals.router)
app.include_router(consultations.router)
app.include_router(doctor.router)


@app.get("/")
def root():
    return {"service": "CareConfide API", "status": "ok"}


@app.get("/api/health")
def health():
    return JSONResponse({
        "status": "ok",
        "supabase_configured": settings.supabase_configured,
        "ai_configured": settings.ai_configured,
        "data_mode": DATA_MODE,
        "ai_mode": "live" if settings.ai_configured else "demo",
    })
