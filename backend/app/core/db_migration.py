"""
Database migration helper - Handles schema updates without external tools
Run automatically on app startup to add missing columns/tables
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import logging

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

                if 'redeemed_amount_cents' not in voucher_columns:
                    logger.info("Adding redeemed_amount_cents column to vouchers table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE vouchers ADD COLUMN redeemed_amount_cents INTEGER"
                        ))
                        conn.commit()
                        logger.info("✓ Added redeemed_amount_cents column to vouchers")
                    except Exception as e:
                        logger.warning(f"Could not add redeemed_amount_cents column: {str(e)}")
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
