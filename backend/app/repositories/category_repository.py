from sqlalchemy.orm import Session
from app.models import Category


class CategoryRepository:
    """Repository for Category model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        name: str,
        description: str = None,
        is_active_in_kasse: bool = True,
        display_order: int = 0,
    ) -> Category:
        """Create a new category"""
        category = Category(
            name=name,
            description=description,
            is_active_in_kasse=is_active_in_kasse,
            display_order=display_order,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def get_by_id(self, category_id: int) -> Category | None:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_all(self, only_active: bool = False) -> list[Category]:
        """Get all categories"""
        query = self.db.query(Category)
        if only_active:
            query = query.filter(Category.is_active_in_kasse == True)
        return query.order_by(Category.display_order).all()
    
    def update(
        self,
        category_id: int,
        name: str = None,
        description: str = None,
        is_active_in_kasse: bool = None,
        display_order: int = None,
    ) -> Category | None:
        """Update a category"""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if is_active_in_kasse is not None:
            category.is_active_in_kasse = is_active_in_kasse
        if display_order is not None:
            category.display_order = display_order
        
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete(self, category_id: int) -> bool:
        """Delete a category"""
        category = self.get_by_id(category_id)
        if not category:
            return False
        
        self.db.delete(category)
        self.db.commit()
        return True
