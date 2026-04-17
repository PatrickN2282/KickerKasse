from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hasher
from app.models import User, UserRole
from app.repositories import UserRepository


ROLE_ADMIN_PANEL = {UserRole.ADMIN, UserRole.KASSENMITGLIED}
ROLE_FINANCE = {UserRole.ADMIN, UserRole.KASSENMITGLIED}
ROLE_MEMBER_MANAGEMENT = {UserRole.ADMIN, UserRole.KASSENMITGLIED}


async def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    return UserRepository(db).get_by_id(user_id)


def require_authenticated_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


def has_any_role(user: User, *roles: UserRole) -> bool:
    return user.role in set(roles)


def require_roles(request: Request, db: Session, *roles: UserRole) -> User:
    user = require_authenticated_user(request, db)
    if roles and not has_any_role(user, *roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


def require_password_confirmation(user: User, password: str | None) -> None:
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation required",
        )

    if not get_password_hasher().verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password confirmation failed",
        )
