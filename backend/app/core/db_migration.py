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
            # Create all tables first (for new models like ZBonHistory)
            from app.models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("✓ All tables created/verified")
            
            # Then apply column additions for existing tables
            self._add_missing_columns()
            
            logger.info("✓ Database migration completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Database migration failed: {str(e)}")
            raise
    
    def _add_missing_columns(self):
        """Add missing columns to existing tables"""
        with self.engine.connect() as conn:
            inspector = inspect(self.engine)
            
            # Migration: Add tax_rate column to products table if missing
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
                        conn.rollback()
            
            # Migration: Add description column to categories if missing
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
                        conn.rollback()


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
