from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal


class TransactionItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price_cents: int = Field(..., ge=0)
    is_internal_material: bool = False
    note: Optional[str] = Field(default=None, max_length=500)


class TransactionItemCreate(TransactionItemBase):
    pass


class TransactionItemResponse(TransactionItemBase):
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
    trigger_cash_drawer: bool = True


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
    voucher_applied_cents: int = 0
    balance_applied_cents: int = 0
    tip_cents: int = 0
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
