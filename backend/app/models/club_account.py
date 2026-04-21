from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class ClubAccountEntry(BaseModel):
    __tablename__ = "club_account_entries"

    amount_cents = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    voucher = relationship("Voucher")
    transaction = relationship("Transaction")
