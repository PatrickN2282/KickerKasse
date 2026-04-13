from sqlalchemy import Column, String, Integer, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


# Many-to-many association table
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
)


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(120), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    is_active_in_kasse = Column(Boolean, default=True, nullable=False)  # Sichtbar in Kassenansicht
    display_order = Column(Integer, default=0, nullable=False)  # Sortierreihenfolge
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to products
    products = relationship(
        "Product",
        secondary=product_category,
        back_populates="categories",
    )

    def __repr__(self):
        return f"<Category {self.name}>"
