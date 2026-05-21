from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func

from .base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    user_username = Column(String(50), nullable=True)
    entity_type = Column(String(50), nullable=False)   # member | product | settings
    entity_id = Column(Integer, nullable=True)
    entity_name = Column(String(255), nullable=True)   # snapshot of name at action time
    action = Column(String(20), nullable=False)         # CREATED | UPDATED | DELETED
    old_value = Column(Text, nullable=True)             # JSON string
    new_value = Column(Text, nullable=True)             # JSON string

    def __repr__(self):
        return f"<AuditLog {self.id} {self.action} {self.entity_type} {self.entity_id}>"
