from sqlalchemy.orm import Session
from app.models import Product


class ProductRepository:
    """Repository for Product model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        name: str,
        price_cents: int,
        description: str = None,
        member_price_cents: int = None,
        is_discountable: bool = True,
        stock_quantity: int = 0,
        is_unlimited_stock: bool = False,
    ) -> Product:
        """Create a new product"""
        product = Product(
            name=name,
            description=description,
            price_cents=price_cents,
            member_price_cents=member_price_cents,
            is_discountable=member_price_cents is not None if member_price_cents is not None else is_discountable,
            stock_quantity=0 if is_unlimited_stock else stock_quantity,
            is_unlimited_stock=is_unlimited_stock,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_by_id(self, product_id: int) -> Product | None:
        """Get product by ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_all(self, only_active: bool = True) -> list[Product]:
        """Get all products"""
        query = self.db.query(Product)
        if only_active:
            query = query.filter(Product.is_active == True)
        return query.order_by(Product.name).all()
    
    def update(self, product_id: int, **kwargs) -> Product | None:
        """Update product"""
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        for key, value in kwargs.items():
            if hasattr(product, key) and key != "id":
                setattr(product, key, value)

        if "member_price_cents" in kwargs:
            product.is_discountable = kwargs["member_price_cents"] is not None

        if product.is_unlimited_stock:
            product.stock_quantity = 0
        
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def deduct_stock(self, product_id: int, quantity: int) -> bool:
        """Deduct stock from product. Returns False if insufficient stock"""
        product = self.get_by_id(product_id)
        if not product:
            return False

        if product.is_unlimited_stock:
            return True
        
        if product.stock_quantity < quantity:
            return False
        
        product.stock_quantity -= quantity
        self.db.commit()
        return True
    
    def add_stock(self, product_id: int, quantity: int) -> Product | None:
        """Add stock to product"""
        product = self.get_by_id(product_id)
        if not product:
            return None

        if product.is_unlimited_stock:
            self.db.refresh(product)
            return product
        
        product.stock_quantity += quantity
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete(self, product_id: int) -> bool:
        """Soft delete product (set is_active to False)"""
        product = self.get_by_id(product_id)
        if not product:
            return False
        
        product.is_active = False
        self.db.commit()
        return True
