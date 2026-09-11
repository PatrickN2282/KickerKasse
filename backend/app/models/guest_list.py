from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class GuestListEntry(BaseModel):
    __tablename__ = "guest_list_entries"

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    guest_name = Column(String(255), nullable=False)
    guest_first_name = Column(String(120), nullable=True)
    guest_last_name = Column(String(120), nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    transaction_item_id = Column(Integer, ForeignKey("transaction_items.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    product = relationship("Product")
    member = relationship("Member")
    transaction = relationship("Transaction")

    def __repr__(self):
        guest_display = f"{self.guest_first_name or ''} {self.guest_last_name or ''}".strip() or self.guest_name
        return f"<GuestListEntry {guest_display} for product {self.product_id}>"
