"""
Database migration helper - Handles schema updates without external tools
Run automatically on app startup to add missing columns/tables
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import logging

from app.services.app_settings_service import DEFAULT_APP_NAME

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles automatic database schema migrations"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def migrate(self) -> bool:
        """Run all pending migrations. Returns True if successful."""
        try:
            logger.info("=" * 70)
            logger.info("DATABASE MIGRATION STARTED")
            logger.info("=" * 70)
            
            # Step 1: Create all tables first
            logger.info("✓ Step 1: Creating/verifying tables...")
            from app.models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("  → All tables created/verified")
            
            # Step 2: Update enum types if needed
            logger.info("✓ Step 2: Updating enum types...")
            self._update_enum_types()
            logger.info("  → Enum types checked")
            
            # Step 3: Apply column additions for existing tables
            logger.info("✓ Step 3: Adding missing columns...")
            self._add_missing_columns()
            logger.info("  → Missing columns added")
            
            logger.info("=" * 70)
            logger.info("✓ DATABASE MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            return True
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"✗ DATABASE MIGRATION FAILED: {str(e)}")
            logger.error("=" * 70)
            import traceback
            logger.error(traceback.format_exc())
            # Don't crash, just log - tables might already exist
            return False
    
    def _update_enum_types(self):
        """Update enum types to match current version"""
        with self.engine.connect() as conn:
            try:
                self._sync_enum_type(
                    conn=conn,
                    enum_name="transactiontype",
                    expected_values=["SALE", "STORNO", "RECHARGE", "VOUCHER_SALE", "VOUCHER_REDEMPTION"],
                    column_specs=[("transactions", "type")],
                )
                self._sync_enum_type(
                    conn=conn,
                    enum_name="paymentmethod",
                    expected_values=["CASH", "BALANCE", "VOUCHER_GIFT", "VOUCHER_PREPAID"],
                    column_specs=[("transactions", "payment_method")],
                )
                self._sync_enum_type(
                    conn=conn,
                    enum_name="userrole",
                    expected_values=["TOP_ADMIN", "ADMIN", "VERKAUF", "MANAGER"],
                    column_specs=[("users", "role"), ("members", "role")],
                    using_expressions={
                        ("users", "role"): (
                            "CASE "
                            "WHEN role::text = 'TOP_ADMIN' THEN 'TOP_ADMIN'::userrole "
                            "WHEN role::text = 'ADMIN' THEN 'ADMIN'::userrole "
                            "WHEN role::text = 'KASSENMITGLIED' THEN 'MANAGER'::userrole "
                            "ELSE 'VERKAUF'::userrole "
                            "END"
                        ),
                        ("members", "role"): (
                            "CASE "
                            "WHEN role IS NULL THEN NULL "
                            "WHEN role::text = 'TOP_ADMIN' THEN 'TOP_ADMIN'::userrole "
                            "WHEN role::text = 'ADMIN' THEN 'ADMIN'::userrole "
                            "WHEN role::text = 'KASSENMITGLIED' THEN 'MANAGER'::userrole "
                            "ELSE 'VERKAUF'::userrole "
                            "END"
                        ),
                    },
                )
                self._sync_enum_type(
                    conn=conn,
                    enum_name="voucherreason",
                    expected_values=["DYP_SIEGER", "PROMOTION"],
                    column_specs=[("vouchers", "reason")],
                    using_expressions={
                        ("vouchers", "reason"): (
                            "CASE "
                            "WHEN reason IS NULL THEN NULL "
                            "WHEN reason::text = 'DYP_SIEGER' THEN 'DYP_SIEGER'::voucherreason "
                            "ELSE 'PROMOTION'::voucherreason "
                            "END"
                        )
                    },
                )
                self._sync_enum_type(
                    conn=conn,
                    enum_name="voucherstatus",
                    expected_values=["CREATED", "PARTIALLY_REDEEMED", "REDEEMED"],
                    column_specs=[("vouchers", "status")],
                    using_expressions={
                        ("vouchers", "status"): (
                            "CASE "
                            "WHEN status::text = 'REDEEMED' THEN 'REDEEMED'::voucherstatus "
                            "ELSE 'CREATED'::voucherstatus "
                            "END"
                        )
                    },
                )
            except Exception as e:
                logger.warning(f"Could not update enum types: {str(e)}")
                try:
                    conn.rollback()
                except:
                    pass

    def _sync_enum_type(
        self,
        conn,
        enum_name: str,
        expected_values: list[str],
        column_specs: list[tuple[str, str]],
        using_expressions: dict[tuple[str, str], str] | None = None,
    ):
        """Recreate enum types when legacy databases are missing values."""
        result = conn.execute(text(
            "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = :enum_name)"
        ), {"enum_name": enum_name})
        enum_exists = result.scalar()

        if not enum_exists:
            logger.debug(f"Enum {enum_name} does not exist yet")
            return

        result = conn.execute(text(
            "SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = :enum_name) ORDER BY enumsortorder"
        ), {"enum_name": enum_name})
        current_values = [row[0] for row in result.fetchall()]

        if current_values == expected_values:
            logger.debug(f"{enum_name} enum already has correct values")
            return

        logger.info(f"Recreating {enum_name} enum with values {expected_values}...")
        temp_name = f"{enum_name}_old"
        values_sql = ", ".join([f"'{value}'" for value in expected_values])

        conn.execute(text(f"ALTER TYPE {enum_name} RENAME TO {temp_name}"))
        conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({values_sql})"))

        for table_name, column_name in column_specs:
            using_expression = (
                using_expressions.get((table_name, column_name))
                if using_expressions
                else None
            ) or f"{column_name}::text::{enum_name}"
            conn.execute(text(
                f"ALTER TABLE {table_name} "
                f"ALTER COLUMN {column_name} TYPE {enum_name} "
                f"USING {using_expression}"
            ))

        conn.execute(text(f"DROP TYPE {temp_name}"))
        conn.commit()
        logger.info(f"✓ Successfully updated {enum_name} enum")
    
    def _add_missing_columns(self):
        """Add missing columns to existing tables"""
        with self.engine.connect() as conn:
            inspector = inspect(self.engine)
            
            # ============================================================================
            # VOUCHER_CODE COLUMN - CRITICAL FOR VOUCHER SYSTEM
            # ============================================================================
            if 'vouchers' in inspector.get_table_names():
                vouchers_columns = {col['name'] for col in inspector.get_columns('vouchers')}
                
                if 'voucher_code' not in vouchers_columns:
                    logger.critical("🚨 CRITICAL: voucher_code column MISSING from vouchers table!")
                    logger.info("Adding voucher_code column...")
                    
                    try:
                        conn.execute(text(
                            "ALTER TABLE vouchers ADD COLUMN voucher_code VARCHAR(20) UNIQUE"
                        ))
                        conn.commit()
                        logger.info("✓ Added voucher_code column to vouchers")
                    except Exception as e:
                        logger.error(f"Failed to add voucher_code column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                    
                    # Generate codes for existing vouchers
                    try:
                        logger.info("Generating voucher codes for existing vouchers...")
                        result = conn.execute(text("""
                            UPDATE vouchers 
                            SET voucher_code = 'V-' || CAST(EXTRACT(YEAR FROM COALESCE(created_at, NOW())) AS INTEGER)::TEXT || '-' || LPAD(CAST(voucher_number AS TEXT), 3, '0') 
                            WHERE voucher_code IS NULL
                        """))
                        conn.commit()
                        logger.info(f"✓ Generated codes for existing vouchers ({result.rowcount} rows)")
                             
                    except Exception as e:
                        logger.warning(f"Could not generate codes: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                else:
                    logger.debug("✓ voucher_code column already exists")
                    try:
                        logger.info("Backfilling missing voucher_code values...")
                        result = conn.execute(text("""
                            UPDATE vouchers
                            SET voucher_code = 'V-' || CAST(EXTRACT(YEAR FROM COALESCE(created_at, NOW())) AS INTEGER)::TEXT || '-' || LPAD(CAST(voucher_number AS TEXT), 3, '0')
                            WHERE voucher_code IS NULL
                        """))
                        conn.commit()
                        logger.info(f"✓ Backfilled missing voucher_code values ({result.rowcount} rows)")
                    except Exception as e:
                        logger.warning(f"Could not backfill voucher_code values: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
            
            # ============================================================================
            # OTHER COLUMNS
            # ============================================================================

            if 'app_settings' in inspector.get_table_names():
                app_settings_columns = {col['name'] for col in inspector.get_columns('app_settings')}

                if 'app_name' not in app_settings_columns:
                    logger.info("Adding app_name column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN app_name VARCHAR(120) DEFAULT :default_app_name NOT NULL"
                        ), {"default_app_name": DEFAULT_APP_NAME})
                        conn.commit()
                        logger.info("✓ Added app_name column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add app_name column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

            if 'members' in inspector.get_table_names():
                member_columns = {col['name'] for col in inspector.get_columns('members')}

                if 'first_name' not in member_columns:
                    conn.execute(text("ALTER TABLE members ADD COLUMN first_name VARCHAR(80)"))
                    conn.execute(text("""
                        UPDATE members
                        SET first_name = COALESCE(
                            NULLIF(SPLIT_PART(TRIM(name), ' ', 1), ''),
                            CONCAT('Mitglied ', member_number::text)
                        )
                    """))
                    conn.execute(text("ALTER TABLE members ALTER COLUMN first_name SET NOT NULL"))
                    conn.commit()

                if 'last_name' not in member_columns:
                    conn.execute(text("ALTER TABLE members ADD COLUMN last_name VARCHAR(80)"))
                    conn.execute(text("""
                        UPDATE members
                        SET last_name = CASE
                            WHEN POSITION(' ' IN TRIM(COALESCE(name, ''))) > 0
                                THEN TRIM(SUBSTRING(TRIM(name) FROM POSITION(' ' IN TRIM(name)) + 1))
                            ELSE ''
                        END
                        WHERE last_name IS NULL
                    """))
                    conn.commit()

                if 'membership_number' not in member_columns:
                    conn.execute(text("ALTER TABLE members ADD COLUMN membership_number VARCHAR(50)"))
                    conn.commit()

                if 'has_discount' not in member_columns:
                    conn.execute(text("ALTER TABLE members ADD COLUMN has_discount BOOLEAN DEFAULT TRUE NOT NULL"))
                    conn.commit()

                if 'role' not in member_columns:
                    conn.execute(text("ALTER TABLE members ADD COLUMN role userrole"))
                    conn.commit()

            if 'transactions' in inspector.get_table_names():
                transaction_columns = {col['name'] for col in inspector.get_columns('transactions')}

                if 'balance_applied_cents' not in transaction_columns:
                    conn.execute(text(
                        "ALTER TABLE transactions ADD COLUMN balance_applied_cents INTEGER DEFAULT 0 NOT NULL"
                    ))
                    conn.commit()
                else:
                    try:
                        conn.execute(text(
                            "UPDATE app_settings "
                            "SET app_name = :default_app_name "
                            "WHERE app_name IS NULL OR TRIM(app_name) = ''"
                        ), {"default_app_name": DEFAULT_APP_NAME})
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not backfill app_name values: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

            if 'users' in inspector.get_table_names():
                users_columns = {col['name']: col for col in inspector.get_columns('users')}
                if 'email' in users_columns:
                    try:
                        conn.execute(text(
                            "UPDATE users SET email = NULL WHERE email IS NOT NULL AND TRIM(email) = ''"
                        ))
                        if not users_columns['email'].get('nullable', True):
                            conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not update users.email nullability: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

                if 'member_id' not in users_columns:
                    try:
                        conn.execute(text(
                            "ALTER TABLE users ADD COLUMN member_id INTEGER REFERENCES members(id)"
                        ))
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_member_id ON users (member_id) WHERE member_id IS NOT NULL"
                        ))
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_single_top_admin "
                            "ON users ((role)) WHERE role = 'TOP_ADMIN'"
                        ))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not add users.member_id column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                else:
                    try:
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_member_id ON users (member_id) WHERE member_id IS NOT NULL"
                        ))
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_single_top_admin "
                            "ON users ((role)) WHERE role = 'TOP_ADMIN'"
                        ))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not ensure users.member_id index: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

            if 'members' in inspector.get_table_names():
                members_columns = {col['name']: col for col in inspector.get_columns('members')}

                try:
                    conn.execute(text(
                        "UPDATE members SET email = NULL WHERE email IS NOT NULL AND TRIM(email) = ''"
                    ))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not normalize member emails: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass

                if 'member_number' not in members_columns:
                    logger.info("Adding member_number column to members table...")
                    try:
                        conn.execute(text("ALTER TABLE members ADD COLUMN member_number INTEGER"))
                        conn.execute(text("""
                            WITH missing_members AS (
                                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS row_number
                                FROM members
                                WHERE member_number IS NULL
                            ),
                            current_max AS (
                                SELECT COALESCE(MAX(member_number), 0) AS max_member_number
                                FROM members
                            )
                            UPDATE members
                            SET member_number = current_max.max_member_number + missing_members.row_number
                            FROM missing_members, current_max
                            WHERE members.id = missing_members.id
                              AND members.member_number IS NULL
                        """))
                        conn.execute(text("ALTER TABLE members ALTER COLUMN member_number SET NOT NULL"))
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ix_members_member_number ON members (member_number)"
                        ))
                        conn.commit()
                        logger.info("✓ Added member_number column to members")
                    except Exception as e:
                        logger.warning(f"Could not add member_number column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                else:
                    try:
                        conn.execute(text("""
                            WITH missing_members AS (
                                SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS row_number
                                FROM members
                                WHERE member_number IS NULL
                            ),
                            current_max AS (
                                SELECT COALESCE(MAX(member_number), 0) AS max_member_number
                                FROM members
                                WHERE member_number IS NOT NULL
                            )
                            UPDATE members
                            SET member_number = current_max.max_member_number + missing_members.row_number
                            FROM missing_members, current_max
                            WHERE members.id = missing_members.id
                              AND members.member_number IS NULL
                        """))
                        conn.execute(text("ALTER TABLE members ALTER COLUMN member_number SET NOT NULL"))
                        conn.execute(text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ix_members_member_number ON members (member_number)"
                        ))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not backfill member_number values: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
             
            # Tax rate column
            if 'products' in inspector.get_table_names():
                products_columns = {col['name'] for col in inspector.get_columns('products')}
                
                if 'tax_rate' not in products_columns:
                    logger.info("Adding tax_rate column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN tax_rate FLOAT DEFAULT 0.0 NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added tax_rate column to products")
                    except Exception as e:
                        logger.warning(f"Could not add tax_rate column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
            
            # Display order column
            if 'categories' in inspector.get_table_names():
                categories_columns = {col['name'] for col in inspector.get_columns('categories')}
                
                if 'display_order' not in categories_columns:
                    logger.info("Adding display_order column to categories table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE categories ADD COLUMN display_order INTEGER DEFAULT 0 NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added display_order column to categories")
                    except Exception as e:
                        logger.warning(f"Could not add display_order column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

            if 'transactions' in inspector.get_table_names():
                transaction_columns = {col['name'] for col in inspector.get_columns('transactions')}

                missing_transaction_columns = [
                    (
                        'voucher_code',
                        "ALTER TABLE transactions ADD COLUMN voucher_code VARCHAR(20)"
                    ),
                    (
                        'voucher_type',
                        "ALTER TABLE transactions ADD COLUMN voucher_type VARCHAR(20)"
                    ),
                    (
                        'voucher_applied_cents',
                        "ALTER TABLE transactions ADD COLUMN voucher_applied_cents INTEGER DEFAULT 0 NOT NULL"
                    ),
                ]

                for column_name, sql in missing_transaction_columns:
                    if column_name in transaction_columns:
                        continue

                    logger.info(f"Adding {column_name} column to transactions table...")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✓ Added {column_name} column to transactions")
                    except Exception as e:
                        logger.warning(f"Could not add {column_name} column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

            if 'vouchers' in inspector.get_table_names():
                voucher_columns = {col['name'] for col in inspector.get_columns('vouchers')}

                missing_voucher_columns = [
                    (
                        'redeemed_amount_cents',
                        "ALTER TABLE vouchers ADD COLUMN redeemed_amount_cents INTEGER"
                    ),
                    (
                        'original_value_cents',
                        "ALTER TABLE vouchers ADD COLUMN original_value_cents INTEGER DEFAULT 0 NOT NULL"
                    ),
                    (
                        'remaining_value_cents',
                        "ALTER TABLE vouchers ADD COLUMN remaining_value_cents INTEGER DEFAULT 0 NOT NULL"
                    ),
                    (
                        'sold_by_user_id',
                        "ALTER TABLE vouchers ADD COLUMN sold_by_user_id INTEGER REFERENCES users(id)"
                    ),
                    (
                        'sold_at',
                        "ALTER TABLE vouchers ADD COLUMN sold_at TIMESTAMP"
                    ),
                    (
                        'sold_in_transaction_id',
                        "ALTER TABLE vouchers ADD COLUMN sold_in_transaction_id INTEGER REFERENCES transactions(id)"
                    ),
                ]

                for column_name, sql in missing_voucher_columns:
                    if column_name in voucher_columns:
                        continue

                    logger.info(f"Adding {column_name} column to vouchers table...")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✓ Added {column_name} column to vouchers")
                    except Exception as e:
                        logger.warning(f"Could not add {column_name} column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass

                try:
                    logger.info("Backfilling voucher original/remaining values...")
                    conn.execute(text("""
                        UPDATE vouchers
                        SET
                            original_value_cents = CASE
                                WHEN original_value_cents IS NULL
                                    THEN value_cents
                                ELSE original_value_cents
                            END,
                            remaining_value_cents = CASE
                                WHEN status::text = 'REDEEMED' THEN 0
                                WHEN remaining_value_cents IS NULL
                                    THEN GREATEST(
                                        value_cents - COALESCE(redeemed_amount_cents, 0),
                                        0
                                    )
                                ELSE remaining_value_cents
                            END,
                            redeemed_amount_cents = COALESCE(redeemed_amount_cents, CASE
                                WHEN status::text = 'REDEEMED' THEN value_cents
                                ELSE 0
                            END)
                    """))
                    conn.commit()
                    logger.info("✓ Backfilled voucher original/remaining values")
                except Exception as e:
                    logger.warning(f"Could not backfill voucher values: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass

                try:
                    logger.info("Normalizing partial voucher statuses...")
                    conn.execute(text("""
                        UPDATE vouchers
                        SET status = CASE
                            WHEN remaining_value_cents <= 0 THEN 'REDEEMED'::voucherstatus
                            WHEN COALESCE(redeemed_amount_cents, 0) > 0 THEN 'PARTIALLY_REDEEMED'::voucherstatus
                            ELSE 'CREATED'::voucherstatus
                        END
                    """))
                    conn.commit()
                    logger.info("✓ Normalized voucher statuses")
                except Exception as e:
                    logger.warning(f"Could not normalize voucher statuses: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass

            if 'zbon_history' in inspector.get_table_names():
                zbon_columns = {col['name'] for col in inspector.get_columns('zbon_history')}

                missing_zbon_columns = [
                    ('report_type', "ALTER TABLE zbon_history ADD COLUMN report_type VARCHAR(50) DEFAULT 'zbon' NOT NULL"),
                    ('gross_revenue_voucher', "ALTER TABLE zbon_history ADD COLUMN gross_revenue_voucher FLOAT DEFAULT 0.0 NOT NULL"),
                    ('total_revenue', "ALTER TABLE zbon_history ADD COLUMN total_revenue FLOAT DEFAULT 0.0 NOT NULL"),
                    ('voucher_created_total', "ALTER TABLE zbon_history ADD COLUMN voucher_created_total FLOAT DEFAULT 0.0 NOT NULL"),
                    ('voucher_redeemed_total', "ALTER TABLE zbon_history ADD COLUMN voucher_redeemed_total FLOAT DEFAULT 0.0 NOT NULL"),
                    ('voucher_open_total', "ALTER TABLE zbon_history ADD COLUMN voucher_open_total FLOAT DEFAULT 0.0 NOT NULL"),
                    ('transaction_count_total', "ALTER TABLE zbon_history ADD COLUMN transaction_count_total INTEGER DEFAULT 0 NOT NULL"),
                    ('voucher_created_count', "ALTER TABLE zbon_history ADD COLUMN voucher_created_count INTEGER DEFAULT 0 NOT NULL"),
                    ('voucher_redeemed_count', "ALTER TABLE zbon_history ADD COLUMN voucher_redeemed_count INTEGER DEFAULT 0 NOT NULL"),
                    ('voucher_open_count', "ALTER TABLE zbon_history ADD COLUMN voucher_open_count INTEGER DEFAULT 0 NOT NULL"),
                    ('created_by_name', "ALTER TABLE zbon_history ADD COLUMN created_by_name VARCHAR(255)"),
                    ('skimmed_by_name', "ALTER TABLE zbon_history ADD COLUMN skimmed_by_name VARCHAR(255)"),
                    ('cash_counted_by_name', "ALTER TABLE zbon_history ADD COLUMN cash_counted_by_name VARCHAR(255)"),
                    ('cash_count_details', "ALTER TABLE zbon_history ADD COLUMN cash_count_details TEXT"),
                    ('report_data', "ALTER TABLE zbon_history ADD COLUMN report_data TEXT"),
                ]

                for column_name, sql in missing_zbon_columns:
                    if column_name in zbon_columns:
                        continue

                    logger.info(f"Adding {column_name} column to zbon_history table...")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✓ Added {column_name} column to zbon_history")
                    except Exception as e:
                        logger.warning(f"Could not add {column_name} column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass


def run_migrations(engine: Engine) -> bool:
    """
    Run database migrations on startup.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        migrator = DatabaseMigrator(engine)
        return migrator.migrate()
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        # Don't crash the app, just log the error
        # This allows the app to start even if migrations fail
        # (useful for development/debugging)
        return False
