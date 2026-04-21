from pydantic import BaseModel, Field, field_validator, model_validator
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
    last_name: str = Field(default="", max_length=80)
    balance_cents: int
    photo_path: Optional[str] = None  # Path to member photo file
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_legacy_name_fields(cls, data):
        if not data:
            return data

        if not isinstance(data, dict):
            data = {
                field: getattr(data, field, None)
                for field in [
                    "id",
                    "member_number",
                    "name",
                    "first_name",
                    "last_name",
                    "membership_number",
                    "email",
                    "phone",
                    "notes",
                    "has_discount",
                    "role",
                    "balance_cents",
                    "photo_path",
                    "created_at",
                    "updated_at",
                ]
            }

        name = (data.get("name") or "").strip()
        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()

        if not first_name:
            parts = name.split(maxsplit=1)
            member_number = data.get("member_number")
            first_name = parts[0] if parts else (f"Mitglied {member_number}" if member_number else "Unbekannt")
            data["first_name"] = first_name

        if not last_name and name:
            parts = name.split(maxsplit=1)
            data["last_name"] = parts[1] if len(parts) > 1 else ""

        role = data.get("role")
        if hasattr(role, "value"):
            data["role"] = role.value

        return data

    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    pass
