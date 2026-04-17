#!/usr/bin/env python3
"""
Post-migration verification script
Run manually after container start to verify migration was successful
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from app.core.database import engine

def check_migration():
    """Check if migration was successful"""
    inspector = inspect(engine)
    
    print("\n" + "=" * 70)
    print("DATABASE MIGRATION VERIFICATION")
    print("=" * 70)
    
    # Step 1: Check tables
    print("\n✓ Step 1: Checking tables...")
    tables = inspector.get_table_names()
    required_tables = ['users', 'members', 'products', 'categories', 'transactions', 'vouchers', 'zbon_history']
    
    for table in required_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} MISSING!")
    
    # Step 2: Check vouchers table columns
    if 'vouchers' in tables:
        print("\n✓ Step 2: Checking vouchers columns...")
        columns = {col['name']: col for col in inspector.get_columns('vouchers')}
        
        required_columns = {
            'id': 'primary key',
            'voucher_number': 'unique sequence number',
            'voucher_code': 'V-2026-001 format',
            'voucher_type': 'GIFT or PREPAID',
            'status': 'CREATED or REDEEMED',
            'value_cents': 'amount in cents',
            'reason': 'gift category',
            'created_by_user_id': 'foreign key',
            'created_at': 'timestamp',
            'updated_at': 'timestamp',
        }
        
        for col_name, description in required_columns.items():
            if col_name in columns:
                col = columns[col_name]
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  ✓ {col_name:25} {col['type']:15} {nullable:10} ({description})")
            else:
                print(f"  ✗ {col_name:25} MISSING!")
    
    # Step 3: Check for existing vouchers
    print("\n✓ Step 3: Checking vouchers data...")
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM vouchers WHERE voucher_code IS NOT NULL"))
            with_code = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM vouchers WHERE voucher_code IS NULL"))
            without_code = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM vouchers"))
            total = result.scalar()
            
            print(f"  Total vouchers: {total}")
            print(f"  With voucher_code: {with_code}")
            print(f"  Without voucher_code: {without_code}")
            
            if total > 0 and without_code > 0:
                print(f"  ⚠️  WARNING: {without_code} vouchers don't have voucher_code!")
            
            # Show first few vouchers
            if total > 0:
                print(f"\n  First few vouchers:")
                result = conn.execute(text(
                    "SELECT id, voucher_number, voucher_code, voucher_type, status FROM vouchers ORDER BY id LIMIT 5"
                ))
                for row in result:
                    code_display = row[2] or "NULL"
                    print(f"    ID {row[0]}: #{row[1]} → {code_display:12} ({row[3]}/{row[4]})")
            
        except Exception as e:
            print(f"  ✗ Error checking vouchers: {e}")
    
    # Step 4: Check enums
    print("\n✓ Step 4: Checking enum types...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT typname FROM pg_type WHERE typname ~ '^(vouchertype|voucherstatus|voucherreason)$' ORDER BY typname"
            ))
            
            found_enums = [row[0] for row in result]
            required_enums = ['paymentmethod', 'transactiontype', 'voucherreason', 'voucherstatus', 'vouchertype']
            
            for enum_name in required_enums:
                if enum_name in found_enums:
                    # Get enum values
                    result = conn.execute(text(f"""
                        SELECT enumlabel FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = '{enum_name}')
                        ORDER BY enumsortorder
                    """))
                    values = [row[0] for row in result]
                    print(f"  ✓ {enum_name:20} {values}")
                else:
                    print(f"  ✗ {enum_name} MISSING!")
    except Exception as e:
        print(f"  ⚠️  Could not check enums: {e}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        check_migration()
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
