from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from bcrypt import checkpw
from sqlalchemy import DateTime, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .user_profiles import UserProfiles
    from .teams import Teams


class UserAccounts(Base):
    __tablename__ = "user_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    #user_role_id: Mapped[uuid.UUID] = mapped_column(
    #    UUID(as_uuid=True),
    #    ForeignKey("user_roles.id", ondelete="RESTRICT"),
    #    nullable=False,
    #    index=True,
    #)

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    last_login_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user_profile_relationship: Mapped["UserProfiles"] = relationship(
        back_populates="user_account_relationship",
        uselist=False,
    )
    team_relationship: Mapped["Teams"] = relationship(
        back_populates="user_account_relationship",
        uselist=False,
    )

    @hybrid_property
    def active(self) -> bool:
        if self.user_profile_relationship is None:
            return False
        return bool(self.user_profile_relationship.is_active)

    @active.expression
    def active(cls):  # type: ignore[override]
        from .user_profiles import UserProfiles

        return (
            select(UserProfiles.is_active)
            .where(UserProfiles.id == cls.user_profile_id)
            .scalar_subquery()
        )

    def verify_password(self, raw_password: str) -> bool:
        if not raw_password:
            return False
        try:
            return checkpw(raw_password.encode("utf-8"), self.password.encode("utf-8"))
        except Exception:  # pylint: disable=broad-except
            return False

    def __repr__(self) -> str:
        return f"UserAccount(id={self.id!s}, username={self.username!r})"

