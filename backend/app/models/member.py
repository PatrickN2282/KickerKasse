from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from .base import BaseModel


class Member(BaseModel):
    __tablename__ = "members"

    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    balance_cents = Column(Integer, default=0, nullable=False)  # In Cent, keine negativen Werte
    photo_path = Column(String(255), nullable=True)  # Pfad zum Mitgliedsfoto
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Member {self.name}>"
