"""InteractionLog ORM model — individual turns within a conversation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base
from app.models.enums import InteractionRole
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class InteractionLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interaction_logs"
    __table_args__ = (
        Index("ix_interaction_logs_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[InteractionRole] = mapped_column(
        Enum(
            InteractionRole,
            name="interaction_role",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    conversation: Mapped[Conversation] = relationship(back_populates="interaction_logs")

    def __repr__(self) -> str:
        return f"<InteractionLog id={self.id} role={self.role}>"
