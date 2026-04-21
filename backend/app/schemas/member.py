from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class MemberBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    membership_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    has_discount: bool = True
    role: Optional[str] = None

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    membership_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    has_discount: Optional[bool] = None
    role: Optional[str] = None
    balance_cents: Optional[int] = None


class MemberResponse(MemberBase):
    id: int
    member_number: int
    name: str
    balance_cents: int
    photo_path: Optional[str] = None  # Path to member photo file
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    pass
