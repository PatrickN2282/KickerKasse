#!/usr/bin/env python3
"""
Test the actual database connection and create a test voucher
"""
import sys
import os
from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.core.db_migration import run_migrations
from app.models import Voucher, User
from app.repositories.voucher_repository import VoucherRepository
from app.schemas.voucher import VoucherResponse

print("=" * 60)
print("VOUCHER SYSTEM TEST")
print("=" * 60)

# Step 1: Check database connection
print("\n1️⃣  Checking database connection...")
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("   ✓ Database connection OK")
except Exception as e:
    print(f"   ✗ Database connection failed: {str(e)}")
    sys.exit(1)

# Step 2: Run migrations
print("\n2️⃣  Running database migrations...")
try:
    run_migrations(engine)
    print("   ✓ Migrations completed")
except Exception as e:
    print(f"   ⚠ Migration warning: {str(e)}")

# Step 3: Check if vouchers table exists and has voucher_code column
print("\n3️⃣  Checking vouchers table structure...")
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    if 'vouchers' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('vouchers')}
        print(f"   ✓ Vouchers table exists with {len(columns)} columns")
        
        if 'voucher_code' in columns:
            print("   ✓ voucher_code column exists")
        else:
            print("   ✗ voucher_code column MISSING!")
    else:
        print("   ✗ Vouchers table does NOT exist!")
except Exception as e:
    print(f"   ✗ Error checking table: {str(e)}")

# Step 4: Try to create a test voucher
print("\n4️⃣  Attempting to create test voucher...")
try:
    db = next(get_db())
    
    # Check if default admin user exists
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        print("   ⚠ No admin user found, creating test voucher without user check...")
        admin_id = 1  # Assume ID 1
    else:
        admin_id = admin_user.id
        print(f"   ✓ Found admin user (ID: {admin_id})")
    
    repo = VoucherRepository(db)
    voucher = repo.create(
        voucher_type="GIFT",
        value_cents=1000,
        created_by_user_id=admin_id,
        reason="COURTESY",
    )
    
    print(f"   ✓ Created voucher!")
    print(f"      - ID: {voucher.id}")
    print(f"      - Number: {voucher.voucher_number}")
    print(f"      - Code: {voucher.voucher_code}")
    print(f"      - Type: {voucher.voucher_type}")
    print(f"      - Status: {voucher.status}")
    
    # Step 5: Test VoucherResponse.from_orm()
    print("\n5️⃣  Testing VoucherResponse.from_orm()...")
    try:
        response = VoucherResponse.from_orm(voucher)
        print(f"   ✓ from_orm() succeeded!")
        print(f"      - voucher_code: {response.voucher_code}")
        print(f"      - voucher_type: {response.voucher_type}")
        print(f"      - status: {response.status}")
        print(f"\n   Full response: {response.model_dump()}")
    except Exception as e:
        print(f"   ✗ from_orm() failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    db.close()
    
except Exception as e:
    print(f"   ✗ Error creating voucher: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
