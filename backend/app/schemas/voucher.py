from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
from typing import Optional, Literal


class VoucherCreateGift(BaseModel):
    """Create a gift voucher"""
    value_cents: int = Field(..., ge=1, description="Value in cents")
    reason: Literal["COURTESY", "PROMOTIONAL", "STAFF_BENEFIT", "OTHER"] = "COURTESY"


class VoucherCreatePrepaid(BaseModel):
    """Create a prepaid voucher"""
    value_cents: int = Field(..., ge=1, description="Value in cents")
    reason: Literal["COURTESY", "PROMOTIONAL", "STAFF_BENEFIT", "OTHER"] = "COURTESY"


class VoucherValidateRequest(BaseModel):
    """Validate a voucher before redemption"""
    voucher_number: str = Field(..., description="Voucher number (e.g., V-001)")


class VoucherRedeemRequest(BaseModel):
    """Redeem a voucher"""
    voucher_number: str = Field(..., description="Voucher number (e.g., V-001)")
    member_id: Optional[int] = None


class VoucherValidationResponse(BaseModel):
    """Response for voucher validation"""
    valid: bool
    voucher_number: str
    voucher_type: str
    value_cents: int
    status: str
    message: str = ""
    reason: Optional[str] = None


class VoucherResponse(BaseModel):
    """Voucher response model"""
    id: int
    voucher_code: str  # Format: V-2026-001
    voucher_type: str  # GIFT or PREPAID
    value_cents: int
    status: str  # CREATED or REDEEMED
    reason: Optional[str] = None  # For GIFT vouchers
    created_by_user_id: int
    created_at: datetime
    redeemed_by_user_id: Optional[int] = None
    redeemed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    """List of vouchers with pagination"""
    vouchers: list[VoucherResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VoucherRedeemResponse(BaseModel):
    """Response after redeeming a voucher"""
    success: bool
    voucher_number: str
    voucher_type: str
    value_cents: int
    transaction_id: int
    message: str
