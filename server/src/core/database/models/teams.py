from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, String, Text, Integer, DateTime, ForeignKey, Index, event
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database.base import Base
from src.core.database.models.user_accounts import UserAccounts
# from src.core.database.models.team import Teams  # o Groups, según tu modelo


class Teams(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user_account_relationship: Mapped["UserAccounts"] = relationship(
        back_populates="team_relationship",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"Tickets(id={self.id!s}, code={getattr(self, 'code', None)!r}, status={self.status!r})"



@event.listens_for(Teams.__table__, "after_create")
def seed_default_status_types(target, connection, **kwargs) -> None:
    data = [
        {"id": uuid.uuid4(), "description": "Soporte"},
        {"id": uuid.uuid4(), "description": "Asesoría"},
    ]
    connection.execute(target.insert(), data)
