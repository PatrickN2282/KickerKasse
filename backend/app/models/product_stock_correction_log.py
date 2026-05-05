from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class ProductStockCorrectionLog(BaseModel):
    __tablename__ = "product_stock_correction_logs"

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(120), nullable=False)
    old_stock_quantity = Column(Integer, nullable=False)
    new_stock_quantity = Column(Integer, nullable=False)
    change_quantity = Column(Integer, nullable=False)
    executed_by_username = Column(String(50), nullable=False)
    reason = Column(String(255), nullable=False, default="KORREKTURBUCHUNG")
    created_at = Column(DateTime, default=func.now(), nullable=False)

    product = relationship("Product")

    def __repr__(self):
        return f"<ProductStockCorrectionLog {self.id} - {self.product_name}>"
