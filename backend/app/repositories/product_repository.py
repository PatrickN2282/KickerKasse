from sqlalchemy.orm import Session
from app.models import Product


class ProductRepository:
    """Repository for Product model"""
    
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalize_warengruppe(values: dict) -> dict:
        normalized_values = dict(values)
        warengruppe = normalized_values.get("warengruppe")
        if isinstance(warengruppe, str):
            warengruppe = warengruppe.strip()
            normalized_values["warengruppe"] = warengruppe or None
        return normalized_values

    @staticmethod
    def _normalize_stock_fields(values: dict) -> dict:
        normalized_values = dict(values)
        if normalized_values.get("is_unlimited_stock"):
            normalized_values["stock_quantity"] = 0
        return normalized_values
    
    def create(
        self,
        name: str,
        price_cents: int,
        description: str = None,
        member_price_cents: int = None,
        is_discountable: bool = True,
        stock_quantity: int = 0,
        is_unlimited_stock: bool = False,
        warengruppe: str = None,
    ) -> Product:
        """Create a new product"""
        product_data = {
            "name": name,
            "description": description,
            "warengruppe": warengruppe,
            "price_cents": price_cents,
            "member_price_cents": member_price_cents,
            "is_discountable": is_discountable,
            "stock_quantity": stock_quantity,
            "is_unlimited_stock": is_unlimited_stock,
        }
        product_data = self._normalize_stock_fields(product_data)
        product_data = self._normalize_warengruppe(product_data)
        product = Product(**product_data)
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

        normalized_kwargs = self._normalize_warengruppe(self._normalize_stock_fields(kwargs))
        for key, value in normalized_kwargs.items():
            if hasattr(product, key) and key != "id":
                setattr(product, key, value)
        
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def deduct_stock(self, product_id: int, quantity: int) -> bool:
        """Deduct stock from product. Returns False if insufficient stock"""
        product = self.get_by_id(product_id)
        if not product:
            return False

        if not (product.is_unlimited_stock or product.stock_quantity >= quantity):
            return False
        
        if product.is_unlimited_stock:
            return True

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
