from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class BalanceLog(BaseModel):
    __tablename__ = "balance_logs"

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    old_balance_cents = Column(Integer, nullable=False)
    new_balance_cents = Column(Integer, nullable=False)
    change_cents = Column(Integer, nullable=False)
    
    reason = Column(String(255), nullable=False)  # z.B. "SALE", "STORNO", "MANUAL_RECHARGE"
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    member = relationship("Member")
    transaction = relationship("Transaction")

    def __repr__(self):
        return f"<BalanceLog {self.id} - {self.reason}>"
