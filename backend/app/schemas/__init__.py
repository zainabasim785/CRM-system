"""Pydantic request / response schemas (API contracts)."""

from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    BookingResult,
    ConversationMessage,
    FollowUpResult,
    IntentType,
    TriageResult,
)
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.schemas.auth import LoginRequest, RegisterResponse, TokenResponse
from app.schemas.conversation import ConversationCreate, ConversationRead, ConversationUpdate
from app.schemas.interaction_log import InteractionLogCreate, InteractionLogRead
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "AgentRequest",
    "AgentResponse",
    "AppointmentCreate",
    "AppointmentRead",
    "AppointmentUpdate",
    "BookingResult",
    "ConversationCreate",
    "ConversationMessage",
    "ConversationRead",
    "ConversationUpdate",
    "FollowUpResult",
    "IntentType",
    "InteractionLogCreate",
    "InteractionLogRead",
    "LoginRequest",
    "RegisterResponse",
    "ReminderCreate",
    "ReminderRead",
    "ReminderUpdate",
    "TokenResponse",
    "TriageResult",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
