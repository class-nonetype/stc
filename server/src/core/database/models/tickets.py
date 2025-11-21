from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, String, Text, Integer, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database.base import Base
from src.core.database.models import *


class Tickets(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    #title: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)

    request_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("request_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    priority_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("priority_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    status_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("status_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )


    # Relaciones principales
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    
    # encargado
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ## Ámbito organizacional (opcionales)
    #organization_id: Mapped[uuid.UUID | None] = mapped_column(
    #    UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"),
    #    nullable=True, index=True
    #)
    #project_id: Mapped[uuid.UUID | None] = mapped_column(
    #    UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
    #    nullable=True, index=True
    #)
    #category_id: Mapped[uuid.UUID | None] = mapped_column(
    #    UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"),
    #    nullable=True, index=True
    #)

    # Fechas ciclo de vida
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Extensibilidad y métricas

    #attachments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    #comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    #watchers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Auditoría y control
    #source: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 'web' | 'email' | 'api'
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_resolved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_readed: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False, server_default="false")

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    request_type_relationship: Mapped["RequestTypes"] = relationship(
        "RequestTypes",
        foreign_keys=[request_type_id],
    )

    priority_relationship: Mapped["PriorityTypes"] = relationship(
        "PriorityTypes",
        foreign_keys=[priority_type_id],
    )

    status_relationship: Mapped["StatusTypes"] = relationship(
        "StatusTypes",
        foreign_keys=[status_type_id],
    )

    requester_relationship: Mapped["UserAccounts"] = relationship(
        "UserAccounts",
        foreign_keys=[requester_id],
    )

    team_relationship: Mapped["Teams"] = relationship(
        "Teams",
        foreign_keys=[team_id],
    )

    attachments_relationship: Mapped[list["TicketAttachments"]] = relationship(
        "TicketAttachments",
        back_populates="ticket_relationship",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    #def __repr__(self) -> str:
    #    return f"Tickets(id={self.id!s}, code={getattr(self, 'code', None)!r}, status={self.status!r})"
