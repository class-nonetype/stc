from __future__ import annotations

import uuid
from sqlalchemy import Integer, String, event
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base

from .user_accounts import UserAccounts





# tipo de solicitud del ticket
class RequestTypes(Base):
    __tablename__ = "request_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    value: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


# prioridad del ticket
class PriorityTypes(Base):
    __tablename__ = "priority_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    value: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


# estado del ticket
class StatusTypes(Base):
    __tablename__ = "status_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    value: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )




@event.listens_for(RequestTypes.__table__, "after_create")
def seed_default_request_types(target, connection, **kwargs) -> None:
    data = [
        {"value": 1, "description": "Edición contactos"},
        {"value": 2, "description": "RDA duplicado"},
        {"value": 3, "description": "Cambio SISPA"},
        #{"value": 1, "description": "Error"},
        #{"value": 2, "description": "Requisito"},
        #{"value": 3, "description": "Tarea"},
        #{"value": 4, "description": "Incidente"},
        #{"value": 5, "description": "Pregunta"},
        #{"value": 6, "description": "Soporte"},
    ]
    connection.execute(target.insert(), data)



@event.listens_for(PriorityTypes.__table__, "after_create")
def seed_default_priority_types(target, connection, **kwargs) -> None:
    data = [
        {"value": 1, "description": "Bajo"},
        {"value": 2, "description": "Medio"},
        {"value": 3, "description": "Alto"},
        {"value": 4, "description": "Urgente"},
    ]
    connection.execute(target.insert(), data)


@event.listens_for(StatusTypes.__table__, "after_create")
def seed_default_status_types(target, connection, **kwargs) -> None:
    data = [
        {"value": 1, "description": "En espera"},
        {"value": 2, "description": "Abierto"},
        {"value": 3, "description": "En proceso"},
        {"value": 4, "description": "Resuelto"},
        #{"value": 5, "description": "Cerrado"},
        {"value": 5, "description": "Cancelado"},
    ]
    connection.execute(target.insert(), data)


