from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
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
    voucher_code: Optional[str] = None  # Can be None if DB column missing, frontend generates fallback
    voucher_type: str  # GIFT or PREPAID
    value_cents: int
    status: str  # CREATED or REDEEMED
    reason: Optional[str] = None  # For GIFT vouchers
    created_by_user_id: int
    created_at: datetime
    redeemed_by_user_id: Optional[int] = None
    redeemed_at: Optional[datetime] = None

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
    
    @field_validator('voucher_code', mode='before')
    @classmethod
    def fallback_voucher_code(cls, v, info):
        """Fallback: generate voucher_code from ID if not in DB"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"[Validator] voucher_code value: {v}, type: {type(v)}")
        logger.debug(f"[Validator] info.data: {info.data if hasattr(info, 'data') else 'NO DATA'}")
        
        # If already set, use it
        if v is not None and str(v).strip():
            logger.debug(f"[Validator] Using provided voucher_code: {v}")
            return v
        
        # Fallback: generate from ID if available
        if hasattr(info, 'data') and isinstance(info.data, dict):
            id_val = info.data.get('id')
            if id_val:
                code = f"V-2026-{str(id_val).zfill(3)}"
                logger.debug(f"[Validator] Generated code from ID {id_val}: {code}")
                return code
            else:
                logger.debug(f"[Validator] No ID in data: {info.data.keys() if info.data else 'empty'}")
        
        # Last resort: return None and let frontend handle it
        logger.debug(f"[Validator] Returning None (frontend fallback)")
        return None


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
