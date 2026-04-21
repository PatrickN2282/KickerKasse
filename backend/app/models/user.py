from sqlalchemy import Column, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    VERKAUF = "VERKAUF"
    MANAGER = "MANAGER"


ROLE_ALIASES = {
    "ADMIN": UserRole.ADMIN,
    "CASHIER": UserRole.VERKAUF,
    "VERKAUF": UserRole.VERKAUF,
    "KASSENMITGLIED": UserRole.MANAGER,
    "MANAGER": UserRole.MANAGER,
}


def parse_user_role(role: str | UserRole | None, *, default: UserRole | None = None) -> UserRole | None:
    if role in (None, ""):
        return default
    if isinstance(role, UserRole):
        return role

    normalized_role = ROLE_ALIASES.get(str(role).strip().upper())
    if normalized_role is None:
        raise ValueError(f"Invalid role: {role}")
    return normalized_role


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VERKAUF)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def __repr__(self):
        return f"<User {self.username}>"
