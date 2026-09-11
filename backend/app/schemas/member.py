from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional


from .validation import NormalizedModel, UpdateModel, PersonName, Email, Phone, MembershipNumber, NonNegativeInt, validate_member_name


class MemberBase(NormalizedModel):
    first_name: PersonName
    last_name: PersonName
    membership_number: MembershipNumber = None
    email: Email = None
    phone: Phone = None
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
    @model_validator(mode="after")
    def check_combined_name(self):
        validate_member_name(self.first_name, self.last_name)
        return self

    account_password: Optional[str] = Field(default=None, min_length=8)


class MemberUpdate(UpdateModel):
    non_nullable_fields = {"first_name", "last_name", "has_discount"}

    first_name: Optional[PersonName] = None
    last_name: Optional[PersonName] = None
    membership_number: MembershipNumber = None
    email: Email = None
    phone: Phone = None
    notes: Optional[str] = None
    has_discount: Optional[bool] = None
    role: Optional[str] = None
    account_password: Optional[str] = Field(default=None, min_length=8)

    @model_validator(mode="before")
    @classmethod
    def reject_balance_changes(cls, data):
        # Reject explicitly rather than silently ignoring the former update field.
        # Presence matters: null, unchanged values and mixed updates are forbidden too.
        if isinstance(data, dict) and "balance_cents" in data:
            raise ValueError("Guthaben bitte über Aufladung oder Guthabenkorrektur ändern")
        return data


class MemberBalanceCorrectionRequest(BaseModel):
    new_balance_cents: NonNegativeInt
    reason: Optional[str] = Field(default=None, max_length=255)


class MemberSelectionResponse(BaseModel):
    """Only the fields needed to select and charge a member at checkout."""
    id: int
    member_number: int
    membership_number: MembershipNumber = None
    name: str
    first_name: str
    last_name: str
    photo_path: Optional[str] = None
    has_discount: bool
    balance_cents: int

    class Config:
        from_attributes = True


class MemberResponse(MemberBase):
    id: int
    member_number: int
    name: str
    last_name: str = Field(default="", max_length=80)
    balance_cents: int
    photo_path: Optional[str] = None  # Path to member photo file
    account_username: Optional[str] = None
    has_user_account: bool = False
    archived_at: datetime | None = None
    user_account_active: bool = False
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
                    "archived_at",
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
                    "account_username",
                    "has_user_account",
                    "user_account_active",
                    "drawer_targets",
                    "linked_user",
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

        linked_user = data.pop("linked_user", None)
        if linked_user is not None:
            data["account_username"] = getattr(linked_user, "username", None)
            data["has_user_account"] = True
            data["user_account_active"] = bool(getattr(linked_user, "is_active", False))
        else:
            data["has_user_account"] = bool(data.get("has_user_account", False))
            data["user_account_active"] = bool(data.get("user_account_active", False))

        return data

    class Config:
        from_attributes = True


class MemberDetailResponse(MemberResponse):
    pass


class MemberRechargeResponse(MemberResponse):
    drawer_targets: list[str] = Field(default_factory=list)


class MemberBalanceCorrectionLogResponse(BaseModel):
    id: int
    member_id: int
    member_name: str
    old_balance_cents: int
    new_balance_cents: int
    change_cents: int
    executed_by_username: str
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True
