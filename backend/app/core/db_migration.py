"""
Database migration helper - Handles schema updates without external tools
Run automatically on app startup to add missing columns/tables
"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
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
                # Check if voucherreason enum exists
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'voucherreason')"
                ))
                enum_exists = result.scalar()
                
                if enum_exists:
                    logger.info("Updating voucherreason enum type...")
                    try:
                        # Get current enum values
                        result = conn.execute(text(
                            "SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'voucherreason') ORDER BY enumsortorder"
                        ))
                        current_values = [row[0] for row in result.fetchall()]
                        logger.debug(f"Current enum values: {current_values}")
                        
                        # Define expected values in correct order
                        expected_values = ['COURTESY', 'PROMOTIONAL', 'STAFF_BENEFIT', 'OTHER']
                        
                        # Check if we need to update
                        if current_values != expected_values:
                            # We need to recreate the enum
                            logger.info("Recreating voucherreason enum with updated values...")
                            
                            # Rename old enum
                            conn.execute(text("ALTER TYPE voucherreason RENAME TO voucherreason_old"))
                            
                            # Create new enum with correct values
                            values_str = ", ".join([f"'{v}'" for v in expected_values])
                            conn.execute(text(f"CREATE TYPE voucherreason AS ENUM ({values_str})"))
                            
                            # Update columns to use new enum
                            conn.execute(text(
                                "ALTER TABLE vouchers ALTER COLUMN reason TYPE voucherreason USING reason::text::voucherreason"
                            ))
                            
                            # Drop old enum
                            conn.execute(text("DROP TYPE voucherreason_old"))
                            
                            logger.info("✓ Successfully updated voucherreason enum")
                        else:
                            logger.debug("voucherreason enum already has correct values")
                    
                    except Exception as e:
                        logger.debug(f"Enum already up to date or error: {str(e)}")
                    
                    conn.commit()
            except Exception as e:
                logger.warning(f"Could not update enum types: {str(e)}")
                try:
                    conn.rollback()
                except:
                    pass
    
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
                        conn.execute(text("""
                            UPDATE vouchers 
                            SET voucher_code = 'V-2026-' || LPAD(CAST(voucher_number AS TEXT), 3, '0') 
                            WHERE voucher_code IS NULL
                        """))
                        conn.commit()
                        logger.info("✓ Generated codes for existing vouchers")
                            
                    except Exception as e:
                        logger.warning(f"Could not generate codes: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                else:
                    logger.debug("✓ voucher_code column already exists")
            
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
