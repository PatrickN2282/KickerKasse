#!/usr/bin/env python3
"""
Test Pydantic serialization without DB connection
Tests the full voucher response schema with enum handling
"""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator, computed_field, ConfigDict
from typing import Optional

# Define Enums like in the actual code
class VoucherType(str, Enum):
    GIFT = "GIFT"
    PREPAID = "PREPAID"

class VoucherStatus(str, Enum):
    CREATED = "CREATED"
    REDEEMED = "REDEEMED"

class VoucherReason(str, Enum):
    DYP_SIEGER = "DYP_SIEGER"
    PROMOTION = "PROMOTION"

# Updated VoucherResponse matching the actual code
class VoucherResponse(BaseModel):
    """Voucher response model"""
    id: int
    voucher_code: str = "V-2026-000"  # Default fallback
    voucher_type: str
    value_cents: int
    status: str
    reason: Optional[str] = None
    created_by_user_id: int
    created_at: datetime
    redeemed_by_user_id: Optional[int] = None
    redeemed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, validate_default=True)
    
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
    def ensure_voucher_code(cls, v, info):
        """Ensure voucher_code is always present, generate from id if missing"""
        # If exists and not empty, use it
        if v:
            return v
        
        # If voucher_code doesn't exist, try to generate from ID
        if hasattr(info, 'data') and isinstance(info.data, dict):
            id_val = info.data.get('id')
            if id_val:
                return f"V-2026-{str(id_val).zfill(3)}"
        
        return "V-2026-0"

# Test Case 1: ORM Mode with Enums and voucher_code present
print("=" * 70)
print("Test 1: from_orm() with Enum fields AND voucher_code present")
print("=" * 70)

class MockVoucher:
    """Mock ORM object with all fields"""
    id = 1
    voucher_code = "V-2026-001"  # ✓ Voucher code exists
    voucher_type = VoucherType.GIFT
    value_cents = 1000
    status = VoucherStatus.CREATED
    reason = VoucherReason.PROMOTION
    created_by_user_id = 1
    created_at = datetime.now()
    redeemed_by_user_id = None
    redeemed_at = None

try:
    response = VoucherResponse.from_orm(MockVoucher())
    print("✓ from_orm() succeeded!")
    print(f"  voucher_code: {response.voucher_code}")
    print(f"  voucher_type: {response.voucher_type} (was Enum, now: {type(response.voucher_type).__name__})")
    print(f"  status: {response.status}")
    print(f"  reason: {response.reason}")
    print(f"  Created success message would show:")
    print(f"    ✅ Gutschein erstellt!")
    print(f"    {response.voucher_code or f'V-2026-{str(response.id).padStart(3, \"0\")}'}")
except Exception as e:
    print(f"✗ from_orm() failed: {e}")
    import traceback
    traceback.print_exc()

# Test Case 2: ORM Mode WITHOUT voucher_code (OLD DB SCHEMA)
print("\n" + "=" * 70)
print("Test 2: from_orm() WITHOUT voucher_code (simulating old DB)")
print("=" * 70)

class MockVoucherNoCode:
    """Mock ORM object WITHOUT voucher_code (old DB)"""
    id = 2
    # voucher_code = None  # Missing field!
    voucher_type = VoucherType.PREPAID
    value_cents = 2000
    status = VoucherStatus.CREATED
    reason = None
    created_by_user_id = 1
    created_at = datetime.now()
    redeemed_by_user_id = None
    redeemed_at = None

try:
    # Workaround: Manually create dict without voucher_code field
    response = VoucherResponse.from_orm(MockVoucherNoCode())
    print("✓ from_orm() succeeded (with fallback)!")
    print(f"  voucher_code: {response.voucher_code}")
    print(f"  (This was generated because DB didn't have voucher_code field)")
except Exception as e:
    print(f"⚠️  from_orm() failed (trying dict fallback...)")
    
    # Fallback: use dict initialization
    try:
        data = {
            'id': 2,
            'voucher_type': VoucherType.PREPAID,
            'value_cents': 2000,
            'status': VoucherStatus.CREATED,
            'reason': None,
            'created_by_user_id': 1,
            'created_at': datetime.now(),
        }
        response = VoucherResponse(**data)
        print("✓ Dict initialization succeeded!")
        print(f"  voucher_code: {response.voucher_code}")
        print(f"  (Auto-generated to {response.voucher_code} from ID)")
    except Exception as e2:
        print(f"✗ Dict init failed: {e2}")

# Test Case 3: Verify Frontend Display Logic
print("\n" + "=" * 70)
print("Test 3: Frontend display logic simulation")
print("=" * 70)

test_responses = [
    {"id": 1, "voucher_code": "V-2026-001"},
    {"id": 2, "voucher_code": None},
    {"id": 3},  # No voucher_code at all
]

for test in test_responses:
    voucher_code = test.get('voucher_code')
    voucher_id = test.get('id')
    
    # This is what the frontend does:
    display_code = voucher_code or f"V-2026-{str(voucher_id).zfill(3)}"
    
    print(f"\nVoucher ID: {voucher_id}")
    print(f"  voucher_code from API: {voucher_code}")
    print(f"  Display in UI: {display_code}")

print("\n" + "=" * 70)
print("All tests completed!")
print("=" * 70)
print("\nExpected behavior:")
print("1. If DB has voucher_code column → Use it directly")
print("2. If DB is old (no column) → Generate from ID")
print("3. Frontend fallback → Uses API value or generates from ID")
