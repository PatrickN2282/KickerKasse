"""Database initialization - creates default users and categories on startup"""
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, UserRole, Category
import bcrypt


def init_default_users(db: Session) -> None:
    """Create default users if they don't exist"""
    
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
    
    # Create sales user "Kasse1"
    cashier_password_hash = bcrypt.hashpw(
        "Kasse1123".encode(), bcrypt.gensalt(12)
    ).decode()
    
    cashier_user = User(
        username="Kasse1",
        email="kasse1@kassensoftware.local",
        password_hash=cashier_password_hash,
        role=UserRole.VERKAUF,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db.add(admin_user)
    db.add(cashier_user)
    db.commit()
    
    print("✅ Default users created: admin (admin123) and Kasse1 (Kasse1123)")
    
    # Initialize default categories
    init_default_categories(db)


def init_default_categories(db: Session) -> None:
    """Create default product categories if they don't exist"""
    
    # Check if categories already exist
    existing_categories = db.query(Category).count()
    
    if existing_categories > 0:
        # Already initialized
        return
    
    default_categories = [
        {"name": "Getränke", "description": "Getränke und Getränkepakete", "display_order": 1},
        {"name": "Material", "description": "Material und Zubehör", "display_order": 2},
        {"name": "Speisen", "description": "Speisen und Snacks", "display_order": 3},
        {"name": "Veranstaltung", "description": "Veranstaltungen und Events", "display_order": 4},
    ]
    
    for cat_data in default_categories:
        category = Category(
            name=cat_data["name"],
            description=cat_data["description"],
            is_active_in_kasse=True,
            display_order=cat_data["display_order"],
        )
        db.add(category)
    
    db.commit()
    print("✅ Default categories created: Getränke, Material, Speisen, Veranstaltung")
