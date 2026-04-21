from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hasher
from app.models import User, UserRole
from app.repositories import UserRepository


ROLE_ADMIN_PANEL = {UserRole.ADMIN, UserRole.MANAGER}
ROLE_FINANCE = {UserRole.ADMIN, UserRole.MANAGER}
ROLE_MEMBER_MANAGEMENT = {UserRole.ADMIN, UserRole.MANAGER}


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
    if user.role == UserRole.TOP_ADMIN:
        return True
    return user.role in set(roles)


def require_top_admin(request: Request, db: Session) -> User:
    return require_roles(request, db, UserRole.TOP_ADMIN)


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


def resolve_confirmation_user(
    db: Session,
    current_user: User,
    password: str | None,
    *,
    username: str | None = None,
    allow_top_admin_override: bool = False,
) -> User:
    requested_username = (username or "").strip()
    if not requested_username or requested_username == current_user.username:
        require_password_confirmation(current_user, password)
        return current_user

    if not allow_top_admin_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Abweichende Zugangsdaten sind für diese Aktion nicht erlaubt",
        )

    override_user = UserRepository(db).get_by_username(requested_username)
    if not override_user or not override_user.is_active or override_user.role != UserRole.TOP_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf diese Aktion mit abweichenden Zugangsdaten freigeben",
        )

    require_password_confirmation(override_user, password)
    return override_user


def require_auth(f):
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        if not request or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        require_authenticated_user(request, db)
        return await f(*args, **kwargs)
    return decorated


def require_admin(f):
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        if not request or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        require_roles(request, db, UserRole.ADMIN)
        return await f(*args, **kwargs)
    return decorated
