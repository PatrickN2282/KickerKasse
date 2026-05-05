from sqlalchemy.orm import Session
from app.models import ProductStockCorrectionLog
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
        is_unlimited_stock: bool = False,
        warengruppe: str = None,
        is_variable_price: bool = False,
    ):
        """Create a new product"""
        return self.repo.create(
            name, price_cents, description, member_price_cents,
            is_discountable, stock_quantity, is_unlimited_stock, warengruppe,
            is_variable_price,
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
        return bool(product and (product.is_unlimited_stock or product.stock_quantity >= quantity))
    
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

    def correct_stock(self, product_id: int, new_stock_quantity: int, executed_by_username: str):
        """Set product stock without cash flow and create audit log."""
        product = self.repo.get_by_id(product_id)
        if not product:
            return None

        old_stock_quantity = product.stock_quantity
        product.stock_quantity = new_stock_quantity

        log = ProductStockCorrectionLog(
            product_id=product.id,
            product_name=product.name,
            old_stock_quantity=old_stock_quantity,
            new_stock_quantity=new_stock_quantity,
            change_quantity=new_stock_quantity - old_stock_quantity,
            executed_by_username=executed_by_username,
            reason="KORREKTURBUCHUNG",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(product)
        self.db.refresh(log)
        return product

    def get_stock_correction_logs(self):
        """Get all product stock correction logs."""
        return (
            self.db.query(ProductStockCorrectionLog)
            .order_by(ProductStockCorrectionLog.created_at.desc(), ProductStockCorrectionLog.id.desc())
            .all()
        )
    
    def delete_product(self, product_id: int):
        """Delete product (soft delete)"""
        return self.repo.delete(product_id)
