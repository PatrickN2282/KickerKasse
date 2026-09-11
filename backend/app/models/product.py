from sqlalchemy import CheckConstraint, Column, String, Integer, DateTime, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint('price_cents >= 0', name='ck_products_price_nonnegative'),
        CheckConstraint('member_price_cents IS NULL OR member_price_cents >= 0', name='ck_products_member_price_nonnegative'),
        CheckConstraint('stock_quantity >= 0', name='ck_products_stock_nonnegative'),
        CheckConstraint('minimum_stock_quantity >= 0', name='ck_products_minimum_stock_nonnegative'),
        CheckConstraint('tax_rate >= 0 AND tax_rate <= 100', name='ck_products_tax_rate_range'),
        CheckConstraint('length(trim(name)) > 0', name='ck_products_name_not_blank'),
    )

    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=True)
    warengruppe = Column(String(120), nullable=True)
    price_cents = Column(Integer, nullable=False)  # Normaler Preis in Cent
    member_price_cents = Column(Integer, nullable=True)  # Mitgliedspreis in Cent
    is_discountable = Column(Boolean, default=True, nullable=False)  # Rabattfähig
    stock_quantity = Column(Integer, default=0, nullable=False)  # Lagerbestand
    minimum_stock_quantity = Column(Integer, default=0, nullable=False)  # Mindestbestand
    notify_on_low_stock = Column(Boolean, default=False, nullable=False)  # Benachrichtigung bei Mindestbestand
    is_unlimited_stock = Column(Boolean, default=False, nullable=False)  # Immer verfügbar
    is_variable_price = Column(Boolean, default=False, nullable=False)  # Preis wird beim Kauf eingegeben
    image_path = Column(String(255), nullable=True)  # Pfad zum Produktbild
    is_active = Column(Boolean, default=True, nullable=False)
    is_visible_in_kasse = Column(Boolean, default=True, nullable=False)  # Unabhängig vom Archivstatus in der Kasse anzeigen
    requires_guest_list = Column(Boolean, default=False, nullable=False)  # Gästeliste erforderlich
    opens_small_parts_drawer = Column(Boolean, default=False, nullable=False)  # Zusätzliches Kleinteile-Lager öffnen
    tax_rate = Column(Float, default=0.0, nullable=False)  # Steuersatz in % (z.B. 19.0, 7.0, 0.0)
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
