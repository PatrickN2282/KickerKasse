from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=True)
    price_cents = Column(Integer, nullable=False)  # Normaler Preis in Cent
    member_price_cents = Column(Integer, nullable=True)  # Mitgliedspreis in Cent
    is_discountable = Column(Boolean, default=True, nullable=False)  # Rabattfähig
    stock_quantity = Column(Integer, default=0, nullable=False)  # Lagerbestand
    image_path = Column(String(255), nullable=True)  # Pfad zum Produktbild
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to categories
    categories = relationship(
        "Category",
        secondary="product_category",
        back_populates="products",
    )

    def __repr__(self):
        return f"<Product {self.name}>"
