"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, calendar, reception

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(calendar.router)
api_router.include_router(reception.router)
