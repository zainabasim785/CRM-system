# =============================================================================
# AI Reception Agent — FastAPI Backend
# =============================================================================
import os
import uuid
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Graceful imports — missing optional deps don't break the server
# ---------------------------------------------------------------------------
try:
    import sqlalchemy  # noqa: F401
    HAS_DB = bool(os.getenv("DATABASE_URL"))
except ImportError:
    HAS_DB = False

try:
    import google.auth  # noqa: F401
    HAS_CALENDAR = bool(os.getenv("GOOGLE_CALENDAR_CREDENTIALS"))
except ImportError:
    HAS_CALENDAR = False

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Reception Agent API", version="1.0.0")

# Read allowed origins from env, fall back to local dev + production frontend
origins_str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://crm-system-ivory.vercel.app",
)
origins = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class TriageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class TriageResponse(BaseModel):
    intent: str
    reply: str
    requires_escalation: bool
    conversation_id: str


class BookingRequest(BaseModel):
    date: str
    time: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    confirmed: bool
    appointment_id: Optional[str] = None
    message: str


class AvailabilityResponse(BaseModel):
    slots: list[dict]


class FollowUpRequest(BaseModel):
    conversation_id: str
    message: str


class FollowUpResponse(BaseModel):
    reply: str
    requires_escalation: bool


# ---------------------------------------------------------------------------
# In-memory store (swap for DB + CrewAI in production)
# ---------------------------------------------------------------------------
conversations: dict[str, list[dict]] = {}
appointments: list[dict] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "service": "AI Reception Agent"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "in-memory" if not HAS_DB else "postgresql",
        "calendar": "disabled" if not HAS_CALENDAR else "enabled",
    }


@app.post("/api/triage", response_model=TriageResponse)
def triage(req: TriageRequest):
    """Classify visitor intent and return a reply."""
    conv_id = req.conversation_id or str(uuid.uuid4())

    # Simple keyword-based triage (replace with CrewAI agent call)
    text = req.message.lower()
    if any(w in text for w in ["hour", "open", "close"]):
        intent = "hours"
        reply = "We're open Monday to Saturday, 9 AM to 7 PM. Would you like me to check availability?"
        escalate = False
    elif any(w in text for w in ["book", "appointment", "schedule"]):
        intent = "booking"
        reply = "I can check availability now. What day works best for you?"
        escalate = False
    elif any(w in text for w in ["available", "availability", "free", "slot"]):
        intent = "availability"
        reply = "Tuesday and Thursday afternoons are open this week. Shall I hold a slot for you?"
        escalate = False
    elif any(w in text for w in ["refund", "complaint", "legal", "emergency", "urgent"]):
        intent = "escalate"
        reply = "This needs a closer look from our team. Connecting you to a human now."
        escalate = True
    else:
        intent = "general"
        reply = "Got it. Could you tell me a little more, or would you like me to connect you with someone?"
        escalate = False

    # Store conversation
    if conv_id not in conversations:
        conversations[conv_id] = []
    conversations[conv_id].append({"role": "visitor", "text": req.message})
    conversations[conv_id].append({"role": "agent", "text": reply})

    return TriageResponse(
        intent=intent,
        reply=reply,
        requires_escalation=escalate,
        conversation_id=conv_id,
    )


@app.post("/api/booking", response_model=BookingResponse)
def book(req: BookingRequest):
    """Book an appointment (mock — replace with Google Calendar + CrewAI)."""
    appt_id = str(uuid.uuid4())[:8]
    appointments.append(
        {
            "id": appt_id,
            "date": req.date,
            "time": req.time or "10:00",
            "name": req.name,
            "email": req.email,
            "phone": req.phone,
            "notes": req.notes,
        }
    )
    return BookingResponse(
        confirmed=True,
        appointment_id=appt_id,
        message=f"Appointment confirmed for {req.name} on {req.date} at {req.time or '10:00'}.",
    )


@app.get("/api/availability", response_model=AvailabilityResponse)
def get_availability(date_str: Optional[str] = None):
    """Return available time slots (mock)."""
    target = date_str or date.today().isoformat()
    slots = [
        {"date": target, "time": "09:00", "available": True},
        {"date": target, "time": "10:00", "available": True},
        {"date": target, "time": "11:00", "available": False},
        {"date": target, "time": "14:00", "available": True},
        {"date": target, "time": "15:00", "available": True},
        {"date": target, "time": "16:00", "available": False},
    ]
    return AvailabilityResponse(slots=slots)


@app.post("/api/follow-up", response_model=FollowUpResponse)
def follow_up(req: FollowUpRequest):
    """Continue an existing conversation."""
    if req.conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversations[req.conversation_id].append({"role": "visitor", "text": req.message})

    # Simple mock reply
    text = req.message.lower()
    if "yes" in text or "sure" in text:
        reply = "Great! Let me get that set up for you."
        escalate = False
    elif "no" in text:
        reply = "No problem. Is there anything else I can help with?"
        escalate = False
    else:
        reply = "Thanks for the additional info. Let me check on that."
        escalate = False

    conversations[req.conversation_id].append({"role": "agent", "text": reply})

    return FollowUpResponse(reply=reply, requires_escalation=escalate)