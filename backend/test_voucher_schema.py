#!/usr/bin/env python3
"""
Quick test to verify VoucherResponse schema works correctly with from_orm()
"""
from datetime import datetime
from app.models import Voucher, VoucherType, VoucherStatus, VoucherReason
from app.schemas import VoucherResponse

# Create a mock voucher object (simulate what would come from DB)
mock_voucher = type('MockVoucher', (), {
    'id': 1,
    'voucher_number': 1,
    'voucher_code': 'V-2026-001',
    'voucher_type': VoucherType.GIFT,
    'status': VoucherStatus.CREATED,
    'value_cents': 1000,
    'reason': VoucherReason.COURTESY,
    'created_by_user_id': 1,
    'created_at': datetime.now(),
    'redeemed_by_user_id': None,
    'redeemed_at': None,
})()

print("Testing VoucherResponse.from_orm()...")
print(f"Mock voucher type: {type(mock_voucher)}")
print(f"Mock voucher.voucher_code: {mock_voucher.voucher_code}")
print(f"Mock voucher.voucher_type: {mock_voucher.voucher_type} (type: {type(mock_voucher.voucher_type)})")
print(f"Mock voucher.status: {mock_voucher.status} (type: {type(mock_voucher.status)})")
print()

try:
    response = VoucherResponse.from_orm(mock_voucher)
    print("✓ from_orm() succeeded!")
    print(f"Response dict: {response.model_dump()}")
    print(f"  - voucher_code: {response.voucher_code}")
    print(f"  - voucher_type: {response.voucher_type}")
    print(f"  - status: {response.status}")
except Exception as e:
    print(f"✗ from_orm() failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nTesting VoucherResponse.from_orm() fallback for missing voucher_code...")
mock_voucher_without_code = type('MockVoucherWithoutCode', (), {
    'id': 2,
    'voucher_number': 2,
    'voucher_code': None,
    'voucher_type': VoucherType.PREPAID,
    'status': VoucherStatus.CREATED,
    'value_cents': 2000,
    'reason': VoucherReason.OTHER,
    'created_by_user_id': 1,
    'created_at': datetime(2025, 1, 1),
    'redeemed_by_user_id': None,
    'redeemed_at': None,
})()

try:
    response = VoucherResponse.from_orm(mock_voucher_without_code)
    print("✓ fallback from_orm() succeeded!")
    print(f"  - voucher_number: {response.voucher_number}")
    print(f"  - voucher_code: {response.voucher_code}")
except Exception as e:
    print(f"✗ fallback from_orm() failed: {str(e)}")
    import traceback
    traceback.print_exc()
