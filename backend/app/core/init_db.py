"""Database initialization - creates default data on startup"""
from sqlalchemy.orm import Session
from app.models import Category


def init_default_users(db: Session) -> None:
    """Initialize non-user default data only."""
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
