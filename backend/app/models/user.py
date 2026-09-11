from sqlalchemy import Column, String, Enum, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class UserRole(str, enum.Enum):
    TOP_ADMIN = "TOP_ADMIN"
    ADMIN = "ADMIN"
    VERKAUF = "VERKAUF"
    MANAGER = "MANAGER"


ROLE_ALIASES = {
    "TOP_ADMIN": UserRole.TOP_ADMIN,
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
        raise ValueError(
            f"Invalid role: {role}. Valid roles are: TOP_ADMIN, ADMIN, VERKAUF, MANAGER"
        )
    return normalized_role


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VERKAUF)
    is_active = Column(Boolean, default=True, nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True, unique=True)
    # Anforderung 1 (TopAdmin-Passwort-Reset-Workflow): zählt aufeinanderfolgende
    # fehlgeschlagene Login-Versuche. Wird bei erfolgreichem Login auf 0 zurückgesetzt.
    # Ab 5 zeigt das Frontend automatisch den Self-Service-Reset-Dialog für den TopAdmin.
    session_version = Column(Integer, nullable=False, default=1, server_default="1")
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    member = relationship("Member", back_populates="linked_user")

    @property
    def is_admin(self) -> bool:
        return self.role in {UserRole.TOP_ADMIN, UserRole.ADMIN}

    @property
    def is_top_admin(self) -> bool:
        return self.role == UserRole.TOP_ADMIN

    def __repr__(self):
        return f"<User {self.username}>"


# Cover direct and linked-account mutations at their shared persistence boundary.
from sqlalchemy import event, inspect, update


@event.listens_for(User, "before_update")
def revoke_sessions_on_access_change(mapper, connection, user):
    state = inspect(user)
    if any(state.attrs[name].history.has_changes() for name in ("password_hash", "role", "is_active")):
        user.session_version = User.session_version + 1
        from .password_reset_token import PasswordResetToken
        connection.execute(update(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).values(used_at=func.now()))
