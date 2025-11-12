from __future__ import annotations

from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., validation_alias=AliasChoices("email", "e_mail"))
    is_active: bool | None = Field(default=True)


class UserAccount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=255)


class TeamGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class SignUpRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    UserProfile: UserProfile
    UserAccount: UserAccount
    TeamGroup: TeamGroup
