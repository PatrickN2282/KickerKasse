from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from .base import BaseModel
from .user import UserRole


class Member(BaseModel):
    __tablename__ = "members"

    member_number = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    membership_number = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    has_discount = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(UserRole), nullable=True)
    balance_cents = Column(Integer, default=0, nullable=False)  # In Cent, keine negativen Werte
    photo_path = Column(String(255), nullable=True)  # Pfad zum Mitgliedsfoto
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Member #{self.member_number} {self.name}>"
