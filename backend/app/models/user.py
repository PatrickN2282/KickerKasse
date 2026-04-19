from sqlalchemy import Column, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CASHIER = "CASHIER"
    KASSENMITGLIED = "KASSENMITGLIED"


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CASHIER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def __repr__(self):
        return f"<User {self.username}>"
