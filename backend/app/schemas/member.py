from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class MemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    balance_cents: Optional[int] = None


class MemberResponse(MemberBase):
    id: int
    member_number: int
    balance_cents: int
    photo_path: Optional[str] = None  # Path to member photo file
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    pass
