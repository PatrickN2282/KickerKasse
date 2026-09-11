from sqlalchemy import CheckConstraint, Column, String, Integer, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
from .user import UserRole


class Member(BaseModel):
    __tablename__ = "members"
    __table_args__ = (
        CheckConstraint('balance_cents >= 0', name='ck_members_balance_nonnegative'),
        CheckConstraint('length(trim(name)) > 0', name='ck_members_name_not_blank'),
        CheckConstraint("length(trim(first_name) || ' ' || trim(last_name)) <= 120", name='ck_members_combined_name_length'),
    )

    archived_at = Column(DateTime, nullable=True, index=True)
    member_number = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    membership_number = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(120), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    has_discount = Column(Boolean, default=True, nullable=False)
    role = Column(Enum(UserRole), nullable=True)
    balance_cents = Column(Integer, default=0, nullable=False)  # In Cent, keine negativen Werte
    photo_path = Column(String(255), nullable=True)  # Pfad zum Mitgliedsfoto
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    linked_user = relationship("User", back_populates="member", uselist=False)

    def __repr__(self):
        return f"<Member #{self.member_number} {self.name}>"
