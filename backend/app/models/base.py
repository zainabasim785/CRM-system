"""
Declarative base for all ORM models.

Alembic imports `Base.metadata` to autogenerate migrations.
Concrete models (User, Appointment, Lead, etc.) will inherit from Base later.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata registry for SQLAlchemy 2.0 models."""

    pass
