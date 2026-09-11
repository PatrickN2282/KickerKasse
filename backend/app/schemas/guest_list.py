from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, List


class GuestListEntryCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    member_id: Optional[int] = None
    guest_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    guest_first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    guest_last_name: Optional[str] = Field(default=None, max_length=120)
    transaction_id: Optional[int] = None

    @model_validator(mode="after")
    def normalize_guest_names(self):
        guest_name = (self.guest_name or "").strip()
        guest_first_name = (self.guest_first_name or "").strip()
        guest_last_name = (self.guest_last_name or "").strip()

        if not guest_first_name and guest_name:
            parts = guest_name.split(maxsplit=1)
            guest_first_name = parts[0]
            if len(parts) > 1 and not guest_last_name:
                guest_last_name = parts[1]

        if not guest_first_name:
            raise ValueError("guest_first_name is required")

        self.guest_first_name = guest_first_name
        self.guest_last_name = guest_last_name or None
        self.guest_name = f"{guest_first_name} {guest_last_name}".strip()
        return self


class GuestListEntryBatchCreate(BaseModel):
    entries: List[GuestListEntryCreate]


class GuestListEntryResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    member_id: Optional[int] = None
    member_name: Optional[str] = None
    guest_name: str
    guest_first_name: str
    guest_last_name: Optional[str] = None
    transaction_id: Optional[int] = None
    transaction_item_id: Optional[int] = None
    receipt_number: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GuestListByProductResponse(BaseModel):
    product_id: int
    product_name: str
    entries: List[GuestListEntryResponse]


class GuestListPageResponse(BaseModel):
    entries: List[GuestListEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GuestListProductResponse(BaseModel):
    id: int
    name: str


class KnownGuestResponse(BaseModel):
    guest_name: str
    guest_first_name: str
    guest_last_name: Optional[str] = None
    short_display_name: str
