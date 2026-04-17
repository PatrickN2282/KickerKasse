#!/usr/bin/env python3
"""
Diagnostic script to check actual database state and API responses
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models import Voucher
from app.repositories.voucher_repository import VoucherRepository
from app.schemas.voucher import VoucherResponse
import json
from datetime import datetime

print("\n" + "=" * 80)
print("VOUCHER SYSTEM DIAGNOSTIC")
print("=" * 80)

# Step 1: Check database structure
print("\n1️⃣  CHECKING DATABASE STRUCTURE")
print("-" * 80)

with engine.connect() as conn:
    # Check if table exists
    result = conn.execute(text(
        "SELECT to_regclass('public.vouchers')"
    ))
    table_exists = result.scalar() is not None
    print(f"  Table 'vouchers' exists: {table_exists}")
    
    if table_exists:
        # Get table structure
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'vouchers'
            ORDER BY ordinal_position
        """))
        
        print("\n  Column Structure:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            print(f"    • {row[0]:25} {row[1]:20} {nullable}")
        
        # Check if voucher_code column exists
        result = conn.execute(text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'vouchers' AND column_name = 'voucher_code')"
        ))
        has_voucher_code = result.scalar()
        print(f"\n  🔍 voucher_code column exists: {has_voucher_code}")

# Step 2: Check existing vouchers in DB
print("\n2️⃣  CHECKING EXISTING VOUCHERS IN DATABASE")
print("-" * 80)

db = SessionLocal()
try:
    vouchers_count = db.query(Voucher).count()
    print(f"  Total vouchers in DB: {vouchers_count}")
    
    if vouchers_count > 0:
        print(f"\n  First 5 vouchers (raw ORM objects):")
        
        first_vouchers = db.query(Voucher).limit(5).all()
        for v in first_vouchers:
            print(f"\n    ID {v.id}:")
            print(f"      • voucher_number: {v.voucher_number}")
            print(f"      • voucher_code: {v.voucher_code}")
            print(f"      • voucher_type: {v.voucher_type}")
            print(f"      • status: {v.status}")
            print(f"      • value_cents: {v.value_cents}")
            print(f"      • reason: {v.reason}")
            
            # Try to convert with Pydantic
            try:
                response = VoucherResponse.from_orm(v)
                print(f"      ✓ Pydantic conversion successful")
                print(f"      → voucher_code in response: {response.voucher_code}")
                print(f"      → Full response.model_dump():")
                resp_dict = response.model_dump()
                for key in ['id', 'voucher_code', 'voucher_type', 'status', 'value_cents']:
                    print(f"         {key}: {resp_dict.get(key)}")
            except Exception as e:
                print(f"      ✗ Pydantic conversion failed: {e}")
    
finally:
    db.close()

# Step 3: Test Repository.create()
print("\n3️⃣  TESTING REPOSITORY.CREATE() METHOD")
print("-" * 80)

db = SessionLocal()
try:
    # Create a test voucher USING REPOSITORY (simulates what API does)
    repo = VoucherRepository(db)
    
    print("  Creating test GIFT voucher...")
    test_voucher = repo.create(
        voucher_type="GIFT",
        value_cents=5000,
        created_by_user_id=1,
        reason="PROMOTION",
    )
    
    print(f"  ✓ Voucher created via Repository:")
    print(f"    • ID: {test_voucher.id}")
    print(f"    • voucher_number: {test_voucher.voucher_number}")
    print(f"    • voucher_code: {test_voucher.voucher_code}")
    
    # Now convert with Pydantic (simulates what API does)
    print(f"\n  Converting to VoucherResponse...")
    try:
        response = VoucherResponse.from_orm(test_voucher)
        print(f"  ✓ Conversion successful:")
        print(f"    • response.voucher_code: {response.voucher_code}")
        print(f"    • response.id: {response.id}")
        
        # Simulate what frontend receives
        print(f"\n  What frontend would receive (model_dump_json):")
        response_json = response.model_dump_json()
        response_dict = json.loads(response_json)
        print(f"    {json.dumps(response_dict, indent=6, default=str)}")
        
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()

finally:
    db.close()

# Step 4: Check API response format
print("\n4️⃣  CHECKING API RESPONSE STRUCTURE")
print("-" * 80)

print("""
  When POST /api/admin/vouchers/gift/ returns 201:
  
  Expected response:
  {
    "id": 123,
    "voucher_code": "V-2026-001",
    "voucher_type": "GIFT",
    "value_cents": 1000,
    "status": "CREATED",
    "reason": "PROMOTION",
    "created_by_user_id": 1,
    "created_at": "2026-04-15T...",
    ...
  }
  
  If voucher_code is null/undefined → frontend shows fallback "V-2026-{id}"
  If voucher_code is missing → frontend shows "V-2026-undefined"
""")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE - Check output above for issues")
print("=" * 80 + "\n")
