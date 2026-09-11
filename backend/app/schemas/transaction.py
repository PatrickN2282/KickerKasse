from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import List, Optional, Literal


class TransactionItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price_cents: int = Field(..., ge=0)
    is_internal_material: bool = False
    note: Optional[str] = Field(default=None, max_length=500)


class SaleGuest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_id: Optional[int] = Field(default=None, gt=0)
    guest_first_name: str = Field(min_length=1, max_length=120)
    guest_last_name: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def normalize(self):
        self.guest_first_name = self.guest_first_name.strip()
        self.guest_last_name = (self.guest_last_name or "").strip() or None
        if not self.guest_first_name:
            raise ValueError("Bitte einen Gastnamen eingeben")
        return self


class TransactionItemCreate(TransactionItemBase):
    model_config = ConfigDict(extra="forbid")
    guests: List[SaleGuest] = Field(default_factory=list)



class TransactionItemResponse(TransactionItemBase):
    product_name: Optional[str] = None
    product_group_name: Optional[str] = None
    category_name: Optional[str] = None
    tax_rate_snapshot: Optional[float] = None
    snapshot_version: Optional[int] = None
    id: int
    total_price_cents: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    payment_method: Literal["CASH", "BALANCE"]  # Payment method enum
    user_id: int


class VoucherRedemptionData(BaseModel):
    voucher_number: str


class TransactionCreate(TransactionBase):
    member_id: Optional[int] = None
    items: List[TransactionItemCreate]
    voucher_redemptions: List[VoucherRedemptionData] = Field(default_factory=list)
    balance_discount_cents: int = Field(default=0, ge=0)
    tip_cents: int = Field(default=0, ge=0)
    cash_received_cents: Optional[int] = Field(default=None, ge=0)
    expected_total_amount_cents: Optional[int] = Field(default=None, ge=0)
    expected_member_balance_cents: Optional[int] = Field(default=None, ge=0)
    # Kept for older clients. Drawer decisions are derived server-side and this
    # value is intentionally not trusted as a hardware instruction.
    trigger_cash_drawer: bool = False


class VoucherRedemptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    voucher_id: int
    voucher_code: str
    amount_cents: int


class TransactionResponse(BaseModel):
    id: int
    receipt_number: Optional[int] = None
    type: str  # "SALE", "STORNO", "RECHARGE"
    payment_method: str
    total_amount_cents: int
    user_id: int
    member_id: Optional[int] = None
    voucher_code: Optional[str] = None
    voucher_type: Optional[str] = None
    voucher_redemptions: List[VoucherRedemptionResponse] = Field(default_factory=list)
    voucher_applied_cents: int = 0
    balance_applied_cents: int = 0
    tip_cents: int = 0
    cash_received_cents: Optional[int] = None
    change_given_cents: Optional[int] = None
    open_small_parts_drawer: bool = False
    drawer_targets: List[Literal["main", "small_parts"]] = Field(default_factory=list)
    items: List[TransactionItemResponse]
    issued_prepaid_voucher_numbers: List[str] = Field(default_factory=list)
    next_unissued_prepaid_voucher_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionStornoCreate(BaseModel):
    transaction_id: int


class ZBonResponse(BaseModel):
    total_cash_cents: int
    total_balance_cents: int
    transaction_count: int
    created_at: datetime
