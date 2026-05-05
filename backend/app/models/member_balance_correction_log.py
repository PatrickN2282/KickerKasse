from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class MemberBalanceCorrectionLog(BaseModel):
    __tablename__ = "member_balance_correction_logs"

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    member_name = Column(String(160), nullable=False)
    old_balance_cents = Column(Integer, nullable=False)
    new_balance_cents = Column(Integer, nullable=False)
    change_cents = Column(Integer, nullable=False)
    executed_by_username = Column(String(50), nullable=False)
    reason = Column(String(255), nullable=False, default="KORREKTURBUCHUNG")
    created_at = Column(DateTime, default=func.now(), nullable=False)

    member = relationship("Member")

    def __repr__(self):
        return f"<MemberBalanceCorrectionLog {self.id} - {self.member_name}>"
