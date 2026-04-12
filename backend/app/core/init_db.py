"""Database initialization - creates default users on startup"""
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, UserRole
import bcrypt


def init_default_users(db: Session) -> None:
    """Create admin and defaultcashier user if they don't exist"""
    
    # Check if any users exist
    existing_users = db.query(User).count()
    
    if existing_users > 0:
        # Already initialized
        return
    
    # Create admin user
    admin_password_hash = bcrypt.hashpw(
        "admin123".encode(), bcrypt.gensalt(12)
    ).decode()
    
    admin_user = User(
        username="admin",
        email="admin@kassensoftware.local",
        password_hash=admin_password_hash,
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # Create cashier user "Kasse1"
    cashier_password_hash = bcrypt.hashpw(
        "Kasse1123".encode(), bcrypt.gensalt(12)
    ).decode()
    
    cashier_user = User(
        username="Kasse1",
        email="kasse1@kassensoftware.local",
        password_hash=cashier_password_hash,
        role=UserRole.CASHIER,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db.add(admin_user)
    db.add(cashier_user)
    db.commit()
    
    print("✅ Default users created: admin (admin123) and Kasse1 (Kasse1123)")
