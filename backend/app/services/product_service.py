from sqlalchemy.orm import Session
from app.repositories import ProductRepository


class ProductService:
    """Product management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
    
    def create_product(
        self, name: str, price_cents: int, description: str = None,
        member_price_cents: int = None, is_discountable: bool = True,
        stock_quantity: int = 0,
    ):
        """Create a new product"""
        return self.repo.create(
            name, price_cents, description, member_price_cents,
            is_discountable, stock_quantity
        )
    
    def get_product(self, product_id: int):
        """Get product by ID"""
        return self.repo.get_by_id(product_id)
    
    def get_all_products(self, only_active: bool = True):
        """Get all products"""
        return self.repo.get_all(only_active)
    
    def update_product(self, product_id: int, **kwargs):
        """Update product"""
        return self.repo.update(product_id, **kwargs)
    
    def check_stock(self, product_id: int, quantity: int) -> bool:
        """Check if product has sufficient stock"""
        product = self.repo.get_by_id(product_id)
        return product and product.stock_quantity >= quantity
    
    def adjust_stock(self, product_id: int, quantity: int):
        """Adjust product stock (positive or negative)"""
        product = self.repo.get_by_id(product_id)
        if not product:
            return None
        
        if quantity > 0:
            return self.repo.add_stock(product_id, quantity)
        else:
            if not self.repo.deduct_stock(product_id, abs(quantity)):
                return None
            return self.repo.get_by_id(product_id)
    
    def delete_product(self, product_id: int):
        """Delete product (soft delete)"""
        return self.repo.delete(product_id)
