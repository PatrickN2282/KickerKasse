"""Shared input boundaries for forms, APIs and data imports."""
from typing import Annotated, ClassVar

from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

MAX_INT = 2_147_483_647
NonNegativeInt = Annotated[int, Field(ge=0, le=MAX_INT)]
DatabaseInt = Annotated[int, Field(ge=-MAX_INT - 1, le=MAX_INT)]
Name = Annotated[str, Field(min_length=1, max_length=120)]
PersonName = Annotated[str, Field(min_length=1, max_length=80)]


def optional_text(value):
    return value.strip() or None if isinstance(value, str) else value


Description = Annotated[Annotated[str, Field(max_length=255)] | None, BeforeValidator(optional_text)]
Email = Annotated[Annotated[str, Field(max_length=120)] | None, BeforeValidator(optional_text)]
Phone = Annotated[Annotated[str, Field(max_length=20)] | None, BeforeValidator(optional_text)]
MembershipNumber = Annotated[Annotated[str, Field(max_length=50)] | None, BeforeValidator(optional_text)]


class NormalizedModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_text(cls, value, info):
        if isinstance(value, str) and info.field_name != "account_password":
            return value.strip()
        return value


class UpdateModel(NormalizedModel):
    non_nullable_fields: ClassVar[set[str]] = set()

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_null(cls, data):
        if isinstance(data, dict):
            for key in cls.non_nullable_fields:
                if key in data and data[key] is None:
                    raise ValueError(f"'{key}' darf nicht null sein")
        return data


def validate_member_name(first_name, last_name):
    if len(" ".join(part.strip() for part in (first_name, last_name) if part and part.strip())) > 120:
        raise ValueError("Vor- und Nachname dürfen zusammen höchstens 120 Zeichen enthalten")
