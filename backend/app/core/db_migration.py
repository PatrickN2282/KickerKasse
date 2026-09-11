"""
Database migration helper - Handles schema updates without external tools
Run automatically on app startup to add missing columns/tables
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import logging
import re

from app.constants import (
    INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
    INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
    INTERNAL_MATERIAL_CATEGORY_NAME,
)
from app.services.app_settings_service import (
    DEFAULT_APP_NAME,
    DEFAULT_KASSE_AREA_BACKGROUND_COLOR,
    DEFAULT_SESSION_TIMER_MINUTES,
    DEFAULT_KASSE_DIRECT_LOGIN_ENABLED,
    DEFAULT_DECKEL_ENABLED,
    DEFAULT_GUEST_LIST_ENABLED,
    DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE,
    DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY,
    DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED,
    DEFAULT_EMAIL_ENABLED,
    DEFAULT_EMAIL_SENDER,
    DEFAULT_EMAIL_RECIPIENT_ZBON,
    DEFAULT_EMAIL_RECIPIENT_STOCK,
    DEFAULT_EMAIL_RECIPIENT_BACKUP,
    DEFAULT_EMAIL_SUBJECT_SUFFIX,
    DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED,
    DEFAULT_SMTP_HOST,
    DEFAULT_SMTP_PORT,
    DEFAULT_SMTP_USERNAME,
    DEFAULT_SMTP_PASSWORD,
    DEFAULT_SMTP_USE_TLS,
    DEFAULT_SEND_ZBON_ON_CREATE_ENABLED,
    DEFAULT_SCHEDULED_ZBON_ENABLED,
    DEFAULT_SCHEDULED_ZBON_TIME,
    DEFAULT_SCHEDULED_ZBON_REPORT_TYPE,
    DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED,
    DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME,
)

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
            
            from app.models import Base
            from app.core.schema_verification import run_versioned_steps, ensure_data_constraints
            from app.core.access_migration import migrate_access
            from app.core.booking_migration import migrate_vouchers, migrate_guests
            from app.core.closure_migration import migrate_closures, migrate_operations
            from app.core.history_migration import migrate_history
            from app.core.mail_status_migration import migrate_mail_status
            run_versioned_steps(self.engine, [
                ("1.6.5", "create_tables", lambda: Base.metadata.create_all(bind=self.engine)),
                ("1.6.5", "enum_types", self._update_enum_types),
                ("1.6.5", "legacy_columns", self._add_missing_columns),
                ("1.6.5", "integrity_indexes", self._ensure_integrity_indexes),
                ("1.6.6", "data_constraints", lambda: ensure_data_constraints(self.engine)),
                ("1.6.7", "access_sessions_and_limits", lambda: migrate_access(self.engine)),
                ("1.6.10", "voucher_redemptions", lambda: migrate_vouchers(self.engine)),
                ("1.6.11", "sale_guest_positions", lambda: migrate_guests(self.engine)),
                ("1.6.12", "receipt_counter_and_closures", lambda: migrate_closures(self.engine)),
                ("1.6.13", "booking_operations", lambda: migrate_operations(self.engine)),
                ("1.6.14", "history_snapshots_and_member_archive", lambda: migrate_history(self.engine)),
                ("2.3.0", "mail_schedule_and_delivery_status", lambda: migrate_mail_status(self.engine)),
                ("2.6.0", "mail_subject_info_fields", self._add_email_subject_info_columns),
                ("2.6.4", "product_kasse_visibility", self._add_product_kasse_visibility_column),
            ])

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
            # The entrypoint and local startup must reject a False result.
            return False

    def _add_email_subject_info_columns(self):
        """Add per-mail subject info fields before strict schema verification."""
        with self.engine.begin() as conn:
            existing = {column["name"] for column in inspect(conn).get_columns("app_settings")}
            for column_name in (
                "email_subject_zbon_info",
                "email_subject_stock_info",
                "email_subject_backup_info",
            ):
                if column_name not in existing:
                    conn.execute(text(
                        f"ALTER TABLE app_settings ADD COLUMN {column_name} VARCHAR(120)"
                    ))

    def _add_product_kasse_visibility_column(self):
        """Keep product lifecycle and cash-register visibility independent."""
        with self.engine.begin() as conn:
            existing = {column["name"] for column in inspect(conn).get_columns("products")}
            if "is_visible_in_kasse" not in existing:
                conn.execute(text(
                    "ALTER TABLE products ADD COLUMN is_visible_in_kasse "
                    "BOOLEAN DEFAULT TRUE NOT NULL"
                ))

    def _ensure_integrity_indexes(self):
        """Install safeguards that need an explicit migration on existing databases."""
        with self.engine.begin() as conn:
            duplicate_stornos = conn.execute(text("""
                SELECT reference_transaction_id
                FROM transactions
                WHERE type = 'STORNO' AND reference_transaction_id IS NOT NULL
                GROUP BY reference_transaction_id
                HAVING COUNT(*) > 1
            """)).fetchall()
            if duplicate_stornos:
                references = ", ".join(str(row[0]) for row in duplicate_stornos[:10])
                raise RuntimeError(
                    "Cannot enforce one-storno-per-sale; duplicate historical "
                    f"stornos exist for transaction IDs: {references}"
                )
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_transactions_storno_reference
                ON transactions (reference_transaction_id)
                WHERE type = 'STORNO'
            """))

    def _update_enum_types(self):
        """Update enum types to match current version"""
        with self.engine.connect() as conn:
            try:
                self._sync_enum_type(
                    conn=conn,
                    enum_name="transactiontype",
                    expected_values=["SALE", "STORNO", "RECHARGE", "VOUCHER_CREATE", "VOUCHER_SALE", "VOUCHER_REDEMPTION"],
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
                            "WHEN role::text IN ('MANAGER', 'KASSENMITGLIED') THEN 'MANAGER'::userrole "
                            "ELSE 'VERKAUF'::userrole "
                            "END"
                        ),
                        ("members", "role"): (
                            "CASE "
                            "WHEN role IS NULL THEN NULL "
                            "WHEN role::text = 'TOP_ADMIN' THEN 'TOP_ADMIN'::userrole "
                            "WHEN role::text = 'ADMIN' THEN 'ADMIN'::userrole "
                            "WHEN role::text IN ('MANAGER', 'KASSENMITGLIED') THEN 'MANAGER'::userrole "
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
                            "WHEN status::text = 'PARTIALLY_REDEEMED' THEN 'PARTIALLY_REDEEMED'::voucherstatus "
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
                raise

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

        inspector = inspect(conn)
        defaults = {}
        existing_specs = []
        for table_name, column_name in column_specs:
            if not inspector.has_table(table_name):
                continue
            columns = {c["name"]: c for c in inspector.get_columns(table_name)}
            if column_name not in columns:
                continue  # The legacy-column step adds this column afterwards.
            existing_specs.append((table_name, column_name))
            default = columns[column_name].get("default")
            if default is not None:
                defaults[(table_name, column_name)] = default
                conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT"))

        conn.execute(text(f"ALTER TYPE {enum_name} RENAME TO {temp_name}"))
        conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({values_sql})"))

        for table_name, column_name in existing_specs:
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
            default = defaults.get((table_name, column_name))
            if default is not None:
                default = default.replace(f"::{enum_name}", "::text")
                converted_default = re.sub(rf"\b{column_name}\b", lambda _: f"({default})", using_expression)
                conn.execute(text(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT {converted_default}"))

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
                        raise
                    
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
                        raise
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
                        raise
            
            # ============================================================================
            # OTHER COLUMNS
            # ============================================================================

            if 'categories' in inspector.get_table_names():
                categories_columns = {col['name'] for col in inspector.get_columns('categories')}
                if 'color' not in categories_columns:
                    logger.info("Adding color column to categories table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE categories ADD COLUMN color VARCHAR(20)"
                        ))
                        conn.commit()
                        logger.info("✓ Added color column to categories")
                    except Exception as e:
                        logger.warning(f"Could not add categories.color column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

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
                        raise

                if 'kasse_layout' not in app_settings_columns:
                    logger.info("Adding kasse_layout column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN kasse_layout VARCHAR(50)"
                        ))
                        conn.commit()
                        logger.info("✓ Added kasse_layout column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_layout column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'session_timer_enabled' not in app_settings_columns:
                    logger.info("Adding session_timer_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN session_timer_enabled BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added session_timer_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add session_timer_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'session_timer_minutes' not in app_settings_columns:
                    logger.info("Adding session_timer_minutes column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN session_timer_minutes INTEGER DEFAULT :default_session_timer_minutes NOT NULL"
                        ), {"default_session_timer_minutes": DEFAULT_SESSION_TIMER_MINUTES})
                        conn.commit()
                        logger.info("✓ Added session_timer_minutes column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add session_timer_minutes column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'kasse_direct_login_enabled' not in app_settings_columns:
                    logger.info("Adding kasse_direct_login_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN kasse_direct_login_enabled BOOLEAN DEFAULT :default_kasse_direct_login_enabled NOT NULL"
                        ), {"default_kasse_direct_login_enabled": DEFAULT_KASSE_DIRECT_LOGIN_ENABLED})
                        conn.commit()
                        logger.info("✓ Added kasse_direct_login_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_direct_login_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'guest_list_enabled' not in app_settings_columns:
                    logger.info("Adding guest_list_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN guest_list_enabled BOOLEAN DEFAULT :default_guest_list_enabled NOT NULL"
                        ), {"default_guest_list_enabled": DEFAULT_GUEST_LIST_ENABLED})
                        conn.commit()
                        logger.info("✓ Added guest_list_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add guest_list_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'kasse_area_background_color' not in app_settings_columns:
                    logger.info("Adding kasse_area_background_color column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN kasse_area_background_color VARCHAR(7) DEFAULT :default_kasse_area_background_color NOT NULL"
                        ), {"default_kasse_area_background_color": DEFAULT_KASSE_AREA_BACKGROUND_COLOR})
                        conn.commit()
                        logger.info("✓ Added kasse_area_background_color column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_area_background_color column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise


                if 'kasse_products_background_path' not in app_settings_columns:
                    logger.info("Adding kasse_products_background_path column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN kasse_products_background_path VARCHAR(255)"
                        ))
                        conn.commit()
                        logger.info("✓ Added kasse_products_background_path column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_products_background_path column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'kasse_products_background_scale' not in app_settings_columns:
                    logger.info("Adding kasse_products_background_scale column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN kasse_products_background_scale INTEGER DEFAULT :default_background_scale NOT NULL"
                        ), {"default_background_scale": DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE})
                        conn.commit()
                        logger.info("✓ Added kasse_products_background_scale column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_products_background_scale column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'kasse_products_background_opacity' not in app_settings_columns:
                    logger.info("Adding kasse_products_background_opacity column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN kasse_products_background_opacity INTEGER DEFAULT :default_opacity NOT NULL"
                        ), {"default_opacity": DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY})
                        conn.commit()
                        logger.info("✓ Added kasse_products_background_opacity column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_products_background_opacity column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'kasse_products_background_enabled' not in app_settings_columns:
                    logger.info("Adding kasse_products_background_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN kasse_products_background_enabled BOOLEAN DEFAULT :default_enabled NOT NULL"
                        ), {"default_enabled": DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED})
                        conn.commit()
                        logger.info("✓ Added kasse_products_background_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add kasse_products_background_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'deckel_enabled' not in app_settings_columns:
                    logger.info("Adding deckel_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN deckel_enabled BOOLEAN DEFAULT :default_deckel_enabled NOT NULL"
                        ), {"default_deckel_enabled": DEFAULT_DECKEL_ENABLED})
                        conn.commit()
                        logger.info("✓ Added deckel_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add deckel_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_name' not in app_settings_columns:
                    logger.info("Adding business_name column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_name VARCHAR(160)"))
                        conn.commit()
                        logger.info("✓ Added business_name column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_name column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_street' not in app_settings_columns:
                    logger.info("Adding business_street column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_street VARCHAR(160)"))
                        conn.commit()
                        logger.info("✓ Added business_street column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_street column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_zip' not in app_settings_columns:
                    logger.info("Adding business_zip column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_zip VARCHAR(20)"))
                        conn.commit()
                        logger.info("✓ Added business_zip column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_zip column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_city' not in app_settings_columns:
                    logger.info("Adding business_city column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_city VARCHAR(120)"))
                        conn.commit()
                        logger.info("✓ Added business_city column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_city column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_phone' not in app_settings_columns:
                    logger.info("Adding business_phone column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_phone VARCHAR(50)"))
                        conn.commit()
                        logger.info("✓ Added business_phone column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_phone column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_email' not in app_settings_columns:
                    logger.info("Adding business_email column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_email VARCHAR(160)"))
                        conn.commit()
                        logger.info("✓ Added business_email column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_email column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_tax_number' not in app_settings_columns:
                    logger.info("Adding business_tax_number column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_tax_number VARCHAR(80)"))
                        conn.commit()
                        logger.info("✓ Added business_tax_number column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_tax_number column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'business_registration_number' not in app_settings_columns:
                    logger.info("Adding business_registration_number column to app_settings table...")
                    try:
                        conn.execute(text("ALTER TABLE app_settings ADD COLUMN business_registration_number VARCHAR(120)"))
                        conn.commit()
                        logger.info("✓ Added business_registration_number column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add business_registration_number column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_enabled' not in app_settings_columns:
                    logger.info("Adding email_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN email_enabled BOOLEAN DEFAULT :default_email_enabled NOT NULL"
                        ), {"default_email_enabled": DEFAULT_EMAIL_ENABLED})
                        conn.commit()
                        logger.info("✓ Added email_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_sender' not in app_settings_columns:
                    logger.info("Adding email_sender column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN email_sender VARCHAR(160) DEFAULT :default_email_sender"
                        ), {"default_email_sender": DEFAULT_EMAIL_SENDER})
                        conn.commit()
                        logger.info("✓ Added email_sender column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_sender column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_recipient_zbon' not in app_settings_columns:
                    logger.info("Adding email_recipient_zbon column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN email_recipient_zbon VARCHAR(160) DEFAULT :default_email_recipient"
                        ), {"default_email_recipient": DEFAULT_EMAIL_RECIPIENT_ZBON})
                        conn.commit()
                        logger.info("✓ Added email_recipient_zbon column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_recipient_zbon column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_recipient_stock' not in app_settings_columns:
                    logger.info("Adding email_recipient_stock column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN email_recipient_stock VARCHAR(160) DEFAULT :default_email_recipient_stock"
                        ), {"default_email_recipient_stock": DEFAULT_EMAIL_RECIPIENT_STOCK})
                        conn.commit()
                        logger.info("✓ Added email_recipient_stock column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_recipient_stock column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_recipient_backup' not in app_settings_columns:
                    logger.info("Adding email_recipient_backup column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN email_recipient_backup VARCHAR(160) DEFAULT :default_email_recipient_backup"
                        ), {"default_email_recipient_backup": DEFAULT_EMAIL_RECIPIENT_BACKUP})
                        conn.commit()
                        logger.info("✓ Added email_recipient_backup column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_recipient_backup column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'email_subject_suffix' not in app_settings_columns:
                    logger.info("Adding email_subject_suffix column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN email_subject_suffix VARCHAR(120) DEFAULT :default_email_subject_suffix"
                        ), {"default_email_subject_suffix": DEFAULT_EMAIL_SUBJECT_SUFFIX})
                        conn.commit()
                        logger.info("✓ Added email_subject_suffix column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_subject_suffix column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                for subject_info_column in (
                    'email_subject_zbon_info',
                    'email_subject_stock_info',
                    'email_subject_backup_info',
                ):
                    if subject_info_column in app_settings_columns:
                        continue
                    logger.info("Adding %s column to app_settings table...", subject_info_column)
                    try:
                        conn.execute(text(
                            f"ALTER TABLE app_settings ADD COLUMN {subject_info_column} VARCHAR(120)"
                        ))
                        conn.commit()
                        logger.info("✓ Added %s column to app_settings", subject_info_column)
                    except Exception as e:
                        logger.warning("Could not add %s column: %s", subject_info_column, str(e))
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        raise

                if 'email_critical_stock_enabled' not in app_settings_columns:
                    logger.info("Adding email_critical_stock_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN email_critical_stock_enabled BOOLEAN DEFAULT :default_email_critical_stock_enabled NOT NULL"
                        ), {"default_email_critical_stock_enabled": DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED})
                        conn.commit()
                        logger.info("✓ Added email_critical_stock_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add email_critical_stock_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'smtp_host' not in app_settings_columns:
                    logger.info("Adding smtp_host column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN smtp_host VARCHAR(255) DEFAULT :default_smtp_host"
                        ), {"default_smtp_host": DEFAULT_SMTP_HOST})
                        conn.commit()
                        logger.info("✓ Added smtp_host column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add smtp_host column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'smtp_port' not in app_settings_columns:
                    logger.info("Adding smtp_port column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN smtp_port INTEGER DEFAULT :default_smtp_port NOT NULL"
                        ), {"default_smtp_port": DEFAULT_SMTP_PORT})
                        conn.commit()
                        logger.info("✓ Added smtp_port column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add smtp_port column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'smtp_username' not in app_settings_columns:
                    logger.info("Adding smtp_username column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN smtp_username VARCHAR(255) DEFAULT :default_smtp_username"
                        ), {"default_smtp_username": DEFAULT_SMTP_USERNAME})
                        conn.commit()
                        logger.info("✓ Added smtp_username column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add smtp_username column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'smtp_password' not in app_settings_columns:
                    logger.info("Adding smtp_password column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN smtp_password VARCHAR(255) DEFAULT :default_smtp_password"
                        ), {"default_smtp_password": DEFAULT_SMTP_PASSWORD})
                        conn.commit()
                        logger.info("✓ Added smtp_password column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add smtp_password column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'smtp_use_tls' not in app_settings_columns:
                    logger.info("Adding smtp_use_tls column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN smtp_use_tls BOOLEAN DEFAULT :default_smtp_use_tls NOT NULL"
                        ), {"default_smtp_use_tls": DEFAULT_SMTP_USE_TLS})
                        conn.commit()
                        logger.info("✓ Added smtp_use_tls column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add smtp_use_tls column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'send_zbon_on_create_enabled' not in app_settings_columns:
                    logger.info("Adding send_zbon_on_create_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN send_zbon_on_create_enabled BOOLEAN DEFAULT :default_send_on_create NOT NULL"
                        ), {"default_send_on_create": DEFAULT_SEND_ZBON_ON_CREATE_ENABLED})
                        conn.commit()
                        logger.info("✓ Added send_zbon_on_create_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add send_zbon_on_create_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'scheduled_zbon_enabled' not in app_settings_columns:
                    logger.info("Adding scheduled_zbon_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN scheduled_zbon_enabled BOOLEAN DEFAULT :default_scheduled_enabled NOT NULL"
                        ), {"default_scheduled_enabled": DEFAULT_SCHEDULED_ZBON_ENABLED})
                        conn.commit()
                        logger.info("✓ Added scheduled_zbon_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add scheduled_zbon_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'scheduled_zbon_time' not in app_settings_columns:
                    logger.info("Adding scheduled_zbon_time column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN scheduled_zbon_time VARCHAR(5) DEFAULT :default_scheduled_time NOT NULL"
                        ), {"default_scheduled_time": DEFAULT_SCHEDULED_ZBON_TIME})
                        conn.commit()
                        logger.info("✓ Added scheduled_zbon_time column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add scheduled_zbon_time column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'scheduled_zbon_report_type' not in app_settings_columns:
                    logger.info("Adding scheduled_zbon_report_type column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings ADD COLUMN scheduled_zbon_report_type VARCHAR(32) DEFAULT :default_scheduled_report_type NOT NULL"
                        ), {"default_scheduled_report_type": DEFAULT_SCHEDULED_ZBON_REPORT_TYPE})
                        conn.commit()
                        logger.info("✓ Added scheduled_zbon_report_type column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add scheduled_zbon_report_type column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'scheduled_database_backup_enabled' not in app_settings_columns:
                    logger.info("Adding scheduled_database_backup_enabled column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN scheduled_database_backup_enabled BOOLEAN DEFAULT :default_backup_enabled NOT NULL"
                        ), {"default_backup_enabled": DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED})
                        conn.commit()
                        logger.info("✓ Added scheduled_database_backup_enabled column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add scheduled_database_backup_enabled column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'scheduled_database_backup_time' not in app_settings_columns:
                    logger.info("Adding scheduled_database_backup_time column to app_settings table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE app_settings "
                            "ADD COLUMN scheduled_database_backup_time VARCHAR(5) DEFAULT :default_backup_time NOT NULL"
                        ), {"default_backup_time": DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME})
                        conn.commit()
                        logger.info("✓ Added scheduled_database_backup_time column to app_settings")
                    except Exception as e:
                        logger.warning(f"Could not add scheduled_database_backup_time column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

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
                        raise

            if 'guest_list_entries' in inspector.get_table_names():
                guest_list_columns = {col['name'] for col in inspector.get_columns('guest_list_entries')}

                if 'guest_first_name' not in guest_list_columns:
                    logger.info("Adding guest_first_name column to guest_list_entries table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE guest_list_entries ADD COLUMN guest_first_name VARCHAR(120)"
                        ))
                        conn.commit()
                        logger.info("✓ Added guest_first_name column to guest_list_entries")
                    except Exception as e:
                        logger.warning(f"Could not add guest_first_name column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'guest_last_name' not in guest_list_columns:
                    logger.info("Adding guest_last_name column to guest_list_entries table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE guest_list_entries ADD COLUMN guest_last_name VARCHAR(120)"
                        ))
                        conn.commit()
                        logger.info("✓ Added guest_last_name column to guest_list_entries")
                    except Exception as e:
                        logger.warning(f"Could not add guest_last_name column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'member_id' not in guest_list_columns:
                    logger.info("Adding member_id column to guest_list_entries table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE guest_list_entries ADD COLUMN member_id INTEGER"
                        ))
                        conn.execute(text(
                            "ALTER TABLE guest_list_entries "
                            "ADD CONSTRAINT fk_guest_list_entries_member_id "
                            "FOREIGN KEY (member_id) REFERENCES members(id)"
                        ))
                        conn.commit()
                        logger.info("✓ Added member_id column to guest_list_entries")
                    except Exception as e:
                        logger.warning(f"Could not add member_id column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                try:
                    rows = conn.execute(text(
                        "SELECT id, guest_name, guest_first_name, guest_last_name FROM guest_list_entries"
                    )).fetchall()

                    for row in rows:
                        row_mapping = row._mapping
                        entry_id = row_mapping["id"]
                        guest_name = (row_mapping.get("guest_name") or "").strip()
                        guest_first_name = (row_mapping.get("guest_first_name") or "").strip()
                        guest_last_name = (row_mapping.get("guest_last_name") or "").strip()

                        if not guest_first_name and guest_name:
                            parts = guest_name.split(maxsplit=1)
                            guest_first_name = parts[0]
                            if len(parts) > 1 and not guest_last_name:
                                guest_last_name = parts[1]

                        if not guest_first_name:
                            continue

                        normalized_guest_name = f"{guest_first_name} {guest_last_name}".strip()
                        if (
                            (row_mapping.get("guest_first_name") or "").strip() == guest_first_name
                            and (row_mapping.get("guest_last_name") or "").strip() == guest_last_name
                            and guest_name == normalized_guest_name
                        ):
                            continue

                        conn.execute(
                            text(
                                "UPDATE guest_list_entries "
                                "SET guest_name = :guest_name, guest_first_name = :guest_first_name, guest_last_name = :guest_last_name "
                                "WHERE id = :entry_id"
                            ),
                            {
                                "entry_id": entry_id,
                                "guest_name": normalized_guest_name,
                                "guest_first_name": guest_first_name,
                                "guest_last_name": guest_last_name or None,
                            }
                        )

                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not normalize guest list name columns: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

            if 'cash_entries' in inspector.get_table_names():
                cash_entry_columns = {col['name'] for col in inspector.get_columns('cash_entries')}

                if 'receipt_number' not in cash_entry_columns:
                    try:
                        conn.execute(text(
                            "ALTER TABLE cash_entries ADD COLUMN receipt_number INTEGER"
                        ))
                        conn.execute(text(
                            "CREATE INDEX IF NOT EXISTS ix_cash_entries_receipt_number ON cash_entries (receipt_number)"
                        ))
                        conn.commit()
                    except Exception as e:
                        logger.warning(f"Could not add cash_entries.receipt_number column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                try:
                    current_max_result = conn.execute(text("""
                        SELECT GREATEST(
                            COALESCE((SELECT MAX(receipt_number) FROM transactions), 0),
                            COALESCE((SELECT MAX(receipt_number) FROM cash_entries), 0)
                        )
                    """))
                    current_max_receipt = current_max_result.scalar() or 0

                    conn.execute(text("""
                        WITH numbered_entries AS (
                            SELECT
                                id,
                                ROW_NUMBER() OVER (ORDER BY created_at ASC, id ASC) + :current_max AS next_receipt_number
                            FROM cash_entries
                            WHERE receipt_number IS NULL
                        )
                        UPDATE cash_entries
                        SET receipt_number = numbered_entries.next_receipt_number
                        FROM numbered_entries
                        WHERE cash_entries.id = numbered_entries.id
                    """), {"current_max": current_max_receipt})
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not backfill cash_entries.receipt_number values: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

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
                        raise

                if 'failed_login_attempts' not in users_columns:
                    # Anforderung 1: TopAdmin-Passwort-Reset-Workflow benötigt einen
                    # Fehlversuchszähler, um nach 5 Fehlversuchen automatisch den
                    # Self-Service-Reset-Dialog anzubieten.
                    try:
                        conn.execute(text(
                            "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"
                        ))
                        conn.commit()
                        logger.info("✓ Added failed_login_attempts column to users")
                    except Exception as e:
                        logger.warning(f"Could not add users.failed_login_attempts column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

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
                        raise
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
                        raise

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
                    raise

                # Member emails are intentionally non-unique. Keep historical DBs compatible
                # by removing legacy unique constraints/indexes that were created in older
                # versions.
                try:
                    conn.execute(text("""
                        DO $$
                        DECLARE idx RECORD;
                        BEGIN
                            FOR idx IN (
                                SELECT i.indexname
                                FROM pg_indexes i
                                WHERE i.schemaname = current_schema()
                                  AND i.tablename = 'members'
                                  AND i.indexdef ILIKE 'CREATE UNIQUE INDEX%'
                                  AND i.indexdef ILIKE '%(email)%'
                            ) LOOP
                                EXECUTE format('DROP INDEX IF EXISTS %I', idx.indexname);
                            END LOOP;
                        END
                        $$;
                    """))
                    conn.execute(text("""
                        DO $$
                        DECLARE c RECORD;
                        BEGIN
                            FOR c IN (
                                SELECT conname
                                FROM pg_constraint
                                WHERE conrelid = 'members'::regclass
                                  AND contype = 'u'
                                  AND EXISTS (
                                      SELECT 1
                                      FROM unnest(conkey) AS colnum
                                      JOIN pg_attribute a
                                        ON a.attrelid = conrelid
                                       AND a.attnum = colnum
                                      WHERE a.attname = 'email'
                                  )
                            ) LOOP
                                EXECUTE format('ALTER TABLE members DROP CONSTRAINT IF EXISTS %I', c.conname);
                            END LOOP;
                        END
                        $$;
                    """))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not remove members.email unique constraints: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

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
                        raise
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
                        raise
             
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
                        raise

                if 'minimum_stock_quantity' not in products_columns:
                    logger.info("Adding minimum_stock_quantity column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN minimum_stock_quantity INTEGER DEFAULT 0 NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added minimum_stock_quantity column to products")
                    except Exception as e:
                        logger.warning(f"Could not add minimum_stock_quantity column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'notify_on_low_stock' not in products_columns:
                    logger.info("Adding notify_on_low_stock column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN notify_on_low_stock BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added notify_on_low_stock column to products")
                    except Exception as e:
                        logger.warning(f"Could not add notify_on_low_stock column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'is_unlimited_stock' not in products_columns:
                    logger.info("Adding is_unlimited_stock column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN is_unlimited_stock BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added is_unlimited_stock column to products")
                    except Exception as e:
                        logger.warning(f"Could not add is_unlimited_stock column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'warengruppe' not in products_columns:
                    logger.info("Adding warengruppe column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN warengruppe VARCHAR(120)"
                        ))
                        conn.commit()
                        logger.info("✓ Added warengruppe column to products")
                    except Exception as e:
                        logger.warning(f"Could not add warengruppe column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'is_variable_price' not in products_columns:
                    logger.info("Adding is_variable_price column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN is_variable_price BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added is_variable_price column to products")
                    except Exception as e:
                        logger.warning(f"Could not add is_variable_price column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'requires_guest_list' not in products_columns:
                    logger.info("Adding requires_guest_list column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN requires_guest_list BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added requires_guest_list column to products")
                    except Exception as e:
                        logger.warning(f"Could not add requires_guest_list column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'opens_small_parts_drawer' not in products_columns:
                    logger.info("Adding opens_small_parts_drawer column to products table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE products ADD COLUMN opens_small_parts_drawer BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added opens_small_parts_drawer column to products")
                    except Exception as e:
                        logger.warning(f"Could not add opens_small_parts_drawer column: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise
            
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
                        raise

                try:
                    conn.execute(text("""
                        INSERT INTO categories (name, description, is_active_in_kasse, display_order, created_at, updated_at)
                        SELECT :name, :description, TRUE, :display_order, NOW(), NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM categories WHERE name = :name
                        )
                    """), {
                        "name": INTERNAL_MATERIAL_CATEGORY_NAME,
                        "description": INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
                        "display_order": INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
                    })
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not ensure fixed internal material category: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

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
                    (
                        'tip_cents',
                        "ALTER TABLE transactions ADD COLUMN tip_cents INTEGER DEFAULT 0 NOT NULL"
                    ),
                    (
                        'cash_received_cents',
                        "ALTER TABLE transactions ADD COLUMN cash_received_cents INTEGER"
                    ),
                    (
                        'change_given_cents',
                        "ALTER TABLE transactions ADD COLUMN change_given_cents INTEGER"
                    ),
                    (
                        'member_name',
                        "ALTER TABLE transactions ADD COLUMN member_name VARCHAR(160)"
                    ),
                    (
                        'performed_by_username',
                        "ALTER TABLE transactions ADD COLUMN performed_by_username VARCHAR(50)"
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
                        raise

                # Backfill snapshot columns for existing transactions
                try:
                    conn.execute(text("""
                        UPDATE transactions t
                        SET member_name = m.name
                        FROM members m
                        WHERE t.member_id = m.id
                          AND t.member_name IS NULL
                    """))
                    conn.execute(text("""
                        UPDATE transactions t
                        SET performed_by_username = u.username
                        FROM users u
                        WHERE t.user_id = u.id
                          AND t.performed_by_username IS NULL
                    """))
                    conn.commit()
                    logger.info("✓ Backfilled snapshot columns for existing transactions")
                except Exception as e:
                    logger.warning(f"Could not backfill transaction snapshot columns: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

            if 'transaction_items' in inspector.get_table_names():
                transaction_item_columns = {col['name'] for col in inspector.get_columns('transaction_items')}

                if 'is_internal_material' not in transaction_item_columns:
                    logger.info("Adding is_internal_material column to transaction_items table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE transaction_items "
                            "ADD COLUMN is_internal_material BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added is_internal_material column to transaction_items")
                    except Exception as e:
                        logger.warning(f"Could not add is_internal_material to transaction_items: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'note' not in transaction_item_columns:
                    logger.info("Adding note column to transaction_items table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE transaction_items "
                            "ADD COLUMN note VARCHAR(500)"
                        ))
                        conn.commit()
                        logger.info("✓ Added note column to transaction_items")
                    except Exception as e:
                        logger.warning(f"Could not add note to transaction_items: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'product_name' not in transaction_item_columns:
                    logger.info("Adding product_name snapshot column to transaction_items table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE transaction_items ADD COLUMN product_name VARCHAR(120)"
                        ))
                        conn.execute(text("""
                            UPDATE transaction_items ti
                            SET product_name = p.name
                            FROM products p
                            WHERE ti.product_id = p.id
                              AND ti.product_name IS NULL
                        """))
                        conn.commit()
                        logger.info("✓ Added product_name snapshot column to transaction_items")
                    except Exception as e:
                        logger.warning(f"Could not add product_name to transaction_items: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

            if 'deckel_items' in inspector.get_table_names():
                deckel_item_columns = {col['name'] for col in inspector.get_columns('deckel_items')}

                if 'is_internal_material' not in deckel_item_columns:
                    logger.info("Adding is_internal_material column to deckel_items table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE deckel_items "
                            "ADD COLUMN is_internal_material BOOLEAN DEFAULT FALSE NOT NULL"
                        ))
                        conn.commit()
                        logger.info("✓ Added is_internal_material column to deckel_items")
                    except Exception as e:
                        logger.warning(f"Could not add is_internal_material to deckel_items: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

                if 'note' not in deckel_item_columns:
                    logger.info("Adding note column to deckel_items table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE deckel_items "
                            "ADD COLUMN note VARCHAR(500)"
                        ))
                        conn.commit()
                        logger.info("✓ Added note column to deckel_items")
                    except Exception as e:
                        logger.warning(f"Could not add note to deckel_items: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

            if 'material_account_entries' in inspector.get_table_names():
                material_account_columns = {col['name'] for col in inspector.get_columns('material_account_entries')}

                if 'transaction_item_id' not in material_account_columns:
                    logger.info("Adding transaction_item_id column to material_account_entries table...")
                    try:
                        conn.execute(text(
                            "ALTER TABLE material_account_entries "
                            "ADD COLUMN transaction_item_id INTEGER"
                        ))
                        conn.execute(text(
                            "ALTER TABLE material_account_entries "
                            "ADD CONSTRAINT fk_material_account_entries_transaction_item_id "
                            "FOREIGN KEY (transaction_item_id) REFERENCES transaction_items(id)"
                        ))
                        conn.commit()
                        logger.info("✓ Added transaction_item_id column to material_account_entries")
                    except Exception as e:
                        logger.warning(f"Could not add transaction_item_id to material_account_entries: {str(e)}")
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise

            if 'vouchers' in inspector.get_table_names():
                voucher_columns = {col['name'] for col in inspector.get_columns('vouchers')}

                missing_voucher_columns = [
                    (
                        'redeemed_amount_cents',
                        "ALTER TABLE vouchers ADD COLUMN redeemed_amount_cents INTEGER"
                    ),
                    (
                        'original_value_cents',
                        "ALTER TABLE vouchers ADD COLUMN original_value_cents INTEGER"
                    ),
                    (
                        'remaining_value_cents',
                        "ALTER TABLE vouchers ADD COLUMN remaining_value_cents INTEGER"
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
                        raise

                try:
                    logger.info("Backfilling voucher original/remaining values...")
                    conn.execute(text("""
                        UPDATE vouchers
                        SET
                            status = CASE
                                WHEN remaining_value_cents IS NOT NULL OR status::text = 'REDEEMED' THEN status
                                WHEN value_cents - COALESCE(redeemed_amount_cents, 0) <= 0 THEN 'REDEEMED'::voucherstatus
                                WHEN COALESCE(redeemed_amount_cents, 0) > 0 THEN 'PARTIALLY_REDEEMED'::voucherstatus
                                ELSE 'CREATED'::voucherstatus
                            END,
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
                                WHEN remaining_value_cents IS NOT NULL THEN GREATEST(COALESCE(original_value_cents, value_cents) - remaining_value_cents, 0)
                                ELSE 0
                            END)
                        WHERE original_value_cents IS NULL OR remaining_value_cents IS NULL OR redeemed_amount_cents IS NULL
                    """))
                    conn.commit()
                    logger.info("✓ Backfilled voucher original/remaining values")
                except Exception as e:
                    logger.warning(f"Could not backfill voucher values: {str(e)}")
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise

                # NULL distinguishes interrupted backfills from legitimate zero balances.
                for column_name in ("original_value_cents", "remaining_value_cents"):
                    conn.execute(text(f"ALTER TABLE vouchers ALTER COLUMN {column_name} SET DEFAULT 0"))
                    conn.execute(text(f"ALTER TABLE vouchers ALTER COLUMN {column_name} SET NOT NULL"))
                conn.commit()

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
                    ('article_revenue_cents', "ALTER TABLE zbon_history ADD COLUMN article_revenue_cents INTEGER"),
                    ('cash_sale_payments_cents', "ALTER TABLE zbon_history ADD COLUMN cash_sale_payments_cents INTEGER"),
                    ('balance_redeemed_cents', "ALTER TABLE zbon_history ADD COLUMN balance_redeemed_cents INTEGER"),
                    ('voucher_redeemed_cents', "ALTER TABLE zbon_history ADD COLUMN voucher_redeemed_cents INTEGER"),
                    ('member_recharges_cents', "ALTER TABLE zbon_history ADD COLUMN member_recharges_cents INTEGER"),
                    ('club_account_recharges_cents', "ALTER TABLE zbon_history ADD COLUMN club_account_recharges_cents INTEGER"),
                    ('prepaid_sales_cents', "ALTER TABLE zbon_history ADD COLUMN prepaid_sales_cents INTEGER"),
                    ('tip_donations_cents', "ALTER TABLE zbon_history ADD COLUMN tip_donations_cents INTEGER"),
                    ('cash_opening_balance_cents', "ALTER TABLE zbon_history ADD COLUMN cash_opening_balance_cents INTEGER"),
                    ('cash_deposits_cents', "ALTER TABLE zbon_history ADD COLUMN cash_deposits_cents INTEGER"),
                    ('cash_withdrawals_cents', "ALTER TABLE zbon_history ADD COLUMN cash_withdrawals_cents INTEGER"),
                    ('cash_calculated_cents', "ALTER TABLE zbon_history ADD COLUMN cash_calculated_cents INTEGER"),
                    ('total_revenue_cents', "ALTER TABLE zbon_history ADD COLUMN total_revenue_cents INTEGER"),
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
                        raise


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
        # Callers treat False as a fatal startup failure.
        return False
