from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class Deckel(BaseModel):
    __tablename__ = "deckel"

    name = Column(String(120), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    created_by = relationship("User")
    items = relationship("DeckelItem", back_populates="deckel", cascade="all, delete-orphan")


class DeckelItem(BaseModel):
    __tablename__ = "deckel_items"

    deckel_id = Column(Integer, ForeignKey("deckel.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    total_price_cents = Column(Integer, nullable=False)
    is_internal_material = Column(Boolean, nullable=False, default=False)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    deckel = relationship("Deckel", back_populates="items")
    product = relationship("Product")
