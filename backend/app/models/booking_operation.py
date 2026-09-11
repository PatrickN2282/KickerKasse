from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from .base import BaseModel


class BookingOperation(BaseModel):
    __tablename__ = "booking_operations"
    operation_key = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=False)
    response_status = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ReceiptCounter(BaseModel):
    __tablename__ = "receipt_counter"
    last_number = Column(Integer, nullable=False, default=0)
