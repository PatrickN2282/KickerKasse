from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, Literal


class VoucherCreateGift(BaseModel):
    """Create a gift voucher"""
    value_cents: int = Field(..., ge=1, description="Value in cents")
    reason: Literal["DYP_SIEGER", "PROMOTION"] = "PROMOTION"
    auth_password: str = Field(..., min_length=1)


class VoucherCreatePrepaid(BaseModel):
    """Create a prepaid voucher"""
    value_cents: int = Field(..., ge=1, description="Value in cents")
    auth_password: str = Field(..., min_length=1)


class VoucherValidateRequest(BaseModel):
    """Validate a voucher before redemption"""
    voucher_number: str = Field(..., description="Voucher number (e.g., V-001)")
    cart_total_cents: Optional[int] = Field(None, ge=0, description="Current cart total in cents")


class VoucherRedeemRequest(BaseModel):
    """Redeem a voucher"""
    voucher_number: str = Field(..., description="Voucher number (e.g., V-001)")
    member_id: Optional[int] = None
    cart_total_cents: Optional[int] = Field(None, ge=0)


class VoucherValidationResponse(BaseModel):
    """Response for voucher validation"""
    valid: bool
    voucher_number: str
    voucher_type: str
    value_cents: int
    status: str
    message: str = ""
    reason: Optional[str] = None
    applicable_amount_cents: int = 0
    remaining_value_cents: int = 0
    covers_cart_total: bool = False


class VoucherResponse(BaseModel):
    """Voucher response model"""
    id: int
    voucher_number: int
    voucher_code: Optional[str] = None
    voucher_type: str  # GIFT or PREPAID
    value_cents: int
    original_value_cents: int
    remaining_value_cents: int
    status: str  # CREATED or REDEEMED
    reason: Optional[str] = None  # For GIFT vouchers
    description: Optional[str] = None
    created_by_user_id: int
    created_by_username: Optional[str] = None
    created_at: datetime
    redeemed_by_user_id: Optional[int] = None
    redeemed_at: Optional[datetime] = None
    redeemed_amount_cents: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('voucher_type', 'status', 'reason', mode='before')
    @classmethod
    def convert_enums(cls, v):
        """Convert enum values to their string representation"""
        if v is None:
            return None
        if hasattr(v, 'value'):  # It's an Enum
            return v.value
        return str(v)
    
    @model_validator(mode='after')
    def ensure_voucher_code(self):
        """Generate voucher_code fallback for legacy rows if missing"""
        if self.voucher_code is not None and str(self.voucher_code).strip():
            return self

        year = self.created_at.year if self.created_at else datetime.now().year
        self.voucher_code = f"V-{year}-{str(self.voucher_number).zfill(3)}"
        return self


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
    applied_amount_cents: int = 0


class VoucherUpdateRequest(BaseModel):
    """Editable voucher fields for admin"""
    value_cents: int = Field(..., ge=1, description="Value in cents")
    reason: Optional[Literal["DYP_SIEGER", "PROMOTION"]] = None
    description: Optional[str] = Field(None, max_length=255)
