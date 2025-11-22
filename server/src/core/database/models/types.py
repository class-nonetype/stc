from __future__ import annotations

import uuid
from sqlalchemy import Integer, String, event
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base

from .user_accounts import UserAccounts





# tipo de solicitud del ticket
class RequestTypes(Base):
    __tablename__ = 'request_types'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


# prioridad del ticket
class PriorityTypes(Base):
    __tablename__ = 'priority_types'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


# estado del ticket
class StatusTypes(Base):
    __tablename__ = 'status_types'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )




@event.listens_for(RequestTypes.__table__, 'after_create')
def seed_default_request_types(target, connection, **kwargs) -> None:
    data = [
        {'description': 'Edición contactos'},
        {'description': 'RDA duplicado'},
        {'description': 'Cambio SISPA'},
        #{'description': 'Error'},
        #{'description': 'Requisito'},
        #{'description': 'Tarea'},
        #{'description': 'Incidente'},
        #{'description': 'Pregunta'},
        #{'description': 'Soporte'},
    ]
    connection.execute(target.insert(), data)



@event.listens_for(PriorityTypes.__table__, 'after_create')
def seed_default_priority_types(target, connection, **kwargs) -> None:
    data = [
        {'description': 'Baja'},
        {'description': 'Media'},
        {'description': 'Alta'},
        {'description': 'Urgente'},
    ]
    connection.execute(target.insert(), data)


@event.listens_for(StatusTypes.__table__, 'after_create')
def seed_default_status_types(target, connection, **kwargs) -> None:
    data = [
        {'description': 'En espera'},
        {'description': 'Abierto'},
        {'description': 'En proceso'},
        {'description': 'Resuelto'},
        {'description': 'Cancelado'},
        #{'description': 'Cerrado'},
    ]
    connection.execute(target.insert(), data)


